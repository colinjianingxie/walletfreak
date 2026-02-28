from ninja import Router
from django.http import JsonResponse
from django.conf import settings
from core.services import db
from api.auth_middleware import BearerAuth
import stripe
import json

router = Router(tags=["subscriptions"], auth=BearerAuth())

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/checkout/")
def create_checkout(request):
    """Create Stripe checkout session with mobile deep link URLs."""
    uid = request.auth
    try:
        body = json.loads(request.body)
        price_id = body.get("price_id")

        if not price_id:
            return JsonResponse({"error": "price_id required"}, status=400)

        profile = db.get_user_profile(uid)
        email = profile.get("email", "") if profile else ""

        # Use deep links for mobile
        success_url = body.get(
            "success_url",
            "walletfreak://subscription/success?session_id={CHECKOUT_SESSION_ID}",
        )
        cancel_url = body.get("cancel_url", "walletfreak://subscription/cancel")

        # Check for existing Stripe customer
        customer_id = profile.get("stripe_customer_id") if profile else None

        checkout_params = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {"firebase_uid": uid},
        }

        if customer_id:
            checkout_params["customer"] = customer_id
        else:
            checkout_params["customer_email"] = email

        session = stripe.checkout.Session.create(**checkout_params)

        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.post("/portal/")
def create_portal(request):
    """Create Stripe billing portal session."""
    uid = request.auth
    try:
        profile = db.get_user_profile(uid)
        customer_id = profile.get("stripe_customer_id") if profile else None

        if not customer_id:
            return JsonResponse({"error": "No subscription found"}, status=400)

        return_url = "walletfreak://subscription"
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        return {"portal_url": session.url}
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@router.get("/status/")
def subscription_status(request):
    """Get current subscription status."""
    uid = request.auth
    try:
        profile = db.get_user_profile(uid)
        if not profile:
            return {"is_premium": False}

        return {
            "is_premium": profile.get("is_premium", False),
            "subscription_status": profile.get("subscription_status"),
            "current_period_end": str(profile.get("current_period_end", "")),
            "cancel_at_period_end": profile.get("cancel_at_period_end", False),
        }
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
