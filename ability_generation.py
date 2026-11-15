"""
Ability score generation methods used during character creation
"""
import dice

ABILITIES = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)

POOL_VALUES = (15, 14, 13, 12, 10, 8)

POINT_BUY_TOTAL = 27
POINT_BUY_MIN = 8
POINT_BUY_MAX = 15
POINT_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}

METHOD_RANDOM = "random"
METHOD_POOL = "pool"
METHOD_POINT_BUY = "point_buy"


class AbilityGenerator:
    """Holds the ability scores being built for the selected method"""

    def __init__(self):
        self.method = METHOD_RANDOM
        self.scores = {}
        self.set_method(METHOD_RANDOM)

    def set_method(self, method):
        self.method = method
        if method == METHOD_RANDOM:
            self.roll()
        elif method == METHOD_POOL:
            self.scores = {name: None for name in ABILITIES}
        elif method == METHOD_POINT_BUY:
            self.scores = {name: POINT_BUY_MIN for name in ABILITIES}
        else:
            raise ValueError(f"Unknown method: {method}")

    def roll(self):
        """Roll every ability with 4d6 drop lowest"""
        self.scores = {name: dice.ability_score() for name in ABILITIES}

    def cycle_pool(self, ability, step=1):
        """Assign the next/previous free pool value to an ability"""
        used = [
            value for name, value in self.scores.items()
            if name != ability and value is not None
        ]
        # Handles repeated values in the pool (e.g. a pool with two 12s)
        available = list(POOL_VALUES)
        for value in used:
            available.remove(value)
        options = [None] + sorted(available, reverse=True)
        current = self.scores[ability]
        index = options.index(current) if current in options else 0
        self.scores[ability] = options[(index + step) % len(options)]

    def points_spent(self):
        return sum(POINT_COSTS[score] for score in self.scores.values())

    def points_left(self):
        return POINT_BUY_TOTAL - self.points_spent()

    def can_adjust(self, ability, step):
        """Whether a point buy score can move by step (+1/-1)"""
        new_score = self.scores[ability] + step
        if not POINT_BUY_MIN <= new_score <= POINT_BUY_MAX:
            return False
        extra = POINT_COSTS[new_score] - POINT_COSTS[self.scores[ability]]
        return extra <= self.points_left()

    def adjust(self, ability, step):
        if self.can_adjust(ability, step):
            self.scores[ability] += step

    def is_complete(self):
        return all(score is not None for score in self.scores.values())
