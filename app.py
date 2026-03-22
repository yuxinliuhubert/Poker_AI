from flask import Flask, render_template, request, jsonify
import threading
import traceback
from Engine import TexasHoldem 
from player import HumanPlayer, BotPlayer, action_queue, current_ui_state
import player
from cards import Card 
app = Flask(__name__)
master_log = []
last_history_len = 0

def refresh_dashboard(game, human, status, show_bot_thoughts=False):
    """Reads the raw Engine state and formats it for the Web UI"""
    global master_log, last_history_len
    import player 
    from cards import Card
    
    # 1. Detect if the engine cleared its history for a new hand
    if len(game.history) < last_history_len:
        last_history_len = 0
        
    # 2. Grab ONLY the new events we haven't seen yet
    new_events = game.history[last_history_len:]
    
    for event in new_events:
        action = event.get('action')
        msg = None
        
        if action == 'new_hand':
            # Added a line break to visually separate hands!
            msg = f"<br><b>--- New Hand (Dealer: {event.get('dealer', 'Unknown')}) ---</b>"
        elif action == 'post_blinds':
            msg = f"Blinds posted: SB ${event.get('sb')}, BB ${event.get('bb')}"
        elif action == 'hole_cards':
            if event['player'] == human.name:
                cards = [str(Card(c)) for c in event['cards']]
                msg = f"Dealt to you: {cards}"
        elif action == 'deal_community':
            cards = [str(Card(c)) for c in event['cards']]
            msg = f"Board updated: {cards}"
        elif action in ['call', 'check', 'raise']:
            msg = f"{event['player']} {action}s for ${event.get('amount', 0)}."
        elif action == 'fold':
            msg = f"{event['player']} folds."
        elif action == 'bot_thought' and show_bot_thoughts:
            msg = f"MathBot: {event['thought']}"
        elif action == 'showdown_hand':
            cards = [str(Card(c)) for c in event['cards']]
            msg = f"{event['player']} shows: {cards} ({event.get('hand_class', '')})"
        elif action == 'showdown_win':
            msg = f"{event['winner']} wins ${event.get('amount')} at Showdown!"
        elif action == 'win_uncontested':
            msg = f"{event['winner']} wins ${event.get('amount')} (Uncontested)!"
            
        if msg:
            master_log.append(msg)
            
    # 3. Update the tracker for the next UI update
    last_history_len = len(game.history)
    
    # 4. Cap the log at 150 items so your browser doesn't eventually lag
    master_log = master_log[-150:]
            
    # 5. Calculate the Live Table Math
    highest_bet = max([p.current_bet for p in game.players]) if game.players else 0
    human_bet = human.current_bet if human else 0
    to_call = highest_bet - human_bet
    
    # 6. Update the global state
    player.current_ui_state.clear()
    player.current_ui_state.update({
        "status": status,
        "name": human.name,
        "hand": [str(Card(c)) for c in human.hand] if human else [],
        "board": [str(Card(c)) for c in game.community_cards],
        "pot": game.pot,
        "to_call": to_call,
        "stack": human.stack if human else 0,
        "highest_bet": highest_bet,
        "human_bet": human_bet,
        "min_raise": game.big_blind,
        "log": master_log  # Send the permanent log!
    })

def run_game():
 
    try:
        print("\n--- ENGINE THREAD STARTING ---")
        game = TexasHoldem(buy_in=1000, big_blind=20, small_blind=10, history_print_on=True)
        
        human = HumanPlayer("Hubert", stack=1000)
        human.ui_enabled = True  
        human.trigger_ui_update = lambda status: refresh_dashboard(game, human, status)
        
        bot = BotPlayer("MathBot", stack=1000, evaluator=game.evaluator)
        
        game.add_player(human)
        game.add_player(bot)
        
        while human.stack > 0 and bot.stack > 0:
            game.play_hand()
            
            refresh_dashboard(game, human, "hand_over")
            
            print("Hand over. Waiting for user to click 'Deal Next Hand'...")
            action_queue.get(block=True)
    except Exception as e:
        # --- NEW: Catch the silent crash and print it! ---
        print("\n" + "="*40)
        print("!!! BACKGROUND THREAD CRASHED !!!")
        print("="*40)
        traceback.print_exc()


# Start the game loop in the background
game_thread = threading.Thread(target=run_game)
game_thread.daemon = True
game_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_state', methods=['GET'])
def get_state():
    return jsonify(player.current_ui_state)

@app.route('/send_action', methods=['POST'])
def send_action():
    data = request.json
    action_queue.put(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)