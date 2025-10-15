# Miser 2D - Arabic Version with Proper Text Handling
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'load-display pandagl')

from ursina import *
import random, os, sys, math
import arabic_reshaper
from bidi.algorithm import get_display

# ----- Asset Folder (for EXE builds) -----
if getattr(sys, 'frozen', False):
    application.asset_folder = os.path.dirname(sys.executable)

app = Ursina(title='Miser 2D - Arabic')

# ----- Window Setup -----
camera.orthographic = True
camera.fov = 10
window.color = color.rgb(13, 13, 13)
Sky(texture='sand_3_1.png')

# ----- Arabic Font -----
arabic_font = 'Amiri-Regular.ttf'  # <-- put a TTF Arabic font here

def arabic(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

# ----- Constants -----
SEARCH_TIME = 5
COOLDOWN_TIME = 10

# ----- Materials -----
class MaterialType:
    Cloth = arabic('قماش')
    Iron = arabic('حديد')
    Glass = arabic('زجاج')
    Seed = arabic('بذور')
    Paper = arabic('ورق')
    Jewelry = arabic('مجوهرات')
    AncientCoin = arabic('عملة قديمة')
    Gemstone = arabic('حجر كريم')

ITEM_TEMPLATES = [
    {'name':MaterialType.Paper, 'value':6, 'material':MaterialType.Paper, 'rarity':arabic('شائع')},
    {'name':MaterialType.Cloth,'value':7,'material':MaterialType.Cloth,'rarity':arabic('شائع')},
    {'name':arabic('مسمار'),'value':8,'material':MaterialType.Iron,'rarity':arabic('غير شائع')},
    {'name':MaterialType.Iron,'value':10,'material':MaterialType.Iron,'rarity':arabic('غير شائع')},
    {'name':MaterialType.Glass,'value':9,'material':MaterialType.Glass,'rarity':arabic('غير شائع')},
    {'name':MaterialType.Jewelry,'value':25,'material':MaterialType.Jewelry,'rarity':arabic('نادر')},
    {'name':MaterialType.AncientCoin,'value':40,'material':MaterialType.Jewelry,'rarity':arabic('ملحمي')},
    {'name':MaterialType.Gemstone,'value':50,'material':MaterialType.Jewelry,'rarity':arabic('ملحمي')},
]

RARITY_MULTIPLIERS = {arabic('شائع'): 1.0, arabic('غير شائع'): 1.5, arabic('نادر'): 2.0, arabic('ملحمي'): 3.0}

# ----- Sound -----
pickup_sound = Audio('item-pickup.mp3', autoplay=False)
sell_sound = Audio('crp.mp3', autoplay=False)
error_sound = Audio('error.mp3', autoplay=False)
search_sound = Audio('search.mp3', autoplay=False)

# ----- Player -----
player = Entity(model='quad', color=color.lime, scale=(0.5,0.5), position=(0,0))
player.speed = 4
player_anim_timer = 0
player_idle_color = color.lime
player_move_color = color.green

def animate_player():
    global player_anim_timer
    player_anim_timer += time.dt * 6
    player.color = lerp(player.color, player_move_color if abs(math.sin(player_anim_timer)) > 0.5 else player_idle_color, 0.4)

def camera_follow():
    camera.position = lerp(camera.position, (player.x, player.y, -10), 6 * time.dt)

# ----- UI -----
coins = 0
inventory = []

text_color = color.rgb(10, 10, 10)
highlight_color = color.rgb(30, 30, 30)

coins_text = Text(text=arabic(f'العملات: {coins}'), font=arabic_font, position=window.top_left + Vec2(0.1,-0.05), scale=1.2, color=text_color)
inv_text   = Text(text=arabic('المخزون: []'), font=arabic_font, position=window.top + Vec2(0,-0.08), scale=1.0, color=text_color)
msg_text   = Text(text='', font=arabic_font, position=window.center, scale=1.2, color=color.azure, origin=(0,0))

progress_bar = Entity(model='quad', color=color.azure, scale=(0,0.2), position=(0,-0.4))
progress_bar.visible = False

def show_msg(text, duration=1.5):
    msg_text.text = arabic(text)
    invoke(lambda: setattr(msg_text, 'text',''), delay=duration)

def refresh_inventory():
    inv_text.text = arabic(f"المخزون: {[i['name'] for i in inventory]}")

def add_coins(amount):
    global coins
    coins += amount
    coins_text.text = arabic(f'العملات: {coins}')

def picked_up(item):
    inventory.append(item)
    pickup_sound.play()
    show_msg(f"وجدت {item['name']} ({item['rarity']})")
    refresh_inventory()

# ----- Trash Bin -----
class TrashBin(Entity):
    def __init__(self, **kwargs):
        super().__init__(model='quad', texture='trash_bin.png', scale=(0.6,0.6), **kwargs)
        self.cooldown = 0
        self.searching = False
        self.tooltip = Text(parent=camera.ui, text=arabic('[E] بحث'), font=arabic_font, scale=0.6, color=text_color)
        self.tooltip.enabled = False

    def update(self):
        if distance(player.position, self.position) < 1:
            self.tooltip.enabled = True
            self.tooltip.position = window.center + Vec2(0,-0.4)
            if self.cooldown > 0:
                self.tooltip.text = arabic(f"الانتظار: {int(self.cooldown)} ث")
            else:
                self.tooltip.text = arabic('[E] بحث')
        else:
            self.tooltip.enabled = False
        if self.cooldown > 0:
            self.cooldown -= time.dt

    def search(self):
        if self.cooldown > 0 or self.searching:
            error_sound.play()
            show_msg(arabic("لا يمكنك البحث الآن!"))
            return

        self.searching = True
        progress_bar.visible = True
        progress_bar.scale_x = 0
        search_sound.play()

        def do_search():
            r = random.random()
            if r < 0.6: rarity = arabic('شائع')
            elif r < 0.85: rarity = arabic('غير شائع')
            elif r < 0.95: rarity = arabic('نادر')
            else: rarity = arabic('ملحمي')

            valid_items = [i for i in ITEM_TEMPLATES if i['rarity'] == rarity]
            item = random.choice(valid_items)
            item_copy = dict(item)
            item_copy['value'] = int(item['value'] * RARITY_MULTIPLIERS[rarity])
            picked_up(item_copy)

            self.cooldown = COOLDOWN_TIME
            self.searching = False
            progress_bar.visible = False

        def update_bar():
            if not self.searching:
                return
            progress_bar.scale_x += (1/SEARCH_TIME) * time.dt * 10
            if progress_bar.scale_x >= 10:
                progress_bar.scale_x = 10
                do_search()
                return
            invoke(update_bar, delay=0.1)

        invoke(update_bar, delay=0.1)
        invoke(do_search, delay=SEARCH_TIME)

# ----- Vendor -----
class Vendor(Entity):
    def __init__(self, name, accepts, color_tint=color.brown, **kwargs):
        super().__init__(model='quad', color=color_tint, scale=(0.7,0.7), **kwargs)
        self.name = arabic(name)
        self.accepts = accepts
        self.tooltip = Text(parent=camera.ui, text=arabic(f'[E] بيع إلى {name}'), font=arabic_font, scale=0.6, color=color.black)
        self.tooltip.enabled = False

        self.label = Text(
            text=self.name,
            parent=scene,
            font=arabic_font,
            scale=3.0,
            color=color.black,
            origin=(0,0)
        )
        self.label.world_position = self.world_position + Vec3(0,1,0)

    def update(self):
        self.label.world_position = self.world_position + Vec3(0,1,0)
        if distance(player.position, self.position) < 1:
            self.tooltip.enabled = True
            self.tooltip.position = window.center + Vec2(0,-0.4)
        else:
            self.tooltip.enabled = False

    def sell_items(self):
        sold = 0
        for i in range(len(inventory)-1, -1, -1):
            it = inventory[i]
            if it['material'] == self.accepts:
                add_coins(it['value'])
                inventory.pop(i)
                sold += 1
        refresh_inventory()
        if sold > 0:
            sell_sound.play()
            show_msg(arabic(f"تم بيع {sold} عنصر(عناصر) إلى {self.name}"))
        else:
            error_sound.play()
            show_msg(arabic(f"{self.name} لا يشتري أغراضك"))

# ----- Trash Bins & Vendors -----
trash_bins = [TrashBin(position=(random.uniform(-5,5), random.uniform(-3,3))) for _ in range(6)]
vendors = [
    Vendor('الخياط', MaterialType.Cloth, color_tint=color.azure, position=(-6,2)),
    Vendor('الحداد', MaterialType.Iron, color_tint=color.gray, position=(6,2)),
    Vendor('صانع الزجاج', MaterialType.Glass, color_tint=color.cyan, position=(-6,-2)),
    Vendor('المزارع', MaterialType.Seed, color_tint=color.green, position=(6,-2)),
    Vendor('صانع الورق', MaterialType.Paper, color_tint=color.orange, position=(0,4)),
    Vendor('صائغ', MaterialType.Jewelry, color_tint=color.gold, position=(0,-4)),
]

# ----- Player Control -----
def update():
    camera_follow()
    move = Vec2(held_keys['d'] - held_keys['a'], held_keys['w'] - held_keys['s']).normalized()
    player.position += move * time.dt * player.speed
    if move.length() > 0:
        animate_player()

def input(key):
    if key == 'e':
        for bin in trash_bins:
            if distance(player.position, bin.position) < 1:
                bin.search()
                return
        for vendor in vendors:
            if distance(player.position, vendor.position) < 1:
                vendor.sell_items()
                return

# ----- Start -----
show_msg('استخدم WASD للتحرك، و E للبحث أو البيع.', duration=4)
app.run()
