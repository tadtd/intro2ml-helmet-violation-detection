import numpy as np


def get_composite_union_box(
    motorbike_box: tuple[float, float, float, float],
    non_helmet_box: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    """Calculate the bounding box coordinates for the composite union of motorbike and violating head."""
    mx1, my1, mx2, my2 = motorbike_box
    nx1, ny1, nx2, ny2 = non_helmet_box
    
    ux1 = max(0, int(min(mx1, nx1)))
    uy1 = max(0, int(min(my1, ny1)))
    ux2 = min(width, int(max(mx2, nx2)))
    uy2 = min(height, int(max(my2, ny2)))
    
    return ux1, uy1, ux2, uy2
