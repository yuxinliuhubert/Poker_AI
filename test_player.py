from player import HumanPlayer, BotPlayer
from cards import Deck

# Setup
deck = Deck()
p1 = HumanPlayer("Hero", stack=1000)
p2 = BotPlayer("Villain", stack=1000)

# Deal cards (Integers)
p1.receive_cards(deck.deal(2))
p2.receive_cards(deck.deal(2))

# Fake Game State (Pre-flop, Villain bet 10)
game_state = {
    'community_cards': [],
    'current_bet': 10,
    'pot': 15,
    'min_raise': 10
}

# Force the Human (You) to act
print("--- TEST SCENARIO ---")
action, amount = p1.get_action(game_state)
print(f"You chose to: {action} ${amount}")
print(f"Your remaining stack: {p1.stack}")