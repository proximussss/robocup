import numpy as np

def GenerateBasicFormation():
    """
    Optimized formation for 5v5 soccer:
    - Spreads players across field for better passing angles
    - Maintains defensive structure while providing attacking options
    - Creates triangles for passing opportunities
    - Positions players to support both offense and defense
    """
    
    # Optimized formation with better spacing and tactical positioning
    formation = [
        np.array([-13.5, 0]),      # Player 1: Goalkeeper (deep, centered)
        np.array([-8, -3.5]),      # Player 2: Left Defender (covers left side, supports mid)
        np.array([-3, 4]),         # Player 3: Right Midfielder (forward on right, creates width)
        np.array([5, -2]),         # Player 4: Left Forward (forward on left, balanced)
        np.array([10.5, 1.5])      # Player 5: Right Forward (advanced, slightly wide for shooting angle)
    ]
    
    # Alternative aggressive formation for when we need to press
    # formation = [
    #     np.array([-13, 0]),       # Goalkeeper
    #     np.array([-6, -4]),       # Left Defender (more forward)
    #     np.array([-2, 3.5]),      # Right Defender/Mid (very forward)
    #     np.array([8, -2.5]),      # Left Forward (advanced)
    #     np.array([11.5, 2])       # Right Forward (very advanced)
    # ]
    
    # Defensive formation variant
    # formation = [
    #     np.array([-13.5, 0]),     # Goalkeeper
    #     np.array([-10, -3]),      # Left Defender (deeper)
    #     np.array([-9, 3]),        # Right Defender (deeper)
    #     np.array([-1, 0]),        # Central Midfielder
    #     np.array([8, 0])          # Forward (balanced)
    # ]

    return formation

def GenerateStartingFormation():
    """
    Starting formation at match start (kickoff):
    - Front player positioned in the middle
    - Balanced initial setup
    """
    formation = [
        np.array([-13.5, 0]),      # Player 1: Goalkeeper (deep, centered)
        np.array([-8, -3.5]),      # Player 2: Left Defender
        np.array([-3, 4]),         # Player 3: Right Midfielder
        np.array([5, -2]),         # Player 4: Left Forward
        np.array([11.5, 0])        # Player 5: Center Forward (MIDDLE - as requested)
    ]
    
    return formation

def GenerateAttackingFormation(ball_pos):
    """
    Attacking formation when ball is in opponent half:
    - Goalkeeper stays deep
    - One defender stays back (with goalkeeper)
    - Rest assist toward scoring (push forward)
    """
    ball_arr = np.array(ball_pos)
    
    # Attacking formation: aggressive forward push
    formation = [
        np.array([-13.5, 0]),      # Player 1: Goalkeeper (deep, centered)
        np.array([-10, 0]),        # Player 2: Defender staying back (with GK)
        np.array([2, 3]),          # Player 3: Attacking Midfielder (right side)
        np.array([8, -2.5]),       # Player 4: Left Forward (advanced)
        np.array([12, 0])         # Player 5: Center Forward (advanced, ready to score)
    ]
    
    return formation

def GenerateDefensiveFormation(ball_pos):
    """
    Defensive formation when ball is near our keeper:
    - Goalkeeper stays deep
    - One defender always close to goalkeeper for support
    - All players collapse to our half to assist with defending
    """
    ball_arr = np.array(ball_pos)
    
    # Defensive formation with defender supporting goalkeeper
    formation = [
        np.array([-13.5, 0]),      # Player 1: Goalkeeper (deep, centered)
        np.array([-11, 2.5]),      # Player 2: Defender supporting keeper (close to GK, slightly right)
        np.array([-8, -2]),        # Player 3: Left Defender (covers left side)
        np.array([-6, 3]),         # Player 4: Right Defender (covers right side, supports)
        np.array([-3, 0])          # Player 5: Sweeper/Defensive Midfielder (between defense and midfield)
    ]
    
    return formation
