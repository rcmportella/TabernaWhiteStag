"""Edrick's dialog and shop entry in the plaza of Guluvia."""

from pathlib import Path

import pygame

from store import Store
from dialog import Choice, Dialog, DialogNode
from equipment import torch, shovel, crowbar, rope, lantern
from combat import Combat, TILE_SIZE as COMBAT_TILE_SIZE
from tilemap import TileMap

BACKGROUND = Path(__file__).resolve().parent / "Resources" / "Background" / "LojadoEdrick.png"
BASEMENT_MAP = Path(__file__).resolve().parent / "edrickcellar.json"

EDRICK_QUEST = (
    "Procure Edrick Compra-Tudo no mercado. Ele está procurando ajuda e paga bem por isso."
)

EDRICK_INTRO = (
    "É você que Theron enviou para me ajudar a resolver um probleminha?",
)
EDRICK_MISSION_BRIEFING = (
    "Ótimo, isto será fácil para você e seus companheiros. A última carga que "
    "recebi, parece que estava infestada de ratos, mas não quaisquer ratos, ratos "
    "gigantescos que tomaram meu porão e estão impedindo de eu acessar minhas "
    "mercadorias. Por favor, resolvam este problema para mim e terão um desconto "
    "nas minhas mercadorias daqui por diante."
)
EDRICK_REFUSED = (
    "Então você terá que esperar, pois não estou conseguindo acessar meu inventário. "
    "Volte mais tarde."
)
EDRICK_RETURN_GOODS = ("Graças a você, meus ratos se foram e posso acessar minhas mercadorias novamente!",)
EDRICK_RETURN = "De volta à minha loja? O que precisa?"

EDRICK_GOODS = (
    torch,
    shovel,
    crowbar,
    rope,
    lantern,
)


def build_edrick_dialog(host) -> Dialog:
    background = pygame.transform.smoothscale(
        pygame.image.load(str(BACKGROUND)).convert(), host.window.get_size()
    )

    def _accept(_dialog):
        host.accepted_quests.add(EDRICK_QUEST)
        host.edrick_mission_accepted = True
        return "to_shop"

    def _enter_shop(dialog):
        host.edrick_shop = Store(
            host.window,
            host.party,
            title="Edrick, o Compra-Tudo",
            greeting="Tenho tudo o que um aventureiro precisa para sobreviver!",
            subtitle="Tochas, cordas, ferramentas e lanternas — o básico bem feito.",
            categories={
                "general": ("Mercadorias", EDRICK_GOODS),
            },
            background_path=BACKGROUND,
        )
        dialog.close()

    def _enter_basement(dialog):
        try:
            mapa = TileMap.load(
                str(BASEMENT_MAP),
                pygame,
                tile_size=COMBAT_TILE_SIZE,
                tile_path="Resources/Tiles/Tile",
            )
        except Exception as e:
            dialog.set_lines([("Edrick", f"Erro ao carregar o porão: {e}")])
            return None
        
        combat = Combat(host.window, host.party, mapa)
        result = combat.run()
        
        if result == "victory":
            host.edrick_cellar_cleared = True
            return "cellar_cleared"
        elif result == "defeat":
            # Sinaliza para o host (Tavern) que o jogo deve acabar
            host.game_over = True
            dialog.close()
            return None
        elif result == "quit":
            # O jogador fechou a janela durante o combate
            dialog.close()
            return None
        
        return "to_shop"

    nodes = [
        DialogNode(
            "intro0",
            lines=[("Edrick", EDRICK_INTRO[0])],
            choices=[
                Choice("Sim, sou eu. Qual o seu problema?", target=_accept),
                Choice("Não, eu apenas vim aqui comprar equipamentos",
                       target="refused"),
            ],
        ),
        DialogNode(
            "refused",
            lines=[("Edrick", EDRICK_REFUSED)],
            choices=[Choice("Sair", target=None)],
        ),
        DialogNode(
            "to_shop",
            lines=[("Edrick", EDRICK_MISSION_BRIEFING)],
            choices=[
                Choice("Descer ao porão", target=_enter_basement),
                Choice("Sair", target=None),
            ],
        ),
        DialogNode(
            "cellar_cleared",
            lines=[("Edrick", EDRICK_RETURN_GOODS[0])],
            choices=[
                Choice("Ver mercadorias", target=_enter_shop),
                Choice("Sair", target=None),
            ],
        ),
        DialogNode(
            "basement",
            lines=[("Edrick", "A porta range... algo se move lá embaixo. (em breve)")],
            choices=[Choice("Voltar", target="to_shop")],
        ),
        DialogNode(
            "menu",
            lines=[("Edrick", EDRICK_RETURN)],
            choices=[
                Choice("Ver mercadorias", target=_enter_shop),
                Choice("Até logo", target=None),
            ],
        ),
    ]

    if host.edrick_cellar_cleared:
        start = "menu"
#    elif host.edrick_mission_accepted:
#        start = "to_shop"
    else:
        start = "intro0"
    return Dialog(nodes, start, background,
                  default_portrait=host.npc_portraits["Edrick"], host=host)