"""
The game state and logic (model component) of 512, 
a game based on 2048 with a few changes. 
This is the 'model' part of the model-view-controller
construction plan.  It must NOT depend on any
particular view component, but it produces event 
notifications to trigger view updates. 
"""

from game_element import GameElement, GameEvent, EventKind
from typing import List, Tuple, Optional
import random

# Configuration constants
GRID_SIZE = 4

class Vec():
    """A Vec is an (x,y) or (row, column) pair that
    represents distance along two orthogonal axes.
    Interpreted as a position, a Vec represents
    distance from (0,0).  Interpreted as movement,
    it represents distance from another position.
    Thus we can add two Vecs to get a Vec.
    """
    #Fixme:  We need a constructor, and __add__ method, and __eq__.
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other: 'Vec') -> 'Vec':
        return Vec(self.x + other.x, self.y + other.y)

    def __eq__(self, other: 'Vec') -> 'Vec':
        return self.x == other.x and self.y == other.y






class Tile(GameElement):
    """A slidy numbered thing."""

    def __init__(self, pos: Vec, value: int):
        super().__init__()
        self.row = pos.x
        self.col = pos.y
        self.value = value

    def __repr__(self):
        """Not like constructor --- more useful for debugging"""
        return f"Tile[{self.row},{self.col}]:{self.value}"

    def __str__(self):
        return str(self.value)

    def move_to(self, new_pos: Vec):
        self.row = new_pos.x
        self.col = new_pos.y
        self.notify_all(GameEvent(EventKind.tile_updated, self))

    def __eq__(self, other: "Tile"):
        return self.value == other.value

    def merge(self, other: "Tile"):
        # This tile incorporates the value of the other tile
        self.value = self.value + other.value
        self.notify_all(GameEvent(EventKind.tile_updated, self))
        # The other tile has been absorbed.  Resistance was futile.
        other.notify_all(GameEvent(EventKind.tile_removed, other))




class Board(GameElement):
    """The game grid.  Inherits 'add_listener' and 'notify_all'
    methods from game_element.GameElement so that the game
    can be displayed graphically.
    """

    def __init__(self, rows=4, cols=4):
        super().__init__()
        self.tiles = []  # FIXME: a grid holds a matrix of tiles
        self.rows = rows
        self.cols = cols
        for row in range(rows):
            row_tiles = []
            for col in range(cols):
                row_tiles.append(None)
            self.tiles.append(row_tiles)

    def __getitem__(self, pos: Vec) -> Tile:
        return self.tiles[pos.x][pos.y]

    def __setitem__(self, pos: Vec, tile: Tile):
        self.tiles[pos.x][pos.y] = tile

    def _empty_positions(self) -> List[Vec]:
        """Return a list of positions of None values,
        i.e., unoccupied spaces.
        """
        empty = []
        for row in range(len(self.tiles)):
            for col in range(len(self.tiles[row])):
                if self.tiles[row][col] is None:
                    empty.append(Vec(row, col))
        return empty

    def has_empty(self) -> bool:
        """Is there at least one grid element without a tile?"""
        if self._empty_positions == []:
            return False
        else:
            return True

        # FIXME: Should return True if there is some element with value None

    def place_tile(self, value=None):
        """Place a tile on a randomly chosen empty square."""
        empty = self._empty_positions()
        assert len(empty) > 0
        choice = random.choice(empty)
        row, col = choice.x, choice.y
        if value is None:
            # 0.1 probability of 4
            if random.random() <= 0.1:
                value = 4
            else:
                value = 2
        new_tile = Tile(Vec(row, col), value)
        self.tiles[row][col] = new_tile
        self.notify_all(GameEvent(EventKind.tile_created, new_tile))

    def score(self) -> int:
        """Calculate a score from the board.
        (Differs from classic 1024, which calculates score
        based on sequence of moves rather than state of
        board.
        """
        count = 0
        for row in range(len(self.tiles)):
            for col in range(len(self.tiles)):
                count += self.tiles[row][col].values
        return count

    def to_list(self) -> List[List[int]]:
        """Test scaffolding: represent each Tile by its
        integer value and empty positions as 0
        """
        result = [ ]
        for row in self.tiles:
            row_values = []
            for col in row:
                if col is None:
                    row_values.append(0)
                else:
                    row_values.append(col.value)
            result.append(row_values)
        return result

    def from_list(self, values: List[List[int]]):
        ''' inverse of to list'''
        for row in range(len(values)):
            for col in range(len(values[row])):
                if values[row][col] == 0:
                    self.tiles[row][col] = None
                else:
                    self.tiles[row][col] = Tile(Vec(row, col), values[row][col])

    def in_bounds(self, pos: Vec) -> bool:
        """Is position (pos.x, pos.y) a legal position on the board?"""
        if pos.y >= 0:
            if pos.y < self.cols:
                if pos.x >= 0:
                    if pos.x < self.rows:
                        return True # if any of these are true then it will return True otherwise it is False
        return False

    def _move_tile(self, old_pos: Vec, new_pos: Vec):
        '''moves the tile to a new position'''
        self.tiles[old_pos.x][old_pos.y].move_to(new_pos)
        self.tiles[new_pos.x][new_pos.y] = self.tiles[old_pos.x][old_pos.y]
        self.tiles[old_pos.x][old_pos.y] = None

    def slide(self, pos: Vec,  dir: Vec):
        """Slide tile at pos.x, pos.y (if any)
        in direction (dir.x, dir.y) until it bumps into
        another tile or the edge of the board.
        """
        if self[pos] is None:
            return
        while True:
            new_pos = pos + dir
            if not self.in_bounds(new_pos):
                break
            if self[new_pos] is None:
                self._move_tile(pos, new_pos)
            elif self[pos] == self[new_pos]:
                self[pos].merge(self[new_pos])
                self._move_tile(pos, new_pos)
                break  # Stop moving when we merge with another tile
            else:
                # Stuck against another tile
                break
            pos = new_pos

    def right(self):
        '''moves tiles right'''
        for row in range(self.rows):
            for col in reversed(range(self.cols)):
                self.slide(Vec(row, col), Vec(0, 1))

    def left(self):
        '''moves tiles left'''
        for row in range(self.rows):
            for col in range(self.cols):
                self.slide(Vec(row, col), Vec(0, -1))

    def up(self):
        '''moves tiles up'''
        for row in range(self.rows):
            for col in range(self.cols):
                self.slide(Vec(row, col), Vec(-1, 0))

    def down(self):
        '''moves tiles down'''
        for row in reversed(range(self.rows)):
            for col in range(self.cols):
                self.slide(Vec(row, col), Vec(1, 0))



