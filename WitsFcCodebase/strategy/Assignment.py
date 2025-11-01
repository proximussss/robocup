import numpy as np

def calculate_euclidean_distance(pos1, pos2):
    """
    Calculate Euclidean distance between two 2D positions.
    
    Args:
        pos1: First position as ndarray([x, y]) or None
        pos2: Second position as ndarray([x, y]) or None
    
    Returns:
        float: Euclidean distance between the positions, or very large number if either is None
    """
    # Handle None positions by returning a very large distance
    if pos1 is None or pos2 is None:
        return 1000.0
    
    return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def create_preference_lists(teammate_positions, formation_positions):
    """
    Create preference lists for both players and formation positions based on Euclidean distance.
    
    Args:
        teammate_positions: List of player positions (some may be None)
        formation_positions: List of formation positions
    
    Returns:
        tuple: (player_preferences, formation_preferences)
    """
    num_players = len(teammate_positions)
    num_positions = len(formation_positions)
    
    # Create player preferences (players prefer closer formation positions)
    player_preferences = {}
    for i in range(num_players):
        # Skip if teammate position is None
        if teammate_positions[i] is None:
            # Assign arbitrary preference list (will be filtered out later)
            player_preferences[i] = list(range(num_positions))
            continue
            
        distances = []
        for j in range(num_positions):
            distance = calculate_euclidean_distance(teammate_positions[i], formation_positions[j])
            distances.append((j, distance))
        
        # Sort by distance (closest first)
        distances.sort(key=lambda x: x[1])
        player_preferences[i] = [pos_idx for pos_idx, _ in distances]
    
    # Create formation preferences (positions prefer closer players)
    formation_preferences = {}
    for j in range(num_positions):
        distances = []
        for i in range(num_players):
            distance = calculate_euclidean_distance(formation_positions[j], teammate_positions[i])
            distances.append((i, distance))
        
        # Sort by distance (closest first)
        distances.sort(key=lambda x: x[1])
        formation_preferences[j] = [player_idx for player_idx, _ in distances]
    
    return player_preferences, formation_preferences

def gale_shapley_algorithm(player_preferences, formation_preferences, teammate_positions):
    """
    Implement the Gale-Shapley algorithm for stable matching.
    
    Args:
        player_preferences: Dictionary mapping player indices to their preference lists
        formation_preferences: Dictionary mapping formation indices to their preference lists
        teammate_positions: List of teammate positions (to check for None)
    
    Returns:
        dict: Mapping from player indices to formation indices
    """
    num_players = len(player_preferences)
    num_formations = len(formation_preferences)
    
    # Initialize all players as unmatched (except those with None positions)
    unmatched_players = [i for i in range(num_players) if teammate_positions[i] is not None]
    
    # Track current matches (formation -> player)
    current_matches = {i: None for i in range(num_formations)}
    
    # Track which formations each player has proposed to
    proposals_made = {i: set() for i in range(num_players)}
    
    while unmatched_players:
        player = unmatched_players[0]
        
        # Find the highest-ranked formation this player hasn't proposed to yet
        for formation in player_preferences[player]:
            if formation not in proposals_made[player]:
                proposals_made[player].add(formation)
                
                # Check if formation is free
                if current_matches[formation] is None:
                    # Formation accepts the proposal
                    current_matches[formation] = player
                    unmatched_players.remove(player)
                    break
                else:
                    # Formation is already matched, check preferences
                    current_player = current_matches[formation]
                    
                    # Find preference order for this formation
                    current_player_rank = formation_preferences[formation].index(current_player)
                    new_player_rank = formation_preferences[formation].index(player)
                    
                    if new_player_rank < current_player_rank:
                        # New player is preferred, replace current match
                        current_matches[formation] = player
                        unmatched_players.remove(player)
                        unmatched_players.append(current_player)
                        break
                    # If current player is preferred, reject new proposal and continue
                
                # If we've proposed to all formations, this shouldn't happen in a valid matching
                if len(proposals_made[player]) == num_formations:
                    unmatched_players.remove(player)
                    break
    
    # Convert formation -> player mapping to player -> formation mapping
    player_to_formation = {}
    for formation, player in current_matches.items():
        if player is not None:
            player_to_formation[player] = formation
    
    return player_to_formation

def role_assignment(teammate_positions, formation_positions): 
    """
    Assign roles to teammates using the Gale-Shapley algorithm for stable matching.
    
    Args:
        teammate_positions: List of teammate positions as ndarrays
        formation_positions: List of formation positions as ndarrays
    
    Returns:
        dict: Mapping from unum (1-5) to assigned formation position
    """
    # Input : Locations of all teammate locations and positions
    # Output : Map from unum -> positions
    #-----------------------------------------------------------#
    
    # Create preference lists based on Euclidean distance
    player_preferences, formation_preferences = create_preference_lists(
        teammate_positions, formation_positions
    )
    
    # Run Gale-Shapley algorithm
    player_to_formation = gale_shapley_algorithm(player_preferences, formation_preferences, teammate_positions)
    
    # Convert to the required output format (unum 1-5 to formation positions)
    point_preferences = {}
    for player_idx, formation_idx in player_to_formation.items():
        unum = player_idx + 1  # Convert 0-based index to 1-based unum
        point_preferences[unum] = formation_positions[formation_idx]
    
    return point_preferences