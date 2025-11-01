"""
Game Mode Handler
Manages different play modes and returns appropriate behavior strategies
"""

import numpy as np

class GameModeHandler:
    """
    Handles different game modes and provides appropriate strategies
    """
    
    def __init__(self, world):
        self.world = world
        
    def get_game_mode_group(self, play_mode):
        """
        Categorize play modes into groups for easier handling
        
        Returns:
            str: Game mode group identifier
        """
        # Beam modes (before kickoff and kickoffs)
        if play_mode in [self.world.M_BEFORE_KICKOFF, self.world.M_OUR_KICKOFF, 
                         self.world.M_THEIR_KICKOFF]:
            return "kickoff"
        
        # Free kick modes
        if play_mode in [self.world.M_OUR_FREE_KICK, self.world.M_THEIR_FREE_KICK,
                         self.world.M_OUR_DIR_FREE_KICK, self.world.M_THEIR_DIR_FREE_KICK]:
            return "free_kick"
        
        # Corner kick modes
        if play_mode in [self.world.M_OUR_CORNER_KICK, self.world.M_THEIR_CORNER_KICK]:
            return "corner_kick"
        
        # Goal kick modes
        if play_mode in [self.world.M_OUR_GOAL_KICK, self.world.M_THEIR_GOAL_KICK]:
            return "goal_kick"
        
        # Kick in modes
        if play_mode in [self.world.M_OUR_KICK_IN, self.world.M_THEIR_KICK_IN]:
            return "kick_in"
        
        # Active play
        if play_mode == self.world.M_PLAY_ON:
            return "play_on"
        
        # Goals
        if play_mode in [self.world.M_OUR_GOAL, self.world.M_THEIR_GOAL]:
            return "goal"
        
        # Game over
        if play_mode == self.world.M_GAME_OVER:
            return "game_over"
        
        return "other"
    
    def is_our_set_piece(self, play_mode, is_left_team=None):
        """
        Check if the current set piece is ours
        
        Args:
            play_mode: Current play mode
            is_left_team: Not used (kept for compatibility)
            
        Returns:
            bool: True if it's our set piece
        """
        # The World class already handles left/right, using M_OUR_* and M_THEIR_*
        our_modes = [
            self.world.M_OUR_KICKOFF,
            self.world.M_OUR_FREE_KICK,
            self.world.M_OUR_DIR_FREE_KICK,
            self.world.M_OUR_CORNER_KICK,
            self.world.M_OUR_GOAL_KICK,
            self.world.M_OUR_KICK_IN,
        ]
        
        return play_mode in our_modes

