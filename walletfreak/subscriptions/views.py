import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import StripeCustomer, Subscription # Keep for now if needed, but logic moves to db
import json
import logging
from django.utils import timezone
from datetime import datetime
from core.services import db

logger = logging.getLogger(__name__)


def subscription_home(request):
    subscription = None
    if request.user.is_authenticated:
        # Get subscription from Firestore
        uid = request.user.username
        subscription = db.get_user_subscription(uid)

    return render(request, 'subscriptions/home.html', {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'subscription': subscription,
        'price_monthly': settings.STRIPE_PRICE_MONTHLY,
        'price_yearly': settings.STRIPE_PRICE_YEARLY,
    })

@login_required
def create_checkout_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        # Debug Logging for API Key issue
        if not stripe.api_key:
            logger.warning("Stripe API key was MISSING. Setting it now.")
            stripe.api_key = settings.STRIPE_SECRET_KEY
        else:
             logger.info(f"Stripe API key present: {stripe.api_key[:4]}...")

        uid = request.user.username
        email = request.user.email
        
        # Get Stripe Customer ID from Firestore
        stripe_customer_id = db.get_user_stripe_id(uid)

        if not stripe_customer_id:
            # Create customer in Stripe
            customer = stripe.Customer.create(
                email=email,
                metadata={'firebase_uid': uid}
            )
            stripe_customer_id = customer.id
            # Save to Firestore
            db.update_user_stripe_id(uid, stripe_customer_id)
        
        # Define valid price IDs
        PRICE_MONTHLY = settings.STRIPE_PRICE_MONTHLY
        PRICE_YEARLY = settings.STRIPE_PRICE_YEARLY
        
        # Default to monthly if not specified or invalid
        requested_price_id = request.POST.get('priceId')
        if requested_price_id not in [PRICE_MONTHLY, PRICE_YEARLY]:
            requested_price_id = PRICE_MONTHLY

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': requested_price_id,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=request.build_absolute_uri('/subscriptions/success/'),
                cancel_url=request.build_absolute_uri('/subscriptions/cancel/'),
                # Use UID as reference, not volatile SQLite ID
                client_reference_id=uid,
            )
        except stripe.error.InvalidRequestError as e:
            if "No such customer" in str(e):
                logger.warning(f"Stripe Customer {stripe_customer_id} not found. Re-creating...")
                # Re-create customer
                customer = stripe.Customer.create(
                    email=email,
                    metadata={'firebase_uid': uid}
                )
                stripe_customer_id = customer.id
                db.update_user_stripe_id(uid, stripe_customer_id)
                
                # Retry creating session
                checkout_session = stripe.checkout.Session.create(
                    customer=stripe_customer_id,
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price': requested_price_id,
                            'quantity': 1,
                        },
                    ],
                    mode='subscription',
                    success_url=request.build_absolute_uri('/subscriptions/success/'),
                    cancel_url=request.build_absolute_uri('/subscriptions/cancel/'),
                    client_reference_id=uid,
                )
            else:
                raise e

        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_portal_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        uid = request.user.username
        stripe_customer_id = db.get_user_stripe_id(uid)
        
        if not stripe_customer_id:
            logger.warning(f"User {uid} attempted to access portal without Stripe Customer ID.")
            return redirect('subscription_home')
        
        # Determine return URL (profile page)
        return_url = request.build_absolute_uri('/accounts/profile/')
        
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )
        
        return redirect(portal_session.url, code=303)
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
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
        handle_checkout_session(session)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_invoice_payment_succeeded(invoice)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)

    return HttpResponse(status=200)

def handle_checkout_session(session):
    client_reference_id = session.get('client_reference_id')
    stripe_customer_id = session.get('customer')
    stripe_subscription_id = session.get('subscription')
    
    # client_reference_id is now the Firebase UID
    if client_reference_id:
        uid = client_reference_id
        
        # Update Stripe ID if not set (or ensure it matches)
        db.update_user_stripe_id(uid, stripe_customer_id)
        
        # Update Subscription Status in Firestore
        # We assume active on success
        db.update_subscription(
            uid,
            'active',
            subscription_id=stripe_subscription_id
        )
    else:
        logger.error("No client_reference_id found in session.")

def handle_subscription_updated(stripe_sub):
    stripe_customer_id = stripe_sub.get('customer')
    # Use Stripe API or metadata to find user? 
    # Since we don't have reverse lookup easily in Firestore without query,
    # rely on the fact that we put user_id in metadata when creating customer?
    # Or query Firestore users where stripe_customer_id == X
    
    # Query Firestore for the user with this stripe_id
    users_ref = db.db.collection('users')
    query = users_ref.where('stripe_customer_id', '==', stripe_customer_id).limit(1)
    docs = query.stream()
    
    user_doc = None
    for doc in docs:
        user_doc = doc
        break
        
    if not user_doc:
        logger.error(f"Firestore User with Stripe ID {stripe_customer_id} not found.")
        return

    uid = user_doc.id
    
    status = stripe_sub.get('status')
    current_period_end = datetime.fromtimestamp(stripe_sub.get('current_period_end'), tz=timezone.utc)
    cancel_at_period_end = stripe_sub.get('cancel_at_period_end')
    
    # Robustly get price ID
    items = stripe_sub.get('items', {})
    data_items = items.get('data', [])
    price_id = None
    if data_items:
        price_id = data_items[0].get('price', {}).get('id')

    # Sync with Firestore
    db.update_subscription(
        uid, 
        status, 
        subscription_id=stripe_sub.get('id'),
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
        price_id=price_id
    )

def handle_invoice_payment_succeeded(invoice):
    pass

def handle_subscription_deleted(stripe_sub):
    stripe_customer_id = stripe_sub.get('customer')
    
    # Find user
    users_ref = db.db.collection('users')
    query = users_ref.where('stripe_customer_id', '==', stripe_customer_id).limit(1)
    docs = query.stream()
    
    user_doc = None
    for doc in docs:
        user_doc = doc
        break
        
    if not user_doc:
         logger.error(f"Firestore User with Stripe ID {stripe_customer_id} not found.")
         return

    uid = user_doc.id
    
    # Sync with Firestore
    db.update_subscription(
        uid, 
        'canceled'
    )

@login_required
def success(request):
    return render(request, 'subscriptions/success.html')

@login_required
def cancel(request):
    return render(request, 'subscriptions/cancel.html')
