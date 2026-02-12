from treys import Evaluator as TreysEvaluator
from treys import Card as TreysCard

class HandEvaluator:
    def __init__(self):
        self.engine = TreysEvaluator()

        # precompute map to translate for speed
        # input our integer -> output treys integer

        self.map = {}
        suits = ['c', 'd', 'h', 's']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        
        for i in range(52):
            r_idx = i // 4
            s_idx = i % 4
            # Create the string 'Ah', '2c' that treys understands
            card_str = f"{ranks[r_idx]}{suits[s_idx]}"
            # Convert string to Treys Integer and save it
            self.map[i] = TreysCard.new(card_str)


    def evaluate(self, hole_cards, community_cards):
        """
        Accepts lists of 0-51 integers.
        Returns a score (Lower is better. 1 = Royal Flush).
        """
        # 1. Translate our ints to treys ints
        t_hole = [self.map[c] for c in hole_cards]
        t_board = [self.map[c] for c in community_cards]
        
        # 2. Get the score
        score = self.engine.evaluate(t_hole, t_board)
        
        # 3. Optional: Get a human-readable string like "Pair" or "Flush"
        rank_class = self.engine.get_rank_class(score)
        class_string = self.engine.class_to_string(rank_class)
        
        return score, class_string
    
    def get_win_probability(self, hole_cards, community_cards, n_sims=1000):
        """
        Calculates the % chance (0.0 to 1.0) of winning from the current state.
        
        n_sims: Higher number = more accurate, but slower. 
                1000 is usually good enough for simple bots.
        """
        # 1. Identify all cards currently visible (held or on board)
        visible_cards = set(hole_cards + community_cards)
        
        # 2. Create a "simulation deck" of all UNKNOWN cards
        # (This is why integers 0-51 are so superior - fast math)
        deck_remainder = [c for c in range(52) if c not in visible_cards]
        
        wins = 0
        ties = 0
        
        # 3. Run the simulation loop
        for _ in range(n_sims):
            # Shuffle the unknown cards (randomize the future)
            random.shuffle(deck_remainder)
            
            # Determine how many cards are needed to finish the board (Flop/Turn/River)
            cards_needed = 5 - len(community_cards)
            
            # Deal the imaginary future board
            sim_board = community_cards + deck_remainder[:cards_needed]
            
            # Deal an imaginary opponent hand (random 2 cards)
            # Note: We take from index 'cards_needed' to avoid using board cards
            opp_hole = deck_remainder[cards_needed : cards_needed+2]
            
            # 4. Who won this imaginary game?
            my_score = self.engine.evaluate(hole_cards, sim_board)
            opp_score = self.engine.evaluate(opp_hole, sim_board)
            
            if my_score < opp_score: # Lower score is better in Treys
                wins += 1
            elif my_score == opp_score:
                ties += 1
                
        # 5. Calculate Equity (Win % + half of Tie %)
        equity = (wins + (ties / 2)) / n_sims
        return equity
    