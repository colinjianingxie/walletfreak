from ninja import Router
from django.http import JsonResponse
from django.conf import settings
from core.services import db
from api.auth_middleware import BearerAuth
from calculators.services import OptimizerService
import json
import os

router = Router(tags=["calculators"], auth=BearerAuth())


@router.get("/worth-it/cards/")
def worth_it_card_list(request):
    """Get all cards with annual_fee > 0 for Worth It calculator selection."""
    try:
        all_cards = db.get_cards()
        fee_cards = []
        for card in all_cards:
            af = card.get("annual_fee", 0) or 0
            if af > 0:
                fee_cards.append({
                    "card_id": card.get("slug") or card.get("id"),
                    "name": card.get("name", ""),
                    "issuer": card.get("issuer", ""),
                    "annual_fee": af,
                })

        fee_cards.sort(key=lambda c: c["annual_fee"], reverse=True)
        return {"cards": fee_cards}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.get("/worth-it/{card_slug}/questions/")
def worth_it_questions(request, card_slug: str):
    """Get card with benefits and questions for Worth It audit."""
    try:
        card = db.get_card_by_slug(card_slug)
        if not card:
            return JsonResponse({"error": "Card not found"}, status=404)

        card_questions = card.get("card_questions", [])
        benefits_map = {
            b.get("short_description", ""): b for b in card.get("benefits", [])
        }

        audit_benefits = []
        for q_data in card_questions:
            short_desc = q_data.get("short_desc", "")
            benefit_data = benefits_map.get(short_desc)

            dollar_value = 0
            time_cat = "Annually"
            if benefit_data:
                dollar_value = benefit_data.get("dollar_value", 0)
                time_cat = benefit_data.get("time_category", "Annually")

            q_type = q_data.get("question_type", "toggle")
            choices = q_data.get("choices", [])
            weights = q_data.get("weights", [])

            if q_type == "multiple_choice" and choices:
                input_type = "multiple_choice"
                max_val = len(choices) - 1
            else:
                input_type = "toggle"
                max_val = 1

            audit_benefits.append(
                {
                    "short_description": short_desc,
                    "dollar_value": dollar_value,
                    "time_category": time_cat,
                    "question": q_data.get("question", short_desc),
                    "input_type": input_type,
                    "max_val": max_val,
                    "choices": choices,
                    "weights": weights,
                }
            )

        return {
            "card": {
                "id": card.get("id"),
                "slug": card.get("slug", card.get("id")),
                "name": card.get("name"),
                "issuer": card.get("issuer"),
                "annual_fee": card.get("annual_fee", 0),
                "image_url": card.get("image_url"),
            },
            "benefits": audit_benefits,
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/worth-it/{card_slug}/calculate/")
def worth_it_calculate(request, card_slug: str):
    """Calculate Worth It score from user responses."""
    try:
        body = json.loads(request.body)
        responses = body.get("responses", [])

        card = db.get_card_by_slug(card_slug)
        if not card:
            return JsonResponse({"error": "Card not found"}, status=404)

        annual_fee = card.get("annual_fee", 0)
        card_questions = card.get("card_questions", [])
        benefits_map = {
            b.get("short_description", ""): b for b in card.get("benefits", [])
        }

        total_value = 0.0
        total_user_weight = 0.0
        total_max_weight = 0.0

        for idx, q_data in enumerate(card_questions):
            weights = q_data.get("weights", [])
            this_max_weight = 1.0
            if weights:
                try:
                    this_max_weight = max(weights)
                except ValueError:
                    this_max_weight = 1.0

            this_user_weight = 0.0

            # Get user response for this question
            val = None
            for r in responses:
                if r.get("index") == idx:
                    val = r.get("value")
                    break

            if val is not None:
                try:
                    val = float(val)
                    short_desc = q_data.get("short_desc", "")
                    benefit_data = benefits_map.get(short_desc)

                    dollar_val = 0.0
                    time_cat = ""
                    if benefit_data:
                        dollar_val = benefit_data.get("dollar_value") or 0
                        time_cat = benefit_data.get("time_category", "")

                    benefit_value = 0.0

                    if q_data.get("question_type") == "multiple_choice":
                        choices = q_data.get("choices", [])
                        if choices:
                            idx_val = int(val)
                            if weights and 0 <= idx_val < len(weights):
                                utilization = weights[idx_val]
                                this_user_weight = utilization
                                benefit_value = utilization * dollar_val
                            else:
                                max_idx = len(choices) - 1
                                if max_idx > 0:
                                    utilization = val / max_idx
                                    this_user_weight = utilization
                                    benefit_value = utilization * dollar_val
                                else:
                                    this_user_weight = 1.0 if val >= 0 else 0.0
                                    benefit_value = dollar_val if val >= 0 else 0
                        else:
                            this_user_weight = 1.0 if val > 0 else 0.0
                            benefit_value = dollar_val if val > 0 else 0
                    elif "Monthly" in time_cat:
                        this_user_weight = 1.0 if val > 0 else 0.0
                        benefit_value = (val / 12.0) * dollar_val
                    elif "Quarterly" in time_cat:
                        this_user_weight = 1.0 if val > 0 else 0.0
                        benefit_value = (val / 4.0) * dollar_val
                    elif "Semi" in time_cat:
                        this_user_weight = 1.0 if val > 0 else 0.0
                        benefit_value = (val / 2.0) * dollar_val
                    else:
                        this_user_weight = val
                        benefit_value = val * dollar_val

                    total_value += benefit_value
                    total_user_weight += this_user_weight
                    total_max_weight += this_max_weight
                except (ValueError, IndexError):
                    total_max_weight += this_max_weight
                    continue
            else:
                total_max_weight += this_max_weight

        net_profit = total_value - annual_fee
        fit_percentage = 0
        if total_max_weight > 0:
            fit_percentage = (total_user_weight / total_max_weight) * 100

        optimization_score = min(max(int(fit_percentage), 0), 100)

        return {
            "annual_fee": annual_fee,
            "total_value": round(total_value, 2),
            "net_profit": round(net_profit, 2),
            "optimization_score": optimization_score,
            "is_worth_it": net_profit >= 0,
            "verdict": "Profitably Freakish"
            if net_profit >= 0
            else "Not Quite Essential",
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.get("/spend-it/categories/")
def spend_it_categories(request):
    """Get category list for Spend It calculator."""
    try:
        json_path = os.path.join(
            settings.BASE_DIR, "walletfreak_data", "categories_list.json"
        )
        categories = []

        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                categories = json.load(f)

        ignored = [
            "Financial & Rewards",
            "Protection",
            "Travel Perks",
            "Financial Rewards",
            "Charity",
        ]
        categories = [c for c in categories if c.get("CategoryName") not in ignored]

        icon_mapping = {
            "Airlines": "airplane",
            "Hotels": "office-building",
            "Dining": "silverware-fork-knife",
            "Groceries": "cart",
            "Gas": "gas-station",
            "Transit": "train",
            "Car Rentals": "car",
            "Retail Shopping": "shopping",
            "Entertainment": "ticket",
            "Business": "briefcase",
            "Health": "heart-pulse",
            "Wellness": "spa",
            "Travel Portals": "earth",
            "Lounges": "sofa",
            "Delivery": "truck-delivery",
            "Home Improvement": "hammer",
            "Utilities": "lightning-bolt",
            "Telecom": "cellphone",
            "Streaming": "television",
            "Education": "school",
            "Pet Care": "paw",
            "Fixed Expenses": "calendar",
            "Cruises": "ferry",
        }

        result = []
        for cat in categories:
            name = cat.get("CategoryName", "")
            result.append(
                {
                    "name": name,
                    "icon": icon_mapping.get(name, "circle-outline"),
                    "sub_categories": cat.get("CategoryNameDetailed", []),
                }
            )

        return {"categories": result}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/spend-it/calculate/")
def spend_it_calculate(request):
    """Calculate best cards for a specific purchase."""
    uid = request.auth
    try:
        body = json.loads(request.body)
        amount = float(body.get("amount", 0))
        category = body.get("category", "").strip()
        sub_category = body.get("sub_category", "").strip()

        if not category and not sub_category:
            category = "Everything Else"

        # Get user wallet
        user_wallet_slugs = set()
        owned_cards = db.get_user_cards(uid)
        user_wallet_slugs = {c.get("card_id") for c in owned_cards}

        # Resolve parent/specific/sibling categories
        json_path = os.path.join(
            settings.BASE_DIR, "walletfreak_data", "categories_list.json"
        )
        parent_category = None
        specific_category = sub_category or category
        sibling_categories = []

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    mapping = json.load(f)

                for item in mapping:
                    cat_name = item.get("CategoryName")
                    detailed = item.get("CategoryNameDetailed", [])

                    if specific_category == cat_name or specific_category in detailed:
                        generic_fallback = next(
                            (d for d in detailed if d.startswith("Generic ")), None
                        )
                        parent_category = generic_fallback or cat_name
                        sibling_categories = [
                            d
                            for d in detailed
                            if d != specific_category and d != parent_category
                        ]
                        break

                if not parent_category and specific_category == "Everything Else":
                    parent_category = "All Purchases"
            except Exception:
                pass

        service = OptimizerService()
        results = service.calculate_spend_recommendations(
            amount=amount,
            specific_category=specific_category,
            parent_category=parent_category,
            user_wallet_slugs=user_wallet_slugs,
            sibling_categories=sibling_categories,
        )

        # Serialize results for JSON
        def serialize_result(item):
            card = item.get("card", {})
            return {
                "slug": item.get("slug"),
                "card_name": item.get("card_name"),
                "issuer": card.get("issuer"),
                "annual_fee": card.get("annual_fee", 0),
                "est_points": item.get("est_points", 0),
                "est_value": round(item.get("est_value", 0), 2),
                "earning_rate": item.get("earning_rate"),
                "category_matched": item.get("category_matched"),
                "currency_display": item.get("currency_display"),
                "match_type": item.get("match_type"),
                "is_winner": item.get("is_winner", False),
            }

        wallet_results = [serialize_result(r) for r in results.get("wallet", [])]
        opportunity_results = [
            serialize_result(r) for r in results.get("opportunities", [])
        ]

        return {
            "wallet_results": wallet_results[:10],
            "opportunity_results": opportunity_results[:5],
            "lost_value": round(results.get("lost_value", 0), 2),
            "net_gain": round(results.get("net_gain", 0), 2),
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/sub-optimizer/calculate/")
def sub_optimizer_calculate(request):
    """Calculate SUB (Sign-Up Bonus) Optimizer recommendations."""
    uid = request.auth
    try:
        body = json.loads(request.body)
        planned_spend = float(body.get("planned_spend", 4000))
        duration_months = int(body.get("duration_months", 3))
        sort_by = body.get("sort_by", "recommended")

        user_wallet_slugs = set()
        try:
            owned_cards = db.get_user_cards(uid)
            user_wallet_slugs = {c.get("card_id") for c in owned_cards}
        except Exception:
            pass

        match_scores = {}
        try:
            match_scores = db.calculate_match_scores(uid)
        except Exception:
            pass

        all_cards = db.get_cards()
        monthly_capacity = planned_spend / max(duration_months, 1)
        candidates = []

        for card in all_cards:
            card_id = card.get("slug") or card.get("id")
            if card_id in user_wallet_slugs:
                continue

            bonus_data = card.get("sign_up_bonus")
            if not bonus_data or not bonus_data.get("value"):
                continue

            req_spend = float(bonus_data.get("spend_amount", 0) or 0)
            req_months = float(bonus_data.get("duration_months", 3) or 3)
            if req_spend > planned_spend:
                continue
            monthly_req = req_spend / max(req_months, 1)
            if monthly_req > monthly_capacity + 1.0:
                continue

            bonus_qty = float(bonus_data.get("value", 0) or 0)
            bonus_currency = bonus_data.get("currency", "Points")
            cpp = float(card.get("points_value_cpp", 1.0) or 1.0)

            if "cash" in bonus_currency.lower():
                bonus_value = bonus_qty
            else:
                bonus_value = bonus_qty * (cpp / 100.0)

            earning_rates = card.get("earning_rates", [])
            default_rate = next((er for er in earning_rates if er.get("is_default")), None)
            if not default_rate and earning_rates:
                default_rate = earning_rates[0]

            ongoing_rate_dollar = 0
            if default_rate:
                rate_val = float(default_rate.get("multiplier", default_rate.get("rate", 1)) or 1)
                rate_currency = default_rate.get("currency", "points")
                if "cash" in rate_currency.lower():
                    ongoing_rate_dollar = rate_val / 100.0
                else:
                    ongoing_rate_dollar = rate_val * (cpp / 100.0)

            annual_fee = float(card.get("annual_fee", 0) or 0)
            total_value = bonus_value + (planned_spend * ongoing_rate_dollar)
            net_value = total_value - annual_fee
            roi = (net_value / planned_spend) * 100 if planned_spend > 0 else 0
            match_score = match_scores.get(card_id, 0) or 0
            rank_score = net_value + (match_score * 2.0) if sort_by == "recommended" else net_value

            candidates.append({
                "slug": card_id,
                "name": card.get("name", ""),
                "issuer": card.get("issuer", ""),
                "annual_fee": annual_fee,
                "bonus_display": f"{int(bonus_qty):,} {bonus_currency}" if bonus_qty else "",
                "bonus_value": round(bonus_value, 2),
                "spend_requirement": f"${int(req_spend):,} in {int(req_months)} mo" if req_spend else "",
                "ongoing_rate": f"+${ongoing_rate_dollar:.3f}/$",
                "total_value": round(total_value, 2),
                "net_value": round(net_value, 2),
                "roi": round(roi, 1),
                "match_score": match_score,
                "is_top_pick": False,
                "is_fee_neutral": net_value >= 0 and annual_fee > 0,
            })

        candidates.sort(key=lambda x: x.get("rank_score", x["net_value"]), reverse=True)
        results = candidates[:10]
        if results:
            results[0]["is_top_pick"] = True

        return {"results": results}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
