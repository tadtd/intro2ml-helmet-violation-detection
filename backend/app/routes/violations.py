from typing import Annotated, Any

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..supabase_client import list_user_violations

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("")
def list_violations(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, object]:
    return {"items": list_user_violations(current_user["sub"])}
