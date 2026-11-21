import os
from pathlib import Path


def main() -> None:
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from character_creation import (
        BUTTON,
        GOLD,
        RESULT_NEXT,
        RESULT_QUIT,
        TEXT,
        run_character_creation,
    )
    from pause_menu import BOX, NO_BUTTON, YES_BUTTON
    from tavern import Tavern
    from savegame import (
        SAVE_PATH, SaveError, last_saved_slot, load_game as load_saved_game, slot_exists, slot_path,
    )
    from save_slots import SlotSelector

    background_dir = (
        Path(__file__).resolve().parent / "Resources" / "Background"
    )
    pygame.init()

    background = pygame.image.load(
        str(background_dir / "TavernaWhiteStag.png")
    )
    window = pygame.display.set_mode(background.get_size())
    pygame.display.set_caption("Taverna White Stag")
    background = background.convert()
    title = pygame.image.load(
        str(background_dir / "Titulo.png")
    ).convert_alpha()
    menu = pygame.image.load(
        str(background_dir / "Menu.png")
    ).convert_alpha()
    button_specs = {
        "new_game": pygame.Rect(28, 54, 934, 208),
        "continue": pygame.Rect(28, 282, 934, 208),
        "load_game": pygame.Rect(28, 510, 934, 208),
        "exit": pygame.Rect(28, 740, 934, 208),
    }
    menu = pygame.transform.smoothscale(
        menu,
        (round(menu.get_width() * 0.5), round(menu.get_height() * 0.5)),
    )
    menu_rect = menu.get_rect(bottomright=background.get_rect().bottomright)
    buttons = {
        name: pygame.Rect(
            round(rect.x * 0.5),
            round(rect.y * 0.5),
            round(rect.width * 0.5),
            round(rect.height * 0.5),
        ).move(menu_rect.topleft)
        for name, rect in button_specs.items()
    }

    game = None
    slot_selector = None
    pending_continue_slot = None
    menu_message = ""
    message_font = pygame.font.Font(None, 28)

    def draw_title(scale: float) -> None:
        width = round(title.get_width() * scale)
        height = round(title.get_height() * scale)
        resized_title = pygame.transform.smoothscale(title, (width, height))
        window.blit(background, (0, 0))
        window.blit(
            resized_title,
            ((background.get_width() - width) // 2,
             background.get_height() - height),
        )

    def draw_menu() -> None:
        draw_title(0.3)
        window.blit(menu, menu_rect)
        if menu_message:
            message = message_font.render(menu_message, True, (255, 215, 160))
            window.blit(message, (30, 30))
        if slot_selector is not None:
            slot_selector.draw()
        if pending_continue_slot is not None:
            shade = pygame.Surface(window.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 180))
            window.blit(shade, (0, 0))
            pygame.draw.rect(window, (20, 14, 10), BOX, border_radius=8)
            pygame.draw.rect(window, GOLD, BOX, 2, border_radius=8)
            for text, y in (
                (f"Carregar o último salvamento (slot {pending_continue_slot})?", 370),
                ("O progresso em memória será perdido.", 405),
            ):
                image = message_font.render(text, True, TEXT)
                window.blit(image, image.get_rect(center=(768, y)))
            for rect, label in ((YES_BUTTON, "Sim"), (NO_BUTTON, "Não")):
                pygame.draw.rect(window, BUTTON, rect, border_radius=6)
                pygame.draw.rect(window, GOLD, rect, 2, border_radius=6)
                image = message_font.render(label, True, TEXT)
                window.blit(image, image.get_rect(center=rect.center))
        pygame.display.flip()

    def run_game() -> None:
        nonlocal running, menu_message
        if game is None:
            menu_message = "Nenhuma partida em andamento."
        elif game.run() == RESULT_QUIT:
            running = False
            return
        draw_menu()

    def start_new_game() -> None:
        nonlocal game, running, menu_message
        result, character = run_character_creation(window, background)
        if result == RESULT_QUIT:
            running = False
            return
        if result == RESULT_NEXT:
            game = Tavern(window, character)
            game.open_theron_dialogue()
            menu_message = ""
            run_game()
        else:
            draw_menu()

    def continue_game() -> None:
        nonlocal menu_message, pending_continue_slot
        try:
            slot = last_saved_slot(SAVE_PATH.parent)
        except (SaveError, OSError) as exc:
            menu_message = f"Erro ao identificar o último salvamento: {exc}"
            draw_menu()
            return
        if slot is None:
            menu_message = "Nenhum jogo salvo encontrado."
            draw_menu()
        elif game is not None:
            pending_continue_slot = slot
            draw_menu()
        else:
            load_slot(slot)

    def load_game() -> None:
        nonlocal slot_selector
        slot_selector = SlotSelector(window, SAVE_PATH.parent, "carregar")
        draw_menu()

    def load_slot(slot: int) -> None:
        nonlocal game, menu_message, slot_selector
        path = slot_path(slot, SAVE_PATH.parent)
        try:
            if not slot_exists(path):
                message = f"O slot {slot} está vazio."
                if slot_selector is None:
                    menu_message = message
                else:
                    slot_selector.message = message
                draw_menu()
                return
            state = load_saved_game(path)
        except (SaveError, OSError, pygame.error) as exc:
            if slot_selector is None:
                menu_message = f"Erro ao carregar: {exc}"
            else:
                slot_selector.message = f"Erro ao carregar: {exc}"
            draw_menu()
            return
        game = Tavern(window, state.hero)
        game.apply_state(state)
        game.save_slot = slot
        slot_selector = None
        menu_message = ""
        run_game()

    actions = {
        "new_game": start_new_game,
        "continue": continue_game,
        "load_game": load_game,
    }

    clock = pygame.time.Clock()
    animation_duration_ms = 1000
    animation_start = pygame.time.get_ticks()
    animating = True
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif not animating and pending_continue_slot is not None:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pending_continue_slot = None
                        draw_menu()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if NO_BUTTON.collidepoint(event.pos):
                            pending_continue_slot = None
                            draw_menu()
                        elif YES_BUTTON.collidepoint(event.pos):
                            slot = pending_continue_slot
                            pending_continue_slot = None
                            load_slot(slot)
                elif not animating and slot_selector is not None:
                    selection = slot_selector.handle_event(event)
                    if selection == "cancel":
                        slot_selector = None
                        draw_menu()
                    elif isinstance(selection, int):
                        load_slot(selection)
                elif (
                    not animating
                    and event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):
                    for name, rect in buttons.items():
                        if rect.collidepoint(event.pos):
                            if name == "exit":
                                running = False
                            else:
                                actions[name]()
                            break

            if not running:
                break

            if animating:
                elapsed = pygame.time.get_ticks() - animation_start
                progress = min(elapsed / animation_duration_ms, 1)
                draw_title(1 - 0.7 * progress)

                if progress >= 1:
                    window.blit(menu, menu_rect)
                    animating = False

                pygame.display.flip()

            clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
