from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

from strategy.Assignment import role_assignment 
from strategy.Strategy import Strategy 

from formation.Formation import GenerateBasicFormation


class Agent(Base_Agent):
    def __init__(self, host:str, agent_port:int, monitor_port:int, unum:int,
                 team_name:str, enable_log, enable_draw, wait_for_server=True, is_fat_proxy=False) -> None:
        
        # define robot type
        robot_type = (0,1,1,1,2,3,3,3,4,4,4)[unum-1]

        # Initialize base agent
        # Args: Server IP, Agent Port, Monitor Port, Uniform No., Robot Type, Team Name, Enable Log, Enable Draw, play mode correction, Wait for Server, Hear Callback
        super().__init__(host, agent_port, monitor_port, unum, robot_type, team_name, enable_log, enable_draw, True, wait_for_server, None)

        self.enable_draw = enable_draw
        self.state = 0  # 0-Normal, 1-Getting up, 2-Kicking
        self.kick_direction = 0
        self.kick_distance = 0
        self.fat_proxy_cmd = "" if is_fat_proxy else None
        self.fat_proxy_walk = np.zeros(3) # filtered walk parameters for fat proxy
        
        # Track kick state to prevent falling
        self.kick_in_progress = False
        self.kick_finish_time = 0
        self.last_ball_distance = float('inf')

        self.init_pos = ([-14,0],[-9,-5],[-9,0],[-9,5],[-5,-5],[-5,0],[-5,5],[-1,-6],[-1,-2.5],[-1,2.5],[-1,6])[unum-1] # initial formation


    def beam(self, avoid_center_circle=False):
        r = self.world.robot
        pos = self.init_pos[:] # copy position list 
        self.state = 0

        # Avoid center circle by moving the player back 
        if avoid_center_circle and np.linalg.norm(self.init_pos) < 2.5:
            pos[0] = -2.3 

        if np.linalg.norm(pos - r.loc_head_position[:2]) > 0.1 or self.behavior.is_ready("Get_Up"):
            self.scom.commit_beam(pos, M.vector_angle((-pos[0],-pos[1]))) # beam to initial position, face coordinate (0,0)
        else:
            if self.fat_proxy_cmd is None: # normal behavior
                self.behavior.execute("Zero_Bent_Knees_Auto_Head")
            else: # fat proxy behavior
                self.fat_proxy_cmd += "(proxy dash 0 0 0)"
                self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk


    def move(self, target_2d=(0,0), orientation=None, is_orientation_absolute=True,
             avoid_obstacles=True, priority_unums=[], is_aggressive=False, timeout=3000):
        '''
        Walk to target position

        Parameters
        ----------
        target_2d : array_like
            2D target in absolute coordinates
        orientation : float
            absolute or relative orientation of torso, in degrees
            set to None to go towards the target (is_orientation_absolute is ignored)
        is_orientation_absolute : bool
            True if orientation is relative to the field, False if relative to the robot's torso
        avoid_obstacles : bool
            True to avoid obstacles using path planning (maybe reduce timeout arg if this function is called multiple times per simulation cycle)
        priority_unums : list
            list of teammates to avoid (since their role is more important)
        is_aggressive : bool
            if True, safety margins are reduced for opponents
        timeout : float
            restrict path planning to a maximum duration (in microseconds)    
        '''
        r = self.world.robot

        if self.fat_proxy_cmd is not None: # fat proxy behavior
            self.fat_proxy_move(target_2d, orientation, is_orientation_absolute) # ignore obstacles
            return

        if avoid_obstacles:
            target_2d, _, distance_to_final_target = self.path_manager.get_path_to_target(
                target_2d, priority_unums=priority_unums, is_aggressive=is_aggressive, timeout=timeout)
        else:
            distance_to_final_target = np.linalg.norm(target_2d - r.loc_head_position[:2])

        self.behavior.execute("Walk", target_2d, True, orientation, is_orientation_absolute, distance_to_final_target) # Args: target, is_target_abs, ori, is_ori_abs, distance





    def kick(self, kick_direction=None, kick_distance=None, abort=False, enable_pass_command=False):
        '''
        Walk to ball and kick

        Parameters
        ----------
        kick_direction : float
            kick direction, in degrees, relative to the field
        kick_distance : float
            kick distance in meters
        abort : bool
            True to abort.
            The method returns True upon successful abortion, which is immediate while the robot is aligning itself. 
            However, if the abortion is requested during the kick, it is delayed until the kick is completed.
        avoid_pass_command : bool
            When False, the pass command will be used when at least one opponent is near the ball
            
        Returns
        -------
        finished : bool
            Returns True if the behavior finished or was successfully aborted.
        '''
        # NO DRIBBLING - use Basic_Kick only
        if self.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        self.kick_direction = self.kick_direction if kick_direction is None else kick_direction
        self.kick_distance = self.kick_distance if kick_distance is None else kick_distance

        if self.fat_proxy_cmd is None: # normal behavior
            return self.behavior.execute("Basic_Kick", self.kick_direction, abort) # Basic_Kick has no kick distance control
        else: # fat proxy behavior
            return self.fat_proxy_kick()


    def kickTarget(self, strategyData, mypos_2d=(0,0),target_2d=(0,0), abort=False, enable_pass_command=False):
        '''
        Walk to ball and kick

        Parameters
        ----------
        kick_direction : float
            kick direction, in degrees, relative to the field
        kick_distance : float
            kick distance in meters
        abort : bool
            True to abort.
            The method returns True upon successful abortion, which is immediate while the robot is aligning itself. 
            However, if the abortion is requested during the kick, it is delayed until the kick is completed.
        avoid_pass_command : bool
            When False, the pass command will be used when at least one opponent is near the ball
            
        Returns
        -------
        finished : bool
            Returns True if the behavior finished or was successfully aborted.
        '''

        behavior = self.behavior
        world = self.world
        robot = self.world.robot
        
        # Check if we're currently kicking - wait for completion to prevent falling
        if self.kick_in_progress:
            # Check if kick is finished by checking if ball has moved significantly
            ball_pos = world.ball_abs_pos[:2]
            my_pos = robot.loc_head_position[:2]
            current_ball_dist = np.linalg.norm(ball_pos - my_pos)
            
            # Check if ball moved away significantly (kick completed)
            if current_ball_dist > self.last_ball_distance + 0.5:
                # Ball moved - kick likely completed
                self.kick_in_progress = False
                self.kick_finish_time = world.time_local_ms
                self.state = 2  # Set state to kicking for recovery
            # Check timeout - if too long, reset
            elif world.time_local_ms - self.kick_finish_time > 2000:
                self.kick_in_progress = False
            
            # During kick recovery, maintain stability
            if self.state == 2:
                # Short recovery period after kick to maintain balance
                if world.time_local_ms - self.kick_finish_time < 300:
                    # Stabilize - execute Zero_Bent_Knees for balance
                    behavior.execute("Zero_Bent_Knees_Auto_Head")
                    return False
                else:
                    # Recovery complete
                    self.state = 0
                    return True

        # Calculate the vector from the current position to the target position
        vector_to_target = np.array(target_2d) - np.array(mypos_2d)
        
        # Calculate the distance (magnitude of the vector)
        kick_distance = np.linalg.norm(vector_to_target)
        
        # Calculate the direction (angle) in radians
        direction_radians = np.arctan2(vector_to_target[1], vector_to_target[0])
        
        # Convert direction to degrees for easier interpretation (optional)
        kick_direction = np.degrees(direction_radians)

        if strategyData.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        # Store kick direction
        self.kick_direction = kick_direction
        self.kick_distance = kick_distance
        
        # Track ball distance before kick
        ball_pos = world.ball_abs_pos[:2]
        my_pos = robot.loc_head_position[:2]
        self.last_ball_distance = np.linalg.norm(ball_pos - my_pos)

        if self.fat_proxy_cmd is None: # normal behavior
            # Execute kick
            kick_result = self.behavior.execute("Basic_Kick", self.kick_direction, abort)
            
            # Detect when kick starts (when we're close to ball)
            if not self.kick_in_progress and self.last_ball_distance < 0.5:
                self.kick_in_progress = True
                self.kick_finish_time = world.time_local_ms
            
            return kick_result
        else: # fat proxy behavior
            return self.fat_proxy_kick()

    def think_and_send(self):
        
        behavior = self.behavior
        strategyData = Strategy(self.world)
        d = self.world.draw

        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) # avoid center circle
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None):
            self.state = 0 if behavior.execute("Get_Up") else 1
        elif self.state == 2:
            # Post-kick recovery state - stabilize after kicking to prevent falling
            # Track ball movement to detect kick completion
            ball_pos = self.world.ball_abs_pos[:2]
            my_pos = self.world.robot.loc_head_position[:2]
            current_ball_dist = np.linalg.norm(ball_pos - my_pos)
            
            # Check if ball moved away significantly (kick completed)
            if hasattr(self, 'last_ball_distance') and current_ball_dist > self.last_ball_distance + 0.5:
                # Ball moved - kick completed, continue recovery
                pass
            
            # Recovery period: stabilize for 300ms after kick
            if self.world.time_local_ms - self.kick_finish_time > 300:
                self.state = 0  # Recovery complete
                if strategyData.play_mode != self.world.M_BEFORE_KICKOFF:
                    self.select_skill(strategyData)
            else:
                # Maintain stability during recovery to prevent falling
                behavior.execute("Zero_Bent_Knees_Auto_Head")
        else:
            if strategyData.play_mode != self.world.M_BEFORE_KICKOFF:
                self.select_skill(strategyData)
            else:
                pass


        #--------------------------------------- 3. Broadcast
        self.radio.broadcast()

        #--------------------------------------- 4. Send to server
        if self.fat_proxy_cmd is None: # normal behavior
            self.scom.commit_and_send( strategyData.robot_model.get_command() )
        else: # fat proxy behavior
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() ) 
            self.fat_proxy_cmd = ""



        



    def select_skill(self,strategyData):
        #--------------------------------------- 2. Decide action
        drawer = self.world.draw
        path_draw_options = self.path_manager.draw_options


        #------------------------------------------------------
        #Role Assignment
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            drawer.annotation((0,10.5), "Role Assignment Phase" , drawer.Color.yellow, "status")
        else:
            drawer.clear("status")

        # Determine formation based on ball position and game state
        from formation.Formation import (GenerateBasicFormation, GenerateDefensiveFormation, 
                                         GenerateAttackingFormation, GenerateStartingFormation)
        ball_x = strategyData.ball_2d[0]
        
        # Check if match just started (before kickoff or very early)
        is_match_start = (strategyData.play_mode == self.world.M_BEFORE_KICKOFF or 
                         self.world.time_game < 2.0)  # First 2 seconds
        
        # Formation selection logic:
        if is_match_start:
            # Starting formation: front player in middle
            formation_positions = GenerateStartingFormation()
        elif ball_x < -5.0:  # Ball in our defensive third
            # Defensive formation: all collapse to defend
            formation_positions = GenerateDefensiveFormation(strategyData.ball_2d)
        elif ball_x > 5.0:  # Ball in opponent half
            # Attacking formation: one defender back, rest push forward to assist scoring
            formation_positions = GenerateAttackingFormation(strategyData.ball_2d)
        else:  # Ball central (-5 to 5)
            # Balanced formation: normal play
            formation_positions = GenerateBasicFormation()
        
        point_preferences = role_assignment(strategyData.teammate_positions, formation_positions)
        strategyData.my_desired_position = point_preferences[strategyData.player_unum]
        
        drawer.line(strategyData.mypos, strategyData.my_desired_position, 2,drawer.Color.blue,"target line")

        #------------------------------------------------------
        # Goalkeeper Support: Defender takes over after goalkeeper clears
        # Check if defender should take over from goalkeeper
        if (strategyData.player_unum == 2 and  # This is the defender
            strategyData.active_player_unum == 1 and  # Goalkeeper is active
            strategyData.ShouldDefenderTakeOverFromGoalkeeper()):
            # Defender becomes active player after goalkeeper clearance
            drawer.annotation((0,10.5), "Defender Taking Over" , drawer.Color.cyan, "status")
            # Use intelligent pass/shoot selection
            action_type, target, receiver_unum = strategyData.ShouldShootOrPass(
                strategyData.player_unum,
                strategyData.mypos,
                strategyData.ball_2d,
                strategyData.teammate_positions,
                strategyData.opponent_positions,
                shoot_threshold=0.4
            )
            
            if action_type == 'shoot':
                drawer.line(strategyData.mypos, target, 3, drawer.Color.green, "shoot line")
                drawer.clear("pass line")
                ball_pos = self.world.ball_abs_pos[:2]
                my_pos = self.world.robot.loc_head_position[:2]
                self.last_ball_distance = np.linalg.norm(ball_pos - my_pos)
                self.kick_in_progress = True
                self.kick_finish_time = self.world.time_local_ms
                return self.kickTarget(strategyData, strategyData.mypos, target)
            elif action_type == 'pass' and target is not None:
                drawer.line(strategyData.mypos, target, 2, drawer.Color.red, "pass line")
                drawer.clear("shoot line")
                ball_pos = self.world.ball_abs_pos[:2]
                my_pos = self.world.robot.loc_head_position[:2]
                self.last_ball_distance = np.linalg.norm(ball_pos - my_pos)
                self.kick_in_progress = True
                self.kick_finish_time = self.world.time_local_ms
                return self.kickTarget(strategyData, strategyData.mypos, target)
        
        #------------------------------------------------------
        # Active Player Decision (Submission 2 - Optimized)
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            drawer.annotation((0,10.5), "Active Player" , drawer.Color.yellow, "status")
            
            # More lenient formation check - don't wait too long
            # If formation is close enough or we're near goal, act immediately
            dist_to_goal = np.linalg.norm(np.array(strategyData.mypos) - np.array([15, 0]))
            formation_ready = strategyData.IsFormationReady(point_preferences)
            
            # Act if formation is ready OR if we're close to goal (be aggressive)
            if formation_ready or dist_to_goal < 10.0 or np.linalg.norm(np.array(strategyData.mypos) - np.array(strategyData.ball_2d)) < 2.0:
                # Use intelligent pass/shoot selection with lower threshold for aggression
                action_type, target, receiver_unum = strategyData.ShouldShootOrPass(
                    strategyData.player_unum,
                    strategyData.mypos,
                    strategyData.ball_2d,
                    strategyData.teammate_positions,
                    strategyData.opponent_positions,
                    shoot_threshold=0.4  # Lower threshold for more aggressive shooting
                )
                
                if action_type == 'shoot':
                    drawer.line(strategyData.mypos, target, 3, drawer.Color.green, "shoot line")
                    drawer.clear("pass line")
                    # Track ball distance before kick for fall prevention
                    ball_pos = self.world.ball_abs_pos[:2]
                    my_pos = self.world.robot.loc_head_position[:2]
                    self.last_ball_distance = np.linalg.norm(ball_pos - my_pos)
                    self.kick_in_progress = True
                    self.kick_finish_time = self.world.time_local_ms
                    return self.kickTarget(strategyData, strategyData.mypos, target)
                elif action_type == 'pass' and target is not None:
                    drawer.line(strategyData.mypos, target, 2, drawer.Color.red, "pass line")
                    drawer.clear("shoot line")
                    # Track ball distance before kick for fall prevention
                    ball_pos = self.world.ball_abs_pos[:2]
                    my_pos = self.world.robot.loc_head_position[:2]
                    self.last_ball_distance = np.linalg.norm(ball_pos - my_pos)
                    self.kick_in_progress = True
                    self.kick_finish_time = self.world.time_local_ms
                    return self.kickTarget(strategyData, strategyData.mypos, target)
                else:
                    # Fallback: shoot at goal
                    drawer.line(strategyData.mypos, (15, 0), 3, drawer.Color.green, "shoot line")
                    drawer.clear("pass line")
                    # Track ball distance before kick for fall prevention
                    ball_pos = self.world.ball_abs_pos[:2]
                    my_pos = self.world.robot.loc_head_position[:2]
                    self.last_ball_distance = np.linalg.norm(ball_pos - my_pos)
                    self.kick_in_progress = True
                    self.kick_finish_time = self.world.time_local_ms
                    return self.kickTarget(strategyData, strategyData.mypos, (15, 0))
            else:
                # Formation not ready and not urgent - move to position quickly
                strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, is_aggressive=True)
        else:
            # Not the active player - use optimal defensive positioning
            drawer.clear("pass line")
            drawer.clear("shoot line")
            drawer.clear_player()
            
            # Get optimal defensive position with ball pressure awareness
            defensive_pos, defensive_ori = strategyData.GetOptimalDefensivePosition(
                strategyData.ball_2d,
                strategyData.player_unum,
                strategyData.teammate_positions,
                strategyData.opponent_positions
            )
            
            return self.move(defensive_pos, orientation=defensive_ori)
        
































    

    #--------------------------------------- Fat proxy auxiliary methods


    def fat_proxy_kick(self):
        w = self.world
        r = self.world.robot 
        ball_2d = w.ball_abs_pos[:2]
        my_head_pos_2d = r.loc_head_position[:2]

        if np.linalg.norm(ball_2d - my_head_pos_2d) < 0.25:
            # fat proxy kick arguments: power [0,10]; relative horizontal angle [-180,180]; vertical angle [0,70]
            self.fat_proxy_cmd += f"(proxy kick 10 {M.normalize_deg( self.kick_direction  - r.imu_torso_orientation ):.2f} 20)" 
            self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk
            return True
        else:
            self.fat_proxy_move(ball_2d-(-0.1,0), None, True) # ignore obstacles
            return False


    def fat_proxy_move(self, target_2d, orientation, is_orientation_absolute):
        r = self.world.robot

        target_dist = np.linalg.norm(target_2d - r.loc_head_position[:2])
        target_dir = M.target_rel_angle(r.loc_head_position[:2], r.imu_torso_orientation, target_2d)

        if target_dist > 0.1 and abs(target_dir) < 8:
            self.fat_proxy_cmd += (f"(proxy dash {100} {0} {0})")
            return

        if target_dist < 0.1:
            if is_orientation_absolute:
                orientation = M.normalize_deg( orientation - r.imu_torso_orientation )
            target_dir = np.clip(orientation, -60, 60)
            self.fat_proxy_cmd += (f"(proxy dash {0} {0} {target_dir:.1f})")
        else:
            self.fat_proxy_cmd += (f"(proxy dash {20} {0} {target_dir:.1f})")