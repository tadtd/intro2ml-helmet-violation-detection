from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from ..auth import get_current_user
from ..db.violations import list_user_violations, list_violations as list_all_violations
from ..db.profiles import get_profile

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("")
def list_violations(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    video_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    profile = get_profile(current_user["sub"])
    if profile.get("role") == "admin" and video_id is not None:
        items = list_all_violations(video_id=video_id, limit=limit, offset=offset)
    else:
        items = list_user_violations(
            current_user["sub"],
            limit=limit,
            offset=offset,
        )
    return {"items": items, "limit": limit, "offset": offset}
