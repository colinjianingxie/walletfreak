from ninja import Router
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
import json

router = Router(tags=["notifications"], auth=BearerAuth())


@router.get("/")
def list_notifications(request):
    """List user's notifications (paginated via ?limit=20&cursor=doc_id)."""
    uid = request.auth
    try:
        limit = int(request.GET.get('limit', 20))
        limit = min(limit, 50)
        cursor = request.GET.get('cursor')
        notifications = db.get_user_notifications(uid, limit=limit, start_after=cursor)
        return {"notifications": notifications}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.get("/unread-count/")
def unread_count(request):
    """Return the number of unread notifications."""
    uid = request.auth
    try:
        count = db.get_unread_count(uid)
        return {"count": count}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/{notification_id}/read/")
def mark_read(request, notification_id: str):
    """Mark a single notification as read."""
    uid = request.auth
    try:
        ok = db.mark_notification_read(uid, notification_id)
        if not ok:
            return JsonResponse({"error": "Not found"}, status=404)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/read-all/")
def mark_all_read(request):
    """Mark all notifications as read."""
    uid = request.auth
    try:
        count = db.mark_all_notifications_read(uid)
        return {"success": True, "count": count}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.delete("/{notification_id}/")
def delete_notification(request, notification_id: str):
    """Delete a single notification."""
    uid = request.auth
    try:
        ok = db.delete_notification(uid, notification_id)
        if not ok:
            return JsonResponse({"error": "Not found"}, status=404)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
