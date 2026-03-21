from cards import Card
import random

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
        if amount >= self.stack:
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
                try:
                    # NEW LOGIC: We ask for the TOTAL amount you want to have in front of you
                    total_target = int(input(f"New total bet (must be at least {game_state['current_bet'] + game_state['min_raise']}): "))
                    
                    # Calculate how much EXTRA you need to put in
                    amount_to_add = total_target - self.current_bet
                    
                    if total_target < game_state['current_bet'] + game_state['min_raise']:
                        print(f"Raise must be at least ${game_state['current_bet'] + game_state['min_raise']} total.")
                        continue
                        
                    if amount_to_add > self.stack:
                        print(f"You only have ${self.stack} left! Try a smaller amount or go all-in.")
                        continue
                        
                    self.bet(amount_to_add)
                    return "raise", amount_to_add
                except ValueError:
                    print("Invalid number.")



class BotPlayer(Player):
    def __init__(self, name, stack=1000, evaluator=None):
        super().__init__(name, stack)
        self.evaluator = evaluator 
        self.last_thought = ""     

    def get_action(self, game_state):
        to_call = game_state['current_bet'] - self.current_bet
        active_players = game_state.get('active_players', 2)
        
        # 1. Calculate Pot Odds
        total_pot_if_called = game_state['pot'] + to_call
        pot_odds = to_call / total_pot_if_called if total_pot_if_called > 0 else 0

        # 2. Ask the Evaluator for the Win Probability
        if self.evaluator:
            sim_results = self.evaluator.get_win_probability(
                player_num=active_players, 
                hole_cards=self.hand, 
                community_cards=game_state['community_cards']
            )
            equity = sim_results['equity']
        else:
            equity = 0.5 # Fallback if no evaluator is hooked up

        # 3. Formulate the Thought Process
        self.last_thought = (
            f"[{self.name} Math] Hand: {self.hand} | Pot Odds: {pot_odds:.1%} | Win Equity: {equity:.1%} "
            f"| Diff: {(equity - pot_odds):.1%} | # of sim: {sim_results["sims_run"]} | win: {sim_results["win"]} | tie: {sim_results["tie"]} | loss: {sim_results["loss"]}"
        )
        # print(self.last_thought) 

        # 4. Make the Decision
        if to_call == 0 and equity < 0.5:
            return "check", 0

        if equity > (pot_odds + 0.20): 
            raise_amount = to_call + game_state['min_raise']
            raise_amount += random.choice([0, game_state['min_raise'], game_state['min_raise'] * 2])
            
            if raise_amount > self.stack:
                 raise_amount = self.stack 
            
            self.bet(raise_amount)
            return "raise", raise_amount
            
        elif equity >= pot_odds:
            amount = min(to_call, self.stack)
            self.bet(amount)
            verb = "call" if amount > 0 else "check"
            return verb, amount
            
        else:
            self.status = "folded"
            return "fold", 0