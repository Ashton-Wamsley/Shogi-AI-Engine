import tkinter as tk
from Shogi_Engine import Game

TILE = 60
BOARD_SIZE = 9

class ShogiUI:
    def __init__(self, root, game: Game):
        self.root = root
        self.game = game
        self.canvas = tk.Canvas(root, width=TILE*BOARD_SIZE, height=TILE*BOARD_SIZE)
        self.canvas.pack()

        self.selected = None
        self.canvas.bind("<Button-1>", self.on_click)

        self.info_label = tk.Label(root, text="Your turn (Sente, bottom).")
        self.info_label.pack()

        self.draw_board()

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

        sente_hand = " ".join(self.game.board.hands[1])
        gote_hand = " ".join(self.game.board.hands[-1])
        self.root.title(f"Shogi AI | Sente hand: [{sente_hand}]  Gote hand: [{gote_hand}]")

    def on_click(self, event):
        if self.game.board.to_move != 1:
            return

        row = event.y // TILE
        column = event.x // TILE

        if not (0 <= row < 9 and 0 <= column < 9):
            return

        if self.selected is None:
            piece = self.game.board.grid[row][column]
            if piece is None:
                return
            owner, code = piece
            if owner != 1:
                return
            self.selected = (row, column)
            self.highlight_square(row, column)
        else:
            from_tile = self.selected
            to_tile = (row, column)
            self.selected = None
            self.draw_board()

            self.game.handle_human_move(from_tile, to_tile)
            self.draw_board()

            if self.game.board.to_move == -1 and not self.game.board.is_terminal():
                self.info_label.config(text="AI thinking...")
                self.root.after(200, self.ai_move)
            else:
                self.info_label.config(text="Your turn.")
    
    def highlight_tile(self, row, column):
        x1, y1 = column*TILE, row*TILE
        x2, y2 = x1+TILE, y1+TILE
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3)

    def ai_move(self):
        self.game.handle_ai_move()
        self.draw_board()
        if self.game.board.is_terminal():
            self.info_label.config(text="Game over.")
        else:
            self.info_label.config(text="Your turn.")
