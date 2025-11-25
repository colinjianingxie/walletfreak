from django.core.management.base import BaseCommand
from core.services import db
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds the Firestore database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # 1. Credit Cards Data
        # Format: Name, Issuer, Fee, Benefits/Description
        raw_cards = [
            ("Chase Sapphire Preferred® Card", "Chase", 95, "5x points on travel via Chase Travel, 3x on dining/online groceries/streaming, 2x on other travel; $50 hotel credit; transferable points to partners; travel protections like trip cancellation."),
            ("American Express® Gold Card", "American Express", 325, "4x points at restaurants (up to $50,000/year) and U.S. supermarkets (up to $25,000/year), 3x on flights; $120 Uber Cash, $120 dining credit, $100 Resy credit; no foreign fees."),
            ("Capital One Venture X Rewards Credit Card", "Capital One", 395, "10x miles on hotels/rental cars via Capital One Travel, 5x on flights/vacation rentals, 2x on all; $300 travel credit, 10,000 anniversary miles; lounge access; transferable miles."),
            ("Chase Freedom Unlimited®", "Chase", 0, "5% on travel via Chase Travel, 3% on dining/drugstores, 1.5% on all; 0% intro APR 15 months; no minimum redemption."),
            ("Wells Fargo Active Cash® Card", "Wells Fargo", 0, "Unlimited 2% cash rewards; $200 bonus; 0% intro APR 12 months; cell phone protection."),
            ("Blue Cash Preferred® Card from American Express", "American Express", 95, "6% at U.S. supermarkets (up to $6,000/year), 6% on streaming, 3% on gas/transit; $10 monthly subscription credit; 0% intro APR 12 months."),
            ("Citi Double Cash® Card", "Citi", 0, "2% cash back (1% on purchase + 1% on payment); 0% intro APR on balance transfers 18 months; 5% on hotels/car rentals via Citi Travel."),
            ("Capital One Venture Rewards Credit Card", "Capital One", 95, "5x miles on hotels/vacation rentals/rental cars via Capital One Travel, 2x on all; $120 Global Entry/TSA PreCheck credit; transferable miles."),
            ("Chase Sapphire Reserve®", "Chase", 795, "8x points on Chase Travel, 4x on flights/hotels direct, 3x on dining; $300 travel credit; lounge access; transferable points."),
            ("American Express Platinum Card®", "American Express", 895, "5x points on flights/prepaid hotels via Amex Travel; $200 Uber Cash, $300 entertainment credit, $600 hotel credit; lounge access."),
            ("Prime Visa", "Chase", 0, "5% at Amazon/Whole Foods/Chase Travel (with Prime), 2% at gas/restaurants/transit; purchase/extended warranty protection."),
            ("Discover it® Cash Back", "Discover", 0, "5% on rotating categories (up to quarterly max), 1% on all; Cashback Match; 0% intro APR 15 months on purchases/balance transfers."),
            ("Wells Fargo Reflect® Card", "Wells Fargo", 0, "0% intro APR 21 months on purchases/balance transfers; cell phone protection."),
            ("Capital One Savor Cash Rewards Credit Card", "Capital One", 0, "8% on Capital One Entertainment, 5% on hotels/rental cars via Travel, 3% on dining/entertainment/groceries/streaming; 0% intro APR 12 months."),
            ("Chase Freedom Flex®", "Chase", 0, "5% on rotating categories (up to $1,500 quarterly), 5% on travel via Chase, 3% on dining/drugstores; 0% intro APR 15 months."),
            ("Citi Strata Premier® Card", "Citi", 95, "10x points on hotels/car rentals/attractions via Citi Travel, 3x on air travel/hotels/restaurants/supermarkets/gas; $100 hotel credit; transferable points."),
            ("Blue Cash Everyday® Card from American Express", "American Express", 0, "3% at U.S. supermarkets/online retail/gas (up to $6,000/category/year); $7 monthly Disney+ credit; 0% intro APR 15 months."),
            ("Capital One Quicksilver Cash Rewards Credit Card", "Capital One", 0, "Unlimited 1.5% cash back, 5% on hotels/rental cars via Travel; 0% intro APR 15 months; no foreign fees."),
            ("United℠ Explorer Card", "Chase", 150, "2x miles on United/dining/hotels; free checked bag, priority boarding; $100 United credit; Global Entry/TSA credit."),
            ("Marriott Bonvoy Boundless® Credit Card", "Chase", 95, "6x points at Marriott, 3x on groceries/gas/dining (up to $6,000/year); annual free night (35,000 points); Silver Elite status."),
            ("Delta SkyMiles® Platinum American Express Card", "American Express", 350, "3x miles on Delta/hotels, 2x on restaurants/U.S. supermarkets; companion certificate; free checked bag; $120 Resy/Rideshare credits."),
            ("Hilton Honors American Express Surpass® Card", "American Express", 150, "12x points at Hilton, 6x at U.S. restaurants/supermarkets/gas, 4x on U.S. online retail; $200 Hilton credits; Gold status."),
            ("Southwest Rapid Rewards® Priority Credit Card", "Chase", 229, "4x points on Southwest, 2x on gas/restaurants; $75 travel credit; 7,500 anniversary points; upgraded boardings."),
            ("Discover it® Miles", "Discover", 0, "Unlimited 1.5x miles; mile-for-mile match; 0% intro APR 15 months; no foreign fees."),
            ("Capital One VentureOne Rewards Credit Card", "Capital One", 0, "5x miles on hotels/rental cars via Travel, 1.25x on all; 0% intro APR 15 months; transferable miles."),
            ("IHG One Rewards Premier Credit Card", "Chase", 99, "Up to 26x points at IHG; fourth night free; annual free night; Platinum Elite status; Global Entry credit."),
            ("American Express® Green Card", "American Express", 150, "3x points on travel/transit/restaurants; $209 CLEAR credit; trip delay insurance; no foreign fees."),
            ("United Quest℠ Card", "Chase", 350, "3x miles on United, 2x on dining/streaming/travel; free checked bags; $200 TravelBank cash; 10,000-mile discount."),
            ("Citi Simplicity® Card", "Citi", 0, "0% intro APR 12 months purchases/21 months balance transfers; no late fees/penalty rate; Quick Lock."),
            ("Discover it® Chrome", "Discover", 0, "2% at gas/restaurants (up to $1,000/quarter), 1% on all; Cashback Match; 0% intro APR 18 months balance transfers."),
            ("The World of Hyatt Credit Card", "Chase", 95, "Up to 9x points at Hyatt; annual free night (Category 1-4); Discoverist status; extra night after $15,000 spend."),
            ("Capital One QuicksilverOne Cash Rewards Credit Card", "Capital One", 39, "1.5% cash back, 5% on hotels/rental cars via Travel; credit line reviews; for fair credit."),
            ("Marriott Bonvoy Brilliant® American Express® Card", "American Express", 650, "6x points at Marriott, 3x on restaurants/flights; $300 dining credit; annual free night (85,000 points); Platinum status."),
            ("Delta SkyMiles® Reserve American Express Card", "American Express", 650, "3x miles on Delta; Sky Club access; companion certificate; free checked bag; $240 Resy credit."),
            ("Hilton Honors Aspire Card from American Express", "American Express", 550, "14x points at Hilton, 7x on dining/travel; $400 resort credits; Diamond status; annual free night."),
            ("Aeroplan® Credit Card", "Chase", 95, "3x on dining/groceries/Air Canada; 500 bonus points every $2,000; free checked bag; 25K status."),
            ("British Airways Visa Signature® Card", "Chase", 95, "3x Avios on British Airways/Aer Lingus/Iberia/LEVEL, 2x on hotels; Travel Together Ticket after $30,000; 10% flight discount."),
            ("U.S. Bank Smartly Visa Signature Card", "U.S. Bank", 0, "2% cash back (higher with bank savings); for account holders."),
            ("Capital One Savor Student Cash Rewards Credit Card", "Capital One", 0, "8% on entertainment, 3% on dining/groceries/streaming; no foreign fees; for students."),
            ("Discover it® Secured Credit Card", "Discover", 0, "2% at gas/restaurants (up to $1,000/quarter), 1% on all; Cashback Match; security deposit refund potential."),
            ("Capital One Platinum Secured Credit Card", "Capital One", 0, "Credit building; security deposit starting $49; automatic reviews; no foreign fees."),
            ("Chase Slate Edge®", "Chase", 0, "Low intro APR; credit limit reviews; purchase/extended warranty protection."),
            ("IHG One Rewards Traveler Credit Card", "Chase", 0, "Up to 17x at IHG; fourth night free; Silver Elite status; no foreign fees."),
            ("United Club℠ Card", "Chase", 695, "4x miles on United; lounge membership; free checked bags; Premier access."),
            ("Bank of America® Customized Cash Rewards credit card for Students", "Bank of America", 0, "3% in choice category, 2% at groceries/wholesale; 0% intro APR 15 cycles; for students."),
            ("Discover it® Student Cash Back", "Discover", 0, "5% rotating categories, 1% on all; Cashback Match; no credit score required."),
            ("Capital One Quicksilver Student Cash Rewards Credit Card", "Capital One", 0, "1.5% cash back, 5% on hotels/rental cars via Travel; no foreign fees; for students."),
            ("Discover it® Student Chrome", "Discover", 0, "2% at gas/restaurants (up to $1,000/quarter), 1% on all; Cashback Match; for students."),
            ("Capital One Quicksilver Secured Cash Rewards Credit Card", "Capital One", 0, "1.5% cash back, 5% on hotels/rental cars via Travel; security deposit refund potential."),
            ("U.S. Bank Shield™ Visa® Card", "U.S. Bank", 0, "4% on prepaid travel via Travel Center; 0% intro APR 18 cycles; $20 annual credit.")
        ]

        # Helper to extract benefits from description string
        def parse_benefits(desc):
            # Very basic parsing to create a list of benefits for the UI
            parts = desc.split(';')
            benefits = []
            for i, part in enumerate(parts):
                part = part.strip()
                if not part: continue
                # Try to guess type/amount
                b_type = 'credit' if '$' in part else 'perk'
                amount = 0
                if '$' in part:
                    # simplistic extraction
                    try:
                        amount = int(''.join(filter(str.isdigit, part.split('$')[1].split(' ')[0])))
                    except:
                        pass
                
                # Detect frequency
                frequency = 'annual' # Default
                lower_part = part.lower()
                if 'month' in lower_part or 'uber cash' in lower_part or 'dining credit' in lower_part:
                    frequency = 'monthly'
                elif 'quarter' in lower_part:
                    frequency = 'quarterly'
                elif 'semi-annual' in lower_part:
                    frequency = 'semi-annual'
                
                benefits.append({
                    'id': f'benefit_{i}',
                    'name': part,
                    'description': part,
                    'type': b_type,
                    'amount': amount,
                    'reset_period': frequency # Using reset_period to store frequency
                })
            return benefits

        # Helper to extract rewards structure
        def parse_rewards(desc):
            # Just return a dict with the full description for now
            return {'details': desc}

        card_slug_map = {} # Name -> Slug

        for name, issuer, fee, desc in raw_cards:
            slug = slugify(name)
            card_slug_map[name] = slug
            
            card_data = {
                'name': name,
                'issuer': issuer,
                'annual_fee': fee,
                'rewards_structure': parse_rewards(desc),
                'benefits': parse_benefits(desc),
                'image_url': '',
                'referral_links': [],
                'user_type': []
            }
            db.create_document('credit_cards', card_data, doc_id=slug)
            self.stdout.write(f'Seeded card: {name}')

        # 2. Personalities Data
        personalities = [
            {
                'name': 'Rewards Guru',
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
                'description': 'Budget-conscious learner building credit during school; wants no annual fees, cash back on dining, entertainment, and gas, plus student-specific intro offers and perks.',
                'recommended_names': [
                    'Discover it® Student Cash Back',
                    'Capital One Quicksilver Student Cash Rewards Credit Card',
                    'Discover it® Student Chrome',
                    'Bank of America® Customized Cash Rewards credit card for Students'
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
                'description': p['description'],
                'recommended_cards': rec_slugs,
                'avatar_url': ''
            }
            db.create_document('personalities', p_data, doc_id=slug)
            self.stdout.write(f'Seeded personality: {p["name"]}')

        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
