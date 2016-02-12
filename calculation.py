#!/usr/bin/env python
from __future__ import division     # for automatic floating point div
import random                       # for shuffling
from copy import deepcopy
from queue import Queue, PriorityQueue              

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
        num_piles = 8

        def __init__(self, cards_per_suit=13):
            # Prepare the piles
            foundations = [[i] for i in range(1,5)]
            waste_heaps = [[] for i in range(4)]
            self.piles = foundations + waste_heaps
            self.last_used = 3 # Four foundations --> starts off with 
            self.cards_per_suit = cards_per_suit

        def valid_set(self, card, dest):
            # Always allowed to set on a waste pile
            if dest > 3:
                return True
            # Otherwise make sure it's a step away from the base
            else:
                foundation = self.piles[dest]
                step = foundation[-1]
                base = foundation[0]
                return card == (step+base)%self.cards_per_suit or \
                       card == (step+base)

        def valid_move(self, src, dest):
            if dest > 3:
                print("Move destination must be a foundation")
                return False
            elif src < 4:
                print("Cannot move from a foundation")
                return False
            else:
                src_card = self.piles[src][-1]
                return self.valid_set(src_card, dest)

        def play_drawn(self, card, dest):
            copy = deepcopy(self)
            copy.piles[dest].append(card)
            copy.last_used += 1
            return copy

        def move_card(self, src, dest):
            copy = deepcopy(self)
            card = copy.piles[src].pop()
            copy.piles[dest].append(card)
            return copy

        def priority(self):
            deck_size = self.cards_per_suit*4
            n_founds = sum([len(found) for found in self.piles[:4]])
            n_waste = sum([len(waste) for waste in self.piles[4:]])
            return deck_size - n_founds + n_waste

        def __lt__(self, other):
            return self.priority() < other.priority()

        def __str__(self):
            string = "============\n" + \
                     "Foundations:\n" + \
                     "============\n"
            for f in range(4):
                string += str(self.piles[f]) + "\n"
            string += "===========\n" + \
                      "Waste heaps\n" + \
                      "===========\n"
            for w in range(4,8):
                string += str(self.piles[w]) + "\n"
            return string

class Calculation:
    def __init__(self, cards_per_suit=13):
        self.values = list(range(1,cards_per_suit+1))
        self.winning = [[i if i==cards_per_suit else base*i%cards_per_suit for i in self.values] for base in range(1,5)]
        self.win_pos = [[win_stack.index(i) for win_stack in self.winning] for i in self.values]

        # Prepare the deck
        all_values = (self.values * 4)
        non_foundation = all_values[4:]
        random.shuffle(non_foundation)
        self.deck = all_values[:4] + non_foundation

        self.cards_per_suit = cards_per_suit

    def is_winning(self, board):
        return board.piles[:4] == self.winning

    def play_bfs(self):
        boards = PriorityQueue()
        new_board = CalculationBoard(self.cards_per_suit)
        boards.put((new_board.priority(), new_board))
        while boards:
            priority, board = boards.get()

            print("=== Current board ===")
            print(board)

            # Stop if the board is already winning
            if self.is_winning(board):
                print("Won a board!")
                return board

            # Check if anything is playable from the waste heaps
            for waste_i in range(4,8):
                waste_heap = board.piles[waste_i]
                if len(waste_heap) > 0:
                    for found_i in range(4):
                        if board.valid_move(waste_i, found_i):
                            next_board = board.move_card(waste_i, found_i)
                            boards.put((next_board.priority(), next_board))

            # Draw a card and do something with it
            if board.last_used < len(self.deck)-1:
                next_card = self.deck[board.last_used+1]

                # Check all foundations
                for found_i in range(4):
                    if board.valid_set(next_card, found_i):
                        next_board = board.play_drawn(next_card, found_i)
                        boards.put((next_board.priority(), next_board))

                # TODO: Rank waste piles
                waste_ranks = [(len(board.piles[i]),i) for i in range(4,8)]
                waste_ranks.sort()

                # Place on waste piles in order
                for weight,waste_i in waste_ranks:
                    next_board = board.play_drawn(next_card, waste_i)
                    boards.put((next_board.priority(), next_board))

            else:
                print("Losing game!")


    def play_dfs(self):
        wins = []
        boards = []


calculation = Calculation(5)
print(calculation.deck)
calculation.play_bfs()


