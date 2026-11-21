"""Shared save-slot selection panel."""

import json
from textwrap import wrap

import pygame

from character_creation import BUTTON, GOLD, TEXT
from savegame import SLOT_COUNT, slot_exists, slot_path

SLOT_BOX = pygame.Rect(448, 240, 640, 550)
SLOT_BUTTONS = tuple(pygame.Rect(568, 330 + index * 65, 400, 50)
                     for index in range(SLOT_COUNT))
SLOT_CANCEL = pygame.Rect(668, 690, 200, 50)


class SlotSelector:
    def __init__(self, window, directory, action, current_slot=None):
        self.window = window
        self.directory = directory
        self.action = action
        self.current_slot = current_slot
        self.message = ""
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 48)
        self.descriptions = [self.describe_slot(slot_path(index, directory))
                             for index in range(1, SLOT_COUNT + 1)]

    @staticmethod
    def describe_slot(path):
        try:
            if not slot_exists(path):
                return "vazio"
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            name = data["characters"][0]["name"]
            if not isinstance(name, str) or not name:
                raise ValueError("Nome do herói inválido")
        except (OSError, UnicodeDecodeError, ValueError, KeyError, IndexError, TypeError):
            return "arquivo inválido ou inacessível"
        return f"ocupado — {name}"

    def text(self, text, pos, font, color=TEXT):
        image = font.render(text, True, color)
        self.window.blit(image, image.get_rect(center=pos))

    def button(self, rect, label):
        pygame.draw.rect(self.window, BUTTON, rect, border_radius=6)
        pygame.draw.rect(self.window, GOLD, rect, 2, border_radius=6)
        if self.small_font.size(label)[0] > rect.width - 20:
            while label and self.small_font.size(label + "...")[0] > rect.width - 20:
                label = label[:-1]
            label += "..."
        self.text(label, rect.center, self.small_font)

    def draw(self):
        shade = pygame.Surface(self.window.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        self.window.blit(shade, (0, 0))
        pygame.draw.rect(self.window, (20, 14, 10), SLOT_BOX, border_radius=8)
        pygame.draw.rect(self.window, GOLD, SLOT_BOX, 2, border_radius=8)
        self.text(f"Escolha um slot para {self.action}", (768, 285), self.title_font, GOLD)
        for index, rect in enumerate(SLOT_BUTTONS, start=1):
            status = self.descriptions[index - 1]
            current = " (atual)" if index == self.current_slot else ""
            self.button(rect, f"Slot {index}{current} — {status}")
        if self.message:
            for index, line in enumerate(wrap(self.message, 55)[:2]):
                self.text(line, (768, 625 + index * 25), self.small_font, GOLD)
        self.button(SLOT_CANCEL, "Cancelar")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "cancel"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if SLOT_CANCEL.collidepoint(event.pos):
                return "cancel"
            for index, rect in enumerate(SLOT_BUTTONS, start=1):
                if rect.collidepoint(event.pos):
                    return index
        return None
