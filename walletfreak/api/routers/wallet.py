from ninja import Router
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
from api.schemas.wallet import (
    AddCardRequest,
    UpdateStatusRequest,
    UpdateAnniversaryRequest,
    UpdateBenefitRequest,
    ToggleIgnoreRequest,
    RemoveCardRequest,
)
from api.schemas.common import SuccessResponse, ErrorResponse
from datetime import datetime, timedelta
from calendar import monthrange
from cards.templatetags.card_extras import resolve_card_image_url
import json

router = Router(tags=["wallet"], auth=BearerAuth())


@router.get("/")
def get_wallet(request):
    """Get full dashboard data with benefit calculations.

    This is a direct port of dashboard/views/main.py:dashboard()
    """
    uid = request.auth  # set by BearerAuth

    # Get user cards by status
    try:
        active_cards = db.get_user_cards(uid, status="active")
        inactive_cards = db.get_user_cards(uid, status="inactive")
        eyeing_cards = db.get_user_cards(uid, status="eyeing")
    except Exception:
        active_cards, inactive_cards, eyeing_cards = [], [], []

    # Get personality
    try:
        assigned_personality = db.get_user_assigned_personality(uid)
    except Exception:
        assigned_personality = None

    # Get all cards for lookup
    try:
        all_cards = db.get_cards()
    except Exception:
        all_cards = []

    cards_map = {c["id"]: c for c in all_cards}

    # Calculate benefits
    action_needed_benefits = []
    maxed_out_benefits = []
    ignored_benefits = []
    total_used_value = 0
    total_potential_value = 0
    total_annual_fee = 0

    current_year = datetime.now().year
    current_month = datetime.now().month
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    for card in active_cards:
        try:
            card_details = cards_map.get(card["card_id"])
            if not card_details:
                continue

            card["image_url"] = card_details.get("image_url")
            card["name"] = card_details.get("name")

            total_annual_fee += card_details.get("annual_fee") or 0

            anniversary_date_str = card.get("anniversary_date", "")
            anniversary_date = None

            if anniversary_date_str == "default":
                anniversary_month = 1
                anniversary_year = current_year - 1
            elif anniversary_date_str:
                try:
                    anniversary_date = datetime.strptime(anniversary_date_str, "%Y-%m-%d")
                    anniversary_month = anniversary_date.month
                    anniversary_year = anniversary_date.year
                except Exception:
                    anniversary_month = 1
                    anniversary_year = current_year
            else:
                anniversary_month = 1
                anniversary_year = current_year

            for idx, benefit in enumerate(card_details.get("benefits", [])):
                benefit_type = benefit.get("benefit_type")
                if benefit_type in ["Protection", "Bonus", "Perk", "Lounge", "Status", "Insurance"]:
                    continue

                dollar_value = benefit.get("dollar_value")
                if not dollar_value or dollar_value <= 0:
                    continue

                benefit_id = benefit.get("id") or str(idx)
                frequency = benefit.get("time_category", "Annually (calendar year)")
                benefit_usage_data = card.get("benefit_usage", {}).get(benefit_id, {})

                periods = []
                current_period_status = "empty"
                current_period_used = 0
                ytd_used = 0
                period_values = benefit.get("period_values", {})

                if "monthly" in frequency.lower():
                    for m_idx, m_name in enumerate(months):
                        period_key = f"{current_year}_{m_idx+1:02d}"
                        period_max = period_values.get(period_key, dollar_value / 12)
                        if anniversary_year < current_year:
                            is_available = (m_idx + 1) <= current_month
                        else:
                            is_available = (m_idx + 1) >= anniversary_month and (m_idx + 1) <= current_month

                        p_data = benefit_usage_data.get("periods", {}).get(period_key, {})
                        p_used = p_data.get("used") or 0
                        ytd_used += p_used
                        p_full = p_data.get("is_full", False)

                        status = "full" if (p_full or p_used >= period_max) else ("partial" if p_used > 0 else "empty")
                        periods.append({
                            "label": m_name, "key": period_key, "status": status,
                            "is_current": (m_idx + 1) == current_month,
                            "max_value": period_max, "is_available": is_available, "used": p_used,
                        })
                        if (m_idx + 1) == current_month:
                            current_period_status = status
                            current_period_used = p_used

                elif "quarterly" in frequency.lower():
                    curr_q = (current_month - 1) // 3 + 1
                    anniversary_q = (anniversary_month - 1) // 3 + 1
                    for q in range(1, 5):
                        q_key = f"{current_year}_Q{q}"
                        q_max = period_values.get(q_key, dollar_value / 4)
                        if anniversary_year < current_year:
                            q_available = q <= curr_q
                        else:
                            q_available = q >= anniversary_q and q <= curr_q
                        q_data = benefit_usage_data.get("periods", {}).get(q_key, {})
                        p_used = q_data.get("used") or 0
                        ytd_used += p_used
                        q_status = "full" if (q_data.get("is_full") or p_used >= q_max) else ("partial" if p_used > 0 else "empty")
                        periods.append({
                            "label": f"Q{q}", "key": q_key, "status": q_status,
                            "is_current": q == curr_q, "max_value": q_max,
                            "is_available": q_available, "used": p_used,
                        })
                        if q == curr_q:
                            current_period_status = q_status
                            current_period_used = p_used

                elif "semi-annually" in frequency.lower():
                    h1_key = f"{current_year}_H1"
                    h2_key = f"{current_year}_H2"
                    h1_max = period_values.get(h1_key, dollar_value / 2)
                    h2_max = period_values.get(h2_key, dollar_value / 2)

                    h1_data = benefit_usage_data.get("periods", {}).get(h1_key, {})
                    h1_status = "full" if (h1_data.get("is_full") or (h1_data.get("used") or 0) >= h1_max) else ("partial" if (h1_data.get("used") or 0) > 0 else "empty")
                    h1_available = current_month >= 1 if anniversary_year < current_year else (anniversary_month <= 6 and current_month >= 1)
                    periods.append({"label": "H1", "key": h1_key, "status": h1_status, "is_current": current_month <= 6, "max_value": h1_max, "is_available": h1_available, "used": h1_data.get("used") or 0})

                    h2_data = benefit_usage_data.get("periods", {}).get(h2_key, {})
                    h2_status = "full" if (h2_data.get("is_full") or (h2_data.get("used") or 0) >= h2_max) else ("partial" if (h2_data.get("used") or 0) > 0 else "empty")
                    h2_available = current_month >= 7 if anniversary_year < current_year else ((anniversary_month <= 6 and current_month >= 7) or (anniversary_month >= 7 and current_month >= anniversary_month))
                    periods.append({"label": "H2", "key": h2_key, "status": h2_status, "is_current": current_month > 6, "max_value": h2_max, "is_available": h2_available, "used": h2_data.get("used") or 0})

                    if current_month <= 6:
                        current_period_status = h1_status
                        current_period_used = h1_data.get("used") or 0
                    else:
                        current_period_status = h2_status
                        current_period_used = h2_data.get("used") or 0
                    ytd_used = (h1_data.get("used") or 0) + (h2_data.get("used") or 0)

                elif "every 4 years" in frequency.lower():
                    # Every 4 years frequency
                    if anniversary_date:
                        this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day)
                        if datetime.now() < this_year_anniv:
                            annual_start_year = current_year - 1
                        else:
                            annual_start_year = current_year
                    else:
                        annual_start_year = current_year

                    base_year = anniversary_year if anniversary_year else 2020
                    block_idx = (annual_start_year - base_year) // 4
                    block_start_year = base_year + (block_idx * 4)
                    block_end_year = block_start_year + 4

                    period_key = f"{block_start_year}_{block_end_year}"

                    if anniversary_date:
                        reset_date_obj = datetime(block_end_year, anniversary_month, anniversary_date.day)
                        reset_date_str = reset_date_obj.strftime("%b %d, %Y")
                    else:
                        reset_date_str = f"Dec 31, {block_end_year}"

                    p_data = benefit_usage_data.get("periods", {}).get(period_key, {})
                    p_used = p_data.get("used") or 0
                    p_full = p_data.get("is_full", False)

                    status = "full" if (p_full or p_used >= dollar_value) else ("partial" if p_used > 0 else "empty")
                    periods.append({
                        "label": f"{block_start_year}-{block_end_year}",
                        "key": period_key, "status": status,
                        "is_current": True, "max_value": dollar_value, "used": p_used,
                        "reset_date": reset_date_str,
                    })
                    current_period_status = status
                    current_period_used = p_used
                    ytd_used = p_used

                else:
                    # Annual / Anniversary
                    if "anniversary" in frequency.lower() and anniversary_date:
                        now_date = datetime.now()
                        this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day)
                        if now_date < this_year_anniv:
                            start_year = current_year - 1
                        else:
                            start_year = current_year
                        period_key = str(start_year)
                        end_year = start_year + 1
                        reset_date_obj = datetime(end_year, anniversary_month, anniversary_date.day)
                        reset_date_str = reset_date_obj.strftime("%b %d, %Y")
                    else:
                        period_key = str(current_year)
                        reset_date_str = f"Dec 31, {current_year}"

                    p_data = benefit_usage_data.get("periods", {}).get(period_key, {})
                    p_used = p_data.get("used") or 0
                    p_full = p_data.get("is_full", False)
                    status = "full" if (p_full or p_used >= dollar_value) else ("partial" if p_used > 0 else "empty")
                    periods.append({
                        "label": str(current_year), "key": period_key, "status": status,
                        "is_current": True, "max_value": dollar_value, "used": p_used,
                        "reset_date": reset_date_str,
                    })
                    current_period_status = status
                    current_period_used = p_used
                    ytd_used = p_used

                # Days until expiration
                days_until_expiration = None
                now = datetime.now()
                if "monthly" in frequency.lower():
                    last_day = monthrange(current_year, current_month)[1]
                    period_end = datetime(current_year, current_month, last_day, 23, 59, 59)
                    days_until_expiration = (period_end - now).days
                elif "quarterly" in frequency.lower():
                    curr_q = (current_month - 1) // 3 + 1
                    qem = curr_q * 3
                    last_day = monthrange(current_year, qem)[1]
                    period_end = datetime(current_year, qem, last_day, 23, 59, 59)
                    days_until_expiration = (period_end - now).days
                elif "semi-annually" in frequency.lower():
                    period_end = datetime(current_year, 6, 30, 23, 59, 59) if current_month <= 6 else datetime(current_year, 12, 31, 23, 59, 59)
                    days_until_expiration = (period_end - now).days
                else:
                    period_end = datetime(current_year, 12, 31, 23, 59, 59)
                    days_until_expiration = (period_end - now).days

                is_ignored = benefit_usage_data.get("is_ignored", False)

                benefit_obj = {
                    "user_card_id": card["id"],
                    "card_id": card["card_id"],
                    "card_name": card_details["name"],
                    "benefit_id": benefit_id,
                    "benefit_name": benefit["description"],
                    "amount": dollar_value,
                    "used": current_period_used,
                    "periods": periods,
                    "frequency": frequency,
                    "current_period_status": current_period_status,
                    "days_until_expiration": days_until_expiration,
                    "is_ignored": is_ignored,
                    "ytd_used": ytd_used,
                    "additional_details": benefit.get("additional_details"),
                    "benefit_type": benefit_type,
                }

                if is_ignored:
                    ignored_benefits.append(benefit_obj)
                elif current_period_status == "full":
                    maxed_out_benefits.append(benefit_obj)
                else:
                    action_needed_benefits.append(benefit_obj)

                if not is_ignored:
                    total_potential_value += sum(p.get("max_value", 0) for p in periods)

                if (benefit_type == "Credit" or benefit_type == "Perk") and not is_ignored:
                    total_used_value += ytd_used
        except Exception:
            continue

    # Chase 5/24 calculation
    card_524_map = {c["id"]: c.get("is_524", True) for c in all_cards}
    cutoff_date = datetime.now() - timedelta(days=365 * 2)
    chase_524_count = 0

    for card in active_cards + inactive_cards:
        card_id = card.get("card_id")
        if not card_524_map.get(card_id, True):
            continue
        ann_date_str = card.get("anniversary_date")
        if ann_date_str == "default":
            continue
        if ann_date_str:
            try:
                ann_date = datetime.strptime(ann_date_str, "%Y-%m-%d")
                if ann_date >= cutoff_date:
                    chase_524_count += 1
            except ValueError:
                pass

    # Serialize cards for response
    def serialize_card(c):
        return {
            "id": c.get("id"),
            "user_card_id": c.get("id"),
            "card_id": c.get("card_id"),
            "name": c.get("name", ""),
            "issuer": c.get("issuer", ""),
            "status": c.get("status", ""),
            "anniversary_date": c.get("anniversary_date", ""),
            "annual_fee": c.get("annual_fee", 0),
            "image_url": c.get("image_url", ""),
        }

    return {
        "active_cards": [serialize_card(c) for c in active_cards],
        "inactive_cards": [serialize_card(c) for c in inactive_cards],
        "eyeing_cards": [serialize_card(c) for c in eyeing_cards],
        "personality": {
            "id": assigned_personality.get("id"),
            "name": assigned_personality.get("name"),
            "match_score": assigned_personality.get("match_score", 0),
        }
        if assigned_personality
        else None,
        "action_needed_benefits": action_needed_benefits,
        "maxed_out_benefits": maxed_out_benefits,
        "ignored_benefits": ignored_benefits,
        "total_extracted_value": round(total_used_value, 2),
        "total_potential_value": round(total_potential_value, 2),
        "total_annual_fee": total_annual_fee,
        "net_performance": round(total_used_value - total_annual_fee, 2),
        "chase_524_count": chase_524_count,
        "chase_eligible": chase_524_count < 5,
    }


@router.post("/add-card/{card_id}/")
def add_card(request, card_id: str, payload: AddCardRequest):
    uid = request.auth
    try:
        success = db.add_card_to_user(
            uid, card_id, status=payload.status, anniversary_date=payload.anniversary_date
        )
        if success:
            personality = db.get_user_assigned_personality(uid)
            personality_data = None
            if personality:
                personality_data = {
                    "id": personality.get("id"),
                    "name": personality.get("name"),
                    "match_score": personality.get("match_score", 0),
                }
            return {"success": True, "personality": personality_data}
        return JsonResponse({"success": False, "error": "Card not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@router.post("/remove-card/{user_card_id}/")
def remove_card(request, user_card_id: str, payload: RemoveCardRequest):
    uid = request.auth
    try:
        deleted_card_slug = db.remove_card_from_user(uid, user_card_id)
        if deleted_card_slug and payload.delete_loyalty_program:
            master_card = db.get_card_by_slug(deleted_card_slug)
            if master_card:
                pid = master_card.get("loyalty_program")
                if pid:
                    db.remove_user_loyalty_program(uid, pid)

        personality = db.get_user_assigned_personality(uid)
        personality_data = None
        if personality:
            personality_data = {
                "id": personality.get("id"),
                "name": personality.get("name"),
                "match_score": personality.get("match_score", 0),
            }
        return {"success": True, "personality": personality_data}
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@router.post("/update-status/{user_card_id}/")
def update_status(request, user_card_id: str, payload: UpdateStatusRequest):
    uid = request.auth
    if payload.status not in ["active", "inactive", "eyeing"]:
        return JsonResponse({"success": False, "error": "Invalid status"}, status=400)
    try:
        db.update_card_status(uid, user_card_id, payload.status)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@router.post("/update-anniversary/{user_card_id}/")
def update_anniversary(request, user_card_id: str, payload: UpdateAnniversaryRequest):
    uid = request.auth
    try:
        update_data = {"anniversary_date": payload.anniversary_date, "benefit_usage": {}}
        db.update_card_details(uid, user_card_id, update_data)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@router.post("/update-benefit/{user_card_id}/{benefit_id}/")
def update_benefit(request, user_card_id: str, benefit_id: str, payload: UpdateBenefitRequest):
    uid = request.auth
    try:
        db.update_benefit_usage(
            uid, user_card_id, benefit_id, payload.amount,
            period_key=payload.period_key, is_full=payload.is_full,
            increment=payload.increment,
        )
        return {"success": True}
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@router.post("/toggle-ignore-benefit/{user_card_id}/{benefit_id}/")
def toggle_ignore_benefit(request, user_card_id: str, benefit_id: str, payload: ToggleIgnoreRequest):
    uid = request.auth
    try:
        db.toggle_benefit_ignore(uid, user_card_id, benefit_id, payload.is_ignored)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@router.get("/check-delete/{user_card_id}/")
def check_delete(request, user_card_id: str):
    uid = request.auth
    try:
        all_cards = db.get_user_cards(uid, status="active", hydrate=True)
        target_card = next((c for c in all_cards if c["user_card_id"] == user_card_id), None)
        if not target_card:
            all_cards_all = db.get_user_cards(uid, hydrate=True)
            target_card = next((c for c in all_cards_all if c["user_card_id"] == user_card_id), None)
        if not target_card:
            return JsonResponse({"success": False, "error": "Card not found"}, status=404)

        loyalty_pid = target_card.get("loyalty_program")
        if not loyalty_pid:
            return {"will_be_removed": False, "message": "No loyalty program linked."}

        other_cards_count = sum(
            1 for c in all_cards
            if c.get("loyalty_program") == loyalty_pid
            and str(c.get("user_card_id", "")).strip() != user_card_id.strip()
        )

        program_name = loyalty_pid
        prog_info = db.get_document("program_loyalty", loyalty_pid)
        if prog_info:
            program_name = prog_info.get("program_name", loyalty_pid)

        return {
            "will_be_removed": other_cards_count == 0,
            "program_name": program_name,
            "program_id": loyalty_pid,
            "other_cards_count": other_cards_count,
        }
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
