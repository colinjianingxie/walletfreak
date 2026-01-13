import os
import json
from datetime import datetime
from collections import OrderedDict
from django.conf import settings


class PromptGenerator:
    def __init__(self):
        self.cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data')
        self.sample_card = os.path.join(self.cards_dir, 'chase-sapphire-preferred-card.json')
    
    def _load_sample_json(self):
        """Load the sample card JSON file."""
        with open(self.sample_card, 'r', encoding='utf-8') as f:
            return json.dumps(json.load(f), indent=4)
    
    def _extract_merged_categories(self):
        """
        Extract and merge all categories from all card JSON files.
        Returns a list of category objects with merged CategoryNameDetailed.
        """
        categories = OrderedDict()
        
        for filename in sorted(os.listdir(self.cards_dir)):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.cards_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    card_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue
            
            card_categories = card_data.get('Categories', [])
            for cat in card_categories:
                cat_name = cat.get('CategoryName')
                icon = cat.get('Icon')
                detailed = cat.get('CategoryNameDetailed', [])
                
                if not cat_name:
                    continue
                
                if cat_name not in categories:
                    categories[cat_name] = {
                        'CategoryName': cat_name,
                        'Icon': icon,
                        'CategoryNameDetailed': set()
                    }
                
                for detail in detailed:
                    categories[cat_name]['CategoryNameDetailed'].add(detail)
        
        result = []
        for cat_data in categories.values():
            result.append({
                'CategoryName': cat_data['CategoryName'],
                'Icon': cat_data['Icon'],
                'CategoryNameDetailed': sorted(cat_data['CategoryNameDetailed'])
            })
        
        return result
    
    def _extract_unique_field_values(self):
        """
        Extract unique values for NumericType, Currency, SignUpBonusType, TimeCategory
        across all card JSON files.
        """
        numeric_types = set()
        currencies = set()
        signup_bonus_types = set()
        time_categories = set()
        
        for filename in sorted(os.listdir(self.cards_dir)):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.cards_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    card_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue
            
            # Extract from Benefits
            for benefit in card_data.get('Benefits', []):
                if benefit.get('NumericType'):
                    numeric_types.add(benefit['NumericType'])
                if benefit.get('TimeCategory'):
                    time_categories.add(benefit['TimeCategory'])
            
            # Extract from EarningRates
            for rate in card_data.get('EarningRates', []):
                if rate.get('Currency'):
                    currencies.add(rate['Currency'])
            
            # Extract from SignUpBonuses
            for bonus in card_data.get('SignUpBonuses', []):
                if bonus.get('SignUpBonusType'):
                    signup_bonus_types.add(bonus['SignUpBonusType'])
        
        return {
            'NumericType': sorted(numeric_types),
            'Currency': sorted(currencies),
            'SignUpBonusType': sorted(signup_bonus_types),
            'TimeCategory': sorted(time_categories)
        }
        
    def generate_prompt(self, slug_ids):
        """Generate the update prompt for given slug-id(s)."""
        # Ensure slug_ids is a list
        if isinstance(slug_ids, str):
            slug_ids = [slug_ids]
            
        today = datetime.now().strftime('%Y-%m-%d')
        merged_categories = json.dumps(self._extract_merged_categories(), indent=4)
        unique_values = self._extract_unique_field_values()
        
        # Format card names for the prompt
        card_names = ', '.join(slug_ids)
        
        # Check if the card already exists - if so, use its JSON; otherwise use sample
        if len(slug_ids) == 1:
            card_file = os.path.join(self.cards_dir, f'{slug_ids[0]}.json')
            if os.path.exists(card_file):
                with open(card_file, 'r', encoding='utf-8') as f:
                    example_json = json.dumps(json.load(f), indent=4)
                is_existing_card = True
            else:
                example_json = self._load_sample_json()
                is_existing_card = False
        else:
            example_json = self._load_sample_json()
            is_existing_card = False
        
        if is_existing_card:
            example_label = f"Here is the current JSON for {slug_ids[0]}:"
        else:
            example_label = "It needs to follow a format exactly like this example (Chase Sapphire Preferred):"
        
        prompt = f"""I want to do a websearch to get the latest updates for the following credit card(s): {card_names} as of {today}. {example_label}

{example_json}

The possible categories are:

{merged_categories}

The possible values for specific fields are:
- **NumericType**: {json.dumps(unique_values['NumericType'])}
- **Currency**: {json.dumps(unique_values['Currency'])}
- **SignUpBonusType**: {json.dumps(unique_values['SignUpBonusType'])}
- **TimeCategory**: {json.dumps(unique_values['TimeCategory'])}

There are a couple of rules:

## IMPORTANT: Do Not Change These Fields
- **slug-id**: Must remain exactly as provided
- **CardName**: Must remain exactly as provided
- **ImageURL**: Must remain exactly as provided

## Benefits
Check whether there are any updated benefits for the card. The categories should be specific, but not too specific. For example, the respective categories would then be: ["Disney"], ["Online Groceries"] (because there can be online and regular), and ["Generic Dining"] as restaurants is very generic.

## Earning Rates
Be as accurate and up-to-date as possible with these earning rates. IsDefault represents the "everything else" spend (default spending rate). There should only be 1 IsDefault for each card. If there is 1 rate for multiple services like: 3x points for Disney streaming, online groceries, restaurants -> separate it out into three items: one row for 3x Disney streaming, one row for 3x online groceries, one row for restaurants. The categories should be specific, but not too specific. For example, the respective categories would then be: ["Disney"], ["Online Groceries"] (because there can be online and regular), and ["Generic Dining"] as restaurants is very generic.

## Sign Up Bonus
The signup bonus needs to be up to date. Give me a new EffectiveDate (if the sign up bonus has changed).

## Questions
The credit card questions are questions based off of the benefits. These are used to help gauge whether the card is a good fit. Rather than asking direct questions on whether they will use the benefit, be a bit more "generic" with the questions to gauge user interest. The weights will ultimately determine how much the user values the benefit (1.0 is max).

## Freak Verdict
The freak verdicts are honest opinion on the card. Give a rating and generate an opinion on the card.

## Categories
Categories are very important (especially in Rates and Benefits). Try to be specific in the Rates and Benefits category. Feel free to add to the CategoryNameDetailed if there are any additions to the Categories.

## Output
Generate me the SAME format of JSON as presented in the sample, one for each card requested.

If there are no updates that you found for a card, feel free to return the ORIGINAL json file for that card."""

        return prompt
    
    def generate_minimum_prompt(self, slug_id):
        """Generate a minimal follow-up prompt for an existing card."""
        card_file = os.path.join(self.cards_dir, f'{slug_id}.json')
        
        if not os.path.exists(card_file):
            # If card doesn't exist, fall back to full prompt
            return self.generate_prompt(slug_id)
        
        # Load the existing card JSON
        with open(card_file, 'r', encoding='utf-8') as f:
            card_json = json.dumps(json.load(f), indent=4)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        prompt = f"""Do the same for {slug_id}.json as of {today}. Here is the current JSON:

{card_json}

Remember: Do NOT change slug-id, CardName, or ImageURL. Return the full updated JSON."""

        return prompt

