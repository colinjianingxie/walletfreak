# Seed DB Command Documentation

The `seed_db` management command has been enhanced to support selective seeding via command-line parameters. This allows for faster, targeted database updates during development and maintenance.

## Usage

```bash
python manage.py seed_db [options]
```

## Options

| Option | Description | Example |
|--------|-------------|---------|
| `--cards` | Comma-separated list of card slugs to seed | `--cards=chase-sapphire-preferred,amex-gold` |
| `--types` | Comma-separated list of data types to seed | `--types=rates,benefits` |
| `--referrals` | Seed referrals only | `--referrals` |
| `--personalities` | Seed personalities only | `--personalities` |
| `--quiz-questions` | Seed quiz questions only | `--quiz-questions` |
| `--category-mapping` | Seed category mapping only | `--category-mapping` |

### Valid Data Types
When using `--types`, you can specify one or more of the following:
- `rates`: Earning rates
- `benefits`: Card benefits (includes verdicts)
- `calculator_questions`: Calculator questions
- `sign_up_bonus`: Sign-up bonus information
- `verdict`: Verdicts

## Examples

### 1. Seed Everything (Default)
Updates the entire database.
```bash
python manage.py seed_db
```

### 2. Seed Specific Cards
Update only specific cards (all data types for these cards).
```bash
python manage.py seed_db --cards=chase-sapphire-preferred,amex-gold
```

### 3. Seed Specific Data Types for All Cards
Update only earning rates across all cards.
```bash
python manage.py seed_db --types=rates
```

### 4. Seed Specific Types for Specific Cards
Update only the sign-up bonus for a specific card.
```bash
python manage.py seed_db --cards=chase-sapphire-preferred --types=sign_up_bonus
```

### 5. Seed Individual Collections
Update only referrals, personalities, or other specific collections.
```bash
# Seed only referrals
python manage.py seed_db --referrals

# Seed only personalities
python manage.py seed_db --personalities
```

## Notes
- **Backward Compatibility**: Running without arguments behaves exactly as before (seeds everything).
- **Smart Filtering**: If you specify `--cards`, other flags like `--referrals` will only apply to those cards if applicable.
- **Audit**: Pre-flight data audits are automatically run when modifying card data to ensure integrity.
