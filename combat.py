"""
combat.py
Sistema de combate tático por turnos em grid, seguindo as regras do SRD 5.2.1.
"""
import math
import random
from collections import deque
from pathlib import Path

import pygame

import dice
from character_creation import BUTTON, BUTTON_DISABLED, GOLD, TEXT
from monster import GiantRat
from party import Party
from tilemap import TileMap
from spell import SPELL_LIBRARY

# Ajuste do Grid para tiles de 96x96
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 64
TILE_SIZE = 96
SPRITE_SIZE = 76 # Tamanho do sprite dentro do tile

LOG_WIDTH = 280
SPELL_PANEL_WIDTH = 220

FEET_PER_TILE = 5
MOVEMENT_SPEED_FEET = 30
MOVEMENT_TILES = MOVEMENT_SPEED_FEET // FEET_PER_TILE
MOVE_ANIMATION_MS = 180
ANIMATION_FPS = 60

class Combatant:
    """Wrapper para unificar Character e Monster no combate."""
    def __init__(self, entity, is_player, tile_size=TILE_SIZE):
        self.entity = entity
        self.is_player = is_player
        self.initiative = 0
        self.x = 0
        self.y = 0
        self.has_moved = False
        self.has_acted = False
        self.has_reacted = False
        self.move_left = MOVEMENT_TILES
        
        img_surface = getattr(entity, 'portrait', None) or getattr(entity, 'image', None)
        
        self.sprite = None
        if isinstance(img_surface, pygame.Surface):
            sprite_size = min(SPRITE_SIZE, max(1, tile_size - 10))
            self.sprite = pygame.transform.smoothscale(
                img_surface, (sprite_size, sprite_size))

class Combat:
    def __init__(self, window: pygame.Surface, party: Party, tilemap: TileMap, monster_class=GiantRat, monster_count=8):
        self.window = window
        self.party = party
        self.tilemap = tilemap
        self.tile_size = tilemap.tile_size
        self.screen_w, self.screen_h = window.get_size()
        self.log_x = self.screen_w - LOG_WIDTH - 10
        self.end_turn_button = pygame.Rect(
            self.log_x, self.screen_h - 60, 150, 40)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 36)
        self.log = []
        self.round = 1
        self.state = "initiative"
        self.turn_index = 0
        self.hover_cell = None
        self.result = None
        self._movement_animation = None
        self._animation_clock = pygame.time.Clock()
        self.spell_selection_active = False
        self.selected_spell = None
        self.spell_buttons = []

        self.background = pygame.Surface(window.get_size())
        self.background.fill((30, 30, 40))

        self.combatants = []
        self._setup_entities(monster_class, monster_count)
        self._roll_initiative()

    def _setup_entities(self, monster_class, monster_count):
        for i, char in enumerate(self.party.members):
            c = Combatant(char, True, self.tile_size)
            if i < len(self.tilemap.party_positions):
                c.x, c.y = self.tilemap.party_positions[i]
            else:
                c.x, c.y = i, 0
            self.combatants.append(c)

        for i in range(monster_count):
            mon = monster_class()
            c = Combatant(mon, False, self.tile_size)
            if i < len(self.tilemap.monster_positions):
                c.x, c.y = self.tilemap.monster_positions[i]
            else:
                c.x, c.y = i + 5, 5
            self.combatants.append(c)

    def _roll_initiative(self):
        for c in self.combatants:
            if c.is_player:
                dex_mod = c.entity.get_ability_modifier('dexterity')
                c.initiative = dice.d20() + dex_mod
            else:
                c.initiative = c.entity.roll_initiative()
        
        self.combatants.sort(key=lambda c: c.initiative, reverse=True)
        self.log.append("=== INÍCIO DO COMBATE ===")
        for c in self.combatants:
            self.log.append(f"{c.entity.name} (Iniciativa: {c.initiative})")
        
        self.turn_index = -1
        self._next_turn()

    @property
    def current_combatant(self):
        return self.combatants[self.turn_index]

    def _next_turn(self):
        if not any(c.is_player and c.entity.can_act() for c in self.combatants):
            self.state = "defeat"
            self.result = "defeat"
            self.log.append("O grupo foi derrotado...")
            return
        if not any(not c.is_player and c.entity.is_alive() for c in self.combatants):
            self.state = "victory"
            self.result = "victory"
            self.log.append("Vitória! Todos os monstros foram derrotados.")
            for c in self.combatants:
                if c.is_player:
                    c.entity.end_combat()
                    #colocar no futuro aqui a lógica de recompensas, experiência, loot, etc.
            return

        for _ in range(len(self.combatants)):
            self.turn_index = (self.turn_index + 1) % len(self.combatants)
            if self.current_combatant.entity.is_alive():
                break
        
        if self.turn_index == 0:
            self.round += 1
            self.log.append(f"--- Rodada {self.round} ---")
            
        c = self.current_combatant
        c.has_moved = False
        c.has_acted = False
        c.has_reacted = False
        c.move_left = MOVEMENT_TILES
        
        if c.is_player:
            if c.entity.dying:
                success, stabilized, died = c.entity.roll_death_save()
                if died:
                    self.log.append(f"{c.entity.name} falhou nos death saves e morreu.")
                    self._next_turn()
                    return
                if stabilized:
                    self.log.append(f"{c.entity.name} estabilizou e está inconsciente.")
                    self._next_turn()
                    return
                status = "sucesso" if success else "falha"
                self.log.append(
                    f"{c.entity.name} rola death save: {status} "
                    f"({c.entity.death_successes} sucessos / {c.entity.death_failures} falhas)."
                )
                self._next_turn()
                return
            self.state = "player_turn"
            self.log.append(f"Turno de {c.entity.name}.")
        else:
            self.state = "enemy_turn"
            self.log.append(f"Turno de {c.entity.name}.")
            self._enemy_action()

    def _needs_turn(self, c):
        if c.is_player:
            if c.entity.is_dead:
                return False
            if c.entity.dying:
                return True          # rola death save
            return c.entity.can_act()
        return c.entity.is_alive()

    def _enemy_action(self):
        monster = self.current_combatant
        if not monster.entity.is_alive():
            self._next_turn()
            return

        targets = [c for c in self.combatants if c.is_player and c.entity.is_alive()]
        if not targets:
            self._next_turn()
            return

        target = min(targets, key=lambda t: abs(t.x - monster.x) + abs(t.y - monster.y))
        dist = abs(target.x - monster.x) + abs(target.y - monster.y)
        
        if dist <= 1:
            _, _, _, msg = monster.entity.attack(target.entity)
            self.log.append(msg)
        else:
            paths = self._get_reachable_paths(monster)
            if paths:
                destination = min(
                    paths,
                    key=lambda cell: (
                        abs(target.x - cell[0]) + abs(target.y - cell[1]),
                        len(paths[cell]),
                    ),
                )
                if not self._move_combatant(monster, paths[destination][:1]):
                    return
                self.log.append(f"{monster.entity.name} moveu-se.")
            else:
                self.log.append(f"{monster.entity.name} está bloqueado.")

        pygame.time.wait(500)
        self._next_turn()

    def _is_occupied(self, x, y):
        return any(c.x == x and c.y == y and c.entity.is_alive() for c in self.combatants)

    def _is_in_enemy_zoc(self, combatant, x, y):
        return any(
            other.entity.is_alive()
            and other.is_player != combatant.is_player
            and abs(other.x - x) + abs(other.y - y) == 1
            for other in self.combatants
        )

    def _get_reachable_paths(self, combatant):
        start = (combatant.x, combatant.y)
        paths = {}
        shortest = {start: 0}
        pending = deque([(start, [])])

        while pending:
            (x, y), path = pending.popleft()
            if len(path) >= combatant.move_left:
                continue

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_cell = (x + dx, y + dy)
                nx, ny = next_cell
                distance = len(path) + 1
                if (distance >= shortest.get(next_cell, float("inf"))
                        or not self.tilemap.in_bounds(nx, ny)
                        or self.tilemap.is_blocked(nx, ny, "N")
                        or self._is_occupied(nx, ny)):
                    continue

                next_path = path + [next_cell]
                shortest[next_cell] = distance
                paths[next_cell] = next_path
                enters_zoc = (
                    not self._is_in_enemy_zoc(combatant, x, y)
                    and self._is_in_enemy_zoc(combatant, nx, ny)
                )
                if not enters_zoc:
                    pending.append((next_cell, next_path))

        return paths

    def _opportunity_attackers(self, combatant, x, y):
        return [
            other for other in self.combatants
            if other.entity.is_alive()
            and other.is_player != combatant.is_player
            and not other.has_reacted
            and abs(other.x - combatant.x) + abs(other.y - combatant.y) == 1
            and abs(other.x - x) + abs(other.y - y) > 1
        ]

    def _opportunity_attack(self, attacker, target):
        attacker.has_reacted = True
        if attacker.is_player:
            hit, damage, roll = attacker.entity.attack_roll(
                target.entity.get_armor_class())
            if hit:
                target.entity.take_damage(damage)
                self.log.append(
                    f"{attacker.entity.name} acerta {target.entity.name} "
                    f"com ataque de oportunidade ({roll}, dano: {damage}).")
            else:
                self.log.append(
                    f"{attacker.entity.name} erra o ataque de oportunidade "
                    f"contra {target.entity.name} ({roll}).")
        else:
            _, _, _, message = attacker.entity.attack(target.entity)
            self.log.append(f"{message} (ataque de oportunidade)")

        if not target.entity.is_alive():
            self.log.append(f"{target.entity.name} caiu!")

    def _animate_step(self, combatant, destination):
        start = (combatant.x, combatant.y)
        end = destination
        started_at = pygame.time.get_ticks()

        while True:
            elapsed = pygame.time.get_ticks() - started_at
            progress = min(elapsed / MOVE_ANIMATION_MS, 1.0)
            self._movement_animation = (combatant, start, end, progress)
            self.draw()
            pygame.display.flip()
            pygame.event.pump()
            if progress >= 1:
                break
            self._animation_clock.tick(ANIMATION_FPS)

        self._movement_animation = None

    def _move_combatant(self, combatant, path):
        for x, y in path:
            current = (combatant.x, combatant.y)
            was_in_zoc = self._is_in_enemy_zoc(combatant, *current)
            for attacker in self._opportunity_attackers(combatant, x, y):
                self._opportunity_attack(attacker, combatant)
                if not combatant.entity.is_alive():
                    self._next_turn()
                    return False

            self._animate_step(combatant, (x, y))
            combatant.x, combatant.y = x, y
            combatant.move_left -= 1
            combatant.has_moved = True

            if (not was_in_zoc
                    and self._is_in_enemy_zoc(combatant, x, y)):
                break

        return True

    def get_grid_cell(self, screen_pos):
        mx, my = screen_pos
        gx = (mx - GRID_OFFSET_X) // self.tile_size
        gy = (my - GRID_OFFSET_Y) // self.tile_size
        if 0 <= gx < self.tilemap.cols and 0 <= gy < self.tilemap.rows:
            return gx, gy
        return None

    def handle_event(self, event):
        if self.state in ("victory", "defeat"):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return "exit"
            return None

        if self.spell_selection_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # First check if spell button was clicked
                for spell, button_rect in self.spell_buttons:
                    if button_rect.collidepoint(event.pos):
                        self.selected_spell = spell
                        self.log.append(f"Escolha um alvo para {spell.name} (ou clique em ESC para cancelar).")
                        return None
                
                # If selected_spell exists, we're in target selection mode
                if self.selected_spell:
                    cell = self.get_grid_cell(event.pos)
                    if not cell:
                        self.log.append("Clique em uma célula do mapa para selecionar alvo.")
                        return None
                    
                    gx, gy = cell
                    # Look for target at clicked cell
                    found_target = False
                    for c in self.combatants:
                        if c.x == gx and c.y == gy and c.entity.is_alive():
                            is_beneficial = self._is_beneficial_spell(self.selected_spell)
                            is_same_team = c.is_player == self.current_combatant.is_player
                            
                            # Route spell based on type:
                            # 1. Self-cast (range_ft == 0): Only caster
                            # 2. Beneficial: Allies or self
                            # 3. Offensive: Enemies only
                            if self.selected_spell.range_ft == 0:
                                if c == self.current_combatant:
                                    self._cast_spell_on_target(self.selected_spell, c)
                                    found_target = True
                                else:
                                    self.log.append("Essa magia só pode ser lançada em você mesmo.")
                            elif is_beneficial and is_same_team:
                                self._cast_spell_on_target(self.selected_spell, c)
                                found_target = True
                            elif not is_beneficial and not is_same_team:
                                self._cast_spell_on_target(self.selected_spell, c)
                                found_target = True
                            else:
                                if is_same_team:
                                    self.log.append("Você não pode atacar aliados com essa magia!")
                                else:
                                    self.log.append("Essa magia só funciona em aliados.")
                            return None
                    
                    if not found_target:
                        self.log.append("Nenhum alvo nessa célula.")
                        return None
                else:
                    # Clicked outside spell panel to cancel
                    if event.pos[0] > SPELL_PANEL_WIDTH:
                        self._cancel_spell_selection()
                        return None
                        
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.selected_spell:
                    self.selected_spell = None
                    self.log.append("Seleção de alvo cancelada. Escolha outro spell ou pressione ESC para sair.")
                else:
                    self._cancel_spell_selection()
                return None
            
            return None

        if self.state == "player_turn":
            if not self.current_combatant.entity.can_act():
                self._end_player_turn()
                return None
            if event.type == pygame.MOUSEMOTION:
                self.hover_cell = self.get_grid_cell(event.pos)
                
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Verifica clique no botão de terminar turno
                if self.end_turn_button.collidepoint(event.pos):
                    self._end_player_turn()
                    return None
                
                # Verifica clique no botão de castear magia
                if hasattr(self, 'spell_button') and self.spell_button.collidepoint(event.pos):
                    if not self.current_combatant.has_acted:
                        self._start_spell_selection()
                    else:
                        self.log.append("Você já usou sua ação neste turno.")
                    return None

                cell = self.get_grid_cell(event.pos)
                if not cell:
                    return None
                
                gx, gy = cell
                # Tenta atacar
                for c in self.combatants:
                    if not c.is_player and c.entity.is_alive() and c.x == gx and c.y == gy:
                        dist = abs(c.x - self.current_combatant.x) + abs(c.y - self.current_combatant.y)
                        if dist <= 1:
                            if not self.current_combatant.has_acted:
                                self._player_attack(c)
                            else:
                                self.log.append("Você já usou sua ação de ataque.")
                            return None
                        else:
                            self.log.append("Alvo fora de alcance.")
                            return None
                
                paths = self._get_reachable_paths(self.current_combatant)
                path = paths.get(cell)
                if path:
                    mover = self.current_combatant
                    if self._move_combatant(mover, path):
                        self.log.append(
                            f"{mover.entity.name} moveu-se.")
                else:
                    self.log.append("Célula fora de alcance ou bloqueada.")

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._end_player_turn()
                elif event.key == pygame.K_s and not self.current_combatant.has_acted:
                    self._start_spell_selection()
        return None

    def _end_player_turn(self):
        """Encerra o turno do jogador atual."""
        self.log.append(f"{self.current_combatant.entity.name} encerrou o turno.")
        self._next_turn()

    def _player_attack(self, target_combatant):
        player = self.current_combatant
        target = target_combatant
        
        hit, dmg, attack_roll = player.entity.attack_roll(target.entity.get_armor_class())
        
        if hit:
            target.entity.take_damage(dmg)
            self.log.append(f"{player.entity.name} acerta {target.entity.name} com {attack_roll} (Dano: {dmg}).")
        if not target.entity.is_alive():
            if not target.is_player:
                self.log.append(f"{target.entity.name} caiu!")
            elif target.entity.is_dead:
                self.log.append(f"{target.entity.name} morreu!")
            else:
                self.log.append(f"{target.entity.name} caiu e está morrendo!")
        else:
            self.log.append(f"{player.entity.name} erra {target.entity.name} com {attack_roll}.")
            
        player.has_acted = True

    def _get_castable_spells(self):
        """Get list of spells the current player can cast.
        
        Returns prepared spells (if slots available) and all cantrips (level 0).
        Cantrips can be cast without preparation and don't consume spell slots.
        """
        player = self.current_combatant.entity
        castable = []
        
        # Add prepared spells (level 0 or with available slots)
        for spell in player.prepared_spells:
            if spell.level == 0 or player.spell_slots.get(spell.level, 0) > 0:
                castable.append(spell)
        
        # Add cantrips from known_spells that aren't already listed
        # D&D 5e: Cantrips can be cast without preparation
        for spell in player.known_spells:
            if spell.level == 0 and spell not in castable:
                castable.append(spell)
        
        return castable

    def _is_beneficial_spell(self, spell):
        """Detect if spell is beneficial (targets allies or self).
        
        Beneficial spells include heals, buffs, and self-cast spells.
        Detection uses name patterns (cure, heal, bless, etc.) and range_ft == 0.
        Note: This is a heuristic approach; ideal solution would add spell_type to Spell class.
        """
        beneficial_names = [
            'cure', 'heal', 'bless', 'shield', 'mage armor', 'heroism',
            'shield of faith', 'lay on hands', 'guidance', 'prestidigitation',
            'light', 'mending', 'resistance'
        ]
        spell_name_lower = spell.name.lower()
        
        # Check by name pattern
        for name in beneficial_names:
            if name in spell_name_lower:
                return True
        
        # Check by range 0 (self-cast spells are typically beneficial like Shield, Mage Armor)
        if spell.range_ft == 0:
            return True
        
        return False

    def _start_spell_selection(self):
        """Enter spell selection mode"""
        spells = self._get_castable_spells()
        if not spells:
            self.log.append("Nenhuma magia disponível!")
            return
        
        self.spell_selection_active = True
        self.spell_buttons = []
        
        spell_panel_x = 10
        spell_panel_y = 70
        button_height = 30
        button_width = SPELL_PANEL_WIDTH - 20
        
        for i, spell in enumerate(spells):
            slot_info = f" (cantrip)" if spell.level == 0 else f" (slot {self.current_combatant.entity.spell_slots.get(spell.level, 0)})"
            button_rect = pygame.Rect(
                spell_panel_x,
                spell_panel_y + i * (button_height + 5),
                button_width,
                button_height
            )
            self.spell_buttons.append((spell, button_rect))

    def _cast_spell_on_target(self, spell, target_combatant):
        """Cast spell on a target.
        
        Handles three spell types:
        1. Cantrips (level 0): No slot cost, cast at-will if learned
        2. Beneficial spells (healing/buffs): Can target allies or self
        3. Offensive spells: Target enemies only
        4. Self-cast (range_ft == 0): Target must be caster
        """
        player = self.current_combatant.entity
        target = target_combatant.entity
        
        # For cantrips (level 0), check if learned (don't need preparation)
        if spell.level == 0:
            if spell not in player.known_spells:
                self.log.append("Você não conhece essa magia!")
                return
        else:
            # For prepared spells, check if spell slot available
            if not player.can_cast_spell(spell):
                self.log.append("Não é possível lançar essa magia!")
                return
        
        # Check range (convert ft to tiles: 5 ft = 1 tile)
        distance = abs(target_combatant.x - self.current_combatant.x) + abs(target_combatant.y - self.current_combatant.y)
        spell_range_tiles = spell.range_ft // 5 if spell.range_ft > 0 else 0
        
        # Range 0 is self-only: target must be caster
        if spell.range_ft == 0:
            if target_combatant != self.current_combatant:
                self.log.append("Essa magia só pode ser lançada em você mesmo.")
                return
        elif distance > spell_range_tiles:
            self.log.append(f"Alvo fora do alcance da magia ({distance} tiles > {spell_range_tiles} tiles).")
            return
        
        success, result_msg = player.cast_spell(spell, target)
        if success:
            self.log.append(f"{player.name} lança {spell.name}: {result_msg}")
            self.current_combatant.has_acted = True
            self.spell_selection_active = False
            self.selected_spell = None
        else:
            self.log.append(f"Falha ao lançar {spell.name}: {result_msg}")

    def _cancel_spell_selection(self):
        """Cancel spell selection mode"""
        self.spell_selection_active = False
        self.selected_spell = None
        self.spell_buttons = []

    def _draw_zones_of_control(self):
        zone_surface = pygame.Surface(
            (self.tile_size, self.tile_size), pygame.SRCALPHA)
        for combatant in self.combatants:
            if not combatant.entity.is_alive():
                continue
            color = (80, 150, 255) if combatant.is_player else (255, 90, 90)
            zone_surface.fill((*color, 35))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                x, y = combatant.x + dx, combatant.y + dy
                if not self.tilemap.in_bounds(x, y):
                    continue
                rect = pygame.Rect(
                    GRID_OFFSET_X + x * self.tile_size,
                    GRID_OFFSET_Y + y * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                self.window.blit(zone_surface, rect)
                pygame.draw.rect(self.window, color, rect, 2)

    def draw(self):
        self.window.blit(self.background, (0, 0))
        
        # Desenha o mapa
        self.tilemap.draw(self.window, -GRID_OFFSET_X, -GRID_OFFSET_Y)
        
        # Desenha a grade
        for x in range(self.tilemap.cols + 1):
            sx = GRID_OFFSET_X + x * self.tile_size
            pygame.draw.line(self.window, (60,60,60), (sx, GRID_OFFSET_Y), (sx, GRID_OFFSET_Y + self.tilemap.rows * self.tile_size))
        for y in range(self.tilemap.rows + 1):
            sy = GRID_OFFSET_Y + y * self.tile_size
            pygame.draw.line(self.window, (60,60,60), (GRID_OFFSET_X, sy), (GRID_OFFSET_X + self.tilemap.cols * self.tile_size, sy))

        if self.state == "player_turn":
            reachable_surface = pygame.Surface(
                (self.tile_size, self.tile_size), pygame.SRCALPHA)
            reachable_surface.fill((70, 220, 130, 75))
            for x, y in self._get_reachable_paths(self.current_combatant):
                rect = pygame.Rect(
                    GRID_OFFSET_X + x * self.tile_size,
                    GRID_OFFSET_Y + y * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                self.window.blit(reachable_surface, rect)

        self._draw_zones_of_control()

        # Hover
        if self.hover_cell and self.state == "player_turn":
            hx, hy = self.hover_cell
            rect = pygame.Rect(GRID_OFFSET_X + hx * self.tile_size, GRID_OFFSET_Y + hy * self.tile_size, self.tile_size, self.tile_size)
            pygame.draw.rect(self.window, (255, 255, 255), rect, 2)

        # Desenha combatentes
        for c in self.combatants:
            if c.is_player:
                if c.entity.is_dead:
                    # desenhar combatente morto do jogador (funcionalidade futura)
                    continue
                if not c.entity.is_alive():
                    # desenhar jogador incapacitado (funcionalidade futura)
                    continue
            else:
                if not c.entity.is_alive():
                    # desenhar inimigo incapacitado (funcionalidade futura)
                    continue

            draw_x, draw_y = c.x, c.y
            if self._movement_animation and self._movement_animation[0] is c:
                _, start, end, progress = self._movement_animation
                draw_x = start[0] + (end[0] - start[0]) * progress
                draw_y = start[1] + (end[1] - start[1]) * progress

            sx = GRID_OFFSET_X + round(draw_x * self.tile_size)
            sy = GRID_OFFSET_Y + round(draw_y * self.tile_size)
            
            if c.sprite:
                margin = (self.tile_size - c.sprite.get_width()) // 2
                self.window.blit(c.sprite, (sx + margin, sy + margin))
            else:
                color = (80, 160, 255) if c.is_player else (220, 80, 80)
                pygame.draw.rect(self.window, color, (sx, sy, self.tile_size, self.tile_size))
                letter = self.font.render(c.entity.name[0].upper(), True, (255, 255, 255))
                # Centraliza a letra também
                lx = sx + (self.tile_size - letter.get_width()) // 2
                ly = sy + (self.tile_size - letter.get_height()) // 2
                self.window.blit(letter, (lx, ly))
            
            # Borda indicando quem é o atual
            if c == self.current_combatant:
                pygame.draw.rect(self.window, (255, 255, 0), (sx, sy, self.tile_size, self.tile_size), 3)
            
            # Barra de vida
            hp_ratio = max(0, c.entity.current_hp / c.entity.max_hp)
            pygame.draw.rect(self.window, (200, 0, 0), (sx, sy + self.tile_size - 6, self.tile_size, 6))
            pygame.draw.rect(self.window, (0, 200, 0), (sx, sy + self.tile_size - 6, int(self.tile_size * hp_ratio), 6))

        # HUD Superior
        pygame.draw.rect(self.window, (20, 20, 30), (0, 0, self.screen_w, 60))
        hud_text = f"Rodada {self.round} | Turno: {self.current_combatant.entity.name} | Fase: {self.state}"
        if self.state == "player_turn":
            hud_text += f" | Movimento restante: {self.current_combatant.move_left} células"
        if self.current_combatant.is_player and self.current_combatant.entity.dying:
            extra=(f" | Death saves:{self.current_combatant.entity.death_successes}/{self.current_combatant.entity.death_failures}")
            hud_text += extra
        text = self.font.render(hud_text, True, GOLD)
        self.window.blit(text, (20, 20))

        # Botão Terminar Turno
        if self.state == "player_turn":
            pygame.draw.rect(self.window, BUTTON, self.end_turn_button, border_radius=6)
            pygame.draw.rect(self.window, GOLD, self.end_turn_button, 2, border_radius=6)
            btn_text = self.small_font.render("Terminar Turno (Espaço)", True, TEXT)
            self.window.blit(btn_text, btn_text.get_rect(center=self.end_turn_button.center))
            
            # Spell button
            if self.current_combatant.entity.prepared_spells:
                self.spell_button = pygame.Rect(
                    self.log_x, self.screen_h - 110, 150, 40)
                btn_color = BUTTON if not self.current_combatant.has_acted else BUTTON_DISABLED
                pygame.draw.rect(self.window, btn_color, self.spell_button, border_radius=6)
                pygame.draw.rect(self.window, GOLD, self.spell_button, 2, border_radius=6)
                btn_text = self.small_font.render("Magia (S)", True, TEXT)
                self.window.blit(btn_text, btn_text.get_rect(center=self.spell_button.center))

        # Desenha painel de seleção de magias
        if self.spell_selection_active:
            # Semi-transparent overlay
            overlay = pygame.Surface((SPELL_PANEL_WIDTH, self.screen_h), pygame.SRCALPHA)
            overlay.fill((30, 30, 40, 220))
            self.window.blit(overlay, (0, 0))
            
            # Title
            title = self.small_font.render("Selecione uma Magia:", True, GOLD)
            self.window.blit(title, (10, 10))
            
            # Spell buttons
            for spell, button_rect in self.spell_buttons:
                slot_text = "cantrip" if spell.level == 0 else f"slot {self.current_combatant.entity.spell_slots.get(spell.level, 0)}"
                btn_color = BUTTON if not self.selected_spell or self.selected_spell != spell else (100, 150, 255)
                pygame.draw.rect(self.window, btn_color, button_rect, border_radius=4)
                pygame.draw.rect(self.window, GOLD, button_rect, 2, border_radius=4)
                spell_text = self.small_font.render(f"{spell.name} ({slot_text})", True, TEXT)
                text_rect = spell_text.get_rect(center=button_rect.center)
                self.window.blit(spell_text, text_rect)
            
            # Instructions
            if not self.selected_spell:
                instr = self.small_font.render("ESC para cancelar", True, (150, 150, 150))
                self.window.blit(instr, (10, self.screen_h - 30))
            else:
                instr = self.small_font.render("Escolha um alvo (ESC voltar)", True, (150, 200, 150))
                self.window.blit(instr, (10, self.screen_h - 30))

        # Log de Combate
        log_rect = pygame.Rect(self.log_x, 70, LOG_WIDTH, self.screen_h - 150)
        pygame.draw.rect(self.window, (20, 20, 30), log_rect)
        pygame.draw.rect(self.window, GOLD, log_rect, 2)
        
        y_offset = log_rect.y + 10
        for msg in self.log[-25:]:
            text = self.small_font.render(msg, True, TEXT)
            self.window.blit(text, (log_rect.x + 10, y_offset))
            y_offset += 22

        # Tela de Fim
        if self.state in ("victory", "defeat"):
            overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.window.blit(overlay, (0, 0))
            msg = "VITÓRIA!" if self.state == "victory" else "GAME OVER"
            color = (0, 255, 0) if self.state == "victory" else (255, 0, 0)
            text = self.title_font.render(msg, True, color)
            self.window.blit(text, (self.screen_w // 2 - text.get_width() // 2, self.screen_h // 2 - 50))
            
            if self.state == "victory":
                sub = self.font.render("Clique para voltar ao diálogo", True, TEXT)
            else:
                sub = self.font.render("Clique para encerrar o jogo", True, TEXT)
            self.window.blit(sub, (self.screen_w // 2 - sub.get_width() // 2, self.screen_h // 2 + 20))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            self.draw()
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                res = self.handle_event(event)
                if res == "exit":
                    running = False
            clock.tick(60)
        return self.result