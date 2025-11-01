"""
Dynamic Formation Generator
Creates formations that adapt based on ball position and game state
"""

import numpy as np

class DynamicFormation:
    """
    Generates dynamic formations based on game state
    """
    
    @staticmethod
    def generate_formation(ball_pos, play_mode_group, is_left_team, is_our_set_piece=False):
        """
        Generate a formation based on ball position and game state
        
        Args:
            ball_pos: Current ball position (x, y)
            play_mode_group: Type of play mode (kickoff, play_on, etc.)
            is_left_team: True if we are the left team
            is_our_set_piece: True if it's our set piece
            
        Returns:
            list: Formation positions for 5 players
        """
        ball_x, ball_y = ball_pos[0], ball_pos[1]
        
        # Adjust for team side
        side_multiplier = 1 if is_left_team else -1
        
        if play_mode_group == "kickoff":
            return DynamicFormation._kickoff_formation(side_multiplier)
        elif play_mode_group == "play_on":
            return DynamicFormation._dynamic_play_formation(ball_x, ball_y, side_multiplier)
        elif play_mode_group in ["free_kick", "corner_kick", "kick_in"]:
            return DynamicFormation._set_piece_formation(ball_pos, play_mode_group, side_multiplier, is_our_set_piece)
        elif play_mode_group == "goal_kick":
            return DynamicFormation._goal_kick_formation(side_multiplier, is_our_set_piece)
        else:
            return DynamicFormation._default_formation(side_multiplier)
    
    @staticmethod
    def _kickoff_formation(side_multiplier):
        """Starting kickoff formation"""
        return [
            np.array([-13.5, 0]) * [side_multiplier, 1],      # Goalkeeper
            np.array([-8, -3]) * [side_multiplier, 1],        # Left Defender
            np.array([-8, 3]) * [side_multiplier, 1],         # Right Defender
            np.array([-2, -1]) * [side_multiplier, 1],        # Left Midfielder
            np.array([-0.5, 0]) * [side_multiplier, 1],       # Center Forward (near ball)
        ]
    
    @staticmethod
    def _default_formation(side_multiplier):
        """Default balanced formation"""
        return [
            np.array([-13, 0]) * [side_multiplier, 1],        # Goalkeeper
            np.array([-9, -3]) * [side_multiplier, 1],        # Left Defender
            np.array([-9, 3]) * [side_multiplier, 1],         # Right Defender
            np.array([-3, -2]) * [side_multiplier, 1],        # Left Midfielder
            np.array([-3, 2]) * [side_multiplier, 1],         # Right Midfielder
        ]
    
    @staticmethod
    def _dynamic_play_formation(ball_x, ball_y, side_multiplier):
        """
        Dynamic formation that adapts to ball position
        """
        # Adjust ball position for team side
        ball_x_adjusted = ball_x * side_multiplier
        
        # Goalkeeper stays near goal
        goalkeeper_pos = np.array([-13.5, np.clip(ball_y * 0.3, -2, 2)]) * [side_multiplier, 1]
        
        # Defensive line
        if ball_x_adjusted > 0:
            # Ball in opponent's half - push defense forward
            defense_x = -6
        elif ball_x_adjusted > -7:
            # Ball in midfield - standard position
            defense_x = -9
        else:
            # Ball in our half - drop back
            defense_x = -11
        
        left_defender = np.array([defense_x, -3.5]) * [side_multiplier, 1]
        right_defender = np.array([defense_x, 3.5]) * [side_multiplier, 1]
        
        # Midfield positioning
        if ball_x_adjusted > 5:
            # Ball far in opponent's half - push midfield up
            midfield_x = max(ball_x_adjusted - 5, -2)
        elif ball_x_adjusted < -7:
            # Ball in our defensive third - drop midfield back
            midfield_x = max(ball_x_adjusted + 3, -8)
        else:
            # Ball in middle third
            midfield_x = ball_x_adjusted - 2
        
        # Midfielders spread based on ball position
        midfield_y_offset = 3
        if abs(ball_y) > 3:
            # Ball on the side - shift midfield towards ball
            midfield_y_center = np.clip(ball_y * 0.5, -2, 2)
        else:
            midfield_y_center = 0
        
        left_midfielder = np.array([midfield_x, midfield_y_center - midfield_y_offset]) * [side_multiplier, 1]
        right_midfielder = np.array([midfield_x, midfield_y_center + midfield_y_offset]) * [side_multiplier, 1]
        
        # One midfielder becomes a forward based on ball position
        if ball_x_adjusted > -3:
            # Attacking situation - one midfielder pushes forward
            forward_x = max(ball_x_adjusted + 2, 0)
            
            # Forward moves to support ball
            if abs(ball_y) < 3:
                forward_y = 0
            else:
                forward_y = ball_y * 0.7
            
            forward = np.array([forward_x, forward_y]) * [side_multiplier, 1]
            
            # Return with forward instead of right midfielder
            return [goalkeeper_pos, left_defender, right_defender, left_midfielder, forward]
        else:
            # Defensive situation - keep both midfielders back
            return [goalkeeper_pos, left_defender, right_defender, left_midfielder, right_midfielder]
    
    @staticmethod
    def _set_piece_formation(ball_pos, set_piece_type, side_multiplier, is_ours):
        """
        Formation for set pieces (free kicks, corners, kick-ins)
        """
        ball_x, ball_y = ball_pos[0] * side_multiplier, ball_pos[1]
        
        if is_ours:
            # Our set piece - attacking formation
            return [
                np.array([-13, 0]) * [side_multiplier, 1],                              # Goalkeeper stays back
                np.array([ball_x - 2, ball_y - 2]) * [side_multiplier, 1],              # Support left
                np.array([ball_x - 2, ball_y + 2]) * [side_multiplier, 1],              # Support right
                np.array([ball_x + 3, -1]) * [side_multiplier, 1],                      # Forward left
                np.array([ball_x + 3, 1]) * [side_multiplier, 1],                       # Forward right
            ]
        else:
            # Opponent's set piece - defensive formation
            return [
                np.array([-13.5, np.clip(ball_y * 0.4, -2, 2)]) * [side_multiplier, 1], # Goalkeeper
                np.array([-11, -2]) * [side_multiplier, 1],                             # Defender left
                np.array([-11, 2]) * [side_multiplier, 1],                              # Defender right
                np.array([-8, ball_y - 1.5]) * [side_multiplier, 1],                    # Defensive mid left
                np.array([-8, ball_y + 1.5]) * [side_multiplier, 1],                    # Defensive mid right
            ]
    
    @staticmethod
    def _goal_kick_formation(side_multiplier, is_ours):
        """Formation for goal kicks"""
        if is_ours:
            # Our goal kick - spread out for distribution
            return [
                np.array([-13, 0]) * [side_multiplier, 1],        # Goalkeeper (takes kick)
                np.array([-10, -4]) * [side_multiplier, 1],       # Wide left
                np.array([-10, 4]) * [side_multiplier, 1],        # Wide right
                np.array([-5, -2]) * [side_multiplier, 1],        # Midfielder left
                np.array([-5, 2]) * [side_multiplier, 1],         # Midfielder right
            ]
        else:
            # Opponent's goal kick - press forward
            return [
                np.array([-13, 0]) * [side_multiplier, 1],        # Goalkeeper stays back
                np.array([-7, -3]) * [side_multiplier, 1],        # Defender left
                np.array([-7, 3]) * [side_multiplier, 1],         # Defender right
                np.array([2, -2]) * [side_multiplier, 1],         # Press forward left
                np.array([2, 2]) * [side_multiplier, 1],          # Press forward right
            ]
    
    @staticmethod
    def adjust_formation_for_score(formation, score_diff):
        """
        Adjust formation based on score difference
        
        Args:
            formation: Base formation
            score_diff: Our score - opponent score
            
        Returns:
            list: Adjusted formation
        """
        adjusted_formation = []
        
        for pos in formation:
            adjusted_pos = pos.copy()
            
            if score_diff > 0:
                # Winning - slightly more defensive
                if adjusted_pos[0] > -10:
                    adjusted_pos[0] -= 1
            elif score_diff < -1:
                # Losing by 2+ - more aggressive
                if adjusted_pos[0] < 10:
                    adjusted_pos[0] += 1.5
            
            adjusted_formation.append(adjusted_pos)
        
        return adjusted_formation

