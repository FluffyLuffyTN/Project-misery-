# Miser 2D - Vendor Text Visibility Fix Only
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'load-display pandagl')

from ursina import *
import random, os, sys, math

# ----- Asset Folder (for EXE builds) -----
if getattr(sys, 'frozen', False):
    application.asset_folder = os.path.dirname(sys.executable)

app = Ursina(title='Miser 2D')

# ----- Window Setup -----
camera.orthographic = True
camera.fov = 10
window.color = color.rgb(13, 13, 13)  # Keep original white background
Sky(texture='sand_3_1.png')

# ----- Constants -----
SEARCH_TIME = 5
COOLDOWN_TIME = 10

# ----- Materials -----
class MaterialType:
    Cloth = 'Cloth'
    Iron = 'Iron'
    Glass = 'Glass'
    Seed = 'Seed'
    Paper = 'Paper'
    Jewelry = 'Jewelry'
    AncientCoin = 'Ancient Coin'
    Gemstone = 'Gemstone'

ITEM_TEMPLATES = [
    {'name':'Paper', 'value':6, 'material':MaterialType.Paper, 'rarity':'Common'},
    {'name':'Cloth','value':7,'material':MaterialType.Cloth,'rarity':'Common'},
    {'name':'Nail','value':8,'material':MaterialType.Iron,'rarity':'Uncommon'},
    {'name':'Iron','value':10,'material':MaterialType.Iron,'rarity':'Uncommon'},
    {'name':'Glass','value':9,'material':MaterialType.Glass,'rarity':'Uncommon'},
    {'name':'Jewelry','value':25,'material':MaterialType.Jewelry,'rarity':'Rare'},
    {'name':'Ancient Coin','value':40,'material':MaterialType.Jewelry,'rarity':'Epic'},
    {'name':'Gemstone','value':50,'material':MaterialType.Jewelry,'rarity':'Epic'},
]

RARITY_MULTIPLIERS = {'Common': 1.0, 'Uncommon': 1.5, 'Rare': 2.0, 'Epic': 3.0}

# ----- Sound -----
pickup_sound = Audio('item-pickup.mp3', autoplay=False)
sell_sound = Audio('crp.mp3', autoplay=False)
error_sound = Audio('error.mp3', autoplay=False)
search_sound = Audio('search.mp3', autoplay=False)

# ----- Player -----
player = Entity(model='quad', color=color.lime, scale=(0.5, 0.5), position=(0, 0))
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

coins_text = Text(text=f'Coins: {coins}', position=window.top_left + Vec2(0.1,-0.05), scale=1.2, color=text_color)
inv_text = Text(text='Inventory: []', position=window.top + Vec2(0,-0.08), scale=1.0, color=text_color)
msg_text = Text(text='', position=window.center, scale=1.2, color=color.azure, origin=(0,0))

progress_bar = Entity(model='quad', color=color.azure, scale=(0,0.2), position=(0,-0.4))
progress_bar.visible = False

def show_msg(text, duration=1.5):
    msg_text.text = text
    invoke(lambda: setattr(msg_text, 'text',''), delay=duration)

def refresh_inventory():
    inv_text.text = f"Inventory: {[i['name'] for i in inventory]}"

def add_coins(amount):
    global coins
    coins += amount
    coins_text.text = f'Coins: {coins}'

def picked_up(item):
    inventory.append(item)
    pickup_sound.play()
    show_msg(f"Found {item['name']} ({item['rarity']})", duration=2)
    refresh_inventory()

# ----- Trash Bin -----

class TrashBin(Entity):
    def __init__(self, **kwargs):
        super().__init__(model='quad', texture='trash_bin.png', scale=(0.6,0.6), **kwargs)
        self.cooldown = 0
        self.searching = False
        self.tooltip = Text(parent=camera.ui, text='[E] Search', scale=0.6, color=text_color)
        self.tooltip.enabled = False

    def update(self):
        if distance(player.position, self.position) < 1:
            self.tooltip.enabled = True
            self.tooltip.position = window.center + Vec2(0, -0.4)
            if self.cooldown > 0:
                self.tooltip.text = f"Cooldown: {int(self.cooldown)}s"
            else:
                self.tooltip.text = "[E] Search"
        else:
            self.tooltip.enabled = False

        if self.cooldown > 0:
            self.cooldown -= time.dt

    def search(self):
        if self.cooldown > 0 or self.searching:
            error_sound.play()
            show_msg("Can't search yet!")
            return

        search_sound.play()  # <-- plays search sound immediately

        self.searching = True
        progress_bar.visible = True
        progress_bar.scale_x = 0

        def do_search():
            r = random.random()
            if r < 0.6: rarity = 'Common'
            elif r < 0.85: rarity = 'Uncommon'
            elif r < 0.95: rarity = 'Rare'
            else: rarity = 'Epic'

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
        self.name = name
        self.accepts = accepts
        self.tooltip = Text(parent=camera.ui, text=f'[E] Sell to {name}', scale=0.6, color=color.black)
        self.tooltip.enabled = False
        
        # ---- FIX: text not parented to vendor, so scale is real ----
        self.label = Text(
            text=name,
            parent=scene,               # NOT self
            scale=3.0,                  # big enough now
            color=color.black,
            origin=(0,0),
        )
        self.label.world_position = self.world_position + Vec3(0, 1, 0)  # above vendor

    def update(self):
        # Move label with vendor
        self.label.world_position = self.world_position + Vec3(0, 1, 0)

        if distance(player.position, self.position) < 1:
            self.tooltip.enabled = True
            self.tooltip.position = window.center + Vec2(0, -0.4)
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
            show_msg(f"Sold {sold} item(s) to {self.name}")
        else:
            error_sound.play()
            show_msg(f"{self.name} doesn't buy your items")

# ----- Trash Bins & Vendors -----
trash_bins = [TrashBin(position=(random.uniform(-5,5), random.uniform(-3,3))) for _ in range(6)]
vendors = [
    Vendor('Tailor', MaterialType.Cloth, color_tint=color.azure, position=(-6, 2)),
    Vendor('Blacksmith', MaterialType.Iron, color_tint=color.gray, position=(6, 2)),
    Vendor('Glassworker', MaterialType.Glass, color_tint=color.cyan, position=(-6, -2)),
    Vendor('Farmer', MaterialType.Seed, color_tint=color.green, position=(6, -2)),
    Vendor('Papermaker', MaterialType.Paper, color_tint=color.orange, position=(0, 4)),
    Vendor('Jeweler', MaterialType.Jewelry, color_tint=color.gold, position=(0, -4)),
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
show_msg('Use WASD to move, E to search or sell.', duration=4)
app.run()

