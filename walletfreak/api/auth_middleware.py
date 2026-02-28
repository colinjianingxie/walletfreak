from ninja.security import HttpBearer
from firebase_admin import auth
from core.services import db


class BearerAuth(HttpBearer):
    """Firebase Bearer token authentication for the mobile API."""

    def authenticate(self, request, token):
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token["uid"]

            # Attach uid and profile to request for downstream use
            request.uid = uid
            request.firebase_token = decoded_token

            # Fetch user profile from Firestore
            profile = db.get_user_profile(uid)
            request.user_profile = profile

            return uid
        except Exception:
            return None
