"""
Tactical Strategies
Implements high-level tactical behaviors for attacking and defending
"""

import numpy as np
from math_ops.Math_Ops import Math_Ops as M

class TacticalStrategies:
    """
    Provides tactical decision-making for different game situations
    """
    
    def __init__(self, strategy_data, decision_maker):
        self.strategy = strategy_data
        self.decision_maker = decision_maker
        
    def get_attacking_action(self, agent):
        """
        Determine attacking action for the active player (closest to ball)
        
        Args:
            agent: The agent instance
            
        Returns:
            Action to execute (move or kick)
        """
        # Check if we should clear the ball in dangerous situations
        if self.decision_maker.should_clear_ball():
            # Clear towards opponent half
            clear_target = np.array([15, -self.strategy.ball_2d[1] * 0.5])
            return agent.kickTarget(self.strategy, self.strategy.mypos, clear_target)
        
        # Check if we should pass
        if self.decision_maker.should_pass():
            pass_target = self.decision_maker.get_best_pass_target()
            
            if pass_target is not None:
                target_unum, target_pos = pass_target
                # Lead the pass slightly ahead of teammate
                lead_target = target_pos + np.array([1.0, 0])
                agent.world.draw.line(self.strategy.ball_2d, lead_target, 3, 
                                     agent.world.draw.Color.green, "pass_target")
                return agent.kickTarget(self.strategy, self.strategy.mypos, lead_target, 
                                       enable_pass_command=True)
        
        # Otherwise, dribble towards goal or shoot
        return self._attack_goal(agent)
    
    def _attack_goal(self, agent):
        """
        Attack the goal - dribble or shoot
        
        Args:
            agent: The agent instance
            
        Returns:
            Action to execute
        """
        goal_pos = np.array([15, 0])
        ball_pos = self.strategy.ball_2d
        
        # Distance to goal
        dist_to_goal = np.linalg.norm(ball_pos - goal_pos)
        
        # If close to goal, shoot directly (use kick)
        if dist_to_goal < 8:
            # Aim for corners when far, center when close
            if dist_to_goal > 4:
                # Aim for corners
                if ball_pos[1] > 0:
                    shoot_target = np.array([15, -2])  # Far post
                else:
                    shoot_target = np.array([15, 2])   # Far post
            else:
                # Close to goal - power shot to center
                shoot_target = goal_pos
            
            agent.world.draw.line(ball_pos, shoot_target, 3,
                                 agent.world.draw.Color.red, "shoot_target")
            # Use Basic_Kick for shooting (use_dribble=False)
            return agent.kickTarget(self.strategy, self.strategy.mypos, shoot_target, use_dribble=False)
        else:
            # Far from goal - dribble forward (faster movement)
            # Dribble towards goal, avoiding center if crowded
            dribble_target = goal_pos.copy()
            
            # Check if path to goal is crowded
            opponents_in_path = self.decision_maker.count_opponents_in_radius(
                (ball_pos + goal_pos) / 2, radius=4.0)
            
            if opponents_in_path >= 2:
                # Path is crowded, dribble to the side first
                if ball_pos[1] > 0:
                    dribble_target = np.array([ball_pos[0] + 3, ball_pos[1] - 2])
                else:
                    dribble_target = np.array([ball_pos[0] + 3, ball_pos[1] + 2])
            
            agent.world.draw.line(ball_pos, dribble_target, 3,
                                 agent.world.draw.Color.orange, "dribble_target")
            # Use Dribble behavior for faster ball movement (use_dribble=True)
            return agent.kickTarget(self.strategy, self.strategy.mypos, dribble_target, use_dribble=True)
    
    def get_supporting_action(self, agent):
        """
        Determine action for supporting player (not closest to ball)
        
        Args:
            agent: The agent instance
            
        Returns:
            Action to execute (usually move)
        """
        my_formation_pos = self.strategy.my_desired_position
        ball_pos = self.strategy.ball_2d
        
        # Determine role based on position
        role = self._determine_player_role()
        
        if role == "goalkeeper":
            return self._goalkeeper_behavior(agent)
        elif role == "defender":
            return self._defender_behavior(agent, my_formation_pos)
        elif role == "midfielder":
            return self._midfielder_behavior(agent, my_formation_pos)
        elif role == "forward":
            return self._forward_behavior(agent, my_formation_pos)
        else:
            # Default: move to formation position facing ball
            return agent.move(my_formation_pos, orientation=self.strategy.ball_dir)
    
    def _determine_player_role(self):
        """
        Determine the player's role based on their formation position
        
        Returns:
            str: Role name (goalkeeper, defender, midfielder, forward)
        """
        my_pos = self.strategy.my_desired_position
        
        # Simple role determination based on x-position
        if my_pos[0] < -12:
            return "goalkeeper"
        elif my_pos[0] < -7:
            return "defender"
        elif my_pos[0] < 2:
            return "midfielder"
        else:
            return "forward"
    
    def _goalkeeper_behavior(self, agent):
        """
        Goalkeeper-specific behavior
        
        Args:
            agent: The agent instance
            
        Returns:
            Action to execute
        """
        goal_pos = np.array([-15, 0])
        ball_pos = self.strategy.ball_2d
        
        # Stay near goal but move to intercept ball trajectory
        goalkeeper_x = -13.5
        
        # Move laterally based on ball y-position
        goalkeeper_y = np.clip(ball_pos[1] * 0.4, -3, 3)
        
        goalkeeper_pos = np.array([goalkeeper_x, goalkeeper_y])
        
        # Always face the ball
        return agent.move(goalkeeper_pos, orientation=self.strategy.ball_dir)
    
    def _defender_behavior(self, agent, formation_pos):
        """
        Defender-specific behavior
        
        Args:
            agent: The agent instance
            formation_pos: Assigned formation position
            
        Returns:
            Action to execute
        """
        ball_pos = self.strategy.ball_2d
        
        # If ball is in our defensive third and close, mark it defensively
        if ball_pos[0] < -5 and self.strategy.ball_dist < 8:
            # Move between ball and goal
            defensive_pos = self.decision_maker.get_defensive_position()
            return agent.move(defensive_pos, orientation=self.strategy.ball_dir)
        else:
            # Stay in formation position
            return agent.move(formation_pos, orientation=self.strategy.ball_dir)
    
    def _midfielder_behavior(self, agent, formation_pos):
        """
        Midfielder-specific behavior
        
        Args:
            agent: The agent instance
            formation_pos: Assigned formation position
            
        Returns:
            Action to execute
        """
        ball_pos = self.strategy.ball_2d
        
        # Midfielders are more dynamic - adjust position slightly toward ball
        adjusted_pos = formation_pos + (ball_pos - formation_pos) * 0.2
        
        # But don't get too close to the active player
        if np.linalg.norm(adjusted_pos - ball_pos) < 2:
            adjusted_pos = formation_pos
        
        return agent.move(adjusted_pos, orientation=self.strategy.ball_dir)
    
    def _forward_behavior(self, agent, formation_pos):
        """
        Forward-specific behavior
        
        Args:
            agent: The agent instance
            formation_pos: Assigned formation position
            
        Returns:
            Action to execute
        """
        ball_pos = self.strategy.ball_2d
        goal_pos = np.array([15, 0])
        
        # Forwards should position for receiving passes
        # Stay ahead of ball but not offside
        if ball_pos[0] > 5:
            # Ball is far forward - stay wide and ahead
            forward_x = min(ball_pos[0] + 2, 13)
            forward_y = formation_pos[1]  # Maintain width
            
            forward_pos = np.array([forward_x, forward_y])
        else:
            # Ball is back - stay in formation but ready to run
            forward_pos = formation_pos
        
        # Face the goal when ball is behind, face ball when ball is ahead
        if ball_pos[0] < self.strategy.mypos[0]:
            orientation = M.target_abs_angle(self.strategy.mypos, goal_pos)
        else:
            orientation = self.strategy.ball_dir
        
        return agent.move(forward_pos, orientation=orientation)
    
    def get_set_piece_action(self, agent, is_our_set_piece):
        """
        Handle set piece situations
        
        Args:
            agent: The agent instance
            is_our_set_piece: True if it's our set piece
            
        Returns:
            Action to execute
        """
        if is_our_set_piece:
            # Our set piece
            if self.decision_maker.am_i_closest_to_ball():
                # I take the set piece
                # Look for best pass target or shoot
                pass_target = self.decision_maker.get_best_pass_target()
                
                if pass_target is not None and self.strategy.ball_2d[0] < 10:
                    # Pass to teammate
                    _, target_pos = pass_target
                    return agent.kickTarget(self.strategy, self.strategy.mypos, target_pos,
                                           enable_pass_command=True)
                else:
                    # Shoot at goal
                    goal_target = np.array([15, 0])
                    return agent.kickTarget(self.strategy, self.strategy.mypos, goal_target)
            else:
                # Move to position and wait
                return agent.move(self.strategy.my_desired_position, 
                                 orientation=self.strategy.ball_dir)
        else:
            # Opponent's set piece - defensive positioning
            return self._defender_behavior(agent, self.strategy.my_desired_position)

