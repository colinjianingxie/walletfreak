"""
Points valuations for different reward currencies.
Values are in Cents Per Point (CPP).
"""

POINTS_VALUATIONS = {
    # Generic Types
    'cash back': 1.0,
    'cash rewards': 1.0,
    'miles': 1.0, # Default for generic "miles" if not issuer specific
    'points': 1.0, # Default, overridden by specific maps
    
    # Specific Points Currencies (Approximate valuations)
    # Chase Ultimate Rewards
    'chase-sapphire-preferred-card': 2.05,
    'chase-sapphire-reserve': 2.05,
    'ink-business-preferred-credit-card': 2.05,
    'chase-freedom-unlimited': 1.0, # Cash back marketed
    'chase-freedom-flex': 1.0,
    
    # Amex Membership Rewards
    'american-express-gold-card': 2.0,
    'american-express-platinum-card': 2.0,
    'american-express-green-card': 2.0,
    'the-business-platinum-card-from-american-express': 2.0,
    'american-express-business-gold-card': 2.0,
    'blue-business-plus-credit-card-from-american-express': 2.0,
    
    # Capital One Miles
    'capital-one-venture-x-rewards-credit-card': 1.85,
    'capital-one-venture-rewards-credit-card': 1.85,
    'capital-one-ventureone-rewards-credit-card': 1.85,
    'capital-one-spark-miles-for-business': 1.85,
    
    # Citi ThankYou Points
    'citi-strata-premier-card': 1.6,
    
    # Hotel Points
    'marriott-bonvoy-boundless-credit-card': 0.84, # Marriott
    'marriott-bonvoy-brilliant-american-express-card': 0.84,
    'hilton-honors-american-express-surpass-card': 0.6, # Hilton
    'hilton-honors-aspire-card-from-american-express': 0.6,
    'ihg-one-rewards-premier-credit-card': 0.5, # IHG
    'the-world-of-hyatt-credit-card': 1.7, # Hyatt
    
    # Airline Miles
    'united-explorer-card': 1.2, # United
    'united-quest-card': 1.2,
    'united-club-card': 1.2,
    'delta-skymiles-platinum-american-express-card': 1.2, # Delta
    'delta-skymiles-reserve-american-express-card': 1.2,
    'southwest-rapid-rewards-priority-credit-card': 1.35, # Southwest
    'british-airways-visa-signature-card': 1.5, # Avios
    'aeroplan-credit-card': 1.5, # Aeroplan
    
    # Bilt
    'bilt-mastercard': 2.05,
}

def get_cents_per_point(card_slug, currency_type):
    """
    Get the cents per point value for a given card/currency.
    """
    # 1. Check specific card override
    if card_slug in POINTS_VALUATIONS:
        return POINTS_VALUATIONS[card_slug]
        
    # 2. Check general currency type
    currency_lower = currency_type.lower()
    if 'cash' in currency_lower:
        return 1.0
    
    # 3. Default fallbacks
    return 1.0
