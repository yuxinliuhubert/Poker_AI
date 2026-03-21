class Card:
    # __slots__ prevents Python from creating a dynamic dictionary for each object.
    # This saves massive memory and speeds up access time by ~20%.
    __slots__ = ('_id',)

    STR_RANKS = '23456789TJQKA'
    STR_SUITS = 'cdhs'

    # pre compute a dictionary for manual entry
    CHAR_TO_INT = {}
    for r_idx, r_char in enumerate(STR_RANKS):
        for s_idx, s_char in enumerate(STR_SUITS):
            CHAR_TO_INT[f"{r_char}{s_char}"] = r_idx * 4 + s_idx


    def __init__(self, value):
        if isinstance(value, int):
            self._id = value
        elif isinstance(value, str):
            self._id = self.CHAR_TO_INT[value] 
        else:
            raise ValueError("Invalid Card Input")
        
    @property
    def rank(self):
        return self._id // 4 

    @property
    def suit(self):
        return self._id % 4
    

    # when displaying the card, show rank and suit
    def __repr__(self):
        return f"{self.STR_RANKS[self.rank]}{self.STR_SUITS[self.suit]}"
    
    # less than
    def __lt__(self, other):
        return self._id < other._id
    
    def __eq__(self, other):
        return self._id == other._id
    


# # Test functions
# my_hand = [Card('As'), Card('2h')]
# print(my_hand) 
# print(my_hand[0] == my_hand[1])



import random
class Deck:
    def __init__(self, seed=None):
        # Create a private random generator for this specific deck instance
        self._rng = random.Random(seed)
        
       
        self.cards = list(range(52))
        self.shuffle()
        

    def shuffle(self):
        self._rng.shuffle(self.cards)

    def deal(self, n=1):
        if len(self.cards) < n:
            raise ValueError("Not enough cards")
        
        # take cards from end is faster than front
        dealt_cards = self.cards[-n:]

        # modify the deck to discard the cards
        self.cards = self.cards[:-n]

        # if n == 1:
        #     return dealt_cards[0]
        
        return dealt_cards
    
    def __len__(self):
        return len(self.cards)

