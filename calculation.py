#!/usr/bin/env python
from __future__ import division # for automatic floating point div
import random                   # for shuffling
from copy import deepcopy       # for static board states
from queue import PriorityQueue # for keeping track of boards
import sys                      # for main args
from math import inf            # for max threshold
from time import time           # for performance
import csv                      # for formatted output

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
        deck_i = 8

        def __init__(self, cards_per_suit=13):
            # Prepare the piles
            foundations = [[i] for i in range(1,5)]
            waste_heaps = [[] for i in range(4)]
            self.piles = foundations + waste_heaps
            self.last_used = 3 # Four foundations --> starts off with 
            self.cards_per_suit = cards_per_suit
            self.n_moves = 0
            self.moves = []

        def valid_set(self, card, dest):
            # Always allowed to set on a waste pile
            if dest > 3:
                return True
            # Otherwise make sure it's a step away from the base
            else:
                foundation = self.piles[dest]
                if len(foundation) >= self.cards_per_suit:
                    return False
                else:
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
            bcopy = deepcopy(self)
            bcopy.piles[dest].append(card)
            bcopy.last_used += 1
            bcopy.n_moves += 1
            bcopy.moves.append((CalculationBoard.deck_i, dest))
            return bcopy

        def move_card(self, src, dest):
            bcopy = deepcopy(self)
            card = bcopy.piles[src].pop()
            bcopy.piles[dest].append(card)
            bcopy.n_moves += 1
            bcopy.moves.append((src, dest))
            return bcopy

        def priority(self):
            """
            priority = cost to board + board to finish
                        (n_moves)       ()
            """
            deck_size = self.cards_per_suit*4
            n_deck = deck_size - (self.last_used+1)
            n_founds = sum([len(found) for found in self.piles[:4]])
            n_waste = sum([len(waste) for waste in self.piles[4:]])

            cost_to_board = self.n_moves
            board_to_finish = n_deck + n_waste
            return cost_to_board + board_to_finish - n_founds

        def __lt__(self, other):
            return self.priority() < other.priority()

        def __eq__(self, other):
            return str(self) == str(other)

        def __hash__(self):
            return hash(str(self))

        def __str__(self):
            string =  "Priority: " + str(self.priority()) + "\n"
            string += "Num Moves: " + str(self.n_moves) + "\n"
            string += "============\n" + \
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

        def __repr__(self):
            return str(self.piles)

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

        self.threshold = inf
        self.next_threshold = inf

        self.played = set()
        self.iters = 0

    def is_winning(self, board):
        return board.piles[:4] == self.winning

    def is_lost(self, board):
        remaining_deck = self.deck[board.last_used+1:]

        # Loop through the 

    def play_bfs(self):
        """
        Best-first Search, based on priority() as defined in CalculationBoard.
        Returns the number of moves required to get to the winning board.
        """
        boards = PriorityQueue()
        new_board = CalculationBoard(self.cards_per_suit)
        boards.put(new_board)
        
        while boards:
            board = boards.get()
            self.played.add(board)

            self.print_board(board)

            if self.is_winning(board):
                return board

            children = self.children(board)
            for child in children:
                if child not in self.played:
                    boards.put(child)


    def play_ida(self):
        """
        Iterative deepening algorithm to save on space
        """
        # Initial setup
        root = CalculationBoard(self.cards_per_suit)
        self.threshold = root.priority()
        self.next_threshold = inf
        self.iters += 1

        # Start the search
        not_winning = True
        best_board = None
        while not_winning:
            not_winning, best_board = self.dfs(root)
            self.threshold = self.next_threshold
            self.next_threshold = inf
        return best_board

    def dfs(self, board):
        self.print_board(board)
    
        # Children = boards one move away from this board
        children = self.children(board)
        #print("Children:",str(children))

        for child in children:
            # If it is winning, return that board
            if self.is_winning(child):
                print("Found winner")
                return (False, child)

            # If the child has already lost, quit early
            if self.is_lost(child):
                break

            # If the child is worth expanding, do so
            cost = child.priority()
            if cost <= self.threshold:
                not_winning, winner = self.dfs(child)
                # Break out if child succeeded
                if not not_winning:
                    return not_winning, winner

            # If the child is not worth expanding, then it can at least
            # bound our future generations
            elif cost < self.next_threshold:
                self.next_threshold = cost

        return (True, None)

    def children(self, board):
        children = []

        # Check if anything is playable from the waste heaps
        for waste_i in range(4,8):
            waste_heap = board.piles[waste_i]
            if len(waste_heap) > 0:
                for found_i in range(4):
                    if board.valid_move(waste_i, found_i):
                        next_board = board.move_card(waste_i, found_i)
                        children.append(next_board)

        # Draw a card and do something with it
        if board.last_used < len(self.deck)-1:
            next_card = self.deck[board.last_used+1]

            # Check all foundations
            for found_i in range(4):
                if board.valid_set(next_card, found_i):
                    next_board = board.play_drawn(next_card, found_i)
                    children.append(next_board)

            waste_ranks = [(len(board.piles[i]),i) for i in range(4,8)]
            waste_ranks.sort()

            # Place on waste piles in order
            for weight,waste_i in waste_ranks:
                next_board = board.play_drawn(next_card, waste_i)
                children.append(next_board)

        return children

    def print_board(self, board):
        """
        Function for printing the board every so often, usually only used 
        for larger/longer games
        """
        self.iters += 1
        if self.iters % 10000 == 0:
            print("=== Current board ===")
            print(board)
        return

def main(argv):
    cards_per_suit = 5
    niters = 1

    if len(argv) > 2:
        cards_per_suit = int(argv[1])
        if len(argv) > 2:
            niters = int(argv[2])

    print("Starting games with {0!s} cards per suit".format(cards_per_suit))

    nboards = 0
    decks = []
    moves = []
    times = []
    for i in range(niters):
        print("Game",i)

        # Play and time a game of calculation
        start = time()
        calculation = Calculation(cards_per_suit)
        print("Deck:", calculation.deck)
        board = calculation.play_bfs()
        end = time()

        # Record all the data to output later
        decks.append(calculation.deck)
        moves.append(board.moves)
        times.append(end-start)

    print("Writing to file...")

    human_readable(niters, decks, moves, times, cards_per_suit)

def human_readable(niters, decks, moves, times, cards_per_suit):
    """
    Could replace the csv output if you want to be able to just look at the 
    output, rather than have another program analyze it. Kept in a separate
    function in case I ever want to use it again 
    """
    filename = "moves-{0!s}.txt".format(cards_per_suit)
    with open(filename, 'w+') as output:
        output.write("Cards per Suit: "+str(5)+"\n")
        output.write("=================\n")
        for i in range(niters):
            deck = decks[i]
            move = moves[i]
            elapsed = times[i]
            output.write("Deck:"+str(deck)+"\n")
            output.write("Moves:"+str(move)+"\n")
            output.write("Time elapsed:"+str(elapsed)+"\n")

def program_readable(niters, decks, moves, times, cards_per_suit):
    csv_name = "moves-{0!s}.csv".format(cards_per_suit)
    with open(csv_name, 'w+') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(niters):
            writer.writerow([decks[i], moves[i], times[i]])

if __name__ == "__main__":
    main(sys.argv)


