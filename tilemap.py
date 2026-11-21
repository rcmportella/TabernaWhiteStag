"""
tilemap.py
Sistema reutilizável de construção de mapas com tiles.
Tiles de 32x32, numeração Tile0.png, Tile1.png, ...

Inclui sistema de colisão, obstáculos, armadilhas e posições de entidades.
"""
import json
import os

TILE_DEFINITIONS = {
    0:  {"walls": [], "door": [], "portcullis": [], "secret_door": []}, # Chão livre
    1:  {"walls": ["O"], "door": [], "portcullis": [], "secret_door": []}, # Parede na Esquerda
    2:  {"walls": ["L"], "door": [], "portcullis": [], "secret_door": []}, # Parede na Direita
    3:  {"walls": ["S"], "door": [], "portcullis": [], "secret_door": []}, # Parede em Cima
    4:  {"walls": ["N"], "door": [], "portcullis": [], "secret_door": []}, # Parede em Baixo
    5:  {"walls": ["O","N"], "door": [], "portcullis": [], "secret_door": []}, # canto superior esquerdo
    6:  {"walls": ["L", "N"], "door": [], "portcullis": [], "secret_door": []}, # canto superior direito
    7:  {"walls": ["O", "S"], "door": [], "portcullis": [], "secret_door": []}, # canto inferior esquerdo
    8:  {"walls": ["L", "S"], "door": [], "portcullis": [], "secret_door": []}, # canto inferior direito
    9:  {"walls": [], "door": ["O"], "portcullis": [], "secret_door": []}, # porta oeste
    10: {"walls": [], "door": ["L"], "portcullis": [], "secret_door": []}, # porta leste
    11: {"walls": [], "door": [], "portcullis": [], "secret_door": []}, # Porta aberta oeste
    12: {"walls": [], "door": [], "portcullis": [], "secret_door": []}, # porta aberta leste
    13: {"walls": [], "door": ["N"], "portcullis": [], "secret_door": []}, # Porta em Cima
    14: {"walls": [], "door": ["S"], "portcullis": [], "secret_door": []}, # Porta em Baixo
    15: {"walls": [], "door": [], "portcullis": [], "secret_door": []}, # Porta aberta em cima
    16: {"walls": [], "door": [], "portcullis": [], "secret_door": []}, # Porta aberta em baixo
    17: {"walls": ["L", "O"], "door": [], "portcullis": [], "secret_door": []}, # Parede Esquerda + Parede Direita
    18: {"walls": ["N", "S"], "door": [], "portcullis": [], "secret_door": []}, # Parede Cima + Parede Baixo
    19: {"walls": ["O"], "door": ["L"], "portcullis": [], "secret_door": []}, # parede oeste + porta leste
    20: {"walls": ["L"], "door": ["O"], "portcullis": [], "secret_door": []}, # parede leste + porta oeste
    21: {"walls": ["N"], "door": ["S"], "portcullis": [], "secret_door": []}, # Parede Cima + Porta Baixo
    22: {"walls": ["S"], "door": ["N"], "portcullis": [], "secret_door": []}, # Parede Baixo + Porta Cima
    # --- Novos Tiles com Portcullis ---
    23: {"walls": ["L"], "door": [], "portcullis": ["N"], "secret_door": []},
    24: {"walls": ["O"], "door": [], "portcullis": ["N"], "secret_door": []},
    25: {"walls": ["L"], "door": [], "portcullis": ["S"], "secret_door": []},
    26: {"walls": ["O"], "door": [], "portcullis": ["S"], "secret_door": []},
    27: {"walls": [], "door": [], "portcullis": ["N"], "secret_door": []},
    28: {"walls": [], "door": [], "portcullis": ["S"], "secret_door": []},
    # --- Novos Tiles com Secret Door ---
    29: {"walls": ["O"], "door": [], "portcullis": [], "secret_door": ["O"]},
    30: {"walls": ["L"], "door": [], "portcullis": [], "secret_door": ["L"]},
    31: {"walls": ["N"], "door": [], "portcullis": [], "secret_door": ["N"]},
    32: {"walls": ["S"], "door": [], "portcullis": [], "secret_door": ["S"]},
}

# Limite máximo de entidades para o editor
MAX_PARTY = 6
MAX_MONSTERS = 20


class TileMap:
    def __init__(self, tile_size=32, cols=20, rows=15,
                 tile_count=33, tile_path="Resources/Tiles/Tile", tile_ext=".png"):
        self.tile_size = tile_size
        self.cols = cols
        self.rows = rows
        self.tile_count = tile_count
        self.tile_path = tile_path
        self.tile_ext = tile_ext

        # Camada de tiles: -1 = célula vazia.
        self.data = [-1] * (cols * rows)

        # Camada de armadilhas: {(x, y): {"type": str, "damage": str, "save": str, "dc": int, "effect": str}}
        self.traps = {}

        # Camada de posições de entidades (início do combate no mapa)
        self.party_positions = []     # lista de (x, y) — até MAX_PARTY
        self.monster_positions = []   # lista de (x, y) — até MAX_MONSTERS

        # Cache de superfícies dos tiles
        self.tile_images = {}

    # ------------------------------------------------------------------ #
    # Carregamento de imagens
    # ------------------------------------------------------------------ #
    def load_tiles(self, pygame_module):
        self._pygame = pygame_module
        for i in range(self.tile_count):
            filename = f"{self.tile_path}{i}{self.tile_ext}"
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Tile não encontrado: {filename}")
            img = pygame_module.image.load(filename).convert_alpha()
            if img.get_size() != (self.tile_size, self.tile_size):
                img = pygame_module.transform.scale(
                    img, (self.tile_size, self.tile_size))
            self.tile_images[i] = img

    # ------------------------------------------------------------------ #
    # Acesso às células
    # ------------------------------------------------------------------ #
    def in_bounds(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows

    def set_tile(self, x, y, tile_id):
        if not self.in_bounds(x, y):
            return
        self.data[y * self.cols + x] = tile_id

    def get_tile(self, x, y):
        if not self.in_bounds(x, y):
            return -1
        return self.data[y * self.cols + x]

    # ------------------------------------------------------------------ #
    # SISTEMA DE COLISÃO E OBSTÁCULOS
    # ------------------------------------------------------------------ #
    def get_tile_meta(self, x, y):
        tile_id = self.get_tile(x, y)
        if tile_id < 0:
            return {"walls": [], "door": [], "portcullis": [], "secret_door": []}
        return TILE_DEFINITIONS.get(tile_id, {"walls": [], "door": [], "portcullis": [], "secret_door": []})

    def is_blocked(self, x, y, direction, states=None):
        if states is None:
            states = {}
        meta = self.get_tile_meta(x, y)
        if direction in meta.get("walls", []):
            return True
        for obstacle in ("door", "portcullis", "secret_door"):
            if direction in meta.get(obstacle, []):
                if not states.get(obstacle, False):
                    return True
        return False

    def get_obstacles_in_map(self, obstacle_type):
        obstacles = []
        for y in range(self.rows):
            for x in range(self.cols):
                meta = self.get_tile_meta(x, y)
                for d in meta.get(obstacle_type, []):
                    obstacles.append((x, y, d))
        return obstacles

    # ------------------------------------------------------------------ #
    # SISTEMA DE ARMADILHAS
    # ------------------------------------------------------------------ #
    def set_trap(self, x, y, trap_info):
        """Adiciona/atualiza uma armadilha na célula."""
        if self.in_bounds(x, y):
            self.traps[(x, y)] = trap_info

    def remove_trap(self, x, y):
        self.traps.pop((x, y), None)

    def get_trap(self, x, y):
        return self.traps.get((x, y))

    # ------------------------------------------------------------------ #
    # POSIÇÕES DE ENTIDADES
    # ------------------------------------------------------------------ #
    def add_party_position(self, x, y):
        if not self.in_bounds(x, y):
            return False
        if len(self.party_positions) >= MAX_PARTY:
            return False
        self.party_positions.append((x, y))
        return True

    def add_monster_position(self, x, y):
        if not self.in_bounds(x, y):
            return False
        if len(self.monster_positions) >= MAX_MONSTERS:
            return False
        self.monster_positions.append((x, y))
        return True

    def remove_entity_at(self, x, y):
        """Remove a primeira entidade encontrada na célula (party ou monstro)."""
        if (x, y) in self.party_positions:
            self.party_positions.remove((x, y))
            return "party"
        if (x, y) in self.monster_positions:
            self.monster_positions.remove((x, y))
            return "monster"
        return None

    # ------------------------------------------------------------------ #
    # Redimensionamento
    # ------------------------------------------------------------------ #
    def resize(self, new_cols, new_rows):
        new_data = [-1] * (new_cols * new_rows)
        min_c = min(new_cols, self.cols)
        min_r = min(new_rows, self.rows)
        for y in range(min_r):
            for x in range(min_c):
                new_data[y * new_cols + x] = self.data[y * self.cols + x]
        self.cols = new_cols
        self.rows = new_rows
        self.data = new_data

        # Filtra armadilhas/entidades que ficaram fora do novo tamanho
        self.traps = {pos: t for pos, t in self.traps.items() if self.in_bounds(*pos)}
        self.party_positions = [p for p in self.party_positions if self.in_bounds(*p)]
        self.monster_positions = [m for m in self.monster_positions if self.in_bounds(*m)]

    # ------------------------------------------------------------------ #
    # Renderização
    # ------------------------------------------------------------------ #
    def draw(self, surface, camera_x=0, camera_y=0):
        ts = self.tile_size
        for y in range(self.rows):
            for x in range(self.cols):
                tile_id = self.data[y * self.cols + x]
                if tile_id < 0:
                    continue
                img = self.tile_images.get(tile_id)
                if img is not None:
                    surface.blit(img, (x * ts - camera_x, y * ts - camera_y))

    # ------------------------------------------------------------------ #
    # Serialização JSON
    # ------------------------------------------------------------------ #
    def to_dict(self):
        return {
            "version": 2,  # versão incrementada (agora inclui traps e entidades)
            "tile_size": self.tile_size,
            "cols": self.cols,
            "rows": self.rows,
            "tile_count": self.tile_count,
            "data": list(self.data),
            "traps": {f"{x},{y}": t for (x, y), t in self.traps.items()},
            "party_positions": [list(p) for p in self.party_positions],
            "monster_positions": [list(m) for m in self.monster_positions],
        }

    def from_dict(self, obj):
        self.tile_size = obj.get("tile_size", self.tile_size)
        self.cols = obj["cols"]
        self.rows = obj["rows"]
        self.tile_count = obj.get("tile_count", self.tile_count)
        self.data = list(obj["data"])

        # Carrega armadilhas
        self.traps = {}
        for key, info in obj.get("traps", {}).items():
            try:
                x, y = (int(v) for v in key.split(","))
                self.traps[(x, y)] = info
            except ValueError:
                continue

        # Carrega posições
        self.party_positions = [tuple(p) for p in obj.get("party_positions", [])]
        self.monster_positions = [tuple(m) for m in obj.get("monster_positions", [])]

    def save(self, filename="mapa.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filename, pygame_module, *, tile_size=None, **kwargs):
        with open(filename, "r", encoding="utf-8") as f:
            obj = json.load(f)
        tm = cls(
            tile_size=obj.get("tile_size", 32),
            cols=obj["cols"],
            rows=obj["rows"],
            tile_count=obj.get("tile_count", kwargs.get("tile_count", 33)),
            tile_path=kwargs.get("tile_path", "Resources/Tiles/Tile"),
            tile_ext=kwargs.get("tile_ext", ".png"),
        )
        tm.from_dict(obj)
        if tile_size is not None:
            tm.tile_size = tile_size
        tm.load_tiles(pygame_module)
        return tm