from flask import Flask, render_template, request, jsonify
import threading
from Engine import TexasHoldem 
from player import HumanPlayer, BotPlayer, action_queue, current_ui_state

app = Flask(__name__)

def run_game():
    # Setup the game just like the CLI
    game = TexasHoldem(buy_in=1000, big_blind=20, small_blind=10, history_print_on=True)
    
    human = HumanPlayer("Hubert", stack=1000)
    human.ui_enabled = True  # <--- Turn on the UI mode for Hubert!
    
    bot = BotPlayer("MathBot", stack=1000, evaluator=game.evaluator)
    
    game.add_player(human)
    game.add_player(bot)
    
    while human.stack > 0 and bot.stack > 0:
        game.play_hand()
        # Pause briefly before the next hand starts
        current_ui_state["status"] = "hand_over"

# Start the game loop in the background
game_thread = threading.Thread(target=run_game)
game_thread.daemon = True
game_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_state', methods=['GET'])
def get_state():
    return jsonify(current_ui_state)

@app.route('/send_action', methods=['POST'])
def send_action():
    data = request.json
    action_queue.put(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)