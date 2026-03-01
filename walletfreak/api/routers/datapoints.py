from ninja import Router, Query
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
from ninja import Schema
from typing import Optional
import json

router = Router(tags=["datapoints"])


class DatapointListParams(Schema):
    page: int = 1
    page_size: int = 20
    sort: Optional[str] = None
    card: Optional[str] = None
    benefit: Optional[str] = None


def normalize_datapoint(dp, uid=None):
    """Normalize Firestore datapoint fields for consistent mobile API response."""
    dp["author_name"] = dp.get("user_display_name") or dp.get("author_name") or "Anonymous"
    dp["user_id"] = dp.get("user_id") or dp.get("user_uid") or ""
    dp["benefit"] = dp.get("benefit_name") or dp.get("benefit") or ""
    dp["data"] = dp.get("content") or dp.get("data") or ""
    dp["card_name"] = dp.get("card_name") or ""
    dp["card_slug"] = dp.get("card_slug") or dp.get("card_id") or ""
    dp["status"] = dp.get("status") or "Success"
    dp["created_at"] = dp.get("date_posted") or dp.get("created_at") or ""
    dp["upvotes"] = dp.get("upvote_count", 0) or dp.get("upvotes", 0) or 0
    dp["outdated_count"] = dp.get("outdated_count", 0) or 0

    # Check if current user has voted
    upvoted_by = dp.get("upvoted_by", []) or []
    dp["user_voted"] = uid in upvoted_by if uid else False

    return dp


@router.get("/", auth=BearerAuth())
def datapoint_list(request, params: Query[DatapointListParams]):
    uid = request.auth
    try:
        datapoints = db.get_datapoints()

        # Normalize all datapoints
        datapoints = [normalize_datapoint(d, uid) for d in datapoints]

        if params.card:
            datapoints = [d for d in datapoints if d.get("card_slug") == params.card or d.get("card_name") == params.card]
        if params.benefit:
            datapoints = [d for d in datapoints if d.get("benefit") == params.benefit]

        if params.sort == "newest":
            datapoints.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        elif params.sort == "votes":
            datapoints.sort(key=lambda d: d.get("upvotes", 0), reverse=True)

        total = len(datapoints)
        start = (params.page - 1) * params.page_size
        end = start + params.page_size

        return {
            "datapoints": datapoints[start:end],
            "total": total,
            "page": params.page,
            "has_next": end < total,
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/", auth=BearerAuth())
def submit_datapoint(request):
    uid = request.auth
    try:
        body = json.loads(request.body)
        result = db.create_datapoint(uid, body)
        return {"success": True, "id": result}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/{pk}/vote/", auth=BearerAuth())
def vote_datapoint(request, pk: str):
    uid = request.auth
    try:
        db.vote_on_datapoint(uid, pk)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
