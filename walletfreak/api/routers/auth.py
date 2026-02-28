from ninja import Router
from firebase_admin import auth as firebase_auth, firestore
from core.services import db
from api.schemas.auth import LoginRequest, LoginResponse, UserProfile
from api.schemas.common import ErrorResponse

router = Router(tags=["auth"])


@router.post("/login/", response={200: LoginResponse, 400: ErrorResponse})
def login(request, payload: LoginRequest):
    """Verify Firebase idToken and ensure user profile exists in Firestore."""
    try:
        decoded_token = firebase_auth.verify_id_token(payload.id_token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email", "")
        name = decoded_token.get("name", "")

        first_name = ""
        last_name = ""
        if name:
            parts = name.split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        # Check existing profile
        existing_profile = db.get_user_profile(uid)

        if not existing_profile:
            # New user - create profile
            username = db.generate_unique_username(first_name, last_name, uid)
            user_data = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "is_super_staff": False,
                "is_premium": False,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
            db.create_user_profile(uid, user_data)
            existing_profile = db.get_user_profile(uid)
        else:
            # Existing user - update email, fill empty names
            update_data = {"email": email}
            if not existing_profile.get("first_name"):
                update_data["first_name"] = first_name
            if not existing_profile.get("last_name"):
                update_data["last_name"] = last_name
            db.db.collection("users").document(uid).set(update_data, merge=True)
            existing_profile = db.get_user_profile(uid)

        profile = UserProfile(
            uid=uid,
            email=existing_profile.get("email", email),
            first_name=existing_profile.get("first_name", ""),
            last_name=existing_profile.get("last_name", ""),
            username=existing_profile.get("username", ""),
            is_premium=existing_profile.get("is_premium", False),
            assigned_personality=existing_profile.get("assigned_personality"),
            photo_url=existing_profile.get("photo_url"),
        )

        return 200, LoginResponse(profile=profile)

    except Exception as e:
        return 400, ErrorResponse(error=str(e))
