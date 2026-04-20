import tkinter as tk
from Shogi_Engine import Game

TILE = 60               #Board Size
BOARD_SIZE = 9

class ShogiUI:          #Shows board, side panel, actions, and pieces
    def __init__(self, root, game: Game):
        self.root = root
        self.game = game
        self.canvas = tk.Canvas(root, width=TILE*BOARD_SIZE, height=TILE*BOARD_SIZE)
        self.canvas.grid(row=0, column=0, rowspan=3)

        self.selected = None
        self.legal_targets = []
        self.drop_mode = False
        self.selected_drop_piece = None

        self.canvas.bind("<Button-1>", self.on_click)

        self.info_label = tk.Label(root, text="Your turn (Sente, bottom).")
        self.info_label.grid(row=0, column=1, sticky="w")

        self.ai_info_label = tk.Label(root, text="AI explanation will appear here.", wraplength=250, justify="left")
        self.ai_info_label.grid(row=1, column=1, sticky="nw")

        self.hand_frame = tk.Frame(root)
        self.hand_frame.grid(row=2, column=1, sticky="nw")
        self.drop_buttons = []

        self.draw_board()
        self.update_hand_display()

    def draw_board(self):
        self.canvas.delete("all")
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                x1, y1 = column*TILE, row*TILE
                x2, y2 = x1+TILE, y1+TILE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#F0D9B5")

                piece = self.game.board.grid[row][column]
                if piece:
                    owner, code = piece
                    text = code if owner == 1 else code.lower()
                    self.canvas.create_text(x1+TILE/2, y1+TILE/2, text=text, font=("Arial", 20))

        if self.selected is not None:
            sr, sc = self.selected
            self.highlight_tile(sr, sc, color="blue")
        for (r, c) in self.legal_targets:
            self.highlight_tile(r, c, color="green")

        sente_hand = " ".join(self.game.board.hands[1])
        gote_hand = " ".join(self.game.board.hands[-1])
        self.root.title(f"Shogi AI | Sente hand: [{sente_hand}]  Gote hand: [{gote_hand}]")

    def update_hand_display(self):
        for widget in self.hand_frame.winfo_children():
            widget.destroy()
        self.drop_buttons = []

        tk.Label(self.hand_frame, text="Your hand:").grid(row=0, column=0, sticky="w")
        col = 1
        seen = {}
        for piece in self.game.board.hands[1]:
            seen[piece] = seen.get(piece, 0) + 1
        for code, count in seen.items():
            text = f"{code} x{count}"
            btn = tk.Button(self.hand_frame, text=text,
                            command=lambda c=code: self.start_drop(c))
            btn.grid(row=0, column=col, padx=2, pady=2)
            self.drop_buttons.append(btn)
            col += 1

        tk.Label(self.hand_frame, text="AI hand:").grid(row=1, column=0, sticky="w")
        col = 1
        seen_ai = {}
        for piece in self.game.board.hands[-1]:
            seen_ai[piece] = seen_ai.get(piece, 0) + 1
        for code, count in seen_ai.items():
            text = f"{code} x{count}"
            lbl = tk.Label(self.hand_frame, text=text)
            lbl.grid(row=1, column=col, padx=2, pady=2)
            col += 1

    def update_hand_buttons(self):
        for b in self.drop_buttons:
            b.destroy()
        self.drop_buttons = []

        tk.Label(self.hand_frame, text="Your hand:").grid(row=0, column=0, sticky="w")
        col = 1
        seen = {}
        for piece in self.game.board.hands[1]:
            seen[piece] = seen.get(piece, 0) + 1
        for code, count in seen.items():
            text = f"{code} x{count}"
            btn = tk.Button(self.hand_frame, text=text,
                            command=lambda c=code: self.start_drop(c))
            btn.grid(row=0, column=col, padx=2)
            self.drop_buttons.append(btn)
            col += 1

    def start_drop(self, piece_code):
        if self.game.board.to_move != 1:
            return
        self.drop_mode = True
        self.selected_drop_piece = piece_code
        self.selected = None
        self.legal_targets = []
        self.info_label.config(text=f"Dropping {piece_code}: click a square.")
        self.draw_board()

    def on_click(self, event):
        if self.game.board.to_move != 1:
            return

        row = event.y // TILE
        column = event.x // TILE

        if not (0 <= row < 9 and 0 <= column < 9):
            return
        
        if self.drop_mode:
            self.handle_drop_click(row, column)
            return

        if self.selected is None:
            piece = self.game.board.grid[row][column]
            if piece is None:
                return
            owner, code = piece
            if owner != 1:
                return
            self.selected = (row, column)
            self.legal_targets = self.get_legal_targets(row, column)
            self.draw_board()
        else:
            from_tile = self.selected
            to_tile = (row, column)
            if to_tile not in self.legal_targets:
                self.selected = None
                self.legal_targets = []
                self.draw_board()
                return
            
            promote = False
            if self.should_offer_promotion(from_tile, to_tile):
                promote = self.ask_promotion()

            self.selected = None
            self.legal_targets = []
            self.draw_board()

            self.game.handle_human_move(from_tile, to_tile, promote=promote)
            self.draw_board()
            self.update_hand_display()

            state = self.game.get_game_state()
            if state == "checkmate":
                self.info_label.config(text="You delivered checkmate! Game over.")
                return
            elif state == "stalemate":
                self.info_label.config(text="Stalemate. Game over.")
                return
            elif state == "check":
                self.info_label.config(text="AI is in check. AI thinking...")
            else:
                self.info_label.config(text="AI thinking...")

            if self.game.board.to_move == -1 and not self.game.board.is_terminal():
                self.root.after(200, self.ai_move)
            else:
                self.info_label.config(text="Your turn.")

    def handle_drop_click(self, row, column):
        if self.game.board.grid[row][column] is not None:
            return
        to_tile = (row, column)
        self.game.handle_human_move(None, to_tile, drop_piece=self.selected_drop_piece)
        self.drop_mode = False
        self.selected_drop_piece = None
        self.draw_board()
        self.update_hand_display()

        state = self.game.get_game_state()
        if state == "checkmate":
            self.info_label.config(text="You delivered checkmate! Game over.")
            return
        elif state == "stalemate":
            self.info_label.config(text="Stalemate. Game over.")
            return
        elif state == "check":
            self.info_label.config(text="AI is in check. AI thinking...")
        else:
            self.info_label.config(text="AI thinking...")

        if self.game.board.to_move == -1 and not self.game.board.is_terminal():
            self.root.after(200, self.ai_move)

    def get_legal_targets(self, row, column):
        moves = self.game.move_gen.generate_moves(self.game.board)
        targets = []
        for m in moves:
            if not m.drop and m.from_tile == (row, column):
                targets.append(m.to_tile)
        return targets
    
    def should_offer_promotion(self, from_tile, to_tile):
        fr, fc = from_tile
        tr, tc = to_tile
        piece = self.game.board.grid[fr][fc]
        if piece is None:
            return False
        owner, code = piece
        base = code[1:] if code.startswith('+') else code
        if base in ['K', 'G']:
            return False
        if owner == 1:
            in_zone_from = fr <= 2
            in_zone_to = tr <= 2
        else:
            in_zone_from = fr >= 6
            in_zone_to = tr >= 6
        return in_zone_from or in_zone_to
    
    def ask_promotion(self):
        win = tk.Toplevel(self.root)
        win.title("Promote?")
        label = tk.Label(win, text="Promote this piece?")
        label.pack(padx=10, pady=10)

        result = {"promote": False}

        def yes():
            result["promote"] = True
            win.destroy()

        def no():
            result["promote"] = False
            win.destroy()

        tk.Button(win, text="Yes", command=yes).pack(side="left", padx=10, pady=10)
        tk.Button(win, text="No", command=no).pack(side="right", padx=10, pady=10)

        win.grab_set()
        self.root.wait_window(win)
        return result["promote"]
    
    def highlight_tile(self, row, column, color="red"):
        x1, y1 = column*TILE, row*TILE
        x2, y2 = x1+TILE, y1+TILE
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)

    def ai_move(self):
        explanation = self.game.handle_ai_move()
        self.draw_board()
        self.update_hand_display()

        state = self.game.get_game_state()
        if state == "checkmate":
            self.info_label.config(text="Checkmate. Game over.")
        elif state == "stalemate":
            self.info_label.config(text="Stalemate. Game over.")
        elif state == "check":
            self.info_label.config(text="You are in check. Your turn.")
        else:
            self.info_label.config(text="Your turn.")

        self.ai_info_label.config(text=explanation)
