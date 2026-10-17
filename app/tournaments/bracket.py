import math
from typing import List, Dict, Any, Optional

def next_power_of_two(n: int) -> int:
    """Returns the smallest power of 2 greater than or equal to n."""
    if n <= 1:
        return 2
    return 1 << (n - 1).bit_length()

def generate_standard_seeding_pairs(num_players: int) -> List[tuple]:
    """
    Standard tournament seeding arrangement (e.g. 1 vs 8, 4 vs 5, 2 vs 7, 3 vs 6).
    """
    bracket_size = next_power_of_two(num_players)
    seeds = [1, 2]
    
    while len(seeds) < bracket_size:
        next_seeds = []
        target_sum = len(seeds) * 2 + 1
        for s in seeds:
            next_seeds.append(s)
            next_seeds.append(target_sum - s)
        seeds = next_seeds

    pairs = []
    for i in range(0, len(seeds), 2):
        pairs.append((seeds[i], seeds[i+1]))
    return pairs

def build_single_elimination_bracket(participant_user_ids_sorted_by_seed: List[str]) -> List[Dict[str, Any]]:
    """
    Builds single-elimination tournament structure with byes.
    Returns list of match definitions across all rounds.
    """
    n = len(participant_user_ids_sorted_by_seed)
    if n < 2:
        raise ValueError("Tournament must have at least 2 participants to generate a bracket.")

    bracket_size = next_power_of_two(n)
    total_rounds = int(math.log2(bracket_size))
    
    # Map seed index (1-indexed) to user_id (or None for Bye)
    seed_map: Dict[int, Optional[str]] = {}
    for idx, uid in enumerate(participant_user_ids_sorted_by_seed):
        seed_map[idx + 1] = uid
    for empty_seed in range(n + 1, bracket_size + 1):
        seed_map[empty_seed] = None  # Bye

    seeding_pairs = generate_standard_seeding_pairs(n)
    
    matches_structure = []
    round_matches_map: Dict[int, List[Dict[str, Any]]] = {}

    # Round 1 matches
    round_1 = []
    for m_idx, (s1, s2) in enumerate(seeding_pairs, start=1):
        p1 = seed_map.get(s1)
        p2 = seed_map.get(s2)
        
        # Check for bye
        status = "scheduled"
        winner = None
        if p1 and not p2:
            status = "completed"
            winner = p1
        elif p2 and not p1:
            status = "completed"
            winner = p2
        elif not p1 and not p2:
            status = "completed"

        match_def = {
            "round_number": 1,
            "match_number": m_idx,
            "player1_id": p1,
            "player2_id": p2,
            "winner_id": winner,
            "status": status,
            "is_bye": (p1 is None or p2 is None),
        }
        round_1.append(match_def)
    round_matches_map[1] = round_1

    # Future rounds
    for r in range(2, total_rounds + 1):
        prev_round = round_matches_map[r - 1]
        num_matches = len(prev_round) // 2
        current_round = []
        for m_idx in range(1, num_matches + 1):
            current_round.append({
                "round_number": r,
                "match_number": m_idx,
                "player1_id": None,
                "player2_id": None,
                "winner_id": None,
                "status": "pending",
                "is_bye": False,
            })
        round_matches_map[r] = current_round

    # Advance Round 1 Byes into Round 2 automatically!
    if total_rounds >= 2:
        for m_idx, r1_match in enumerate(round_1):
            if r1_match.get("winner_id"):
                target_r2_match_idx = m_idx // 2
                target_slot = "player1_id" if (m_idx % 2 == 0) else "player2_id"
                round_matches_map[2][target_r2_match_idx][target_slot] = r1_match["winner_id"]
                # If both players now present in round 2, mark scheduled
                r2_m = round_matches_map[2][target_r2_match_idx]
                if r2_m["player1_id"] and r2_m["player2_id"]:
                    r2_m["status"] = "scheduled"

    for r in range(1, total_rounds + 1):
        matches_structure.extend(round_matches_map[r])

    return matches_structure
