"""
Decision Maker
Implements decision-making logic for individual players
"""

import numpy as np
from math_ops.Math_Ops import Math_Ops as M

class DecisionMaker:
    """
    Makes tactical decisions for individual players
    """
    
    def __init__(self, strategy_data):
        self.strategy = strategy_data
        
    def am_i_closest_to_ball(self):
        """Check if I am the closest player to the ball"""
        return self.strategy.active_player_unum == self.strategy.player_unum
    
    def get_closest_teammate_to_position(self, position):
        """
        Find the closest teammate to a given position
        
        Args:
            position: Target position (x, y)
            
        Returns:
            int: Uniform number of closest teammate (1-5)
        """
        min_dist = float('inf')
        closest_unum = None
        
        for i, teammate_pos in enumerate(self.strategy.teammate_positions):
            if teammate_pos is not None:
                dist = np.linalg.norm(teammate_pos - position)
                if dist < min_dist:
                    min_dist = dist
                    closest_unum = i + 1
                    
        return closest_unum
    
    def is_opponent_nearby(self, threshold=2.0):
        """
        Check if any opponent is nearby
        
        Args:
            threshold: Distance threshold in meters
            
        Returns:
            bool: True if opponent is within threshold
        """
        my_pos = self.strategy.mypos
        
        for opp_pos in self.strategy.opponent_positions:
            if opp_pos is not None:
                dist = np.linalg.norm(opp_pos - my_pos)
                if dist < threshold:
                    return True
                    
        return False
    
    def count_teammates_in_radius(self, position, radius=3.0):
        """
        Count teammates within a radius of a position
        
        Args:
            position: Center position
            radius: Radius in meters
            
        Returns:
            int: Number of teammates in radius
        """
        count = 0
        for teammate_pos in self.strategy.teammate_positions:
            if teammate_pos is not None:
                dist = np.linalg.norm(teammate_pos - position)
                if dist < radius:
                    count += 1
        return count
    
    def count_opponents_in_radius(self, position, radius=3.0):
        """
        Count opponents within a radius of a position
        
        Args:
            position: Center position
            radius: Radius in meters
            
        Returns:
            int: Number of opponents in radius
        """
        count = 0
        for opp_pos in self.strategy.opponent_positions:
            if opp_pos is not None:
                dist = np.linalg.norm(opp_pos - position)
                if dist < radius:
                    count += 1
        return count
    
    def should_pass(self):
        """
        Decide if the player should pass instead of dribbling
        
        Returns:
            bool: True if should pass
        """
        # Pass if opponents are very close
        if self.strategy.min_opponent_ball_dist < 1.5:
            return True
        
        # Pass if we're far from goal and have support
        ball_to_goal_dist = np.linalg.norm(self.strategy.ball_2d - np.array([15, 0]))
        if ball_to_goal_dist > 10 and self.count_teammates_in_radius(self.strategy.ball_2d, 5) >= 2:
            return True
        
        return False
    
    def get_best_pass_target(self):
        """
        Find the best teammate to pass to
        
        Returns:
            tuple: (unum, position) of best pass target, or None if no good target
        """
        best_target = None
        best_score = -float('inf')
        
        for i, teammate_pos in enumerate(self.strategy.teammate_positions):
            unum = i + 1
            
            # Skip self
            if unum == self.strategy.player_unum:
                continue
            
            # Skip if position unknown
            if teammate_pos is None:
                continue
            
            # Calculate score based on multiple factors
            score = self._evaluate_pass_target(teammate_pos)
            
            if score > best_score:
                best_score = score
                best_target = (unum, teammate_pos)
        
        return best_target
    
    def _evaluate_pass_target(self, target_pos):
        """
        Evaluate how good a pass target is
        
        Args:
            target_pos: Position of potential pass target
            
        Returns:
            float: Score (higher is better)
        """
        score = 0.0
        
        # Prefer targets closer to opponent goal
        goal_pos = np.array([15, 0])
        dist_to_goal = np.linalg.norm(target_pos - goal_pos)
        score += (30 - dist_to_goal)  # Closer to goal is better
        
        # Penalize if target is too close or too far
        dist_to_ball = np.linalg.norm(target_pos - self.strategy.ball_2d)
        if dist_to_ball < 3:
            score -= 10  # Too close
        elif dist_to_ball > 15:
            score -= 15  # Too far
        else:
            score += 5  # Good distance
        
        # Penalize if opponents are near the target
        opponents_nearby = self.count_opponents_in_radius(target_pos, 2.0)
        score -= opponents_nearby * 5
        
        # Bonus if target is ahead of ball (offensive position)
        if target_pos[0] > self.strategy.ball_2d[0]:
            score += 8
        
        return score
    
    def should_clear_ball(self):
        """
        Decide if we should just clear the ball (defensive situation)
        
        Returns:
            bool: True if should clear
        """
        # Clear if we're in our defensive third and under pressure
        if self.strategy.ball_2d[0] < -5:
            if self.strategy.min_opponent_ball_dist < 2.0:
                return True
        
        return False
    
    def get_defensive_position(self):
        """
        Calculate defensive position based on ball and goal
        
        Returns:
            np.array: Defensive position
        """
        ball_pos = self.strategy.ball_2d
        our_goal = np.array([-15, 0])
        
        # Position between ball and goal
        direction = ball_pos - our_goal
        distance = np.linalg.norm(direction)
        
        if distance > 0:
            direction = direction / distance
            # Position 60% of the way from goal to ball
            defensive_pos = our_goal + direction * min(distance * 0.6, 10)
            return defensive_pos
        
        return our_goal + np.array([2, 0])

