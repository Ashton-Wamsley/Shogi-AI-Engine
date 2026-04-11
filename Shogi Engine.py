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
    def generate_moves(self, board: Board):
        moves = []
        side = board.to_move

        for row in range(9):
            for column in range(9):
                piece = board.grid[row][column]
                if piece is None:
                    continue
                owner, code = piece
                if owner != side:
                    continue
                moves.extend(self._moves_for_piece(board, row, column, owner, code))

        for piece_code in set(board.hands[side]):
            for row in range(9):
                for column in range(9):
                    if board.grid[row][column] is None:
                        moves.append(Move(None, (row, column), piece_code, drop=True))

        return moves
    
    def _moves_for_piece(self, board, row, column, owner, code):
        base = code[1:] if code.startswith('+') else code
        promoted = code.startswith('+')
        moves = []

        forward = -1 if owner == 1 else 1

        def add_step(dr, dc):
            nr, nc = row + dr, column + dc
            if not board.inside(nr, nc):
                return
            target = board.grid[nr][nc]
            if target is None or target[0] != owner:
                promote = self._should_offer_promotion(board, owner, base, row, nr)
                if promote:
                    moves.append(Move((row, column), (nr, nc), code, promote=True))
                moves.append(Move((row, column), (nr, nc), code, promote=False))

        def add_sliding(drs, dcs):
            for dr, dc in zip(drs, dcs):
                nr, nc = row + dr, column + dc
                while board.inside(nr, nc):
                    target = board.grid[nr][nc]
                    if target is None:
                        promote = self._should_offer_promotion(board, owner, base, row, nr)
                        if promote:
                            moves.append(Move((row, column), (nr, nc), code, promote=True))
                        moves.append(Move((row, column), (nr, nc), code, promote=False))
                    else:
                        if target[0] != owner:
                            promote = self._should_offer_promotion(board, owner, base, row, nr)
                            if promote:
                                moves.append(Move((row, column), (nr, nc), code, promote=True))
                            moves.append(Move((row, column), (nr, nc), code, promote=False))
                        break
                    nr += dr
                    nc += dc

        if base == 'P':
            if not promoted:
                add_step(forward, 0)
            else:
                moves.extend(self._gold_moves(board, row, column, owner, code))
        elif base == 'L':
            if not promoted:
                add_sliding([forward]*8, [0]*8)
            else:
                moves.extend(self._gold_moves(board, row, column, owner, code))
        elif base == 'N':
            if not promoted:
                nr = row + 2*forward
                for dc in [-1, 1]:
                    nc = column + dc
                    if board.inside(nr, nc):
                        target = board.grid[nr][nc]
                        if target is None or target[0] != owner:
                            promote = self._should_offer_promotion(board, owner, base, row, nr)
                            if promote:
                                moves.append(Move((row, column), (nr, nc), code, promote=True))
                            moves.append(Move((row, column), (nr, nc), code, promote=False))
            else:
                moves.extend(self._gold_moves(board, row, column, owner, code))
        elif base == 'S':
            if not promoted:
                for dr, dc in [(forward, -1), (forward, 0), (forward, 1),
                               (-forward, -1), (-forward, 1)]:
                    add_step(dr, dc)
            else:
                moves.extend(self._gold_moves(board, row, column, owner, code))
        elif base == 'G':
            moves.extend(self._gold_moves(board, row, column, owner, code))
        elif base == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    add_step(dr, dc)
        elif base == 'B':
            if not promoted:
                add_sliding([1, 1, -1, -1], [1, -1, 1, -1])
            else:
                add_sliding([1, 1, -1, -1], [1, -1, 1, -1])
                for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    add_step(dr, dc)
        elif base == 'R':
            if not promoted:
                add_sliding([1, -1, 0, 0], [0, 0, 1, -1])
            else:
                add_sliding([1, -1, 0, 0], [0, 0, 1, -1])
                for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    add_step(dr, dc)

        return moves

    def _gold_moves(self, board, row, column, owner, code):
        moves = []
        forward = -1 if owner == 1 else 1

        def add_step(dr, dc):
            nr, nc = row + dr, column + dc
            if not board.inside(nr, nc):
                return
            target = board.grid[nr][nc]
            if target is None or target[0] != owner:
                moves.append(Move((row, column), (nr, nc), code, promote=False))

        for dr, dc in [
            (forward, -1), (forward, 0), (forward, 1),
            (0, -1), (0, 1),
            (-forward, 0)
        ]:
            add_step(dr, dc)
        return moves

    def _should_offer_promotion(self, board, owner, base, from_row, to_row):
        if base in ['K', 'G']:
            return False
        if owner == 1:
            return from_row <= 2 or to_row <= 2
        else:
            return from_row >= 6 or to_row >= 6
        
class Evaluator:
    