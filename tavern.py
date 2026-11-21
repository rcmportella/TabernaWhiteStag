"""The tavern hub and its provisional quests and recruits."""

import random
from pathlib import Path
from textwrap import wrap

import pygame

from dialog import Dialog, Choice, rumor_choice, DialogNode
from blacksmith import Blacksmith, gold_text
from edrick import build_edrick_dialog
from character import Character
from character_creation import (
    ABILITY_LABELS, BUTTON, BUTTON_DISABLED, CLASSES, GOLD, RESULT_QUIT, TEXT,
    load_portraits,
)
from equipment import (
    Armor, RationPack, Ring, Shield, Weapon, dagger, leather_armor, greataxe, mace,
    quarterstaff,
)
from guluvia import Guluvia
from party import Party
from pause_menu import PauseMenu
from savegame import GameState, SAVE_PATH
from spell import SPELL_LIBRARY

BACKGROUND = Path(__file__).resolve().parent / "Resources" / "Background" / "TabernaPrincipal.png"
NPC_PORTRAITS = Path(__file__).resolve().parent / "Resources" / "Portraits" / "NPC"
DIALOGUE_PORTRAIT = pygame.Rect(145, 210, 165, 165)

QUESTS = (
    "Procure Edrick Compra-Tudo no mercado. Ele está procurando ajuda e paga bem por isso.",
    "A Baronesa D'Hmiss precisa de ajuda com um problema em suas terras.",
    "Marten Cinta-Dourada paga bem por itens mágicos. Se você tiver algum, procure-o no mercado.",
)

RECRUITS = (
    ("Aldric", "Paladin", "Paladino", 15, 10, 13, 8, 12, 14),
    ("Celeste", "Cleric", "Clériga", 14, 8, 13, 10, 15, 12),
    ("Faelan", "Rogue", "Ladino", 10, 15, 13, 14, 10, 10),
    ("Isolde", "Wizard", "Maga", 8, 12, 13, 15, 14, 10),
    ("Wulfgar", "Fighter", "Guerreiro", 15, 13, 14, 10, 12, 8),
    ("Maeve", "Sorcerer", "Feiticeira", 10, 13, 14, 8, 12, 15),
)

THERON_INTRO = (
    "Seja bem vindo a Estalagem do Cervo Branco onde toda grande aventura tem início. E bem-vindo ao Baronato de Guluvia, terra das ruínas do famoso Castelo da Princesa Argenta."
    "Pela sua aparência você está a procura de aventuras, correto?",
    "Sim amigo. Estou aqui em busca de tesouros e fama. Meu nome é {name}, "
    "e você como se chama?",
    "Me chamo Theron e sou dono desta estalagem e aventureiro aposentado. "
    "Aqui você pode encontrar um quarto para descanso, alguns equipamentos básicos, "
    "outros aventureiros para se juntar a seu grupo, e no quadro de avisos trabalho "
    "para você e seus camaradas. Se precisar de comida e bebida fale com a Aveline "
    "ali atrás, ela irá cuidar de suas necessidades corporais. Agora diga, o que "
    "posso fazer por você?",
)
THERON_RETURN = "O que posso fazer por você amigo?"
NO_MORE_RUMORS = (
    "Não sei de mais rumores. Volte outra hora e quem sabe terei mais coisas a lhe contar."
)
THERON_RUMORS = (
    "Uma jovem e valente guerreira chamada Aliegha foi vista recentemente nas aldeias próximas. Muitos dizem que ela carrega uma espada de rubi e é acompanhada por dois anões e um clérigo.   Alguns acreditam que ela é descendente Princesa Argenta.",
    "Muitos seres estranhos tem sido vistos nas redondezas da floresta ao norte. Essas criaturas dizem os sobreviventes que tem três cabeças, três braços e três pernas. Até agora cinco pessoas foram mortas pelas horríveis criaturas. Os fazendeiros reclamam que seu gado, galinhas e outros animais continuam desaparecendo e culpam essas criaturas.",
    "Ouvi dizer que Edrick Compra-Tudo procura gente corajosa no mercado.",
    "Metade do palácio de Lady Argenta está em ruínas, e muitos acreditam que foi por causa do mago da corte que acidentalmente causou a destruição.",
    "A Baronesa D'Hmiss parece estar em busca de ajuda para suas terras.",
)
THERON_NEXT = pygame.Rect(645, 680, 245, 50)
THERON_OPTIONS = (
    ("Hospedagem", pygame.Rect(370, 600, 370, 50)),
    ("Rumores", pygame.Rect(795, 600, 370, 50)),
    ("Equipamentos", pygame.Rect(370, 670, 370, 50)),
    ("Nos vemos mais tarde", pygame.Rect(795, 670, 370, 50)),
)
AVELINE_INTRO = (
    "Olá aventureiro, se quiser uma boa comida e bebida e só falar comigo, "
    "e se quiser uma boa conversa também. Sei de muitas coisas por aqui"
)
AVELINE_RETURN = (
    "Ora, ora, quem está por aqui? Como andam as aventuras? Deve estar com fome, "
    "sente-se e aproveite nossa deliciosa comida"
)
AVELINE_RUMORS = (
    "Você já deve saber que muito tempo atrás havia aqui por perto um antigo castelo cuja dona era a Lady Argenta. Ela era muito bondosa e generosa com os aldeões. De repente, o castelo foi abandonado e ninguém sabe ao certo o que aconteceu.",
    "Alguns viajantes dizem que Lady Argenta ainda pode estar viva e que o castelo esconde muitos segredos.",
    "Dizem também que um tesouro pode estar escondido nas ruínas do castelo, mas poucos tiveram coragem de procurar.",
)
AVELINE_SHOP = pygame.Rect(370, 475, 370, 50)
AVELINE_RUMOR = pygame.Rect(795, 475, 370, 50)
AVELINE_LEAVE = pygame.Rect(570, 600, 370, 50)
AVELINE_PREVIOUS = pygame.Rect(370, 340, 50, 45)
AVELINE_NEXT = pygame.Rect(1115, 340, 50, 45)
AVELINE_RATIONS = pygame.Rect(370, 490, 795, 55)
AVELINE_MORE_RUMORS = pygame.Rect(795, 600, 370, 50)
AVELINE_BACK = pygame.Rect(370, 700, 245, 50)

THERON = pygame.Rect(430, 100, 670, 785)
AVELINE = pygame.Rect(95, 190, 280, 690)
BOARD = pygame.Rect(1125, 0, 411, 805)
EXIT_BUTTON = pygame.Rect(1255, 940, 250, 52)
PANEL = pygame.Rect(330, 170, 876, 660)
CLOSE_BUTTON = pygame.Rect(1115, 190, 65, 45)
QUEST_TAB = pygame.Rect(355, 245, 220, 48)
RECRUIT_TAB = pygame.Rect(590, 245, 220, 48)
ROW_HEIGHT = 70
DETAILS_BACK = pygame.Rect(100, 915, 200, 52)
DETAILS_RECRUIT = pygame.Rect(1236, 915, 200, 52)
DETAILS_LIST = pygame.Rect(100, 570, 1336, 280)
DETAILS_LINE_HEIGHT = 29
PARTY_PREVIOUS = pygame.Rect(610, 915, 60, 52)
PARTY_NEXT = pygame.Rect(866, 915, 60, 52)
PARTY_EQUIPMENT = pygame.Rect(1236, 915, 200, 52)
PARTY_SPELLS = pygame.Rect(1000, 915, 200, 52)
BACKPACK_LIST = pygame.Rect(780, 200, 656, 650)
PARTY_ACTION = pygame.Rect(100, 650, 200, 48)
RING_RIGHT_BUTTON = pygame.Rect(320, 650, 200, 48)
TARGET_PREVIOUS = pygame.Rect(100, 730, 50, 45)
TARGET_NEXT = pygame.Rect(480, 730, 50, 45)
TARGET_CONFIRM = pygame.Rect(540, 730, 180, 45)
TARGET_CANCEL = pygame.Rect(320, 790, 180, 45)
EQUIPMENT_SLOTS = (
    ("Arma", "weapon"), ("Armadura", "armor"), ("Escudo", "shield"),
    ("Anel esquerdo", "ring_left"), ("Anel direito", "ring_right"),
)

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
        self.city = Guluvia(window)
        self.hero = hero
        self.npc_portraits = {
            name: pygame.transform.smoothscale(
                pygame.image.load(str(NPC_PORTRAITS / f"{name}.png")).convert_alpha(),
                DIALOGUE_PORTRAIT.size,
            )
            for name in ("Theron", "Aveline", "Edrick")
        }
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
            spells = {
                "Isolde": ("light","ray_of_frost", "mage_hand", 
                           "magic_missile", "mage_armor"),
                "Maeve": ("light", "shocking_grasp", "sorcerous_burst",
                          "burning_hands", "detect_magic", "prestidigitation"),
                "Celeste": ("guidance", "sacred_flame", "thaumaturgy",
                            "cure_light_wounds", "bless", "shield_of_faith", "guiding_bolt")
            }
            for spell_id in spells.get(name, ()):
                recruit.learn_spell(SPELL_LIBRARY[spell_id])
            if recruit.prepared_spell_limit:
                recruit.prepare_spells([spell for spell in recruit.known_spells if spell.level > 0])
            if name == "Faelan":
                weapon = dagger()
                armor = leather_armor()
                recruit.add_item(weapon)
                recruit.add_item(armor)
                recruit.equip(weapon)
                recruit.equip(armor)
            elif name == "Wulfgar":
                weapon = greataxe()
                recruit.add_item(weapon)
                recruit.equip(weapon)
            elif name == "Maeve":
                weapon = quarterstaff()
                recruit.add_item(weapon)
                recruit.equip(weapon)
            elif name == "Isolde":
                weapon = dagger()
                recruit.add_item(weapon)
                recruit.equip(weapon)
            elif name == "Celeste":
                weapon = mace()
                armor = leather_armor()
                recruit.add_item(weapon)
                recruit.add_item(armor)
                recruit.equip(weapon)
                recruit.equip(armor)
            if name not in portraits:
                raise ValueError(f"Retrato não encontrado para {name}")
            gender, recruit.portrait = portraits[name]
            recruit.gender = "Male" if gender == "M" else "Female"
            recruit.portrait_id = f"{gender}_{name}"
            self.recruits.append((recruit, label))
        self.accepted_quests = set()
        self.panel = None
        self.theron_dialog = None
        self.theron_intro_seen = False
        self.theron_rumors_heard = set()
        self.aveline_dialog = None
        self.aveline_intro_seen = False
        self.aveline_member_index = 0
        self.aveline_rumors_heard = set()
        self.edrick_dialog = None
        self.edrick_shop = None
        self.edrick_mission_accepted = False
        self.edrick_cellar_cleared = False
        self.board_tab = "quests"
        self.outside = False
        self.blacksmith = None
        self.result = None
        self.game_over = False
        self.pause = None
        self.save_directory = SAVE_PATH.parent
        self.save_slot = None
        self.examined = None
        self.details_scroll = 0
        self.party_view = None
        self.party_index = 0
        self.party_scroll = 0
        self.party_selected_item = None
        self.party_target_index = None
        self.party_message = ""
        self.party_spell_selection = []
        self._portrait_source = None
        self._portrait_thumbnail = None
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 48)

    def build_theron_dialog(self):
        hero = self.hero
        heard = self.theron_rumors_heard

        def _show_rumor(dialog):
            text=dialog.message
            dialog.message=""
            dialog.set_lines([("Theron", text)])

        nodes = [
            DialogNode("intro0",
                    lines=[("Theron", THERON_INTRO[0].format(name=hero.name))],
                    auto_next="intro1"),
            DialogNode("intro1",
                    lines=[(hero.name, THERON_INTRO[1].format(name=hero.name))],
                    portrait=hero.portrait,
                    auto_next="intro2"),
            DialogNode("intro2",
                    lines=[("Theron", THERON_INTRO[2])],
                    auto_next="menu"),
            DialogNode("menu",
                    lines=[("Theron", THERON_RETURN)],
                    choices=[
                        Choice("Hospedagem", target="lodging"),
                        rumor_choice("Rumores", THERON_RUMORS, heard,
                            "rumor", NO_MORE_RUMORS),
                        Choice("Equipamentos", target="equipment_placeholder"),
                        Choice("Nos vemos mais tarde", target=None),
                    ]),
            DialogNode("lodging",
                    lines=[("Theron", "Hospedagem: disponível futuramente.")],
                    choices=[Choice("Voltar ao menu", target="menu"),
                                Choice("Nos vemos mais tarde", target=None)]),
            DialogNode("equipment_placeholder",
                    lines=[("Theron", "Equipamentos: disponível futuramente.")],
                    choices=[Choice("Voltar ao menu", target="menu"),
                                Choice("Nos vemos mais tarde", target=None)]),           
             DialogNode("rumor",
                    lines=[],
                    on_enter=_show_rumor,
                    choices=[Choice("Voltar ao menu", target="menu"),
                                Choice("Nos vemos mais tarde", target=None)]),
        ]
    
        return Dialog(nodes, "intro0", self.background, default_portrait=self.npc_portraits["Theron"],
                    host=self)
    
    def build_aveline_dialog(self):
        def _show_rumor(dialog):
            text = dialog.message
            dialog.message = ""
            dialog.set_lines([("Aveline", text)])

        nodes = [
            DialogNode("menu",
                    lines=[("Aveline",
                            AVELINE_RETURN if self.aveline_intro_seen else AVELINE_INTRO)],
                    choices=[
                        Choice("Comidas e bebidas", target="shop"),
                        rumor_choice("Rumores", AVELINE_RUMORS,
                                        self.aveline_rumors_heard,
                                        "rumor", NO_MORE_RUMORS),
                        Choice("Nos vemos mais tarde", target=None),
                    ]),
            DialogNode("shop",
                    lines=[],                      # filled by on_enter below
                    on_enter=self._aveline_shop_enter,
                    choices=[
                        Choice("<", target=self._aveline_prev_member),
                        Choice(">", target=self._aveline_next_member),
                        Choice("Comprar rações", target=self._aveline_buy_rations),
                        Choice("Voltar", target="menu"),
                    ]),
            DialogNode("rumor",
                    lines=[],
                    on_enter=_show_rumor,
                    choices=[Choice("Voltar", target="menu"), Choice("Nos vemos mais tarde", target=None)]),
        ]
        return Dialog(nodes, "menu", self.background, default_portrait=self.npc_portraits["Aveline"],
                    host=self)

    def _aveline_shop_enter(self, dialog):
        member = self.party.members[self.aveline_member_index]
        rations = RationPack()
        dialog.set_lines([
            ("Aveline", "Escolha quem receberá os suprimentos."),
            ("Aveline", f"Integrante: {member.name}"),
            ("Aveline", f"Ouro do grupo: {gold_text(self.party.total_gold())} po"),
            ("Aveline", f"Rações (10) — {gold_text(rations.cost)} po | {rations.weight} lb"),
        ] + ([("Aveline", dialog.message)] if dialog.message else []))

    def _aveline_prev_member(self, dialog):
        self.aveline_member_index = (self.aveline_member_index - 1) % len(self.party)
        dialog.message = ""
        return "shop"

    def _aveline_next_member(self, dialog):
        self.aveline_member_index = (self.aveline_member_index + 1) % len(self.party)
        dialog.message = ""
        return "shop"

    def _aveline_buy_rations(self, dialog):
        member = self.party.members[self.aveline_member_index]
        if self.party.purchase_item(RationPack(), member):
            dialog.message = f"Rações compradas para {member.name}."
        else:
            dialog.message = "Ouro do grupo insuficiente."
        return "shop"

    def _aveline_next_rumor(self, dialog):
        for rumor in AVELINE_RUMORS:
            if rumor not in self.aveline_rumors_heard:
                self.aveline_rumors_heard.add(rumor)
                dialog.message = rumor
                break
        else:
            dialog.message = NO_MORE_RUMORS
        return "rumor"

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
        if self.party_view is not None:
            self.draw_party_view()
            return
        if self.examined is not None:
            self.draw_recruit_details()
            return
        if self.theron_dialog is not None and self.theron_dialog.open:
            self.theron_dialog.draw(self.window)
            return
        if self.aveline_dialog is not None and self.aveline_dialog.open:
            self.aveline_dialog.draw(self.window)
            return
        if self.edrick_dialog is not None and self.edrick_dialog.open:
            self.edrick_dialog.draw(self.window)
            return
        if self.edrick_shop is not None:
            self.edrick_shop.draw()
            self.draw_hero_portrait()
            return
        if self.blacksmith is not None:
            self.blacksmith.draw()
            self.draw_hero_portrait()
            return
        if self.outside:
            self.city.draw(self.hero_portrait_rect())
            self.draw_hero_portrait()
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
        self.draw_hero_portrait()
        if self.panel:
            self.draw_panel()

    def hero_portrait_rect(self):
        return pygame.Rect(10, self.window.get_height() - 110, 100, 100)

    def draw_hero_portrait(self):
        rect = self.hero_portrait_rect()
        if self.hero.portrait is not self._portrait_source:
            self._portrait_source = self.hero.portrait
            self._portrait_thumbnail = (
                pygame.transform.smoothscale(self.hero.portrait, rect.size)
                if self.hero.portrait is not None else None
            )
        if self._portrait_thumbnail is None:
            pygame.draw.rect(self.window, BUTTON_DISABLED, rect)
            self.text("Herói", rect.center, self.small_font, GOLD, True)
        else:
            self.window.blit(self._portrait_thumbnail, rect)
        pygame.draw.rect(self.window, GOLD, rect, 2)

    def draw_panel(self):
        pygame.draw.rect(self.window, (20, 14, 10), PANEL, border_radius=8)
        pygame.draw.rect(self.window, GOLD, PANEL, 2, border_radius=8)
        self.button(CLOSE_BUTTON, "X")
        if self.panel == "Aveline":
            self.draw_aveline_dialogue()
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

    def draw_dialogue_portrait(self, portrait):
        if portrait is None:
            pygame.draw.rect(self.window, BUTTON_DISABLED, DIALOGUE_PORTRAIT)
            self.text("Herói", DIALOGUE_PORTRAIT.center, self.small_font, GOLD, True)
        else:
            if portrait.get_size() != DIALOGUE_PORTRAIT.size:
                portrait = pygame.transform.smoothscale(portrait, DIALOGUE_PORTRAIT.size)
            self.window.blit(portrait, DIALOGUE_PORTRAIT)
        pygame.draw.rect(self.window, GOLD, DIALOGUE_PORTRAIT, 2)

    def open_theron_dialogue(self):
        self.theron_dialog = self.build_theron_dialog() 
        self.theron_dialog.start_dialog(
            "menu" if self.theron_intro_seen else "intro0")
        self.theron_intro_seen = True

    def handle_theron_click(self, pos):
        # Only needed if your Dialog.handle_event takes a pos rather than an event.
        # If it takes an event (recommended), delete this method entirely.
        pass

    def open_aveline_dialogue(self):
        self.aveline_dialog = self.build_aveline_dialog()
        self.aveline_dialog.start_dialog("menu")
        self.aveline_intro_seen = True

    def open_edrick_dialogue(self):
        self.edrick_dialog = build_edrick_dialog(self)
        self.edrick_dialog.start_dialog()

    def open_edrick_shop(self):
        self.edrick_shop = Blacksmith(self.window, self.party)

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
        if recruit.prepared_spell_limit:
            lines.append(f"Magias preparadas: {len(recruit.prepared_spells)}/{recruit.prepared_spell_limit}")
            lines.extend(f"  {spell.name}" for spell in recruit.prepared_spells)
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

    def draw_details_background(self):
        background = (self.blacksmith.background if self.blacksmith is not None else
                      self.city.background if self.outside else self.background)
        self.window.blit(background, (0, 0))
        overlay = pygame.Surface(self.window.get_size(), pygame.SRCALPHA)
        overlay.fill((20, 14, 10, 240))
        self.window.blit(overlay, (0, 0))

    def draw_character_summary(self, recruit, label):
        if recruit.portrait is None:
            pygame.draw.rect(self.window, BUTTON_DISABLED, (100, 120, 300, 300))
            self.text("Sem retrato", (250, 270), self.font, GOLD, True)
        else:
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

    def draw_recruit_details(self):
        recruit, label = self.examined
        self.draw_details_background()
        self.draw_character_summary(recruit, label)
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

    def backpack_rows(self):
        character = self.party.members[self.party_index]
        equipped = [getattr(character, f"equipped_{slot}") for _, slot in EQUIPMENT_SLOTS]
        items = [item for item in character.inventory
                 if not any(item is equipped_item for equipped_item in equipped)]
        rows = []
        for item in items:
            label = str(item)
            if isinstance(item, RationPack):
                label += f" ({item.quantity} rações)"
            rows.extend((item, part) for part in (wrap(label, 48) or [""]))
        return rows

    def party_lines(self):
        character = self.party.members[self.party_index]
        if self.party_view == "equipment":
            return [line for _, line in self.backpack_rows()] or ["Mochila vazia"]
        if self.party_view == "spells":
            return [f"[{'X' if spell in self.party_spell_selection else ' '}] "
                    f"{spell.name} (nível {spell.level})"
                    for spell in self.party_spell_candidates()] or ["Nenhuma magia disponível"]
        lines = ["Magias conhecidas:"]
        lines.extend(f"  {spell.name}" for spell in character.known_spells)
        if not character.known_spells:
            lines.append("  Nenhuma")
        if character.prepared_spell_limit:
            lines.append(f"Magias preparadas: {len(character.prepared_spells)}/{character.prepared_spell_limit}")
            lines.extend(f"  {spell.name}" for spell in character.prepared_spells)
            lines.extend(f"  {spell.name} (sempre preparada)" for spell in character.always_prepared_spells)
        lines.append("Espaços de magia:")
        if character.spell_slots:
            lines.extend(f"  Nível {level}: {count}"
                         for level, count in sorted(character.spell_slots.items()))
        else:
            lines.append("  Nenhum")
        return [part for line in lines for part in (wrap(line, 100) or [""])]

    def party_spell_candidates(self):
        character = self.party.members[self.party_index]
        return [spell for spell in character.known_spells
                if spell.level > 0 and spell not in character.always_prepared_spells]

    def open_party_spells(self):
        character = self.party.members[self.party_index]
        self.party_view = "spells"
        self.party_scroll = 0
        self.party_spell_selection = character.prepared_spells.copy()
        self.party_message = ""

    def party_list_rect(self):
        return BACKPACK_LIST if self.party_view == "equipment" else DETAILS_LIST

    def max_party_scroll(self):
        visible = self.party_list_rect().height // DETAILS_LINE_HEIGHT
        return max(0, len(self.party_lines()) - visible)

    def draw_party_view(self):
        character = self.party.members[self.party_index]
        self.draw_details_background()
        if self.party_view == "character":
            label = next((label for label, name in CLASSES if name == character.char_class),
                         character.char_class)
            self.draw_character_summary(character, label)
        elif self.party_view == "equipment":
            self.text(f"Equipamentos — {character.name}", (100, 90), self.title_font, GOLD)
            for index, (label, slot) in enumerate(EQUIPMENT_SLOTS):
                item = getattr(character, f"equipped_{slot}")
                self.text(f"{label}: {item or 'Nenhum'}", (100, 210 + index * 65))
            self.text("Mochila", (780, 150), self.font, GOLD)
        else:
            self.text(f"Preparar magias — {character.name}", (100, 90), self.title_font, GOLD)
            self.text(f"Selecionadas: {len(self.party_spell_selection)}/{character.prepared_spell_limit}",
                      (100, 160))
            self.text("Clique nas magias conhecidas para selecionar; confirme as alterações.",
                      (100, 210), self.small_font)
            self.text("Trocas: descanso longo (mago/clérigo/paladino/patrulheiro);",
                      (100, 250), self.small_font)
            self.text("feiticeiro: ao subir de nível.", (100, 280), self.small_font)
            for index, line in enumerate(wrap(self.party_message, 90)):
                self.text(line, (100, 350 + index * 30), self.small_font, GOLD)

        rect = self.party_list_rect()
        pygame.draw.rect(self.window, BUTTON_DISABLED, rect)
        pygame.draw.rect(self.window, GOLD, rect, 2)
        previous_clip = self.window.get_clip()
        self.window.set_clip(rect.inflate(-12, -8))
        visible = rect.height // DETAILS_LINE_HEIGHT
        rows = self.backpack_rows() if self.party_view == "equipment" else []
        for index, line in enumerate(self.party_lines()[self.party_scroll:self.party_scroll + visible]):
            if self.party_view == "equipment":
                row_index = self.party_scroll + index
                if row_index < len(rows) and rows[row_index][0] is self.party_selected_item:
                    pygame.draw.rect(self.window, BUTTON,
                                     (rect.x + 8, rect.y + 5 + index * DETAILS_LINE_HEIGHT,
                                      rect.width - 16, DETAILS_LINE_HEIGHT))
            self.text(line, (rect.x + 15, rect.y + 8 + index * DETAILS_LINE_HEIGHT),
                      self.small_font)
        self.window.set_clip(previous_clip)
        if self.party_view == "equipment":
            self.draw_party_item_actions()
        self.text("Roda do mouse ou setas: rolar", (100, 863), self.small_font)
        self.button(DETAILS_BACK, "Sair" if self.party_view == "character" else "Voltar")
        if self.party_view == "character":
            self.button(PARTY_EQUIPMENT, "Equipamentos")
            if character.prepared_spell_limit:
                self.button(PARTY_SPELLS, "Magias")
        elif self.party_view == "spells":
            self.button(PARTY_EQUIPMENT, "Confirmar")
        if len(self.party) > 1:
            self.button(PARTY_PREVIOUS, "<")
            self.button(PARTY_NEXT, ">")
            self.text(f"{self.party_index + 1}/{len(self.party)}",
                      (768, PARTY_PREVIOUS.centery), self.font, GOLD, True)

    def draw_party_item_actions(self):
        for index, line in enumerate(wrap(self.party_message, 58)):
            self.text(line, (100, 520 + index * 25), self.small_font, GOLD)
        item = self.party_selected_item
        if item is None:
            self.text("Clique em um item da mochila.", (100, 590), self.small_font)
            return
        for index, line in enumerate(wrap(f"Selecionado: {item}", 52)):
            self.text(line, (100, 575 + index * 25), self.small_font, GOLD)
        if self.party_target_index is not None:
            target = self.party.members[self.party_target_index]
            self.text(f"Alvo: {target.name}", (315, 752), self.small_font, GOLD, True)
            self.button(TARGET_PREVIOUS, "<")
            self.button(TARGET_NEXT, ">")
            self.button(TARGET_CONFIRM, "Confirmar")
            self.button(TARGET_CANCEL, "Cancelar")
        elif isinstance(item, Ring):
            self.button(PARTY_ACTION, "Anel esquerdo")
            self.button(RING_RIGHT_BUTTON, "Anel direito")
        elif isinstance(item, (Weapon, Armor, Shield)):
            self.button(PARTY_ACTION, "Equipar")
        elif getattr(item, "consumable", False) and callable(getattr(item, "use", None)):
            self.button(PARTY_ACTION, "Usar")
        else:
            self.text("Este item não pode ser equipado ou usado.", (100, 650), self.small_font)

    def clear_party_selection(self):
        self.party_selected_item = None
        self.party_target_index = None
        self.party_message = ""

    def apply_party_item(self, slot=None):
        character = self.party.members[self.party_index]
        item = self.party_selected_item
        try:
            if self.party_target_index is not None:
                target = self.party.members[self.party_target_index]
                message = character.use_inventory_item(item, target)
            else:
                previous_weapon, previous_shield = character.equipped_weapon, character.equipped_shield
                character.equip(item, slot)
                message = f"{item} equipado."
                if previous_shield is not None and character.equipped_shield is None:
                    message += " Escudo desequipado."
                elif previous_weapon is not None and character.equipped_weapon is None:
                    message += " Arma desequipada."
        except (TypeError, ValueError) as exc:
            self.party_message = f"Não foi possível usar o item: {exc}"
            return
        self.clear_party_selection()
        self.party_message = message
        self.party_scroll = min(self.party_scroll, self.max_party_scroll())

    def handle_party_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.party_scroll = max(0, min(self.max_party_scroll(),
                                           self.party_scroll - event.y))
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_DOWN):
            step = -1 if event.key == pygame.K_UP else 1
            self.party_scroll = max(0, min(self.max_party_scroll(), self.party_scroll + step))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if DETAILS_BACK.collidepoint(event.pos):
                self.party_view = None if self.party_view == "character" else "character"
                self.party_scroll = 0
                self.clear_party_selection()
            elif self.party_view == "character" and PARTY_EQUIPMENT.collidepoint(event.pos):
                self.party_view = "equipment"
                self.party_scroll = 0
                self.clear_party_selection()
            elif (self.party_view == "character" and PARTY_SPELLS.collidepoint(event.pos)
                  and self.party.members[self.party_index].prepared_spell_limit):
                self.open_party_spells()
            elif self.party_view == "spells" and PARTY_EQUIPMENT.collidepoint(event.pos):
                character = self.party.members[self.party_index]
                try:
                    character.prepare_spells(self.party_spell_selection)
                except ValueError as exc:
                    self.party_message = f"Não foi possível preparar magias: {exc}"
                else:
                    self.party_message = "Magias preparadas."
            elif len(self.party) > 1 and (PARTY_PREVIOUS.collidepoint(event.pos)
                                          or PARTY_NEXT.collidepoint(event.pos)):
                step = -1 if PARTY_PREVIOUS.collidepoint(event.pos) else 1
                self.party_index = (self.party_index + step) % len(self.party)
                self.party_scroll = 0
                self.clear_party_selection()
                if self.party_view == "spells":
                    if self.party.members[self.party_index].prepared_spell_limit:
                        self.open_party_spells()
                    else:
                        self.party_view = "character"
            elif self.party_view == "equipment":
                self.handle_backpack_click(event.pos)
            elif self.party_view == "spells" and DETAILS_LIST.inflate(-12, -8).collidepoint(event.pos):
                relative = (event.pos[1] - DETAILS_LIST.y - 8) // DETAILS_LINE_HEIGHT
                index = relative + self.party_scroll
                candidates = self.party_spell_candidates()
                if 0 <= relative < DETAILS_LIST.height // DETAILS_LINE_HEIGHT and index < len(candidates):
                    spell = candidates[index]
                    if spell in self.party_spell_selection:
                        self.party_spell_selection.remove(spell)
                    else:
                        self.party_spell_selection.append(spell)
                    self.party_message = ""

    def handle_backpack_click(self, pos):
        if BACKPACK_LIST.inflate(-12, -8).collidepoint(pos):
            relative = (pos[1] - BACKPACK_LIST.y - 8) // DETAILS_LINE_HEIGHT
            rows = self.backpack_rows()
            index = relative + self.party_scroll
            if 0 <= relative < BACKPACK_LIST.height // DETAILS_LINE_HEIGHT and index < len(rows):
                self.clear_party_selection()
                self.party_selected_item = rows[index][0]
            return
        item = self.party_selected_item
        if item is None:
            return
        if self.party_target_index is not None:
            if TARGET_PREVIOUS.collidepoint(pos) or TARGET_NEXT.collidepoint(pos):
                step = -1 if TARGET_PREVIOUS.collidepoint(pos) else 1
                self.party_target_index = (self.party_target_index + step) % len(self.party)
            elif TARGET_CANCEL.collidepoint(pos):
                self.party_target_index = None
            elif TARGET_CONFIRM.collidepoint(pos):
                self.apply_party_item()
        elif isinstance(item, Ring):
            if PARTY_ACTION.collidepoint(pos):
                self.apply_party_item("ring_left")
            elif RING_RIGHT_BUTTON.collidepoint(pos):
                self.apply_party_item("ring_right")
        elif isinstance(item, (Weapon, Armor, Shield)) and PARTY_ACTION.collidepoint(pos):
            self.apply_party_item()
        elif (getattr(item, "consumable", False) and callable(getattr(item, "use", None))
              and PARTY_ACTION.collidepoint(pos)):
            self.party_target_index = self.party_index
            if len(self.party) == 1:
                self.apply_party_item()

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
        # Verifica se o jogo terminou (Game Over)
        if self.game_over:
            self.result = RESULT_QUIT
            return
        if event.type == pygame.QUIT:
            self.result = RESULT_QUIT
            return
        
        if event.type == pygame.QUIT:
            self.result = RESULT_QUIT
            return
        if self.pause is not None:
            self.pause.handle_event(event)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pause = PauseMenu(self)
            return
        if self.party_view is not None:
            self.handle_party_event(event)
            return
        if self.examined is not None:
            self.handle_details_event(event)
            return

        # NEW: Theron dialog owns input while open
        if self.theron_dialog is not None and self.theron_dialog.open:
            if self.theron_dialog.handle_event(event) == "closed":
                self.theron_dialog = None
            return

        # NEW: Aveline dialog owns input while open
        if self.aveline_dialog is not None and self.aveline_dialog.open:
            if self.aveline_dialog.handle_event(event) == "closed":
                self.aveline_dialog = None
            return

        if self.edrick_dialog is not None and self.edrick_dialog.open:
            if self.edrick_dialog.handle_event(event) == "closed":
                self.edrick_dialog = None
                if self.edrick_shop is None:
                    #No shop queued, return to plaza
                    self.city.set_screen("plaza")
            return 
        if self.edrick_shop is not None:
            if self.edrick_shop.handle_event(event) == "exit":
                self.edrick_shop = None
                self.city.set_screen("plaza")
            return

        if ((self.outside or not self.panel) and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.hero_portrait_rect().collidepoint(event.pos)):
            self.party_view = "character"
            self.party_index = 0
            self.party_scroll = 0
            return
        if self.blacksmith is not None:
            if self.blacksmith.handle_event(event) == "exit":
                self.blacksmith = None
            return
        if self.outside:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                location = self.city.handle_click(event.pos)
                if location == "tavern":
                    self.outside = False
                elif location == "shop":
                    self.blacksmith = Blacksmith(self.window, self.party)
                elif self.city.screen=="edrick" and self.edrick_dialog is None:
                    self.open_edrick_dialogue()
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
            self.open_theron_dialogue()
        elif AVELINE.collidepoint(event.pos):
            self.open_aveline_dialogue()
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
        location = ("blacksmith" if self.blacksmith is not None else
                    self.city.screen if self.outside else "tavern")
        return GameState(self.hero, self.party, self.recruits, self.accepted_quests,
                         location, self.theron_intro_seen, self.aveline_intro_seen,
                         set(self.theron_rumors_heard), set(self.aveline_rumors_heard),
                         self.edrick_mission_accepted, self.edrick_cellar_cleared)

    def apply_state(self, state):
        self.hero = state.hero
        self.party = state.party
        self.recruits = state.recruits
        self.accepted_quests = state.accepted_quests
        self.theron_intro_seen = state.theron_intro_seen
        self.theron_rumors_heard = set(state.theron_rumors_heard)
        self.aveline_dialog = None
        self.aveline_intro_seen = state.aveline_intro_seen
        self.aveline_rumors_heard = set(state.aveline_rumors_heard)
        self.edrick_dialog = None
        self.edrick_shop = None
        self.edrick_mission_accepted = state.edrick_mission_accepted
        self.edrick_cellar_cleared = state.edrick_cellar_cleared
        self.outside = state.location in ("outside", "blacksmith", "plaza", "county", "edrick")
        self.city.set_screen(state.location if state.location in ("plaza", "county", "edrick")
                             else "outside")
        self.blacksmith = (Blacksmith(self.window, self.party)
                           if state.location == "blacksmith" else None)
        self.city.message = ""
        self.panel = None
        self.theron_dialog = None
        self.examined = None
        self.party_view = None
        self.party_index = 0
        self.party_scroll = 0
        self.clear_party_selection()
        self.board_tab = "quests"
        self.details_scroll = 0
        if state.location == "edrick":
            self.open_edrick_dialogue()

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
