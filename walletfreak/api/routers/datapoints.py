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


@router.get("/", auth=BearerAuth())
def datapoint_list(request, params: Query[DatapointListParams]):
    uid = request.auth
    try:
        datapoints = db.get_datapoints()

        if params.card:
            datapoints = [d for d in datapoints if d.get("card_id") == params.card]
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
