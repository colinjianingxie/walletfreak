"""Prompt construction for Grok API — extracted from update_cards_grok.py:566-743."""

import json
import datetime


def build_update_prompt(
    current_json: dict,
    slug: str,
    update_types: list[str],
    category_hierarchy: str,
) -> str:
    """Build the system prompt for Grok to update card data.

    Args:
        current_json: The current hydrated card data dict.
        slug: Card slug identifier.
        update_types: List of components to update (header, benefits, rates, bonus, questions).
        category_hierarchy: Formatted category hierarchy string for the prompt.

    Returns:
        Complete prompt string ready to send to the Grok API.
    """
    today = datetime.date.today().isoformat()

    # Strip internal fields from current_json to avoid confusing LLM
    clean_json = current_json.copy()
    clean_json.pop('active_indices', None)

    # Remove components not being updated
    if 'benefits' not in update_types:
        clean_json.pop('benefits', None)
    if 'rates' not in update_types:
        clean_json.pop('earning_rates', None)
    if 'bonus' not in update_types:
        clean_json.pop('sign_up_bonus', None)
    if 'questions' not in update_types:
        clean_json.pop('questions', None)

    # Build component-specific labels
    components_to_update = []
    if 'header' in update_types:
        components_to_update.append("header (card metadata)")
    if 'bonus' in update_types:
        components_to_update.append("sign-up bonus")
    if 'benefits' in update_types:
        components_to_update.append("benefits")
    if 'rates' in update_types:
        components_to_update.append("earning rates")
    if 'questions' in update_types:
        components_to_update.append("questions")

    components_str = ", ".join(components_to_update)

    # Determine image_url instruction
    if clean_json.get('image_url'):
        image_url_instr = f'- **image_url**: "{clean_json["image_url"]}" (Keep as provided).'
    else:
        image_url_instr = '- **image_url**: null (Default to null if no image provided).'

    # Clean application_link if it has markdown
    app_link = clean_json.get('application_link', '')
    if app_link and app_link.startswith('[') and '](' in app_link and app_link.endswith(')'):
        try:
            clean_json['application_link'] = app_link.split('](')[1][:-1]
        except Exception:
            pass

    prompt = f"""
I want to do a websearch to get the latest updates for the credit card: "{clean_json.get('name', slug)}" (Slug: {slug}) as of {today}.

**FOCUS**: This update is ONLY for: {components_str}. Do NOT update other components.

Here is the CURRENT known data (JSON):
{json.dumps(clean_json, indent=4)}

**TASK**:
1. Search the web (official issuer site preferred) for the current details of this card.
2. Return a JSON object with the UPDATED details for {components_str} ONLY.
3. Validate all fields against the schema below.

**VALID CATEGORIES HIERARCHY**:
{category_hierarchy}

**CRITICAL INSTRUCTIONS FOR UPDATES (READ CAREFULLY)**:
1. **CONSERVATIVE UPDATES**: The "CURRENT known data" provided above is heavily curated. **DO NOT CHANGE** values (especially multipliers or credits) unless you find **EXPLICIT, RECENT EVIDENCE** in the web search results that contradicts it (e.g., a "devaluation" or "new offer").
2. **Ambiguity**: If web results are ambiguous or unclear, **KEEP THE CURRENT VALUE**. Do not guess.
3. **Categories**: You MUST choose categories ONLY from the "Valid Categories Hierarchy" above.
4. **Specificity**: For `benefit_category` and `earning_rates.category`, select the most specific child category if applicable.
5. **No Duplicates**: **DO NOT CREATE DUPLICATE CATEGORIES**.
6. **No Inventions**: Do NOT invent new categories not in the list.

**SCHEMA RULES (Snake Case)**:
- **slug-id**: Must remain "{slug}".
- **name**: Card Name.
- **issuer**: e.g., "American Express", "Chase", "Capital One".
{image_url_instr}
- **annual_fee**: Number (e.g. 95, 0 for no fee).
- **application_link**: Official URL to apply for the card.
- **min_credit_score**: Number (e.g. 670). Use 300 for secured cards.
- **max_credit_score**: Number (e.g. 850).
- **is_524**: Boolean (true if applies to Chase 5/24 rule).
- **freak_verdict**: String: short opinion or "No Freak verdict for this card yet".
"""

    if 'header' in update_types:
        prompt += """
**HEADER FIELDS** (REQUIRED TO UPDATE):
ALL of these fields MUST be included in your response:
- `slug-id`: String (keep as provided)
- `name`: String (card name)
- `issuer`: String (e.g. "Citi", "Chase", "American Express")
- `image_url`: String (or null if not provided)
- `annual_fee`: Number (e.g. 95, use 0 for no fee)
- `application_link`: String (official application URL)
- `min_credit_score`: Number (e.g. 670, use 300 for secured cards)
- `max_credit_score`: Number (e.g. 850)
- `is_524`: Boolean (true/false), if having the card will affect chase 5/24 rule
- `freak_verdict`: String (brief verdict or "No Freak verdict for this card yet")
"""

    if 'benefits' in update_types:
        prompt += """
**BENEFITS** (REQUIRED TO UPDATE):
- **benefits**: List of objects.
- `benefit_id`: (IMPORTANT) Keep existing ID if updating an existing benefit (e.g. "dining-credit"). Create logical ID for new ones (e.g. "disney-bundle").
- `short_description`: e.g. "Uber Cash"
- `description`: Full text.
- `additional_details`: Brief context (e.g. "For prepaid hotel/vacation rental bookings").
- `benefit_category`: List of strings (e.g. ["Rideshare", "Dining"]).
- `benefit_main_category`: String. The single primary category this benefit falls under (e.g. "Dining", "Airlines", "Hotels", "Lounges", "Travel Perks", "Protection", "Financial Rewards", "Retail Shopping", "Rideshare", "Transit", "Business", "Entertainment", "Health", "Rent Payments", "Gas", "Utilities", "Car Rentals"). Must be ONE value only.
- `benefit_type`: "Credit", "Perk", "Protection", "Insurance", "Bonus", "Status", "Access", "Waiver", "Free Night".
- `numeric_value`: Float/Number (e.g. 200.0).
- `numeric_type`: "Cash", "Points", "Miles".
- `dollar_value`: Integer estimated dollar value (e.g. 200).
- `time_category`: "Annually (calendar year)", "Monthly", "One-time", "Per Use", "Quarterly".
- `enrollment_required`: Boolean.
- `effective_date`: String (YYYY-MM-DD) or null.

**CRITICAL FOR BENEFITS**:
- **SPLIT BUNDLED CREDITS**: If a card has a "total annual credit" composed of distinct parts (e.g., "$400 total credit" = "$200 Hotel Credit" + "$200 Airline Fee Credit"), you **MUST** create separate benefit objects for each distinct part. Do not bundle them.
- **Granularity**: We want detailed, separate benefits for tracking purposes.
"""

    if 'rates' in update_types:
        prompt += """
**EARNING RATES** (REQUIRED TO UPDATE):
- **earning_rates**: List of objects. **EVERY card MUST have at least one earning rate** - at minimum an "All Other Purchases" default rate.
- `rate_id`: (IMPORTANT) Keep existing ID (e.g. "dining"). For new cards, create logical IDs like "dining", "travel", "all-other".
- `multiplier`: Number (e.g. 4.0, 1.5, 1.0 for base rate).
- `category`: List of strings (e.g. ["Dining", "Resy Bookings"]). **Must be a list**. Use ["Financial Rewards", "All Purchases"] for the default rate.
- `additional_details`: **REQUIRED**. Specific string detailing conditions (e.g. "on purchases made directly with airlines"). Use "on all other purchases" for default.
- `is_default`: Boolean (True for "All other purchases" rate, False for bonus categories).

**CRITICAL**: You MUST generate earning rates for new cards. Every card earns something on purchases - research and include:
1. Bonus category rates (e.g., 3x on dining)
2. Default "all other purchases" rate (usually 1x or 1% or 2%)
"""

    if 'bonus' in update_types:
        prompt += """
**SIGN-UP BONUS** (REQUIRED TO UPDATE):
- **sign_up_bonus**: List of objects (usually 1).
- `offer_id`: (CRITICAL FOR VERSIONING) If an object exists in the current data's `sign_up_bonus`, you MUST maintain the SAME `offer_id` (e.g. "offer") when updating the value or terms of the current public offer. DO NOT create new IDs like "offer-75k" or "limited-time-offer". Only change the ID if this is a completely different promotion type (e.g., switching from points to cash back).
- `value`: Number (integer).
- `terms`: e.g. "Spend $4k in 3 months".
- `currency`: String. Usually "Points", "Miles", or "Cash", but can be flexible for unique offers (e.g., "Free Night Awards", "Statement Credit", "First Year Free").
- If no sign-up bonus currently exists, return an empty list [].
- If a bonus existed but has expired with no replacement, return an empty list [].
"""

    if 'questions' in update_types:
        prompt += """
**QUESTIONS** (REQUIRED TO UPDATE):
- **questions**: List of objects. Generating 3-5 questions based on benefits is REQUIRED if list is empty.
- `question_id`: e.g. "q-0".
- `short_desc`: e.g. "Uber Cash".
- `question`: "Do you use Uber...?"
- `question_type`: "multiple_choice" or "boolean".
- `choices`: ["Yes", "No", "Sometimes"].
- `weights`: [1.0, 0.0, 0.5].
- `benefit_category`: List of strings (e.g. ["Uber"]).
- Generate 3-5 generic usage questions to gauge if the card fits the user (based on its benefits).
"""

    prompt += f"""
**OUTPUT**:
Return ONLY the strictly valid JSON object with these components: {components_str}. Include the slug-id, name, and issuer fields as well. No markdown.
"""
    return prompt


def build_batch_update_prompt(
    cards: list[tuple[dict, str]],
    update_types: list[str],
    category_hierarchy: str,
) -> str:
    """Build a single prompt that updates multiple cards at once.

    Args:
        cards: List of (current_json, slug) tuples.
        update_types: Components to update.
        category_hierarchy: Formatted category hierarchy string.

    Returns:
        Prompt string covering all cards in the batch.
    """
    today = datetime.date.today().isoformat()

    # Build component labels
    components_to_update = []
    if 'header' in update_types:
        components_to_update.append("header (card metadata)")
    if 'bonus' in update_types:
        components_to_update.append("sign-up bonus")
    if 'benefits' in update_types:
        components_to_update.append("benefits")
    if 'rates' in update_types:
        components_to_update.append("earning rates")
    if 'questions' in update_types:
        components_to_update.append("questions")
    components_str = ", ".join(components_to_update)

    # Build per-card data sections
    cards_section = ""
    for current_json, slug in cards:
        clean_json = current_json.copy()
        clean_json.pop('active_indices', None)
        if 'benefits' not in update_types:
            clean_json.pop('benefits', None)
        if 'rates' not in update_types:
            clean_json.pop('earning_rates', None)
        if 'bonus' not in update_types:
            clean_json.pop('sign_up_bonus', None)
        if 'questions' not in update_types:
            clean_json.pop('questions', None)

        cards_section += f"""
---
### Card: "{clean_json.get('name', slug)}" (Slug: {slug})
```json
{json.dumps(clean_json, indent=2)}
```
"""

    prompt = f"""
I want to do a websearch to get the latest updates for {len(cards)} credit cards as of {today}.

**FOCUS**: This update is ONLY for: {components_str}. Do NOT update other components.

{cards_section}

**VALID CATEGORIES HIERARCHY**:
{category_hierarchy}

**CRITICAL INSTRUCTIONS FOR UPDATES (READ CAREFULLY)**:
1. **CONSERVATIVE UPDATES**: The data provided above is heavily curated. **DO NOT CHANGE** values unless you find **EXPLICIT, RECENT EVIDENCE** in the web search results.
2. **Ambiguity**: If web results are ambiguous or unclear, **KEEP THE CURRENT VALUE**.
3. **Categories**: You MUST choose categories ONLY from the "Valid Categories Hierarchy" above.
4. **Specificity**: For `benefit_category` and `earning_rates.category`, select the most specific child category.
5. **No Duplicates**: **DO NOT CREATE DUPLICATE CATEGORIES**.
6. **No Inventions**: Do NOT invent new categories not in the list.
"""

    # Add schema rules (shared once for all cards)
    if 'benefits' in update_types:
        prompt += """
**BENEFITS SCHEMA**:
- `benefit_id`: Keep existing ID if updating. Create logical ID for new ones.
- `short_description`, `description`, `additional_details`: Strings.
- `benefit_category`: List of strings. `benefit_main_category`: Single string.
- `benefit_type`: "Credit", "Perk", "Protection", "Insurance", "Bonus", "Status", "Access", "Waiver", "Free Night".
- `numeric_value`: Float. `numeric_type`: "Cash", "Points", "Miles". `dollar_value`: Integer.
- `time_category`: "Annually (calendar year)", "Monthly", "One-time", "Per Use", "Quarterly".
- `enrollment_required`: Boolean. `effective_date`: "YYYY-MM-DD" or null.
- **SPLIT BUNDLED CREDITS** into separate benefit objects.
"""

    if 'rates' in update_types:
        prompt += """
**EARNING RATES SCHEMA**:
- `rate_id`: Keep existing ID. `multiplier`: Number. `category`: List of strings.
- `additional_details`: Required string. `is_default`: Boolean.
- Every card MUST have at least an "All Other Purchases" default rate.
"""

    if 'bonus' in update_types:
        prompt += """
**SIGN-UP BONUS SCHEMA**:
- `offer_id`: Keep existing ID when updating. `value`: Number. `terms`: String. `currency`: String.
- If no bonus exists or has expired, return empty list [].
"""

    prompt += f"""
**OUTPUT**:
Return a JSON object keyed by card slug. Each value contains the updated {components_str} for that card.
Example format:
```
{{
  "card-slug-1": {{ "slug-id": "card-slug-1", "name": "...", "benefits": [...], ... }},
  "card-slug-2": {{ "slug-id": "card-slug-2", "name": "...", "benefits": [...], ... }}
}}
```
Return ONLY valid JSON, no markdown. Include slug-id, name, and issuer for each card.
"""
    return prompt
