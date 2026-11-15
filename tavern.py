"""The tavern hub and its provisional quests and recruits."""

from pathlib import Path
from textwrap import wrap

import pygame

from character import Character
from character_creation import (
    ABILITY_LABELS, BUTTON, BUTTON_DISABLED, GOLD, RESULT_QUIT, TEXT, load_portraits,
)
from party import Party
from pause_menu import PauseMenu
from savegame import GameState, SAVE_PATH

BACKGROUND = Path(__file__).resolve().parent / "Resources" / "Background" / "TabernaPrincipal.png"

QUESTS = (
    "Escoltar a caravana para o norte",
    "Investigar a criatura procurada",
    "Ajudar na fazenda",
)

RECRUITS = (
    ("Aldric", "Paladin", "Paladino", 12, 10, 13, 10, 12, 18),
    ("Celeste", "Cleric", "Clériga", 10, 10, 12, 10, 14, 12),
    ("Faelan", "Rogue", "Ladino", 9, 15, 10, 12, 12, 12),
    ("Isolde", "Wizard", "Maga", 10, 10, 10, 15, 12, 15),
    ("Wulfgar", "Fighter", "Guerreiro", 15, 12, 15, 8, 10, 12),
    ("Maeve", "Wizard", "Maga", 9, 12, 10, 14, 12, 12),
)

DIALOGUES = {
    "Theron": ("Bem-vindo à Taverna do Cervo Branco!",
               "Procure o quadro de avisos se estiver atrás de aventuras."),
    "Aveline": ("Olá, aventureiro! Seja bem-vindo.",
                "Se precisar de companhia, veja os anúncios no quadro."),
}

THERON = pygame.Rect(430, 100, 670, 785)
AVELINE = pygame.Rect(95, 190, 280, 690)
BOARD = pygame.Rect(1125, 0, 411, 805)
EXIT_BUTTON = pygame.Rect(1255, 940, 250, 52)
RETURN_BUTTON = pygame.Rect(618, 600, 300, 55)
PANEL = pygame.Rect(330, 170, 876, 660)
CLOSE_BUTTON = pygame.Rect(1115, 190, 65, 45)
QUEST_TAB = pygame.Rect(355, 245, 220, 48)
RECRUIT_TAB = pygame.Rect(590, 245, 220, 48)
ROW_HEIGHT = 70
DETAILS_BACK = pygame.Rect(100, 915, 200, 52)
DETAILS_RECRUIT = pygame.Rect(1236, 915, 200, 52)
DETAILS_LIST = pygame.Rect(100, 570, 1336, 280)
DETAILS_LINE_HEIGHT = 29

RECRUITMENT_REASONS = {
    "already_joined": "Já está no grupo",
    "charisma": "Carisma maior que o do herói",
    "level": "Nível maior que o do herói",
    "full": "Limite de recrutas atingido",
}


class Tavern:
    def __init__(self, window: pygame.Surface, hero: Character):
        self.window = window
        self.background = pygame.image.load(str(BACKGROUND)).convert()
        self.hero = hero
        self.party = Party(hero)
        self.recruits = []
        portraits = {
            name: (gender, image)
            for gender, entries in load_portraits().items()
            for name, image in entries
        }
        for name, char_class, label, str_, dex, con, int_, wis, cha in RECRUITS:
            recruit = Character(name, char_class)
            recruit.set_abilities(str_, dex, con, int_, wis, cha)
            if name not in portraits:
                raise ValueError(f"Retrato não encontrado para {name}")
            gender, recruit.portrait = portraits[name]
            recruit.gender = "Male" if gender == "M" else "Female"
            recruit.portrait_id = f"{gender}_{name}"
            self.recruits.append((recruit, label))
        self.accepted_quests = set()
        self.panel = None
        self.board_tab = "quests"
        self.outside = False
        self.result = None
        self.pause = None
        self.save_path = SAVE_PATH
        self.examined = None
        self.details_scroll = 0
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 48)

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
        return pygame.Rect(355, 330 + index * ROW_HEIGHT, 826, 62)

    def draw(self):
        self.draw_scene()
        if self.pause is not None:
            self.pause.draw()

    def draw_scene(self):
        if self.examined is not None:
            self.draw_recruit_details()
            return
        if self.outside:
            self.window.fill((20, 14, 10))
            self.text("Fora da taverna", (768, 380), self.title_font, GOLD, True)
            self.text("As aventuras ainda não estão disponíveis.",
                      (768, 450), center=True)
            self.button(RETURN_BUTTON, "Voltar à taverna")
            return

        self.window.blit(self.background, (0, 0))
        info = pygame.Surface((440, 82), pygame.SRCALPHA)
        info.fill((20, 14, 10, 220))
        self.window.blit(info, (20, 20))
        hero = self.hero
        self.text(f"{hero.name}  |  Carisma: {hero.charisma}", (35, 29))
        self.text(f"Grupo: {len(self.party)}/6  |  Recrutas: "
                  f"{len(self.party) - 1}/{self.party.recruitment_limit}",
                  (35, 62), self.small_font)
        if self.accepted_quests:
            self.button(EXIT_BUTTON, "Sair da taverna")
        if self.panel:
            self.draw_panel()

    def draw_panel(self):
        pygame.draw.rect(self.window, (20, 14, 10), PANEL, border_radius=8)
        pygame.draw.rect(self.window, GOLD, PANEL, 2, border_radius=8)
        self.button(CLOSE_BUTTON, "X")
        if self.panel in DIALOGUES:
            self.text(self.panel, (355, 195), self.title_font, GOLD)
            for index, line in enumerate(DIALOGUES[self.panel]):
                self.text(line, (370, 310 + index * 45))
            self.text("X para fechar", (370, 750), self.small_font)
            return

        self.text("Quadro de avisos", (355, 195), self.title_font, GOLD)
        self.button(QUEST_TAB, "Missões", self.board_tab == "quests")
        self.button(RECRUIT_TAB, "Recrutas", self.board_tab == "recruits")
        if self.board_tab == "quests":
            self.text("Clique para aceitar uma missão.", (355, 305), self.small_font)
            for index, quest in enumerate(QUESTS):
                rect = self.row_rect(index)
                accepted = quest in self.accepted_quests
                pygame.draw.rect(self.window, BUTTON_DISABLED if accepted else BUTTON, rect)
                self.text(quest, (rect.x + 15, rect.y + 19))
                self.text("Aceita" if accepted else "Aceitar",
                          (rect.right - 100, rect.y + 20), self.small_font, GOLD)
        else:
            self.text(
                f"Recrutas: {len(self.party) - 1}/{self.party.recruitment_limit}  |  "
                f"Carisma máximo: {self.hero.charisma}",
                (355, 305), self.small_font,
            )
            for index, (recruit, label) in enumerate(self.recruits):
                rect = self.row_rect(index)
                pygame.draw.rect(self.window, BUTTON, rect)
                self.text(f"{recruit.name} — {label}  |  Nível {recruit.level}"
                          f"  |  Carisma {recruit.charisma}",
                          (rect.x + 15, rect.y + 19))
                self.text("Examinar",
                          (rect.right - 160, rect.y + 20), self.small_font, GOLD)
        self.text("X para fechar", (355, 785), self.small_font)

    def recruit_detail_lines(self, recruit):
        lines = [
            "Equipamentos:",
            f"  Arma: {recruit.equipped_weapon or 'Nenhuma'}",
            f"  Armadura: {recruit.equipped_armor or 'Nenhuma'}",
            f"  Escudo: {recruit.equipped_shield or 'Nenhum'}",
            "Inventário:",
        ]
        lines.extend(f"  {item}" for item in recruit.inventory)
        if not recruit.inventory:
            lines.append("  Vazio")
        lines.append("Magias conhecidas:")
        lines.extend(f"  {spell.name}" for spell in recruit.known_spells)
        if not recruit.known_spells:
            lines.append("  Nenhuma")
        lines.append("Espaços de magia:")
        if recruit.spell_slots:
            lines.extend(f"  Nível {level}: {count}"
                         for level, count in sorted(recruit.spell_slots.items()))
        else:
            lines.append("  Nenhum")
        return [part for line in lines for part in (wrap(line, 100) or [""])]

    def max_details_scroll(self):
        if self.examined is None:
            return 0
        visible = DETAILS_LIST.height // DETAILS_LINE_HEIGHT
        return max(0, len(self.recruit_detail_lines(self.examined[0])) - visible)

    def draw_recruit_details(self):
        recruit, label = self.examined
        self.window.blit(self.background, (0, 0))
        overlay = pygame.Surface(self.window.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 14, 10, 240))
        self.window.blit(overlay, (0, 0))
        self.window.blit(recruit.portrait, (100, 120))
        pygame.draw.rect(self.window, GOLD, (100, 120, 300, 300), 2)

        self.text(recruit.name, (440, 90), self.title_font, GOLD)
        self.text(f"{label}  |  Nível {recruit.level}", (440, 140))
        gender = {"Male": "Masculino", "Female": "Feminino"}.get(recruit.gender, "Não definido")
        self.text(f"Gênero: {gender}  |  Alinhamento: {recruit.alignment or 'Não definido'}",
                  (440, 180), self.small_font)
        self.text("Atributos", (440, 230), self.font, GOLD)
        for index, (ability, ability_label) in enumerate(ABILITY_LABELS.items()):
            score = getattr(recruit, ability)
            modifier = recruit.get_ability_modifier(ability)
            self.text(f"{ability_label}: {score} ({modifier:+d})",
                      (440, 270 + index * 40))

        self.text("Combate e recursos", (900, 230), self.font, GOLD)
        stats = (
            f"Pontos de vida: {recruit.current_hp}/{recruit.max_hp}",
            f"Classe de armadura: {recruit.get_armor_class()}",
            f"Bônus base de ataque: {recruit.base_attack_bonus:+d}",
            f"Fortitude: {recruit.fortitude_save:+d}",
            f"Reflexos: {recruit.reflex_save:+d}",
            f"Vontade: {recruit.will_save:+d}",
            f"Experiência: {recruit.experience} XP",
            f"Ouro: {recruit.gold} po",
        )
        for index, stat in enumerate(stats):
            self.text(stat, (900, 270 + index * 34), self.small_font)

        pygame.draw.rect(self.window, BUTTON_DISABLED, DETAILS_LIST)
        pygame.draw.rect(self.window, GOLD, DETAILS_LIST, 2)
        previous_clip = self.window.get_clip()
        self.window.set_clip(DETAILS_LIST.inflate(-12, -8))
        visible = DETAILS_LIST.height // DETAILS_LINE_HEIGHT
        lines = self.recruit_detail_lines(recruit)
        for index, line in enumerate(lines[self.details_scroll:self.details_scroll + visible]):
            self.text(line, (DETAILS_LIST.x + 15,
                             DETAILS_LIST.y + 8 + index * DETAILS_LINE_HEIGHT),
                      self.small_font)
        self.window.set_clip(previous_clip)
        self.text("Roda do mouse ou setas: rolar ficha", (100, 863), self.small_font)
        reason = self.party.recruitment_error(recruit)
        self.text(RECRUITMENT_REASONS[reason] if reason else "Disponível para recrutamento",
                  (DETAILS_RECRUIT.centerx, 883), self.small_font, GOLD, True)
        self.button(DETAILS_BACK, "Voltar")
        if reason is None:
            self.button(DETAILS_RECRUIT, "Recrutar")
        else:
            pygame.draw.rect(self.window, BUTTON_DISABLED, DETAILS_RECRUIT, border_radius=6)
            self.text("Recrutar", DETAILS_RECRUIT.center, color=(120, 110, 100), center=True)

    def handle_details_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.details_scroll = max(0, min(self.max_details_scroll(),
                                             self.details_scroll - event.y))
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                step = -1 if event.key == pygame.K_UP else 1
                self.details_scroll = max(0, min(self.max_details_scroll(),
                                                 self.details_scroll + step))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if DETAILS_BACK.collidepoint(event.pos):
                self.examined = None
            elif DETAILS_RECRUIT.collidepoint(event.pos):
                recruit, _ = self.examined
                self.party.add_member(recruit)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.result = RESULT_QUIT
            return
        if self.pause is not None:
            self.pause.handle_event(event)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pause = PauseMenu(self)
            return
        if self.examined is not None:
            self.handle_details_event(event)
            return
        if self.outside:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and RETURN_BUTTON.collidepoint(event.pos)):
                self.outside = False
            return
        if self.panel:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if CLOSE_BUTTON.collidepoint(event.pos):
                    self.panel = None
                elif self.panel == "board":
                    self.handle_board_click(event.pos)
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self.accepted_quests and EXIT_BUTTON.collidepoint(event.pos):
            self.outside = True
        elif THERON.collidepoint(event.pos):
            self.panel = "Theron"
        elif AVELINE.collidepoint(event.pos):
            self.panel = "Aveline"
        elif BOARD.collidepoint(event.pos):
            self.panel = "board"

    def handle_board_click(self, pos):
        if QUEST_TAB.collidepoint(pos):
            self.board_tab = "quests"
        elif RECRUIT_TAB.collidepoint(pos):
            self.board_tab = "recruits"
        elif self.board_tab == "quests":
            for index, quest in enumerate(QUESTS):
                if self.row_rect(index).collidepoint(pos):
                    self.accepted_quests.add(quest)
                    break
        else:
            for index, entry in enumerate(self.recruits):
                if self.row_rect(index).collidepoint(pos):
                    self.examined = entry
                    self.details_scroll = 0
                    break

    def game_state(self):
        return GameState(self.hero, self.party, self.recruits, self.accepted_quests,
                         "outside" if self.outside else "tavern")

    def apply_state(self, state):
        self.hero = state.hero
        self.party = state.party
        self.recruits = state.recruits
        self.accepted_quests = state.accepted_quests
        self.outside = state.location == "outside"
        self.panel = None
        self.examined = None
        self.board_tab = "quests"
        self.details_scroll = 0

    def run(self):
        self.result = None
        self.pause = None
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
