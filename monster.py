"""
Monster and enemy classes for D20 combat
"""
from pathlib import Path

import pygame
import dice

CREATURE_TYPES = frozenset((
    "aberration", "beast", "celestial", "construct", "dragon", "elemental",
    "fey", "fiend", "giant", "humanoid", "monstrosity", "ooze", "plant", "undead",
))

# Tamanhos válidos conforme o SRD 5.2.1 (D&D 5e)
CREATURE_SIZES = frozenset(("Tiny", "Small", "Medium", "Large", "Huge"))

# No topo do arquivo, após CREATURE_SIZES:
XP_BY_CR = {
    0: 10,      # ou 0, dependendo do SRD; 10 é o valor "padrão" para CR 0
    "1/8": 25,
    "1/4": 50,
    "1/2": 100,
    1: 200,
    2: 450,
    3: 700,
    4: 1100,
    5: 1800,
    6: 2300,
    7: 2900,
    8: 3900,
    9: 5000,
    10: 5900,
    11: 7200,
    12: 8400,
    13: 10000,
    14: 11500,
    15: 13000,
    16: 15000,
    17: 18000,
    18: 20000,
    19: 22000,
    20: 25000,
}

# Diretório base para as imagens dos monstros
MONSTERS_DIR = Path(__file__).resolve().parent / "Resources" / "Monsters"


class Monster:
    """
    Generic monster/enemy following D20 rules
    """
    
    def __init__(self, name, hit_dice="1d8", armor_class=10, 
                 attack_bonus=0, damage="1d6", 
                 special_abilities=None, treasure=None, creature_type=None,
                 image_name="monstro.png", initiative_bonus=0,
                 size="Medium", challenge_rating=0, experience_points=None):
        if creature_type is not None and (
                not isinstance(creature_type, str) or creature_type not in CREATURE_TYPES):
            raise ValueError(f"Unknown creature type: {creature_type}")
        if not isinstance(size, str) or size not in CREATURE_SIZES:
            raise ValueError(f"Unknown creature size: {size!r}. "
                             f"Expected one of {sorted(CREATURE_SIZES)}")
        self.name = name
        self.creature_type = creature_type
        self.size = size
        self.hit_dice = hit_dice
        self.armor_class = armor_class
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.special_abilities = special_abilities or []
        self.treasure = treasure or []
        self.image_name = image_name
        self.initiative_bonus = initiative_bonus
        self.challenge_rating = challenge_rating
        self.experience_points = (experience_points if experience_points is not None else XP_BY_CR.get(challenge_rating, 0))
        # Calculate HP from hit dice
        self.max_hp = self._roll_hit_points()
        self.current_hp = self.max_hp
        
        # Basic saving throws (can be customized per monster)
        self.fortitude_save = 0
        self.reflex_save = 0
        self.will_save = 0

    @property
    def image(self) -> pygame.Surface | None:
        """Retorna a imagem do monstro como Surface do Pygame, com fallback para monstro.png."""
        name = self.image_name if self.image_name else "monstro.png"
        if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name:
            raise ValueError("Monster image must be a filename")
        
        path = MONSTERS_DIR / name
        if path.is_file():
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except Exception as e:
                print(f"Erro ao carregar imagem do monstro {self.name}: {e}")

        # Fallback para a imagem genérica
        generic = MONSTERS_DIR / "monstro.png"
        if generic.is_file():
            try:
                return pygame.image.load(str(generic)).convert_alpha()
            except Exception as e:
                print(f"Erro ao carregar imagem genérica do monstro {self.name}: {e}")

        return None
        
    def _roll_hit_points(self):
        """Roll hit points based on hit dice"""
        if 'd' in self.hit_dice:
            count, sides = self.hit_dice.split('d')
            count = int(count)
            sides = int(sides.split('+')[0].split('-')[0])  # Handle modifiers
            
            hp = 0
            for _ in range(count):
                hp += dice.roll(sides)
                
            # Add any flat modifier
            if '+' in self.hit_dice:
                modifier = int(self.hit_dice.split('+')[1])
                hp += modifier
            elif '-' in self.hit_dice:
                modifier = int(self.hit_dice.split('-')[1])
                hp -= modifier
                
            return max(1, hp)
        else:
            return int(self.hit_dice)
            
    def roll_initiative(self):
        """Rola a iniciativa do monstro."""
        return dice.d20(1, self.initiative_bonus)

    def get_armor_class(self):
        """Retorna a Classe de Armadura do monstro."""
        return self.armor_class  
            
    def attack(self, target):
        """
        Attack a target character.
        
        Args:
            target: Character being attacked
            
        Returns:
            Tuple of (hit: bool, damage: int, message: str)
        """
        attack_roll = dice.d20(1, self.attack_bonus)
        
        if attack_roll >= target.get_armor_class():
            # Hit!
            damage_dealt = self._roll_damage()
            target.take_damage(damage_dealt)
            return True, attack_roll, damage_dealt, f"{self.name} hits {target.name} for {damage_dealt} damage!"
        else:
            return False, attack_roll, 0, f"{self.name} misses {target.name}!"
            
    def _roll_damage(self):
        """Roll damage dice"""
        if '+' in self.damage:
            dice_part, mod = self.damage.split('+')
            mod = int(mod)
        elif '-' in self.damage:
            dice_part, mod = self.damage.split('-')
            mod = -int(mod)
        else:
            dice_part = self.damage
            mod = 0
            
        count, sides = dice_part.split('d')
        count = int(count)
        sides = int(sides)
        
        return max(1, dice.roll(sides, count, mod))
        
    def take_damage(self, damage):
        """Take damage and return True if still alive"""
        self.current_hp -= damage
        return self.current_hp > 0
        
    def is_alive(self):
        """Check if monster is still alive"""
        return self.current_hp > 0
        
    def saving_throw(self, save_type):
        """Make a saving throw"""
        if save_type == 'fortitude':
            return dice.d20(1, self.fortitude_save)
        elif save_type == 'reflex':
            return dice.d20(1, self.reflex_save)
        elif save_type == 'will':
            return dice.d20(1, self.will_save)
        else:
            return dice.d20()
            
    def __str__(self):
        return (f"{self.name} ({self.size} {self.creature_type or 'creature'}, "
                f"AC {self.armor_class}, HP {self.current_hp}/{self.max_hp}, "
                f"Init +{self.initiative_bonus})")


# Predefined monsters
class Goblin(Monster):
    """Weak humanoid enemy"""
    def __init__(self):
        super().__init__(
            name="Goblin",
            hit_dice="2d6",
            armor_class=12,
            attack_bonus=0,
            damage="1d4+2",
            creature_type="humanoid",
            treasure=["10 gold pieces"],
            image_name="goblin.png",
            initiative_bonus=2,
            size="Small"
            challenge_rating="1/4",
        )
        self.reflex_save = 3


class Orc(Monster):
    """Medium humanoid warrior"""
    def __init__(self):
        super().__init__(
            name="Orc",
            hit_dice="2d8",
            armor_class=13,
            attack_bonus=1,
            damage="1d8",
            creature_type="humanoid",
            treasure=["20 gold pieces", "Battle axe"],
            image_name="orc.png",
            initiative_bonus=1,
            size="Medium",
            challenge_rating="1/2",
        )
        self.fortitude_save = 3


class Skeleton(Monster):
    """Undead warrior"""
    def __init__(self):
        super().__init__(
            name="Skeleton",
            hit_dice="1d12",
            armor_class=13,
            attack_bonus=2,
            damage="1d6+1",
            creature_type="undead",
            special_abilities=["Undead: immune to mind-affecting"],
            treasure=[],
            image_name="skeleton.png",
            initiative_bonus=2,
            size="Medium",
            challenge_rating="1/4",
        )
        self.will_save = -2


class Ogre(Monster):
    """Large giant enemy"""
    def __init__(self):
        super().__init__(
            name="Ogre",
            hit_dice="4d8+8",
            armor_class=16,
            attack_bonus=8,
            damage="2d8+7",
            creature_type="giant",
            treasure=["50 gold pieces", "Large club"],
            image_name="ogre.png",
            initiative_bonus=-1,
            size="Large",
            challenge_rating="2",
        )
        self.fortitude_save = 5


class Dragon(Monster):
    """Powerful dragon boss"""
    def __init__(self):
        super().__init__(
            name="Young Red Dragon",
            hit_dice="16d10+48",
            armor_class=21,
            attack_bonus=18,
            damage="2d6+7",
            creature_type="dragon",
            special_abilities=["Breath Weapon: 8d10 fire damage, Reflex DC 19 for half"],
            treasure=["500 gold pieces", "Magic sword +1", "Ruby worth 1000gp"],
            image_name="dragon.png",
            initiative_bonus=0,
            size="Large",
            challenge_rating="10",
        )
        self.fortitude_save = 11
        self.reflex_save = 8
        self.will_save = 8
        
    def breath_weapon(self, target):
        """Dragon's breath weapon attack"""
        damage = dice.d10(8)
        save_roll = target.saving_throw('reflex')
        
        if save_roll >= 19:
            damage = damage // 2
            result = f"{target.name} dodges! Takes {damage} fire damage (halved)."
        else:
            result = f"{target.name} is burned! Takes {damage} fire damage!"
            
        target.take_damage(damage)
        return f"{self.name} breathes fire! {result}"


class GiantSpider(Monster):
    """Venomous spider"""
    def __init__(self):
        super().__init__(
            name="Giant Spider",
            hit_dice="4d10+4",
            armor_class=14,
            attack_bonus=5,
            damage="1d8+3",
            creature_type="beast",
            special_abilities=["Poison: DC 14 Fort save or 1d4 STR damage"],
            treasure=[],
            image_name="giant_spider.png",
            initiative_bonus=3,
            size="Large",
            challenge_rating="1",
        )
        self.reflex_save = 4


class Zombie(Monster):
    """Slow undead creature"""
    def __init__(self):
        super().__init__(
            name="Zombie",
            hit_dice="2d12+3",
            armor_class=11,
            attack_bonus=2,
            damage="1d6+1",
            creature_type="undead",
            special_abilities=["Undead: immune to mind-affecting"],
            treasure=[],
            image_name="zombie.png",
            initiative_bonus=-2,
            size="Medium",
            challenge_rating="1/4",
        )
        self.fortitude_save = 3
        self.will_save = -2


class Troll(Monster):
    """Regenerating monster"""
    def __init__(self):
        super().__init__(
            name="Troll",
            hit_dice="6d8+36",
            armor_class=16,
            attack_bonus=9,
            damage="1d6+6",
            creature_type="giant",
            special_abilities=["Regeneration 5: heals 5 HP per round"],
            treasure=["30 gold pieces"],
            image_name="troll.png",
            initiative_bonus=1,
            size="Large",
            challenge_rating="5",
        )
        self.fortitude_save = 9


class GiantRat(Monster):
    """Small beast, pack tactics, from D&D 5e."""
    def __init__(self):
        super().__init__(
            name="Giant Rat",
            hit_dice="2d6",           # HP 7 (2d6)
            armor_class=13,
            attack_bonus=5,           # +2 proficiência + 3 Des (SRD diz +5)
            damage="1d4+3",           # Bite: 1d4 + 3
            creature_type="beast",
            special_abilities=[
                "Pack Tactics: Vantagem no ataque se aliado a 5 pés do alvo.",
                "Darkvision 60 ft.",
                "Perception +2",
                "Speed 30 ft., Climb 30 ft."
            ],
            treasure=[],
            image_name="giant_rat.png",
            initiative_bonus=3,
            size="Small",
            challenge_rating="1/8",
        )
        # Saving throws baseados nos modificadores da imagem
        self.reflex_save = 3          # Destreza +3
        self.fortitude_save = 0       # Constituição +0
        self.will_save = 0            # Sabedoria +0


# Monster factory
MONSTER_TYPES = {
    'goblin': Goblin,
    'orc': Orc,
    'skeleton': Skeleton,
    'ogre': Ogre,
    'dragon': Dragon,
    'giant_spider': GiantSpider,
    'zombie': Zombie,
    'troll': Troll,
    'giant_rat': GiantRat,
}


def create_monster(monster_type):
    """
    Create a monster by type name.
    
    Args:
        monster_type: String name of monster type
        
    Returns:
        Monster instance
    """
    monster_class = MONSTER_TYPES.get(monster_type.lower())
    if monster_class:
        return monster_class()
    else:
        # Default generic monster
        return Monster(name="Unknown Creature", hit_dice="1d4", armor_class=10, size="Medium", challenge_rating=0, experience_points=10)