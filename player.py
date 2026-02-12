from cards import Card
class Player:
    def __init__(self, name, stack=1000):
        self.name = name
        self.stack = stack       # Total chips
        self.hand = []           # List of 2 integers (Hole Cards)
        self.current_bet = 0     # Amount bet in the CURRENT round
        self.status = "active"   # 'active', 'folded', 'allin'

    def receive_cards(self, cards):
        """Accepts a list of 2 integers [51, 12]"""
        self.hand = cards
        self.status = "active"

    def bet(self, amount):
        """
        Moves chips from stack to current_bet.
        Returns the actual amount bet (handles all-in logic).
        """
        if amount > self.stack:
            amount = self.stack  # All-in
            self.status = "allin"
        
        self.stack -= amount
        self.current_bet += amount
        return amount
    
    def reset_round(self):
        """Called after betting round ends (Flop -> Turn)."""
        self.current_bet = 0

    def reset_hand(self):
        """Called after the hand is over."""
        self.hand = []
        self.current_bet = 0
        self.status = "active" if self.stack > 0 else "bust"

    def get_action(self, game_state):
        """
        This method must be overridden by subclasses.
        game_state dictionary:
        {
            'community_cards': [1, 2, 3],
            'current_bet': 50,  # The table's highest bet
            'pot': 100,
            'min_raise': 10
        }
        """
        raise NotImplementedError("Subclasses must implement get_action")

    def __repr__(self):
        # Shows "Bot (1000 chips): [As, Kh]"
        hand_str = str([Card(c) for c in self.hand]) if self.hand else "[]"
        return f"{self.name} (${self.stack}): {hand_str}"
    

class HumanPlayer(Player):
    def get_action(self, game_state):
        # 1. Calculate how much you need to call
        to_call = game_state['current_bet'] - self.current_bet
        
        print(f"\n--- {self.name}'s Turn ---")
        print(f"Hand: {[Card(c) for c in self.hand]}")
        print(f"Community: {[Card(c) for c in game_state['community_cards']]}")
        print(f"Pot: {game_state['pot']} | To Call: {to_call} | Your Sack: ${self.stack}")
        
        while True:
            action = input("Action (f=fold, c=call/check, r=raise): ").lower()
            
            if action == 'f':
                self.status = "folded"
                return "fold", 0
            
            elif action == 'c':
                # Calling means matching the current bet
                amount = min(to_call, self.stack)
                self.bet(amount)
                return "call", amount
            
            elif action == 'r':
                # Raising logic
                try:
                    raise_amount = int(input(f"Raise amount (min {game_state['min_raise']}): "))
                    total_bet = to_call + raise_amount
                    if total_bet > self.stack:
                        print("You don't have enough chips!")
                        continue
                        
                    self.bet(total_bet)
                    return "raise", total_bet
                except ValueError:
                    print("Invalid number.")

import random

class BotPlayer(Player):
    def get_action(self, game_state):
        to_call = game_state['current_bet'] - self.current_bet
        
        # --- SIMPLE AI LOGIC PLACEHOLDER ---
        # 1. If it costs nothing to check, just check.
        if to_call == 0:
            return "check", 0
        
        # 2. Randomly decide to fold, call, or raise
        choice = random.choice(['fold', 'call', 'call', 'raise']) # biased towards calling
        
        if choice == 'fold':
            self.status = "folded"
            return "fold", 0
        
        elif choice == 'raise':
            # Simple raise logic (min raise)
            amount = to_call + game_state['min_raise']
            if amount > self.stack:
                 amount = self.stack # All in if short
            self.bet(amount)
            return "raise", amount
            
        else: # Call
            amount = min(to_call, self.stack)
            self.bet(amount)
            return "call", amount