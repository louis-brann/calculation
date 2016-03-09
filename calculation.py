#!/usr/bin/env python
from __future__ import division # for automatic floating point div
import random                   # for shuffling
from copy import deepcopy       # for static board states
from queue import PriorityQueue # for keeping track of boards
import sys                      # for main args
from math import inf            # for max threshold
from time import time           # for performance
import csv                      # for formatted output
import os.path                  # for output files

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

"""
Playing strategies to potentially incorporate:
----------------------------------------------
1. Keep one pile open for a K
2. Play onto waste piles intelligently
    - Don't block something that comes before you in every pile (otherwise you lose)
    - Weight the piles by how soon the cards come up, play onto piles that 
      have the lowest
        a) number of things coming up soon (threshold)
        b) sum of things coming up soon
    - If you can play on something that comes directly after you, do

Pruning strategies
------------------
1. Determine when you lose
    - If a card is on top of another card that comes before it in all piles,
      the game is over

Efficencies
-----------
1. Don't deep copy boards for every move
    - Store boards at certain points, and in between, store moves until that
      point e.g. save boards at depths of 2, 4, 8, 16 ; calculate moves
      between them until then
2. Make deep copies cheaper 
3. Move priority function to Calculation game level, and have boards store
   their priority instead of calculating it every time

"""

"""
Statistics to Look At
---------------------
1. Branching factor of IDA at different board sizes. Is there a correlation?
2. How many boards an algorithm goes through to find the solution?
3. 
"""

"""
Reports:
1. Ordering which waste pile to try playing on first -- Looking at combos and
   keeping a pile open for K finds a more optimal solution (less moves), but
   it takes longer than simply using the length of the waste pile as the rank
"""

class CalculationBoard:
    """
    A CalculationBoard keeps track of the foundation piles and the waste piles.
    These are kept track of in self.piles. Each board is specific to a game
    of Calculation, but all boards of a game share a deck. Thus, each
    CalculationBoard only keeps an index of where it is in the deck. 
    Each board also keeps track of its moves, which could at some point be
    leveraged for data analysis/ML for smarter playing or for more efficient
    storage of boards. Right now making a move makes a full copy of the board,
    but it might be better to only copy the board every so often, and instead
    have shells of boards that all go off a reference board, and then store 
    the moves from that board.
    """

    num_piles = 8
    deck_i = 8
    k_pile = 4 # Try keeping one waste pile open

    def __init__(self, cards_per_suit=13):
        # Prepare the piles
        foundations = [[i] for i in range(1,5)]
        waste_heaps = [[] for i in range(4)]
        self.piles = foundations + waste_heaps
        self.last_used = 3 # Four foundations --> starts off with 
        self.cards_per_suit = cards_per_suit
        self.n_moves = 0
        self.moves = []
        self.kings_seen = 0

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
        if card == self.cards_per_suit:
            bcopy.kings_seen += 1
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
        string =  "Priority: {0!s}\n".format(self.priority())
        string += "Num Moves: {0!s}\n".format(self.n_moves)
        string += "Progress: {0!s}/{1!s}\n".format(self.last_used+1, self.cards_per_suit*4)
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
    """
    The Calculation class represents a game of Calculation. Each instance has
    a specific deck. To play a game, create an instance to get a deck, and then
    use the play_ida() for IDA* or play_bfs() for best-first search
    """

    def __init__(self, cards_per_suit=13, deck=[]):
        self.cards_per_suit = cards_per_suit
        self.values = list(range(1,cards_per_suit+1))
        self.winning = [[i if i==cards_per_suit else (base*i)%cards_per_suit for i in self.values] for base in range(1,5)]
        self.win_pos = [[win_stack.index(i) for win_stack in self.winning] for i in self.values]

        # Prepare the deck
        if deck == []:
            self.deck = Calculation.random_deck(cards_per_suit)
        else:
            self.deck = deck

        self.played = set()     # Used to avoid redundant boards
        self.iters = 0          # Used for printing, maybe stats

        # IDA* thresholds
        self.threshold = inf
        self.next_threshold = inf  

        # Store played boards to avoid cycles
        self.played = set()

    @staticmethod
    def random_deck(cards_per_suit):
        values = list(range(1,cards_per_suit+1))
        all_values = (values * 4)
        non_foundation = all_values[4:]
        random.shuffle(non_foundation)
        return all_values[:4] + non_foundation

    def is_winning(self, board):
        return board.piles[:4] == self.winning

    def is_lost(self, board):
        remaining_deck = self.deck[board.last_used+1:]

        # TODO: Actually implement
        # Loop through the waste piles and check if any have cards that block
        # the card on all piles
        return False

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

            # Place on waste piles in order
            waste_moves = self.ranked_wastes_k(next_card, board)
            children.extend(waste_moves)

        return children

    # First form of ranking waste: by the length of the waste pile. This is 
    # a decent proxy for how much you're actually going to be blocking by
    # playing on that pile
    def simple_ranked_wastes(self, card, board):
        waste_lens = [(len(board.piles[i]),i) for i in range(4,8)]
        waste_lens.sort()
        return [board.play_drawn(card, w) for (l,w) in waste_lens]

    def precedes(self, board, card, next_card):
        # Check if it will eventually follow it on any foundation
        for i in range(4):
            base = board.piles[i][0]
            # If it follows the card and the card has not already been placed
            if next_card == card + base and not card in board.piles[i]:
                return True
        return False

    def ranked_wastes_short_term(self, card, board):
        waste_moves = []
        for waste_i in range(4,8):
            next_board = board.play_drawn(card, waste_i)
            if next_board not in self.played:
                is_k_pile = (waste_i == CalculationBoard.k_pile)
                waste_pile = board.piles[waste_i]
                # If card precedes a card in some waste pile, play it there first
                if len(waste_pile)>0 and self.precedes(board, card, board.piles[waste_i][-1]):
                    waste_moves.insert(0, next_board)
                # If it's the king pile, only play kings unless all kings have
                # been seen
                elif is_k_pile:
                    if card == self.cards_per_suit or board.kings_seen == 4:
                        waste_moves.append(next_board)
                # If it's not a king pile, try not to play a king there
                elif not card == self.cards_per_suit:
                    waste_moves.append(next_board)
        return waste_moves

    # Keeping this version around in case it is more efficient than checking
    # dependencies
    def ranked_wastes_k(self, card, board):
        # Place on waste piles in order
        waste_moves = []
        for waste_i in range(4,8):
            # If it's a K  
            k_pile_playable = (card == self.cards_per_suit or board.kings_seen == 4)
            if waste_i != CalculationBoard.k_pile or k_pile_playable:
                next_board = board.play_drawn(card, waste_i)
                waste_moves.append(next_board)
        return waste_moves

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

# Output Printing Functions

def human_readable(niters, decks, moves, times, cards_per_suit, mode):
    """
    Could replace the csv output if you want to be able to just look at the 
    output, rather than have another program analyze it. Kept in a separate
    function in case I ever want to use it again 
    """
    version = 0
    filebase = "moves-{0!s}-{1}-{2!s}".format(cards_per_suit, mode, version)
    filename = filebase + ".txt"
    while os.path.exists(filename):
        version += 1
        filebase = filebase[:-1] + str(version)
        filename = filebase + ".txt"
    with open(filename, 'w+') as output:
        output.write("Cards per Suit: "+str(cards_per_suit)+"\n")
        output.write("=================\n")
        for i in range(niters):
            deck = decks[i]
            move = moves[i]
            elapsed = times[i]
            output.write("Deck:"+str(deck)+"\n")
            output.write("Moves:"+str(move)+"\n")
            output.write("Time elapsed:"+str(elapsed)+"\n")

def program_readable(niters, decks, moves, times, cards_per_suit, mode):
    version = 0
    csvbase = "moves-{0!s}-{1}-{2!s}".format(cards_per_suit, mode, version)
    csvname = csvbase + ".txt"
    while os.path.exists(csvname):
        version += 1
        csvbase = csvbase[:-1] + str(version)
        csvname = csvbase + ".csv"
    with open(csv_name, 'w+') as csvfile:
        writer = csv.writer(csvfile)
        for i in range(niters):
            writer.writerow([decks[i], moves[i], times[i]])

# Main Function

def main(argv):
    cards_per_suit = 5
    niters = 1
    mode = "ida"

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
        calculation = Calculation(cards_per_suit, [1, 2, 3, 4, 1, 2, 4, 6, 4, 7, 7, 1, 3, 5, 4, 7, 1, 6, 5, 5, 3, 7, 5, 6, 6, 3, 2, 2])
        print("Deck:", calculation.deck)
        if mode == "bfs":
            start = time()
            board = calculation.play_bfs()
            end = time()
        elif mode == "ida":
            start = time()
            board = calculation.play_ida()
            end = time()

        # Record all the data to output later
        decks.append(calculation.deck)
        moves.append(board.moves)
        times.append(end-start)

    print("Writing to file...")

    human_readable(niters, decks, moves, times, cards_per_suit, mode)

if __name__ == "__main__":
    main(sys.argv)


