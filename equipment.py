"""Equipment based on the System Reference Document 5.2.1.

Prices are in gold pieces and weights are in pounds.
"""

import math
import re
from typing import Callable, TYPE_CHECKING

import dice

if TYPE_CHECKING:
    from character import Character


class Equipment:
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

    def __str__(self) -> str:
        return self.name


class Weapon(Equipment):
    def __init__(
        self, name: str, cost: float, weight: float, damage: str,
        damage_type: str, *, ranged: bool = False, finesse: bool = False,
        magic_bonus: int = 0,
    ):
        super().__init__(name, cost, weight)
        if not re.fullmatch(r"[1-9]\d*d[1-9]\d*(?:[+-]\d+)?", damage):
            raise ValueError("Damage must use dice notation, such as 1d8")
        if not damage_type.strip():
            raise ValueError("A damage type is required")
        if not isinstance(magic_bonus, int):
            raise ValueError("Magic bonus must be an integer")
        self.damage = damage
        self.damage_type = damage_type
        self.ranged = ranged
        self.finesse = finesse
        self.magic_bonus = magic_bonus


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


class RationPack(Equipment):
    def __init__(self):
        super().__init__("Rations (10)", 1, 20)
        self.quantity = 10


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
    def __init__(self):
        super().__init__("Potion of Healing", 50, 0.5, self._heal)

    @staticmethod
    def _heal(target: "Character") -> str:
        before = target.current_hp
        target.heal(dice.d4(2, 2))
        return f"{target.name} regains {target.current_hp - before} HP"


# A small selection of standard equipment; additional items can use the classes.
def longsword() -> Weapon:
    return Weapon("Longsword", 15, 3, "1d8", "slashing")


def dagger() -> Weapon:
    return Weapon("Dagger", 2, 1, "1d4", "piercing", finesse=True)


def shortbow() -> Weapon:
    return Weapon("Shortbow", 25, 2, "1d6", "piercing", ranged=True)


def leather_armor() -> Armor:
    return Armor("Leather Armor", 10, 10, 11, "light")


def chain_shirt() -> Armor:
    return Armor("Chain Shirt", 50, 20, 13, "medium")


def chain_mail() -> Armor:
    return Armor("Chain Mail", 75, 55, 16, "heavy")
