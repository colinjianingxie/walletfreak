from django.core.management.base import BaseCommand
from core.services import db
from django.utils.text import slugify
import os

class Command(BaseCommand):
    help = 'Seeds the Firestore database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # 1. Credit Cards Data - Parse from CSV
        from .parse_benefits_csv import generate_cards_from_csv
        
        # Get the CSV path
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'default_cards_2025_11_27.csv'
        )
        
        self.stdout.write(f'Parsing cards from: {csv_path}')
        cards_data = generate_cards_from_csv(csv_path)
        
        card_slug_map = {} # Name -> Slug

        for card in cards_data:
            slug = slugify(card['name'])
            card_slug_map[card['name']] = slug
            
            db.create_document('credit_cards', card, doc_id=slug)
            self.stdout.write(f'Seeded card: {card["name"]} with {len(card["benefits"])} benefits')

        # 2. Personalities Data
        personalities = [
            {
                'name': 'Rewards Guru',
                'tagline': 'The Strategist',
                'description': 'Treats credit cards like a competitive game, maintaining spreadsheets to maximize points, bonuses, and benefits across multiple cards; strategically churns for value without unnecessary fees.',
                'recommended_names': [
                    'Chase Sapphire Reserve®',
                    'American Express® Gold Card',
                    'Citi Strata Premier® Card',
                    'Capital One Venture X Rewards Credit Card'
                ]
            },
            {
                'name': 'Lifestyle Fashionista',
                'tagline': 'The Trendsetter',
                'description': 'Prioritizes cards that align with a stylish, everyday lifestyle, focusing on aesthetics, shopping protections, and rewards for fashion, coffee, and daily indulgences.',
                'recommended_names': [
                    'American Express® Gold Card',
                    'Capital One Savor Cash Rewards Credit Card',
                    'Prime Visa',
                    'Hilton Honors American Express Surpass® Card'
                ]
            },
            {
                'name': 'Beginner Dabbler',
                'tagline': 'The Starter',
                'description': 'New to rewards, wants simple travel perks without complexity; shops at premium stores like Whole Foods and prefers one versatile card over a wallet full.',
                'recommended_names': [
                    'Chase Sapphire Preferred® Card',
                    'Capital One Venture Rewards Credit Card',
                    'American Express® Green Card',
                    'Prime Visa'
                ]
            },
            {
                'name': 'Cashback Enthusiast',
                'tagline': 'The Pragmatist',
                'description': 'Dismisses points as gimmicks; demands straightforward cash back deposited directly, with zero annual fees and high rates on everyday spending.',
                'recommended_names': [
                    'Wells Fargo Active Cash® Card',
                    'Citi Double Cash® Card',
                    'Capital One Quicksilver Cash Rewards Credit Card',
                    'Discover it® Cash Back'
                ]
            },
            {
                'name': 'Budget Traveler',
                'tagline': 'The Explorer',
                'description': 'Loves travel but sticks to practical, affordable options; seeks flexible points, no-frills perks like hotel credits, and low-to-moderate fees without luxury excess.',
                'recommended_names': [
                    'Capital One Venture Rewards Credit Card',
                    'Chase Freedom Unlimited®',
                    'Citi Strata Premier® Card',
                    'Capital One VentureOne Rewards Credit Card'
                ]
            },
            {
                'name': 'Simple Minimalist',
                'tagline': 'The Essentialist',
                'description': 'Favors one reliable card for clean, hassle-free use; pays off balances monthly, values simplicity over rewards, and avoids debt or complexity.',
                'recommended_names': [
                    'Chase Freedom Unlimited®',
                    'Capital One Quicksilver Cash Rewards Credit Card',
                    'Citi Simplicity® Card',
                    'Wells Fargo Reflect® Card'
                ]
            },
            {
                'name': 'Luxury Spender',
                'tagline': 'The High Roller',
                'description': 'Enjoys high-end perks like lounge access and concierge services; comfortable with premium fees for status symbols, elite benefits, and statement-making cards.',
                'recommended_names': [
                    'Chase Sapphire Reserve®',
                    'American Express Platinum Card®',
                    'Capital One Venture X Rewards Credit Card',
                    'Delta SkyMiles® Reserve American Express Card'
                ]
            },
            {
                'name': 'Deal Hunter',
                'tagline': 'The Optimizer',
                'description': 'Thrives on optimizing deals through rotating categories, bonuses, and free perks; gets satisfaction from stacking rewards on shopping and everyday buys.',
                'recommended_names': [
                    'Chase Freedom Flex®',
                    'Discover it® Cash Back',
                    'Blue Cash Preferred® Card from American Express',
                    'Capital One Savor Cash Rewards Credit Card'
                ]
            },
            {
                'name': 'Balance Manager',
                'tagline': 'The Planner',
                'description': 'Often carries balances and needs low-interest options or intro APRs; focuses on structure to manage debt rather than chasing rewards.',
                'recommended_names': [
                    'Wells Fargo Reflect® Card',
                    'Citi Simplicity® Card',
                    'Discover it® Cash Back',
                    'Chase Slate Edge®'
                ]
            },
            {
                'name': 'Tech Enthusiast',
                'tagline': 'The Innovator',
                'description': 'Attracted to modern, digital-first cards with app integration, sustainability features, and perks like crypto rewards or carbon offsets.',
                'recommended_names': [
                    'Capital One Venture X Rewards Credit Card',
                    'American Express® Green Card',
                    'Discover it® Miles',
                    'U.S. Bank Shield™ Visa® Card'
                ]
            },
            {
                'name': 'Family Oriented',
                'tagline': 'The Provider',
                'description': 'Manages household finances with kids in mind; seeks family-friendly benefits like travel insurance, shared user perks, and protections for group travel or purchases.',
                'recommended_names': [
                    'Chase Sapphire Preferred® Card',
                    'Delta SkyMiles® Platinum American Express Card',
                    'The World of Hyatt Credit Card',
                    'Prime Visa'
                ]
            },
            {
                'name': 'Student',
                'tagline': 'The Scholar',
                'description': 'Budget-conscious learner building credit during school; wants no annual fees, cash back on dining, entertainment, and gas, plus student-specific intro offers and perks.',
                'recommended_names': [
                    'Discover it® Student Cash Back',
                    'Capital One Quicksilver Student Cash Rewards Credit Card',
                    'Discover it® Student Chrome',
                    'Bank of America® Customized Cash Rewards credit card for Students'
                ]
            },
            {
                'name': 'Wallet Freak',
                'tagline': 'The Ultimate Optimizer',
                'description': 'The master of credit card optimization who tracks every benefit, maximizes every dollar, and maintains a perfectly balanced wallet. Combines the strategic mindset of a Rewards Guru with the meticulous tracking of a Deal Hunter, always staying ahead of the game.',
                'recommended_names': [
                    'Chase Sapphire Reserve®',
                    'American Express Platinum Card®',
                    'Capital One Venture X Rewards Credit Card',
                    'Chase Sapphire Preferred® Card'
                ]
            }
        ]

        for p in personalities:
            slug = slugify(p['name'])
            
            # Map recommended card names to slugs
            rec_slugs = []
            for rec_name in p['recommended_names']:
                if rec_name in card_slug_map:
                    rec_slugs.append(card_slug_map[rec_name])
                else:
                    # Fallback if name mismatch (shouldn't happen with copy-paste)
                    rec_slugs.append(slugify(rec_name))

            p_data = {
                'name': p['name'],
                'tagline': p.get('tagline', 'The Archetype'),
                'description': p['description'],
                'recommended_cards': rec_slugs,
                'avatar_url': ''
            }
            db.create_document('personalities', p_data, doc_id=slug)
            self.stdout.write(f'Seeded personality: {p["name"]}')

        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
