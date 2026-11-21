"""Versioned JSON saves for the current game state."""

import json
import math
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from character import Character, PREPARED_SPELL_LIMITS
from character_creation import PORTRAITS_DIR, load_portraits
from equipment import (
    Armor, Equipment, HealingPotion, HolySymbol, HolyWater, RationPack, Ring, Shield, Weapon,
)
from party import Party
from spell import SPELL_LIBRARY

SAVE_PATH = Path(__file__).resolve().parent / "savegame.json"
SLOT_COUNT = 4
VERSION = 1


def slot_path(slot: int, directory: Path = SAVE_PATH.parent) -> Path:
    if type(slot) is not int or not 1 <= slot <= SLOT_COUNT:
        raise ValueError(f"Slot deve estar entre 1 e {SLOT_COUNT}")
    return directory / ("savegame.json" if slot == 1 else f"savegame_{slot}.json")


def slot_exists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


class SaveError(ValueError):
    """A game state cannot be saved or a save file is invalid."""


def _slot_orders(directory: Path, exclude: int | None = None):
    orders = []
    for slot in range(1, SLOT_COUNT + 1):
        if slot == exclude:
            continue
        path = slot_path(slot, directory)
        try:
            try:
                modified = path.lstat().st_mtime_ns
            except FileNotFoundError:
                continue
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("conteúdo inválido")
            order = data.get("save_order", modified)
            if type(order) is not int or order < 0:
                raise ValueError("ordem de salvamento inválida")
            orders.append((order, slot))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            raise SaveError(f"Não foi possível verificar o slot {slot}: {exc}") from exc
    return orders


def last_saved_slot(directory: Path = SAVE_PATH.parent) -> int | None:
    orders = _slot_orders(directory)
    if not orders:
        return None
    latest = max(order for order, _ in orders)
    slots = [slot for order, slot in orders if order == latest]
    if len(slots) != 1:
        raise SaveError("Não foi possível determinar o último slot salvo; escolha um slot.")
    return slots[0]


@dataclass
class GameState:
    hero: Character
    party: Party
    recruits: list[tuple[Character, str]]
    accepted_quests: set[str]
    location: str
    theron_intro_seen: bool = False
    aveline_intro_seen: bool = False
    theron_rumors_heard: set[str] = field(default_factory=set)
    aveline_rumors_heard: set[str] = field(default_factory=set)
    edrick_mission_accepted: bool = False
    edrick_cellar_cleared: bool = False


INT_FIELDS = (
    "level", "strength", "dexterity", "constitution", "intelligence", "wisdom",
    "charisma", "max_hp", "current_hp", "base_attack_bonus", "_armor_class_bonus",
    "fortitude_save", "reflex_save", "will_save", "experience",
)
WEAPON_FLAGS = ("thrown", "light", "versatile", "martial", "heavy", "reach")


def _integer(value, field):
    if type(value) is not int:
        raise SaveError(f"{field} deve ser um número inteiro")
    return value


def _number(value, field):
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        raise SaveError(f"{field} deve ser um número")
    return value


def _string(value, field):
    if not isinstance(value, str) or not value:
        raise SaveError(f"{field} deve ser um texto não vazio")
    return value


def _optional_string(value, field):
    return None if value is None else _string(value, field)


def _list(value, field):
    if not isinstance(value, list):
        raise SaveError(f"{field} deve ser uma lista")
    return value


def _object(value, field):
    if not isinstance(value, dict):
        raise SaveError(f"{field} deve ser um objeto")
    return value


def _item_data(item):
    if isinstance(item, str):
        return {"type": "text", "value": item}
    item_type = type(item)
    if item_type not in (Equipment, Weapon, Armor, Shield, Ring, HealingPotion, HolySymbol,
                         HolyWater, RationPack):
        raise SaveError(f"Item não suportado no salvamento: {type(item).__name__}")
    data = {"type": item_type.__name__, "name": item.name,
            "cost": item.cost, "weight": item.weight, "image_name": item.image_name}
    if item_type is Weapon:
        data.update(damage=item.damage, damage_type=item.damage_type, ranged=item.ranged,
                    finesse=item.finesse, magic_bonus=item.magic_bonus,
                    two_handed=item.two_handed)
        data.update({flag: getattr(item, flag) for flag in WEAPON_FLAGS})
    elif item_type is Armor:
        data.update(base_ac=item.base_ac, category=item.category, magic_bonus=item.magic_bonus)
    elif item_type in (Shield, Ring):
        data["ac_bonus"] = item.ac_bonus
    elif item_type in (HealingPotion, HolyWater):
        data["used"] = item.used
    elif item_type is RationPack:
        data["quantity"] = item.quantity
    return data


def _item_image_from_data(item, data):
    if "image_name" in data:
        name = data["image_name"]
        if (name is not None and
                (not isinstance(name, str) or not name or Path(name).name != name or "\\" in name)):
            raise SaveError("Nome da imagem do equipamento inválido")
        item.image_name = name
    return item


def _item_from_data(data):
    data = _object(data, "item")
    kind = _string(data["type"], "tipo do item")
    if kind == "text":
        return _string(data["value"], "item")
    name = _string(data["name"], "nome do item")
    cost = _number(data["cost"], "custo")
    weight = _number(data["weight"], "peso")
    if kind == "Weapon":
        ranged, finesse = data["ranged"], data["finesse"]
        if type(ranged) is not bool or type(finesse) is not bool:
            raise SaveError("Propriedades de arma inválidas")
        two_handed = data.get("two_handed", name.casefold() == "shortbow" and ranged)
        if type(two_handed) is not bool:
            raise SaveError("Propriedade de duas mãos inválida")
        flags = {flag: data.get(flag, False) for flag in WEAPON_FLAGS}
        if any(type(value) is not bool for value in flags.values()):
            raise SaveError("Propriedades de arma inválidas")
        return _item_image_from_data(
            Weapon(name, cost, weight, _string(data["damage"], "dano"),
                   _string(data["damage_type"], "tipo de dano"),
                   ranged=ranged, finesse=finesse,
                   magic_bonus=_integer(data["magic_bonus"], "bônus mágico"),
                   two_handed=two_handed, **flags), data)
    if kind == "Armor":
        return _item_image_from_data(
            Armor(name, cost, weight, _integer(data["base_ac"], "CA"),
                  _string(data["category"], "categoria"),
                  magic_bonus=_integer(data["magic_bonus"], "bônus mágico")), data)
    if kind == "Shield":
        return _item_image_from_data(
            Shield(name, cost, weight, _integer(data["ac_bonus"], "bônus de CA")), data)
    if kind == "Ring":
        return _item_image_from_data(
            Ring(name, cost, weight, _integer(data["ac_bonus"], "bônus de CA")), data)
    if kind == "Equipment":
        return _item_image_from_data(Equipment(name, cost, weight), data)
    if kind == "HolySymbol":
        return _item_image_from_data(HolySymbol(name, cost, weight), data)
    if kind == "HolyWater":
        if type(data["used"]) is not bool:
            raise SaveError("Estado da água benta inválido")
        item = HolyWater(name, cost, weight)
        item.used = data["used"]
        return _item_image_from_data(item, data)
    if kind in ("HealingPotion", "RationPack"):
        Equipment(name, cost, weight)
        item = HealingPotion() if kind == "HealingPotion" else RationPack()
        item.name, item.cost, item.weight = name, cost, weight
        if kind == "HealingPotion":
            if type(data["used"]) is not bool:
                raise SaveError("Estado da poção inválido")
            item.used = data["used"]
        else:
            item.quantity = _integer(data["quantity"], "quantidade de rações")
            if item.quantity < 0:
                raise SaveError("Quantidade de rações inválida")
        return _item_image_from_data(item, data)
    raise SaveError(f"Tipo de item desconhecido: {kind}")


def _spell_key(spell):
    for key, known in SPELL_LIBRARY.items():
        if type(spell) is type(known) and vars(spell) == vars(known):
            return key
    raise SaveError(f"Magia não suportada no salvamento: {spell.name}")


def _character_data(character):
    if any(spell.level == 0 for spell in
           character.prepared_spells + character.always_prepared_spells):
        raise SaveError("Truques não podem ocupar vagas de magias preparadas")
    if (isinstance(character.equipped_weapon, Weapon)
            and character.equipped_weapon.two_handed
            and character.equipped_shield is not None):
        raise SaveError(f"{character.name} não pode usar escudo com arma de duas mãos")
    if (character.equipped_ring_left is not None
            and character.equipped_ring_left is character.equipped_ring_right):
        raise SaveError("O mesmo anel não pode ocupar os dois espaços")
    if character.portrait is not None and character.portrait_id is None:
        raise SaveError(f"Retrato de {character.name} não possui identificador")
    if character.portrait_id is not None:
        portraits = {path.stem for path in PORTRAITS_DIR.glob("*.png")}
        if character.portrait is None or character.portrait_id not in portraits:
            raise SaveError(f"Retrato inválido de {character.name}")
    equipped = {}
    for slot in ("weapon", "armor", "shield", "ring_left", "ring_right"):
        item = getattr(character, f"equipped_{slot}")
        if item is None:
            equipped[slot] = None
        else:
            index = next((i for i, existing in enumerate(character.inventory)
                          if existing is item), None)
            if index is None:
                raise SaveError(f"Equipamento de {character.name} não está no inventário")
            equipped[slot] = index
    return {
        "name": character.name, "char_class": character.char_class,
        "gender": character.gender, "alignment": character.alignment,
        "portrait_id": character.portrait_id,
        **{field: getattr(character, field) for field in INT_FIELDS},
        "gold": character.gold,
        "inventory": [_item_data(item) for item in character.inventory],
        "equipped": equipped,
        "known_spells": [_spell_key(spell) for spell in character.known_spells],
        "prepared_spells": [_spell_key(spell) for spell in character.prepared_spells],
        "always_prepared_spells": [_spell_key(spell) for spell in character.always_prepared_spells],
        "preparation_replacements": character.preparation_replacements,
        "spell_slots": character.spell_slots,
        "layonhands_pool": character.layonhands_pool,
    }


def _character_from_data(data, portraits):
    data = _object(data, "personagem")
    values = {field: _integer(data[field], field) for field in INT_FIELDS}
    if values["level"] < 1 or values["max_hp"] < 1:
        raise SaveError("Nível ou pontos de vida máximos inválidos")
    character = Character(_string(data["name"], "nome"),
                          _string(data["char_class"], "classe"), values["level"])
    for field, value in values.items():
        setattr(character, field, value)
    character.gold = _number(data["gold"], "ouro")
    character.gender = _optional_string(data["gender"], "gênero")
    character.alignment = _optional_string(data["alignment"], "alinhamento")
    character.portrait_id = _optional_string(data["portrait_id"], "retrato")
    if character.portrait_id is not None:
        if character.portrait_id not in portraits:
            raise SaveError(f"Retrato não encontrado: {character.portrait_id}")
        character.portrait = portraits[character.portrait_id]
    inventory_data = _list(data["inventory"], "inventário")
    character.inventory = [_item_from_data(item) for item in inventory_data]
    equipped = _object(data["equipped"], "equipamentos")
    for slot, expected in (("weapon", Weapon), ("armor", Armor), ("shield", Shield),
                           ("ring_left", Ring), ("ring_right", Ring)):
        index = equipped.get(slot) if slot.startswith("ring_") else equipped[slot]
        if index is None:
            continue
        index = _integer(index, slot)
        if not 0 <= index < len(character.inventory):
            raise SaveError(f"Índice de equipamento inválido: {slot}")
        item = character.inventory[index]
        if not isinstance(item, expected):
            raise SaveError(f"Equipamento inválido: {slot}")
        if (slot == "shield" and isinstance(character.equipped_weapon, Weapon)
                and character.equipped_weapon.two_handed):
            weapon_data = inventory_data[equipped["weapon"]]
            if (isinstance(weapon_data, dict) and "two_handed" not in weapon_data
                    and character.equipped_weapon.name.casefold() == "shortbow"
                    and character.equipped_weapon.ranged):
                continue
            raise SaveError("Escudo e arma de duas mãos equipados ao mesmo tempo")
        if slot == "ring_right" and character.equipped_ring_left is item:
            raise SaveError("O mesmo anel não pode ocupar os dois espaços")
        character.equip(item, slot if isinstance(item, Ring) else None)
    character.known_spells = []
    for key in _list(data["known_spells"], "magias"):
        key = _string(key, "magia")
        if key not in SPELL_LIBRARY:
            raise SaveError(f"Magia desconhecida: {key}")
        character.known_spells.append(SPELL_LIBRARY[key])
    if "prepared_spells" in data:
        legacy_lay_on_hands = False
        for key in _list(data.get("always_prepared_spells", []), "magias sempre preparadas"):
            key = _string(key, "magia sempre preparada")
            if key not in SPELL_LIBRARY or SPELL_LIBRARY[key] not in character.known_spells:
                raise SaveError(f"Magia sempre preparada desconhecida: {key}")
            if key == "lay_on_hands":
                if legacy_lay_on_hands:
                    raise SaveError("Magia sempre preparada duplicada")
                legacy_lay_on_hands = True
                continue
            if SPELL_LIBRARY[key] in character.always_prepared_spells:
                raise SaveError("Magia sempre preparada duplicada")
            character.grant_always_prepared_spell(SPELL_LIBRARY[key])
        prepared = []
        for key in _list(data["prepared_spells"], "magias preparadas"):
            key = _string(key, "magia preparada")
            if key not in SPELL_LIBRARY:
                raise SaveError(f"Magia preparada desconhecida: {key}")
            if key == "lay_on_hands" and character.char_class in PREPARED_SPELL_LIMITS:
                if SPELL_LIBRARY[key] not in character.known_spells or legacy_lay_on_hands:
                    raise SaveError("Magia preparada inválida: lay_on_hands")
                legacy_lay_on_hands = True
                continue
            prepared.append(SPELL_LIBRARY[key])
        if character.char_class in PREPARED_SPELL_LIMITS:
            character.prepare_spells(prepared)
        elif prepared:
            raise SaveError("Classe sem magias preparadas")
        replacements = data.get("preparation_replacements", 0)
        if replacements is None:
            if character.char_class not in ("Wizard", "Cleric"):
                raise SaveError("Permissão de troca de magias inválida")
        elif type(replacements) is not int or replacements < 0:
            raise SaveError("Permissão de troca de magias inválida")
        character.preparation_replacements = replacements
    elif character.prepared_spell_limit:
        max_level = (min(5, (character.level + 3) // 4)
                     if character.char_class in ("Paladin", "Ranger")
                     else min(9, (character.level + 1) // 2))
        eligible = [spell for spell in character.known_spells if 1 <= spell.level <= max_level]
        character.prepare_spells(list(dict.fromkeys(eligible))[:character.prepared_spell_limit])
    slots = _object(data["spell_slots"], "espaços de magia")
    character.spell_slots = {}
    for key, value in slots.items():
        if not isinstance(key, str) or not key.isdigit():
            raise SaveError("Nível de magia inválido")
        character.spell_slots[int(key)] = _integer(value, "espaços de magia")
    default_pool = 5 * character.level if character.char_class == "Paladin" else 0
    character.layonhands_pool = _integer(
        data.get("layonhands_pool", default_pool), "reserva de Imposição de Mãos")
    if not 0 <= character.layonhands_pool <= default_pool:
        raise SaveError("Reserva de Imposição de Mãos inválida")
    if character.char_class == "Paladin":
        character.learn_spell(SPELL_LIBRARY["lay_on_hands"])
    return character


def _state_data(state):
    characters = [state.hero]

    def index_for(character):
        for index, existing in enumerate(characters):
            if existing is character:
                return index
        characters.append(character)
        return len(characters) - 1

    if state.party.leader is not state.hero or not state.party.members or state.party.members[0] is not state.hero:
        raise SaveError("O herói deve ser o líder da companhia")
    members = [index_for(member) for member in state.party.members]
    recruits = [{"character": index_for(character), "label": label}
                for character, label in state.recruits]
    if len(set(members)) != len(members) or len(members) > 6:
        raise SaveError("Companhia inválida")
    if state.location not in ("tavern", "outside", "blacksmith", "plaza", "county", "edrick"):
        raise SaveError("Local desconhecido")
    if type(state.theron_intro_seen) is not bool:
        raise SaveError("Estado do diálogo de Theron inválido")
    if type(state.aveline_intro_seen) is not bool:
        raise SaveError("Estado do diálogo de Aveline inválido")
    if type(state.edrick_mission_accepted) is not bool:
        raise SaveError("Estado da missão de Edrick inválido")
    if type(state.edrick_cellar_cleared) is not bool:
        raise SaveError("Estado do porão de Edrick inválido")
    for rumors in (state.theron_rumors_heard, state.aveline_rumors_heard):
        if not isinstance(rumors, set):
            raise SaveError("Rumores ouvidos devem ser um conjunto")
        for rumor in rumors:
            _string(rumor, "rumor ouvido")
    return {"version": VERSION, "characters": [_character_data(c) for c in characters],
            "members": members, "recruits": recruits, "quests": sorted(state.accepted_quests),
            "location": state.location, "position": state.party.position,
            "theron_intro_seen": state.theron_intro_seen,
            "aveline_intro_seen": state.aveline_intro_seen,
            "theron_rumors_heard": sorted(state.theron_rumors_heard),
            "aveline_rumors_heard": sorted(state.aveline_rumors_heard),
            "edrick_mission_accepted": state.edrick_mission_accepted,
            "edrick_cellar_cleared": state.edrick_cellar_cleared}


def _state_from_data(data):
    data = _object(data, "salvamento")
    if type(data["version"]) is not int or data["version"] != VERSION:
        raise SaveError("Versão de salvamento não suportada")
    portraits = {f"{gender}_{name}": image
                 for gender, entries in load_portraits().items()
                 for name, image in entries}
    characters = [_character_from_data(value, portraits)
                  for value in _list(data["characters"], "personagens")]
    if not characters:
        raise SaveError("Salvamento sem herói")

    def character_at(index):
        index = _integer(index, "índice de personagem")
        if not 0 <= index < len(characters):
            raise SaveError("Índice de personagem inválido")
        return characters[index]

    members = [character_at(index) for index in _list(data["members"], "companhia")]
    if not members or members[0] is not characters[0] or len(members) > 6 or len(set(members)) != len(members):
        raise SaveError("Companhia inválida")
    party = Party(characters[0])
    party.members = members
    position = _list(data["position"], "posição")
    if len(position) != 2:
        raise SaveError("Posição inválida")
    party.position = [_integer(value, "posição") for value in position]
    recruits = []
    for value in _list(data["recruits"], "recrutas"):
        record = _object(value, "recruta")
        recruits.append((character_at(record["character"]), _string(record["label"], "classe")))
    if len({id(character) for character, _ in recruits}) != len(recruits):
        raise SaveError("Lista de recrutas duplicada")
    quests = {_string(quest, "missão") for quest in _list(data["quests"], "missões")}
    location = _string(data["location"], "local")
    if location not in ("tavern", "outside", "blacksmith", "plaza", "county", "edrick"):
        raise SaveError("Local desconhecido")
    theron_intro_seen = data.get("theron_intro_seen", False)
    if type(theron_intro_seen) is not bool:
        raise SaveError("Estado do diálogo de Theron inválido")
    aveline_intro_seen = data.get("aveline_intro_seen", False)
    if type(aveline_intro_seen) is not bool:
        raise SaveError("Estado do diálogo de Aveline inválido")
    edrick_mission_accepted = data.get("edrick_mission_accepted", False)
    if type(edrick_mission_accepted) is not bool:
        raise SaveError("Estado da missão de Edrick inválido")
    edrick_cellar_cleared = data.get("edrick_cellar_cleared", False)
    if type(edrick_cellar_cleared) is not bool:
        raise SaveError("Estado do porão de Edrick inválido")
    theron_rumors = {_string(rumor, "rumor ouvido") for rumor in
                     _list(data.get("theron_rumors_heard", []), "rumores de Theron")}
    aveline_rumors = {_string(rumor, "rumor ouvido") for rumor in
                      _list(data.get("aveline_rumors_heard", []), "rumores de Aveline")}
    return GameState(characters[0], party, recruits, quests, location, theron_intro_seen,
                     aveline_intro_seen, theron_rumors, aveline_rumors,
                     edrick_mission_accepted, edrick_cellar_cleared)


def save_game(state: GameState, path: Path = SAVE_PATH):
    try:
        data = _state_data(state)
        slot = next((index for index in range(1, SLOT_COUNT + 1)
                     if path == slot_path(index, path.parent)), None)
        if slot is not None:
            orders = _slot_orders(path.parent, exclude=slot)
            data["save_order"] = max((order for order, _ in orders), default=0) + 1
        contents = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
        _state_from_data(json.loads(contents))
    except (KeyError, TypeError, ValueError) as exc:
        raise SaveError(f"Não foi possível preparar o salvamento: {exc}") from exc
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".save-", delete=False) as handle:
            temporary_path = Path(handle.name)
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def load_game(path: Path = SAVE_PATH) -> GameState:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        return _state_from_data(data)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SaveError(f"Arquivo de salvamento inválido: {exc}") from exc
