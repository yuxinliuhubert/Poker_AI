import time
from cards import Deck, Card
from datetime import datetime
from evaluator import HandEvaluator
from player import HumanPlayer, BotPlayer


class TexasHoldem:

    def __init__(self,history_print_on=False, buy_in=1000, big_blind=20, small_blind=10):


        self.buy_in = buy_in
        self.big_blind = big_blind
        self.small_blind = small_blind
        self.history_print_on = history_print_on
        if self.history_print_on:
            # Creates a file like: game_history_20260320_225725.txt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_filename = f"data/game_history_{timestamp}.txt"
            
            # Write a header to the new file immediately
            with open(self.log_filename, "w") as f:
                f.write(f"Poker Engine Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
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
        
    def change_blind(self,small_blind_size):
        self.small_blind = small_blind_size
        self.big_blind = 2 * small_blind_size
        print(f"Blind changed to: small: {self.small_blind}, big: {self.big_blind}")
        

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
        

        
        # 2. Move Dealer Button FIRST so the log is accurate
        self.dealer_pos = (self.dealer_pos + 1) % len(self.players)
        
        # Log the setup
        self.history.append({
            "action": "new_hand",
            "blinds": (self.small_blind, self.big_blind),
            "dealer": self.players[self.dealer_pos].name,
            "active_players": [p.name for p in self.players if p.stack > 0]
        })
        
        # 3. Determine Blinds (Fixing the Heads-Up Poker Rules!)
        n = len(self.players)
        if n == 2:
            # In Heads-Up, the Dealer IS the Small Blind
            sb_pos = self.dealer_pos
            bb_pos = (self.dealer_pos + 1) % 2
        else:
            # Standard 3+ Player rules
            sb_pos = (self.dealer_pos + 1) % n
            bb_pos = (self.dealer_pos + 2) % n
        
        sb_player = self.players[sb_pos]
        bb_player = self.players[bb_pos]
        
        print(f"Button: {self.players[self.dealer_pos].name}")

        sb_amount = sb_player.bet(self.small_blind)
        bb_amount = bb_player.bet(self.big_blind)
        
        self.pot += (sb_amount + bb_amount)
        self.current_bet = self.big_blind 
        
        print(f"{sb_player.name} posts Small Blind: ${sb_amount}")
        print(f"{bb_player.name} posts Big Blind: ${bb_amount}")
        
        self.history.append({"action": "post_blinds", "sb": sb_amount, "bb": bb_amount})

        # 4. Deal Hole Cards
        for player in self.players:
            if player.stack > 0: 
                cards = self.deck.deal(2) 
                player.receive_cards(cards)
                self.history.append({
                        "action": "hole_cards",
                        "player": player.name,
                        "cards": cards
                    })
                
        print("Cards dealt.")

        # 5. Return the index of the first player to act
        utg_pos = (bb_pos + 1) % n
        return utg_pos
    

    def play_betting_round(self, start_pos):
        """
        Executes a single round of betting (Pre-flop, Flop, Turn, or River).
        """
        # If everyone folded or went all-in on a previous street, skip betting
        players_can_act = [p for p in self.players if p.status == 'active']
        if len(players_can_act) == 0:
            return
        
        # If only 1 player can act and they've already matched the bet, skip
        if len(players_can_act) == 1:
            active_players = [p for p in self.players if p.status in ['active', 'allin']]
            # If they are facing an all-in they need to call, we still run the loop.
            # Otherwise, if no one else can act, the round is over.
            if len(active_players) == 1 or players_can_act[0].current_bet == self.current_bet:
                return

        current_pos = start_pos
        players_acted = 0
        
        print("\n--- Betting Round Starts ---")

        # The round continues until every active player has had a chance to act 
        # WITHOUT the bet being raised.
        while players_acted < len(players_can_act):
            player = self.players[current_pos]
            
            # Skip players who already folded or pushed all-in
            if player.status != 'active':
                current_pos = (current_pos + 1) % len(self.players)
                continue

            # 1. Build the state dictionary to feed the Player's get_action() method
            game_state = {
                'community_cards': self.community_cards,
                'current_bet': self.current_bet,
                'pot': self.pot,
                'min_raise': self.big_blind, # Keeping minimum raise simple for now
                'active_players': len([p for p in self.players if p.status in ['active', 'allin']]),
                'history': self.history
            }

            # 2. Ask the player for their move
            action, amount_added = player.get_action(game_state)

            if hasattr(player, 'last_thought') and player.last_thought:
                self.history.append({
                    "action": "bot_thought", 
                    "thought": player.last_thought
                })
            
            # 3. Process the move
            if action == 'fold':
                print(f"{player.name} folds.")
                self.history.append({"player": player.name, "action": "fold"})
                # We recalculate who can act since someone just dropped out
                players_can_act = [p for p in self.players if p.status == 'active']
                
            elif action in ['call', 'check']:
                verb = "checks" if amount_added == 0 else f"calls ${amount_added}"
                print(f"{player.name} {verb}.")
                self.pot += amount_added
                self.history.append({"player": player.name, "action": action, "amount": amount_added})
                players_acted += 1
                
            elif action == 'raise':
                print(f"{player.name} raises to ${player.current_bet}.")
                self.pot += amount_added
                self.current_bet = player.current_bet 
                self.history.append({"player": player.name, "action": "raise", "amount": amount_added})
                
                # --- THE CRUCIAL PART ---
                # A raise re-opens the action. Everyone else now has to respond 
                # to this new bet, so we reset the "players_acted" counter to 1 (this player).
                players_acted = 1 

            # 4. Check for early termination (everyone else folded)
            active_and_allin = [p for p in self.players if p.status in ['active', 'allin']]
            if len(active_and_allin) == 1:
                print(f"\nEveryone folded. {active_and_allin[0].name} wins the pot of ${self.pot}!")
                break 

            # Move to the next seat
            current_pos = (current_pos + 1) % len(self.players)
            
        # 5. Clean up at the end of the round
        # Reset everyone's current_bet tracker to 0 for the next street
        for p in self.players:
            p.reset_round()
        self.current_bet = 0

    def deal_community_cards(self, num_cards):
            """
            Deals a specified number of cards to the board.
            Pass in 3 for the Flop, 1 for the Turn, 1 for the River.
            """
            # 1. deal from the deck and add to the board
            new_cards = self.deck.deal(num_cards)
            self.community_cards.extend(new_cards)
            
            # 2. Log it for your history tracker
            self.history.append({
                "action": "deal_community", 
                "cards": new_cards
            })
            
            # 3. Figure out what street we are on for clean terminal output
            total_board_cards = len(self.community_cards)
            if total_board_cards == 3:
                street_name = "FLOP"
            elif total_board_cards == 4:
                street_name = "TURN"
            elif total_board_cards == 5:
                street_name = "RIVER"
            else:
                street_name = "BOARD"
                
            # 4. Print the current board state
            # Assuming Card(c) formats the integer into a readable string like "As" or "Td"
            board_str = [str(Card(c)) for c in self.community_cards]
            print(f"\n*** {street_name} *** [ {', '.join(board_str)} ]")
    
    def resolve_showdown(self):
            """
            Determines the winner(s) among remaining players and distributes the pot.
            """
            # 1. Identify players who made it to the River without folding
            showdown_players = [p for p in self.players if p.status in ['active', 'allin']]
            
            print("\n" + "="*15 + " SHOWDOWN " + "="*15)
            
            # Edge Case: If everyone else folded before the showdown, the last person standing wins
            if len(showdown_players) == 1:
                winner = showdown_players[0]
                print(f"{winner.name} wins ${self.pot} (Uncontested)")
                winner.stack += self.pot
                self.history.append({"action": "win_uncontested", "winner": winner.name, "amount": self.pot})
                self.pot = 0
                return

            # 2. Evaluate hands for all remaining players
            best_score = float('inf')
            winners = []

            for player in showdown_players:
                # Treys evaluation: Lower integer = Better hand
                score = self.evaluator.evaluate(player.hand, self.community_cards)
                
                # Translate the integer score into a readable string (e.g., "Flush", "Two Pair")
                hand_class = self.evaluator.get_rank_class(score)
                hand_string = self.evaluator.class_to_string(hand_class)
                
                # Print their hand for the terminal output
                hand_repr = [str(Card(c)) for c in player.hand]
                print(f"{player.name} shows {hand_repr} - {hand_string}")

                self.history.append({
                    "action": "showdown_hand",
                    "player": player.name,
                    "cards": player.hand,
                    "hand_class": hand_string
                })

                # Track the best (lowest) score
                if score < best_score:
                    best_score = score
                    winners = [player] # We found a new best hand, overwrite the winners list
                elif score == best_score:
                    winners.append(player) # Tied for best hand, add them to the split pot list

            # 3. Distribute the Pot
            # Split the pot evenly among however many winners there are
            win_amount = self.pot / len(winners)
            
            print("-" * 30)
            for winner in winners:
                winner.stack += win_amount
                winning_hand_name = self.evaluator.class_to_string(self.evaluator.get_rank_class(best_score))
                print(f"WINNER: {winner.name} wins ${win_amount:.1f} with {winning_hand_name}!")
                
                self.history.append({
                    "action": "showdown_win", 
                    "winner": winner.name, 
                    "amount": win_amount,
                    "score": best_score
                })

            # 4. Empty the pot for the next hand
            self.pot = 0

    def get_post_flop_start_pos(self):
            """Finds the first active player to the left of the dealer button."""
            pos = (self.dealer_pos + 1) % len(self.players)
            # Keep moving left until we find someone who hasn't folded
            while self.players[pos].status not in ['active', 'allin']:
                pos = (pos + 1) % len(self.players)
            return pos

    def is_hand_over(self):
        """Checks if everyone but one person has folded."""
        active_and_allin = [p for p in self.players if p.status in ['active', 'allin']]
        
        if len(active_and_allin) <= 1:
            # If only one person is left, they win the pot uncontested
            if len(active_and_allin) == 1:
                winner = active_and_allin[0]
                print(f"\nEveryone folded. {winner.name} wins the pot of ${self.pot}!")
                winner.stack += self.pot
                self.history.append({"action": "win_uncontested", "winner": winner.name, "amount": self.pot})
                self.pot = 0
            
            # Hand is over, clean up
            for p in self.players:
                p.reset_hand()
            return True
            
        return False

    def play_hand(self):
        """The master sequence for a single hand of Texas Hold'em."""
        
        # 1. Pre-Flop Setup & Betting
        utg_pos = self.start_hand()
        self.play_betting_round(utg_pos)
        if self.is_hand_over(): 
            return

        # 2. The Flop
        self.deal_community_cards(3)
        self.play_betting_round(self.get_post_flop_start_pos())
        if self.is_hand_over(): 
            return

        # 3. The Turn
        self.deal_community_cards(1)
        self.play_betting_round(self.get_post_flop_start_pos())
        if self.is_hand_over(): 
            return

        # 4. The River
        self.deal_community_cards(1)
        self.play_betting_round(self.get_post_flop_start_pos())
        
        # 5. The Showdown
        if not self.is_hand_over():
            self.resolve_showdown()

        self.save_history_to_file()
            
        # Clean up for the next hand
        for p in self.players:
            p.reset_hand()

    def save_history_to_file(self):
        if not self.history_print_on:
            return

        with open(self.log_filename, "a") as f: 
            f.write("\n" + "="*40 + "\n")
            f.write(f"HAND LOG\n")
            f.write("="*40 + "\n")
            
            for event in self.history:
                action = event.get('action')
                
                if action == 'new_hand':
                    f.write(f"New Hand Started. Dealer: {event['dealer']}\n")
                elif action == 'post_blinds':
                    f.write(f"Blinds Posted: SB ${event['sb']}, BB ${event['bb']}\n")
                
                # --- NEW: Write the hole cards ---
                elif action == 'hole_cards':
                    cards_str = [str(Card(c)) for c in event['cards']]
                    f.write(f"Dealt to {event['player']}: {cards_str}\n")
                    
                elif action == 'deal_community':
                    cards = [str(Card(c)) for c in event['cards']]
                    f.write(f"Board Updated: {cards}\n")
                elif action == 'fold':
                    f.write(f"{event['player']} folded.\n")
                elif action in ['call', 'check', 'raise']:
                    f.write(f"{event['player']} {action}ed for ${event.get('amount', 0)}.\n")
                    
                # Inside save_history_to_file loop:
                elif action == 'bot_thought':
                    f.write(f"  -> {event['thought']}\n")

                # --- NEW: Write the shown hands ---
                elif action == 'showdown_hand':
                    cards_str = [str(Card(c)) for c in event['cards']]
                    f.write(f"{event['player']} shows: {cards_str} ({event.get('hand_class', '')})\n")
                    
                elif action == 'showdown_win':
                    f.write(f"WINNER: {event['winner']} won ${event['amount']} at Showdown.\n")
                elif action == 'win_uncontested':
                    f.write(f"WINNER: {event['winner']} won ${event['amount']} (Everyone folded).\n")
            
            f.write("-" * 20 + "\n")


if __name__ == "__main__":
    # 1. Initialize the game engine (10/20 blinds)
    game = TexasHoldem(buy_in=1000, small_blind=10, big_blind=20,history_print_on=True)

    # 2. Create the players
    # Right now, the bot is just using the random-action stub we left in Player.py
    human = HumanPlayer("Hubert", stack=1000)
    bot = BotPlayer("MathBot", stack=1000, evaluator=game.evaluator)

    # 3. Seat them at the table
    game.add_player(human)
    game.add_player(bot)

    print("\n" + "*"*50)
    print(" Welcome to the Texas Hold'em Test Arena! ")
    print(f" Playing against {bot.name}. Blinds: {game.small_blind}/{game.big_blind} ")
    print("*"*50)

    # 4. The Infinite Poker Loop
    hand_number = 1
    while human.stack > 0 and bot.stack > 0:
        print(f"\n" + "="*40)
        print(f"--- STARTING HAND #{hand_number} ---")
        print(f"Stacks: {human.name} (${human.stack}) | {bot.name} (${bot.stack})")
        print("="*40)
        
        # Execute the master sequence we just built
        game.play_hand()
        
        # Check if anyone got felted
        if human.stack <= 0:
            print(f"\nYou are out of chips! {bot.name} wins the match.")
            break
        elif bot.stack <= 0:
            print(f"\n{bot.name} is out of chips! You win the match!")
            break
            
        # Pause before dealing the next hand
        play_on = input("\nDeal another hand? (y/n): ").lower()
        if play_on != 'y':
            break
            
        hand_number += 1

    print("\nThanks for playing! Test session ended.")