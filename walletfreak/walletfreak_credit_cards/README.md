# WalletFreak Credit Card Data Management

This directory contains the master data for all credit cards in WalletFreak. The data is managed using a relational file structure and updated via the `update_cards_grok` management command, which leverages the Grok API for real-time web search and data extraction.

## Directory Structure

Each card has its own directory in `master/` (e.g., `master/american-express-platinum-card/`), containing:

*   **`header.json`**: Core card metadata (name, issuer, fees, links) and the `active_indices` mapping (which version of each benefit/rate is currently active).
*   **`benefits/`**: Individual JSON files for each benefit (e.g., `dining-credit-v1.json`). Support versioning.
*   **`earning_rates/`**: Individual JSON files for earning rates.
*   **`sign_up_bonus/`**: JSON files for active offers.
*   **`card_questions/`**: Generated questions for the "Is this card worth it?" quiz.

## Adding New Cards

To add a new credit card, you simply need its intended "slug" (ID). The system will automatically search the web and generate the files.

### 1. Run the Command
Use the `update_cards_grok` command with the `--cards` argument. You can specify multiple slugs separated by commas.

```bash
# Example: Adding a single card
python manage.py update_cards_grok --cards "capital-one-venture-x"

# Example: Adding multiple cards
python manage.py update_cards_grok --cards "chase-sapphire-reserve,american-express-gold-card"
```

**Requirements:**
- `GROK_API_KEY` must be set in your `.env` file.

### 2. What Happens
1.  **Template Creation**: The script detects it's a new card and creates an empty memory template.
2.  **Web Search**: It queries Grok to search the web for the current details, benefits, and offers for the card.
3.  **Category Enforcement**: It scans your existing cards to find valid benefit categories (e.g., "Dining", "Travel") and instructs Grok to use them to keep data clean.
4.  **Generation**: It generates the full card JSON.
5.  **Saving**: It splits the JSON into the relational file structure (`header.json`, `benefits/*.json`, etc.).

### 3. Verify & Seed
After generation, inspect the files in `walletfreak_credit_cards/master/<card-slug>/`. If everything looks good, load it into the database:

```bash
# Seed specific cards
python manage.py seed_db --cards "capital-one-venture-x"

# OR use the auto-seed flag during update
python manage.py update_cards_grok --cards "capital-one-venture-x" --auto-seed
```

## Updating Existing Cards

The process for updating cards is identical.

```bash
python manage.py update_cards_grok --cards "existing-card-slug"
```

**Versioning Logic:**
- The script compares the new data from Grok against the *currently active* version in `master/`.
- **No Change**: If a benefit is identical, no file is changed.
- **Change Detected**: If a benefit has changed (e.g., value increased), the old file is marked inactive (`valid_until` = yesterday), and a **new version** file is created (e.g., `dining-credit-v2.json`) and set as active in `header.json`.

## Bulk Updates
To run the update on **ALL** cards in the `master/` directory:

```bash
python manage.py update_cards_grok
```
*(Note: This consumes significant API credits and takes time.)*

## Command Reference

### Basic Usage

```bash
# Update a single card
python manage.py update_cards_grok --cards "card-slug"

# Update multiple cards
python manage.py update_cards_grok --cards "card-1,card-2,card-3"

# Update all cards
python manage.py update_cards_grok
```

### Available Flags

#### `--cards` (Optional)
Comma-separated list of card slugs to update. If omitted, updates all cards in `master/`.

```bash
python manage.py update_cards_grok --cards "chase-sapphire-reserve,amex-platinum"
```

#### `--update-types` (Optional, Default: `all`)
Specify which components to update. Reduces API token usage by only updating selected components.

**Valid types:** `bonus`, `benefits`, `rates`, `questions`, `all`

```bash
# Update only sign-up bonus
python manage.py update_cards_grok --cards "card-slug" --update-types bonus

# Update benefits and earning rates
python manage.py update_cards_grok --cards "card-slug" --update-types benefits,rates

# Update everything (default)
python manage.py update_cards_grok --cards "card-slug" --update-types all
```

#### `--premium-only` (Optional)
Only update premium tier cards (cards with `annual_fee > 0`). Useful for targeted updates.

```bash
# Update only premium cards
python manage.py update_cards_grok --premium-only

# Update premium cards, only their benefits
python manage.py update_cards_grok --premium-only --update-types benefits
```

#### `--dry-run` (Optional)
Preview which cards would be updated without making API calls or changes.

```bash
# See which cards would be updated
python manage.py update_cards_grok --dry-run

# See which premium cards would be updated
python manage.py update_cards_grok --premium-only --dry-run
```

#### `--auto-seed` (Optional)
Automatically seed the database after updating cards.

```bash
# Update and immediately seed to database
python manage.py update_cards_grok --cards "card-slug" --auto-seed
```

### Common Workflows

#### Add a New Card
```bash
# 1. Generate card data
python manage.py update_cards_grok --cards "new-card-slug"

# 2. Review the generated files in master/new-card-slug/

# 3. Seed to database
python manage.py seed_db --cards "new-card-slug"

# OR do it all in one step
python manage.py update_cards_grok --cards "new-card-slug" --auto-seed
```

#### Update Sign-Up Bonuses for All Premium Cards
```bash
# Dry run first to see what would be updated
python manage.py update_cards_grok --premium-only --update-types bonus --dry-run

# Run the actual update
python manage.py update_cards_grok --premium-only --update-types bonus
```

#### Update Benefits for Specific Cards
```bash
python manage.py update_cards_grok --cards "amex-platinum,chase-sapphire-reserve" --update-types benefits
```

#### Refresh All Data for a Card
```bash
# Update everything (default behavior)
python manage.py update_cards_grok --cards "card-slug"
```

### Requirements

- **Environment Variable:** `GROK_API_KEY` must be set in your `.env` file
- **API Credits:** Each update consumes Grok API credits based on the complexity of the card and components being updated

### Tips

1. **Use `--dry-run`** to preview updates before making actual API calls
2. **Use `--update-types`** to reduce API costs when you only need to update specific components
3. **Use `--premium-only`** to focus on high-value cards
4. **Combine flags** for targeted updates: `--premium-only --update-types bonus --dry-run`
