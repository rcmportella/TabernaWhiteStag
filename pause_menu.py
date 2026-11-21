"""Pause menu and confirmations for saved games."""

from textwrap import wrap

import pygame

from character_creation import BUTTON, GOLD, TEXT
from savegame import SaveError, load_game, save_game, slot_exists, slot_path
from save_slots import SlotSelector

RESULT_MENU = "menu"
BOX = pygame.Rect(448, 240, 640, 550)
SAVE_BUTTON = pygame.Rect(568, 330, 400, 55)
LOAD_BUTTON = pygame.Rect(568, 405, 400, 55)
MAIN_BUTTON = pygame.Rect(568, 480, 400, 55)
RESUME_BUTTON = pygame.Rect(568, 555, 400, 55)
YES_BUTTON = pygame.Rect(488, 520, 160, 55)
NO_BUTTON = pygame.Rect(688, 520, 160, 55)
CANCEL_BUTTON = pygame.Rect(888, 520, 160, 55)


class PauseMenu:
    def __init__(self, tavern):
        self.tavern = tavern
        self.mode = "menu"
        self.message = ""
        self.selector = None
        self.selected_slot = None

    def button(self, rect, label):
        pygame.draw.rect(self.tavern.window, BUTTON, rect, border_radius=6)
        pygame.draw.rect(self.tavern.window, GOLD, rect, 2, border_radius=6)
        self.tavern.text(label, rect.center, center=True)

    def draw(self):
        if self.mode in ("save_slots", "load_slots", "main_slots"):
            self.selector.draw()
            return
        window = self.tavern.window
        shade = pygame.Surface(window.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        window.blit(shade, (0, 0))
        pygame.draw.rect(window, (20, 14, 10), BOX, border_radius=8)
        pygame.draw.rect(window, GOLD, BOX, 2, border_radius=8)
        self.tavern.text("Menu de pausa", (768, 285), self.tavern.title_font, GOLD, True)
        if self.mode == "menu":
            self.button(SAVE_BUTTON, "Salvar")
            self.button(LOAD_BUTTON, "Carregar")
            self.button(MAIN_BUTTON, "Tela Principal")
            self.button(RESUME_BUTTON, "Continuar")
            if self.tavern.save_slot is not None:
                self.tavern.text(f"Slot atual: {self.tavern.save_slot}", (768, 630),
                                 self.tavern.small_font, GOLD, True)
            if self.message:
                lines = [line for part in self.message.splitlines()
                         for line in (wrap(part, 66) or [""])]
                for index, line in enumerate(lines[:4]):
                    self.tavern.text(line, (768, 655 + index * 26),
                                     self.tavern.small_font, TEXT, True)
            return
        prompts = {
            "overwrite": (f"Substituir o salvamento do slot {self.selected_slot}?",),
            "load": (f"Carregar o slot {self.selected_slot}?",
                     "O progresso não salvo será perdido."),
            "main": ("Salvar o jogo antes de voltar", "à tela principal?"),
            "main_overwrite": (f"Substituir o salvamento do slot {self.selected_slot}",
                               "antes de voltar?"),
        }
        for index, line in enumerate(prompts[self.mode]):
            self.tavern.text(line, (768, 370 + index * 35), center=True)
        self.button(YES_BUTTON, "Sim")
        self.button(NO_BUTTON, "Não")
        self.button(CANCEL_BUTTON, "Cancelar")

    def save(self, exit_after=False):
        try:
            save_game(self.tavern.game_state(),
                      slot_path(self.selected_slot, self.tavern.save_directory))
        except (SaveError, OSError, pygame.error) as exc:
            self.mode = "menu"
            self.message = f"Erro ao salvar:\n{exc}"
            return
        self.tavern.save_slot = self.selected_slot
        if exit_after:
            self.tavern.result = RESULT_MENU
        else:
            self.mode = "menu"
            self.message = f"Jogo salvo no slot {self.selected_slot}."

    def load(self):
        try:
            state = load_game(slot_path(self.selected_slot, self.tavern.save_directory))
        except (SaveError, OSError, pygame.error) as exc:
            self.mode = "menu"
            self.message = f"Erro ao carregar:\n{exc}"
            return
        self.tavern.apply_state(state)
        self.tavern.save_slot = self.selected_slot
        self.tavern.pause = None

    def select_slots(self, mode):
        self.mode = mode
        action = "carregar" if mode == "load_slots" else "salvar"
        self.selector = SlotSelector(self.tavern.window, self.tavern.save_directory,
                                     action, self.tavern.save_slot)

    def handle_event(self, event):
        if self.mode in ("save_slots", "load_slots", "main_slots"):
            selection = self.selector.handle_event(event)
            if selection == "cancel":
                self.mode = "menu"
            elif isinstance(selection, int):
                self.selected_slot = selection
                try:
                    exists = slot_exists(slot_path(selection, self.tavern.save_directory))
                except OSError as exc:
                    self.selector.message = f"Erro ao acessar o slot {selection}: {exc}"
                    return
                if self.mode == "load_slots":
                    if exists:
                        self.mode = "load"
                    else:
                        self.selector.message = f"O slot {selection} está vazio."
                elif exists:
                    self.mode = "main_overwrite" if self.mode == "main_slots" else "overwrite"
                else:
                    self.save(exit_after=self.mode == "main_slots")
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.mode == "menu":
                self.tavern.pause = None
            elif self.mode in ("overwrite", "load", "main_overwrite"):
                self.mode = {"overwrite": "save_slots", "load": "load_slots",
                             "main_overwrite": "main_slots"}[self.mode]
            else:
                self.mode = "menu"
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self.mode == "menu":
            self.message = ""
            if SAVE_BUTTON.collidepoint(event.pos):
                self.select_slots("save_slots")
            elif LOAD_BUTTON.collidepoint(event.pos):
                self.select_slots("load_slots")
            elif MAIN_BUTTON.collidepoint(event.pos):
                self.mode = "main"
            elif RESUME_BUTTON.collidepoint(event.pos):
                self.tavern.pause = None
            return
        if CANCEL_BUTTON.collidepoint(event.pos):
            self.mode = {"overwrite": "save_slots", "load": "load_slots",
                         "main_overwrite": "main_slots"}.get(self.mode, "menu")
        elif NO_BUTTON.collidepoint(event.pos):
            if self.mode == "main":
                self.tavern.result = RESULT_MENU
            else:
                self.mode = {"overwrite": "save_slots", "load": "load_slots",
                             "main_overwrite": "main_slots"}.get(self.mode, "menu")
        elif YES_BUTTON.collidepoint(event.pos):
            if self.mode == "overwrite":
                self.save()
            elif self.mode == "load":
                self.load()
            elif self.mode == "main":
                self.select_slots("main_slots")
            elif self.mode == "main_overwrite":
                self.save(exit_after=True)
