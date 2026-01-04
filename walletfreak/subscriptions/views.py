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

def subscription_home(request):
    subscription = None
    if request.user.is_authenticated:
        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            subscription = None

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

        # Define valid price IDs
        PRICE_MONTHLY = settings.STRIPE_PRICE_MONTHLY
        PRICE_YEARLY = settings.STRIPE_PRICE_YEARLY
        
        # Default to monthly if not specified or invalid
        requested_price_id = request.POST.get('priceId')
        if requested_price_id not in [PRICE_MONTHLY, PRICE_YEARLY]:
            requested_price_id = PRICE_MONTHLY

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer.stripe_customer_id,
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
                client_reference_id=str(request.user.id),
            )
        except stripe.error.InvalidRequestError as e:
            if "No such customer" in str(e):
                logger.warning(f"Stripe Customer {stripe_customer.stripe_customer_id} not found. Re-creating...")
                # Re-create customer in current environment
                customer = stripe.Customer.create(
                    email=request.user.email,
                    metadata={'user_id': request.user.id}
                )
                stripe_customer.stripe_customer_id = customer.id
                stripe_customer.save()
                
                # Retry creating session with new customer ID
                checkout_session = stripe.checkout.Session.create(
                    customer=stripe_customer.stripe_customer_id,
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
                    client_reference_id=str(request.user.id),
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
        # Get Stripe Customer
        stripe_customer = StripeCustomer.objects.get(user=request.user)
        
        # Determine return URL (profile page)
        return_url = request.build_absolute_uri('/accounts/profile/')
        
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer.stripe_customer_id,
            return_url=return_url,
        )
        
        return redirect(portal_session.url, code=303)
    except StripeCustomer.DoesNotExist:
        # If no stripe customer, they likely aren't subscribed or it's an error
        # Redirect to pricing?
        logger.warning(f"User {request.user.id} attempted to access portal without Stripe Customer ID.")
        return redirect('subscription_home')
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
            
            # Sync with Firestore to ensure immediate premium access
            db.update_user_subscription(
                user.username,
                'active',
                subscription_id=stripe_subscription_id
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
        db.update_user_subscription(
            user.username, 
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
