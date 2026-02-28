from ninja import Schema
from typing import Optional, Any


class AddCardRequest(Schema):
    status: str = "active"
    anniversary_date: Optional[str] = None


class UpdateStatusRequest(Schema):
    status: str


class UpdateAnniversaryRequest(Schema):
    anniversary_date: str


class UpdateBenefitRequest(Schema):
    amount: float = 0
    period_key: Optional[str] = None
    is_full: bool = False
    increment: bool = False


class ToggleIgnoreRequest(Schema):
    is_ignored: bool


class RemoveCardRequest(Schema):
    delete_loyalty_program: bool = False
