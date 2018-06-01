#!/usr/bin/env python

"""
    haxcs: an old-school roguelike with a computer science theme
    Copyright (C) 2018 Mike Lam

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
import curses

from game import Game

def main():

    # initialize game (loading previous savegame if present)
    random.seed()
    main_game = Game.load_savegame()
    if main_game is None:
        main_game = Game()

    # main game loop
    curses.wrapper(main_game.run)

    # print hall of fame
    Game.print_hof()

main()

