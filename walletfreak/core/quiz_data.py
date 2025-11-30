"""
Quiz questions and personality data for the credit card recommendation system.
"""

# Quiz Questions
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
        'max_selections': None,
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
                'text': 'I’ll pay $95–$150 if it pays for itself quickly',
                'personalities': ['value-traveler', 'foodie-grocery-king', 'category-hunter']
            },
            {
                'id': 'mid_fee',
                'text': '$250–$400 is fine if the perks are real',
                'personalities': ['points-strategist', 'value-traveler', 'wallet-freak']
            },
            {
                'id': 'high_fee',
                'text': '$550+ is totally okay if I’m getting way more value',
                'personalities': ['luxury-jetsetter', 'wallet-freak', 'business-powerhouse']
            }
        ]
    },
    {
        'stage': 4,
        'question': 'Which of these sound like YOU?',
        'subtitle': 'Select all that apply',
        'max_selections': None,
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
                'text': 'I’m happy to open new cards for big welcome bonuses',
                'personalities': ['wallet-freak', 'points-strategist', 'category-hunter']
            },
            {
                'id': 'business',
                'text': 'I have business or side-hustle expenses',
                'personalities': ['business-powerhouse', 'wallet-freak']
            },
            {
                'id': 'student',
                'text': 'I’m a student or just starting my credit journey',
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

# Personality Definitions
PERSONALITIES = [
    {
        'name': 'The Global Entry',  # Renamed from Luxury Jetsetter to match screenshot vibe
        'slug': 'luxury-jetsetter',
        'tagline': 'The gold standard for travel.',
        'description': 'Flexible points that transfer to high-value partners like Hyatt, plus unbeatable travel insurance.',
        'stats': {
            'annual_fees': 550,
            'credit_value': 300,
            'points_value': 1200,
            'net_value': 950
        },
        'slots': [
            {
                'name': 'The Hub',
                'description': 'The core card that unlocks transfer partners and travel insurance.',
                'cards': ['chase-sapphire-reserve-card', 'chase-sapphire-preferred-card']
            },
            {
                'name': 'The Point Generator',
                'description': 'Earns points faster on everyday purchases to transfer to your Hub.',
                'cards': ['chase-freedom-unlimited-card', 'chase-freedom-flex-card']
            }
        ],
        'rules': [
            {
                'title': 'The Anchor',
                'description': 'The Sapphire Reserve is your hub. It unlocks 50% more value for travel and enables point transfers.'
            },
            {
                'title': 'The Accumulator',
                'description': 'Use Freedom Unlimited for everything else. Move those points to your Sapphire account to boost their value.'
            },
            {
                'title': 'The Redemption',
                'description': 'Transfer points to World of Hyatt. A 30k point night at a Park Hyatt can be worth $1,000+.'
            }
        ]
    },
    {
        'name': 'Wallet Freak',
        'slug': 'wallet-freak',
        'tagline': 'The Ultimate Optimizer',
        'description': 'You are the final boss of this game. You track every portal, every transfer partner, every retention offer, and you make the issuers cry.',
        'stats': {
            'annual_fees': 1200,
            'credit_value': 1400,
            'points_value': 2500,
            'net_value': 2700
        },
        'slots': [
            {
                'name': 'Premium Hub',
                'description': 'Lounge access and transfer partners.',
                'cards': ['american-express-platinum-card', 'capital-one-venture-x-rewards-credit-card']
            },
            {
                'name': 'Dining & Grocery',
                'description': 'Maximum multipliers on food.',
                'cards': ['american-express-gold-card']
            },
            {
                'name': 'Catch-All',
                'description': 'For everything else.',
                'cards': ['blue-business-plus-credit-card-from-american-express', 'chase-freedom-unlimited-card']
            }
        ],
        'rules': [
            {
                'title': 'Maximize Credits',
                'description': 'Ensure you use every single monthly credit (Uber, Dining, etc.) to offset the high fees.'
            },
            {
                'title': 'Retention Offers',
                'description': 'Call every year when the annual fee hits to ask for a retention offer.'
            },
            {
                'title': 'Business Cards',
                'description': 'Use business cards to keep your personal credit report clean and earn more points.'
            }
        ]
    },
    {
        'name': 'Points Strategist',
        'slug': 'points-strategist',
        'tagline': 'The Transfer Partner Ninja',
        'description': 'You want transferable points and know every sweet spot redemption. You don\'t need Amex Platinum coupons — you just want the highest cents-per-point possible.',
        'stats': {
            'annual_fees': 395,
            'credit_value': 300,
            'points_value': 800,
            'net_value': 705
        },
        'slots': [
            {
                'name': 'The Hub',
                'description': 'Your main travel card.',
                'cards': ['capital-one-venture-x-rewards-credit-card', 'chase-sapphire-preferred-card']
            },
            {
                'name': 'The Multiplier',
                'description': 'Earns 2x-3x on categories.',
                'cards': ['capital-one-savorone-cash-rewards-credit-card', 'chase-freedom-flex-card']
            }
        ],
        'rules': [
            {
                'title': 'Transfer Partners',
                'description': 'Never redeem for cash back. Always transfer to airline or hotel partners.'
            },
            {
                'title': 'The Duo',
                'description': 'Combine cards from the same ecosystem (e.g. Capital One Duo or Chase Trifecta) to pool points.'
            }
        ]
    },
    {
        'name': 'Business Powerhouse',
        'slug': 'business-powerhouse',
        'tagline': 'The 0.5–3x Everything Monster',
        'description': 'You run real money through cards — ads, software, inventory, shipping, travel. You want uncapped 3–5x on the categories that matter most to your business.',
        'stats': {
            'annual_fees': 690,
            'credit_value': 400,
            'points_value': 2000,
            'net_value': 1710
        },
        'slots': [
            {
                'name': 'Ad Spend & Software',
                'description': '4x points on top business categories.',
                'cards': ['american-express-business-gold-card', 'chase-ink-business-preferred-credit-card']
            },
            {
                'name': 'Flat Rate Business',
                'description': '2x or 1.5x on all other business spend.',
                'cards': ['blue-business-plus-credit-card-from-american-express', 'chase-ink-business-unlimited-card']
            }
        ],
        'rules': [
            {
                'title': 'Separate Expenses',
                'description': 'Keep business expenses strictly on business cards for easier accounting.'
            },
            {
                'title': 'Employee Cards',
                'description': 'Issue cards to employees to earn points on their spend too.'
            }
        ]
    },
    {
        'name': 'Cashback Pragmatist',
        'slug': 'cashback-pragmatist',
        'tagline': 'Points Are a Scam, Give Me Cash',
        'description': 'You want real cash, no games, no portals, no annual fees (or tiny ones).',
        'stats': {
            'annual_fees': 0,
            'credit_value': 0,
            'points_value': 500,
            'net_value': 500
        },
        'slots': [
            {
                'name': 'Flat Rate',
                'description': '2% cash back on everything.',
                'cards': ['wells-fargo-active-cash-card', 'citi-double-cash-card']
            },
            {
                'name': 'Category Booster',
                'description': '5% on your top category.',
                'cards': ['citi-custom-cash-card']
            }
        ],
        'rules': [
            {
                'title': 'Keep it Simple',
                'description': 'Focus on cards with no annual fee and high cash back rates.'
            },
            {
                'title': 'Auto-Redeem',
                'description': 'Set up auto-redemption to your bank account so you never have to think about it.'
            }
        ]
    },
    {
        'name': 'Foodie & Grocery King',
        'slug': 'foodie-grocery-king',
        'tagline': '6% groceries / 4–5% dining or nothing',
        'description': 'Your biggest spend is eating. You need the absolute highest return on restaurants, grocery stores, and food delivery.',
        'stats': {
            'annual_fees': 250,
            'credit_value': 240,
            'points_value': 800,
            'net_value': 790
        },
        'slots': [
            {
                'name': 'Dining & Groceries',
                'description': 'The heavy hitters for food spend.',
                'cards': ['american-express-gold-card', 'capital-one-savorone-cash-rewards-credit-card']
            },
            {
                'name': 'Supermarkets',
                'description': '6% back at US supermarkets.',
                'cards': ['blue-cash-preferred-card-from-american-express']
            }
        ],
        'rules': [
            {
                'title': 'Dining Credits',
                'description': 'Use the monthly dining credits on the Gold card to offset the fee.'
            },
            {
                'title': 'Grocery Cap',
                'description': 'Watch out for the $6k annual cap on the Blue Cash Preferred.'
            }
        ]
    },
    {
        'name': 'Simple Minimalist',
        'slug': 'simple-minimalist',
        'tagline': 'One card, peace of mind',
        'description': 'You want one card that does everything reasonably well and you never want to think about it again.',
        'stats': {
            'annual_fees': 0,
            'credit_value': 0,
            'points_value': 400,
            'net_value': 400
        },
        'slots': [
            {
                'name': 'The One Card',
                'description': 'Your daily driver for everything.',
                'cards': ['citi-double-cash-card', 'wells-fargo-active-cash-card', 'capital-one-quicksilver-cash-rewards-credit-card']
            }
        ],
        'rules': [
            {
                'title': 'Set and Forget',
                'description': 'Put everything on autopay and use this one card for every purchase.'
            }
        ]
    },
    {
        'name': 'Value Traveler',
        'slug': 'value-traveler',
        'tagline': 'Good travel perks without the pain',
        'description': 'You love travel but want the fee easily offset. Venture X and CSP are your sweet spot.',
        'stats': {
            'annual_fees': 95,
            'credit_value': 50,
            'points_value': 600,
            'net_value': 555
        },
        'slots': [
            {
                'name': 'Travel Hub',
                'description': 'Great value travel card.',
                'cards': ['chase-sapphire-preferred-card', 'capital-one-venture-rewards-credit-card']
            },
            {
                'name': 'Everyday',
                'description': 'Earns points on daily spend.',
                'cards': ['chase-freedom-unlimited-card']
            }
        ],
        'rules': [
            {
                'title': 'Hotel Credit',
                'description': 'Use the $50 hotel credit on the Sapphire Preferred to reduce the effective fee.'
            },
            {
                'title': 'Transfer Partners',
                'description': 'Learn to use Hyatt or airline partners for outsized value.'
            }
        ]
    },
    {
        'name': 'Category Hunter',
        'slug': 'category-hunter',
        'tagline': '5% rotating categories = dopamine',
        'description': 'You activate every quarterly category and love stacking offers.',
        'stats': {
            'annual_fees': 0,
            'credit_value': 0,
            'points_value': 600,
            'net_value': 600
        },
        'slots': [
            {
                'name': 'Rotating Categories',
                'description': '5% back on changing categories.',
                'cards': ['chase-freedom-flex-card', 'discover-it-cash-back-card']
            },
            {
                'name': 'Custom Category',
                'description': '5% on your top spend category.',
                'cards': ['citi-custom-cash-card']
            }
        ],
        'rules': [
            {
                'title': 'Activate Quarterly',
                'description': 'Set a reminder to activate your 5% categories every quarter.'
            },
            {
                'title': 'Max Out',
                'description': 'Try to hit the $1,500 spend cap on the 5% categories.'
            }
        ]
    },
    {
        'name': 'Student Starter',
        'slug': 'student-starter',
        'tagline': 'Building credit while eating out',
        'description': 'You\'re in school or just graduated, want no annual fee, high rewards on dining/Amazon/Uber, and easy approval.',
        'stats': {
            'annual_fees': 0,
            'credit_value': 0,
            'points_value': 200,
            'net_value': 200
        },
        'slots': [
            {
                'name': 'Student Card',
                'description': 'Great rewards with no credit history needed.',
                'cards': ['discover-it-student-cash-back-card', 'capital-one-savorone-student-cash-rewards-credit-card']
            }
        ],
        'rules': [
            {
                'title': 'Pay in Full',
                'description': 'Always pay your full balance every month to build good credit.'
            },
            {
                'title': 'Keep it Open',
                'description': 'Keep your oldest card open to maintain a long credit history.'
            }
        ]
    }
]