from piece import Piece


class Board:
    def __init__(self):
        self.board = [[" "] * 8] * 8
    
    def new_board(self):
        self.board[7] = [Piece("white", "Rook", "a1"), Piece("white", "Knight", "b1"), Piece("white", "Bishop", "c1"), Piece("white", "Queen", "d1"), Piece("white", "King", "e1"), Piece("white", "Bishop", "f1"), Piece("white", "Knight", "g1"), Piece("white", "Rook", "h1")]
        self.board[6] = [Piece("white", "Pawn", "a2"), Piece("white", "Pawn", "b2"), Piece("white", "Pawn", "c2"), Piece("white", "Pawn", "d2"), Piece("white", "Pawn", "e2"), Piece("white", "Pawn", "f2"), Piece("white", "Pawn", "g2"), Piece("white", "Pawn", "h2")]
        self.board[1] = [Piece("white", "Pawn", "a7"), Piece("white", "Pawn", "b7"), Piece("white", "Pawn", "c7"), Piece("white", "Pawn", "d7"), Piece("white", "Pawn", "e7"), Piece("white", "Pawn", "f7"), Piece("white", "Pawn", "g7"), Piece("white", "Pawn", "h7")]
        self.board[0] = [Piece("white", "Rook", "a8"), Piece("white", "Knight", "b8"), Piece("white", "Bishop", "c8"), Piece("white", "Queen", "d8"), Piece("white", "King", "e8"), Piece("white", "Bishop", "f8"), Piece("white", "Knight", "g8"), Piece("white", "Rook", "h8")]

    def print_board(self):
        for row in self.board:
            print("|", end="")
            for col in row:
                print(f"{col.token[0]}|" if col != " " else " |", end="")
            print()