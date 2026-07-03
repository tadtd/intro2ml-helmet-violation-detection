def is_stationary(
    track_history: list[tuple[float, float, float, float]],
    threshold: float = 5.0,
) -> bool:
    """Return True if the motorbike has moved less than the threshold distance in its tracking history."""
    if len(track_history) < 5:
        # Not enough history to confirm stationary
        return False
        
    first = track_history[0]
    last = track_history[-1]
    
    first_cx = (first[0] + first[2]) / 2
    first_cy = (first[1] + first[3]) / 2
    last_cx = (last[0] + last[2]) / 2
    last_cy = (last[1] + last[3]) / 2
    
    displacement = ((last_cx - first_cx) ** 2 + (last_cy - first_cy) ** 2) ** 0.5
    return displacement < threshold
