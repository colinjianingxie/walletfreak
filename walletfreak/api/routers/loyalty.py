from ninja import Router
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
import json

router = Router(tags=["loyalty"], auth=BearerAuth())


@router.get("/")
def loyalty_list(request):
    """Get loyalty programs with balances."""
    uid = request.auth
    try:
        all_programs = db.get_all_loyalty_programs()
        programs_map = {p["id"]: p for p in all_programs}

        user_balances = db.get_user_loyalty_balances(uid)
        user_cards = db.get_user_cards(uid, status="active")

        programs_to_display = {}

        for b in user_balances:
            pid = b["program_id"]
            programs_to_display[pid] = {"balance": b.get("balance", 0), "source": "balance"}

        for card in user_cards:
            lp = card.get("loyalty_program")
            if lp and lp not in programs_to_display:
                programs_to_display[lp] = {"balance": 0, "source": "card"}

        display_programs = []
        for pid, data in programs_to_display.items():
            prog_details = programs_map.get(pid, {})
            if not prog_details:
                prog_details = {"program_name": "Unknown Program", "id": pid, "type": "other"}

            balance = data.get("balance", 0)
            valuation = prog_details.get("valuation", 1.0)
            est_value = (balance * valuation) / 100.0

            display_programs.append({
                "program_id": pid,
                "name": prog_details.get("program_name"),
                "type": prog_details.get("type", "other"),
                "balance": balance,
                "valuation": valuation,
                "est_value": est_value,
                "logo_url": prog_details.get("logo_url"),
                "category": prog_details.get("currency_group", "Points"),
            })

        display_programs.sort(key=lambda x: x["name"] or "")
        total_est_value = sum(p["est_value"] for p in display_programs)

        return {
            "programs": display_programs,
            "total_est_value": total_est_value,
            "all_programs": all_programs,
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/add/")
def add_program(request):
    uid = request.auth
    try:
        body = json.loads(request.body)
        program_id = body.get("program_id")
        if not program_id:
            return JsonResponse({"error": "program_id required"}, status=400)
        db.update_user_loyalty_balance(uid, program_id, 0)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/update/")
def update_balance(request):
    uid = request.auth
    try:
        body = json.loads(request.body)
        program_id = body.get("program_id")
        balance = body.get("balance")
        if not program_id or balance is None:
            return JsonResponse({"error": "Missing data"}, status=400)
        db.update_user_loyalty_balance(uid, program_id, balance)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/remove/")
def remove_program(request):
    uid = request.auth
    try:
        body = json.loads(request.body)
        program_id = body.get("program_id")
        if not program_id:
            return JsonResponse({"error": "program_id required"}, status=400)
        db.remove_user_loyalty_program(uid, program_id)
        return {"success": True}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
