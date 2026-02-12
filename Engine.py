import time
from cards import Deck, Card
from evaluator import HandEvaluator
from player import HumanPlayer, BotPlayer


class TexasHoldem:
    class TexasHoldem:
        def __init__(self, buy_in=1000, big_blind=20, small_blind=10):
            self.buy_in = buy_in
            self.big_blind = big_blind
            self.small_blind = small_blind
            
            # 1. Players (Dynamic)
            self.players = []  # Starts empty, use add_player()
            self.dealer_pos = 0 

            # 2. Game State
            self.pot = 0
            self.community_cards = []
            self.deck = None
            
            # 3. Transparency / Replay Log (Crucial)
            self.history = [] 

            # 4. Tools
            self.evaluator = HandEvaluator()
            

        def add_player(self, player):
            """Adds a player to the game."""
            self.players.append(player)
            
            # Log this event so the replay knows who sat down
            self.history.append({
                "action": "player_join",
                "name": player.name,
                "stack": player.stack
            })

        def start_hand(self):
            # 1. Reset for new hand
            self.pot = 0
            self.community_cards = []
            self.deck = Deck() # Shuffle
            
            # CLEAR history for the new hand (or keep appending if you want a full game log)
            # Usually, we want a "Hand History", so we clear it here.
            self.history = [] 
            
            # Log the setup
            self.history.append({
                "action": "new_hand",
                "blinds": (self.small_blind, self.big_blind),
                "dealer": self.players[self.dealer_pos].name,
                "active_players": [p.name for p in self.players if p.stack > 0]
            })

            self.dealer_pos = (self.dealer_pos + 1) % len(self.players)
            
            # 2. Determine Blinds based on Dealer Position
            # SB is 1 seat left of Dealer, BB is 2 seats left
            n = len(self.players)
            sb_pos = (self.dealer_pos + 1) % n
            bb_pos = (self.dealer_pos + 2) % n
            
            sb_player = self.players[sb_pos]
            bb_player = self.players[bb_pos]
            
            print(f"Button: {self.players[self.dealer_pos].name}")


