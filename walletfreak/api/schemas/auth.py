from ninja import Schema
from typing import Optional


class LoginRequest(Schema):
    id_token: str


class UserProfile(Schema):
    uid: str
    email: str
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    is_premium: bool = False
    assigned_personality: Optional[str] = None
    photo_url: Optional[str] = None


class LoginResponse(Schema):
    success: bool = True
    profile: UserProfile
