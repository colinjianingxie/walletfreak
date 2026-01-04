from django.core.management.base import BaseCommand
from django.conf import settings
import stripe

class Command(BaseCommand):
    help = 'Initialize Stripe Products and Prices'

    def handle(self, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        product_name = "Wallet Freak Premium"
        
        # Check if product exists
        existing_products = stripe.Product.search(query=f"name:'{product_name}'")
        
        if existing_products['data']:
            product = existing_products['data'][0]
            self.stdout.write(self.style.SUCCESS(f"Product '{product_name}' already exists: {product.id}"))
        else:
            product = stripe.Product.create(name=product_name)
            self.stdout.write(self.style.SUCCESS(f"Created Product '{product_name}': {product.id}"))

        # Create Prices
        # Monthly: $4.99
        self.create_price(product.id, 499, 'month', 'monthly')
        
        # Yearly: $49.99
        self.create_price(product.id, 4999, 'year', 'yearly')

    def create_price(self, product_id, amount_cents, interval, lookup_key):
        # Check if price with lookup_key exists to avoid duplicates
        # Note: lookup_keys are good for unique identification.
        
        try:
             prices = stripe.Price.list(
                product=product_id,
                lookup_keys=[lookup_key],
                limit=1
            )
             if prices['data']:
                 price = prices['data'][0]
                 self.stdout.write(self.style.SUCCESS(f"Price '{lookup_key}' already exists: {price.id}"))
                 return price
        except Exception:
            pass

        price = stripe.Price.create(
            product=product_id,
            unit_amount=amount_cents,
            currency='usd',
            recurring={'interval': interval},
            lookup_key=lookup_key,
            nickname=f"{lookup_key.capitalize()} Premium"
        )
        self.stdout.write(self.style.SUCCESS(f"Created Price '{lookup_key}': {price.id}"))
        return price
