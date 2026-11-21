"""City map and locations reserved for future interactions."""

from pathlib import Path

import pygame

from character_creation import BUTTON, GOLD, TEXT

BACKGROUND_DIR = Path(__file__).resolve().parent / "Resources" / "Background"
BACKGROUND = BACKGROUND_DIR / "Guluvia.png"
MAP_SIZE = (1536, 1024)
COUNTY_SIZE = (1024, 1536)
BACK_BUTTON = pygame.Rect(1255, 940, 250, 52)
LOCATIONS = {
    "tavern": ("Taverna", pygame.Rect(0, 60, 460, 900)),
    "shop": ("Loja de armas e armaduras", pygame.Rect(1270, 520, 266, 445)),
    "temple": ("Templo", pygame.Rect(970, 320, 300, 385)),
    "statue": ("Estátua", pygame.Rect(805, 560, 95, 235)),
    "castle": ("Castelo", pygame.Rect(700, 0, 490, 260)),
}
PLAZA_LOCATIONS = {
    "edrick": ("Loja de Edrick", pygame.Rect(650, 575, 490, 220)),
    "market": ("Mercado", pygame.Rect(0, 520, 325, 210)),
    "county": ("Saída da cidade", pygame.Rect(1250, 490, 135, 220)),
}
COUNTY_LOCATIONS = {
    "plaza": ("Guluvia (Galluovia)", pygame.Rect(435, 655, 200, 80)),
}
SCREENS = {
    "outside": ("Guluvia.png", MAP_SIZE, LOCATIONS),
    "plaza": ("PlazadeGuluvia.png", MAP_SIZE, PLAZA_LOCATIONS),
    "county": ("CondadodeGuluvia.png", COUNTY_SIZE, COUNTY_LOCATIONS),
    "edrick": ("LojadoEdrick.png", MAP_SIZE, {}),
}


class Guluvia:
    def __init__(self, window):
        self.window = window
        self.screen = "outside"
        self._backgrounds = {}
        self.font = pygame.font.Font(None, 30)
        self.message = ""

    def set_screen(self, screen):
        if screen not in SCREENS:
            raise ValueError(f"Tela de Guluvia desconhecida: {screen}")
        self.screen = screen
        self.message = ""

    def image_rect(self):
        width, height = self.window.get_size()
        if self.screen != "county":
            return self.window.get_rect()
        scale = min(width / COUNTY_SIZE[0], height / COUNTY_SIZE[1])
        size = (round(COUNTY_SIZE[0] * scale), round(COUNTY_SIZE[1] * scale))
        return pygame.Rect((0, 0), size).move((width - size[0]) // 2,
                                               (height - size[1]) // 2)

    @property
    def background(self):
        if self.screen not in self._backgrounds:
            filename = SCREENS[self.screen][0]
            image = pygame.image.load(str(BACKGROUND_DIR / filename)).convert()
            rect = self.image_rect()
            background = pygame.Surface(self.window.get_size())
            background.fill((20, 14, 10))
            background.blit(pygame.transform.smoothscale(image, rect.size), rect)
            self._backgrounds[self.screen] = background
        return self._backgrounds[self.screen]

    def back_button_rect(self):
        width, height = self.window.get_size()
        return pygame.Rect(round(BACK_BUTTON.x * width / MAP_SIZE[0]),
                           round(BACK_BUTTON.y * height / MAP_SIZE[1]),
                           round(BACK_BUTTON.width * width / MAP_SIZE[0]),
                           round(BACK_BUTTON.height * height / MAP_SIZE[1]))

    def location_at(self, pos):
        image_rect = self.image_rect()
        if not image_rect.collidepoint(pos):
            return None
        _, size, locations = SCREENS[self.screen]
        map_pos = ((pos[0] - image_rect.x) * size[0] / image_rect.width,
                   (pos[1] - image_rect.y) * size[1] / image_rect.height)
        return next((key for key, (_, rect) in locations.items()
                     if rect.collidepoint(map_pos)), None)

    def draw(self, hover_exclusion=None):
        self.window.blit(self.background, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        location = (None if hover_exclusion and hover_exclusion.collidepoint(mouse_pos)
                    else self.location_at(mouse_pos))
        locations = SCREENS[self.screen][2]
        name = locations[location][0] if location else ""
        label = self.message if not name or self.message.startswith(f"{name}:") else name
        if label:
            text = self.font.render(label, True, TEXT if location else GOLD)
            rect = text.get_rect(midtop=(self.window.get_width() // 2, 20))
            panel = rect.inflate(24, 16)
            pygame.draw.rect(self.window, (20, 14, 10), panel, border_radius=6)
            pygame.draw.rect(self.window, GOLD, panel, 2, border_radius=6)
            self.window.blit(text, rect)
        if self.screen in ("plaza", "edrick"):
            rect = self.back_button_rect()
            pygame.draw.rect(self.window, BUTTON, rect, border_radius=6)
            pygame.draw.rect(self.window, GOLD, rect, 2, border_radius=6)
            label = "Voltar a Guluvia" if self.screen == "plaza" else "Voltar à praça"
            text = self.font.render(label, True, TEXT)
            self.window.blit(text, text.get_rect(center=rect.center))

    def handle_click(self, pos):
        if self.screen in ("plaza", "edrick") and self.back_button_rect().collidepoint(pos):
            self.set_screen("outside" if self.screen == "plaza" else "plaza")
            return False
        location = self.location_at(pos)
        if self.screen == "outside" and location in ("tavern", "shop"):
            self.message = ""
            return location
        if location in ("statue", "plaza", "county", "edrick"):
            self.set_screen("plaza" if location == "statue" else location)
            return False
        if location is not None:
            self.message = f"{SCREENS[self.screen][2][location][0]}: disponível futuramente."
        return False
