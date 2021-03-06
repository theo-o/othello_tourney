import Othello_Core as core
import random
import math

class Strategy(core.OthelloCore):

    def __init__(self):
        self.scores = {}

    def is_valid(self, move):
        """Is move a square on the board?"""
        return isinstance(move, int) and move in self.squares()


    def opponent(self, player):
        """Get player's opponent piece."""
        return core.BLACK if player is core.WHITE else core.WHITE


    def find_bracket(self, square, player, board, direction):
        """
        Find a square that forms a bracket with `square` for `player` in the given
        `direction`.  Returns None if no such square exists.
        """
        bracket = square + direction
        if board[bracket] == player:
            return None
        opp = self.opponent(player)
        while board[bracket] == opp:
            bracket += direction
        return None if board[bracket] in (core.OUTER, core.EMPTY) else bracket


    def is_legal(self, move, player, board):
        """Is this a legal move for the player?"""
        hasbracket = lambda direction: self.find_bracket(move, player, board, direction)
        return board[move] == core.EMPTY and any(map(hasbracket, core.DIRECTIONS))


    ### Making moves

    # When the player makes a move, we need to update the board and flip all the
    # bracketed pieces.

    def make_move(self, move, player, board):
        """Update the board to reflect the move by the specified player."""
        if not self.is_legal(move, player, board):
            raise self.IllegalMoveError(player, move, board)
        board[move] = player
        for d in core.DIRECTIONS:
            self.make_flips(move, player, board, d)
        return board


    def make_flips(self, move, player, board, direction):
        """Flip pieces in the given direction as a result of the move by player."""
        bracket = self.find_bracket(move, player, board, direction)
        if not bracket:
            return
        square = move + direction
        while square != bracket:
            board[square] = player
            square += direction


    ### Monitoring players

    class IllegalMoveError(Exception):
        def __init__(self, player, move, board):
            self.player = player
            self.move = move
            self.board = board

        def __str__(self):
            return '%s cannot move to square %d' % (core.PLAYERS[self.player], self.move)


    def legal_moves(self, player, board):
        """Get a list of all legal moves for player."""
        return [sq for sq in self.squares() if self.is_legal(sq, player, board)]


    def any_legal_move(self, player, board):
        """Can player make any moves?"""
        return any(self.is_legal(sq, player, board) for sq in self.squares())


    def next_player(self,board, prev_player):
        """Which player should move next?  Returns None if no legal moves exist."""
        opp = self.opponent(prev_player)
        if self.any_legal_move(opp, board):
            return opp
        elif self.any_legal_move(prev_player, board):
            return prev_player
        return None


    def score(self,player, board):
        """Compute player's score (number of player's pieces minus opponent's)."""
        mine, theirs = 0, 0
        opp = self.opponent(player)
        for sq in self.squares():
            piece = board[sq]
            if piece == player:
                mine += 1
            elif piece == opp:
                theirs += 1
        return mine - theirs

    def game_over(self, player, board):
        return self.legal_moves(player, board) + \
            self.legal_moves(self.opponent(player), board) == []

    def no_moves(self, player, board):
        return self.legal_moves(player, board) == []

    ################ strategies #################
    def human(self, player, board):
        print(self.print_board(board))
        move = input("Move for player %s? (11-88): " % player)
        move = int(move)
        return move

    def random(self, player, board):
        print(self.print_board(board))
        return random.choice(self.legal_moves(player, board))

    SQUARE_WEIGHTS = [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 120, -20, 20, 5, 5, 20, -20, 120, 0,
        0, -20, -40, -5, -5, -5, -5, -40, -20, 0,
        0, 20, -5, 15, 3, 3, 15, -5, 20, 0,
        0, 5, -5, 3, 3, 3, 3, -5, 5, 0,
        0, 5, -5, 3, 3, 3, 3, -5, 5, 0,
        0, 20, -5, 15, 3, 3, 15, -5, 20, 0,
        0, -20, -40, -5, -5, -5, -5, -40, -20, 0,
        0, 120, -20, 20, 5, 5, 20, -20, 120, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    ]

    def weighted_score(self, player, board):
        """
        Compute the difference between the sum of the weights of player's
        squares and the sum of the weights of opponent's squares.
        """
        opp = self.opponent(player)
        total = 0
        for sq in self.squares():
            if board[sq] == player:
                total += self.SQUARE_WEIGHTS[sq]
            elif board[sq] == opp:
                total -= self.SQUARE_WEIGHTS[sq]
        return total

    def minimax(self, player, board, depth, evaluate):
        """
        Find the best legal move for player, searching to the specified depth.
        Returns a tuple (move, min_score), where min_score is the guaranteed minimum
        score achievable for player if the move is made.
        """

        # We define the value of a board to be the opposite of its value to our
        # opponent, computed by recursively applying `minimax` for our opponent.
        def value(board):
            return -self.minimax(self.opponent(player), board, depth - 1, evaluate)[0]

        # When depth is zero, don't examine possible moves--just determine the value
        # of this board to the player.
        if depth == 0:
            return evaluate(player, board), None

        # We want to evaluate all the legal moves by considering their implications
        # `depth` turns in advance.  First, find all the legal moves.
        moves = self.legal_moves(player, board)

        # If player has no legal moves, then either:
        if not moves:
            # either the game is over, so the best achievable score is victory or defeat;
            if not self.any_legal_move(self.opponent(player), board):
                return self.final_value(player, board), None
            # or we have to pass this turn, so just find the value of this board.
            return value(board), None

        # When there are multiple legal moves available, choose the best one by
        # maximizing the value of the resulting boards.
        return max((value(self.make_move(m, player, list(board))), m) for m in moves)

    # Values for endgame boards are big constants.
    MAX_VALUE = sum(map(abs, SQUARE_WEIGHTS))
    MIN_VALUE = -MAX_VALUE

    def final_value(self, player, board):
        """The game is over--find the value of this board to player."""
        diff = self.score(player, board)
        if diff < 0:
            return self.MIN_VALUE
        elif diff > 0:
            return self.MAX_VALUE
        return diff

    def minimax_searcher(self, depth, evaluate):
        """
        Construct a strategy that uses `minimax` with the specified leaf board
        evaluation function.
        """

        def strategy(player, board):
            return self.minimax(player, board, depth, evaluate)[1]

        return strategy

    def alphabeta(self, player, board, alpha, beta, depth, evaluate):
        """
        Find the best legal move for player, searching to the specified depth.  Like
        minimax, but uses the bounds alpha and beta to prune branches.
        """
        if depth == 0:
            return evaluate(player, board), None

        def value(board, alpha, beta):
            # Like in `minimax`, the value of a board is the opposite of its value
            # to the opponent.  We pass in `-beta` and `-alpha` as the alpha and
            # beta values, respectively, for the opponent, since `alpha` represents
            # the best score we know we can achieve and is therefore the worst score
            # achievable by the opponent.  Similarly, `beta` is the worst score that
            # our opponent can hold us to, so it is the best score that they can
            # achieve.
            return -self.alphabeta(self.opponent(player), board, -beta, -alpha, depth - 1, evaluate)[0]

        moves = self.legal_moves(player, board)
        moves.sort(key = lambda x: self.SQUARE_WEIGHTS[x], reverse=True)

        if not moves:
            if not self.any_legal_move(self.opponent(player), board):
                return self.final_value(player, board), None
            return value(board, alpha, beta), None

        best_move = moves[0]
        for move in moves:
            if alpha >= beta:
                # If one of the legal moves leads to a better score than beta, then
                # the opponent will avoid this branch, so we can quit looking.
                break
            val = value(self.make_move(move, player, list(board)), alpha, beta)
            if val > alpha:
                # If one of the moves leads to a better score than the current best
                # achievable score, then replace it with this one.
                alpha = val
                best_move = move
        return alpha, best_move


    def alphabeta_searcher(self,depth, evaluate):
        def strategy(player, board):
            return self.alphabeta(player, board, self.MIN_VALUE, self.MAX_VALUE, depth, evaluate)[1]

        return strategy

    def lookup_board_score(self, board):
        board_s = "".join(board)
        (w,l,s) = self.scores[board_s] if board_s in self.scores else (0,0,math.inf)
        return s+random.random()/10000 +1/math.sqrt(w+l)\
            if board_s in self.scores else math.inf

    def random_playout(self, player, board):
        board_s = "".join(board)
        moves = self.legal_moves(player, board)
        if moves:
            #moves.sort(key = lambda x: self.lookup_board_score(self.make_move(x, player, list(board))),
            #           reverse = True)
            #move = moves[0]
            move = random.choice(moves)
            return -self.random_playout(self.opponent(player), self.make_move(move, player, list(board)))
        elif self.legal_moves(self.opponent(player), board):
            return -self.random_playout(self.opponent(player), board)
        else:
            #print(self.print_board(board))
            #print(player, self.score(player, board))
            return self.score(player, board)

    def update_board_score(self, board, result):
        board_s = "".join(board)
        if board_s in self.scores:
            (w,l,s) = self.scores[board_s]
        else:
            (w,l,s) = (0,0,math.inf)
        if result > 0:
            self.scores[board_s] = (w+1, l, (w+1)/(w+l+1))
        else:
            self.scores[board_s] = (w, l+1, w/(w+l+1))

    def tree_playout(self, player, board):
        moves = self.legal_moves(player, board)
        if moves:
            moves.sort(key = lambda x: self.lookup_board_score(self.make_move(x, player, list(board))),
                       reverse = True)
            move = moves[0]
            result = -self.tree_playout(self.opponent(player), self.make_move(move, player, list(board)))
            self.update_board_score(board, result)
            return result

        elif self.legal_moves(self.opponent(player), board):
            result =  -self.tree_playout(self.opponent(player), board)
            self.update_board_score(board, result)
            return result

        else:
            result =  self.score(player, board)
            self.update_board_score(board, result)
            return result

    def random_score(self, player, board, num):
        board_s = "".join(board)
        if board_s in self.scores:
            value, wins, losses = self.scores[board_s]
        else:
            wins, losses = (0,0)
        for i in range(num):
            score = self.random_playout(player, board)
            if score>0:
                wins += 1
            else:
                losses += 1
        self.scores[board_s] = (wins, losses,  wins / (wins+ losses))
        return wins / (wins + losses), wins, wins+losses

    def monte_carlo1(self, player, board):
        num = 10
        scores = [(self.random_score(player, self.make_move(m, player, list(board)), num), m)
                  for m in self.legal_moves(player, board)]
        for (s, m) in scores:
            print ("%i: %3.2f = %i/%i" % (m,s[0], s[1], s[2]))
        return sorted(scores, reverse = True)[0][1]

    def monte_carlo2(self, player, board):
        self.scores={}
        num = 10
        for i in range(num):
            self.tree_playout(player, board)
        moves = self.legal_moves(player, board)
        moves.sort(key = lambda x: self.lookup_board_score(self.make_move(x, player, list(board))),
                   reverse = True)
        move = moves[0]
        for m in moves:
            s = self.scores["".join(self.make_move(m, player, list(board)))]
            print ("%i: %3.2f = %i/%i" % (m,s[2], s[0], s[0]+s[1]))
        return move

    def random_strategy(self, board, player):
        return random.choice(self.legal_moves(player, board))

    def parallel_random_strategy(self, board, player, best_move, still_running):
        best_move.value = random.choice(self.legal_moves(player, board))

    def forfeit_strategy(self, board, player):
        return -39

    def best_strategy(self, board, player, best_move, still_running):
        depth = 4
        evaluate = self.weighted_score
        best_move.value = self.random_strategy(board, player)
        #best_move.value = self.forfeit_strategy(board, player)
        #while(True):
            #best_move.value = self.alphabeta(player, board, self.MIN_VALUE, self.MAX_VALUE, depth, evaluate)[1]
            #depth += 1
