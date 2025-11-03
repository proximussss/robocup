import math
import numpy as np
from math_ops.Math_Ops import Math_Ops as M



class Strategy():
    def __init__(self, world):
        self.play_mode = world.play_mode
        self.robot_model = world.robot  
        self.my_head_pos_2d = self.robot_model.loc_head_position[:2]
        self.player_unum = self.robot_model.unum
        self.mypos = (world.teammates[self.player_unum-1].state_abs_pos[0],world.teammates[self.player_unum-1].state_abs_pos[1])
       
        self.side = 1
        if world.team_side_is_left:
            self.side = 0

        self.teammate_positions = [teammate.state_abs_pos[:2] if teammate.state_abs_pos is not None 
                                    else None
                                    for teammate in world.teammates
                                    ]
        
        self.opponent_positions = [opponent.state_abs_pos[:2] if opponent.state_abs_pos is not None 
                                    else None
                                    for opponent in world.opponents
                                    ]



        

        self.team_dist_to_ball = None
        self.team_dist_to_oppGoal = None
        self.opp_dist_to_ball = None

        self.prev_important_positions_and_values = None
        self.curr_important_positions_and_values = None
        self.point_preferences = None
        self.combined_threat_and_definedPositions = None


        self.my_ori = self.robot_model.imu_torso_orientation
        self.ball_2d = world.ball_abs_pos[:2]
        self.ball_vec = self.ball_2d - self.my_head_pos_2d
        self.ball_dir = M.vector_angle(self.ball_vec)
        self.ball_dist = np.linalg.norm(self.ball_vec)
        self.ball_sq_dist = self.ball_dist * self.ball_dist # for faster comparisons
        self.ball_speed = np.linalg.norm(world.get_ball_abs_vel(6)[:2])
        
        self.goal_dir = M.target_abs_angle(self.ball_2d,(15.05,0))

        self.PM_GROUP = world.play_mode_group

        self.slow_ball_pos = world.get_predicted_ball_pos(0.5) # predicted future 2D ball position when ball speed <= 0.5 m/s

        # list of squared distances between teammates (including self) and slow ball (sq distance is set to 1000 in some conditions)
        self.teammates_ball_sq_dist = [np.sum((p.state_abs_pos[:2] - self.slow_ball_pos) ** 2)  # squared distance between teammate and ball
                                  if p.state_last_update != 0 and (world.time_local_ms - p.state_last_update <= 360 or p.is_self) and not p.state_fallen
                                  else 1000 # force large distance if teammate does not exist, or its state info is not recent (360 ms), or it has fallen
                                  for p in world.teammates ]

        # list of squared distances between opponents and slow ball (sq distance is set to 1000 in some conditions)
        self.opponents_ball_sq_dist = [np.sum((p.state_abs_pos[:2] - self.slow_ball_pos) ** 2)  # squared distance between teammate and ball
                                  if p.state_last_update != 0 and world.time_local_ms - p.state_last_update <= 360 and not p.state_fallen
                                  else 1000 # force large distance if opponent does not exist, or its state info is not recent (360 ms), or it has fallen
                                  for p in world.opponents ]

        self.min_teammate_ball_sq_dist = min(self.teammates_ball_sq_dist)
        self.min_teammate_ball_dist = math.sqrt(self.min_teammate_ball_sq_dist)   # distance between ball and closest teammate
        self.min_opponent_ball_dist = math.sqrt(min(self.opponents_ball_sq_dist)) # distance between ball and closest opponent

        self.active_player_unum = self.teammates_ball_sq_dist.index(self.min_teammate_ball_sq_dist) + 1

        self.my_desired_position = self.mypos
        self.my_desired_orientation = self.ball_dir


    def GenerateTeamToTargetDistanceArray(self, target, world):
        for teammate in world.teammates:
            pass
        

    def IsFormationReady(self, point_preferences):
        """
        Check if formation is ready. More lenient threshold for faster play.
        """
        is_formation_ready = True
        for i in range(1, 6):
            if i != self.active_player_unum: 
                teammate_pos = self.teammate_positions[i-1]

                if not teammate_pos is None:
                    distance = np.sum((teammate_pos - point_preferences[i]) **2)
                    if(distance > 0.5):  # More lenient threshold (was 0.3)
                        is_formation_ready = False

        return is_formation_ready
    
    def GetOptimalDefensivePosition(self, ball_pos, my_unum, teammate_positions, opponent_positions):
        """
        Calculate optimal defensive position when not active player.
        Balances formation position with ball pressure.
        
        Args:
            ball_pos: Current ball position
            my_unum: Uniform number of this player
            teammate_positions: List of teammate positions
            opponent_positions: List of opponent positions
            
        Returns:
            tuple: (target_position, orientation)
        """
        # Get formation position
        from formation.Formation import GenerateBasicFormation
        from strategy.Assignment import role_assignment
        formation_positions = GenerateBasicFormation()
        point_preferences = role_assignment(teammate_positions, formation_positions)
        formation_pos = point_preferences.get(my_unum, self.mypos)
        
        # If ball is in our half and close, apply defensive pressure
        ball_arr = np.array(ball_pos)
        my_pos_arr = np.array(self.mypos)
        dist_to_ball = np.linalg.norm(my_pos_arr - ball_arr)
        
        # If ball is in defensive third, move slightly toward ball
        if ball_arr[0] < -5.0 and dist_to_ball < 8.0:
            # Move toward ball but stay between ball and goal
            defensive_offset = (ball_arr - my_pos_arr) * 0.3  # 30% toward ball
            target_pos = formation_pos + defensive_offset
            # Keep in formation bounds
            target_pos[0] = max(-14.5, min(target_pos[0], 5.0))
            target_pos[1] = np.clip(target_pos[1], -10, 10)
        else:
            target_pos = formation_pos
        
        # Face the ball or goal direction
        if dist_to_ball < 6.0:
            orientation = self.GetDirectionRelativeToMyPositionAndTarget(ball_pos)
        else:
            orientation = self.GetDirectionRelativeToMyPositionAndTarget(target_pos)
        
        return target_pos, orientation

    def GetDirectionRelativeToMyPositionAndTarget(self,target):
        target_vec = target - self.my_head_pos_2d
        target_dir = M.vector_angle(target_vec)

        return target_dir

    def EvaluatePassSafety(self, passer_pos, receiver_pos, opponent_positions, min_safe_distance=1.5):
        """
        Evaluate how safe a pass is by checking if opponents can intercept it.
        
        Args:
            passer_pos: Position of the player making the pass
            receiver_pos: Position of the intended receiver
            opponent_positions: List of opponent positions
            min_safe_distance: Minimum distance opponents should be from pass line
            
        Returns:
            float: Safety score (0-1, where 1 is safest)
        """
        if receiver_pos is None:
            return 0.0
        
        passer_pos = np.array(passer_pos)
        receiver_pos = np.array(receiver_pos)
        pass_dir = receiver_pos - passer_pos
        pass_length = np.linalg.norm(pass_dir)
        
        if pass_length < 0.1:
            return 0.0
        
        pass_dir_normalized = pass_dir / pass_length
        
        # Check each opponent's distance to the pass line
        min_opponent_dist_to_pass = float('inf')
        for opp_pos in opponent_positions:
            if opp_pos is None:
                continue
            
            opp_pos = np.array(opp_pos)
            # Distance from opponent to pass line segment
            dist_to_pass = M.distance_point_to_segment(opp_pos, passer_pos, receiver_pos)
            
            # Check if opponent is near the pass path (within reasonable interception distance)
            # Consider opponents that are close to the pass line and could potentially intercept
            opp_to_passer = opp_pos - passer_pos
            
            # Check if opponent is between or near the pass segment
            dot_passer = np.dot(opp_to_passer, pass_dir_normalized)
            
            # If opponent is in the general direction of the pass (extended range for safety)
            if -2.0 < dot_passer < pass_length + 2.0:  # Extended range to catch nearby opponents
                # Only consider if opponent is close enough to actually intercept
                if dist_to_pass < 3.0:  # Reasonable interception distance
                    min_opponent_dist_to_pass = min(min_opponent_dist_to_pass, dist_to_pass)
        
        # Safety score: closer to 1 if opponents are far from pass line
        if min_opponent_dist_to_pass == float('inf'):
            return 1.0
        
        safety_score = min(1.0, min_opponent_dist_to_pass / min_safe_distance)
        return max(0.0, safety_score)

    def EvaluateTeammatePosition(self, teammate_pos, ball_pos, goal_pos=(15, 0), passer_pos=None):
        """
        Evaluate the quality of a teammate's position for receiving a pass.
        Considers: distance to goal, forward position, field position, advancement from ball.
        
        Args:
            teammate_pos: Position of the teammate
            ball_pos: Current ball position
            goal_pos: Position of opponent goal
            passer_pos: Position of passer (for advancement calculation)
            
        Returns:
            float: Position quality score (0-1, where 1 is best)
        """
        if teammate_pos is None:
            return 0.0
        
        teammate_pos = np.array(teammate_pos)
        ball_pos = np.array(ball_pos)
        goal_pos = np.array(goal_pos)
        
        # Forward position bonus (being closer to opponent goal is better) - MORE WEIGHT
        forward_score = max(0.0, (teammate_pos[0] + 15) / 30.0)  # Normalize from -15 to 15
        
        # Advancement bonus: prioritize teammates who are forward of the ball
        if passer_pos is not None:
            passer_pos = np.array(passer_pos)
            advancement = teammate_pos[0] - passer_pos[0]  # Positive means forward
            advancement_score = max(0.0, min(1.0, (advancement + 15) / 30.0))
        else:
            advancement_score = forward_score
        
        # Distance to goal (closer to goal is better)
        dist_to_goal = np.linalg.norm(teammate_pos - goal_pos)
        goal_distance_score = max(0.0, 1.0 - (dist_to_goal / 25.0))  # Reduced max distance
        
        # Field width position (slightly off-center can be good for wide passes)
        # But center is still valuable
        abs_y = abs(teammate_pos[1])
        if abs_y < 3.0:  # Center is good
            width_score = 1.0
        elif abs_y < 7.0:  # Wide but acceptable
            width_score = 0.7
        else:
            width_score = 0.3  # Too wide
        
        # Combined score (prioritize forward advancement)
        position_score = 0.4 * advancement_score + 0.3 * forward_score + 0.2 * goal_distance_score + 0.1 * width_score
        
        return position_score

    def EvaluatePassToTeammate(self, passer_pos, receiver_unum, teammate_positions, opponent_positions, ball_pos):
        """
        Evaluate the overall quality of passing to a specific teammate.
        Optimized for aggressive forward play.
        
        Args:
            passer_pos: Position of the player making the pass
            receiver_unum: Uniform number of potential receiver (1-5)
            teammate_positions: List of all teammate positions
            opponent_positions: List of all opponent positions
            ball_pos: Current ball position
            
        Returns:
            float: Pass quality score (0-1, where 1 is best pass)
        """
        if receiver_unum < 1 or receiver_unum > 5:
            return 0.0
        
        receiver_pos = teammate_positions[receiver_unum - 1]
        if receiver_pos is None:
            return 0.0
        
        passer_pos = np.array(passer_pos)
        receiver_pos = np.array(receiver_pos)
        
        # Safety score (opponent interference) - critical but allow some risk for good positions
        safety_score = self.EvaluatePassSafety(passer_pos, receiver_pos, opponent_positions)
        
        # Position quality score (with advancement bonus)
        position_score = self.EvaluateTeammatePosition(receiver_pos, ball_pos, goal_pos=(15, 0), passer_pos=passer_pos)
        
        # Pass distance - prefer medium to long forward passes
        pass_distance = np.linalg.norm(receiver_pos - passer_pos)
        if pass_distance < 0.8:
            distance_score = pass_distance / 0.8  # Too close
        elif pass_distance < 2.0:
            distance_score = 0.8  # Short pass
        elif pass_distance <= 10.0:
            distance_score = 1.0  # Good medium pass
        elif pass_distance <= 15.0:
            distance_score = max(0.7, 1.0 - (pass_distance - 10.0) / 10.0)  # Long but acceptable
        else:
            distance_score = 0.5  # Very long - risky
        
        # Angle bonus: prefer passes forward
        pass_dir = receiver_pos - passer_pos
        if pass_dir[0] > 0:  # Forward pass
            forward_bonus = 1.0
        elif pass_dir[0] > -2.0:  # Lateral pass
            forward_bonus = 0.7
        else:  # Backward pass
            forward_bonus = 0.4
        
        # Safety threshold: if safety is too low, heavily penalize
        if safety_score < 0.3:
            safety_multiplier = 0.3  # Heavy penalty for unsafe passes
        elif safety_score < 0.6:
            safety_multiplier = 0.7
        else:
            safety_multiplier = 1.0
        
        # Combined score - prioritize safe forward passes
        pass_score = (0.4 * safety_score * safety_multiplier + 
                      0.35 * position_score + 
                      0.15 * distance_score + 
                      0.1 * forward_bonus)
        
        return pass_score

    def EvaluateShootingOpportunity(self, shooter_pos, ball_pos, goal_pos=(15, 0), goal_width=2.02, opponent_positions=None):
        """
        Evaluate if shooting at the goal is a good opportunity.
        More aggressive - shoot more often when in good positions.
        
        Args:
            shooter_pos: Position of the player
            ball_pos: Current ball position
            goal_pos: Center of opponent goal (x, y)
            goal_width: Width of the goal in meters
            opponent_positions: List of opponent positions (for obstacle checking)
            
        Returns:
            tuple: (shoot_score, target_position)
                shoot_score: Quality score (0-1, where 1 is best shot)
                target_position: Best target point in goal (x, y)
        """
        shooter_pos = np.array(shooter_pos)
        ball_pos = np.array(ball_pos)
        goal_pos = np.array(goal_pos)
        
        # Distance to goal
        dist_to_goal = np.linalg.norm(shooter_pos - goal_pos)
        
        # Calculate angle to goalposts
        goal_left = np.array([goal_pos[0], goal_pos[1] - goal_width/2])
        goal_right = np.array([goal_pos[0], goal_pos[1] + goal_width/2])
        
        vec_to_left = goal_left - shooter_pos
        vec_to_right = goal_right - shooter_pos
        angle_to_left = M.vector_angle(vec_to_left)
        angle_to_right = M.vector_angle(vec_to_right)
        
        goal_angle = abs(M.normalize_deg(angle_to_right - angle_to_left))
        
        # Shooting score based on distance and angle - MORE AGGRESSIVE
        # Closer is MUCH better
        if dist_to_goal < 8.0:
            distance_score = 1.0  # Very close - excellent
        elif dist_to_goal < 12.0:
            distance_score = 0.9  # Close - very good
        elif dist_to_goal < 18.0:
            distance_score = 0.7  # Medium - good
        else:
            distance_score = max(0.0, 1.0 - (dist_to_goal - 18.0) / 15.0)  # Far but still possible
        
        # Wider angle is better (more goal to aim at)
        angle_score = min(1.0, goal_angle / 20.0)  # More sensitive to angle
        
        # Forward position (being in front of goal is better)
        # Bonus if in opponent half
        if shooter_pos[0] > 0:
            forward_score = 0.9 + 0.1 * min(1.0, shooter_pos[0] / 15.0)  # In opponent half
        else:
            forward_score = max(0.3, (shooter_pos[0] + 15) / 30.0)  # Our half
        
        # Check for opponents blocking shot
        blocking_score = 1.0
        if opponent_positions is not None:
            min_blocking_dist = float('inf')
            for opp_pos in opponent_positions:
                if opp_pos is None:
                    continue
                opp_pos = np.array(opp_pos)
                # Check if opponent is between shooter and goal
                dist_to_shot_line = M.distance_point_to_segment(opp_pos, shooter_pos, goal_pos)
                vec_to_opp = opp_pos - shooter_pos
                vec_to_goal = goal_pos - shooter_pos
                if np.dot(vec_to_opp, vec_to_goal) > 0:  # Opponent in front
                    if dist_to_shot_line < 2.0:  # Close to shot line
                        min_blocking_dist = min(min_blocking_dist, dist_to_shot_line)
            
            if min_blocking_dist < float('inf'):
                blocking_score = min(1.0, min_blocking_dist / 2.0)
        
        # Combined score - prioritize distance and angle
        shoot_score = (0.4 * distance_score + 
                      0.3 * angle_score + 
                      0.2 * forward_score + 
                      0.1 * blocking_score)
        
        # Optimize target: aim at corner if far, center if close
        if dist_to_goal > 12.0:
            # Far shot - aim at a corner (alternate based on position)
            if shooter_pos[1] > 0:
                target_position = np.array([goal_pos[0], goal_pos[1] - 0.8])  # Lower corner
            else:
                target_position = np.array([goal_pos[0], goal_pos[1] + 0.8])  # Upper corner
        else:
            # Close shot - aim center
            target_position = goal_pos
        
        return shoot_score, target_position

    def SelectBestPassTarget(self, passer_unum, passer_pos, teammate_positions, opponent_positions, ball_pos):
        """
        Select the best teammate to pass to based on evaluation scores.
        Lower threshold for more aggressive passing.
        
        Args:
            passer_unum: Uniform number of the player making the pass (1-5)
            passer_pos: Position of the player making the pass
            teammate_positions: List of all teammate positions
            opponent_positions: List of all opponent positions
            ball_pos: Current ball position
            
        Returns:
            tuple: (best_receiver_unum, best_receiver_pos, pass_score)
                None if no good pass is available
        """
        best_receiver_unum = None
        best_receiver_pos = None
        best_score = 0.0
        
        for unum in range(1, 6):
            if unum == passer_unum:
                continue  # Don't pass to self
            
            pass_score = self.EvaluatePassToTeammate(
                passer_pos, unum, teammate_positions, opponent_positions, ball_pos
            )
            
            if pass_score > best_score:
                best_score = pass_score
                best_receiver_unum = unum
                best_receiver_pos = teammate_positions[unum - 1]
        
        # Lower threshold for more aggressive play - accept more passes
        if best_score > 0.25:  # Lowered from 0.3
            return best_receiver_unum, best_receiver_pos, best_score
        else:
            return None, None, 0.0

    def ShouldShootOrPass(self, shooter_unum, shooter_pos, ball_pos, teammate_positions, opponent_positions, shoot_threshold=0.4):
        """
        Decide whether to shoot at goal or pass to a teammate.
        More aggressive - shoot more often, especially when close.
        
        Args:
            shooter_unum: Uniform number of the player (1-5)
            shooter_pos: Position of the player
            ball_pos: Current ball position
            teammate_positions: List of all teammate positions
            opponent_positions: List of all opponent positions
            shoot_threshold: Minimum shooting score to choose shooting over passing
            
        Returns:
            tuple: (action_type, target)
                action_type: 'shoot' or 'pass'
                target: Target position (goal position or teammate position)
                receiver_unum: If action is 'pass', the receiver unum, otherwise None
        """
        shooter_pos_arr = np.array(shooter_pos)
        dist_to_goal = np.linalg.norm(shooter_pos_arr - np.array([15, 0]))
        
        # Evaluate shooting opportunity with opponent awareness
        shoot_score, shoot_target = self.EvaluateShootingOpportunity(
            shooter_pos, ball_pos, goal_pos=(15, 0), opponent_positions=opponent_positions
        )
        
        # Evaluate best pass
        best_receiver_unum, best_receiver_pos, pass_score = self.SelectBestPassTarget(
            shooter_unum, shooter_pos, teammate_positions, opponent_positions, ball_pos
        )
        
        # Adaptive shoot threshold based on distance
        # Very close to goal - shoot almost always
        if dist_to_goal < 6.0:
            adaptive_threshold = 0.2  # Very low - shoot aggressively
        elif dist_to_goal < 10.0:
            adaptive_threshold = 0.35
        elif dist_to_goal < 15.0:
            adaptive_threshold = shoot_threshold
        else:
            adaptive_threshold = min(0.6, shoot_threshold + 0.1)  # Slightly higher for far shots
        
        # Decision logic: prioritize shooting when close, passing when far
        # Shoot if: close to goal OR shoot score is good and better than pass
        if dist_to_goal < 8.0:
            # Very close - shoot unless pass is significantly better
            if pass_score > shoot_score + 0.2 and best_receiver_unum is not None:
                return 'pass', best_receiver_pos, best_receiver_unum
            else:
                return 'shoot', shoot_target, None
        elif shoot_score >= adaptive_threshold:
            # Good shot opportunity
            if shoot_score >= pass_score * 0.9:  # Shoot if comparable or better
                return 'shoot', shoot_target, None
            elif best_receiver_unum is not None and pass_score > 0.3:
                return 'pass', best_receiver_pos, best_receiver_unum
            else:
                return 'shoot', shoot_target, None
        elif best_receiver_unum is not None and pass_score > 0.25:
            # Good pass available
            return 'pass', best_receiver_pos, best_receiver_unum
        elif shoot_score > 0.15 or dist_to_goal < 12.0:
            # Fallback: shoot if reasonable opportunity or relatively close
            return 'shoot', shoot_target, None
        else:
            # Last resort: try pass or shoot
            if best_receiver_unum is not None:
                return 'pass', best_receiver_pos, best_receiver_unum
            else:
                return 'shoot', (15, 0), None
    
