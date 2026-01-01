from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import stripe
from core.services import db

stripe.api_key = settings.STRIPE_SECRET_KEY

def pricing_page(request):
    """Render the pricing page"""
    return render(request, 'subscriptions/pricing.html', {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'is_premium': db.is_premium(request.session.get('uid')) if request.session.get('uid') else False
    })

@login_required
def create_checkout_session(request):
    """Create a Stripe Checkout Session"""
    if request.method == 'POST':
        try:
            domain_url = settings.CSRF_TRUSTED_ORIGINS[0] # taking first one as base for now, might need better logic
            # Better to use request.build_absolute_uri('/') but need to handle potential http/https issues behind proxies
            # Let's use relative URLs which Stripe supports if we provide full URL
            
            # Construct base URL from request
            host = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            base_url = f"{protocol}://{host}"

            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=base_url + '/subscriptions/success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=base_url + '/subscriptions/cancel/',
                client_reference_id=request.session.get('uid'),
                customer_email=request.user.email,
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return JsonResponse({'error': str(e)})

    return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    return HttpResponse(status=200)

def handle_checkout_session_completed(session):
    """Grant premium access"""
    uid = session.get('client_reference_id')
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    
    if uid:
        db.set_premium(uid, True)
        # We might want to store subscription details too
        db.update_user_subscription(uid, {
            'stripe_customer_id': customer_id,
            'stripe_subscription_id': subscription_id,
            'subscription_status': 'active'
        })

def handle_subscription_deleted(subscription):
    """Revoke premium access"""
    # We need to find the user by customer_id or subscription_id
    # Since we don't have a direct reverse lookup in Firestore efficient without index,
    # we might need to rely on metadata or user storing stripe_customer_id.
    # For now, let's assume we can query by stripe_customer_id if we index it, 
    # OR we rely on client_reference_id if passed (subscription deleted might not have it).
    
    customer_id = subscription.get('customer')
    
    # Needs a way to lookup user by stripe customer id
    # db.find_user_by_stripe_customer_id(customer_id) -> uid
    # For MVP, we might skip this unless we add that lookup method.
    # I will add a method to core/services/db.py (users.py) to handle this lookup or update.
    
    uid = db.get_uid_by_stripe_customer_id(customer_id)
    if uid:
        db.set_premium(uid, False)
        db.update_user_subscription(uid, {
            'subscription_status': 'canceled'
        })

def success(request):
    return render(request, 'subscriptions/success.html')

def cancel(request):
    return render(request, 'subscriptions/cancel.html')
