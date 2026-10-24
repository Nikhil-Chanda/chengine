
import chess
import time
from dataclasses import dataclass

# ============================================================
# MyChessAI
# A basic chess engine using python-chess for legal move rules.
# Search: iterative deepening, negamax, alpha-beta, quiescence.
# ============================================================

ENGINE_NAME = "MyChessAI"
MAX_DEPTH = 64
MATE_SCORE = 100_000
INF = 1_000_000
TIME_LIMIT = 5.0  # seconds per move; adjust as needed

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


@dataclass
class SearchResult:
    move: chess.Move | None
    score: int
    depth: int
    nodes: int


class SearchTimeout(Exception):
    pass


class MyChessAI:
    def __init__(self):
        self.nodes = 0
        self.deadline = 0.0
        self.tt = {}
        self.killers = {}
        self.history = {}
        self.root_best_move = None

    # --------------------------------------------------------
    # Evaluation: positive means good for White.
    # --------------------------------------------------------

    def evaluate_white(self, board):
        if board.is_checkmate():
            return -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE

        if board.is_game_over(claim_draw=True):
            return 0

        score = 0

        for color in (chess.WHITE, chess.BLACK):
            sign = 1 if color == chess.WHITE else -1

            for piece_type, value in PIECE_VALUES.items():
                squares = board.pieces(piece_type, color)
                score += sign * len(squares) * value

                # Simple positional bonuses.
                if piece_type != chess.KING:
                    for square in squares:
                        file_index = chess.square_file(square)
                        rank_index = chess.square_rank(square)

                        # Encourage central activity.
                        center_distance = (
                            abs(3.5 - file_index)
                            + abs(3.5 - rank_index)
                        )
                        score += sign * int(
                            max(0, 7 - center_distance * 2)
                            * (2 if piece_type in (
                                chess.KNIGHT, chess.BISHOP
                            ) else 1)
                        )

                        # Encourage pawns to advance.
                        if piece_type == chess.PAWN:
                            advance = (
                                rank_index if color == chess.WHITE
                                else 7 - rank_index
                            )
                            score += sign * advance * 5

            # Small bonus for castling rights.
            if board.has_kingside_castling_rights(color):
                score += sign * 15
            if board.has_queenside_castling_rights(color):
                score += sign * 10

        return score

    def evaluate(self, board):
        score = self.evaluate_white(board)
        return score if board.turn == chess.WHITE else -score

    # --------------------------------------------------------
    # Search utilities
    # --------------------------------------------------------

    def check_time(self):
        if time.monotonic() >= self.deadline:
            raise SearchTimeout()

    def position_key(self, board):
        # Include repetition-relevant history in the key so
        # search does not reuse scores from incompatible paths.
        return (
            board.fen(),
            tuple(board.move_stack[-8:]),
        )

    def move_order_score(self, board, move, tt_move=None, ply=0):
        if tt_move is not None and move == tt_move:
            return 10_000_000

        score = 0

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)

            if board.is_en_passant(move):
                victim_value = PIECE_VALUES[chess.PAWN]
            else:
                victim_value = (
                    PIECE_VALUES[victim.piece_type]
                    if victim else 0
                )

            attacker_value = (
                PIECE_VALUES[attacker.piece_type]
                if attacker else 0
            )

            score += 1_000_000 + victim_value * 10 - attacker_value

        if move.promotion:
            score += 800_000 + PIECE_VALUES.get(move.promotion, 0)

        killer_moves = self.killers.get(ply, [])
        if move in killer_moves:
            score += 500_000 - killer_moves.index(move) * 1000

        score += self.history.get(
            (board.turn, move.from_square, move.to_square), 0
        )

        return score

    def ordered_moves(self, board, tt_move=None, ply=0, captures_only=False):
        moves = list(board.legal_moves)

        if captures_only:
            moves = [
                move for move in moves
                if board.is_capture(move) or move.promotion
            ]

        moves.sort(
            key=lambda move: self.move_order_score(
                board, move, tt_move, ply
            ),
            reverse=True,
        )
        return moves

    # --------------------------------------------------------
    # Quiescence search: continue tactical captures at leaves.
    # --------------------------------------------------------

    def quiescence(self, board, alpha, beta, ply=0):
        self.nodes += 1

        if self.nodes % 1024 == 0:
            self.check_time()

        if board.is_checkmate():
            return -MATE_SCORE + ply

        if board.is_game_over(claim_draw=True):
            return 0

        in_check = board.is_check()

        if not in_check:
            stand_pat = self.evaluate(board)

            if stand_pat >= beta:
                return beta

            alpha = max(alpha, stand_pat)

        # When in check, all legal evasions must be searched.
        if in_check:
            moves = list(board.legal_moves)
            moves.sort(
                key=lambda move: self.move_order_score(
                    board, move, ply=ply
                ),
                reverse=True,
            )
        else:
            moves = self.ordered_moves(
                board, ply=ply, captures_only=True
            )

        for move in moves:
            self.check_time()
            board.push(move)

            try:
                score = -self.quiescence(
                    board, -beta, -alpha, ply + 1
                )
            finally:
                board.pop()

            if score >= beta:
                return beta

            alpha = max(alpha, score)

        return alpha

    # --------------------------------------------------------
    # Negamax with alpha-beta pruning and transposition table.
    # --------------------------------------------------------

    def negamax(self, board, depth, alpha, beta, ply=0):
        self.nodes += 1

        if self.nodes % 1024 == 0:
            self.check_time()

        if board.is_checkmate():
            return -MATE_SCORE + ply, None

        if board.is_game_over(claim_draw=True):
            return 0, None

        original_alpha = alpha
        key = self.position_key(board)
        tt_entry = self.tt.get(key)
        tt_move = None

        if tt_entry is not None:
            tt_depth, tt_score, tt_flag, tt_move = tt_entry

            if tt_depth >= depth:
                if tt_flag == "EXACT":
                    return tt_score, tt_move
                elif tt_flag == "LOWER":
                    alpha = max(alpha, tt_score)
                elif tt_flag == "UPPER":
                    beta = min(beta, tt_score)

                if alpha >= beta:
                    return tt_score, tt_move

        if depth <= 0:
            return self.quiescence(board, alpha, beta, ply), None

        best_score = -INF
        best_move = None

        moves = self.ordered_moves(board, tt_move, ply)

        for move in moves:
            self.check_time()
            board.push(move)

            try:
                score, _ = self.negamax(
                    board, depth - 1, -beta, -alpha, ply + 1
                )
                score = -score
            finally:
                board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            # Store quiet moves that cause cutoffs as killer moves.
            if alpha >= beta:
                if not board.is_capture(move) and not move.promotion:
                    killers = self.killers.setdefault(ply, [])
                    if move not in killers:
                        killers.insert(0, move)
                        del killers[2:]

                    hist_key = (
                        board.turn, move.from_square, move.to_square
                    )
                    self.history[hist_key] = min(
                        100_000,
                        self.history.get(hist_key, 0) + depth * depth,
                    )
                break

        if best_score <= original_alpha:
            flag = "UPPER"
        elif best_score >= beta:
            flag = "LOWER"
        else:
            flag = "EXACT"

        self.tt[key] = (depth, best_score, flag, best_move)

        return best_score, best_move

    # --------------------------------------------------------
    # Iterative deepening: keep the last completed result.
    # --------------------------------------------------------

    def choose_move(self, board, max_depth=MAX_DEPTH, time_limit=TIME_LIMIT):
        if board.is_game_over(claim_draw=True):
            return SearchResult(None, 0, 0, 0)

        # Work on a private copy so searching cannot alter the
        # caller's board or its move history.
        search_board = board.copy(stack=True)
        original_fen = search_board.fen()
        original_stack = tuple(search_board.move_stack)

        self.nodes = 0
        self.deadline = time.monotonic() + max(0.01, time_limit)
        self.tt.clear()
        self.killers.clear()
        self.history.clear()

        legal_moves = list(search_board.legal_moves)
        if not legal_moves:
            return SearchResult(None, 0, 0, self.nodes)

        # Always have a legal fallback before beginning search.
        best_move = legal_moves[0]
        best_score = self.evaluate(search_board)
        completed_depth = 0

        try:
            for depth in range(1, max_depth + 1):
                self.check_time()

                alpha = -INF
                beta = INF
                iteration_best = None
                iteration_score = -INF

                moves = self.ordered_moves(
                    search_board, best_move, ply=0
                )

                for move in moves:
                    self.check_time()
                    search_board.push(move)

                    try:
                        score, _ = self.negamax(
                            search_board,
                            depth - 1,
                            -beta,
                            -alpha,
                            ply=1,
                        )
                        score = -score
                    finally:
                        search_board.pop()

                    if score > iteration_score:
                        iteration_score = score
                        iteration_best = move

                    alpha = max(alpha, score)

                if iteration_best is not None:
                    best_move = iteration_best
                    best_score = iteration_score
                    completed_depth = depth

                print(
                    f"depth={depth} score={best_score} "
                    f"nodes={self.nodes} move={best_move}",
                    flush=True,
                )

        except SearchTimeout:
            pass

        # Verify the private search board has been restored.
        if (
            search_board.fen() != original_fen
            or tuple(search_board.move_stack) != original_stack
        ):
            raise RuntimeError(
                "Internal error: search failed to restore its board."
            )

        # Validate the chosen move against the actual current position.
        if best_move not in board.legal_moves:
            raise RuntimeError(
                f"AI selected illegal move {best_move}; "
                f"position={board.fen()}"
            )

        return SearchResult(
            best_move, best_score, completed_depth, self.nodes
        )


# ============================================================
# Command-line interface
# ============================================================

def print_board(board):
    print()
    print(board)
    print("FEN:", board.fen())
    print()


def main():
    board = chess.Board()
    ai = MyChessAI()

    print(f"{ENGINE_NAME} — enter moves in UCI format, e.g. e2e4.")
    print("Type 'quit' to exit.")
    print("You play White; the AI plays Black.")

    while not board.is_game_over(claim_draw=True):
        print_board(board)

        if board.turn == chess.WHITE:
            try:
                user_input = input("Your move: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                return

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                return

            try:
                move = chess.Move.from_uci(user_input)
            except ValueError:
                print("Invalid UCI format. Example: e2e4 or e7e8q")
                continue

            if move not in board.legal_moves:
                print("Illegal move. Try again.")
                continue

            board.push(move)

        else:
            print("AI is thinking...")

            result = ai.choose_move(
                board,
                max_depth=MAX_DEPTH,
                time_limit=TIME_LIMIT,
            )

            move = result.move

            if move is None:
                break

            # Defensive check immediately before applying the move.
            if move not in board.legal_moves:
                raise RuntimeError(
                    f"Illegal AI move: {move}\n"
                    f"Current FEN: {board.fen()}"
                )

            print(
                f"Completed depth: {result.depth}; "
                f"searched nodes: {result.nodes}"
            )
            print(f"AI plays {move}; score={result.score}")

            board.push(move)

    print_board(board)
    print("Game over:", board.result())
    print(board.outcome(claim_draw=True))


if __name__ == "__main__":
    main()
