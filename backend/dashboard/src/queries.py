import logging
from typing import Any
from fastapi import APIRouter, Request, Query, HTTPException, status

from common.db.client import get_supabase_client
from common.db.constants import normalize_model_name

logger = logging.getLogger("dashboard.queries")
router = APIRouter()


@router.get("/violations")
def list_filtered_violations(
    request: Request,
    startDate: str | None = Query(None),
    endDate: str | None = Query(None),
    model: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    user_id = request.state.user_id
    role = request.state.role

    try:
        supabase = get_supabase_client()
        query = supabase.table("violations").select("*")

        # Row-level security: Operators only see their own violations, admins see all
        if role != "admin":
            query = query.eq("user_id", user_id)

        # Filters
        if model and model.strip().lower() != "all":
            try:
                query = query.eq("model_used", normalize_model_name(model))
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
        if startDate:
            query = query.gte("timestamp", startDate)
        if endDate:
            query = query.lte("timestamp", endDate)

        # Pagination & Ordering
        query = query.order("timestamp", desc=True)
        end_idx = offset + limit - 1
        query = query.range(offset, end_idx)

        response = query.execute()
        return {
            "items": response.data or [],
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to query violations: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query violations: {str(exc)}",
        )
