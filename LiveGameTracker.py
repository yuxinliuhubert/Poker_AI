class LiveSeat:
    def __init__(self, seat_number, is_hero=False):
        self.seat_number = seat_number
        self.is_hero = is_hero
        self.status = "active" # active, folded, allin
        self.stack = 0
        self.current_bet = 0
        self.hole_cards = [] # Will only be populated for Hero, or Villains at showdown

class LivePokerTracker:
    def __init__(self, num_players, hero_seat_index):
        self.seats = [LiveSeat(i, is_hero=(i == hero_seat_index)) for i in range(num_players)]
        self.hero = self.seats[hero_seat_index]
        
        self.pot = 0
        self.community_cards = []
        self.current_bet = 0
        
        # This will store clean, parseable data for your future AI training
        self.hand_log = {
            "hero_cards": [],
            "board": [],
            "actions": [],
            "showdown": []
        }

    def input_hero_cards(self):
        """You type this in when the real dealer pitches you your cards."""
        cards_str = input(f"Enter Hero's hole cards (e.g., 'As Kd'): ")
        # Convert string to your Card objects here
        self.hero.hole_cards = self.parse_cards(cards_str)
        self.hand_log["hero_cards"] = cards_str

    def record_villain_action(self, seat_num):
        """Logs what an opponent did in the real world."""
        action = input(f"What did Seat {seat_num} do? (f=fold, c=call/check, r=raise): ")
        
        if action == 'f':
            self.seats[seat_num].status = "folded"
            self.hand_log["actions"].append({"seat": seat_num, "move": "fold"})
            
        elif action == 'r':
            amount = int(input("Total bet amount: "))
            self.current_bet = amount
            self.hand_log["actions"].append({"seat": seat_num, "move": "raise", "amount": amount})

    def prompt_hero_action(self):
        """
        Right now: Asks you what you want to do.
        Future: Passes self.get_game_state() to your AI Bot for a decision.
        """
        print("\n--- HERO'S TURN ---")
        # FUTURE AI HOOK: 
        # recommended_action = my_bot.get_action(self.get_game_state())
        # print(f"AI Recommends: {recommended_action}")
        
        action = input("What is your action? (f/c/r): ")
        self.hand_log["actions"].append({"seat": self.hero.seat_number, "move": action})

    def record_showdown(self):
        """Handles the mucking vs. showing logic."""
        active_seats = [s for s in self.seats if s.status in ['active', 'allin']]
        
        for seat in active_seats:
            if seat.is_hero:
                continue # We already know our cards
                
            did_show = input(f"Did Seat {seat.seat_number} show or muck? (s/m): ")
            if did_show == 's':
                cards_str = input(f"Enter Seat {seat.seat_number}'s cards: ")
                seat.hole_cards = self.parse_cards(cards_str)
                self.hand_log["showdown"].append({"seat": seat.seat_number, "cards": cards_str})
            else:
                self.hand_log["showdown"].append({"seat": seat.seat_number, "cards": "mucked"})