"""Equipment selection during character creation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pygame

from character import Character
from character_creation import (
    BUTTON, BUTTON_DISABLED, GOLD, RESULT_CANCEL, RESULT_NEXT, RESULT_QUIT, TEXT,
)
from equipment import (
    Armor, Equipment, HealingPotion, RationPack, Ring, Shield, Weapon,
    dagger, greataxe, ring_of_protection, rope,
)

RESOURCE_DIR = Path(__file__).resolve().parent / "Resources"


@dataclass(frozen=True)
class ShopItem:
    label: str
    factory: Callable[[], Equipment]
    slot: str


CATALOG = (
    ShopItem("Espada longa",
             lambda: Weapon("Longsword", 15, 3, "1d8", "slashing"), "weapon"),
    ShopItem("Adaga",
             dagger, "weapon"),
    ShopItem("Espada curta",
             lambda: Weapon("Shortsword", 10, 2, "1d6", "piercing", finesse=True), "weapon"),
    ShopItem("Machado grande",
             greataxe, "weapon"),
    ShopItem("Peitoral",
             lambda: Armor("Breastplate", 400, 20, 14, "medium"), "armor"),
    ShopItem("Escudo Pipa (+3 CA)",
             lambda: Shield("Kite Shield", 100, 6, 3), "shield"),
    ShopItem("Armadura de couro",
             lambda: Armor("Leather Armor", 10, 10, 11, "light"), "armor"),
    ShopItem("Escudo redondo (+2 CA)",
             lambda: Shield("Round Shield", 10, 6, 2), "shield"),
    ShopItem("Anel de Proteção +1", ring_of_protection, "ring_left"),
    ShopItem("Anel de Proteção +1", ring_of_protection, "ring_right"),
    ShopItem("Poção de cura", HealingPotion, "backpack"),
    ShopItem("Rações (10)", RationPack, "backpack"),
    ShopItem("Corda", rope, "backpack"),
)

# The background has no weapon or shield spaces; those are drawn separately.
SLOTS = {
    "weapon": ("Arma", pygame.Rect(90, 275, 120, 115)),
    "shield": ("Escudo", pygame.Rect(90, 440, 120, 115)),
    "head": ("Cabeça", pygame.Rect(429, 76, 122, 118)),
    "shoulders": ("Ombros", pygame.Rect(287, 228, 121, 112)),
    "armor": ("Tórax", pygame.Rect(429, 329, 122, 119)),
    "waist": ("Cintura", pygame.Rect(333, 519, 141, 118)),
    "legs": ("Pernas", pygame.Rect(413, 721, 121, 129)),
    "neck": ("Pescoço", pygame.Rect(929, 162, 120, 118)),
    "hands": ("Mãos", pygame.Rect(979, 448, 122, 122)),
    "feet": ("Pés", pygame.Rect(953, 775, 121, 123)),
    "ring_left": ("Anel esquerdo", pygame.Rect(1144, 597, 117, 116)),
    "ring_right": ("Anel direito", pygame.Rect(1144, 730, 117, 118)),
    "backpack": ("Mochila", pygame.Rect(1156, 141, 285, 312)),
}
BACK_BUTTON = pygame.Rect(80, 935, 200, 50)
NEXT_BUTTON = pygame.Rect(1256, 935, 200, 50)
LIST_RECT = pygame.Rect(570, 305, 580, 520)
ROW_HEIGHT = 105
VISIBLE_ROWS = (LIST_RECT.height - 90) // ROW_HEIGHT


class EquipmentShop:
    def __init__(self, window: pygame.Surface, character: Character):
        self.window = window
        self.character = character
        self.background = pygame.image.load(
            str(RESOURCE_DIR / "Background" / "Equipar.png")
        ).convert()
        self.images: dict[Path, pygame.Surface] = {}
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 40)
        self.open_slot = None
        self.option_scroll = 0
        self.message = ""
        self.result = None
        self.initial_gold = character.gold
        self.initial_inventory = list(character.inventory)
        self.initial_equipment = (
            character.equipped_weapon, character.equipped_armor,
            character.equipped_shield, character.equipped_ring_left,
            character.equipped_ring_right,
        )

    def options(self):
        return [entry for entry in CATALOG if entry.slot == self.open_slot]

    def scroll_options(self, step):
        limit = max(0, len(self.options()) - VISIBLE_ROWS)
        self.option_scroll = max(0, min(limit, self.option_scroll + step))

    def open_slot_at(self, pos):
        for key, (_, rect) in SLOTS.items():
            if rect.collidepoint(pos):
                self.open_slot = key
                self.option_scroll = 0
                self.message = ""
                return

    def owned(self, entry):
        return {
            "weapon": self.character.equipped_weapon,
            "armor": self.character.equipped_armor,
            "shield": self.character.equipped_shield,
            "ring_left": self.character.equipped_ring_left,
            "ring_right": self.character.equipped_ring_right,
        }.get(entry.slot) is not None

    def buy(self, entry):
        if self.owned(entry):
            self.message = "Este espaço já está equipado."
            return
        item = entry.factory()
        if not self.character.remove_gold(item.cost):
            self.message = "Ouro insuficiente."
            return
        self.character.add_item(item)
        if entry.slot != "backpack":
            previous_weapon = self.character.equipped_weapon
            previous_shield = self.character.equipped_shield
            self.character.equip(item, entry.slot if isinstance(item, Ring) else None)
        self.message = f"{entry.label} comprado."
        if entry.slot != "backpack":
            if previous_shield is not None and self.character.equipped_shield is None:
                self.message += " Escudo desequipado."
            elif previous_weapon is not None and self.character.equipped_weapon is None:
                self.message += " Arma desequipada."

    def rollback(self):
        self.character.gold = self.initial_gold
        self.character.inventory = self.initial_inventory[:]
        (self.character.equipped_weapon, self.character.equipped_armor,
         self.character.equipped_shield, self.character.equipped_ring_left,
         self.character.equipped_ring_right) = self.initial_equipment

    def text(self, text, pos, font=None, color=TEXT, center=False):
        surface = (font or self.font).render(text, True, color)
        rect = surface.get_rect(center=pos) if center else surface.get_rect(topleft=pos)
        self.window.blit(surface, rect)

    def button(self, rect, label):
        pygame.draw.rect(self.window, BUTTON, rect, border_radius=6)
        pygame.draw.rect(self.window, GOLD, rect, 2, border_radius=6)
        self.text(label, rect.center, center=True)

    def draw_item_image(self, item, rect):
        path = item.image
        if path is None:
            pygame.draw.rect(self.window, BUTTON_DISABLED, rect)
            pygame.draw.rect(self.window, GOLD, rect, 1)
            self.text("Sem", (rect.centerx, rect.centery - 10), self.small_font, center=True)
            self.text("imagem", (rect.centerx, rect.centery + 10), self.small_font, center=True)
            return
        if path not in self.images:
            self.images[path] = pygame.transform.smoothscale(
                pygame.image.load(str(path)).convert_alpha(), (88, 88)
            )
        self.window.blit(self.images[path], rect)

    def draw(self):
        self.window.blit(self.background, (0, 0))
        self.text(f"Ouro: {self.character.gold:g} po", (70, 65), self.title_font, GOLD)
        self.text(f"CA: {self.character.get_armor_class()}", (70, 105), self.font, GOLD)
        self.text("Clique em um espaço para comprar", (70, 145), self.small_font)
        for key in ("weapon", "shield"):
            label, rect = SLOTS[key]
            self.text(label, (rect.centerx, rect.y - 20), center=True)
            pygame.draw.rect(self.window, (20, 14, 10), rect)
            pygame.draw.rect(self.window, GOLD, rect, 2)

        for slot in ("weapon", "armor", "shield", "ring_left", "ring_right"):
            item = getattr(self.character, f"equipped_{slot}")
            if item is not None:
                rect = SLOTS[slot][1]
                self.draw_item_image(item, pygame.Rect(0, 0, 88, 88).move(
                    rect.centerx - 44, rect.centery - 44))
        backpack_items = []
        for entry in CATALOG:
            if entry.slot == "backpack":
                item = entry.factory()
                count = self.character.count_item(item.name)
                if count:
                    backpack_items.append((item, count))
        for index, (item, count) in enumerate(backpack_items[:4]):
            pos = (1188 + (index % 2) * 108, 230 + (index // 2) * 110)
            self.draw_item_image(item, pygame.Rect(*pos, 88, 88))
            self.text(f"x{count}", (pos[0] + 44, pos[1] + 97), center=True)
        if len(backpack_items) > 4:
            self.text(f"+{len(backpack_items) - 4} tipos",
                      (SLOTS["backpack"][1].centerx, 180), self.small_font, GOLD, True)

        if self.message:
            self.text(self.message, (768, 918), self.small_font, GOLD, True)
        self.button(BACK_BUTTON, "Voltar")
        self.button(NEXT_BUTTON, "Prosseguir")
        if self.open_slot:
            self.draw_list()

    def draw_list(self):
        pygame.draw.rect(self.window, (20, 14, 10), LIST_RECT, border_radius=6)
        pygame.draw.rect(self.window, GOLD, LIST_RECT, 2, border_radius=6)
        self.text(SLOTS[self.open_slot][0], (LIST_RECT.x + 20, LIST_RECT.y + 15),
                  self.title_font, GOLD)
        self.text("Clique para comprar   |   Roda: rolar   |   Esc: fechar",
                  (LIST_RECT.x + 20, LIST_RECT.y + 55), self.small_font)
        options = self.options()
        if not options:
            self.text("Nenhum equipamento disponível.", (LIST_RECT.x + 20, LIST_RECT.y + 115))
        for index, entry in enumerate(options[self.option_scroll:self.option_scroll + VISIBLE_ROWS]):
            rect = self.row_rect(index)
            item = entry.factory()
            disabled = self.owned(entry) or self.character.gold < item.cost
            pygame.draw.rect(self.window, BUTTON_DISABLED if disabled else BUTTON, rect)
            self.draw_item_image(item, pygame.Rect(rect.x + 5, rect.y + 5, 88, 88))
            self.text(entry.label, (rect.x + 108, rect.y + 14))
            equipped = getattr(self.character, f"equipped_{entry.slot}", None)
            if self.owned(entry):
                status = "Equipado" if equipped.name == item.name else "Espaço ocupado"
            else:
                status = f"{item.cost:g} po"
            if not self.owned(entry) and self.character.gold < item.cost:
                status += " — ouro insuficiente"
            self.text(status, (rect.x + 108, rect.y + 51), self.small_font, GOLD)

    @staticmethod
    def row_rect(index):
        return pygame.Rect(LIST_RECT.x + 15, LIST_RECT.y + 90 + index * ROW_HEIGHT,
                           LIST_RECT.width - 30, 98)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.rollback()
            self.result = RESULT_QUIT
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and (
            BACK_BUTTON.collidepoint(event.pos) or NEXT_BUTTON.collidepoint(event.pos)
        ):
            if BACK_BUTTON.collidepoint(event.pos):
                self.rollback()
                self.result = RESULT_CANCEL
            else:
                self.result = RESULT_NEXT
        elif self.open_slot:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.open_slot = None
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN):
                self.scroll_options(-1 if event.key == pygame.K_UP else 1)
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll_options(-event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not LIST_RECT.collidepoint(event.pos):
                    self.open_slot = None
                    self.open_slot_at(event.pos)
                else:
                    options = self.options()[self.option_scroll:self.option_scroll + VISIBLE_ROWS]
                    for index, entry in enumerate(options):
                        if self.row_rect(index).collidepoint(event.pos):
                            self.buy(entry)
                            break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.open_slot_at(event.pos)

    def run(self):
        clock = pygame.time.Clock()
        while self.result is None:
            self.draw()
            pygame.display.flip()
            for event in pygame.event.get():
                self.handle_event(event)
                if self.result is not None:
                    break
            clock.tick(60)
        return self.result
