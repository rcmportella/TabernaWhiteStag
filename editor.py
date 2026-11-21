"""
editor.py
Editor interativo de mapas com tiles.
Modos: [1] Tiles, [2] Armadilhas, [3] Party, [4] Monstros.

Controles:
    Botão esquerdo  -> pintar / adicionar (conforme o modo)
    Botão direito   -> apagar / remover
    Clique na paleta-> escolher tile (modo Tiles)
    Scroll do mouse -> mover câmera (Vertical/Horizontal) OU rolar paleta (se o mouse estiver sobre ela)
    Page Up/Down    -> rolar a paleta de tiles
    Setas           -> mover câmera
    1 / 2 / 3 / 4   -> alternar modo (Tiles / Armadilhas / Party / Monstros)
    G               -> Salvar Como... (abre diálogo)
    F5              -> Salvar rápido (no arquivo atual)
    L               -> Abrir mapa... (abre diálogo)
    C               -> Limpar mapa
    ESC             -> sair
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog

import pygame

from tilemap import TileMap, MAX_PARTY, MAX_MONSTERS

# ---------------------------------------------------------------------- #
# Configurações (Atualizadas para 96x96)
# ---------------------------------------------------------------------- #
TILE_SIZE = 96
TILE_COUNT = 33
DEFAULT_COLS = 15
DEFAULT_ROWS = 10

PALETTE_COLS = 2
PALETTE_CELL = 96
PALETTE_MARGIN = 8
PALETTE_WIDTH = PALETTE_COLS * (PALETTE_CELL + PALETTE_MARGIN) + PALETTE_MARGIN

HEADER_H = 40

DEFAULT_TRAP = {
    "type": "spike",
    "damage": "1d6",
    "save": "DEX",
    "dc": 12,
    "effect": "Perde movimento no próximo turno.",
}


# ---------------------------------------------------------------------- #
# Diálogos nativos (tkinter)
# ---------------------------------------------------------------------- #
def _tk_root() -> tk.Tk:
    root = getattr(_tk_root, "_root", None)
    if root is None:
        root = tk.Tk()
        root.withdraw()
        _tk_root._root = root
    return root


def ask_open_path(initial_dir: str = ".") -> str | None:
    root = _tk_root()
    path = filedialog.askopenfilename(
        parent=root,
        title="Abrir mapa",
        initialdir=initial_dir,
        filetypes=[("Mapa JSON", "*.json"), ("Todos os arquivos", "*.*")],
    )
    return path or None


def ask_save_path(default_name: str = "mapa.json", initial_dir: str = ".") -> str | None:
    root = _tk_root()
    path = filedialog.asksaveasfilename(
        parent=root,
        title="Salvar mapa como...",
        initialdir=initial_dir,
        initialfile=default_name,
        defaultextension=".json",
        filetypes=[("Mapa JSON", "*.json"), ("Todos os arquivos", "*.*")],
    )
    return path or None


class NumberField:
    def __init__(self, rect, label, value, on_commit):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.text = str(value)
        self.editing = False
        self.on_commit = on_commit
        self.cursor_blink = 0

    def start_edit(self):
        self.editing = True
        self.text = ""
        self.cursor_blink = 0

    def stop_edit(self, commit=True):
        if not self.editing:
            return
        self.editing = False
        if commit and self.text.isdigit() and int(self.text) > 0:
            self.on_commit(int(self.text))

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.start_edit()
                return True
            elif self.editing:
                self.stop_edit(True)
                return True

        if not self.editing:
            return False

        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB):
                self.stop_edit(True)
                return True
            elif ev.key == pygame.K_ESCAPE:
                self.stop_edit(False)
                return True
            elif ev.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif ev.unicode.isdigit() and len(self.text) < 4:
                self.text += ev.unicode
                return True
        return False

    def draw(self, screen, font):
        lbl = font.render(self.label, True, (220, 220, 220))
        screen.blit(lbl, (self.rect.left, self.rect.top - 16))

        bg = (60, 60, 75) if self.editing else (35, 35, 45)
        border = (245, 179, 1) if self.editing else (90, 90, 110)
        pygame.draw.rect(screen, bg, self.rect)
        pygame.draw.rect(screen, border, self.rect, 1)

        display = self.text if self.editing else (self.text or "0")
        txt = font.render(display, True, (255, 255, 255))
        screen.blit(txt, (self.rect.left + 5,
                          self.rect.centery - txt.get_height() // 2))

        if self.editing:
            self.cursor_blink = (self.cursor_blink + 1) % 60
            if self.cursor_blink < 30:
                cx = self.rect.left + 5 + txt.get_width() + 1
                pygame.draw.line(screen, (255, 255, 255),
                                 (cx, self.rect.top + 4),
                                 (cx, self.rect.bottom - 4))


def draw_overlays(screen, mapa, camera_x, camera_y, map_view):
    ts = TILE_SIZE

    # Armadilhas (roxo)
    for (x, y), info in mapa.traps.items():
        sx = map_view.left + x * ts - camera_x
        sy = map_view.top + y * ts - camera_y
        if not map_view.collidepoint(sx, sy):
            continue
        rect = pygame.Rect(sx, sy, ts, ts)
        overlay = pygame.Surface((ts, ts), pygame.SRCALPHA)
        overlay.fill((160, 60, 200, 120))
        screen.blit(overlay, rect)
        pygame.draw.rect(screen, (200, 100, 255), rect, 3)
        font = pygame.font.SysFont("consolas", 36, bold=True)
        letter = font.render("T", True, (255, 255, 255))
        screen.blit(letter, (sx + ts // 2 - letter.get_width() // 2,
                             sy + ts // 2 - letter.get_height() // 2))

    # Party (azul)
    for (x, y) in mapa.party_positions:
        sx = map_view.left + x * ts - camera_x
        sy = map_view.top + y * ts - camera_y
        if not map_view.collidepoint(sx, sy):
            continue
        rect = pygame.Rect(sx, sy, ts, ts)
        pygame.draw.rect(screen, (80, 160, 255), rect, 4)
        font = pygame.font.SysFont("consolas", 40, bold=True)
        letter = font.render("P", True, (255, 255, 255))
        screen.blit(letter, (sx + ts // 2 - letter.get_width() // 2,
                             sy + ts // 2 - letter.get_height() // 2))

    # Monstros (vermelho)
    for (x, y) in mapa.monster_positions:
        sx = map_view.left + x * ts - camera_x
        sy = map_view.top + y * ts - camera_y
        if not map_view.collidepoint(sx, sy):
            continue
        rect = pygame.Rect(sx, sy, ts, ts)
        pygame.draw.rect(screen, (220, 80, 80), rect, 4)
        font = pygame.font.SysFont("consolas", 40, bold=True)
        letter = font.render("M", True, (255, 255, 255))
        screen.blit(letter, (sx + ts // 2 - letter.get_width() // 2,
                             sy + ts // 2 - letter.get_height() // 2))


def main():
    pygame.init()
    
    # Consulta o tamanho da tela e abre maximizado (sem bordas)
    info = pygame.display.Info()
    SCREEN_W, SCREEN_H = info.current_w, info.current_h
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.NOFRAME)
    
    pygame.display.set_caption("Editor de Mapas com Tiles (96x96)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 14)

    mapa = TileMap(
        tile_size=TILE_SIZE,
        cols=DEFAULT_COLS,
        rows=DEFAULT_ROWS,
        tile_count=TILE_COUNT,
        tile_path="Resources/Tiles/Tile",
        tile_ext=".png",
    )
    try:
        mapa.load_tiles(pygame)
    except FileNotFoundError as e:
        print("Erro:", e)
        pygame.quit()
        sys.exit(1)

    map_view = pygame.Rect(PALETTE_WIDTH, HEADER_H,
                           SCREEN_W - PALETTE_WIDTH, SCREEN_H - HEADER_H)

    def commit_cols(v):
        mapa.resize(v, mapa.rows)
        clamp_camera()

    def commit_rows(v):
        mapa.resize(mapa.cols, v)
        clamp_camera()

    field_cols = NumberField((PALETTE_WIDTH + 10, 12, 60, 22),
                             "Colunas", mapa.cols, commit_cols)
    field_rows = NumberField((PALETTE_WIDTH + 90, 12, 60, 22),
                             "Linhas", mapa.rows, commit_rows)
    fields = [field_cols, field_rows]

    # Configuração do Scroll da Paleta
    palette_scroll_y = 0
    palette_content_height = ((TILE_COUNT + PALETTE_COLS - 1) // PALETTE_COLS) * (PALETTE_CELL + PALETTE_MARGIN)
    palette_view_height = SCREEN_H - HEADER_H
    max_palette_scroll = max(0, palette_content_height - palette_view_height)

    def get_palette_rects():
        """Gera os retângulos da paleta considerando o scroll atual."""
        rects = []
        for i in range(TILE_COUNT):
            col = i % PALETTE_COLS
            row = i // PALETTE_COLS
            rx = PALETTE_MARGIN + col * (PALETTE_CELL + PALETTE_MARGIN)
            ry = HEADER_H + PALETTE_MARGIN + row * (PALETTE_CELL + PALETTE_MARGIN) - palette_scroll_y
            rects.append((pygame.Rect(rx, ry, PALETTE_CELL, PALETTE_CELL), i))
        return rects

    selected_tile = 0
    edit_mode = "tiles"
    camera_x = camera_y = 0

    current_path: str | None = None
    dirty = False
    base_title = "Editor de Mapas (96x96)"

    def update_caption():
        name = os.path.basename(current_path) if current_path else "(novo)"
        mark = " *" if dirty else ""
        pygame.display.set_caption(f"{base_title} — {name}{mark}")

    def mark_dirty():
        nonlocal dirty
        dirty = True
        update_caption()

    def mark_clean():
        nonlocal dirty
        dirty = False
        update_caption()

    def do_save_as():
        nonlocal current_path
        initial_name = os.path.basename(current_path) if current_path else "mapa.json"
        initial_dir = os.path.dirname(current_path) if current_path else "."
        path = ask_save_path(initial_name, initial_dir)
        if not path:
            return
        mapa.save(path)
        current_path = path
        mark_clean()
        print(f"Mapa salvo em {path}")

    def do_save_quick():
        if current_path is None:
            do_save_as()
        else:
            mapa.save(current_path)
            mark_clean()
            print(f"Mapa salvo em {current_path}")

    def do_open():
        nonlocal current_path
        initial_dir = os.path.dirname(current_path) if current_path else "."
        path = ask_open_path(initial_dir)
        if not path:
            return
        try:
            novo = TileMap.load(path, pygame,
                                tile_path="Resources/Tiles/Tile",
                                tile_count=TILE_COUNT,
                                tile_size=TILE_SIZE)
        except Exception as exc:
            print("Falha ao abrir:", exc)
            return
        mapa.from_dict(novo.to_dict())
        try:
            mapa.load_tiles(pygame)
        except Exception as exc:
            print("Falha ao recarregar tiles:", exc)
        field_cols.text = str(mapa.cols)
        field_rows.text = str(mapa.rows)
        clamp_camera()
        current_path = path
        mark_clean()
        print(f"Mapa carregado de {path}")

    def screen_to_tile(mx, my):
        if not map_view.collidepoint(mx, my):
            return None
        wx = mx - map_view.left + camera_x
        wy = my - map_view.top + camera_y
        x, y = wx // TILE_SIZE, wy // TILE_SIZE
        return (x, y) if mapa.in_bounds(x, y) else None

    def clamp_camera():
        nonlocal camera_x, camera_y
        max_x = max(0, mapa.cols * TILE_SIZE - map_view.width)
        max_y = max(0, mapa.rows * TILE_SIZE - map_view.height)
        camera_x = max(0, min(camera_x, max_x))
        camera_y = max(0, min(camera_y, max_y))

    update_caption()

    running = True
    painting = None

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            consumed = False
            for f in fields:
                if f.handle_event(ev):
                    consumed = True
                    break
            if consumed:
                continue

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_g:
                    do_save_as()
                elif ev.key == pygame.K_F5:
                    do_save_quick()
                elif ev.key == pygame.K_l:
                    do_open()
                elif ev.key == pygame.K_c:
                    mapa.data = [-1] * (mapa.cols * mapa.rows)
                    mapa.traps.clear()
                    mapa.party_positions.clear()
                    mapa.monster_positions.clear()
                    mark_dirty()
                elif ev.key == pygame.K_1:
                    edit_mode = "tiles"
                elif ev.key == pygame.K_2:
                    edit_mode = "traps"
                elif ev.key == pygame.K_3:
                    edit_mode = "party"
                elif ev.key == pygame.K_4:
                    edit_mode = "monsters"
                elif ev.key == pygame.K_PAGEUP:
                    palette_scroll_y = max(0, palette_scroll_y - TILE_SIZE)
                elif ev.key == pygame.K_PAGEDOWN:
                    palette_scroll_y = min(max_palette_scroll, palette_scroll_y + TILE_SIZE)

            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                in_palette = mx < PALETTE_WIDTH and my > HEADER_H

                if edit_mode == "tiles" and in_palette:
                    clicked_palette = False
                    for rect, tid in get_palette_rects():
                        if rect.collidepoint(mx, my):
                            selected_tile = tid
                            clicked_palette = True
                            break
                    if clicked_palette:
                        continue

                t = screen_to_tile(mx, my)
                if t:
                    x, y = t
                    if ev.button == 1:
                        if edit_mode == "tiles":
                            painting = "add"
                            mapa.set_tile(x, y, selected_tile)
                            mark_dirty()
                        elif edit_mode == "traps":
                            mapa.set_trap(x, y, DEFAULT_TRAP.copy())
                            mark_dirty()
                        elif edit_mode == "party":
                            if mapa.add_party_position(x, y):
                                mark_dirty()
                        elif edit_mode == "monsters":
                            if mapa.add_monster_position(x, y):
                                mark_dirty()
                    elif ev.button == 3:
                        if edit_mode == "tiles":
                            painting = "erase"
                            mapa.set_tile(x, y, -1)
                            mark_dirty()
                        elif edit_mode == "traps":
                            mapa.remove_trap(x, y)
                            mark_dirty()
                        else:
                            mapa.remove_entity_at(x, y)
                            mark_dirty()

            elif ev.type == pygame.MOUSEBUTTONUP:
                painting = None

            elif ev.type == pygame.MOUSEMOTION:
                if painting and edit_mode == "tiles":
                    t = screen_to_tile(*ev.pos)
                    if t:
                        mapa.set_tile(t[0], t[1],
                                      selected_tile if painting == "add" else -1)
                        mark_dirty()

            elif ev.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if mx < PALETTE_WIDTH and my > HEADER_H:
                    # Scroll na paleta
                    palette_scroll_y = max(0, min(max_palette_scroll, palette_scroll_y - ev.y * 30))
                else:
                    # Scroll no mapa
                    camera_y -= ev.y * TILE_SIZE
                    camera_x -= ev.x * TILE_SIZE
                    clamp_camera()

        if not any(f.editing for f in fields):
            keys = pygame.key.get_pressed()
            speed = 15
            if keys[pygame.K_LEFT]:  camera_x -= speed
            if keys[pygame.K_RIGHT]: camera_x += speed
            if keys[pygame.K_UP]:    camera_y -= speed
            if keys[pygame.K_DOWN]:  camera_y += speed
            clamp_camera()

        # ---------------- Desenho ---------------- #
        screen.fill((30, 30, 38))

        prev_clip = screen.get_clip()
        screen.set_clip(map_view)
        pygame.draw.rect(screen, (10, 10, 12), map_view)
        map_bounds = pygame.Rect(map_view.left - camera_x, map_view.top - camera_y,
                                 mapa.cols * TILE_SIZE, mapa.rows * TILE_SIZE)
        pygame.draw.rect(screen, (25, 25, 32), map_bounds)
        
        mapa.draw(screen, camera_x - map_view.left, camera_y - map_view.top)
        draw_overlays(screen, mapa, camera_x, camera_y, map_view)

        for gx in range(mapa.cols + 1):
            sx = map_view.left + gx * TILE_SIZE - camera_x
            if map_view.left <= sx <= map_view.right:
                pygame.draw.line(screen, (50, 50, 60),
                                 (sx, map_bounds.top), (sx, map_bounds.bottom))
        for gy in range(mapa.rows + 1):
            sy = map_view.top + gy * TILE_SIZE - camera_y
            if map_view.top <= sy <= map_view.bottom:
                pygame.draw.line(screen, (50, 50, 60),
                                 (map_bounds.left, sy), (map_bounds.right, sy))
        screen.set_clip(prev_clip)

        # Header
        pygame.draw.rect(screen, (42, 42, 52), (0, 0, SCREEN_W, HEADER_H))
        hud = font.render(
            "Modo: %s   |   [1]Tiles [2]Armadilhas [3]Party [4]Monstros   |   "
            "Party: %d/%d   Monstros: %d/%d   |   "
            "[G]Salvar [F5]Salvar [L]Abrir [C]Limpar [PgUp/PgDn]Rolar Paleta"
            % (edit_mode.upper(),
               len(mapa.party_positions), MAX_PARTY,
               len(mapa.monster_positions), MAX_MONSTERS),
            True, (230, 230, 230))
        screen.blit(hud, (10, 12))

        for f in fields:
            f.draw(screen, font)

        # Paleta (com clipping para o scroll)
        pygame.draw.rect(screen, (38, 38, 48),
                         (0, HEADER_H, PALETTE_WIDTH, SCREEN_H - HEADER_H))
        
        prev_clip_palette = screen.get_clip()
        screen.set_clip(pygame.Rect(0, HEADER_H, PALETTE_WIDTH, SCREEN_H - HEADER_H))
        
        for rect, tid in get_palette_rects():
            if rect.bottom < HEADER_H or rect.top > SCREEN_H:
                continue # Otimização: não desenha fora da tela
                
            img = mapa.tile_images.get(tid)
            if img:
                if img.get_size() != (PALETTE_CELL, PALETTE_CELL):
                    thumb = pygame.transform.scale(img, (PALETTE_CELL, PALETTE_CELL))
                else:
                    thumb = img
                screen.blit(thumb, rect.topleft)
            else:
                pygame.draw.rect(screen, (80, 20, 20), rect)
                
            border_color = (245, 179, 1) if tid == selected_tile else (70, 70, 80)
            pygame.draw.rect(screen, border_color, rect, 2)
            
        screen.set_clip(prev_clip_palette)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()