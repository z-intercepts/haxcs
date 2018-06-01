"""
    haxcs: an old-school roguelike with a computer science theme
    Copyright (C) 2018 Mike Lam

    This file contains the logic for generating random dungeon floors.

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

import collections
import random

from geom import Point, Rect

DEFAULT_ROOM_NUM_LLIMIT = 5
DEFAULT_ROOM_NUM_ULIMIT = 8

DEFAULT_ROOM_WIDTH_MIN  = 6
DEFAULT_ROOM_WIDTH_MAX  = 22
DEFAULT_ROOM_HEIGHT_MIN = 4
DEFAULT_ROOM_HEIGHT_MAX = 10

DEFAULT_ROOM_HORIZONTAL_BUFFER = 10
DEFAULT_ROOM_VERTICAL_BUFFER   = 5

INVALID_ROOM = Rect(0,0,0,0)

VISION_BLOCKERS = { ' ', '+', '-', '|' }
EXPLORABLES     = { ' ',      '-', '|', '#' }

class Floor:
    '''
    "floor" = 2d array of base characters implemented as a list of strings
    '''

    def __init__(self, width, height, up):
        self.width = width
        self.height = height
        self.up = up
        self.down = None
        self.rooms = []
        self.base = []
        self.explored = []
        for row in range(height):
            line = " " * width
            self.base.append(line)
            self.explored.append(line)

    def get_base(self, row, col):
        return self.base[row][col] if self.is_inside(row, col) else '\0'

    def get_base_pt(self, pt):
        return self.get_base(pt.row, pt.col)

    def base_blocks_vision(self, row, col):
        return self.base[row][col] in VISION_BLOCKERS

    def set_base(self, row, col, char):
        self.base[row] = self.base[row][:col] + char + self.base[row][col+1:]

    def set_base_pt(self, pt, char):
        self.set_base(pt.row, pt.col, char)

    def explore(self, row, col):
        if self.base[row][col] in EXPLORABLES:
            self.explored[row] = self.explored[row][:col] + \
                    self.base[row][col] + self.explored[row][col+1:]

    def explore_pt(self, pt):
        self.explore(pt.row, pt.col)

    def is_inside(self, row, col):
        return (row >= 0 and row < self.height and
                col >= 0 and col < self.width)

    def is_rect_inside(self, rect):
        return (self.is_inside(rect.top,      rect.left) and
                self.is_inside(rect.bottom-1, rect.left) and
                self.is_inside(rect.top,      rect.right-1) and
                self.is_inside(rect.bottom-1, rect.right-1))

    def is_rect_empty(self, rect):
        valid = self.is_rect_inside(rect)
        if valid:
            for row in range(rect.top, rect.bottom):
                for col in range(rect.left, rect.right):
                    if self.base[row][col] != ' ':
                        valid = False
        return valid

    def add_room(self, room):
        self.rooms.append(room)
        [left, right, top, bottom] = room.bounds()
        for row in range(top, bottom):
            for col in range(left, right):
                if row == top or row == bottom-1:
                    self.set_base(row, col, '-')
                elif col == left or col == right-1:
                    self.set_base(row, col, '|')
                else:
                    self.set_base(row, col, '.')

    def random_point(self, vbuffer=0, hbuffer=0):
        row = random.randrange(vbuffer, self.height-vbuffer)
        col = random.randrange(hbuffer, self.width-hbuffer)
        return Point(row,col)

    def random_point_in_room(self, vbuffer=0, hbuffer=0):
        pt = self.random_point(vbuffer, hbuffer)
        while not self.is_in_room(pt.row, pt.col):
            pt = self.random_point(vbuffer, hbuffer)
        return pt

    def is_in_room(self, row, col):
        return self.is_inside(row, col) and self.base[row][col] == '.'

    def generate_door (self, default='#'):
        return '+' if random.random() < 0.33 else default

    def generate_room(self, center=None):
        '''
        generate random locations until a valid room is found
        '''
        count = 0
        valid = False
        while not valid:

            # generate center
            if center == None:
                pt = self.random_point(DEFAULT_ROOM_VERTICAL_BUFFER,
                        DEFAULT_ROOM_HORIZONTAL_BUFFER)
                row = pt.row
                col = pt.col
            else:
                row = center.row
                col = center.col

            # generate size
            height = random.randrange(DEFAULT_ROOM_HEIGHT_MIN,
                    DEFAULT_ROOM_HEIGHT_MAX, 2)
            width = random.randrange(DEFAULT_ROOM_WIDTH_MIN,
                    DEFAULT_ROOM_WIDTH_MAX, 2)

            # check for empty area in floor
            room = Rect(col-width/2,  col+width/2+1,
                        row-height/2, row+height/2+1)
            room.grow(2)
            valid = self.is_rect_empty(room)
            room.shrink(2)

            # stop looking if we've looked too long
            count = count + 1
            if not valid and count > 500:
                return INVALID_ROOM

        return room

    def connect_rooms (self, room1, room2, permissive=False, tries=5):
        '''
        generates a connecting straight path between two rooms if one is
        possible without overwriting any other paths or rooms; in permissive
        mode the path is allowed to overwrite/intersect with other paths;
        returns true if the rooms could be connected and false otherwise
        '''
        room1.shrink()
        room2.shrink()
        [l1, r1, t1, b1] = room1.bounds()
        [l2, r2, t2, b2] = room2.bounds()
        room1.grow()
        room2.grow()
        path_created = False
        attempts = 0

        while not path_created and attempts < tries:
            attempts += 1

            # horizontal path
            if (t1 <= t2 and b1 >= t2) or (t2 <= t1 and b2 >= t1):
                top = max(t1,t2)
                bot = min(b1,b2)
                left = min(r1,r2)
                right = max(l1,l2)
                if top < bot:
                    row = random.randrange(top,bot)
                    valid = True
                    for col in range(left,right):
                        if not (self.base[row][col] == ' ' or
                                self.base[row][col] == '|' or
                                (permissive and self.base[row][col] == '#')):
                            valid = False
                    if valid:
                        path_created = True
                        for col in range(left,right):
                            if self.base[row][col] == ' ':
                                self.set_base(row, col, '#')
                            elif self.base[row][col] == '|':
                                self.set_base(row, col, self.generate_door())

            # vertical path
            if ((l1 <= l2 and r1 >= l2) or (l2 <= l1 and r2 >= l1)):
                left = max(l1,l2)
                right = min(r1,r2)
                top = min(b1,b2)
                bot = max(t1,t2)
                if left < right:
                    col = random.randrange(left,right)
                    valid = True
                    for row in range(top,bot):
                        if not (self.base[row][col] == ' ' or
                                self.base[row][col] == '-' or
                                (permissive and self.base[row][col] == '#')):
                            valid = False
                    if valid:
                        path_created = True
                        for row in range(top,bot):
                            if self.base[row][col] == ' ':
                                self.set_base(row, col, '#')
                            elif self.base[row][col] == '-':
                                self.set_base(row, col, self.generate_door())
        return path_created

    @staticmethod
    def generate_basic_floor (width, height, up=None, debug=False):
        '''
        generate a floor with some rooms and paths between them; all rooms are
        guaranteed to be reachable
        '''
        floor = Floor(width, height, up)

        if up == None:
            # this is the first floor; just pick a random upstairs location
            floor.up = floor.random_point(DEFAULT_ROOM_VERTICAL_BUFFER,
                    DEFAULT_ROOM_HORIZONTAL_BUFFER)

        # generate first room
        room = floor.generate_room(floor.up)
        if room == INVALID_ROOM:
            raise "Cannot generate first room!"
        floor.add_room(room)
        floor.set_base_pt(floor.up, '<')

        # generate other rooms
        for r in range(random.randrange(DEFAULT_ROOM_NUM_LLIMIT,
                                        DEFAULT_ROOM_NUM_ULIMIT)):
            room = floor.generate_room()
            if not room == INVALID_ROOM:
                floor.add_room(room)

                if debug:   # add room label to upper-left corner
                    floor.set_base(room.top, room.left, str(r+1))

        # adjacency lists for tracking room connections
        adjacent = {}
        for r in range(len(floor.rooms)):
            adjacent[r] = set()

        # breadth-first search from first room to try to connect all rooms
        connected = {0}
        workqueue = collections.deque()
        workqueue.append(0)
        while len(workqueue) > 0:
            r1 = workqueue.popleft()
            for r2 in range(len(floor.rooms)):
                if r2 not in connected:
                    if floor.connect_rooms(floor.rooms[r1],
                                           floor.rooms[r2], False, 5):
                        adjacent[r1].add(r2)
                        adjacent[r2].add(r1)
                        connected.add(r2)
                        workqueue.append(r2)

        if debug:
            print ("After first pass: connected = " + str(connected))

        # try again (more aggressively) to connect unconnected rooms
        for r1 in range(len(floor.rooms)):
            if r1 not in connected:
                for r2 in range(len(floor.rooms)):
                    if r1 != r2 and r2 in connected:
                        if debug:
                            print ("2nd pass: connecting " + str(r1) + " to " + str(r2))
                        if floor.connect_rooms(floor.rooms[r1],
                                               floor.rooms[r2], True, 10):
                            adjacent[r1].add(r2)
                            adjacent[r2].add(r1)
                            connected.add(r1)
                            break

        # add a few extra connections (low effort; for aesthetics only)
        for i in range(10):
            r1 = random.randrange(len(floor.rooms))
            r2 = random.randrange(len(floor.rooms))
            if r1 != r2 and r1 not in adjacent[r2]:
                if floor.connect_rooms(floor.rooms[r1],
                                       floor.rooms[r2], False, 1):
                    adjacent[r1].add(r2)
                    adjacent[r2].add(r1)

        # generate downstairs
        floor.down = floor.random_point_in_room(6,6)
        floor.set_base_pt(floor.down, '>')

        # check full-connectedness
        if len(connected) == len(floor.rooms):
            # all rooms are connected -- good to go
            return floor
        else:
            # this level is potentially impossible -- need to start over
            return Floor.generate_basic_floor(width, height, up, debug)


if __name__ == "__main__":
    f = Floor.generate_basic_floor(80,25,None,True)
    for line in f.base:     # print floor (base only)
        print (line)

