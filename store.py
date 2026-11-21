"""Generic store/shop for the game."""

from pathlib import Path
from typing import Callable, Iterable

import pygame

from character_creation import BUTTON, BUTTON_DISABLED, GOLD, TEXT
from equipment import Armor, Equipment, Shield, Weapon
from party import Party

PANEL = pygame.Rect(50, 35, 700, 825)
CATEGORY_BUTTON = pygame.Rect(75, 195, 190, 48)
SELL_BUTTON = pygame.Rect(275, 195, 190, 48)
MEMBER_PREVIOUS = pygame.Rect(75, 270, 50, 45)
MEMBER_NEXT = pygame.Rect(615, 270, 50, 45)
LIST_RECT = pygame.Rect(75, 355, 650, 435)
SCROLL_UP = pygame.Rect(677, 355, 48, 48)
SCROLL_DOWN = pygame.Rect(677, 742, 48, 48)
EXIT_BUTTON = pygame.Rect(1255, 940, 250, 52)
ROW_HEIGHT = 53
VISIBLE_ROWS = LIST_RECT.height // ROW_HEIGHT


def gold_text(amount: float) -> str:
    return f"{amount:.4f}".rstrip("0").rstrip(".")


class Store:
    """
    Loja genérica.

    Exemplo de uso:
        Store(window, party,
              title="Edrick, o Compra-Tudo",
              greeting="Tenho tudo o que precisa!",
              subtitle="Itens gerais para aventureiros.",
              categories={
                  "general": ("Mercadorias", (torch, rope, crowbar, shovel, lantern)),
              },
              background_path=BACKGROUND)
    """

    def __init__(
        self,
        window: pygame.Surface,
        party: Party,
        *,
        title: str,
        greeting: str,
        subtitle: str,
        categories: dict[str, tuple[str, Iterable[Callable[[], Equipment]]]],
        background_path: Path,
        allow_sell: bool = True,
    ):
        self.window = window
        self.party = party
        self.title_text = title
        self.greeting = greeting
        self.subtitle = subtitle
        self.categories = categories
        self.allow_sell = allow_sell

        # Carrega fundo
        image = pygame.image.load(str(background_path)).convert()
        self.background = pygame.transform.smoothscale(image, window.get_size())

        # Estado
        self.category_keys = list(categories.keys())
        self.mode = self.category_keys[0]  # Primeira categoria por padrão
        self.member_index = 0
        self.scroll = 0
        self.message = ""
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 40)
        self.images: dict[Path, pygame.Surface] = {}

    # ---------------- Propriedades ---------------- #
    @property
    def member(self):
        return self.party.members[self.member_index]

    def category_label(self, key: str) -> str:
        return self.categories[key][0]

    def items(self):
        if self.mode == "sell":
            return [item for item in self.member.inventory
                    if isinstance(item, (Equipment, Weapon, Armor, Shield))]
        _, factories = self.categories[self.mode]
        return [factory() for factory in factories]

    def max_scroll(self):
        return max(0, len(self.items()) - VISIBLE_ROWS)

    # ---------------- Ações ---------------- #
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

    # ---------------- Desenho ---------------- #
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
        self.text(self.title_text, (75, 52), self.title_font, GOLD)
        self.text(self.greeting, (75, 100))
        self.text(self.subtitle, (75, 136), self.small_font)

        # Botões de categoria (dinâmicos)
        button_rects = []
        for i, key in enumerate(self.category_keys):
            rect = pygame.Rect(75 + i * 200, 195, 190, 48)
            button_rects.append((rect, key))
            self.button(rect, self.category_label(key), self.mode == key)
        if self.allow_sell:
            sell_rect = pygame.Rect(75 + len(self.category_keys) * 200, 195, 190, 48)
            self.button(sell_rect, "Vender", self.mode == "sell")

        # Navegação de membros
        self.button(MEMBER_PREVIOUS, "<")
        self.button(MEMBER_NEXT, ">")
        self.text(f"Integrante: {self.member.name}", (370, 292), self.font, GOLD, True)
        self.text(f"Ouro do grupo: {gold_text(self.party.total_gold())} po",
                  (75, 325), self.small_font, GOLD)
        self.text("Clique para vender (75%)" if self.mode == "sell" else "Clique para comprar",
                  (440, 325), self.small_font)

        # Lista
        pygame.draw.rect(self.window, BUTTON_DISABLED, LIST_RECT)
        pygame.draw.rect(self.window, GOLD, LIST_RECT, 2)
        entries = self.items()
        if not entries:
            self.text("Nenhum item disponível.", (95, 375), self.small_font)
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
        self.button(EXIT_BUTTON, "Sair da loja")

    # ---------------- Eventos ---------------- #
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

            # Botões de categoria
            for i, key in enumerate(self.category_keys):
                rect = pygame.Rect(75 + i * 200, 195, 190, 48)
                if rect.collidepoint(pos):
                    self.mode, self.scroll, self.message = key, 0, ""
                    return None
            if self.allow_sell and pygame.Rect(
                75 + len(self.category_keys) * 200, 195, 190, 48
            ).collidepoint(pos):
                self.mode, self.scroll, self.message = "sell", 0, ""
                return None

            # Navegação de membros
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

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            self.draw()
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                result = self.handle_event(event)
                if result == "exit":
                    running = False
                    break
            clock.tick(60)
        return "exit"