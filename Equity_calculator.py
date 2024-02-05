import numpy as np
import random
import time
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

def tokens_2(input_string):
    if len(input_string) % 2 != 0:
        raise ValueError("Input string length must be even.")
    tokens = [input_string[i:i+2] for i in range(0, len(input_string), 2)]
    return tokens

class card:
    def __init__(self, rank, color, name):
        self.name = name
        self.rank = rank
        self.color = color
    def index(self):
        return (self.rank, self.color)

class map:
    def __init__(self):
        self.color_names = ['h', 's', 'd', 'c'] #columns
        self.rank_names = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'] #rows
        self.card_map = {}
        for index_row in range(len(self.rank_names)):
            for index_col in range(len(self.color_names)):
                key = f"{self.rank_names[index_row]}{self.color_names[index_col]}"
                value = card(index_row, index_col, f"{self.rank_names[index_row]}{self.color_names[index_col]}")
                self.card_map[key] = value
        self.index_map = {}
        for index_row in range(len(self.rank_names)):
            for index_col in range(len(self.color_names)):
                key = (index_row, index_col)
                value = f"{self.rank_names[index_row]}{self.color_names[index_col]}"
                self.index_map[key] = value

    def card(self, name):
        return self.card_map[name]

    def card_index(self, name):
        return self.card_map[name].index()
    
class deck:
    card_map = map()
    def __init__(self, cards = '', blocked_cards = ''):
        #print(deck.card_map.card_map)
        self.card_map = map()
        self.card_array = np.zeros((13, 4))
        self.cards_names = tokens_2(cards)
        self.blocked_cards_names = tokens_2(blocked_cards)
        for name in self.cards_names:
            self.card_array[self.card_map.card_index(name)] = 1
        for name in self.blocked_cards_names:
            self.card_array[self.card_map.card_index(name)] = -1
    def deal_random(self):
        while True:
            random_rank = random.randint(0, 12)
            random_color = random.randint(0, 3)
            if self.card_array[random_rank, random_color] == 0:
                self.card_array[random_rank, random_color] = 1
                break

    def deal_card(self, name):
        if self.card_array[self.card_map.card_index(name)] == 1:
            self.card_array[self.card_map.card_index(name)] = 1

    def __add__(self, other):
        if isinstance(other, deck):
            tmp = copy.copy(self)
            tmp.card_array = tmp.card_array + other.card_array
            tmp.cards_names += other.cards_names
            tmp.blocked_cards_names += other.blocked_cards_names
            return tmp
        else:
            raise ValueError("'+' Operation not defined")

    def __sub__(self, other):
        if isinstance(other, deck):
            tmp = copy.copy(self)
            tmp.card_array = tmp.card_array - other.card_array
            for element in other.cards_names:
                if element in tmp.cards_names:
                    tmp.cards_names.remove(element)
            for element in other.blocked_cards_names:
                if element in tmp.blocked_cards_names:
                    tmp.blocked_cards_names.remove(element)
            return tmp
        else:
            raise ValueError("'-' Operation not defined")

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            tmp = copy.copy(self)
            tmp.card_array = tmp.card_array * 2
            return tmp
        else:
            raise ValueError("'*' Operation not defined")
        
class player_range: #input_string.split(',')
    def __init__(self, input_codes, blocked_cards = ''):
        self.color_names = ['h', 's', 'd', 'c'] #columns
        self.rank_names = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'] #rows
        self.blocked_cards_names = tokens_2(blocked_cards)
        self.input_codes = input_codes.split(',')
        self.hands_list = []
        for input_code in self.input_codes:
            if len(input_code) == 3:
                if input_code[2] == 'o':
                    for color1 in self.color_names:
                        for color2 in self.color_names:
                            if color1 != color2:
                                card1 = f"{input_code[0]}{color1}"
                                card2 = f"{input_code[1]}{color2}"
                                if not (card1 in self.blocked_cards_names or card2 in self.blocked_cards_names):
                                    self.hands_list.append(f"{input_code[0]}{color1}{input_code[1]}{color2}")
                if input_code[2] == 's':
                    for color1, color2 in zip(self.color_names, self.color_names):
                        if color1 == color2:
                            card1 = f"{input_code[0]}{color1}"
                            card2 = f"{input_code[1]}{color2}"
                            if not (card1 in self.blocked_cards_names or card2 in self.blocked_cards_names):
                                self.hands_list.append(f"{input_code[0]}{color1}{input_code[1]}{color2}") 
            if len(input_code) == 2:                   
                if input_code[0] == input_code[1]:
                    card_name = input_code[0]
                    for index1 in range(len(self.color_names)):
                        for index2 in range(index1+1,len(self.color_names)):
                            if self.color_names[index1] != self.color_names[index2]:
                                card1 = f"{card_name}{self.color_names[index1]}"
                                card2 = f"{card_name}{self.color_names[index2]}"
                                if not (card1 in self.blocked_cards_names or card2 in self.blocked_cards_names):
                                    self.hands_list.append(f"{input_code[0]}{self.color_names[index1]}{input_code[1]}{self.color_names[index2]}")

def code_range(input_codes):
    rank_names = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'] #rows
    input_codes = input_codes.split(',')
    output = ''
    for input_code in input_codes:
        if len(input_code) == 4 and input_code[3] == '+':
            high_name = input_code[0]
            low_name = input_code[1]
            high_index = rank_names.index(high_name)
            low_index = rank_names.index(low_name)
            for index in range(low_index, high_index):
                output = output + f"{rank_names[high_index]}{rank_names[index]}{input_code[2]},"
        if len(input_code) == 3 and input_code[2] == '+':
            if input_code[0] == input_code[1]:
                pair_name = input_code[0]
                pair_index = rank_names.index(pair_name)
                for index in range(pair_index, 13):
                    output = output + f"{rank_names[index]}{rank_names[index]},"
            if input_code[0] != input_code[1]:
                high_name = input_code[0]
                low_name = input_code[1]
                high_index = rank_names.index(high_name)
                low_index = rank_names.index(low_name)
                for index in range(low_index, high_index):
                    output = output + f"{rank_names[high_index]}{rank_names[index]}o,{rank_names[high_index]}{rank_names[index]}s,"
        if len(input_code) == 3 and input_code[2] != '+':
            output = output + input_code + ','
        if len(input_code) == 2:
            if input_code[0] == input_code[1]:
                output = output + f"{input_code[0]}{input_code[0]},"
            if input_code[0] != input_code[1]:
                output = output + f"{input_code[0]}{input_code[1]}s,{input_code[0]}{input_code[1]}o,"

    return output[0:-1]

def check_straights(cards):
    array = cards.card_array
    rank_sum = np.sum(array, axis=1) #asis 1 - suma po rankach #axis 0 suma po kolorach
    for n in range(-1, 10):
        is_straight = True
        for m in range(0, 5):
            if rank_sum[(n+m)%13] < 1:
                is_straight = False
                break
        if is_straight == True:
            if n != -1:
                if max(np.sum(array[n:n+5,:],axis = 0)) == 5:
                    return "straight flush", [n+4]
            elif max(np.sum(np.vstack((array[0:0+4,:], array[12,:])), axis=0)) == 5:
                return "straight flush", [3]
            else:
                return "straight", [n+4]
    return None, None

def check_above_straight(cards):
    array = cards.card_array
    rank_sum = np.sum(array, axis=1) #asis 1 - suma po rankach #axis 0 suma po kolorach
    color_sum = np.sum(array, axis=0)
    if max(rank_sum) == 4:
        quad_index = np.where(rank_sum == 4)[0][0]
        rank_sum[quad_index] = 0
        return "quads", [quad_index, max(np.where(rank_sum > 0)[0])]
    elif np.size(np.where(rank_sum >= 3)[0]) >= 1 and np.size(np.where(rank_sum >= 2)[0]) >= 2:
        index_of_highest_trips = max(np.where(rank_sum >= 3)[0])
        rank_sum[index_of_highest_trips] = 0
        return "full house", [index_of_highest_trips, max(np.where(rank_sum >= 2)[0])]
    elif max(color_sum) >= 5:
        # print('------------------flush-----------------')
        # print(array)
        # print(rank_sum)
        # print(color_sum)
        color_index = np.where(color_sum >= 5)[0]
        # print(color_index)
        index_of_flush = np.where(array[:,color_index] == 1)[0]
        # print(index_of_flush)
        index_of_flush = np.sort(index_of_flush)[::-1]
        # print(index_of_flush)
        return "flush" , [index_of_flush[0], index_of_flush[1], index_of_flush[2], index_of_flush[3], index_of_flush[4]]
    else:
        return None, None
    
def check_below_straight(cards):
    array = cards.card_array
    rank_sum = np.sum(array, axis=1) #asis 1 - suma po rankach #axis 0 suma po kolorach
    color_sum = np.sum(array, axis=0)
    if max(rank_sum) == 3:
        trips_index = max(np.where(rank_sum == 3)[0])
        high_index = np.where(rank_sum == 1)[0]
        high_index = np.sort(high_index)[::-1]
        return "trips", [trips_index, high_index[0], high_index[1]]
    elif np.size(np.where(rank_sum == 2)[0]) >= 2:
        pair_index = np.where(rank_sum == 2)[0]
        pair_index = np.sort(pair_index)[::-1]
        out1 = pair_index[0]
        out2 = pair_index[1]
        rank_sum[out1] = 0
        rank_sum[out2] = 0
        high_index = np.where(rank_sum >= 1)[0]
        return "two pairs", [out1, out2, max(high_index)]
    elif np.size(np.where(rank_sum == 2)[0]) == 1:
        #print(array)
        pair_index = np.where(rank_sum == 2)[0][0]
        high_index = np.where(rank_sum == 1)[0]
        high_index = np.sort(high_index)[::-1]
        #print(high_index)
        return "pair", [pair_index, high_index[0], high_index[1], high_index[2]]
    else:
        #print(array)
        high_index = np.where(rank_sum == 1)[0]
        high_index = np.sort(high_index)[::-1]
        #print(high_index)
        return "high card", [high_index[0], high_index[1], high_index[2], high_index[3], high_index[4]]

comb_rank = {"high card" : 0, "pair" : 1, "two pairs" : 2, "trips" : 3, "straight" : 4, "flush" : 5, "full house" : 6, "quads" : 7, "straight flush" : 8}

def check_combo(cards):
    comb, helpers = check_straights(cards)
    comb2, helpers2 = check_above_straight(cards)
    if comb == "straight flush":
        return comb, helpers
    if comb == "straight":
        if comb2 != None:
            return comb2, helpers2
        else:
            return comb, helpers
    if comb == None:
        if comb2 != None:
            return comb2, helpers2
        comb, helpers = check_below_straight(cards)
        return comb, helpers
    
def winner(combo1, helpers1, combo2, helpers2):
    if comb_rank[combo1] == comb_rank[combo2]:
        #print(helpers1, helpers2)
        for helper1, helper2 in zip(helpers1, helpers2):
            if helper1 > helper2:
                return 1
            if helper1 < helper2:
                return -1
        return 0
    if comb_rank[combo1] > comb_rank[combo2]:
        return 1
    if comb_rank[combo1] < comb_rank[combo2]:
        return -1
    
def monte_carlo_hand(villian_hand, hero_hand = 'AhTd', board_cards = '', n =10000):
    hero = deck(hero_hand) # nie mozna tu wrzucac zablokowanych kart bo sie buguje
    villian = deck(villian_hand) # nie mozna tu wrzucac zablokowanych kart bo sie buguje
    outcome_tab = np.array([0, 0, 0])
    print(villian_hand)
    for m in range(n):
        board = deck(board_cards,(villian_hand+hero_hand))
        for l in range(5 - len(board_cards)//2):
            board.deal_random()
        hero_river = board + villian + hero*2
        villian_river = board + villian*2 + hero
        hero_combo, hero_kickers = check_combo(hero_river)
        villian_combo, villian_kickers = check_combo(villian_river)
        outcome = winner(hero_combo, hero_kickers, villian_combo, villian_kickers)
        outcome_tab[outcome+1] += 1
    return outcome_tab

if __name__ == "__main__":
    
    # hero_hand = "AhAd"
    # villian_range_code = 'ATs+,AQo+,77+,65,74o,J2s'
    # board_cards = "As7h8d"

    hero_hand = "AhTd"
    villian_range_code = 'K2+'
    board_cards = "Ks7h8d"

    # outcome_tab = np.array([0, 0, 0])
    # start = time.time()
    # hero = deck(hero_hand)
    # villian_range = player_range(input_codes=code_range(villian_range_code), blocked_cards=hero_hand+board_cards)
    # for villian_hand in villian_range.hands_list:
    #     villian = deck(villian_hand)
    #     print(villian_hand)
    #     for n in range(10000):
    #         board = deck(board_cards,(villian_hand+hero_hand))
    #         for m in range((5 - len(board_cards)//2)):
    #             board.deal_random()
    #         hero_river = board + villian + hero*2
    #         villian_river = board + villian*2 + hero
    #         hero_combo, hero_kickers = check_combo(hero_river)
    #         villian_combo, villian_kickers = check_combo(villian_river)
    #         outcome = winner(hero_combo, hero_kickers, villian_combo, villian_kickers)    
    #         outcome_tab[outcome+1] += 1
    # end = time.time()
    # print(end - start)
    # outcome_tab = outcome_tab / np.sum(outcome_tab)
    # print(outcome_tab)

    outcome_tab = np.array([0, 0, 0])
    villian_range = player_range(input_codes=code_range(villian_range_code), blocked_cards=hero_hand+board_cards)
    start = time.time()
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [executor.submit(monte_carlo_hand, villian_hand, hero_hand, board_cards) for villian_hand in villian_range.hands_list]
        for future in futures:
            outcome_tab = outcome_tab + future.result()
    end = time.time()
    print(end - start)
    outcome_tab = outcome_tab / np.sum(outcome_tab)
    print(outcome_tab)
    