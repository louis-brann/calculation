#!/usr/bin/env python
import random                            # for shuffling
from copy import deepcopy                # for static board states
from collections import namedtuple       # for simple classes
from queue import PriorityQueue          # for BFSSolver board ordering
from dataclasses import dataclass, field # for prioritizing boards
from math import inf                     # for max threshold

"""
Calculation Player

This is a program to try to play Calculation. 

Setup:  A, 2, 3, 4 as base cards ;;; 4 slots for waste piles
Goal:   Build on each base card in steps of that base card (A by 1s, 2 by 2s,
        3 by 3s, 4 by 4s) with wrapping, until each stack gets to K

Rules:  Draw one card at a time. If you cannot play on one of the foundations,
        you must play it one of the four waste heaps. You can only move a card
        from a waste heap to one of the foundations, not to another waste heap.
"""

class CalculationBoard:
    """
    A CalculationBoard keeps the state of a calculation game.
    There are 4 foundations, 4 waste piles, and a deck of cards to draw from.
    The calculation board is a snapshot of where all the cards are.
    """

    NUM_WASTES = NUM_FOUNDATIONS = NUM_SUITS = 4

    class PileTypes:
        FOUNDATION = "F"
        WASTE = "W"
        DECK = "D"

    class CardLocation:
        def __init__(self, pile_type=None, pile_index=None):
            self.pile_type = pile_type
            self.pile_index = pile_index

        def __repr__(self):
            return "{type}{index}".format(type=self.pile_type, index=self.pile_index)

    class Move:
        def __init__(self, src=None, dest=None):
            self.src = src
            self.dest = dest

        def __repr__(self):
            return "({src} -> {dest})".format(src=self.src, dest=self.dest)

    class InvalidMoveException(Exception):
        pass

    # TODO: do we need to pass in cards_per_suit and deck?
    # they were relics of tree-searching, but that may not be necessary.
    def __init__(self, cards_per_suit=13, deck=None):
        self.cards_per_suit = cards_per_suit
        self.foundations = [[i] for i in range(1, 1+CalculationBoard.NUM_FOUNDATIONS)]
        self.wastes = [[] for i in range(CalculationBoard.NUM_WASTES)]

        self.card_values = list(range(1, cards_per_suit)) + [0]
        self.winning = [[(base*i)%cards_per_suit for i in self.card_values] for base in range(1, 1+CalculationBoard.NUM_FOUNDATIONS)]

        self.deck = deck if deck else CalculationBoard.generate_random_deck(cards_per_suit)

        self.moves = []

    def __eq__(self, other):
        return self.foundations == other.foundations and self.wastes == other.wastes and self.deck == other.deck

    def __repr__(self):
        return str([self.foundations, self.wastes, self.deck])

    # So it can be used in sets
    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def generate_random_deck(cards_per_suit):
        suit = list(range(1, cards_per_suit)) + [0]
        # unshuffled deck (suits in order)
        deck =  suit * CalculationBoard.NUM_SUITS
        # foundation cards start out in foundation piles, not deck
        deck = deck[CalculationBoard.NUM_FOUNDATIONS:]
        random.shuffle(deck)
        return deck

    def is_winning(self):
        return self.foundations == self.winning

    def get_possible_moves(self):
        moves_from_waste_piles = self.get_possible_moves_from_waste()
        moves_from_deck = self.get_possible_moves_from_deck()
        return moves_from_waste_piles + moves_from_deck

    def can_play_on_foundation(self, card_to_play, foundation_index):
        foundation = self.foundations[foundation_index]

        # If we've already reached king, that pile's already done. Can't play any more
        top_card = foundation[-1]
        if top_card == 0:
            return False

        base_card = foundation[0]
        expected_next = (top_card + base_card) % self.cards_per_suit
        return card_to_play == expected_next

    def get_possible_moves_from_waste(self):
        """
        Checks if any of the cards in the waste piles are playable onto the
        foundations. Returns a list of Moves.
        """
        possible_moves = []
        for i in range(len(self.wastes)):
            waste = self.wastes[i]
            if not waste:
                continue

            src = CalculationBoard.CardLocation(pile_type=CalculationBoard.PileTypes.WASTE, pile_index=i)
            src_card = waste[-1]
            for j in range(len(self.foundations)):
                dest = CalculationBoard.CardLocation(pile_type=CalculationBoard.PileTypes.FOUNDATION, pile_index=j)
                if self.can_play_on_foundation(src_card, j):
                    possible_moves.append(CalculationBoard.Move(src=src, dest=dest))

        return possible_moves

    def get_possible_moves_from_deck(self):
        possible_moves = []
        if not self.deck:
            return possible_moves

        src_card = self.deck[-1]
        src = CalculationBoard.CardLocation(pile_type=CalculationBoard.PileTypes.DECK, pile_index=0)

        # deck to foundations
        for j in range(len(self.foundations)):
            dest = CalculationBoard.CardLocation(pile_type=CalculationBoard.PileTypes.FOUNDATION, pile_index=j)
            if self.can_play_on_foundation(src_card, j):
                possible_moves.append(CalculationBoard.Move(src=src, dest=dest))

        # deck to waste --> all waste are playable
        for i in range(len(self.wastes)):
            dest = CalculationBoard.CardLocation(pile_type=CalculationBoard.PileTypes.WASTE, pile_index=i)
            possible_moves.append(CalculationBoard.Move(src=src, dest=dest))

        return possible_moves

    @staticmethod
    def apply_move_to_board(board, move):
        new_board = deepcopy(board) # immutable, avoid changing

        src = move.src
        if src.pile_type == CalculationBoard.PileTypes.DECK:
            card = new_board.deck.pop()
        elif src.pile_type == CalculationBoard.PileTypes.WASTE:
            card = new_board.wastes[src.pile_index].pop()
        else:
            raise InvalidMoveException("Unexpected move source pile type: {}".format(src.pile_type))
        
        dest = move.dest
        if dest.pile_type == CalculationBoard.PileTypes.FOUNDATION:
            new_board.foundations[dest.pile_index].append(card)
        elif dest.pile_type == CalculationBoard.PileTypes.WASTE:
            new_board.wastes[dest.pile_index].append(card)
        else:
            raise InvalidMoveException("Unexpected move dest pile type: {}".format(dest.pile_type))

        new_board.moves.append(move)

        return new_board




class CalculationPlayer:
    def choose_best_move(self, possible_moves):
        """
        core logic for the player. subclasses should overwrite to implement
        their own logic
        """
        pass

class RandomPlayer(CalculationPlayer):
    def choose_best_move(self, possible_moves):
        return random.choice(possible_moves)

class GreedyPlayer(CalculationPlayer):
    def choose_best_move(self, possible_moves):
        # list of (weight, move)
        weighted_moves = [(self.get_move_weight(move), move) for move in possible_moves]
        weighted_moves.sort(key=lambda x: x[0])
        return weighted_moves[0][1]

    def get_move_weight(self, move):
        if move.dest.pile_type == CalculationBoard.PileTypes.FOUNDATION:
            return 1
        else:
            return 2





class CalculationSolver:
  def __init__(self, board):
    self.starting_board = deepcopy(board)
    self.played = set()
    self.limit = (board.NUM_SUITS * board.cards_per_suit) ** 5

  def solve(self):
    pass

@dataclass(order=True)
class PrioritizedBoard:
  priority: int
  board: CalculationBoard=field(compare=False)

def old_priority(board):
  foundation_lens = list(map(len, board.foundations))
  waste_lens = list(map(len, board.wastes))
  
  progress = sum(foundation_lens)
  
  deck_size = board.cards_per_suit * CalculationBoard.NUM_SUITS
  distance = deck_size - len(board.deck)
  
  foundation_diff = max(foundation_lens) - min(foundation_lens)
  waste_diff = max(waste_lens) - min(waste_lens)
  evenness = (foundation_diff + waste_diff)/4

  difficulty = 1 # TODO: buried costs

  return distance + difficulty + evenness - progress

def distance_traveled(board):
    deck_size = board.cards_per_suit * CalculationBoard.NUM_SUITS
    played_so_far = deck_size - len(board.deck)
    return played_so_far

def distance_to_go(board):
    deck_size = board.cards_per_suit * CalculationBoard.NUM_SUITS
    num_in_foundations = sum(map(len, board.foundations))
    distance_from_goal = deck_size - num_in_foundations
    return distance_from_goal

def a_star_priority(board):
    return distance_traveled(board) + distance_to_go(board)

class BFSSolver(CalculationSolver):
  def __init__(self, board, priority_func):
    super().__init__(board)
    self.priority = priority_func

  def solve(self):
    boards = PriorityQueue()
    board = self.starting_board
    pb = PrioritizedBoard(self.priority(board), board)
    boards.put(pb)

    while boards and len(self.played) <= self.limit:
      pb = boards.get()
      board = pb.board
      self.played.add(board)

      # print(str(board))

      if board.is_winning():
        return board

      for move in CalculationBoard.get_possible_moves(board):
        child_board = CalculationBoard.apply_move_to_board(board, move)
        if child_board not in self.played:
          pb = PrioritizedBoard(self.priority(child_board), child_board)
          boards.put(pb)

    return board

def play_game(board, player):
    """
    Automates playthrough from board state with given player's playing strategy
    """
    # print("===== STARTING =====")
    while not board.is_winning():
        # print(str(board))
        possible_moves = board.get_possible_moves()
        if not possible_moves:
            # print("===== LOST :( =====")
            return False

        move = player.choose_best_move(possible_moves)
        new_board = CalculationBoard.apply_move_to_board(board, move)
        board = new_board

    # print(str(board))
    # print("===== WON!!! :D =====")
    return True
    # TODO: keep track of moves

# Main Function

def compare_players(player1, player2, cards_per_suit, num_games):
  results1 = []
  results2 = []
  for game in range(num_games):
    board = CalculationBoard(cards_per_suit)
    results1.append(play_game(board, player1))
    results2.append(play_game(board, player2))
  print("Player 1 won {0} games".format(results1.count(True)))
  print("Player 2 won {0} games".format(results2.count(True)))

def main():
    cards_per_suit = 7
    board = CalculationBoard(cards_per_suit)

    print("===== STARTING DECK ======")
    print(board.deck)

    print("===== COMPARING PLAYERS ========")
    player = RandomPlayer()
    player2 = GreedyPlayer()
    compare_players(player, player2, cards_per_suit, 5)

    print("===== BFS OLD PRIORITY ========")
    bfs = BFSSolver(board, old_priority)
    end_board = bfs.solve()
    print("Num played: {0}".format(len(bfs.played)))
    print("Num moves: {0}".format(len(end_board.moves)))

    print("===== BFS A* PRIORITY ========")
    bfs = BFSSolver(board, a_star_priority)
    end_board = bfs.solve()
    print("Num played: {0}".format(len(bfs.played)))
    print("Num moves: {0}".format(len(end_board.moves)))

if __name__ == "__main__":
    main()


