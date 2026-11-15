"""
Character system following OGL D20 rules
"""
import dice
from equipment import Armor, Equipment, Potion, Shield, Weapon


# Classes that can only have a specific alignment
CLASS_ALIGNMENT_RESTRICTIONS = {"Paladin": "Lawful Good"}


class Character:
    """
    Player character with D20 attributes and stats
    """
    
    def __init__(self, name, char_class="Fighter", level=1):
        self.name = name
        self.char_class = char_class
        self.level = level

        # Identity
        self.gender = None
        self.alignment = None
        self.portrait = None
        self.portrait_id = None
        
        # Core ability scores (3-18 range typically)
        self.strength = 10
        self.dexterity = 10
        self.constitution = 10
        self.intelligence = 10
        self.wisdom = 10
        self.charisma = 10
        
        # Combat stats
        self.max_hp = 10
        self.current_hp = 10
        self.base_attack_bonus = 0
        self._armor_class_bonus = 0
        
        # Saving throws (Fortitude, Reflex, Will)
        self.fortitude_save = 0
        self.reflex_save = 0
        self.will_save = 0
        
        # Inventory and equipment
        self.inventory = []
        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_shield = None
        
        # Spells (for spellcasting classes)
        self.known_spells = []
        self.spell_slots = {}  # {level: available_slots}
        
        # Experience and wealth
        self.experience = 0
        self.gold = 0
        
    @staticmethod
    def required_alignment(char_class):
        """Alignment imposed by the class, or None if unrestricted"""
        return CLASS_ALIGNMENT_RESTRICTIONS.get(char_class)

    def set_alignment(self, alignment):
        required = self.required_alignment(self.char_class)
        if required and alignment != required:
            raise ValueError(f"{self.char_class} must be {required}")
        self.alignment = alignment

    def roll_abilities(self):
        """Roll ability scores using 4d6 drop lowest method"""
        self.strength = dice.ability_score()
        self.dexterity = dice.ability_score()
        self.constitution = dice.ability_score()
        self.intelligence = dice.ability_score()
        self.wisdom = dice.ability_score()
        self.charisma = dice.ability_score()
        self._update_derived_stats()
        
    def set_abilities(self, str_score, dex, con, int_score, wis, cha):
        """Set ability scores manually"""
        self.strength = str_score
        self.dexterity = dex
        self.constitution = con
        self.intelligence = int_score
        self.wisdom = wis
        self.charisma = cha
        self._update_derived_stats()
        
    def _update_derived_stats(self):
        """Update HP, AC, and other derived stats based on abilities"""
        con_mod = self.get_ability_modifier('constitution')
        
        # Update HP based on class and constitution
        if self.char_class == "Fighter":
            self.max_hp = 10 + con_mod + (self.level - 1) * (6 + con_mod)
            self.base_attack_bonus = self.level
            self.fortitude_save = 2 + (self.level // 2)
            self.reflex_save = 0 + (self.level // 3)
            self.will_save = 0 + (self.level // 3)
        elif self.char_class == "Paladin":
            self.max_hp = 10 + con_mod + (self.level - 1) * (6 + con_mod)
            self.base_attack_bonus = self.level
            self.fortitude_save = 2 + (self.level // 2)
            self.reflex_save = 0 + (self.level // 3)
            self.will_save = 0 + (self.level // 3)
        elif self.char_class == "Wizard":
            self.max_hp = 4 + con_mod + (self.level - 1) * (3 + con_mod)
            self.base_attack_bonus = self.level // 2
            self.fortitude_save = 0 + (self.level // 3)
            self.reflex_save = 0 + (self.level // 3)
            self.will_save = 2 + (self.level // 2)
            self._setup_wizard_spells()
        elif self.char_class == "Rogue":
            self.max_hp = 6 + con_mod + (self.level - 1) * (4 + con_mod)
            self.base_attack_bonus = (self.level * 3) // 4
            self.fortitude_save = 0 + (self.level // 3)
            self.reflex_save = 2 + (self.level // 2)
            self.will_save = 0 + (self.level // 3)
        elif self.char_class == "Cleric":
            self.max_hp = 8 + con_mod + (self.level - 1) * (5 + con_mod)
            self.base_attack_bonus = (self.level * 3) // 4
            self.fortitude_save = 2 + (self.level // 2)
            self.reflex_save = 0 + (self.level // 3)
            self.will_save = 2 + (self.level // 2)
            self._setup_cleric_spells()
        
        # Ensure HP is at least 1 per level
        self.max_hp = max(self.max_hp, self.level)
        self.current_hp = self.max_hp
        
        self._armor_class_bonus = 0
        
    def _setup_wizard_spells(self):
        """Setup spell slots for wizard"""
        # Simplified spell slots per level
        slots_per_level = {
            1: {0: 3, 1: 1},
            2: {0: 3, 1: 2},
            3: {0: 3, 1: 2, 2: 1},
            4: {0: 4, 1: 3, 2: 2},
            5: {0: 4, 1: 3, 2: 2, 3: 1}
        }
        self.spell_slots = slots_per_level.get(self.level, {0: 3, 1: 1})
        
    def _setup_cleric_spells(self):
        """Setup spell slots for cleric"""
        # Simplified spell slots per level
        slots_per_level = {
            1: {0: 3, 1: 1},
            2: {0: 4, 1: 2},
            3: {0: 4, 1: 2, 2: 1},
            4: {0: 5, 1: 3, 2: 2},
            5: {0: 5, 1: 3, 2: 2, 3: 1}
        }
        self.spell_slots = slots_per_level.get(self.level, {0: 3, 1: 1})
        
    def get_ability_modifier(self, ability):
        """Get the modifier for an ability score"""
        score = getattr(self, ability.lower())
        return dice.modifier(score)
    
    def _base_armor_class(self):
        dex_mod = self.get_ability_modifier('dexterity')
        if isinstance(self.equipped_armor, Armor):
            return self.equipped_armor.armor_class(dex_mod)
        # Preserve compatibility with older equipment objects.
        return 10 + dex_mod + getattr(self.equipped_armor, 'ac_bonus', 0)

    @property
    def armor_class(self):
        return self.get_armor_class()

    @armor_class.setter
    def armor_class(self, value):
        shield_bonus = self.equipped_shield.ac_bonus if self.equipped_shield else 0
        self._armor_class_bonus = value - self._base_armor_class() - shield_bonus

    def get_armor_class(self):
        """Calculate AC from the equipped armor and other modifiers."""
        shield_bonus = self.equipped_shield.ac_bonus if self.equipped_shield else 0
        return self._base_armor_class() + shield_bonus + self._armor_class_bonus
    
    def get_weapon_damage(self):
        """
        Get damage dice from equipped weapon
        
        Returns:
            Damage dice string (e.g., "1d8") or "1d3" for unarmed
        """
        if self.equipped_weapon and hasattr(self.equipped_weapon, 'damage'):
            return self.equipped_weapon.damage
        
        # Unarmed damage
        return "1d3"
        
    def attack_roll(self, target_ac, weapon_damage=None):
        """
        Make an attack roll against a target.
        
        Args:
            target_ac: Target's Armor Class
            weapon_damage: Damage dice (e.g., "1d8", "2d6"), or None to use equipped weapon
            
        Returns:
            Tuple of (hit: bool, damage: int, attack_roll: int)
        """
        # Use equipped weapon damage if no weapon specified
        using_equipped_weapon = weapon_damage is None
        if using_equipped_weapon:
            weapon_damage = self.get_weapon_damage()
        
        ability_mod = self.get_ability_modifier('strength')
        weapon_bonus = 0
        if using_equipped_weapon and isinstance(self.equipped_weapon, Weapon):
            weapon = self.equipped_weapon
            dex_mod = self.get_ability_modifier('dexterity')
            if weapon.finesse:
                ability_mod = max(ability_mod, dex_mod)
            elif weapon.ranged:
                ability_mod = dex_mod
            weapon_bonus = weapon.magic_bonus
        attack_roll = dice.d20(1, self.base_attack_bonus + ability_mod + weapon_bonus)
        
        if attack_roll >= target_ac:
            # Hit! Roll damage
            damage = self._roll_damage(weapon_damage) + ability_mod + weapon_bonus
            return True, max(1, damage), attack_roll
        else:
            return False, 0, attack_roll
            
    def _roll_damage(self, damage_dice):
        """Parse and roll damage dice string (e.g., '2d6', '1d8+2')"""
        if '+' in damage_dice:
            dice_part, mod = damage_dice.split('+')
            mod = int(mod)
        elif '-' in damage_dice:
            dice_part, mod = damage_dice.split('-')
            mod = -int(mod)
        else:
            dice_part = damage_dice
            mod = 0
            
        # Parse dice notation
        count, sides = dice_part.split('d')
        count = int(count)
        sides = int(sides)
        
        return dice.roll(sides, count, mod)
        
    def take_damage(self, damage):
        """Take damage and return True if still alive"""
        self.current_hp -= damage
        return self.current_hp > 0
        
    def heal(self, amount):
        """Heal damage, capped at max HP"""
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        
    def is_alive(self):
        """Check if character is still alive"""
        return self.current_hp > 0
        
    def saving_throw(self, save_type):
        """
        Make a saving throw.
        
        Args:
            save_type: 'fortitude', 'reflex', or 'will'
            
        Returns:
            Roll result
        """
        if save_type == 'fortitude':
            return dice.d20(1, self.fortitude_save)
        elif save_type == 'reflex':
            return dice.d20(1, self.reflex_save)
        elif save_type == 'will':
            return dice.d20(1, self.will_save)
        else:
            return dice.d20()
            
    def add_item(self, item):
        """Add item to inventory"""
        if isinstance(item, Equipment) and any(existing is item for existing in self.inventory):
            raise ValueError("This equipment is already in the inventory")
        if isinstance(item, Potion) and item.used:
            raise ValueError("A used potion cannot be added to inventory")
        self.inventory.append(item)

    def equip(self, item):
        """Equip a weapon, armor or shield already in the inventory."""
        if not isinstance(item, (Weapon, Armor, Shield)):
            raise TypeError("Only weapons, armor and shields can be equipped")
        if not any(existing is item for existing in self.inventory):
            raise ValueError("Equipment must be in the inventory")
        if isinstance(item, Weapon):
            self.equipped_weapon = item
        elif isinstance(item, Armor):
            self.equipped_armor = item
        else:
            self.equipped_shield = item

    def unequip_weapon(self):
        self.equipped_weapon = None

    def unequip_armor(self):
        self.equipped_armor = None

    def unequip_shield(self):
        self.equipped_shield = None
    
    def add_gold(self, amount):
        """Add gold to character's wealth"""
        self.gold += amount
        return self.gold
    
    def remove_gold(self, amount):
        """Remove gold from character. Returns True if successful, False if not enough gold."""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False
    
    def count_item(self, item_name):
        """Count how many items with the given name are in inventory."""
        count = 0
        for item in self.inventory:
            # Handle both string items and item objects
            if hasattr(item, 'name'):
                if item.name.lower() == item_name.lower():
                    count += 1
            elif isinstance(item, str):
                if item.lower() == item_name.lower():
                    count += 1
        return count
    
    def remove_items(self, item_name, quantity):
        """Remove a specific quantity of items. Returns True if successful, False if not enough."""
        if self.count_item(item_name) >= quantity:
            removed = 0
            # Create a new list without the removed items
            new_inventory = []
            for item in self.inventory:
                # Check if this is the item to remove
                is_target = False
                if hasattr(item, 'name'):
                    is_target = item.name.lower() == item_name.lower()
                elif isinstance(item, str):
                    is_target = item.lower() == item_name.lower()
                
                # Remove if we haven't removed enough yet
                if is_target and removed < quantity:
                    removed += 1
                else:
                    new_inventory.append(item)
            
            self.inventory = new_inventory
            if not any(item is self.equipped_weapon for item in self.inventory):
                self.unequip_weapon()
            if not any(item is self.equipped_armor for item in self.inventory):
                self.unequip_armor()
            if not any(item is self.equipped_shield for item in self.inventory):
                self.unequip_shield()
            return True
        return False
        
    def use_item(self, item_name, target=None):
        """Use an inventory item on the character or on the specified target."""
        if target is None:
            target = self
        for item in self.inventory:
            if getattr(item, 'name', '').lower() == item_name.lower():
                if not callable(getattr(item, 'use', None)):
                    raise TypeError(f"{item.name} cannot be used as a consumable")
                effect = item.use(target)
                if item.consumable:
                    self.inventory.remove(item)
                return effect
        return None
        
    def learn_spell(self, spell):
        """Learn a new spell"""
        if spell not in self.known_spells:
            self.known_spells.append(spell)
            
    def can_cast_spell(self, spell):
        """Check if character can cast a spell"""
        if spell not in self.known_spells:
            return False
        spell_level = spell.level
        return self.spell_slots.get(spell_level, 0) > 0
        
    def cast_spell(self, spell, target=None):
        """Cast a spell"""
        if not self.can_cast_spell(spell):
            return False, "Cannot cast spell"
            
        # Use spell slot
        self.spell_slots[spell.level] -= 1
        
        # Execute spell effect
        result = spell.cast(self, target)
        return True, result
        
    def short_rest(self):
        """Short rest to restore some HP"""
        heal_amount = max(1, self.level)
        self.heal(heal_amount)
        
    def long_rest(self):
        """Long rest to restore all HP and spell slots"""
        self.current_hp = self.max_hp
        self._update_derived_stats()  # Restore spell slots
        
    def rest(self):
        """Alias for long_rest for backward compatibility"""
        self.long_rest()
        
    def gain_experience(self, xp):
        """Gain experience points"""
        self.experience += xp
        # Simple level up at 1000 XP per level
        while self.experience >= self.level * 1000:
            self.level_up()
            
    def level_up(self):
        """Level up the character"""
        self.level += 1
        self._update_derived_stats()
    
    def get_character_sheet(self, detailed=True):
        """
        Get a formatted character sheet.
        
        Args:
            detailed: If True, shows full character sheet. If False, shows compact version.
        
        Returns:
            Formatted character sheet string
        """
        if detailed:
            # Detailed character sheet
            sheet = "=" * 60 + "\n"
            sheet += f"  {self.name.upper()}\n"
            sheet += f"  Level {self.level} {self.char_class}\n"
            sheet += "=" * 60 + "\n\n"
            
            # Combat Stats
            sheet += "COMBAT STATS:\n"
            sheet += f"  Hit Points:        {self.current_hp}/{self.max_hp}\n"
            sheet += f"  Armor Class:       {self.get_armor_class()}"
            sheet += f"  Base Attack Bonus: +{self.base_attack_bonus}\n"
            sheet += f"  Experience:        {self.experience} XP\n"
            sheet += f"  Gold:              {self.gold} gp\n\n"
            
            # Ability Scores with Modifiers
            sheet += "ABILITY SCORES:\n"
            sheet += f"  Strength:      {self.strength:2d} ({self.get_ability_modifier('strength'):+d})\n"
            sheet += f"  Dexterity:     {self.dexterity:2d} ({self.get_ability_modifier('dexterity'):+d})\n"
            sheet += f"  Constitution:  {self.constitution:2d} ({self.get_ability_modifier('constitution'):+d})\n"
            sheet += f"  Intelligence:  {self.intelligence:2d} ({self.get_ability_modifier('intelligence'):+d})\n"
            sheet += f"  Wisdom:        {self.wisdom:2d} ({self.get_ability_modifier('wisdom'):+d})\n"
            sheet += f"  Charisma:      {self.charisma:2d} ({self.get_ability_modifier('charisma'):+d})\n\n"
            
            # Saving Throws
            sheet += "SAVING THROWS:\n"
            sheet += f"  Fortitude: +{self.fortitude_save}\n"
            sheet += f"  Reflex:    +{self.reflex_save}\n"
            sheet += f"  Will:      +{self.will_save}\n\n"
            
            # Equipment
            sheet += "EQUIPMENT:\n"
            if self.equipped_weapon:
                sheet += f"  Weapon: {self.equipped_weapon}\n"
            if self.equipped_armor:
                sheet += f"  Armor:  {self.equipped_armor}\n"
            if self.equipped_shield:
                sheet += f"  Shield: {self.equipped_shield}\n"
            if not self.equipped_weapon and not self.equipped_armor and not self.equipped_shield:
                sheet += "  None equipped\n"
            
            # Inventory
            if self.inventory:
                sheet += f"\nINVENTORY ({len(self.inventory)} items):\n"
                for item in self.inventory:
                    sheet += f"  - {item}\n"
            
            # Spells
            if self.known_spells:
                sheet += f"\nKNOWN SPELLS ({len(self.known_spells)}):\n"
                for spell in self.known_spells:
                    sheet += f"  - {spell.name}\n"
            
            sheet += "=" * 60
            return sheet
        else:
            # Compact version (original format)
            return (f"{self.name} - Level {self.level} {self.char_class}\n"
                    f"HP: {self.current_hp}/{self.max_hp} | AC: {self.get_armor_class()} | Gold: {self.gold}\n"
                    f"STR: {self.strength} DEX: {self.dexterity} CON: {self.constitution}\n"
                    f"INT: {self.intelligence} WIS: {self.wisdom} CHA: {self.charisma}")
        
    def __str__(self):
        """Default string representation - returns compact version"""
        return self.get_character_sheet(detailed=False)
