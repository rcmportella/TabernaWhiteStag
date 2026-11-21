"""Ragnar's weapon and armor shop in Guluvia."""

from pathlib import Path

import pygame

import equipment
from character_creation import BUTTON, BUTTON_DISABLED, GOLD, TEXT
from equipment import Armor, Equipment, Shield, Weapon
from party import Party

BACKGROUND = Path(__file__).resolve().parent / "Resources" / "Background" / "LojadeArmasdeGuluvia.png"

WEAPONS = (
    equipment.dagger, equipment.mace, equipment.club, equipment.greatclub,
    equipment.handaxe, equipment.javelin, equipment.light_hammer, equipment.sickle,
    equipment.quarterstaff, equipment.spear, equipment.dart, equipment.light_crossbow,
    equipment.short_bow, equipment.sling, equipment.battleaxe, equipment.flail,
    equipment.glaive, equipment.greataxe, equipment.greatsword, equipment.halberd,
    equipment.lance, equipment.longsword, equipment.maul, equipment.morningstar,
    equipment.pike, equipment.rapier, equipment.scimitar, equipment.shortsword,
    equipment.trident, equipment.warhammer, equipment.warpick, equipment.whip,
    equipment.handcrossbow, equipment.heavy_crossbow, equipment.longbow,
)
ARMORS = (
    equipment.padded_armor, equipment.leather_armor, equipment.studded_leather_armor,
    equipment.hide_armor, equipment.chain_shirt, equipment.scale_mail,
    equipment.breastplate, equipment.half_plate_armor, equipment.ring_mail,
    equipment.chain_mail, equipment.splint_armor, equipment.plate_armor,
    equipment.small_shield, equipment.large_shield, equipment.kite_shield,
)

PANEL = pygame.Rect(50, 35, 700, 825)
WEAPONS_BUTTON = pygame.Rect(75, 195, 190, 48)
ARMORS_BUTTON = pygame.Rect(275, 195, 190, 48)
SELL_BUTTON = pygame.Rect(475, 195, 190, 48)
MEMBER_PREVIOUS = pygame.Rect(75, 270, 50, 45)
MEMBER_NEXT = pygame.Rect(615, 270, 50, 45)
LIST_RECT = pygame.Rect(75, 355, 650, 435)
SCROLL_UP = pygame.Rect(677, 355, 48, 48)
SCROLL_DOWN = pygame.Rect(677, 742, 48, 48)
EXIT_BUTTON = pygame.Rect(1255, 940, 250, 52)
ROW_HEIGHT = 53
VISIBLE_ROWS = LIST_RECT.height // ROW_HEIGHT


def gold_text(amount):
    return f"{amount:.4f}".rstrip("0").rstrip(".")


class Blacksmith:
    def __init__(self, window: pygame.Surface, party: Party):
        self.window = window
        image = pygame.image.load(str(BACKGROUND)).convert()
        self.background = pygame.transform.smoothscale(image, window.get_size())
        self.party = party
        self.mode = "weapons"
        self.member_index = 0
        self.scroll = 0
        self.message = ""
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 40)
        self.images: dict[Path, pygame.Surface] = {}

    @property
    def member(self):
        return self.party.members[self.member_index]

    def items(self):
        if self.mode == "sell":
            return [item for item in self.member.inventory
                    if isinstance(item, (Weapon, Armor, Shield))]
        factories = WEAPONS if self.mode == "weapons" else ARMORS
        return [factory() for factory in factories]

    def max_scroll(self):
        return max(0, len(self.items()) - VISIBLE_ROWS)

    def buy(self, item: Equipment):
        if not self.party.purchase_item(item, self.member):
            self.message = "Ouro do grupo insuficiente."
            return
        self.message = f"{item.name} comprado para {self.member.name}."

    def sell(self, item: Equipment):
        self.member.remove_item(item)
        self.party.leader.add_gold(item.cost * 0.75)
        self.scroll = min(self.scroll, self.max_scroll())
        self.message = f"{item.name} vendido por {gold_text(item.cost * 0.75)} po."

    def text(self, text, pos, font=None, color=TEXT, center=False):
        surface = (font or self.font).render(text, True, color)
        rect = surface.get_rect(center=pos) if center else surface.get_rect(topleft=pos)
        self.window.blit(surface, rect)

    def button(self, rect, label, selected=False):
        pygame.draw.rect(self.window, (130, 90, 40) if selected else BUTTON,
                         rect, border_radius=6)
        pygame.draw.rect(self.window, GOLD, rect, 2, border_radius=6)
        self.text(label, rect.center, center=True)

    @staticmethod
    def row_rect(index):
        return pygame.Rect(85, LIST_RECT.y + 5 + index * ROW_HEIGHT, 580, ROW_HEIGHT - 4)

    def draw_item_image(self, item, rect):
        path = item.image
        if path is None:
            self.text("—", rect.center, self.small_font, GOLD, True)
            return
        if path not in self.images:
            self.images[path] = pygame.transform.smoothscale(
                pygame.image.load(str(path)).convert_alpha(), rect.size)
        self.window.blit(self.images[path], rect)

    def draw(self):
        self.window.blit(self.background, (0, 0))
        overlay = pygame.Surface(PANEL.size, pygame.SRCALPHA)
        overlay.fill((20, 14, 10, 235))
        self.window.blit(overlay, PANEL)
        pygame.draw.rect(self.window, GOLD, PANEL, 2, border_radius=8)
        self.text("Ragnar, o ferreiro", (75, 52), self.title_font, GOLD)
        self.text("Bem-vindo à minha forja, aventureiro!", (75, 100))
        self.text("Escolha suas armas e armaduras, ou mostre-me o que quer vender.",
                  (75, 136), self.small_font)
        for rect, label, mode in ((WEAPONS_BUTTON, "Armas", "weapons"),
                                  (ARMORS_BUTTON, "Armaduras", "armor"),
                                  (SELL_BUTTON, "Vender", "sell")):
            self.button(rect, label, self.mode == mode)
        self.button(MEMBER_PREVIOUS, "<")
        self.button(MEMBER_NEXT, ">")
        self.text(f"Integrante: {self.member.name}", (370, 292), self.font, GOLD, True)
        self.text(f"Ouro do grupo: {gold_text(self.party.total_gold())} po",
                  (75, 325), self.small_font, GOLD)
        self.text("Clique para vender (75%)" if self.mode == "sell" else "Clique para comprar",
                  (440, 325), self.small_font)
        pygame.draw.rect(self.window, BUTTON_DISABLED, LIST_RECT)
        pygame.draw.rect(self.window, GOLD, LIST_RECT, 2)
        entries = self.items()
        if not entries:
            self.text("Nenhuma arma ou armadura para vender.", (95, 375), self.small_font)
        for index, item in enumerate(entries[self.scroll:self.scroll + VISIBLE_ROWS]):
            rect = self.row_rect(index)
            pygame.draw.rect(self.window, BUTTON, rect, border_radius=4)
            self.draw_item_image(item, pygame.Rect(rect.x + 4, rect.y + 4, 40, 40))
            equipped = any(item is getattr(self.member, f"equipped_{slot}")
                           for slot in ("weapon", "armor", "shield"))
            name = f"{item.name} (equipado)" if equipped else item.name
            self.text(name, (rect.x + 52, rect.y + 13), self.small_font)
            price = item.cost * 0.75 if self.mode == "sell" else item.cost
            self.text(f"{gold_text(price)} po", (rect.right - 90, rect.y + 13),
                      self.small_font, GOLD)
        self.button(SCROLL_UP, "^")
        self.button(SCROLL_DOWN, "v")
        self.text("Roda, setas ou botões: rolar", (75, 802), self.small_font)
        if self.message:
            self.text(self.message, (75, 830), self.small_font, GOLD)
        self.button(EXIT_BUTTON, "Voltar à cidade")

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.max_scroll(), self.scroll - event.y))
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN):
            step = -1 if event.key == pygame.K_UP else 1
            self.scroll = max(0, min(self.max_scroll(), self.scroll + step))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if EXIT_BUTTON.collidepoint(pos):
                return "exit"
            for rect, mode in ((WEAPONS_BUTTON, "weapons"), (ARMORS_BUTTON, "armor"),
                               (SELL_BUTTON, "sell")):
                if rect.collidepoint(pos):
                    self.mode, self.scroll, self.message = mode, 0, ""
                    return None
            if MEMBER_PREVIOUS.collidepoint(pos) or MEMBER_NEXT.collidepoint(pos):
                step = -1 if MEMBER_PREVIOUS.collidepoint(pos) else 1
                self.member_index = (self.member_index + step) % len(self.party)
                self.scroll, self.message = 0, ""
            elif SCROLL_UP.collidepoint(pos) or SCROLL_DOWN.collidepoint(pos):
                step = -1 if SCROLL_UP.collidepoint(pos) else 1
                self.scroll = max(0, min(self.max_scroll(), self.scroll + step))
            else:
                for index, item in enumerate(self.items()[self.scroll:self.scroll + VISIBLE_ROWS]):
                    if self.row_rect(index).collidepoint(pos):
                        if self.mode == "sell":
                            self.sell(item)
                        else:
                            self.buy(item)
                        break
        return None
