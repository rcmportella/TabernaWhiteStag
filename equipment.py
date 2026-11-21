"""Equipment based on the System Reference Document 5.2.1.

Prices are in gold pieces and weights are in pounds.
"""

import math
import re
from pathlib import Path
from typing import Callable, TYPE_CHECKING

import dice

if TYPE_CHECKING:
    from character import Character
    from monster import Monster

ITEMS_DIR = Path(__file__).resolve().parent / "Resources" / "Items"


class Equipment:
    image_name: str | None = None

    def __init__(self, name: str, cost: float, weight: float):
        if not name.strip():
            raise ValueError("Equipment must have a name")
        if not math.isfinite(cost) or cost < 0:
            raise ValueError("Cost must be a nonnegative finite number")
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("Weight must be a nonnegative finite number")
        self.name = name
        self.cost = cost
        self.weight = weight

    @property
    def image(self) -> Path | None:
        name = self.image_name if self.image_name is not None else f"{self.name}.png"
        if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name:
            raise ValueError("Equipment image must be a filename")
        for filename in (name, name.replace(" ", "")):
            path = ITEMS_DIR / filename
            if path.is_file():
                return path
        return None

    def __str__(self) -> str:
        return self.name


class Weapon(Equipment):
    def __init__(
        self, name: str, cost: float, weight: float, damage: str,
        damage_type: str, *, ranged: bool = False, finesse: bool = False,
        magic_bonus: int = 0, two_handed: bool = False, thrown: bool = False,
        light: bool = False, versatile: bool = False, martial: bool = False,
        heavy: bool = False, reach: bool = False
    ):
        super().__init__(name, cost, weight)
        if not re.fullmatch(r"[1-9]\d*d[1-9]\d*(?:[+-]\d+)?", damage):
            raise ValueError("Damage must use dice notation, such as 1d8")
        if not damage_type.strip():
            raise ValueError("A damage type is required")
        if not isinstance(magic_bonus, int):
            raise ValueError("Magic bonus must be an integer")
        if type(two_handed) is not bool:
            raise TypeError("two_handed must be a boolean")
        if type(thrown) is not bool:
            raise TypeError("thrown must be a boolean")
        if type(light) is not bool:
            raise TypeError("light must be a boolean")
        if type(versatile) is not bool:
            raise TypeError("versatile must be a boolean")
        if type(martial) is not bool:
            raise TypeError("martial must be a boolean")
        if type(heavy) is not bool:
            raise TypeError("heavy must be a boolean")
        if type(reach) is not bool:
            raise TypeError("reach must be a boolean")
        self.damage = damage
        self.damage_type = damage_type
        self.ranged = ranged
        self.finesse = finesse
        self.magic_bonus = magic_bonus
        self.two_handed = two_handed
        self.thrown = thrown
        self.light = light
        self.versatile = versatile
        self.martial = martial
        self.heavy = heavy
        self.reach = reach


class Armor(Equipment):
    def __init__(
        self, name: str, cost: float, weight: float, base_ac: int,
        category: str, *, magic_bonus: int = 0,
    ):
        super().__init__(name, cost, weight)
        if category not in ("light", "medium", "heavy"):
            raise ValueError("Armor category must be light, medium, or heavy")
        if not isinstance(base_ac, int) or base_ac < 0:
            raise ValueError("Base AC must be a nonnegative integer")
        if not isinstance(magic_bonus, int):
            raise ValueError("Magic bonus must be an integer")
        self.base_ac = base_ac
        self.category = category
        self.magic_bonus = magic_bonus

    def armor_class(self, dexterity_modifier: int) -> int:
        if self.category == "heavy":
            dexterity_modifier = 0
        elif self.category == "medium":
            dexterity_modifier = min(dexterity_modifier, 2)
        return self.base_ac + dexterity_modifier + self.magic_bonus


class Shield(Equipment):
    def __init__(self, name: str, cost: float, weight: float, ac_bonus: int):
        super().__init__(name, cost, weight)
        if not isinstance(ac_bonus, int) or ac_bonus < 0:
            raise ValueError("Shield AC bonus must be a nonnegative integer")
        self.ac_bonus = ac_bonus


class Ring(Equipment):
    def __init__(self, name: str, cost: float, weight: float, ac_bonus: int):
        super().__init__(name, cost, weight)
        if type(ac_bonus) is not int or ac_bonus < 0:
            raise ValueError("Ring AC bonus must be a nonnegative integer")
        self.ac_bonus = ac_bonus


class RationPack(Equipment):
    image_name = "Ration.png"
    consumable = True

    def __init__(self):
        super().__init__("Rations (10)", 1, 20)
        self.quantity = 10

    def use(self, target: "Character") -> str:
        if self.quantity <= 0:
            raise ValueError("Não há rações neste pacote")
        self.quantity -= 1
        return f"{target.name} usou uma ração. Restantes: {self.quantity}."


class Potion(Equipment):
    consumable = True

    def __init__(
        self, name: str, cost: float, weight: float,
        effect: Callable[["Character"], str],
    ):
        super().__init__(name, cost, weight)
        if not callable(effect):
            raise TypeError("Potion effect must be callable")
        self.effect = effect
        self.used = False

    def use(self, target: "Character") -> str:
        if self.used:
            raise ValueError(f"{self.name} has already been used")
        result = self.effect(target)
        self.used = True
        return result


class HealingPotion(Potion):
    image_name = "HealingPotion.png"

    def __init__(self):
        super().__init__("Potion of Healing", 50, 0.5, self._heal)

    @staticmethod
    def _heal(target: "Character") -> str:
        before = target.current_hp
        target.heal(dice.d4(2, 2))
        return f"{target.name} regains {target.current_hp - before} HP"

class HolyWater(Equipment):
    """A single-use vial that damages undead and fiends."""

    consumable = True

    def __init__(self, name="Holy Water", cost=25, weight=1):
        super().__init__(name, cost, weight)
        self.is_holy_water = True
        self.used = False

    def use(self, target: "Character | Monster") -> str:
        from character import Character
        from monster import Monster

        if self.used:
            raise ValueError(f"{self.name} has already been used")
        if not isinstance(target, (Character, Monster)):
            raise TypeError("Holy water requires a character or monster target")
        if target.creature_type is None:
            raise ValueError(f"Creature type is not defined for {target.name}")
        if target.creature_type in ("undead", "fiend"):
            damage = dice.d8(2)
            target.take_damage(damage)
            result = f"{target.name} takes {damage} radiant damage from {self.name}."
        else:
            result = f"{self.name} has no effect on {target.name}."
        self.used = True
        return result

class HolySymbol(Equipment):
    """Holy Symbol - material component for Cleric/Paladin spells"""
    
    def __init__(self, name="Holy Symbol", cost=5, weight=1):
        super().__init__(name, cost, weight)
        # Pode ser um amuleto, emblema, relicário, etc.
        self.is_holy_symbol = True


# A small selection of standard equipment; additional items can use the classes.
def dagger() -> Weapon:
    return Weapon("Dagger", 2, 1, "1d4", "piercing", finesse=True, light=True, thrown=True)
def mace() -> Weapon:
    return Weapon("Mace", 5, 4, "1d6", "bludgeoning")
def club() -> Weapon:
    return Weapon("Club", 1, 2, "1d4", "bludgeoning")
def greatclub() -> Weapon:
    return Weapon("Greatclub", 2, 10, "1d8", "bludgeoning", two_handed=True)
def handaxe() -> Weapon:
    return Weapon("Handaxe", 5, 2, "1d6", "slashing", thrown=True, light=True)
def javelin() -> Weapon:
    return Weapon("Javelin", 1, 2, "1d6", "piercing", thrown=True)
def light_hammer() -> Weapon:
    return Weapon("Light Hammer", 2, 2, "1d4", "bludgeoning", thrown=True, light=True)
def sickle() -> Weapon:
    return Weapon("Sickle", 1, 2, "1d4", "slashing", light=True)
def quarterstaff() -> Weapon:
    return Weapon("Quarterstaff", 2, 4, "1d6", "bludgeoning", versatile=True)
def spear() -> Weapon:
    return Weapon("Spear", 1, 3, "1d6", "piercing", thrown=True, versatile=True)
def dart() -> Weapon:
    return Weapon("Dart", 0.25, 0.25, "1d4", "piercing", finesse=True, thrown=True)
def light_crossbow() -> Weapon:
    return Weapon("Light Crossbow", 25, 5, "1d8", "piercing", ranged=True, two_handed=True)
def short_bow() -> Weapon:
    return Weapon("Shortbow", 25, 2, "1d6", "piercing", ranged=True, two_handed=True)
shortbow = short_bow

def sling() -> Weapon:
    return Weapon("Sling", 0.5, 0.5, "1d4", "bludgeoning", ranged=True)
def battleaxe() -> Weapon:
    return Weapon("Battleaxe", 10, 4, "1d8", "slashing", versatile=True, martial=True)
def flail() -> Weapon:
    return Weapon("Flail", 10, 2, "1d8", "bludgeoning", martial=True)
def glaive() -> Weapon:
    return Weapon("Glaive", 20, 6, "1d10", "slashing", two_handed=True, martial=True, reach=True, heavy=True)
def greataxe() -> Weapon:
    return Weapon("Greataxe", 30, 7, "1d12", "slashing", two_handed=True, heavy=True)
def greatsword() -> Weapon:
    return Weapon("Greatsword", 50, 6, "2d6", "slashing", two_handed=True, heavy=True)
def halberd() -> Weapon:
    return Weapon("Halberd", 20, 6, "1d10", "slashing", two_handed=True, martial=True, reach=True, heavy=True)
def lance() -> Weapon:
    return Weapon("Lance", 10, 6, "1d10", "piercing", reach=True, heavy=True, two_handed=True, martial=True)
def longsword() -> Weapon:
    return Weapon("Longsword", 15, 3, "1d8", "slashing", martial=True, versatile=True)
def maul() -> Weapon:
    return Weapon("Maul", 10, 10, "2d6", "bludgeoning", two_handed=True, heavy=True, martial=True)
def morningstar() -> Weapon:
    return Weapon("Morningstar", 15, 4, "1d8", "piercing", martial=True)
def pike() -> Weapon:
    return Weapon("Pike", 5, 18, "1d10", "piercing", two_handed=True, reach=True, heavy=True, martial=True)
def rapier() -> Weapon:
    return Weapon("Rapier", 25, 2, "1d8", "piercing", finesse=True, martial=True)
def scimitar() -> Weapon:
    return Weapon("Scimitar", 25, 3, "1d6", "slashing", finesse=True, martial=True, light=True)
def shortsword() -> Weapon:
    return Weapon("Shortsword", 10, 2, "1d6", "piercing", finesse=True, martial=True, light=True)
def trident() -> Weapon:
    return Weapon("Trident", 5, 4, "1d8", "piercing", thrown=True, versatile=True, martial=True)
def warhammer() -> Weapon:
    return Weapon("Warhammer", 15, 5, "1d8", "bludgeoning", versatile=True, martial=True)
def warpick() -> Weapon:
    return Weapon("Warpick", 5, 2, "1d8", "piercing", martial=True, versatile=True)
def whip() -> Weapon:
    return Weapon("Whip", 2, 3, "1d4", "slashing", finesse=True, reach=True, martial=True)
def handcrossbow() -> Weapon:
    return Weapon("Hand Crossbow", 75, 3, "1d6", "piercing", ranged=True, light=True)
def heavy_crossbow() -> Weapon:
    return Weapon("Heavy Crossbow", 50, 18, "1d10", "piercing", ranged=True, heavy=True, two_handed=True)
def longbow() -> Weapon:
    return Weapon("Longbow", 50, 2, "1d8", "piercing", ranged=True, heavy=True, two_handed=True)
def padded_armor() -> Armor:
    return Armor("Padded Armor", 5, 8, 11, "light")
def leather_armor() -> Armor:
    return Armor("Leather Armor", 10, 10, 11, "light")

def studded_leather_armor() -> Armor:
    return Armor("Studded Leather Armor", 45, 13, 12, "light")
def hide_armor() -> Armor:
    return Armor("Hide Armor", 10, 12, 12, "medium")
def chain_shirt() -> Armor:
    return Armor("Chain Shirt", 50, 20, 13, "medium")
def scale_mail() -> Armor:
    return Armor("Scale Mail", 50, 45, 14, "medium")
def breastplate() -> Armor:
    return Armor("Breastplate", 400, 20, 14, "medium")
def half_plate_armor() -> Armor:
    return Armor("Half Plate Armor", 750, 40, 15, "medium")
def ring_mail() -> Armor:
    return Armor("Ring Mail", 30, 40, 14, "heavy")
def chain_mail() -> Armor:
    return Armor("Chain Mail", 75, 55, 16, "heavy")

def splint_armor() -> Armor:
    return Armor("Splint Armor", 200, 60, 17, "heavy")

def plate_armor() -> Armor:
    return Armor("Plate Armor", 1500, 65, 18, "heavy")
def small_shield() -> Shield:
    return Shield("Small Shield", 10, 6, 2)

def large_shield() -> Shield:
    return Shield("Large Shield", 30, 10, 3)
def kite_shield() -> Shield:
    return Shield("Kite Shield", 100, 8, 3)

def ring_of_protection() -> Ring:
    return Ring("Ring of Protection +1", 1000, 0, 1)


def rope() -> Equipment:
    return Equipment("Rope", 1, 5)
def spellbook() -> Equipment:
    return Equipment("Spellbook", 100, 10)
def holy_symbol() -> HolySymbol:
    return HolySymbol()
def torch() -> Equipment:
    return Equipment("Torch", 0.1, 1)
def crowbar() -> Equipment:
    return Equipment("Crowbar", 2, 5)
def lantern() -> Equipment:
    return Equipment("Lantern", 5, 2)
def shovel() -> Equipment:
    return Equipment("Shovel", 2, 5)

