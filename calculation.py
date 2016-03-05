#!/usr/bin/env python
from __future__ import division     # for automatic floating point div
import random                       # for shuffling
from copy import deepcopy           # for static board states
from queue import Queue, PriorityQueue # for keeping track of boards
import sys                          # for main args

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
        deck_i = 9
        founds_i = range(0,4)
        wastes_i = range(4,8)

        def __init__(self, cards_per_suit=13):
            self.cards_per_suit = cards_per_suit

            # Prepare the piles
            foundations = [[i] for i in range(1,5)]
            waste_heaps = [[] for i in CalculationBoard.wastes_i]
            self.piles = foundations + waste_heaps

            # Four foundations --> starts off with 4 cards used in the deck
            self.last_used = 3 

        def valid_dest(self, card, dest):
            # Never allowed to play onto deck
            if dest == CalculationBoard.deck_i:
                return False
            # Always allowed to set on a waste pile
            elif dest in CalculationBoard.wastes_i:
                return True
            # On foundations, make sure it's a step away from the base
            else:
                foundation = self.piles[dest]
                if len(foundation) >= self.cards_per_suit:
                    #print("Too many cards on foundation!")
                    return False
                else:
                    step = foundation[-1]
                    base = foundation[0]
                    return card == (step+base)%self.cards_per_suit or \
                           card == (step+base)

        def valid_src(self, src):
            # Allowed to take from anywhere but foundations
            if src in CalculationBoard.founds_i:
                print("Can't play from foundation")
                return False

        def valid_move(self, src, dest):
            return self.valid_src(src) and self.valid_dest(self.piles[src][-1],dest)

        def play_drawn(self, card, dest):
            """
            Given a card from the deck and a destination pile, plays the 
            card to the destination pile and 
            """
            copy = deepcopy(self)
            copy.piles[dest].append(card)
            copy.last_used += 1
            return copy

        def move_card(self, src, dest):
            """
            Used for playing a card from one pile to another pile. Separate
            from playing a card from the deck, because the deck is shared by
            all boards, so figuring out what card it is different
            """
            copy = deepcopy(self)
            card = copy.piles[src].pop()
            copy.piles[dest].append(card)
            return copy

        def priority(self):
            deck_size = self.cards_per_suit*4
            n_in_deck = deck_size - (self.last_used+1)
            n_founds = sum([len(found) for found in self.piles[:4]])
            n_waste = sum([len(waste) for waste in self.piles[4:]])
            return n_in_deck - n_founds + n_waste

        def __lt__(self, other):
            return self.priority() < other.priority()

        def __eq__(self, other):
            return str(self)==str(other)

        def __hash__(self):
            return hash(str(self))

        def __str__(self):
            string = ""
            # Foundations
            for f in CalculationBoard.founds_i:
                string += str(self.piles[f]) + "\n"
            # Waste piles
            for w in CalculationBoard.wastes_i:
                string += str(self.piles[w]) + "\n"
            return string

class Calculation:
    def __init__(self, cards_per_suit=13):
        self.values = list(range(1,cards_per_suit+1))
        self.winning = [[i if i==cards_per_suit else (base*i)%cards_per_suit for i in self.values] for base in range(1,4)]
        self.win_pos = [[win_stack.index(i) for win_stack in self.winning] for i in self.values]

        # Prepare the deck
        all_values = (self.values * 4)
        non_foundation = all_values[4:]
        random.shuffle(non_foundation)
        self.deck = all_values[:4] + non_foundation

        self.cards_per_suit = cards_per_suit

        # Store played boards to avoid cycles
        self.played = set()

    def is_winning(self, board):
        return board.piles[:4] == self.winning

    def play_bfs(self):
        boards = PriorityQueue()
        new_board = CalculationBoard(self.cards_per_suit)
        boards.put((new_board.priority(), new_board))
        counter = 0
        while boards:
            priority, board = boards.get()
            self.played.add(board)

            if counter % 10000 == 0:
                print("=== Current board ===")
                print(board)

            # Stop if the board is already winning
            if self.is_winning(board):
                print("Won a board!")
                return counter

            # Check if anything is playable from the waste heaps
            for waste_i in range(4,8):
                waste_heap = board.piles[waste_i]
                if len(waste_heap) > 0:
                    for found_i in range(4):
                        if board.valid_move(waste_i, found_i):
                            next_board = board.move_card(waste_i, found_i)
                            if next_board not in self.played:
                                boards.put((next_board.priority(), next_board))

            # Draw a card and do something with it
            if board.last_used < len(self.deck)-1:
                next_card = self.deck[board.last_used+1]

                # Check all foundations
                for found_i in range(4):
                    if board.valid_dest(next_card, found_i):
                        next_board = board.play_drawn(next_card, found_i)
                        if next_board not in self.played: 
                            boards.put((next_board.priority(), next_board))

                # TODO: Rank waste piles
                waste_ranks = [(len(board.piles[i]),i) for i in range(4,8)]
                waste_ranks.sort()

                # Place on waste piles in order
                for weight,waste_i in waste_ranks:
                    next_board = board.play_drawn(next_card, waste_i)
                    if next_board not in self.played:
                        boards.put((next_board.priority(), next_board))

            counter += 1

def main(argv):
    cards_per_suit = 5

    if len(argv) > 1:
        cards_per_suit = int(argv[1])

    num_iters = 1
    num_boards = 0
    for i in range(num_iters):
        print("New game!")
        calculation = Calculation(cards_per_suit)
        print(calculation.deck)

        num_boards += calculation.play_bfs()

    print("Average number of boards: ", num_boards/num_iters)

if __name__ == "__main__":
    main(sys.argv)


