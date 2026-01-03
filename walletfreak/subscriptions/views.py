import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import StripeCustomer, Subscription
import json
import logging
from django.utils import timezone
from datetime import datetime
from core.services import db

logger = logging.getLogger(__name__)


stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def subscription_home(request):
    try:
        subscription = request.user.subscription
    except Subscription.DoesNotExist:
        subscription = None

    return render(request, 'subscriptions/home.html', {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'subscription': subscription
    })

@login_required
def create_checkout_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        # Get or create Stripe Customer
        stripe_customer, created = StripeCustomer.objects.get_or_create(user=request.user)
        
        if created:
            # Create customer in Stripe
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={'user_id': request.user.id}
            )
            stripe_customer.stripe_customer_id = customer.id
            stripe_customer.save()
        elif not stripe_customer.stripe_customer_id:
             # Fallback if model exists but ID is missing (shouldn't happen but safe)
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={'user_id': request.user.id}
            )
            stripe_customer.stripe_customer_id = customer.id
            stripe_customer.save()

        # You should replace this with your actual Price ID from Stripe Dashboard
        # For now, we'll assume it's passed or hardcoded. 
        # Ideally, use an environment variable or a constant.
        PRICE_ID = 'price_1Qhk... (replace me)' # TODO: User needs to put their price ID here
        
        # If user passed a price_id (e.g. from frontend hidden input)
        requested_price_id = request.POST.get('priceId')
        if requested_price_id:
            PRICE_ID = requested_price_id

        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': PRICE_ID,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri('/subscriptions/success/'),
            cancel_url=request.build_absolute_uri('/subscriptions/cancel/'),
            client_reference_id=str(request.user.id),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
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
        # Fulfill the purchase...
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
    
    if client_reference_id:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=client_reference_id)
            
            # Ensure StripeCustomer exists and is linked
            StripeCustomer.objects.get_or_create(
                user=user,
                defaults={'stripe_customer_id': stripe_customer_id}
            )
            
            # Create or update Subscription
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    'stripe_subscription_id': stripe_subscription_id,
                    'status': 'active', # We assume active on success
                }
            )
        except User.DoesNotExist:
            logger.error(f"User with ID {client_reference_id} not found during webhook processing.")

def handle_subscription_updated(stripe_sub):
    stripe_customer_id = stripe_sub.get('customer')
    # Find user by strip customer id
    try:
        customer = StripeCustomer.objects.get(stripe_customer_id=stripe_customer_id)
        user = customer.user
        
        status = stripe_sub.get('status')
        current_period_end = datetime.fromtimestamp(stripe_sub.get('current_period_end'), tz=timezone.utc)
        cancel_at_period_end = stripe_sub.get('cancel_at_period_end')
        price_id = stripe_sub['items']['data'][0]['price']['id']

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'status': status,
                'current_period_end': current_period_end,
                'cancel_at_period_end': cancel_at_period_end,
                'price_id': price_id,
                'stripe_subscription_id': stripe_sub.get('id')
            }
        )
        
        # Sync with Firestore
        # user.username is the UID
        is_premium = status in ['active', 'trialing']
        db.update_user_subscription(
            user.username, 
            is_premium, 
            status, 
            subscription_id=stripe_sub.get('id'),
            current_period_end=current_period_end
        )
        
    except StripeCustomer.DoesNotExist:
        logger.error(f"StripeCustomer with ID {stripe_customer_id} not found.")

def handle_invoice_payment_succeeded(invoice):
    # Usually handled by subscription updated, but good for explicit tracking if needed
    pass

def handle_subscription_deleted(stripe_sub):
    stripe_customer_id = stripe_sub.get('customer')
    try:
        customer = StripeCustomer.objects.get(stripe_customer_id=stripe_customer_id)
        user = customer.user
        
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'status': 'canceled',
            }
        )
        
        # Sync with Firestore
        db.update_user_subscription(
            user.username, 
            False, 
            'canceled'
        )
    except StripeCustomer.DoesNotExist:
        logger.error(f"StripeCustomer with ID {stripe_customer_id} not found.")

@login_required
def success(request):
    return render(request, 'subscriptions/success.html')

@login_required
def cancel(request):
    return render(request, 'subscriptions/cancel.html')
