# dialog.py
"""Reusable branching dialog for NPCs and menus."""

from dataclasses import dataclass, field
from textwrap import wrap
from typing import Callable, Optional

import pygame

from character_creation import BUTTON, BUTTON_DISABLED, GOLD, TEXT


@dataclass
class Choice:
    """A selectable option in a dialog node.

    ``target`` is either the id of the next node, a callable receiving the
    dialog (which may return a node id or close it), or None to close it.
    """
    label: str
    target: Optional[str | Callable] = None
    enabled: bool = True
    # optional short hint shown to the right of the label
    hint: str = ""

@dataclass
class DialogNode:
    """One screen of a dialog.

    ``lines`` is a list of ``(speaker, text)`` tuples so a single node can
    contain a hero line followed by an NPC line (like Theron's intro).
    ``choices`` are laid out automatically under the text. A node with an
    empty ``choices`` list and a non-None ``auto_next`` behaves like a
    "continue" page.
    """
    id: str
    lines: list[tuple[str, str]] = field(default_factory=list)
    choices: list[Choice] = field(default_factory=list)
    auto_next: Optional[str] = None            # for "Continuar" pages
    portrait: Optional[pygame.Surface] = None  # per-node override
    on_enter: Optional[Callable] = None        # run on node activation
    close_label: str = "Nos vemos mais tarde"  # auto-added if close_allowed
    close_allowed: bool = True

PANEL = pygame.Rect(330, 170, 876, 660)
PORTRAIT = pygame.Rect(145, 210, 165, 165)
CLOSE_BUTTON = pygame.Rect(1115, 190, 65, 45)
TEXT_LEFT = 370
TEXT_TOP = 280
LINE_HEIGHT = 32
CHOICE_HEIGHT = 50
CHOICE_GAP = 10
CHOICE_TOP = 587


class Dialog:
    def __init__(self, nodes: dict[str, DialogNode], start: str,
                 background: pygame.Surface, default_portrait: pygame.Surface | None = None,
                 on_close: Callable | None = None, host=None):
        self.nodes = {n.id: n for n in nodes}
        self.start = start
        self.background = background
        self.default_portrait = default_portrait
        self.current: DialogNode | None = None
        self.portrait = default_portrait
        self.open = False
        self.message = ""
        self.on_close = on_close
        self.host = host
        self._choice_rects: list[tuple[pygame.Rect, Choice]] = []
        self._next_rect: pygame.Rect | None = None
        self._close_rect = CLOSE_BUTTON
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 48)

    # ---- lifecycle --------------------------------------------------
    def start_dialog(self, node_id: str | None = None):
        self.open = True
        self.message = ""
        self._goto(node_id or self.start)

    def close(self):
        self.open = False
        self.current = None
        if self.on_close:
            self.on_close(self)

    def _goto(self, node_id):
        node = self.nodes[node_id]
        self.current = node
        self.portrait = node.portrait or self.default_portrait
        self._choice_rects.clear()
        self._next_rect = None
        if node.on_enter:
            node.on_enter(self)
        self.message = ""          # <-- clear AFTER on_enter

    # ---- text helpers ----------------------------------------------
    def wrapped_lines(self) -> list[tuple[str, str, pygame.Surface | None]]:
        """Return (speaker, line, portrait_for_line) for all text in the node."""
        out = []
        for speaker, text in self.current.lines:
            for part in wrap(text, 65) or [""]:
                out.append((speaker, part, self.portrait))
        return out

    def _layout_choices(self):
        self._choice_rects.clear()
        y = CHOICE_TOP
        for choice in self.current.choices:
            rect = pygame.Rect(TEXT_LEFT, y, 795, CHOICE_HEIGHT)
            self._choice_rects.append((rect, choice))
            y += CHOICE_HEIGHT + CHOICE_GAP

    # ---- input ------------------------------------------------------
    def handle_event(self, event) -> str | None:
        """Return an action string for the host, or None.

        Returning ``"closed"`` when the dialog shuts itself lets the host
        distinguish "still open" from "user left".
        """
        if not self.open or self.current is None:
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return "closed"

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self._close_rect.collidepoint(event.pos):
            self.close()
            return "closed"

        if self._next_rect is not None and self._next_rect.collidepoint(event.pos):
            self._goto(self.current.auto_next)
            return None

        for rect, choice in self._choice_rects:
            if rect.collidepoint(event.pos):
                return self._choose(choice)
        return None

    def _choose(self, choice: Choice) -> str | None:
        if not choice.enabled:
            return None
        target = choice.target
        if target is None:
            self.close()
            return "closed"
        if callable(target):
            result = target(self)
            if not self.open:
                return "closed"
            if isinstance(result, str):
                self._goto(result)
                return result
            return None
        if isinstance(target, str):
            self._goto(target)
            return target
        return None

    # ---- drawing ----------------------------------------------------
    def draw(self, window: pygame.Surface):
        if not self.open or self.current is None:
            return
        window.blit(self.background, (0, 0))
        pygame.draw.rect(window, (20, 14, 10), PANEL, border_radius=8)
        pygame.draw.rect(window, GOLD, PANEL, 2, border_radius=8)
        self._button(window, self._close_rect, "X")

        # portrait
        if self.portrait is None:
            pygame.draw.rect(window, BUTTON_DISABLED, PORTRAIT)
            self._text(window, "—", PORTRAIT.center, self.small_font, GOLD, center=True)
        else:
            window.blit(pygame.transform.smoothscale(self.portrait, PORTRAIT.size), PORTRAIT)
        pygame.draw.rect(window, GOLD, PORTRAIT, 2)

        # speaker + text
        first_speaker = self.current.lines[0][0] if self.current.lines else ""
        self._text(window, first_speaker, (355, 195), self.title_font, GOLD)
        y = TEXT_TOP
        for speaker, line, _ in self.wrapped_lines():
            self._text(window, line, (TEXT_LEFT, y), self.font)
            y += LINE_HEIGHT
        if self.message:
            self._text(window, self.message, (TEXT_LEFT, y + 8), self.small_font, GOLD)

        # choices / continue
        self._layout_choices()
        if self.current.auto_next:
            self._next_rect = pygame.Rect(645, 680, 245, 50)
            self._button(window, self._next_rect, "Continuar")
            self._choice_rects.clear()
        else:
            self._next_rect = None
            for rect, choice in self._choice_rects:
                color = BUTTON if choice.enabled else BUTTON_DISABLED
                pygame.draw.rect(window, color, rect, border_radius=6)
                pygame.draw.rect(window, GOLD, rect, 2, border_radius=6)
                self._text(window, choice.label, (rect.x + 15, rect.centery),
                           self.font, center=False, topleft=False, midleft=True)
                if choice.hint:
                    self._text(window, choice.hint, (rect.right - 15, rect.centery),
                               self.small_font, GOLD, midright=True)

    # tiny blit helpers with alignment options
    def _text(self, window, text, pos, font, color=TEXT, center=False,
              topleft=True, midleft=False, midright=False):
        surf = font.render(text, True, color)
        if center:
            rect = surf.get_rect(center=pos)
        elif midleft:
            rect = surf.get_rect(midleft=pos)
        elif midright:
            rect = surf.get_rect(midright=pos)
        else:
            rect = surf.get_rect(topleft=pos)
        window.blit(surf, rect)

    def _button(self, window, rect, label):
        pygame.draw.rect(window, BUTTON, rect, border_radius=6)
        pygame.draw.rect(window, GOLD, rect, 2, border_radius=6)
        self._text(window, label, rect.center, self.font, center=True)

    def set_lines(self, lines):
        self.current.lines = list(lines)

def rumor_choice(label: str, rumors: tuple[str, ...], heard: set[str],
    node_id: str, fallback_message: str, next_rumor_node: str = None) -> Choice:
    """Return a Choice that jumps to ``node_id`` and stores a picked rumor in ``dialog.message`` — the node's ``lines`` can be empty and ``on_enter`` can read ``dialog.message`` to display it."""
    def _pick(dialog: Dialog):
        remaining = [r for r in rumors if r not in heard]
        if remaining:
            rumor = remaining[0]  # deterministic; use random.choice if preferred
            heard.add(rumor)
            dialog.message = rumor
        else:
            dialog.message = fallback_message
        dialog._goto(node_id)
    return Choice(label, target=_pick)

