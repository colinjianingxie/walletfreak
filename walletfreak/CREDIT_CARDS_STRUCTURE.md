# Credit Card Benefits Data Structure

## Overview

This document describes the new credit card data structure that supports detailed benefit tracking from the CSV file `default_cards_2025_11_27.csv`.

## Firestore Schema

### Collection: `credit_cards`

Each credit card document has the following structure:

```json
{
  "name": "Chase Sapphire Preferred® Card",
  "issuer": "Chase",
  "annual_fee": 95,
  "image_url": "",
  "referral_links": [],
  "user_type": [],
  "benefits": [
    {
      "description": "5x total points on travel purchased through Chase Travel",
      "category": "Permanent",
      "dollar_value": null,
      "effective_date": "2025-11-27"
    },
    {
      "description": "$50 Annual Chase Travel Hotel Credit",
      "category": "Annually (anniversary year)",
      "dollar_value": 50,
      "effective_date": "2025-11-27"
    }
  ]
}
```

### Benefit Structure

Each benefit in the `benefits` array contains:

- **description** (string): Full description of the benefit
- **category** (string): Benefit frequency/type
  - `"Permanent"` - Always active benefit
  - `"Annually (anniversary year)"` - Resets on card anniversary
  - `"Annually (calendar year)"` - Resets on calendar year
  - `"Monthly"` - Resets monthly
  - `"Quarterly"` - Resets quarterly
  - `"Semi-annually"` - Resets twice per year
  - `"Every 4 years"` - Resets every 4 years (e.g., TSA PreCheck)
  - Other custom periods as needed
- **dollar_value** (float or null): Monetary value of the benefit (null for non-monetary benefits like points multipliers)
- **effective_date** (string): Date when this benefit information was last updated (YYYY-MM-DD format)

## Data Import

### Seeding the Database

To seed the database with credit card data from the CSV:

```bash
cd walletfreak
python manage.py seed_db
```

This command will:
1. Parse `default_cards_2025_11_27.csv`
2. Convert each card and its benefits to the Firestore format
3. Create documents in the `credit_cards` collection
4. Also seed personality data

### CSV Format

The source CSV has the following columns:
- **Vendor**: Card issuer (e.g., "Chase", "American Express")
- **CardName**: Full name of the credit card
- **BenefitDescription**: Description of the specific benefit
- **Category**: Benefit frequency/reset period
- **DollarValue**: Monetary value (or "N/A" for non-monetary benefits)
- **EffectiveDate**: Date of the benefit information

## Admin Portal Management

### Accessing the Admin Portal

Navigate to `/custom-admin/cards/` to manage credit cards.

### Available Actions

1. **View All Cards**: See a list of all credit cards with their issuer, annual fee, and benefit count
2. **Create New Card**: Add a new credit card with benefits (JSON format)
3. **Edit Card**: Modify card details and benefits
4. **Delete Card**: Remove a card from the database

### Editing Benefits

Benefits are edited as JSON in the admin portal. Example format:

```json
[
  {
    "description": "5x points on travel",
    "category": "Permanent",
    "dollar_value": null,
    "effective_date": "2025-11-27"
  },
  {
    "description": "$300 annual travel credit",
    "category": "Annually (calendar year)",
    "dollar_value": 300,
    "effective_date": "2025-11-27"
  }
]
```

## User Card Tracking

When users add cards to their wallet, the system tracks:

```json
{
  "card_id": "chase-sapphire-preferred-card",
  "name": "Chase Sapphire Preferred® Card",
  "image_url": "",
  "status": "active",
  "added_at": "2025-11-27T12:00:00Z",
  "anniversary_date": "2025-01-15",
  "benefit_usage": {
    "benefit_0": {
      "used": 25.50,
      "last_updated": "2025-11-27T12:00:00Z"
    },
    "benefit_1": {
      "used": 300.00,
      "last_updated": "2025-11-27T12:00:00Z"
    }
  }
}
```

This allows tracking of:
- Which benefits have been used
- How much of each benefit has been utilized (partial or full)
- When benefits were last updated
- Automatic reset based on benefit category (monthly, annually, etc.)

### Benefit Tracking Features

The dashboard provides two ways to track benefit usage:

1. **Toggle Full Usage**: Click "Mark Full" to mark a benefit as fully used, or "Reset" to mark it as unused
2. **Custom Amount**: Enter a specific dollar amount used (e.g., $150 of a $300 credit) and click "Update"

The system automatically:
- Calculates remaining benefit value
- Resets usage based on benefit category (monthly, quarterly, annually, etc.)
- Updates total utilization percentage
- Tracks when each benefit was last updated

## Migration from Old Structure

The old structure had:
- Simple `rewards_structure` with text details
- Limited `benefits` array with basic structure

The new structure provides:
- Detailed benefit tracking per card
- Monetary values for credits
- Reset periods for proper benefit tracking
- Effective dates for benefit information

## Future Enhancements

Potential improvements to consider:

1. **Benefit Categories**: Add benefit type categorization (travel, dining, cash back, etc.)
2. **Benefit Caps**: Track spending caps for benefits (e.g., "up to $6,000 per year")
3. **Benefit Eligibility**: Add enrollment requirements or eligibility criteria
4. **Historical Benefits**: Track benefit changes over time
5. **Benefit Comparisons**: Tools to compare benefits across cards
6. **Automated Reminders**: Notify users when benefits reset or are about to expire

## API Endpoints

The following service methods are available:

- `db.get_cards()` - Get all credit cards
- `db.get_card_by_slug(slug)` - Get a specific card by slug
- `db.create_document('credit_cards', data, doc_id=slug)` - Create a new card
- `db.update_document('credit_cards', slug, data)` - Update a card
- `db.delete_document('credit_cards', slug)` - Delete a card

## Notes

- Card slugs are generated from card names using Django's `slugify()` function
- The CSV parser is located at `core/management/commands/parse_benefits_csv.py`
- Admin templates are in `custom_admin/templates/custom_admin/`
- All 83 cards from the CSV are parsed and ready for import