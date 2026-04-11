from dataclasses import dataclass
import math
import copy

@dataclass(frozen=True)

class Move:
    from_tile : tuple | None
    to_tile : tuple
    piece : str
    promote : bool = False
    drop : bool = False

PIECE_VALUES = {
    'P': 1, 'L': 3, 'N': 3, 'S': 4, 'G': 5,
    'B': 8, 'R': 10,
    '+P': 5, '+L': 5, '+N': 5, '+S': 5, '+B': 11, '+R': 13,
    'K': 1000
}

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(9)] for _ in range(9)]
        self.to_move = 1 
        self.hands = {1: [], -1: []}

    def initial_setup(self):
        self.grid[0] = [
            (-1, 'L'), (-1, 'N'), (-1, 'S'), (-1, 'G'),
            (-1, 'K'),
            (-1, 'G'), (-1, 'S'), (-1, 'N'), (-1, 'L')
        ]
        self.grid[1][1] = (-1, 'R')
        self.grid[1][7] = (-1, 'B')
        for c in range(9):
            self.grid[2][c] = (-1, 'P')

        self.grid[8] = [
            (1, 'L'), (1, 'N'), (1, 'S'), (1, 'G'),
            (1, 'K'),
            (1, 'G'), (1, 'S'), (1, 'N'), (1, 'L')
        ]
        self.grid[7][7] = (1, 'R')
        self.grid[7][1] = (1, 'B')
        for c in range(9):
            self.grid[6][c] = (1, 'P')

    def clone(self):
        return copy.deepcopy(self)
    
    def inside(self, row, column):
        return 0 <= row < 9 and 0 <= column < 9
    
    def apply_move(self, move : Move):
        if move.drop:
            self.hands[self.to_move].remove(move.piece)
            row, column = move.to_tile
            self.grid[row][column] = (self.to_move, move.piece)
        else:
            fr, fc = move.from_tile
            tr, tc = move.to_tile
            owner, code = self.grid[fr][fc]

            captured = self.grid[tr][tc]
            if captured is not None:
                cap_owner, cap_code = captured
                if cap_code.startswith('+'):
                    cap_code = cap_code[1:]
                self.hands[self.to_move].append(cap_code)
            self.grid[fr][fc] = None
            if move.promote:
                if not code.startswith('+') and code not in ['G', 'K']:
                    code = '+' + code
            self.grid[tr][tc] = (owner, code)

        self.to_move *= -1

    def is_terminal(self):
        has_sente_king = False
        has_gote_king = False
        for row in range(9):
            for column in range(9):
                p = self.grid[r][c]
                if p is None:
                    continue
                owner, code = p
                if code == 'K':
                    if owner == 1:
                        has_sente_king = True
                    else:
                        has_gote_king = True
        return not (has_sente_king and has_gote_king)
    
class MoveGenerator:
    



