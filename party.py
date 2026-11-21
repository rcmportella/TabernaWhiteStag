"""
Party management system for the player's group of characters
"""
from character import Character
from equipment import Equipment


class Party:
    """
    Manages a group of player characters
    """
    
    def __init__(self, leader: Character | None = None):
        self.members = []
        self.leader = leader
        self.position = [1, 1]  # Starting position on map (row, col)
        if leader is not None:
            self.members.append(leader)

    @property
    def recruitment_limit(self):
        if self.leader is None:
            return 5
        return min(5, max(0, self.leader.charisma - 10))

    def recruitment_error(self, character):
        """Return the reason a character cannot join, or None."""
        if character in self.members:
            return "already_joined"
        if self.leader is not None and character.charisma > self.leader.charisma:
            return "charisma"
        if self.leader is not None and character.level > self.leader.level:
            return "level"
        if len(self.members) >= 6 or (
            self.leader is not None and len(self.members) - 1 >= self.recruitment_limit
        ):
            return "full"
        return None
        
    def add_member(self, character):
        """Add a character to the party"""
        if self.recruitment_error(character) is None:
            self.members.append(character)
            return True
        return False
        
    def remove_member(self, character):
        """Remove a character from the party"""
        if character is not self.leader and character in self.members:
            self.members.remove(character)
            return True
        return False
        
    def get_member(self, index):
        """Get a party member by index"""
        if 0 <= index < len(self.members):
            return self.members[index]
        return None
        
    def is_alive(self):
        """Check if at least one party member is alive"""
        return any(member.is_alive() for member in self.members)
        
    def get_alive_members(self):
        """Get list of living party members"""
        return [m for m in self.members if m.is_alive()]
        
    def total_gold(self):
        """Get total gold from all party members"""
        return sum(m.gold for m in self.members)

    def purchase_item(self, item: Equipment, recipient: Character) -> bool:
        """Buy an item with shared gold, giving it to a party member."""
        if recipient not in self.members:
            raise ValueError("Recipient must be a party member")
        if self.total_gold() < item.cost:
            return False
        recipient.add_item(item)
        remaining = item.cost
        for member in self.members:
            contribution = min(max(member.gold, 0), remaining)
            member.gold -= contribution
            remaining -= contribution
            if remaining <= 0:
                break
        return True
        
    def distribute_gold(self, amount):
        """Distribute gold evenly among party members"""
        share = amount // len(self.members)
        remainder = amount % len(self.members)
        
        for member in self.members:
            member.gold += share
            
        # Give remainder to first member
        if self.members:
            self.members[0].gold += remainder
            
    def distribute_experience(self, amount):
        """Distribute experience evenly among alive party members"""
        alive = self.get_alive_members()
        if not alive:
            return
            
        share = amount // len(alive)
        for member in alive:
            member.gain_experience(share)
            
    def rest(self):
        """Rest to restore HP (short rest)"""
        for member in self.members:
            member.short_rest()
            
    def full_rest(self):
        """Full rest to restore all HP and spell slots"""
        for member in self.members:
            member.long_rest()
    
    def average_level(self):
        """Get average level of alive party members"""
        alive = self.get_alive_members()
        if not alive:
            return 0
        return sum(m.level for m in alive) / len(alive)
            
    def __len__(self):
        return len(self.members)
        
    def __getitem__(self, index):
        return self.members[index]
        
    def __iter__(self):
        return iter(self.members)
