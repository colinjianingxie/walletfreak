from ninja import Router
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth

router = Router(tags=["personalities"])


@router.get("/", auth=BearerAuth())
def personality_list(request):
    """Get all personalities with quiz questions."""
    uid = request.auth

    try:
        personalities = db.get_personalities()
    except Exception:
        personalities = []

    try:
        quiz_questions = db.get_quiz_questions()
    except Exception:
        quiz_questions = []

    assigned = None
    try:
        assigned = db.get_user_assigned_personality(uid)
    except Exception:
        pass

    return {
        "personalities": personalities,
        "quiz_questions": quiz_questions,
        "assigned_personality": assigned,
    }


@router.get("/{slug}/", auth=BearerAuth())
def personality_detail(request, slug: str):
    """Get personality detail with hydrated card slots."""
    try:
        personality = db.get_personality_by_slug(slug)
        if not personality:
            return JsonResponse({"error": "Personality not found"}, status=404)

        personality["slug"] = personality["id"]

        # Ensure tagline, rules, and categories are present
        personality.setdefault("tagline", "")
        personality.setdefault("rules", [])
        personality.setdefault("categories", [])

        # Hydrate card slots
        all_cards = db.get_cards()
        cards_map = {c["id"]: c for c in all_cards}

        for slot in personality.get("slots", []):
            hydrated_cards = []
            for card_slug in slot.get("cards", []):
                card = cards_map.get(card_slug)
                if card:
                    hydrated_cards.append({
                        "id": card.get("id"),
                        "slug": card.get("id"),
                        "name": card.get("name"),
                        "issuer": card.get("issuer"),
                        "annual_fee": card.get("annual_fee", 0),
                        "image_url": card.get("image_url", ""),
                    })
            slot["hydrated_cards"] = hydrated_cards

        return personality
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/submit/", auth=BearerAuth())
def submit_quiz(request):
    """Submit personality quiz results."""
    uid = request.auth
    import json

    try:
        body = json.loads(request.body)
        personality_id = body.get("personality_id")
        score = body.get("score", 0)

        if not personality_id:
            return JsonResponse({"error": "personality_id required"}, status=400)

        db.update_user_personality(uid, personality_id, score=score)
        return {"success": True, "personality_id": personality_id}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
