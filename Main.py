import tkinter as tk
from Shogi_Engine import Board, MoveGenerator, Evaluator, MinimaxEngine, Game
from Shogi_UI import ShogiUI

def main():
    board = Board()
    move_gen = MoveGenerator()
    evaluator = Evaluator()
    engine = MinimaxEngine(move_gen, evaluator, max_depth=2)

    game = Game(board, move_gen, evaluator, engine)

    root = tk.Tk()
    ui = ShogiUI(root, game)
    root.mainloop()


if __name__ == "__main__":
    main()