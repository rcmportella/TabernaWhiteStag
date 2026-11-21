"""
Spell system based on OGL D20 rules
"""
import dice


class Spell:
    """Base spell class"""
    
    def __init__(self, name, level, school, casting_time="1 action",
                 range_ft=30, duration="Instantaneous", description="", *,
                 ritual: bool = False, components: tuple[str, ...] = (),
                 material_component: str | None = None, concentration: bool = False):
        self.name = name
        self.level = level  # 0 for cantrips, 1-9 for spell levels
        self.school = school  # Evocation, Abjuration, etc.
        self.casting_time = casting_time
        self.range_ft = range_ft
        self.duration = duration
        self.description = description
        self.ritual = ritual
        self.components = tuple(components)
        self.material_component = material_component
        self.concentration = concentration
        
    def cast(self, caster, target=None):
        """
        Cast the spell. Override in subclasses.
        
        Args:
            caster: Character casting the spell
            target: Target of the spell (can be caster, enemy, or None)
            
        Returns:
            Result description
        """
        return f"{caster.name} casts {self.name}!"
        
    def __str__(self):
        level_str = "Cantrip" if self.level == 0 else f"Level {self.level}"
        return f"{self.name} ({level_str} {self.school}): {self.description}"


class MagicMissile(Spell):
    """Magic Missile spell - automatic hit"""
    
    def __init__(self):
        super().__init__(
            name="Magic Missile",
            level=1,
            school="Evocation",
            range_ft=120,
            components=("V", "S"),
            description="Three glowing darts strike unerringly. Each dart deals 1d4+1 force damage."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Magic Missile"
            
        missiles = 3
        total_damage = 0
        for _ in range(missiles):
            damage = dice.d4(1, 1)
            total_damage += damage
            
        target.take_damage(total_damage)
        return f"{self.name} hits {target.name} for {total_damage} force damage!"

class MageArmor(Spell):
    """Mage Armor spell - protective magical force"""
    
    def __init__(self):
        super().__init__(
            name="Mage Armor",
            level=1,
            school="Abjuration",
            range_ft=0,
            duration="8 hours",
            components=("V", "S", "M"),
            material_component="a piece of cured leather",
            description="A protective magical force surrounds the target, granting +4 armor bonus to AC. Ends if the target dons armor."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            target = caster
            
        # Apply +4 armor bonus to AC (following the same pattern as Shield)
        target.armor_class += 4
        return f"A shimmering magical force surrounds {target.name}! AC increased to {target.armor_class}."

class Sleep(Spell):
    """Sleep spell - puts creatures into magical slumber"""
    
    def __init__(self):
        super().__init__(
            name="Sleep",
            level=1,
            school="Enchantment",
            range_ft=90,
            duration="1 minute",
            components=("V", "S", "M"),
            material_component="a pinch of sand or rose petals",
            concentration=True,
            description="Creates a magical slumber. Rolls 2d4 hit points of creatures; those with lowest HP fall asleep first. Undead and creatures immune to sleep are unaffected."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Sleep"
            
        # Roll 2d4 to determine total HP affected
        hp_pool = dice.d4(2)
        
        # Check if target is immune (undead, etc.)
        if getattr(target, 'is_undead', False):
            return f"{target.name} is undead and immune to Sleep!"
            
        # Check if target's HP is within the pool
        if target.current_hp <= hp_pool:
            target.is_asleep = True
            return (f"{caster.name} casts Sleep! {target.name} falls into a magical slumber "
                    f"({target.current_hp} HP affected of {hp_pool} pool).")
        else:
            return (f"{caster.name} casts Sleep, but {target.name} has too many hit points "
                    f"({target.current_hp} HP > {hp_pool} pool). No effect.")

class Fireball(Spell):
    """Fireball spell - area effect damage"""
    
    def __init__(self):
        super().__init__(
            name="Fireball",
            level=3,
            school="Evocation",
            range_ft=150,
            components=("V", "S", "M"),
            material_component="a ball of bat guano and sulfur",
            description="A bright streak explodes with a roar dealing 8d6 fire damage. Reflex save DC 15 for half."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Fireball"
            
        damage = dice.d6(8)
        
        # Target makes Reflex save
        save_dc = 15
        save_roll = target.saving_throw('reflex')
        
        if save_roll >= save_dc:
            damage = damage // 2
            result = f"{target.name} saves! Takes {damage} fire damage (halved)."
        else:
            result = f"{target.name} fails save! Takes {damage} fire damage!"
            
        target.take_damage(damage)
        return f"{self.name} engulfs the area! {result}"


class CureWounds(Spell):
    """Cure Light Wounds - healing spell"""
    
    def __init__(self):
        super().__init__(
            name="Cure Light Wounds",
            level=1,
            school="Conjuration",
            range_ft=5,
            casting_time="1 action",
            components=("V", "S"),
            description="Heals 1d8 + caster's Wisdom modifier hit points."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            target = caster
            
        wis_mod = caster.get_ability_modifier('wisdom')
        healing = dice.d8(1, wis_mod)
        target.heal(healing)
        
        return f"{self.name} heals {target.name} for {healing} HP! ({target.current_hp}/{target.max_hp})"
    
class Guidance(Spell):
    """Guidance cantrip - grants a bonus to ability checks"""

    def __init__(self):
        super().__init__(
            name="Guidance",
            level=0,
            school="Divination",
            range_ft=30,
            duration="1 minute",
            components=("V", "S"),
            description="Target can add a d4 to one ability check of its choice within 1 minute."
        )

class Sacred_Flame(Spell):
    """Sacred Flame cantrip - radiant damage"""

    def __init__(self):
        super().__init__(
            name="Sacred Flame",
            level=0,
            school="Evocation",
            range_ft=60,
            components=("V", "S"),
            description="Flame-like radiance descends on a target, dealing 1d8 radiant damage. Target can make a Dexterity save for half."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Sacred Flame"

        damage = dice.d8()

        save_dc = 13
        save_roll = target.saving_throw('dexterity')

        if save_roll >= save_dc:
            damage = damage // 2
            result = f"{target.name} partially avoids the flame! Takes {damage} radiant damage (halved)."
        else:
            result = f"{target.name} is engulfed! Takes {damage} radiant damage!"

        target.take_damage(damage)
        return f"{self.name} strikes {target.name}! {result}"

class Thaumaturgy(Spell):
    """Thaumaturgy cantrip - minor magical effects"""

    def __init__(self):
        super().__init__(
            name="Thaumaturgy",
            level=0,
            school="Transmutation",
            range_ft=30,
            components=("V",),
            description="You create minor magical effects within range."
        )

    def cast(self, caster, target=None):
        if target is None:
            target = caster

        bonus = dice.d4()
        target.add_temporary_bonus('ability_check', bonus)
        return f"{self.name} grants {target.name} a +{bonus} bonus to their next ability check."

class Shield(Spell):
    """Shield spell - protective magic"""
    
    def __init__(self):
        super().__init__(
            name="Shield",
            level=1,
            school="Abjuration",
            range_ft=0,
            duration="1 round",
            components=("V", "S"),
            description="An invisible barrier grants +4 to AC until your next turn."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            target = caster
            
        # Temporarily increase AC
        target.armor_class += 4
        return f"A shimmering shield surrounds {target.name}! AC increased to {target.armor_class}."


class BurningHands(Spell):
    """Burning Hands - cone of fire"""
    
    def __init__(self):
        super().__init__(
            name="Burning Hands",
            level=1,
            school="Evocation",
            range_ft=15,
            components=("V", "S"),
            description="A cone of fire deals 3d4 fire damage. Reflex save DC 13 for half."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Burning Hands"
            
        damage = dice.d4(3)
        
        save_dc = 13
        save_roll = target.saving_throw('reflex')
        
        if save_roll >= save_dc:
            damage = damage // 2
            result = f"{target.name} partially dodges! Takes {damage} fire damage (halved)."
        else:
            result = f"{target.name} is engulfed! Takes {damage} fire damage!"
            
        target.take_damage(damage)
        return f"Flames shoot from {caster.name}'s hands! {result}"


class LightningBolt(Spell):
    """Lightning Bolt - line of electricity"""
    
    def __init__(self):
        super().__init__(
            name="Lightning Bolt",
            level=3,
            school="Evocation",
            range_ft=120,
            components=("V", "S", "M"),
            material_component="a bit of fur and a crystal rod",
            description="A stroke of lightning deals 8d6 electricity damage. Reflex save DC 15 for half."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Lightning Bolt"
            
        damage = dice.d6(8)
        
        save_dc = 15
        save_roll = target.saving_throw('reflex')
        
        if save_roll >= save_dc:
            damage = damage // 2
            result = f"{target.name} partially evades! Takes {damage} electricity damage (halved)."
        else:
            result = f"{target.name} is struck! Takes {damage} electricity damage!"
            
        target.take_damage(damage)
        return f"A bolt of lightning streaks forth! {result}"


class Bless(Spell):
    """Bless - buff spell"""
    
    def __init__(self):
        super().__init__(
            name="Bless",
            level=1,
            school="Enchantment",
            duration="1 minute",
            components=("V", "S", "M"),
            material_component="a holy symbol worth at least 5 gp",
            description="Allies gain +1 to attack rolls and saving throws."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            target = caster
            
        # Simple implementation: temporary BAB boost
        target.base_attack_bonus += 1
        return f"{target.name} is blessed! Attack bonus increased."


class DetectMagic(Spell):
    """Detect Magic - senses magical auras"""
    
    def __init__(self):
        super().__init__(
            name="Detect Magic",
            level=1,
            school="Divination",
            range_ft=60,
            duration="Concentration, up to 1 minute",
            ritual=True,
            components=("V", "S"),
            description="Sense the presence of magic within 60 feet."
        )
        
    def cast(self, caster, target=None):
        return f"{caster.name} senses magical auras in the area..."

class Prestidigitation(Spell):
    """Prestidigitation cantrip - minor magical effects"""

    def __init__(self):
        super().__init__(
            name="Prestidigitation",
            level=0,
            school="Transmutation",
            range_ft=10,
            duration="1 hour",
            components=("V", "S"),
            description="Create minor magical effects within range."
        )

    def cast(self, caster, target=None):
        return f"{caster.name} performs a minor magical effect."


class RayOfFrost(Spell):
    """Ray of Frost cantrip"""
    
    def __init__(self):
        super().__init__(
            name="Ray of Frost",
            level=0,
            school="Evocation",
            range_ft=60,
            components=("V", "S"),
            description="A frigid beam deals 1d8 cold damage."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Ray of Frost"
            
        # Make a ranged touch attack
        int_mod = caster.get_ability_modifier('intelligence')
        attack_roll = dice.d20(1, caster.base_attack_bonus + int_mod)
        
        if attack_roll >= target.armor_class:
            damage = dice.d8()
            target.take_damage(damage)
            return f"A ray of frost strikes {target.name} for {damage} cold damage!"
        else:
            return f"The ray of frost misses {target.name}!"

class AcidSplash(Spell):
    """Acid Splash cantrip - hurls a bubble of acid"""
    
    def __init__(self):
        super().__init__(
            name="Acid Splash",
            level=0,
            school="Conjuration",
            range_ft=60,
            components=("V", "S"),
            description="You hurl a bubble of acid. One creature takes 1d6 acid damage. Reflex save DC 13 negates."
        )
        
    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Acid Splash"
            
        damage = dice.d6()
        
        save_dc = 13
        save_roll = target.saving_throw('reflex')
        
        if save_roll >= save_dc:
            return f"{target.name} dodges the acid splash! No damage."
        else:
            target.take_damage(damage)
            return f"{self.name} hits {target.name} for {damage} acid damage!"

class ChillTouch(Spell):
    """Chill Touch cantrip - creates a ghostly skeletal hand that delivers a chilling touch"""

    def __init__(self):
        super().__init__(
            name="Chill Touch",
            level=0,
            school="Necromancy",
            range_ft=60,
            components=("V", "S"),
            description="A ghostly skeletal hand delivers a chilling touch. Deals 1d8 cold damage."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Chill Touch"

        damage = dice.d8()
        target.take_damage(damage)
        return f"{self.name} hits {target.name} for {damage} cold damage!"

class FireBolt(Spell):
    """Fire Bolt cantrip - hurls a mote of fire"""

    def __init__(self):
        super().__init__(
            name="Fire Bolt",
            level=0,
            school="Evocation",
            range_ft=120,
            components=("V", "S"),
            description="You hurl a mote of fire. One creature takes 1d10 fire damage. Reflex save DC 13 negates."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Fire Bolt"

        damage = dice.d10()

        save_dc = 13
        save_roll = target.saving_throw('reflex')

        if save_roll >= save_dc:
            return f"{target.name} dodges the fire bolt! No damage."
        else:
            target.take_damage(damage)
            return f"{self.name} hits {target.name} for {damage} fire damage!"

class SorcerousBurst(Spell):
    """Sorcerous Burst cantrip - releases a burst of magical energy"""

    def __init__(self):
        super().__init__(
            name="Sorcerous Burst",
            level=0,
            school="Evocation",
            range_ft=120,
            components=("V", "S"),
            description="You release a burst of magical energy. One creature takes 1d8 force damage. Reflex save DC 13 negates."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Sorcerous Burst"

        damage = dice.d8()

        save_dc = 13
        save_roll = target.saving_throw('reflex')

        if save_roll >= save_dc:
            return f"{target.name} dodges the sorcerous burst! No damage."
        else:
            target.take_damage(damage)
            return f"{self.name} hits {target.name} for {damage} force damage!"

class Light(Spell):
    """Light cantrip - creates a magical light source"""

    def __init__(self):
        super().__init__(
            name="Light",
            level=0,
            school="Evocation",
            range_ft=60,
            components=("V", "M"),
            material_component="a firefly or phosphorescent moss",
            description="You create a magical light source. The light lasts for 1 hour."
        )

    def cast(self, caster, target=None):
        return f"{self.name} creates a magical light source."

class MageHand(Spell):
    """Mage Hand cantrip - creates a spectral hand"""

    def __init__(self):
        super().__init__(
            name="Mage Hand",
            level=0,
            school="Conjuration",
            range_ft=30,
            components=("V", "S"),
            description="You create a spectral hand that can manipulate objects at a distance."
        )

    def cast(self, caster, target=None):
        return f"{self.name} creates a spectral hand."

class ShockingGrasp(Spell):
    """Shocking Grasp cantrip - delivers a jolt of electricity"""

    def __init__(self):
        super().__init__(
            name="Shocking Grasp",
            level=0,
            school="Evocation",
            range_ft=5,
            components=("V", "S"),
            description="You deliver a jolt of electricity to a creature within range."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Shocking Grasp"

        damage = dice.d8()
        target.take_damage(damage)
        return f"{self.name} hits {target.name} for {damage} lightning damage!"

class FeatherFall(Spell):
    """Feather Fall - slows the descent of falling creatures"""

    def __init__(self):
        super().__init__(
            name="Feather Fall",
            level=1,
            school="Transmutation",
            range_ft=60,
            duration="1 minute/level",
            components=("V", "M"),
            material_component="a small feather or a piece of down",
            description="You slow the descent of up to five falling creatures within range."
        )

    def cast(self, caster, target=None):
        return f"{self.name} slows the descent of falling creatures."

class Thunderwave(Spell):
    """Thunderwave - creates a wave of thunderous force"""

    def __init__(self):
        super().__init__(
            name="Thunderwave",
            level=1,
            school="Evocation",
            range_ft=15,
            components=("V", "S"),
            description="You create a wave of thunderous force that damages and pushes creatures away."
        )

    def cast(self, caster, target=None):
        return f"{self.name} creates a wave of thunderous force."

class Guiding_Bolt(Spell):
    """Guiding Bolt - a radiant attack that grants advantage on the next attack"""

    def __init__(self):
        super().__init__(
            name="Guiding Bolt",
            level=1,
            school="Evocation",
            range_ft=120,
            components=("V", "S"),
            description="A flash of light streaks toward a creature, dealing radiant damage and granting advantage on the next attack against it."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Guiding Bolt"

        damage = dice.d6() + dice.d6()  # 2d6 radiant damage
        target.take_damage(damage)
        target.add_condition("vulnerable_to_next_attack")
        return f"{self.name} hits {target.name} for {damage} radiant damage and grants advantage on the next attack against it!"

class Shield_of_Faith(Spell):

    """Shield of Faith - grants a target a bonus to AC"""

    def __init__(self):
        super().__init__(
            name="Shield of Faith",
            level=1,
            school="Abjuration",
            range_ft=60,
            components=("V", "S"),
            description="A shimmering field appears and surrounds a creature of your choice, granting it a bonus to AC."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Shield of Faith"

        target.add_condition("shield_of_faith")
        return f"{self.name} grants {target.name} a bonus to AC!"

class Lay_on_Hands(Spell):

    """Lay on Hands - heals a target for a pool of hit points"""

    def __init__(self):
        super().__init__(
            name="Lay on Hands",
            level=0,
            school="Evocation",
            range_ft=5,
            components=("V", "S"),
            description="You touch a creature and restore a number of hit points from your pool."
        )

    def cast(self, caster, target=None, points_to_spend=5):
        if target is None:
            return "No target selected for Lay on Hands"
        # Verifica se há pontos de Lay on Hands disponíveis
        if caster.layonhands_pool <= 0:
            return f"{caster.name} has no Lay on Hands points available"
        # Limita o gasto ao que está disponível e ao que foi pedido
        actual_heal = min(points_to_spend, caster.layonhands_pool)

        # Gasta o pool e cura o alvo
        caster.layonhands_pool -= actual_heal
        target.heal(actual_heal)

        return (f"{self.name} heals {target.name} for {actual_heal} hit points! "
                f"({caster.name}'s pool remaining: {caster.layonhands_pool})")

class Heroism(Spell):

    """Heroism - grants a target temporary hit points and immunity to fear"""

    def __init__(self):
        super().__init__(
            name="Heroism",
            level=1,
            school="Enchantment",
            range_ft=5,
            duration="1 minute/level",
            components=("V", "S"),
            concentration=True,
            description="A willing creature you touch is imbued with bravery, gaining temporary hit points and immunity to fear."
        )

    def cast(self, caster, target=None):
        if target is None:
            return "No target selected for Heroism"

        target.add_condition("heroism")
        temp_hp = caster.get_ability_modifier('charisma')  # Example: use Charisma modifier for temp HP
        target.add_temporary_hp(temp_hp)  # Example: grants temporary hit points based on Charisma modifier
        return f"{self.name} grants {target.name} {temp_hp} hit points and immunity to fear!"
    
# Spell library - available spells
SPELL_LIBRARY = {
    # Cantrips (Level 0)
    'ray_of_frost': RayOfFrost(),
    'acid_splash': AcidSplash(),
    'chill_touch': ChillTouch(),
    'fire_bolt': FireBolt(),
    'light': Light(),
    'mage_hand': MageHand(),
    'sorcerous_burst': SorcerousBurst(),
    'prestidigitation': Prestidigitation(),
    'shocking_grasp': ShockingGrasp(),
    'guidance': Guidance(),
    'sacred_flame': Sacred_Flame(),
    'thaumaturgy': Thaumaturgy(),
    'lay_on_hands': Lay_on_Hands(),
    
    # Level 1
    'detect_magic': DetectMagic(),
    'magic_missile': MagicMissile(),
    'cure_light_wounds': CureWounds(),
    'shield': Shield(),
    'burning_hands': BurningHands(),
    'bless': Bless(),
    'mage_armor': MageArmor(),
    'sleep': Sleep(),
    'feather_fall': FeatherFall(),
    'thunderwave': Thunderwave(),
    'guiding_bolt': Guiding_Bolt(),
    'shield_of_faith': Shield_of_Faith(),
    'heroism': Heroism(),
    
    # Level 3
    'fireball': Fireball(),
    'lightning_bolt': LightningBolt(),
}

SPELL_LISTS = {
    "Wizard": {
        # Cantrips (Nível 0)
        "ray_of_frost", 
        "acid_splash", 
        "chill_touch", 
        "fire_bolt", 
        "light", 
        "mage_hand",
        
        # Nível 1
        "detect_magic", 
        "magic_missile", 
        "shield", 
        "burning_hands", 
        "mage_armor", 
        "sleep", 
        "feather_fall", 
        "thunderwave",
        
        # Nível 3
        "fireball", 
        "lightning_bolt"
    },
    
    "Sorcerer": {
        # Cantrips (Nível 0)
        "ray_of_frost", 
        "acid_splash", 
        "chill_touch", 
        "fire_bolt", 
        "light", 
        "sorcerous_burst",
        
        # Nível 1
        "detect_magic", 
        "magic_missile", 
        "shield", 
        "burning_hands", 
        "mage_armor", 
        "sleep", 
        "feather_fall", 
        "thunderwave",
        
        # Nível 3
        "fireball", 
        "lightning_bolt"
    },
    "Cleric": {
        # Cantrips (Nível 0)
        "guidance",
        "sacred_flame",
        "thaumaturgy",

        # Nível 1
        "cure_light_wounds",
        "bless",
        "shield_of_faith",
        "guiding_bolt"
    },
    "Paladin": {
        # Cantrips (Nível 0)
        "lay_on_hands",

        # Nível 1
        "cure_light_wounds",
        "bless",
        "shield_of_faith",
        "heroism"
    }
}

def get_spell(spell_name):
    """Get a spell from the library by name"""
    return SPELL_LIBRARY.get(spell_name.lower().replace(' ', '_'))


def list_spells_by_level(level):
    """List all spells of a given level"""
    return [spell for spell in SPELL_LIBRARY.values() if spell.level == level]
