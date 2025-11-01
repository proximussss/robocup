import numpy as np

def GenerateBasicFormation():
    """
    Generate a basic balanced formation (2-2-1: 2 defenders, 2 midfielders, 1 forward)
    This is used as a fallback when dynamic formation is not available
    """
    formation = [
        np.array([-13, 0]),      # Goalkeeper - stays near goal
        np.array([-9, -3]),      # Left Defender
        np.array([-9, 3]),       # Right Defender
        np.array([-3, -2]),      # Left Midfielder
        np.array([-3, 2]),       # Right Midfielder (acts as forward)
    ]

    return formation


def GenerateDefensiveFormation():
    """
    Generate a defensive formation (3-1-1: 3 defenders, 1 midfielder, 1 forward)
    Use when protecting a lead
    """
    formation = [
        np.array([-13.5, 0]),    # Goalkeeper
        np.array([-10, -3]),     # Left Defender
        np.array([-10, 0]),      # Center Defender
        np.array([-10, 3]),      # Right Defender
        np.array([-5, 0]),       # Central Midfielder
    ]

    return formation


def GenerateAttackingFormation():
    """
    Generate an attacking formation (1-2-2: 1 defender, 2 midfielders, 2 forwards)
    Use when chasing a game
    """
    formation = [
        np.array([-13, 0]),      # Goalkeeper
        np.array([-8, 0]),       # Center Defender
        np.array([-3, -2.5]),    # Left Midfielder
        np.array([-3, 2.5]),     # Right Midfielder
        np.array([5, 0]),        # Central Forward
    ]

    return formation


def GenerateWideFormation():
    """
    Generate a wide formation for more width in attack
    """
    formation = [
        np.array([-13, 0]),      # Goalkeeper
        np.array([-9, -2]),      # Left Defender
        np.array([-9, 2]),       # Right Defender
        np.array([-2, -4.5]),    # Wide Left
        np.array([-2, 4.5]),     # Wide Right
    ]

    return formation
