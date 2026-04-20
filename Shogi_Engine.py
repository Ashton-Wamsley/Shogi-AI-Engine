from dataclasses import dataclass
import math
import copy

@dataclass(frozen=True)

class Move:                         #Moves the AI and player can make
    from_tile : tuple | None
    to_tile : tuple
    piece : str
    promote : bool = False
    drop : bool = False

PIECE_VALUES = {                    
    'P': 1,  'L': 3,  'N': 3,  'S': 4,  'G': 5,
    'B': 8,  'R': 10,
    '+P': 6, '+L': 6, '+N': 6, '+S': 6, '+B': 11, '+R': 13,
    'K': 1000
}

class Board:                        #Initial Board and all actions that change or affect board state
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
        new_b = Board()
        new_b.to_move = self.to_move
        new_b.grid = [row[:] for row in self.grid]
        new_b.hands = {
            1: self.hands[1][:],
            -1: self.hands[-1][:]
        }
        return new_b
    
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

    def find_king(self, owner):
        for row in range(9):
            for column in range(9):
                p = self.grid[row][column]
                if p is None:
                    continue
                o, code = p
                if o == owner and code == 'K':
                    return (row, column)
        return None
    
    def is_square_attacked(self, owner, target_row, target_column, move_gen):
        enemy = -owner
        for row in range(9):
            for column in range(9):
                p = self.grid[row][column]
                if p is None:
                    continue
                o, code = p
                if o != enemy:
                    continue
                moves = move_gen._moves_for_piece(self, row, column, o, code)
                for m in moves:
                    if m.to_tile == (target_row, target_column):
                        return True
        return False
    
    def is_in_check(self, owner, move_gen):
        king_pos = self.find_king(owner)
        if king_pos is None:
            return True
        kr, kc = king_pos
        return self.is_square_attacked(owner, kr, kc, move_gen)

    def is_terminal(self):
        has_sente_king = False
        has_gote_king = False
        for row in range(9):
            for column in range(9):
                p = self.grid[row][column]
                if p is None:
                    continue
                owner, code = p
                if code == 'K':
                    if owner == 1:
                        has_sente_king = True
                    else:
                        has_gote_king = True
        return not (has_sente_king and has_gote_king)
    
class MoveGenerator:                #Legal Moves and piece movement
    def generate_moves(self, board: Board, legal_only=True):
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
            count = board.hands[side].count(piece_code)
            for _ in range(count):
                for row in range(9):
                    for column in range(9):
                        if board.grid[row][column] is None:
                            if self._legal_drop(board, side, piece_code, row, column):
                                moves.append(Move(None, (row, column), piece_code, drop=True))

        if not legal_only:
            return moves
        
        legal_moves = []
        for m in moves:
            new_b = board.clone()
            new_b.apply_move(m)
            if not new_b.is_in_check(side, self):
                legal_moves.append(m)
        return legal_moves
    
    def _legal_drop(self, board: Board, owner, code, row, column):
        if code == 'P':
            for r in range(9):
                p = board.grid[r][column]
                if p is None:
                    continue
                o, c = p
                if o == owner and c == 'P':
                    return False
            if (owner == 1 and row == 0) or (owner == -1 and row == 8):
                return False
        if code == 'L':
            if (owner == 1 and row == 0) or (owner == -1 and row == 8):
                return False
        if code == 'N':
            if (owner == 1 and row <= 1) or (owner == -1 and row >= 7):
                return False    
        if code == 'P':
            temp = board.clone()
            temp.apply_move(Move(None, (row, column), code, drop=True))
            enemy = -owner
            if temp.is_in_check(enemy, self):
                enemy_moves = self.generate_moves(temp)
                if not enemy_moves:
                    return False
        return True
    
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

    def _promotion_status(self, owner, base, from_row, to_row):
        if base in ['K', 'G']:
            return (False, False)
        if owner == 1:
            in_zone_from = from_row <= 2
            in_zone_to = to_row <= 2
        else:
            in_zone_from = from_row >= 6
            in_zone_to = to_row >= 6
        can_promote = in_zone_from or in_zone_to

        must_promote = False
        if base == 'P' or base == 'L':
            if (owner == 1 and to_row == 0) or (owner == -1 and to_row == 8):
                must_promote = True
        if base == 'N':
            if (owner == 1 and to_row <= 1) or (owner == -1 and to_row >= 7):
                must_promote = True

        return (must_promote, can_promote)

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
                if promoted:
                    moves.append(Move((row, column), (nr, nc), code, promote=False))
                else:
                    must, can = self._promotion_status(owner, base, row, nr)
                    if must:
                        moves.append(Move((row, column), (nr, nc), code, promote=True))
                    elif can:
                        moves.append(Move((row, column), (nr, nc), code, promote=True))
                        moves.append(Move((row, column), (nr, nc), code, promote=False))
                    else:
                        moves.append(Move((row, column), (nr, nc), code, promote=False))

        def add_sliding(drs, dcs):
            for dr, dc in zip(drs, dcs):
                nr, nc = row + dr, column + dc
                while board.inside(nr, nc):
                    target = board.grid[nr][nc]
                    if target is None:
                        if promoted:
                            moves.append(Move((row, column), (nr, nc), code, promote=False))
                        else:
                            must, can = self._promotion_status(owner, base, row, nr)
                            if must:
                                moves.append(Move((row, column), (nr, nc), code, promote=True))
                            elif can:
                                moves.append(Move((row, column), (nr, nc), code, promote=True))
                                moves.append(Move((row, column), (nr, nc), code, promote=False))
                            else:
                                moves.append(Move((row, column), (nr, nc), code, promote=False))
                    else:
                        if target[0] != owner:
                            if promoted:
                                moves.append(Move((row, column), (nr, nc), code, promote=False))
                            else:
                                must, can = self._promotion_status(owner, base, row, nr)
                                if must:
                                    moves.append(Move((row, column), (nr, nc), code, promote=True))
                                elif can:
                                    moves.append(Move((row, column), (nr, nc), code, promote=True))
                                    moves.append(Move((row, column), (nr, nc), code, promote=False))
                                else:
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
                add_sliding([forward] * 8, [0] * 8)
            else:
                moves.extend(self._gold_moves(board, row, column, owner, code))
        elif base == 'N':
            if not promoted:
                nr = row + 2 * forward
                for dc in [-1, 1]:
                    nc = column + dc
                    if board.inside(nr, nc):
                        target = board.grid[nr][nc]
                        if target is None or target[0] != owner:
                            if promoted:
                                moves.append(Move((row, column), (nr, nc), code, promote=False))
                            else:
                                must, can = self._promotion_status(owner, base, row, nr)
                                if must:
                                    moves.append(Move((row, column), (nr, nc), code, promote=True))
                                elif can:
                                    moves.append(Move((row, column), (nr, nc), code, promote=True))
                                    moves.append(Move((row, column), (nr, nc), code, promote=False))
                                else:
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
        
class Evaluator:                    #Movement heuristics/evaluation
    def evaluate(self, board: Board):
        score = 0

        for row in range(9):
            for column in range(9):
                piece = board.grid[row][column]
                if piece is None:
                    continue
                owner, code = piece
                val = PIECE_VALUES[code]
                base = code[1:] if code.startswith('+') else code

                if base in ['P', 'L', 'N', 'S']:
                    if owner == 1:
                        advancement = 8 - row
                    else:
                        advancement = row 
                    val += advancement // 2
                if base == 'K':
                    if owner == 1:
                        if row >= 6:
                            val += 4
                        else:
                            val -= 4
                    else:
                        if row <= 2:
                            val += 4
                        else:
                            val -= 4
                score += val if owner == 1 else -val

        for owner in [1, -1]:
            for code in board.hands[owner]:
                val = PIECE_VALUES[code] + 1
                score += val if owner == 1 else -val

        return score
    
class MinimaxEngine:                #AI decision making Minimax/Alpha-Beta Pruning
    def __init__(self, move_gen, evaluator, max_depth=3):
        self.move_gen = move_gen
        self.evaluator = evaluator
        self.max_depth = max_depth

    def choose_move(self, board: Board):
        best_move = None
        alpha, beta = -math.inf, math.inf
        best_score = -math.inf

        moves = self.move_gen.generate_moves(board)
        if not moves:
            return None, self.evaluator.evaluate(board)

        def move_value(m):
            tr, tc = m.to_tile
            target = board.grid[tr][tc]
            capture_val = 0
            if target is not None:
                _, code = target
                capture_val = PIECE_VALUES.get(code, 0)
            promo_bonus = 3 if m.promote else 0
            return capture_val + promo_bonus

        moves.sort(key=move_value, reverse=True)

        for move in moves:
            new_board = board.clone()
            new_board.apply_move(move)
            score = -self._search(new_board, self.max_depth - 1, -beta, -alpha)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
        return best_move, best_score

    def _search(self, board: Board, depth, alpha, beta):
        if depth == 0 or board.is_terminal():
            return self.evaluator.evaluate(board)

        moves = self.move_gen.generate_moves(board)
        if not moves:
            return self.evaluator.evaluate(board)

        def move_value(m):
            fr, fc = m.from_tile if not m.drop else (None, None)
            tr, tc = m.to_tile
            target = board.grid[tr][tc]
            if target is None:
                return 0
            _, code = target
            return PIECE_VALUES.get(code, 0)

        moves.sort(key=move_value, reverse=True)

        for move in moves:
            new_board = board.clone()
            new_board.apply_move(move)
            score = -self._search(new_board, depth - 1, -beta, -alpha)
            if score >= beta:
                return score
            alpha = max(alpha, score)
        return alpha

class Game:                         #Handles games turns and text displayed based on games current state
    def __init__(self, board, move_gen, evaluator, engine):
        self.board = board
        self.move_gen = move_gen
        self.evaluator = evaluator
        self.engine = engine

    def get_game_state(self):
        side = self.board.to_move
        in_check = self.board.is_in_check(side, self.move_gen)
        moves = self.move_gen.generate_moves(self.board)
        if not moves and in_check:
            return "checkmate"
        if not moves and not in_check:
            return "stalemate"
        if in_check:
            return "check"
        return "normal"

    def handle_human_move(self, from_tile, to_tile, promote=False, drop_piece=None):
        moves = self.move_gen.generate_moves(self.board)
        chosen = None
        if drop_piece is not None:
            for m in moves:
                if m.drop and m.piece == drop_piece and m.to_tile == to_tile:
                    chosen = m
                    break
        else:
            for m in moves:
                if not m.drop and m.from_tile == from_tile and m.to_tile == to_tile:
                    if m.promote == promote or (not m.promote and not promote):
                        chosen = m
                        break

        if chosen:
            self.board.apply_move(chosen)

    def handle_ai_move(self):
        if self.board.is_terminal():
            return "Game over (king captured)."
        move, score = self.engine.choose_move(self.board)
        if not move:
            return "AI has no legal moves."

        self.board.apply_move(move)

        if move.drop:
            action = f"AI drops {move.piece} at {move.to_tile}"
        else:
            action = f"AI moves {move.piece} from {move.from_tile} to {move.to_tile}"
            if move.promote:
                action += " and promotes"

        eval_str = f"Evaluation: {score:+.1f}"

        state = self.get_game_state()
        if state == "checkmate":
            status = "Checkmate against you."
        elif state == "stalemate":
            status = "Stalemate."
        elif state == "check":
            status = "You are in check."
        else:
            status = "Position is ongoing."

        return f"{action}. {eval_str}. {status}"
