"""
Character creation screen
"""
from pathlib import Path

import pygame

import dice
from ability_generation import (
    ABILITIES,
    METHOD_POINT_BUY,
    METHOD_POOL,
    METHOD_RANDOM,
    AbilityGenerator,
)
from character import Character

RESULT_NEXT = "next"
RESULT_CANCEL = "cancel"
RESULT_QUIT = "quit"

PORTRAIT_SIZE = (300, 300)
PORTRAITS_DIR = Path(__file__).resolve().parent / "Resources" / "Portraits" / "Heroes"
MAX_NAME_LENGTH = 20

GENDERS = (("Masculino", "M"), ("Feminino", "F"))
# (label shown, class used by the Character rules)
CLASSES = (
    ("Guerreiro", "Fighter"),
    ("Paladino", "Paladin"),
    ("Clérigo", "Cleric"),
    ("Mago", "Wizard"),
    ("Ladino", "Rogue"),
)
ALIGNMENTS = (
    "Lawful Good", "Neutral Good", "Chaotic Good",
    "Lawful Neutral", "True Neutral", "Chaotic Neutral",
    "Lawful Evil", "Neutral Evil", "Chaotic Evil",
)
METHODS = (
    (METHOD_RANDOM, "Aleatório (4d6)"),
    (METHOD_POOL, "Conjunto (15,14,13,12,10,8)"),
    (METHOD_POINT_BUY, "Compra de pontos (27)"),
)
ABILITY_LABELS = {
    "strength": "Força",
    "dexterity": "Destreza",
    "constitution": "Constituição",
    "intelligence": "Inteligência",
    "wisdom": "Sabedoria",
    "charisma": "Carisma",
}

TEXT = (235, 220, 180)
GOLD = (212, 160, 70)
PANEL = (20, 14, 10, 225)
BUTTON = (60, 44, 30)
BUTTON_SELECTED = (130, 90, 40)
BUTTON_DISABLED = (40, 36, 32)


class Dropdown:
    """Combo box whose option list scrolls when it has many entries"""

    MAX_VISIBLE = 6
    ROW_HEIGHT = 40

    def __init__(self, rect, options, value):
        self.rect = pygame.Rect(rect)
        self.options = list(options)  # [(label, value)]
        self.value = value
        self.is_open = False
        self.scroll = 0
        self.locked = False

    @property
    def label(self):
        return next(l for l, v in self.options if v == self.value)

    def visible_count(self):
        return min(len(self.options), self.MAX_VISIBLE)

    def list_rect(self):
        return pygame.Rect(
            self.rect.x, self.rect.bottom + 2,
            self.rect.width, self.visible_count() * self.ROW_HEIGHT,
        )

    def toggle(self):
        if self.locked:
            return
        self.is_open = not self.is_open
        if self.is_open:
            index = [v for _, v in self.options].index(self.value)
            self.scroll = max(0, min(index, len(self.options) - self.visible_count()))

    def scroll_by(self, step):
        limit = len(self.options) - self.visible_count()
        self.scroll = max(0, min(limit, self.scroll + step))

    def option_at(self, pos):
        area = self.list_rect()
        if not area.collidepoint(pos):
            return None
        return self.options[self.scroll + (pos[1] - area.y) // self.ROW_HEIGHT][1]


def load_portraits():
    """Return {prefix: [(name, surface)]} with portraits resized to 300x300"""
    portraits = {"M": [], "F": []}
    for path in sorted(PORTRAITS_DIR.glob("*.png")):
        prefix = path.name[:2]
        if prefix in ("M_", "F_"):
            image = pygame.image.load(str(path)).convert_alpha()
            portraits[prefix[0]].append(
                (path.stem[2:], pygame.transform.smoothscale(image, PORTRAIT_SIZE))
            )
    return portraits


class CharacterCreation:
    def __init__(self, window, background):
        self.window = window
        self.background = background
        self.font = pygame.font.Font(None, 30)
        self.title_font = pygame.font.Font(None, 56)
        self.portraits = load_portraits()

        self.name = ""
        self.gender = "M"
        self.portrait_index = 0
        self.dropdowns = {
            "class": Dropdown((440, 270, 350, 44), CLASSES, CLASSES[0][1]),
            "alignment": Dropdown(
                (440, 370, 350, 44), [(a, a) for a in ALIGNMENTS], "True Neutral"
            ),
        }
        self.abilities = AbilityGenerator()
        self.hits = []

    @property
    def char_class(self):
        return self.dropdowns["class"].value

    @property
    def alignment(self):
        return self.dropdowns["alignment"].value

    def sync_alignment(self):
        """Force and lock the alignment when the class restricts it"""
        dropdown = self.dropdowns["alignment"]
        required = Character.required_alignment(self.char_class)
        dropdown.locked = required is not None
        if required:
            dropdown.value = required

    def open_dropdown(self):
        return next((d for d in self.dropdowns.values() if d.is_open), None)

    def current_portraits(self):
        return self.portraits[self.gender]

    def can_proceed(self):
        return bool(self.name.strip()) and self.abilities.is_complete()

    def build_character(self):
        portrait_name, portrait = self.current_portraits()[self.portrait_index]
        character = Character(self.name.strip(), self.char_class)
        self.sync_alignment()
        character.set_abilities(*(self.abilities.scores[a] for a in ABILITIES))
        character.gender = "Male" if self.gender == "M" else "Female"
        character.set_alignment(self.alignment)
        character.portrait = portrait
        character.portrait_id = f"{self.gender}_{portrait_name}"
        character.add_gold(1000)
        return character

    def set_gender(self, gender):
        if gender != self.gender:
            self.gender = gender
            self.portrait_index = 0

    def step_portrait(self, step):
        count = len(self.current_portraits())
        if count:
            self.portrait_index = (self.portrait_index + step) % count

    def draw_text(self, text, pos, font=None, color=TEXT, center=False):
        surface = (font or self.font).render(text, True, color)
        rect = surface.get_rect(center=pos) if center else surface.get_rect(topleft=pos)
        self.window.blit(surface, rect)

    def button(self, rect, label, action, selected=False, enabled=True):
        rect = pygame.Rect(rect)
        color = BUTTON_DISABLED if not enabled else (
            BUTTON_SELECTED if selected else BUTTON
        )
        pygame.draw.rect(self.window, color, rect, border_radius=6)
        pygame.draw.rect(self.window, GOLD if enabled else (80, 70, 60), rect, 2, border_radius=6)
        self.draw_text(
            label, rect.center, color=TEXT if enabled else (120, 110, 100), center=True
        )
        if enabled:
            self.hits.append((rect, action))

    def draw(self):
        self.hits = []
        self.sync_alignment()
        self.window.blit(self.background, (0, 0))
        panel = pygame.Surface((1456, 944), pygame.SRCALPHA)
        panel.fill(PANEL)
        self.window.blit(panel, (40, 40))
        self.draw_text("Criação de Personagem", (768, 85), self.title_font, GOLD, True)

        self.draw_identity()
        self.draw_choices()
        self.draw_abilities()

        self.button((80, 900, 200, 50), "Cancelar", self.cancel)
        self.button(
            (1240, 900, 200, 50), "Próximo", self.proceed, enabled=self.can_proceed()
        )
        open_list = self.open_dropdown()
        if open_list:
            self.draw_dropdown_list(open_list)

    def draw_identity(self):
        portraits = self.current_portraits()
        frame = pygame.Rect(80, 130, *PORTRAIT_SIZE)
        if portraits:
            self.window.blit(portraits[self.portrait_index][1], frame)
        pygame.draw.rect(self.window, GOLD, frame, 2)
        self.button((80, 445, 60, 44), "<", lambda: self.step_portrait(-1))
        self.button((320, 445, 60, 44), ">", lambda: self.step_portrait(1))
        if portraits:
            self.draw_text(portraits[self.portrait_index][0], (230, 467), center=True)

        self.draw_text("Nome", (80, 510))
        box = pygame.Rect(80, 540, 300, 44)
        pygame.draw.rect(self.window, (10, 8, 6), box, border_radius=6)
        pygame.draw.rect(self.window, GOLD, box, 2, border_radius=6)
        caret = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else ""
        self.draw_text(self.name + caret, (box.x + 10, box.y + 12))

    def draw_choices(self):
        self.draw_text("Gênero", (440, 130))
        for i, (label, code) in enumerate(GENDERS):
            self.button(
                (440 + i * 180, 165, 170, 44), label,
                lambda c=code: self.set_gender(c), self.gender == code,
            )

        self.draw_text("Classe", (440, 235))
        self.draw_text("Alinhamento", (440, 335))
        for dropdown in self.dropdowns.values():
            self.draw_dropdown(dropdown)
        # Space below is reserved for upcoming attributes (e.g. proficiencies)

    def draw_dropdown(self, dropdown):
        locked = dropdown.locked
        pygame.draw.rect(
            self.window, BUTTON_DISABLED if locked else BUTTON,
            dropdown.rect, border_radius=6,
        )
        pygame.draw.rect(
            self.window, (80, 70, 60) if locked else GOLD,
            dropdown.rect, 2, border_radius=6,
        )
        self.draw_text(
            dropdown.label, (dropdown.rect.x + 12, dropdown.rect.y + 12),
            color=(150, 140, 120) if locked else TEXT,
        )
        if not locked:
            self.draw_text(
                "^" if dropdown.is_open else "v",
                (dropdown.rect.right - 26, dropdown.rect.y + 12),
            )
            self.hits.append((dropdown.rect, dropdown.toggle))

    def draw_dropdown_list(self, dropdown):
        area = dropdown.list_rect()
        pygame.draw.rect(self.window, (10, 8, 6), area)
        for row in range(dropdown.visible_count()):
            label, value = dropdown.options[dropdown.scroll + row]
            item = pygame.Rect(area.x, area.y + row * dropdown.ROW_HEIGHT,
                               area.width, dropdown.ROW_HEIGHT)
            if value == dropdown.value:
                pygame.draw.rect(self.window, BUTTON_SELECTED, item)
            elif item.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.window, BUTTON, item)
            self.draw_text(label, (item.x + 12, item.y + 10))
        pygame.draw.rect(self.window, GOLD, area, 2)
        hidden = len(dropdown.options) - dropdown.visible_count()
        if hidden > 0:
            track = pygame.Rect(area.right - 8, area.y, 6, area.height)
            thumb_h = area.height * dropdown.visible_count() // len(dropdown.options)
            thumb_y = area.y + (area.height - thumb_h) * dropdown.scroll // hidden
            pygame.draw.rect(self.window, (50, 40, 30), track)
            pygame.draw.rect(self.window, GOLD, (track.x, thumb_y, 6, thumb_h))

    def draw_abilities(self):
        self.draw_text("Atributos", (1020, 130))
        for i, (method, label) in enumerate(METHODS):
            self.button(
                (1020, 165 + i * 54, 420, 44), label,
                lambda m=method: self.abilities.set_method(m),
                self.abilities.method == method,
            )

        method = self.abilities.method
        for i, ability in enumerate(ABILITIES):
            y = 350 + i * 50
            score = self.abilities.scores[ability]
            self.draw_text(ABILITY_LABELS[ability], (1020, y + 10))
            self.draw_text(
                "-" if score is None else str(score), (1250, y + 10), center=False
            )
            if score is not None:
                self.draw_text(f"({dice.modifier(score):+d})", (1385, y + 10))

            if method == METHOD_POOL:
                self.button(
                    (1290, y, 40, 40), "<",
                    lambda a=ability: self.abilities.cycle_pool(a, -1),
                )
                self.button(
                    (1335, y, 40, 40), ">",
                    lambda a=ability: self.abilities.cycle_pool(a, 1),
                )
            elif method == METHOD_POINT_BUY:
                self.button(
                    (1290, y, 40, 40), "-",
                    lambda a=ability: self.abilities.adjust(a, -1),
                    enabled=self.abilities.can_adjust(ability, -1),
                )
                self.button(
                    (1335, y, 40, 40), "+",
                    lambda a=ability: self.abilities.adjust(a, 1),
                    enabled=self.abilities.can_adjust(ability, 1),
                )

        if method == METHOD_RANDOM:
            self.button((1020, 665, 420, 44), "Rolar novamente", self.abilities.roll)
        elif method == METHOD_POINT_BUY:
            self.draw_text(
                f"Pontos restantes: {self.abilities.points_left()}", (1020, 675)
            )
        else:
            self.draw_text("Atribua cada valor do conjunto uma vez", (1020, 675))

    def cancel(self):
        self.result = RESULT_CANCEL

    def proceed(self):
        self.result = RESULT_NEXT

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.result = RESULT_QUIT
        elif self.open_dropdown():
            self.handle_dropdown_event(event, self.open_dropdown())
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.hits:
                if rect.collidepoint(event.pos):
                    action()
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif (
                event.unicode
                and event.unicode.isprintable()
                and len(self.name) < MAX_NAME_LENGTH
            ):
                self.name += event.unicode

    def handle_dropdown_event(self, event, dropdown):
        if event.type == pygame.MOUSEWHEEL:
            dropdown.scroll_by(-event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            value = dropdown.option_at(event.pos)
            if value is not None:
                dropdown.value = value
            dropdown.is_open = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            dropdown.is_open = False

    def run(self):
        """Run the screen. Returns (result, character or None)"""
        from equipment_shop import EquipmentShop

        self.result = None
        clock = pygame.time.Clock()
        while True:
            self.draw()
            pygame.display.flip()
            for event in pygame.event.get():
                self.handle_event(event)
                if self.result is not None:
                    break
            if self.result == RESULT_NEXT:
                character = self.build_character()
                result = EquipmentShop(self.window, character).run()
                if result == RESULT_CANCEL:
                    self.result = None
                elif result == RESULT_NEXT:
                    return RESULT_NEXT, character
                else:
                    return result, None
            elif self.result is not None:
                return self.result, None
            clock.tick(60)


def run_character_creation(window, background):
    return CharacterCreation(window, background).run()
