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
Variables
    Priority
        Progress: Num cards in foundation piles (to a power?)
        Distance
        Difficulty
        Evenness
    Algorithm
        IDA*
        Best First Search
        Monte Carlo Search
    Children
        simple      (rank piles by length)
        kings       (save a pile for kings)
        short_term  (favor piles that create chains)
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

    def is_foundation(self, pile_i):
        return pile_i < 4

    def is_waste(self, pile_i):
        return pile_i > 3

    def nth_card(self, base, n):
        """
        Only valid for foundations
        """
        return (base + base*n) % self.cards_per_suit

    def next_card(self, pile_i):
        """
        Only valid for foundations
        """
        pile = self.piles[pile_i]
        return self.nth_card(pile[0], len(pile))

    def old_matches_next_card(self, pile_i):
        foundation = self.piles[dest]
        if len(foundation) >= self.cards_per_suit:
            return False
        else:
            step = foundation[-1]
            base = foundation[0]
            return card == (step+base)%self.cards_per_suit

    def valid_set(self, card, dest):
        # Always allowed to set on a waste pile
        if self.is_waste(dest):
            return True
        else:
            return len(self.piles[dest])<self.cards_per_suit and card == self.next_card(dest) 

        # If we didn't return True yet, it is not valid
        return False

    def valid_move(self, src, dest):
        """
        A move must be from a waste pile to a foundation pile
        """
        # Must move from waste pile
        valid_source = self.is_waste(src)
        # Can't move to another waste pile
        valid_dest = self.is_foundation(dest)
        # Make sure the card is allowed for the move
        valid_transition = self.valid_set(self.piles[src][-1], dest)
        
        return valid_source and valid_dest and valid_transition

    def play_drawn(self, card, dest):
        """
        Returns a new board with a card played from the deck onto a pile
        """
        bcopy = deepcopy(self)
        bcopy.piles[dest].append(card)
        bcopy.last_used += 1
        bcopy.n_moves += 1
        bcopy.moves.append((CalculationBoard.deck_i, dest))
        if card == 0:
            bcopy.kings_seen += 1
        return bcopy

    def move_card(self, src, dest):
        """
        Returns a new board with a card moved from src to dest
        """
        bcopy = deepcopy(self)
        card = bcopy.piles[src].pop()
        bcopy.piles[dest].append(card)
        bcopy.n_moves += 1
        bcopy.moves.append((src, dest))
        return bcopy

    def len_priority(self):
        """
        priority = cost to board + board to finish
                    (n_moves)       ()
        """
        deck_size = self.cards_per_suit*4
        n_deck = deck_size - (self.last_used+1)
        n_founds = sum(map(len, self.piles[:4]))
        n_waste = sum(map(len, self.piles[4:]))

        cost_to_board = self.n_moves
        board_to_finish = n_deck + n_waste
        return cost_to_board + board_to_finish

    def buried_cost(self):
        ans = 0
        for found in self.piles[:4]:
            base_card = found[0]
            found_len = len(found)
            next_card = self.nth_card(base_card, found_len)

            for i in range(4):
                # Hack to avoid going off the end
                if next_card == base_card:
                    break

                min_dist = None

                for waste in self.piles[4:]:
                    if next_card in waste:
                        dist = len(waste) - waste.index(next_card)
                        if min_dist != None:
                            min_dist = min(min_dist, dist)
                        else:
                            min_dist = dist


                if min_dist != None:
                    ans += min_dist * (self.cards_per_suit - found_len - i)

                next_card = (next_card + base_card) % self.cards_per_suit
        return ans

    def priority(self):
        """
            Progress to goal: 
                how many cards in foundation piles
            Distance to goal: 
                how many cards are left in deck (at least)
            Difficulty: 
                how buried are cards that are needed soon?
        """
        found_sizes = [len(f) for f in self.piles[:4]]
        waste_sizes = [len(w) for w in self.piles[4:]]

        progress = sum(found_sizes)    # Num cards in foundations
        distance = (self.cards_per_suit*4) - (self.last_used+1)  # Num cards left in deck

        found_diff = max(found_sizes) - min(found_sizes)
        waste_diff = max(waste_sizes) - min(waste_sizes)
        evenness = (found_diff + waste_diff)/4

        difficulty = self.buried_cost()  # How hard it is to get the next few
                                        # cards off the waste piles

        a = 1
        b = 1
        c = 1
        d = 1
        return distance*a + difficulty*b + evenness*c - progress*d

    # Note this equality/less than disparity is terrible style
    def __lt__(self, other):
        return self.priority() < other.priority()

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        string =  "Priority: {0!s}\n".format(self.priority())
        string += "Num Moves: {0!s}\n".format(self.n_moves)
        string += "Drawn: {0!s}/{1!s}\n".format(self.last_used+1, self.cards_per_suit*4)
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
        self.values = list(range(1,cards_per_suit)) + [0]
        self.winning = [[(base*i)%cards_per_suit for i in self.values] for base in range(1,5)]
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
        values = list(range(1, cards_per_suit)) + [0]
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
            print("IDA start")
            not_winning, best_board = self.dfs(root)
            self.threshold = self.next_threshold
            self.next_threshold = inf
        return best_board

    def dfs(self, board):
        self.print_board(board)
    
        # Children = boards one move away from this board
        children = self.children(board)
        children.sort()

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
            waste_moves = self.ranked_wastes_short_term(next_card, board)
            children.extend(waste_moves)

        return children

    # First form of ranking waste: by the length of the waste pile. This is 
    # a decent proxy for how much you're actually going to be blocking by
    # playing on that pile
    def ranked_wastes_simple(self, card, board):
        waste_lens = [(len(board.piles[i]),i) for i in range(4,8)]
        waste_lens.sort()
        return [board.play_drawn(card, w) for (l,w) in waste_lens]

    def precedes(self, board, card, next_card):
        # K precedes nothing
        if card == 0:
            return False

        # Check if it will eventually follow it on any foundation
        for i in range(4):
            base = board.piles[i][0]
            # If it follows the card and the card has not already been placed
            if next_card == card + base and card not in board.piles[i]:
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
                    if card == 0 or board.kings_seen == 4:
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
            # Try only playing kings on K pile
            k_pile_playable = (card == 0 or board.kings_seen == 4)
            if waste_i == CalculationBoard.k_pile:
                if k_pile_playable:
                    next_board = board.play_drawn(card, waste_i)
                    waste_moves.append(next_board)
            elif card != 0:
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
    filebase = "output/priority-{0!s}-{1}-sorted-{2!s}".format(cards_per_suit, mode, version)
    filename = filebase + ".txt"
    while os.path.exists(filename):
        version += 1
        filebase = filebase[:-1] + str(version)
        filename = filebase + ".txt"
    print("Writing to", filename)
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
    csvbase = "data/priority1-{0!s}-{1}-{2!s}".format(cards_per_suit, mode, version)
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

    if len(argv) > 1:
        print(argv[1])
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
        calculation = Calculation(cards_per_suit)
        # calculation = Calculation(cards_per_suit, [1, 2, 3, 4, 1, 2, 4, 6, 4, 7, 7, 1, 3, 5, 4, 7, 1, 6, 5, 5, 3, 7, 5, 6, 6, 3, 2, 2])
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


