#!/usr/bin/env python
from __future__ import division     # for automatic floating point div
import random                       # for shuffling
from copy import deepcopy               

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

class Calculation:
    def __init__(self, cards_per_suit=13):
        self.values = list(range(1,cards_per_suit+1))
        self.winning = [[i if i==cards_per_suit else base*i%cards_per_suit for i in self.values] for base in range(1,5)]
        self.win_pos = [[win_stack.index(i) for win_stack in self.winning] for i in self.values]

        # Prepare the deck
        self.deck = (self.values * 4)[4:]
        random.shuffle(self.deck)

    def play(self):
        print("=== Starting game with deck ===")
        print(self.deck)

        boards = []
        boards.append(CalculationBoard())
        while boards:
            board = boards.pop()
            print("=== Current Board ===")
            print(board)

            next_card = board.deck.pop()

            # Decide which waste heap is worst to play it on, stack that first
            # so it gets played last
            waste_depths = [(len(board.piles[i]), i) for i in range(5,9)]
            waste_depths.sort(reverse=True)
            for depth,pile in waste_depths:
                boards.push(CalculationBoard.from_board_with_move(board,next_card,pile))

            # If the card is valid to go on a stack, make that move and push
            # that new board
            for base in range(1,5):
                if board.is_move_valid(new_card, base):
                    boards.push(CalculationBoard.from_board_with_move(board,next_card,base))

    class CalculationBoard:
        def __init__(self):
            # Prepare the piles
            self.foundations = [list(i) for i in range(1,4)]
            self.waste_heaps = [[] for i in range(1,4)]

        def is_move_valid(self, card, foundation):
            return card == self.foundations[foundation][-1]+foundation

        def is_winning(self):
            return self.foundations == Calculation.winning

        def rank_move(self, card, pile):
            # return -1 if not valid
            if pile < 4 and not is_move_valid(self, card, pile):
                return -1
            
            # Currently all valid moves are ranked one
            # TODO: Make this more complex
            return 1

        def place_card(self, card, pile):
            is_waste = pile/4
            index = pile%4
            if is_waste:
                self.waste_heaps[index].append(card)
            else:
                self.foundations[index].append(card)

        def from_board_with_move(board, card, pile):
            copy = deepcopy(board)
            copy.place_card(board,card,pile)
            return copy

        def __repr__(self):
            string = ""
            string.join([str(l)+"\n" for l in self.foundations])
            string.join([str(l)+"\n" for l in self.waste_heaps])
            return string

calculation = Calculation(5)
print(calculation.deck)

