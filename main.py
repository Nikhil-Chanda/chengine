from board import Board


def init_board():
    board = Board()
    board.new_board()
    board.print_board()


def main():
    init_board()


if __name__ == "__main__":
    main()