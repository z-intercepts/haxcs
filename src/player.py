"""
    haxcs: an old-school roguelike with a computer science theme
    Copyright (C) 2018 Mike Lam

    This file contains player information storage and logic.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import random
from geom import Point

NAMES = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi",
        "Ivan", "Judy", "Kate", "Leo", "Mallory", "Neil", "Olivia", "Paul",
        "Quincy", "Ruth", "Sybil", "Trudy", "Ursula", "Victor", "Wendy",
        "Xavier", "Yan", "Zeke"]

RACES = ["Human", "Android", "AI"]
CLASSES = ["Hacker", "Developer", "Sysadmin", "Researcher", "Intern"]

#             1  2  3   4   5   6   7   8    9   10 (max)
XP_LEVELS = [ 0, 3, 7, 12, 18, 25, 40, 75, 120, 200, 999999999 ]

WALKABLE = { '.', '#', '<', '>' }
LCASE_DIRECTIONS = [ 'h', 'l', 'j', 'k', 'y', 'b', 'u', 'n' ]
UCASE_DIRECTIONS = [ 'H', 'L', 'J', 'K', 'Y', 'B', 'U', 'N' ]
DIRECTION_OFFSETS = {
    'h': Point( 0,-1), 'H': Point( 0,-1),
    'l': Point( 0, 1), 'L': Point( 0, 1),
    'j': Point( 1, 0), 'J': Point( 1, 0),
    'k': Point(-1, 0), 'K': Point(-1, 0),
    'y': Point(-1,-1), 'Y': Point(-1,-1),
    'b': Point( 1,-1), 'B': Point( 1,-1),
    'u': Point(-1, 1), 'U': Point(-1, 1),
    'n': Point( 1, 1), 'N': Point( 1, 1)
}

class Player:
    '''
    PC-related data and logic
    '''

    def __init__(self):
        self.floor     = 0
        self.pos       = Point(0,0)   # overwritten by game state initialization
        self.level     = 1
        self.xp        = 0
        self.next_lvl  = XP_LEVELS[1]
        self.hp        = 10
        self.max_hp    = 10
        self.dmg       = "1d6"
        self.vis_range = 15
        self.gp        = 0
        self.potions   = 1
        self.name      = random.choice(NAMES)
        self.race      = random.choice(RACES)
        self.pclass    = random.choice(CLASSES)

    def handle_input(self, game, screen, c):
        '''
        decode and execute a player command
        returns true if a turn should pass; false otherwise
        '''
        cc = chr(c) if c in range(256) else '\0'
        cfloor = game.get_cur_floor()

        # go upstairs
        if cc == '<':
            if self.floor > 0 and cfloor.get_base_pt(self.pos) == '<':
                self.floor -= 1
                game.add_status("You go up the stairs.")
                game.next_turn()

        # go downstairs
        elif cc == '>':
            if self.floor < len(game.floors)-1 and \
                    cfloor.get_base_pt(self.pos) == '>':
                self.floor += 1
                game.add_status("You go down the stairs.")
                game.next_turn()

        # attack or move one step in the given direction
        elif cc in LCASE_DIRECTIONS:
            newpt = self.pos.add(DIRECTION_OFFSETS[cc])
            npcs = game.npcs_at(self.floor, newpt)
            if len(npcs) > 0:
                random.choice(npcs).handle_attack(game, self)
                game.next_turn()
            elif cfloor.get_base_pt(newpt) in WALKABLE:
                self.pos = newpt
                game.next_turn()

        # move in a straight line until we hit a wall or NPC
        elif cc in UCASE_DIRECTIONS:
            while self.can_keep_walking(game, DIRECTION_OFFSETS[cc]):
                self.pos = self.pos.add(DIRECTION_OFFSETS[cc])
                game.next_turn()

        # open door
        elif cc == 'o':
            d = chr(screen.getch())
            if d in LCASE_DIRECTIONS:
                pt = self.pos.add(DIRECTION_OFFSETS[d])
                if cfloor.get_base_pt(pt) == '+':
                    cfloor.set_base_pt(pt, '.')
                    game.add_status("The door opens.")
                    game.next_turn()

        # search / sleep
        elif cc == 's':
            game.next_turn()

        # quaff potion
        elif cc == 'q':
            if self.potions > 0:
                self.potions -= 1
                self.heal(2 + self.level)
                game.add_status("You quaff a potion--it heals you!")
                game.next_turn()
            else:
                game.add_status("You have no potions.")

    def can_keep_walking(self, game, offset):
        '''
        determine whether SHIFT-dir walking can continue (next step must be
        walkable and clear of NPCs, and there mustn't be any NPCs around the
        player or the destination
        '''
        newpt = self.pos.add(offset)
        if game.get_cur_floor().get_base_pt(newpt) not in WALKABLE:
            return False
        if not game.nothing_at(self.floor, newpt):
            return False
        for _,d in DIRECTION_OFFSETS.items():
            if not game.no_npcs_at(self.floor, self.pos.add(d)):
                return False
            if not game.no_npcs_at(self.floor, newpt.add(d)):
                return False
        return True;

    def level_up(self, game):
        '''
        handle the process of leveling up (can handle multiple levels
        simultaneously)
        '''
        while self.xp >= XP_LEVELS[self.level]:
            self.level += 1
            self.hp += 5
            self.max_hp += 5
            game.add_status("You leveled up!")


    def roll_damage(self):
        '''
        roll dice to determine player damage
        '''
        # figure out which dice to roll
        # (e.g., "2d6" means "roll two 6-sided dice")
        tmp = self.dmg.split('d')
        num = int(tmp[0])
        max_dmg = int(tmp[1])

        # roll the dice and add up the total damage
        total_dmg = 0
        for i in range(num):
            total_dmg = random.randint(1, max_dmg)
        return total_dmg

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.max_hp)

    def take_dmg(self, amount):
        self.hp -= amount

    def kill(self):
        self.hp = 0

