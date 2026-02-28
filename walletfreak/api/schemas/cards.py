from ninja import Schema
from typing import Optional


class CardListParams(Schema):
    page: int = 1
    page_size: int = 20
    issuer: Optional[str] = None
    category: Optional[str] = None
    min_fee: Optional[int] = None
    max_fee: Optional[int] = None
    search: Optional[str] = None
    sort: Optional[str] = None
    wallet: Optional[str] = None
