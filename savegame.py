"""Versioned JSON saves for the current game state."""

import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from character import Character
from character_creation import PORTRAITS_DIR, load_portraits
from equipment import Armor, Equipment, HealingPotion, RationPack, Shield, Weapon
from party import Party
from spell import SPELL_LIBRARY

SAVE_PATH = Path(__file__).resolve().parent / "savegame.json"
VERSION = 1


class SaveError(ValueError):
    """A game state cannot be saved or a save file is invalid."""


@dataclass
class GameState:
    hero: Character
    party: Party
    recruits: list[tuple[Character, str]]
    accepted_quests: set[str]
    location: str


INT_FIELDS = (
    "level", "strength", "dexterity", "constitution", "intelligence", "wisdom",
    "charisma", "max_hp", "current_hp", "base_attack_bonus", "_armor_class_bonus",
    "fortitude_save", "reflex_save", "will_save", "experience",
)


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
    if item_type not in (Equipment, Weapon, Armor, Shield, HealingPotion, RationPack):
        raise SaveError(f"Item não suportado no salvamento: {type(item).__name__}")
    data = {"type": item_type.__name__, "name": item.name,
            "cost": item.cost, "weight": item.weight}
    if item_type is Weapon:
        data.update(damage=item.damage, damage_type=item.damage_type, ranged=item.ranged,
                    finesse=item.finesse, magic_bonus=item.magic_bonus)
    elif item_type is Armor:
        data.update(base_ac=item.base_ac, category=item.category, magic_bonus=item.magic_bonus)
    elif item_type is Shield:
        data["ac_bonus"] = item.ac_bonus
    elif item_type is HealingPotion:
        data["used"] = item.used
    elif item_type is RationPack:
        data["quantity"] = item.quantity
    return data


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
        return Weapon(name, cost, weight, _string(data["damage"], "dano"),
                      _string(data["damage_type"], "tipo de dano"),
                      ranged=ranged, finesse=finesse,
                      magic_bonus=_integer(data["magic_bonus"], "bônus mágico"))
    if kind == "Armor":
        return Armor(name, cost, weight, _integer(data["base_ac"], "CA"),
                     _string(data["category"], "categoria"),
                     magic_bonus=_integer(data["magic_bonus"], "bônus mágico"))
    if kind == "Shield":
        return Shield(name, cost, weight, _integer(data["ac_bonus"], "bônus de CA"))
    if kind == "Equipment":
        return Equipment(name, cost, weight)
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
        return item
    raise SaveError(f"Tipo de item desconhecido: {kind}")


def _spell_key(spell):
    for key, known in SPELL_LIBRARY.items():
        if type(spell) is type(known) and vars(spell) == vars(known):
            return key
    raise SaveError(f"Magia não suportada no salvamento: {spell.name}")


def _character_data(character):
    if character.portrait is not None and character.portrait_id is None:
        raise SaveError(f"Retrato de {character.name} não possui identificador")
    if character.portrait_id is not None:
        portraits = {path.stem for path in PORTRAITS_DIR.glob("*.png")}
        if character.portrait is None or character.portrait_id not in portraits:
            raise SaveError(f"Retrato inválido de {character.name}")
    equipped = {}
    for slot in ("weapon", "armor", "shield"):
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
        "spell_slots": character.spell_slots,
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
    character.inventory = [_item_from_data(item)
                           for item in _list(data["inventory"], "inventário")]
    equipped = _object(data["equipped"], "equipamentos")
    for slot, expected in (("weapon", Weapon), ("armor", Armor), ("shield", Shield)):
        index = equipped[slot]
        if index is None:
            continue
        index = _integer(index, slot)
        if not 0 <= index < len(character.inventory):
            raise SaveError(f"Índice de equipamento inválido: {slot}")
        item = character.inventory[index]
        if not isinstance(item, expected):
            raise SaveError(f"Equipamento inválido: {slot}")
        character.equip(item)
    character.known_spells = []
    for key in _list(data["known_spells"], "magias"):
        key = _string(key, "magia")
        if key not in SPELL_LIBRARY:
            raise SaveError(f"Magia desconhecida: {key}")
        character.known_spells.append(SPELL_LIBRARY[key])
    slots = _object(data["spell_slots"], "espaços de magia")
    character.spell_slots = {}
    for key, value in slots.items():
        if not isinstance(key, str) or not key.isdigit():
            raise SaveError("Nível de magia inválido")
        character.spell_slots[int(key)] = _integer(value, "espaços de magia")
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
    if state.location not in ("tavern", "outside"):
        raise SaveError("Local desconhecido")
    return {"version": VERSION, "characters": [_character_data(c) for c in characters],
            "members": members, "recruits": recruits, "quests": sorted(state.accepted_quests),
            "location": state.location, "position": state.party.position}


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
    if location not in ("tavern", "outside"):
        raise SaveError("Local desconhecido")
    return GameState(characters[0], party, recruits, quests, location)


def save_game(state: GameState, path: Path = SAVE_PATH):
    try:
        contents = json.dumps(_state_data(state), ensure_ascii=False, indent=2, allow_nan=False)
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
