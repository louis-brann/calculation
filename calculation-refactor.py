#!/usr/bin/env python
import random                      # for shuffling
from copy import deepcopy          # for static board states
from collections import namedtuple # for simple classes

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

    NUM_FOUNDATIONS = 4
    NUM_WASTES = 4
    NUM_PILES = NUM_FOUNDATIONS + NUM_WASTES

    class PileTypes:
        FOUNDATION = 1
        WASTE = 2
        DECK = 3

    # TODO: do we need to pass in cards_per_suit and deck?
    # they were relics of tree-searching, but that may not be necessary.
    def __init__(self, cards_per_suit=13, deck=None):
        self.foundations = [[i] for i in range(1, 1+CalculationBoard.NUM_FOUNDATIONS)]
        self.wastes = [[] for i in range(CalculationBoard.NUM_WASTES)]

        self.card_values = list(range(1, cards_per_suit)) + [0]
        self.winning = [[(base*i)%cards_per_suit for i in self.card_values] for base in range(1, 1+CalculationBoard.NUM_FOUNDATIONS)]

        self.deck = deck if deck else CalculationBoard.generate_random_deck(cards_per_suit)

    def __eq__(self, other):
        return self.foundations == other.foundations and self.wastes == other.wastes and self.deck == other.deck

    def __repr__(self):
        return str([self.foundations, self.wastes, self.deck])

    @staticmethod
    def generate_random_deck(cards_per_suit):
        values = list(range(1, cards_per_suit)) + [0]
        all_values = (values * 4)
        non_foundation = all_values[4:]
        random.shuffle(non_foundation)
        return all_values[:4] + non_foundation

    def is_winning(self):
        return self.foundations == self.winning

    def get_possible_moves(self):
        moves_from_waste_piles = self.get_possible_moves_from_waste()
        moves_from_deck = self.get_possible_moves_from_deck()
        return moves_from_waste_piles + moves_from_deck

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

            src = CardLocation(pile_type=CalculationBoard.PileTypes.WASTE, pile_index=i)
            top_card = waste[-1]
            for j in range(len(self.foundations)):
                foundation = self.foundations[j]
                increment = base_card = foundation[0]
                next_expected = foundation[-1] + increment
                if top_card == next_expected:
                    dest = CardLocation(pile_type=CalculationBoard.PileTypes.FOUNDATION, pile_index=j)
                    possible_moves.append(Move(src=src, dest=dest))
        return possible_moves

    def get_possible_moves_from_deck(self):
        possible_moves = []
        if not self.deck:
            return possible_moves

        top_card = self.deck[-1]
        src = CardLocation(pile_type=CalculationBoard.PileTypes.DECK, pile_index=0)

        # deck to foundations
        for j in range(len(self.foundations)):
            foundation = self.foundations[j]
            increment = base_card = foundation[0]
            next_expected = foundation[-1] + increment
            if top_card == next_expected:
                dest = CardLocation(pile_type=CalculationBoard.PileTypes.FOUNDATION, pile_index=j)
                possible_moves.append(Move(src=src, dest=dest))

        # deck to waste --> all waste are playable
        for i in range(len(self.wastes)):
            dest = CardLocation(pile_type=CalculationBoard.PileTypes.WASTE, pile_index=i)
            possible_moves.append(Move(src=src, dest=dest))

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

        return new_board

CardLocation = namedtuple('CardLocation', ['pile_type', 'pile_index'])
Move = namedtuple('Move', ['src', 'dest'])
class InvalidMoveException(Exception):
    pass

class CalculationPlayer:
    def choose_best_move(self, possible_moves):
        """
        core logic for the player. subclasses should overwrite to implement
        their own logic
        """
        return random.choice(possible_moves)

# Main Function

def main():
    cards_per_suit = 5
    board = CalculationBoard(cards_per_suit)
    player = CalculationPlayer()
    while not board.is_winning():
        possible_moves = board.get_possible_moves()
        if not possible_moves:
            print "===== NO MORE MOVES ====="
            print "Last board: " + str(board)
            return

        move = player.choose_best_move(possible_moves)
        # try:
        new_board = CalculationBoard.apply_move_to_board(board, move)
        # except InvalidMoveException:
        #     print "=== ERROR ==="
        #     print board
        #     for move in possible_moves:
        #         print "src: {src}, dest: {dest}".format(src=move.src, dest=move.dest)
        #     return
        board = new_board

    print "===== WON!!! ====="
    # TODO: keep track of moves

if __name__ == "__main__":
    main()


