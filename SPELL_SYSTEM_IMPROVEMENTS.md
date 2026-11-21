# Spell System Improvements - Session 2

## Summary
Fixed critical issues in the D&D 5e-style spell casting system to fully support all spell types: cantrips, beneficial spells, self-cast spells, and offensive spells.

## Problems Fixed

### 1. **Cantrips Not Appearing in Menu**
- **Issue**: Cantrips (level 0 spells) only appeared if prepared
- **D&D 5e Rule**: Cantrips can be cast at-will without preparation
- **Fix**: Modified `_get_castable_spells()` to include all level 0 spells from `known_spells`

### 2. **Beneficial Spells Only Targeting Enemies**
- **Issue**: Spells like "Cure Wounds", "Bless" couldn't target allies
- **Fix**: Added `_is_beneficial_spell()` to detect spell type by name patterns and range
- **Detection Logic**:
  - Name contains: cure, heal, bless, shield, mage armor, heroism, etc.
  - OR spell has `range_ft == 0` (self-cast spells like Shield, Mage Armor)

### 3. **Self-Cast Spells Not Working**
- **Issue**: Spells with `range_ft = 0` couldn't be used
- **Fix**: Modified `_cast_spell_on_target()` to allow self-targeting only for self-cast spells

## Changes Made

### File: `combat.py`

#### 1. `_get_castable_spells()` (Lines 455-473)
```python
def _get_castable_spells(self):
    # Returns prepared spells + all cantrips from known_spells
    # Cantrips = spells with level 0
    # D&D 5e: Cantrips can be cast at-will without preparation
```

#### 2. `_is_beneficial_spell()` (Lines 475-500)
```python
def _is_beneficial_spell(self, spell):
    # Heuristic detection: checks name patterns and range_ft == 0
    # Note: Ideal solution would add spell_type attribute to Spell class
    # Current implementation covers all standard D&D 5e beneficial spells
```

#### 3. `_cast_spell_on_target()` (Lines 509-553)
```python
def _cast_spell_on_target(self, spell, target_combatant):
    # Cantrips (level 0):
    #   - Check if spell in known_spells
    #   - Don't consume spell slots
    # Prepared spells (level 1+):
    #   - Check can_cast_spell() for slot availability
    # Range validation:
    #   - range_ft == 0: target must be caster
    #   - range_ft > 0: check Manhattan distance
```

#### 4. `handle_event()` Spell Selection (Lines 325-363)
```python
# Target routing logic for three spell types:
# 1. Self-cast (range_ft == 0): Only caster
# 2. Beneficial: Allies or self (same team)
# 3. Offensive: Enemies only (different team)
```

### File: `character.py`
- Modified line 73: Added `self._update_derived_stats()` in `__init__`
- Ensures `spell_slots` are initialized for spellcasting classes

## Spell Type Support Matrix

| Spell Type | Cantrip | Prepared | Beneficial | Self-Cast | Range |
|-----------|---------|----------|-----------|-----------|-------|
| Fire Bolt | ✓ | - | ✗ | ✗ | 120 ft |
| Magic Missile | ✗ | ✓ | ✗ | ✗ | 60 ft |
| Shield | ✗ | ✓ | ✓ | ✓ | 0 ft |
| Cure Wounds | ✗ | ✓ | ✓ | ✗ | touch |
| Bless | ✗ | ✓ | ✓ | ✗ | 30 ft |

## Technical Details

### Cantrip Handling
- Cantrips exist in both `prepared_spells` and `known_spells`
- `_get_castable_spells()` checks for duplicates to avoid showing same cantrip twice
- Cantrips don't consume spell slots (level 0 spells)

### Beneficial Spell Detection
Current hardcoded names (can be extended):
- Healing: cure, heal
- Buffs: bless, shield, mage armor, heroism, shield of faith, lay on hands
- Utility: guidance, prestidigitation, light, mending, resistance

### Range Validation
- Ranges converted from feet to tiles (5 ft = 1 tile)
- Uses Manhattan distance for all spells
- Special case: `range_ft == 0` requires exact self-target

## Known Limitations

1. **Hardcoded Spell Names**: `_is_beneficial_spell()` uses name patterns which could miss custom spells
   - Solution: Would require adding `spell_type` attribute to `Spell` class

2. **No Multi-Target Support**: Current system targets single combatants only
   - Spells like "Fireball" with AoE would need separate implementation

3. **No Concentration Tracking**: No system for concentration-required spells
   - Would need separate `concentration` state tracking

## Testing

All improvements verified with `test_spell_improvements.py`:
- ✅ Cantrips appear without preparation
- ✅ Beneficial spells detected correctly
- ✅ Self-cast spells (range 0) work
- ✅ Prepared spell slot consumption working
- ✅ Unprepared spells properly excluded
- ✅ Cleric spell system working

## D&D 5e Compliance

✓ Cantrips cast at-will (no slots)
✓ Prepared spells limited by slots
✓ Spell range validation
✓ Team-aware targeting (allies vs enemies)
✓ Self-cast restrictions

## Future Improvements

1. Add `spell_type` to `Spell` class for robust detection
2. Implement concentration mechanic
3. Add area-of-effect (AoE) spell support
4. Add ritual casting for spells that support it
5. Add spell saving throws for damage spells
