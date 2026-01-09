import os
import json
import requests
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Updates credit card data using Grok API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cards',
            type=str,
            help='Comma-separated list of card slugs to update',
        )
        parser.add_argument(
            '--auto-seed',
            action='store_true',
            help='Automatically seed the database after update',
        )

    def handle(self, *args, **options):
        api_key = os.environ.get('GROK_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("GROK_API_KEY not found in environment variables"))
            return

        cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards')
        card_slugs = options.get('cards')
        auto_seed = options.get('auto-seed')
        
        if card_slugs:
            slugs = [s.strip() for s in card_slugs.split(',') if s.strip()]
            files = [f"{s}.json" for s in slugs]
        else:
            files = [f for f in os.listdir(cards_dir) if f.endswith('.json')]

        self.stdout.write(f"Processing {len(files)} files...")
        updated_slugs = []

        for filename in files:
            filepath = os.path.join(cards_dir, filename)
            if not os.path.exists(filepath):
                 self.stdout.write(self.style.WARNING(f"File not found: {filename}"))
                 continue

            try:
                with open(filepath, 'r') as f:
                    current_data = json.load(f)
                
                slug = current_data.get('slug-id')
                name = current_data.get('CardName')
                
                self.stdout.write(f"Updating {name} ({slug})...")
                
                # Construct Prompt
                prompt = self.construction_prompt(current_data)
                
                # Call API
                new_data = self.call_grok_api(api_key, prompt)
                
                if new_data:
                    # Validate
                    is_valid, error = self.validate_json(new_data, slug)
                    if not is_valid:
                        self.stdout.write(self.style.ERROR(f"Validation Failed for {slug}: {error}"))
                        continue
                        
                    # Save
                    with open(filepath, 'w') as f:
                        json.dump(new_data, f, indent=4)
                    self.stdout.write(self.style.SUCCESS(f"Successfully updated {filename}"))
                    updated_slugs.append(slug)
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to get valid response for {slug}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {filename}: {e}"))

        if auto_seed and updated_slugs:
            self.stdout.write("Running auto-seed...")
            from django.core.management import call_command
            try:
                # We can just run seed_db for these specific cards to be efficient
                # Or run it generally if lists are long
                cards_arg = ",".join(updated_slugs)
                call_command('seed_db', cards=cards_arg)
                self.stdout.write(self.style.SUCCESS("Auto-seed completed."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Auto-seed failed: {e}"))

    def validate_json(self, data, expected_slug):
        required_keys = [
            "Vendor", "CardName", "slug-id", "ImageURL", "Benefits", 
            "EarningRates", "SignUpBonuses", "Questions", "FreakVerdict", "Categories"
        ]
        
        for key in required_keys:
            if key not in data:
                return False, f"Missing required key: {key}"
                
        if data.get("slug-id") != expected_slug:
             return False, f"Slug mismatch. Expected {expected_slug}, got {data.get('slug-id')}"
             
        return True, None

    def call_grok_api(self, api_key, prompt):
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides JSON updates for credit cards."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "grok-4-latest",
            "stream": False,
            "temperature": 0
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Clean Markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"API Request Failed: {e}")
            if 'response' in locals():
                print(response.text)
            return None

    def get_aggregated_categories(self):
        """
        Parses all card JSONs to aggregate unique categories and their detailed items.
        Returns a list of category objects suitable for insertion into the prompt.
        """
        cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards')
        categories_map = {} # Name -> {Icon, DetailedSet}

        if not os.path.exists(cards_dir):
            return []

        for filename in os.listdir(cards_dir):
            if not filename.endswith('.json'):
                continue
            
            try:
                with open(os.path.join(cards_dir, filename), 'r') as f:
                    data = json.load(f)
                
                for cat in data.get('Categories', []):
                    name = cat.get('CategoryName')
                    icon = cat.get('Icon')
                    detailed = cat.get('CategoryNameDetailed', [])
                    
                    if not name:
                         continue
                         
                    if name not in categories_map:
                        categories_map[name] = {
                            'CategoryName': name,
                            'Icon': icon,
                            'CategoryNameDetailed': set()
                        }
                    
                    # Merge sets
                    categories_map[name]['CategoryNameDetailed'].update(detailed)
                    
            except Exception:
                continue
        
        # Convert to list
        result = []
        for name, data in categories_map.items():
            result.append({
                'CategoryName': name,
                'Icon': data['Icon'],
                'CategoryNameDetailed': sorted(list(data['CategoryNameDetailed']))
            })
            
        return result

    def construction_prompt(self, current_json):
        today = datetime.date.today().isoformat()
        slug = current_json.get('slug-id')
        
        # Get dynamic categories
        possible_categories = self.get_aggregated_categories()
        
        prompt = f"""
I want to do a websearch to get the latest updates for the following credit card(s): {slug} as of {today}. Here is the current JSON for {slug}:

{json.dumps(current_json, indent=4)}

The possible categories are:

{json.dumps(possible_categories, indent=4)}

The possible values for specific fields are:
- **NumericType**: ["Cash", "Days", "FreeNight", "Lounge", "Membership", "Miles", "Months", "Passes", "Percent", "Perk", "Points", "Upgrade"]
- **Currency**: ["cash back", "cash rewards", "miles", "points"]
- **SignUpBonusType**: ["Cash", "Miles", "Points"]
- **TimeCategory**: ["Annually (February statement)", "Annually (anniversary year)", "Annually (calendar year)", "Every 4 years", "Every 4-4.5 years", "First year", "Minimum 12 months", "Minimum 12 months from activation", "Monthly", "One Time", "Ongoing", "Per Claim", "Per Trip", "Per occurrence", "Per qualifying stay", "Per year", "Permanent", "Permanent (Medallion year)", "Permanent (calendar year)", "Permanent (per claim)", "Quarterly", "Semi-annually"]

There are a couple of rules:

## IMPORTANT: Do Not Change These Fields
- **slug-id**: Must remain exactly as provided
- **CardName**: Must remain exactly as provided
- **ImageURL**: Must remain exactly as provided

## Benefits
Check whether there are any updated benefits for the card. The categories should be specific, but not too specific. For example, the respective categories would then be: ["Disney"], ["Online Groceries"] (because there can be online and regular), and ["Generic Dining"] as restaurants is very generic.

IMPORTANT: If a benefit has been updated (e.g. changed value, terms, or category), do NOT overwrite the existing benefit object if it corresponds to a past effective date. Instead, append a NEW benefit object to the `Benefits` list. This new object MUST have:
1. The same `BenefitId` as the old one (VERY IMPORTANT).
2. A new `EffectiveDate` indicating when this change starts (YYYY-MM-DD).
3. The updated description, value, and details.
Keep the old benefit object exactly as is in the list, so we retain history. Only overwrite if the existing benefit is clearly incorrect or has the same EffectiveDate.

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

If there are no updates that you found for a card, feel free to return the ORIGINAL json file for that card.
"""
        return prompt
