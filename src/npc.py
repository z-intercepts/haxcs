"""
    haxcs: an old-school roguelike with a computer science theme
    Copyright (C) 2018 Mike Lam

    This file contains NPC logic routines.

    Current enemy NPCs:
        * bug (does little damage and wanders randomly, but has a chance of
               splitting into two instead of dying when killed)
        * segfault (becomes more common the deeper you go; chases the player)
        * spectre (teleports around the level and gets free attacks on the
                   place it predicts the player will move)

    Enemy NPC ideas:
        * gridbug (similar to bug but more dangerous;
                   also glows neon and quotes Tron every few turns)
        * agent (high damage, uses A* to chase player; weak v. hackers)
        * qubit (can be in several locations at once)
        * virus (chance to freeze player for a turn)
        * worm (weak but begins spawning new instances when spotted)
        * trojan (mimic; looks like other creatures and hits hard)
        * spam (like worm but spawns even faster; no damage, just an obstacle)
        * edgecase (invisible but only moves along the borders of a room)
        * offbyone (appears to be at previous location; inverted spectre)
        * p~np (enormous hitpoints, low damage; tries to block downstairs)

    Friendly NPC ideas:
        * oracle (quotes Unix "fortune" when touched)
        * mindflayer (cleric; heals player -- DID YOU THINK THIS WAS D&D?!?!?)
        * antivirus (paladin; insta-kills viruses, worms, and trojans)
        * taskman (ranger; shoots "kill process" darts; not always effective)
        * cryptominer (thief; slows down all enemy NPCs on the floor)
        * midi (bard; increases max_hp and dmg of player)
        * knuth (wizard; insta-kills all enemies until distracted by p~np)

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

D_UP        = Point(-1, 0)
D_DOWN      = Point( 1, 0)
D_LEFT      = Point( 0,-1)
D_RIGHT     = Point( 0, 1)
D_CARDINAL  = [D_UP, D_DOWN, D_LEFT, D_RIGHT]
D_UPLEFT    = Point(-1,-1)
D_UPRIGHT   = Point(-1, 1)
D_DOWNLEFT  = Point( 1,-1)
D_DOWNRIGHT = Point( 1, 1)
D_ALLDIRS   = [D_UP, D_DOWN, D_LEFT, D_RIGHT,
               D_UPLEFT, D_UPRIGHT, D_DOWNLEFT, D_DOWNRIGHT]

class NPC:
    '''
    Base class for a single non-player-character. In general, this base class
    should not be instantiated; that would cause a Bad Thing(tm) to happen.
    '''

    def __init__(self, floor, pos):
        self.floor = floor
        self.pos = pos
        self.setup()

    def setup(self):
        self.name  = "Glitch"
        self.glyph = "?"
        self.hp    = 500
        self.dmg   = "1d9001"
        self.kxp   = "42"
        self.turns_till_death = 6       # five ticks

    def do_turn(self, game):
        self.turns_till_death -= 1
        game.add_status("The glitch chirps the number " + str(self.turns_till_death) + "!")
        if self.turns_till_death == 0:
            game.player.kill()

    def roll_damage(self):

        # figure out which dice to roll
        tmp = self.dmg.split('d')
        num = int(tmp[0])
        max_dmg = int(tmp[1])

        # roll the dice
        total_dmg = 0
        for i in range(num):
            total_dmg = random.randint(1, max_dmg)
        return total_dmg

    def handle_attack(self, game, attacker):
        pass

class zach(NPC):
    
    WALKABLE = ['.', '#', '<', '>']

    @staticmethod
    def generate(game):
        # become less common the deeper you dive into the system
          for f in range(len(game.floors)):
              for i in range(random.randrange(0, 10-f)):
                 game.npcs.append(Bug(f, game.floors[f].random_point_in_room()))
    
    def setup(self):
        self.name  = "Zach"
        self.glyph = "Z"
        self.hp    = 5
        self.dmg   = "1d1"
        self.kxp   = 5

    def pos_clear(self, game, pos):
        return game.floors[self.floor].get_base_pt(pos) in self.WALKABLE and \
               game.nothing_at(self.floor, pos)

    def do_turn(self, game):

        # if beside player, attack
        for d in D_CARDINAL:
            if self.pos.add(d) == game.player.pos:
                game.add_status("The bug manifests!")
                game.player.take_dmg(self.roll_damage())
                return

        # otherwise, with 2/3 probability wander aimlessly in a cardinal direction
        if random.random() < 0.67:
            newpt = self.pos.add(random.choice(D_CARDINAL))
            if self.pos_clear(game, newpt):
                self.pos = newpt

    def handle_attack(self, game, attacker):
        self.hp -= attacker.roll_damage()
        if self.hp <= 0:

            # with 1/3 probability, split into two rather than dying
            # (if a new bug can't be created due to obstacles, the original
            #  still remains alive)
            if random.random() < 0.1:
                self.hp = 1
                for d in D_CARDINAL:
                    newpt = self.pos.add(d)
                    if self.pos_clear(game, self.pos.add(d)):
                        game.add_status("Zach reproduces!")
                        game.npcs.append(Bug(self.floor, newpt))
                        break
            else:
                # bug is actually dead
                game.add_status("He deserved what he got")
                game.npcs.remove(self)
                game.player.xp += self.kxp

                # display special message if all bugs on the floor are dead
                for npc in game.npcs:
                    if npc.name == "Bug" and npc.floor == self.floor:
                        return
                game.add_status("You stopped Zach from coding ever again!")



class Bug(NPC):
    '''
    Bugs are common, especially near the surface. They will always attack the
    player if possible, but they are limited in that they can only move and
    attack in cardinal directions. They also do very limited damage
    individually. However, when killed there is a chance that the bug will
    be reborn and split into two new full-health bugs. This can make an
    innocuous situation very dangerous quickly if they are not controlled
    early and deliberately.
    '''

    WALKABLE = [ '.', '#', '<', '>' ]

    @staticmethod
    def generate(game):
        # become less common the deeper you dive into the system
        for f in range(len(game.floors)):
            for i in range(random.randrange(0, 10-f)):
                game.npcs.append(Bug(f, game.floors[f].random_point_in_room()))

    def setup(self):
        self.name  = "Bug"
        self.glyph = "x"
        self.hp    = 1
        self.dmg   = "1d2"
        self.kxp   = 1

    def pos_clear(self, game, pos):
        return game.floors[self.floor].get_base_pt(pos) in self.WALKABLE and \
               game.nothing_at(self.floor, pos)

    def do_turn(self, game):

        # if beside player, attack
        for d in D_CARDINAL:
            if self.pos.add(d) == game.player.pos:
                game.add_status("The bug manifests!")
                game.player.take_dmg(self.roll_damage())
                return

        # otherwise, with 2/3 probability wander aimlessly in a cardinal direction
        if random.random() < 0.67:
            newpt = self.pos.add(random.choice(D_CARDINAL))
            if self.pos_clear(game, newpt):
                self.pos = newpt

    def handle_attack(self, game, attacker):
        self.hp -= attacker.roll_damage()
        if self.hp <= 0:

            # with 1/3 probability, split into two rather than dying
            # (if a new bug can't be created due to obstacles, the original
            #  still remains alive)
            if random.random() < 0.33:
                self.hp = 1
                for d in D_CARDINAL:
                    newpt = self.pos.add(d)
                    if self.pos_clear(game, self.pos.add(d)):
                        game.add_status("The bug reproduces!")
                        game.npcs.append(Bug(self.floor, newpt))
                        break
            else:
                # bug is actually dead
                game.add_status("The bug has been fixed!")
                game.npcs.remove(self)
                game.player.xp += self.kxp

                # display special message if all bugs on the floor are dead
                for npc in game.npcs:
                    if npc.name == "Bug" and npc.floor == self.floor:
                        return
                game.add_status("Floor is bug-free!")


class Segfault(NPC):
    '''
    The Segfault is a fairly common enemy, and gets increasingly common the
    lower the player goes. They hit harder than bugs and can hit in any
    direction, but unlike bugs they do not always attack when given the
    opportunity. They do however tend to try to chase the player, albeit in
    a fairly unimaginative manner.
    '''

    WALKABLE = [ '.', '#', '<', '>' ]

    @staticmethod
    def generate(game):
        # become more common the deeper you dive into the system
        for f in range(len(game.floors)):
            for i in range(random.randrange(f, (f+1)*2+1)):
                game.npcs.append(Segfault(f, game.floors[f].random_point_in_room()))

    def setup(self):
        self.name  = "Segfault"
        self.glyph = "v"
        self.hp    = 4
        self.dmg   = "1d4"
        self.kxp   = 2

    def pos_clear(self, game, pos):
        return game.floors[self.floor].get_base_pt(pos) in self.WALKABLE and \
               game.nothing_at(self.floor, pos)

    def do_turn(self, game):

        # with 3/4 probability, attack player if beside them
        if random.random() < 0.75:
            for d in D_ALLDIRS:
                if self.pos.add(d) == game.player.pos:
                    game.add_status("Segmentation fault!")
                    game.player.take_dmg(self.roll_damage())
                    return

        # otherwise, with 2/3 probability, try to get closer to player
        if random.random() < 0.67:
            cdist = game.player.pos.dist_sq(self.pos)
            dirs = list(D_ALLDIRS)
            random.shuffle(dirs)
            for d in dirs:
                newpt = self.pos.add(d)
                if game.player.pos.dist_sq(newpt) < cdist and \
                        self.pos_clear(game, newpt):
                    self.pos = newpt
                    return

        # otherwise, with 2/3 probability wander aimlessly
        if random.random() < 0.67:
            newpt = self.pos.add(random.choice(D_ALLDIRS))
            if self.pos_clear(game, newpt):
                self.pos = newpt

    def handle_attack(self, game, attacker):
        dmg = attacker.roll_damage()
        self.hp -= dmg
        game.add_status("The segfault was hit for " + str(dmg) + " damage.")
        if self.hp <= 0:
            game.add_status("The segfault has been handled!")
            game.npcs.remove(self)
            game.player.xp += self.kxp


class Spectre(NPC):
    '''
    A mysterious entity that haunts the lowest level of the dungeon, the
    spectre is part real and part spirit. Thus, it cannot see the player
    directly, and so it must infer the player's location from their previous
    actions. Being part spirit, it can teleport at will around the floor,
    and will attempt to attack the square where it believes the player will go.
    The player would be wise to avoid predictable movement while engaging
    the spectre in combat.
    '''

    WALKABLE = [ '.', '#', '<', '>', ' ' ]

    @staticmethod
    def generate(game):
        # spawn one on the lowest floor of the system
        game.npcs.append(Spectre(len(game.floors)-1,
                game.floors[-1].random_point_in_room()))

    def setup(self):
        self.name  = "Spectre"
        self.glyph = "&"
        self.hp    = 40
        self.dmg   = "2d6"
        self.kxp   = 4
        self.lastppos = self.pos    # for speculative execution
        self.prevppos = self.pos

    def pos_clear(self, game, pos):
        return game.floors[self.floor].get_base_pt(pos) in self.WALKABLE and \
               game.nothing_at(self.floor, pos)

    def do_turn(self, game):

        # speculate as to the player's current position using their last two
        target = self.lastppos.offset(self.lastppos.row - self.prevppos.row,
                                      self.lastppos.col - self.prevppos.col)

        # update trackers
        self.prevppos = self.lastppos
        self.lastppos = game.player.pos

        # if beside player, attack with 1/4 probability
        for d in D_ALLDIRS:
            if self.pos.add(d) == game.player.pos and random.random() < 0.25:
                game.add_status("The spectre hits!")
                game.player.take_dmg(self.roll_damage())
                return

        # otherwise, with probability 2/3, teleport beside player's predicted
        # location and get a free attack on them if they are there
        if random.random() < 0.67:
            dirs = list(D_ALLDIRS)
            random.shuffle(dirs)
            for d in dirs:
                newpt = target.add(d)
                if self.pos_clear(game, newpt):
                    self.pos = newpt
                    game.add_status("The spectre teleports!")
                    if game.player.pos == target:
                        game.add_status("Speculative execution!")
                        game.player.take_dmg(self.roll_damage())
                    return

        # otherwise, with probability 1/4, teleport to a random location on the
        # player's floor
        if random.random() < 0.25:
            self.pos = game.floors[game.player.floor].random_point_in_room()
            game.add_status("The spectre teleports!")
            return

        # otherwise, try to get closer to the target location; if it bumps into
        # the real player it hits them
        cdist = target.dist_sq(self.pos)
        dirs = list(D_ALLDIRS)
        random.shuffle(dirs)
        for d in dirs:
            newpt = self.pos.add(d)
            if target.dist_sq(newpt) < cdist and \
                    self.pos_clear(game, newpt):
                if game.player.pos == newpt:
                    game.add_status("The spectre hits!")
                    game.player.take_dmg(self.roll_damage())
                else:
                    self.pos = newpt


    def handle_attack(self, game, attacker):
        dmg = attacker.roll_damage()
        self.hp -= dmg
        game.add_status("The spectre was hit for " + str(dmg) + " damage.")
        if self.hp <= 0:
            game.add_status("The spectre has a meltdown! It is dead.")
            game.npcs.remove(self)
            game.player.xp += self.kxp

