from ninja import Router, Query
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
from api.schemas.cards import CardListParams

router = Router(tags=["cards"])


@router.get("/", auth=BearerAuth())
def card_list(request, params: Query[CardListParams]):
    """Get card catalog with match scores."""
    uid = request.auth

    try:
        all_cards = db.get_cards()
    except Exception:
        all_cards = []

    # Get user wallet cards
    wallet_card_ids = set()
    try:
        user_cards = db.get_user_cards(uid)
        wallet_card_ids = {card["card_id"] for card in user_cards}
    except Exception:
        pass

    # Get match scores
    user_match_scores = {}
    try:
        user_personality = db.get_user_assigned_personality(uid)
        if user_personality:
            from core.services.personalities import PersonalityMixin
            user_match_scores = getattr(db, '_cached_match_scores', {})
    except Exception:
        pass

    # Derive categories
    categories_map = {
        "Travel": ["travel", "flight", "hotel", "mile", "vacation"],
        "Hotel": ["hotel", "marriott", "hilton", "hyatt", "ihg"],
        "Flights": ["flight", "airline", "delta", "united", "southwest"],
        "Dining": ["dining", "restaurant", "food"],
        "Groceries": ["groceries", "supermarket"],
        "Cash Back": ["cash back", "cash rewards"],
        "Luxury": ["lounge", "luxury", "platinum", "reserve"],
    }

    issuers_set = set()
    categories_set = set()

    for card in all_cards:
        card_cats = set()
        text_to_check = (
            card.get("name", "") + " " + str(card.get("benefits", ""))
        ).lower()

        for cat, keywords in categories_map.items():
            if any(k in text_to_check for k in keywords):
                card_cats.add(cat)

        if card.get("annual_fee", 0) == 0:
            card_cats.add("No Annual Fee")

        card["categories"] = sorted(list(card_cats))
        card["in_wallet"] = card.get("id") in wallet_card_ids
        card["match_score"] = user_match_scores.get(card.get("id"), 0)

        issuers_set.add(card.get("issuer", "Unknown"))
        categories_set.update(card_cats)

    # Apply filters
    filtered = all_cards

    if params.search:
        q = params.search.lower()
        filtered = [
            c for c in filtered
            if q in c.get("name", "").lower() or q in c.get("issuer", "").lower()
        ]

    if params.issuer:
        filtered = [c for c in filtered if c.get("issuer") == params.issuer]

    if params.category:
        filtered = [c for c in filtered if params.category in c.get("categories", [])]

    if params.min_fee is not None:
        filtered = [c for c in filtered if (c.get("annual_fee") or 0) >= params.min_fee]

    if params.max_fee is not None:
        filtered = [c for c in filtered if (c.get("annual_fee") or 0) <= params.max_fee]

    if params.wallet == "in":
        filtered = [c for c in filtered if c.get("in_wallet")]
    elif params.wallet == "out":
        filtered = [c for c in filtered if not c.get("in_wallet")]

    # Sort
    if params.sort == "fee_asc":
        filtered.sort(key=lambda c: c.get("annual_fee") or 0)
    elif params.sort == "fee_desc":
        filtered.sort(key=lambda c: c.get("annual_fee") or 0, reverse=True)
    elif params.sort == "match":
        filtered.sort(key=lambda c: c.get("match_score", 0), reverse=True)
    elif params.sort == "name":
        filtered.sort(key=lambda c: c.get("name", ""))

    # Paginate
    page_size = params.page_size
    page = params.page
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_cards = filtered[start:end]

    # Serialize
    def serialize(c):
        return {
            "id": c.get("id"),
            "slug": c.get("slug", c.get("id")),
            "name": c.get("name"),
            "issuer": c.get("issuer"),
            "annual_fee": c.get("annual_fee", 0),
            "image_url": c.get("image_url", ""),
            "categories": c.get("categories", []),
            "in_wallet": c.get("in_wallet", False),
            "match_score": c.get("match_score", 0),
            "welcome_bonus": c.get("welcome_bonus", ""),
        }

    return {
        "cards": [serialize(c) for c in page_cards],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
        "issuers": sorted(list(issuers_set)),
        "categories": sorted(list(categories_set)),
    }


@router.get("/{slug}/", auth=BearerAuth())
def card_detail(request, slug: str):
    """Get full card details."""
    try:
        card = db.get_card_by_slug(slug)
        if not card:
            return JsonResponse({"error": "Card not found"}, status=404)

        return {
            "id": card.get("id"),
            "slug": card.get("slug", card.get("id")),
            "name": card.get("name"),
            "issuer": card.get("issuer"),
            "annual_fee": card.get("annual_fee", 0),
            "image_url": card.get("image_url", ""),
            "benefits": card.get("benefits", []),
            "earning_rates": card.get("earning_rates", []),
            "rewards_structure": card.get("rewards_structure", []),
            "credits": card.get("credits", []),
            "welcome_bonus": card.get("welcome_bonus", ""),
            "welcome_offer": card.get("welcome_offer", ""),
            "signup_bonus": card.get("signup_bonus", ""),
            "welcome_requirement": card.get("welcome_requirement", ""),
            "loyalty_program": card.get("loyalty_program"),
            "is_524": card.get("is_524", True),
            "referral_url": card.get("referral_url", ""),
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
