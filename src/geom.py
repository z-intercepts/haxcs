"""
    haxcs: an old-school roguelike with a computer science theme
    Copyright (C) 2018 Mike Lam

    This file contains some useful geometry primitives.

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

class Point:
    '''
    "point" = [ row, col ]
    '''

    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.row == other.row and self.col == other.col
        else:
            return False

    def add(self, pt):
        return Point(self.row + pt.row, self.col + pt.col)

    def offset(self, voffset, hoffset):
        return Point(self.row + voffset, self.col + hoffset)

    def dist_sq(self, pt):
        dy = abs(self.row - pt.row)
        dx = abs(self.col - pt.col)
        return dy*dy + dx*dx


class Rect:
    '''
    "rect"  = [ left, right (exclusive)
                top,  bottom (exclusive) ]
    '''

    def __init__(self, left, right, top, bottom):
        self.left   = int(left)
        self.right  = int(right)
        self.top    = int(top)
        self.bottom = int(bottom)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.left == other.left and self.right  == other.right and \
                   self.top  == other.top  and self.bottom == other.bottom
        else:
            return False

    def width(self):
        return self.right - self.left

    def height(self):
        return self.bottom - self.top

    def bounds(self):
        return [self.left, self.right, self.top, self.bottom]

    def shrink(self, amount=1):
        self.left   = self.left   + amount
        self.right  = self.right  - amount
        self.top    = self.top    + amount
        self.bottom = self.bottom - amount

    def grow(self, amount=1):
        self.left   = self.left   - amount
        self.right  = self.right  + amount
        self.top    = self.top    - amount
        self.bottom = self.bottom + amount



