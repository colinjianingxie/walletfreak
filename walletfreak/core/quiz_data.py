"""
Quiz questions and personality data for the credit card recommendation system.
"""

# Quiz Questions - 4 Stages
QUIZ_QUESTIONS = [
    {
        'stage': 1,
        'question': 'What sounds most exciting to you?',
        'subtitle': 'Pick up to 3',
        'max_selections': 3,
        'options': [
            {
                'id': 'free_travel',
                'text': 'Getting free flights or hotel stays',
                'personalities': ['wallet-freak', 'luxury-jetsetter', 'points-strategist', 'value-traveler']
            },
            {
                'id': 'cash_back',
                'text': 'Real cash back I can actually spend',
                'personalities': ['cashback-pragmatist', 'simple-minimalist', 'category-hunter']
            },
            {
                'id': 'airport_lounges',
                'text': 'Chilling in airport lounges with free food/drinks',
                'personalities': ['luxury-jetsetter', 'wallet-freak', 'value-traveler']
            },
            {
                'id': 'hotel_upgrades',
                'text': 'Getting hotel upgrades or free nights',
                'personalities': ['luxury-jetsetter', 'points-strategist', 'value-traveler']
            },
            {
                'id': 'business_expenses',
                'text': 'I have business/side-hustle expenses I want rewarded',
                'personalities': ['business-powerhouse', 'wallet-freak']
            },
            {
                'id': 'welcome_bonuses',
                'text': 'Huge welcome bonuses when I sign up',
                'personalities': ['wallet-freak', 'points-strategist', 'category-hunter']
            },
            {
                'id': 'vip_perks',
                'text': 'VIP perks (concierge, credits, black card vibes)',
                'personalities': ['luxury-jetsetter', 'wallet-freak']
            }
        ]
    },
    {
        'stage': 2,
        'question': 'Where do you actually spend the most money every month?',
        'subtitle': 'Select all that apply',
        'max_selections': None,  # No limit
        'options': [
            {
                'id': 'dining',
                'text': 'Restaurants, bars, food delivery',
                'personalities': ['foodie-grocery-king', 'wallet-freak', 'category-hunter']
            },
            {
                'id': 'groceries',
                'text': 'Groceries & supermarkets',
                'personalities': ['foodie-grocery-king', 'category-hunter']
            },
            {
                'id': 'travel',
                'text': 'Flights, hotels, vacations',
                'personalities': ['luxury-jetsetter', 'points-strategist', 'value-traveler', 'wallet-freak']
            },
            {
                'id': 'online_shopping',
                'text': 'Amazon & online shopping',
                'personalities': ['category-hunter', 'simple-minimalist', 'student-starter']
            },
            {
                'id': 'digital',
                'text': 'Software, ads, subscriptions, digital stuff',
                'personalities': ['business-powerhouse', 'wallet-freak']
            },
            {
                'id': 'gas',
                'text': 'Gas, EV charging, commuting',
                'personalities': ['category-hunter', 'cashback-pragmatist']
            },
            {
                'id': 'high_spend',
                'text': 'I spend a lot on everything (high monthly spend)',
                'personalities': ['wallet-freak', 'luxury-jetsetter', 'business-powerhouse']
            }
        ]
    },
    {
        'stage': 3,
        'question': 'How do you feel about annual fees?',
        'subtitle': 'Pick one',
        'max_selections': 1,
        'options': [
            {
                'id': 'no_fee',
                'text': 'Absolutely not — $0 only',
                'personalities': ['cashback-pragmatist', 'simple-minimalist', 'student-starter', 'category-hunter']
            },
            {
                'id': 'low_fee',
                'text': "I'll pay $95–$150 if it pays for itself quickly",
                'personalities': ['value-traveler', 'foodie-grocery-king', 'category-hunter']
            },
            {
                'id': 'mid_fee',
                'text': '$250–$400 is fine if the perks are real',
                'personalities': ['points-strategist', 'value-traveler', 'wallet-freak']
            },
            {
                'id': 'high_fee',
                'text': "$550+ is totally okay if I'm getting way more value",
                'personalities': ['luxury-jetsetter', 'wallet-freak', 'business-powerhouse']
            }
        ]
    },
    {
        'stage': 4,
        'question': 'Which of these sound like YOU?',
        'subtitle': 'Select all that apply',
        'max_selections': None,  # No limit
        'options': [
            {
                'id': 'optimizer',
                'text': 'I love (or want) spreadsheets and optimizing everything',
                'personalities': ['wallet-freak', 'points-strategist', 'category-hunter']
            },
            {
                'id': 'one_card',
                'text': 'I just want one perfect card and never think again',
                'personalities': ['simple-minimalist', 'cashback-pragmatist']
            },
            {
                'id': 'churner',
                'text': "I'm happy to open new cards for big welcome bonuses",
                'personalities': ['wallet-freak', 'points-strategist', 'category-hunter']
            },
            {
                'id': 'business',
                'text': 'I have business or side-hustle expenses',
                'personalities': ['business-powerhouse', 'wallet-freak']
            },
            {
                'id': 'student',
                'text': "I'm a student or just starting my credit journey",
                'personalities': ['student-starter']
            },
            {
                'id': 'high_spender',
                'text': 'I easily spend $2,000+ per month on cards',
                'personalities': ['wallet-freak', 'luxury-jetsetter', 'business-powerhouse']
            },
            {
                'id': 'carry_balance',
                'text': 'I sometimes carry a balance / want low interest',
                'personalities': ['simple-minimalist']
            }
        ]
    }
]

# Personality Definitions with Wallet Setup
PERSONALITIES = [
    {
        'name': 'Wallet Freak',
        'slug': 'wallet-freak',
        'tagline': 'The Ultimate Optimizer',
        'description': 'You are the final boss of this game. You track every portal, every transfer partner, every retention offer, and you make the issuers cry. You will gladly pay $695 if you extract $2,000+ in value.',
        'wallet_setup': [
            {
                'category': 'Premium Hub (Lounges + Transfer Partners)',
                'cards': ['chase-sapphire-reserve-card', 'capital-one-venture-x-rewards-credit-card', 'american-express-platinum-card']
            },
            {
                'category': 'Dining & Groceries Maximizer',
                'cards': ['american-express-gold-card']
            },
            {
                'category': 'Rotating/Quarterly Categories',
                'cards': ['chase-freedom-flex-card', 'discover-it-cash-back-card']
            },
            {
                'category': 'Catch-All / Flat Rate',
                'cards': ['citi-double-cash-card', 'wells-fargo-active-cash-card']
            },
            {
                'category': 'Business / Side Hustle',
                'cards': ['chase-ink-business-preferred-credit-card', 'american-express-business-gold-card', 'chase-ink-business-cash-credit-card']
            },
            {
                'category': 'Rent (if you pay rent)',
                'cards': ['bilt-mastercard']
            }
        ]
    },
    {
        'name': 'Luxury Jetsetter',
        'slug': 'luxury-jetsetter',
        'tagline': 'The Black Card Flexer',
        'description': 'Airport lounges, hotel status, concierge, upgrades, metal cards that make people whisper "what\'s that?" You pay for the lifestyle and you get the lifestyle.',
        'wallet_setup': [
            {
                'category': 'Ultra-Premium Perks Card',
                'cards': ['american-express-platinum-card', 'chase-sapphire-reserve-card']
            },
            {
                'category': 'Best-Value Premium Alternative',
                'cards': ['capital-one-venture-x-rewards-credit-card']
            },
            {
                'category': 'Hotel Status Card',
                'cards': ['hilton-honors-aspire-card-from-american-express', 'marriott-bonvoy-brilliant-american-express-card']
            },
            {
                'category': 'Airline Status Card (optional)',
                'cards': ['delta-skymiles-reserve-american-express-card', 'united-club-infinite-card']
            }
        ]
    },
    {
        'name': 'Points Strategist',
        'slug': 'points-strategist',
        'tagline': 'The Transfer Partner Ninja',
        'description': 'You want transferable points and know every sweet spot redemption. You don\'t need Amex Platinum coupons — you just want the highest cents-per-point possible.',
        'wallet_setup': [
            {
                'category': 'Main Transferable Points Hub',
                'cards': ['chase-sapphire-preferred-card', 'citi-strata-premier-card', 'capital-one-venture-x-rewards-credit-card']
            },
            {
                'category': 'Everyday Multiplier → Transfers to Hub',
                'cards': ['chase-freedom-unlimited-card']
            },
            {
                'category': 'Dining & Groceries Booster',
                'cards': ['american-express-gold-card']
            },
            {
                'category': 'Rotating Categories Add-on',
                'cards': ['chase-freedom-flex-card']
            }
        ]
    },
    {
        'name': 'Business Powerhouse',
        'slug': 'business-powerhouse',
        'tagline': 'The 0.5–3x Everything Monster',
        'description': 'You run real money through cards — ads, software, inventory, shipping, travel. You want uncapped 3–5x on the categories that matter most to your business.',
        'wallet_setup': [
            {
                'category': 'Business Points Hub',
                'cards': ['chase-ink-business-preferred-credit-card', 'american-express-business-gold-card']
            },
            {
                'category': 'High-Limit Cash Back',
                'cards': ['chase-ink-business-cash-credit-card', 'chase-ink-business-unlimited-card']
            },
            {
                'category': 'Personal Travel Pair (to transfer Ink points)',
                'cards': ['chase-sapphire-preferred-card', 'chase-sapphire-reserve-card']
            }
        ]
    },
    {
        'name': 'Cashback Pragmatist',
        'slug': 'cashback-pragmatist',
        'tagline': 'Points Are a Scam, Give Me Cash',
        'description': 'You want real cash, no games, no portals, no annual fees (or tiny ones).',
        'wallet_setup': [
            {
                'category': 'Main Everyday Card (2%+ cash back)',
                'cards': ['wells-fargo-active-cash-card', 'citi-double-cash-card', 'chase-freedom-unlimited-card']
            },
            {
                'category': 'Optional Category Booster (no fee)',
                'cards': ['citi-custom-cash-card', 'us-bank-cash-plus-visa-signature-card']
            }
        ]
    },
    {
        'name': 'Foodie & Grocery King',
        'slug': 'foodie-grocery-king',
        'tagline': '6% groceries / 4–5% dining or nothing',
        'description': 'Your biggest spend is eating. You need the absolute highest return on restaurants, grocery stores, and food delivery.',
        'wallet_setup': [
            {
                'category': 'Grocery Maximizer',
                'cards': ['blue-cash-preferred-card-from-american-express', 'american-express-gold-card']
            },
            {
                'category': 'Dining & Food Delivery',
                'cards': ['american-express-gold-card', 'capital-one-savorone-cash-rewards-credit-card', 'us-bank-altitude-go-visa-signature-card']
            },
            {
                'category': 'Everything Else',
                'cards': ['wells-fargo-active-cash-card', 'citi-double-cash-card']
            }
        ]
    },
    {
        'name': 'Simple Minimalist',
        'slug': 'simple-minimalist',
        'tagline': 'One card, peace of mind, decent return',
        'description': 'You want one card that does everything reasonably well and you never want to think about it again.',
        'wallet_setup': [
            {
                'category': 'Your One Perfect Card',
                'cards': ['citi-double-cash-card', 'wells-fargo-active-cash-card', 'chase-freedom-unlimited-card', 'capital-one-quicksilver-cash-rewards-credit-card']
            }
        ]
    },
    {
        'name': 'Value Traveler',
        'slug': 'value-traveler',
        'tagline': 'Good travel perks without $550+ fee pain',
        'description': 'You love travel but want the fee easily offset. Venture X and CSP are your sweet spot.',
        'wallet_setup': [
            {
                'category': 'Main Travel Card',
                'cards': ['capital-one-venture-x-rewards-credit-card', 'chase-sapphire-preferred-card', 'citi-strata-premier-card']
            },
            {
                'category': 'Everyday Pair',
                'cards': ['chase-freedom-unlimited-card', 'capital-one-savorone-cash-rewards-credit-card']
            }
        ]
    },
    {
        'name': 'Category Hunter',
        'slug': 'category-hunter',
        'tagline': '5% rotating categories = dopamine',
        'description': 'You activate every quarterly category and love stacking offers.',
        'wallet_setup': [
            {
                'category': 'Quarterly/Rotating King',
                'cards': ['chase-freedom-flex-card', 'discover-it-cash-back-card', 'us-bank-cash-plus-visa-signature-card']
            },
            {
                'category': 'Custom 5% Category Card',
                'cards': ['citi-custom-cash-card']
            },
            {
                'category': 'Flat Rate Backup',
                'cards': ['citi-double-cash-card']
            }
        ]
    },
    {
        'name': 'Student Starter',
        'slug': 'student-starter',
        'tagline': 'Building credit while eating out and shopping',
        'description': 'You\'re in school or just graduated, want no annual fee, high rewards on dining/Amazon/Uber, and easy approval.',
        'wallet_setup': [
            {
                'category': 'Best Student Card',
                'cards': ['discover-it-student-cash-back-card', 'capital-one-savorone-student-cash-rewards-credit-card']
            },
            {
                'category': 'No-Fee Everyday Card',
                'cards': ['capital-one-quicksilver-student-cash-rewards-credit-card']
            },
            {
                'category': 'First "Real" Travel Card (post-grad upgrade path)',
                'cards': ['chase-freedom-unlimited-card', 'capital-one-ventureone-rewards-credit-card']
            }
        ]
    }
]