from ninja import Router
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
import json
import re

router = Router(tags=["profile"], auth=BearerAuth())


@router.get("/")
def get_profile(request):
    """Get user profile."""
    uid = request.auth
    try:
        profile = db.get_user_profile(uid)
        if not profile:
            return JsonResponse({"error": "Profile not found"}, status=404)

        notification_prefs = db.get_user_notification_preferences(uid)

        return {
            "uid": uid,
            "email": profile.get("email", ""),
            "first_name": profile.get("first_name", ""),
            "last_name": profile.get("last_name", ""),
            "username": profile.get("username", ""),
            "is_premium": profile.get("is_premium", False),
            "assigned_personality": profile.get("assigned_personality"),
            "photo_url": profile.get("photo_url"),
            "notification_preferences": notification_prefs,
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/sync/")
def sync_profile(request):
    """Update profile fields."""
    uid = request.auth
    try:
        body = json.loads(request.body)

        if "email" in body:
            db.update_user_email(uid, body["email"])

        if "first_name" in body and "last_name" in body:
            first_name = body["first_name"].strip()
            last_name = body["last_name"].strip()
            if not first_name:
                return JsonResponse({"error": "First name is required"}, status=400)
            db.update_user_name(uid, first_name, last_name)

        if "username" in body:
            username = body["username"].strip()
            if len(username) < 3:
                return JsonResponse({"error": "Username must be at least 3 characters"}, status=400)
            if not re.match(r"^[a-zA-Z0-9_]+$", username):
                return JsonResponse({"error": "Username can only contain letters, numbers, and underscores"}, status=400)
            if db.is_username_taken(username, exclude_uid=uid):
                return JsonResponse({"error": "Username is already taken"}, status=400)
            try:
                db.update_user_username(uid, username)
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)

        if "avatar_slug" in body:
            avatar_slug = body["avatar_slug"]
            if avatar_slug:
                photo_url = f"/static/images/personalities/{avatar_slug}.png"
                db.update_user_avatar(uid, photo_url)

        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/notifications/")
def update_notifications(request):
    """Update notification preferences."""
    uid = request.auth
    try:
        body = json.loads(request.body)
        preferences = body.get("preferences")
        if not preferences:
            return JsonResponse({"error": "No preferences provided"}, status=400)

        db.update_user_notification_preferences(uid, preferences)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
