# Miser 2D Top-Down - Ursina
# Requirements: Python 3.8+, pip install ursina
# Run: python miser_2d.py

from ursina import *
import random

app = Ursina()

# ----- Data Definitions -----
class MaterialType:
    Cloth = 'Cloth'
    Iron = 'Iron'
    Glass = 'Glass'
    Seed = 'Seed'
    Paper = 'Paper'
    Jewelry = 'Jewelry'

ITEM_TEMPLATES = [
    {'name':'Paper',  'value':6,  'material':MaterialType.Paper},
    {'name':'Nail',   'value':8,  'material':MaterialType.Iron},
    {'name':'Cloth',  'value':7,  'material':MaterialType.Cloth},
    {'name':'Glass',  'value':9,  'material':MaterialType.Glass},
    {'name':'Seed',   'value':4,  'material':MaterialType.Seed},
    {'name':'Jewelry','value':25, 'material':MaterialType.Jewelry},
    {'name':'Iron',   'value':10, 'material':MaterialType.Iron},
]

# ----- Player & Inventory -----
player = Entity(model='quad', color=color.green, scale=(0.5,0.5), position=(0,0))
player.speed = 4
inventory = []
coins = 0

coins_text = Text(text=f'Coins: {coins}', position=window.top_left + Vec2(0.1,-0.05), scale=1.2, background=True)
inv_text = Text(text='Inventory: []', position=window.top + Vec2(0,-0.05), scale=1.1, background=True)

def refresh_inventory():
    inv_names = [item['name'] for item in inventory]
    inv_text.text = f"Inventory: {inv_names}"

def add_coins(amount):
    global coins
    coins += amount
    coins_text.text = f'Coins: {coins}'

# ----- Trash Bin -----
class TrashBin(Entity):
    def __init__(self, **kwargs):
        super().__init__(model='quad', color=color.gray, scale=(0.6,0.6), **kwargs)
        self.items = ITEM_TEMPLATES.copy()
        self.tooltip = Text(parent=camera.ui, text='[E] Search', scale=0.6, color=color.white)
        self.tooltip.enabled = False

    def update(self):
        if distance(player.position, self.position) < 1:
            self.tooltip.enabled = True
            self.tooltip.position = self.position + Vec2(0,0.5)
        else:
            self.tooltip.enabled = False

    def search(self):
        r = random.random()
        if r < 0.06:
            item = next(i for i in ITEM_TEMPLATES if i['name']=='Jewelry')
        else:
            item = random.choice(self.items)
        picked_up(item)

def picked_up(item):
    inventory.append(item)
    show_msg(f"Picked up {item['name']}")
    refresh_inventory()

# ----- Vendors -----
class Vendor(Entity):
    def __init__(self, name, accepts, **kwargs):
        super().__init__(model='quad', color=color.brown, scale=(0.7,0.7), **kwargs)
        self.name = name
        self.accepts = accepts
        self.tooltip = Text(parent=camera.ui, text=f'[E] Sell to {name}', scale=0.6, color=color.white)
        self.tooltip.enabled = False

    def update(self):
        if distance(player.position, self.position) < 1:
            self.tooltip.enabled = True
            self.tooltip.position = self.position + Vec2(0,0.5)
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
            show_msg(f"Sold {sold} item(s) to {self.name}")
        else:
            show_msg(f"{self.name} doesn't buy your items")

# ----- UI Messages -----
msg_text = Text(text='', position=window.center, scale=1.2, color=color.azure, origin=(0,0))

def show_msg(text, duration=1.5):
    msg_text.text = text
    invoke(lambda: setattr(msg_text, 'text',''), delay=duration)

# ----- Map Objects -----
trash_bins = [TrashBin(position=(random.uniform(-5,5), random.uniform(-3,3))) for _ in range(8)]
vendors = [
    Vendor('Tailor', MaterialType.Cloth, position=(-6,2)),
    Vendor('Blacksmith', MaterialType.Iron, position=(6,2)),
    Vendor('Glassworker', MaterialType.Glass, position=(-6,-2)),
    Vendor('Farmer', MaterialType.Seed, position=(6,-2)),
    Vendor('Papermaker', MaterialType.Paper, position=(0,4)),
    Vendor('Jeweler', MaterialType.Jewelry, position=(0,-4)),
]

# ----- Player Movement -----
def update():
    # movement
    if held_keys['w']: player.y += time.dt * player.speed
    if held_keys['s']: player.y -= time.dt * player.speed
    if held_keys['a']: player.x -= time.dt * player.speed
    if held_keys['d']: player.x += time.dt * player.speed

def input(key):
    if key=='e':
        for bin in trash_bins:
            if distance(player.position, bin.position)<1:
                bin.search()
                return
        for vendor in vendors:
            if distance(player.position, vendor.position)<1:
                vendor.sell_items()
                return

# ----- Start -----
show_msg('Use WASD to move, E to search or sell.', duration=4)
app.run()
