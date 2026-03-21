from treys import Evaluator as TreysEvaluator
from treys import Card as TreysCard
import random

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
        """Returns ONLY the integer score for speed (Lower is better)."""
        t_hole = [self.map[c] for c in hole_cards]
        t_board = [self.map[c] for c in community_cards]
        return self.engine.evaluate(t_hole, t_board)
    
    # --- NEW: Added these to fix the Engine.py AttributeErrors ---
    def get_rank_class(self, score):
        return self.engine.get_rank_class(score)

    def class_to_string(self, rank_class):
        return self.engine.class_to_string(rank_class)

import random

def get_win_probability(self, player_num, hole_cards, community_cards, max_sims=10000):
        """
        Calculates probabilities with early stopping for performance optimization.
        """
        visible_cards = set(hole_cards + community_cards)
        deck_remainder = [c for c in range(52) if c not in visible_cards]
        
        wins = 0
        ties = 0
        losses = 0 
        total_equity = 0.0 
        
        num_opponents = player_num - 1 
        
        # --- NEW: Convergence tracking variables ---
        check_interval = 500  # Check for convergence every 500 hands
        tolerance = 0.005     # Stop if equity changes by less than 0.5%
        last_equity = 0.0
        actual_sims_run = 0   # Track how many we actually needed
        
        for i in range(1, max_sims + 1):
            actual_sims_run = i
            random.shuffle(deck_remainder)
            cards_needed = 5 - len(community_cards)
            sim_board = community_cards + deck_remainder[:cards_needed]
            
            my_score = self.evaluate(hole_cards, sim_board)
            best_opp_score = float('inf') 
            opp_tie_count = 0 
            
            for j in range(num_opponents):
                start_idx = cards_needed + (j * 2)
                opp_hole = deck_remainder[start_idx : start_idx + 2]
                opp_score = self.evaluate(opp_hole, sim_board)
                
                if opp_score < best_opp_score:
                    best_opp_score = opp_score
                    opp_tie_count = 1 
                elif opp_score == best_opp_score:
                    opp_tie_count += 1 
            
            if my_score < best_opp_score: 
                wins += 1
                total_equity += 1.0 
            elif my_score == best_opp_score:
                ties += 1
                total_equity += 1.0 / (1 + opp_tie_count) 
            else:
                losses += 1 
                
            # --- NEW: Early Stopping Logic ---
            if i % check_interval == 0:
                current_equity = total_equity / i
                # If the difference between this check and the last check is tiny, stop early!
                if abs(current_equity - last_equity) < tolerance:
                    break # We converged! Escape the loop.
                last_equity = current_equity
                
        # Final Calculations (using actual_sims_run instead of max_sims)
        return {
            'win': wins / actual_sims_run,
            'tie': ties / actual_sims_run,
            'loss': losses / actual_sims_run,
            'equity': total_equity / actual_sims_run,
            'sims_run': actual_sims_run # Optional: Good for debugging to see how much time you saved
        }
    

# dsd = HandEvaluator()