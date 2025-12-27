import csv
import json
import os
from datetime import datetime
from django.conf import settings

class PromptGenerator:
    def __init__(self):
        self.base_dir = os.path.join(settings.BASE_DIR, 'walletfreak')
        # Absolute paths for user provided locations - assuming strict alignment with user request
        # User said: /Users/xie/Desktop/projects/walletfreak/walletfreak/...
        # But we should use dynamic paths relative to BASE_DIR if possible, or fallback to fixed names if standard.
        # The user provided full paths, but in the app `settings.BASE_DIR` usually points to `/Users/xie/Desktop/projects/walletfreak`.
        # Let's rely on filenames relative to the `walletfreak` app directory or root.
        # Based on file listing earlier: `walletfreak` dir is inside `walletfreak` project dir?
        # Listing showed `walletfreak` inside `walletfreak`.
        # settings.BASE_DIR is likely /Users/xie/Desktop/projects/walletfreak/walletfreak based on typical Django structure if manage.py is there.
        # Let's assume standard file locations relative to manage.py which is at root of "walletfreak" (the inner one? no, manage.py is usually at project root).
        # Re-checking file list: manage.py is in /Users/xie/Desktop/projects/walletfreak/walletfreak.
        # This suggests the project root provided in `Additional Metadata` /Users/xie/Desktop/projects/walletfreak/walletfreak IS the Django root.
        
        self.files = {
            'credit_cards': os.path.join(settings.BASE_DIR, 'default_credit_cards.csv'),
            'benefits': os.path.join(settings.BASE_DIR, 'default_card_benefits.csv'),
            'rates': os.path.join(settings.BASE_DIR, 'default_rates.csv'),
            'signup': os.path.join(settings.BASE_DIR, 'default_signup.csv'),
            'questions': os.path.join(settings.BASE_DIR, 'calculators/credit_card_questions.csv'),
            'mapping': os.path.join(settings.BASE_DIR, 'default_category_mapping.json')
        }
        
    def _load_csv(self, filepath):
        if not os.path.exists(filepath):
            return []
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            return list(reader)

    def _load_json(self, filepath):
        if not os.path.exists(filepath):
            return {}
        with open(filepath, mode='r', encoding='utf-8') as f:
            return json.load(f)

    def _format_csv_section(self, name, data, slug_ids, slug_field='slug-id'):
        """Helper to format a CSV section with schema and matching rows for multiple slugs"""
        if not data:
            return f"Given {name}: No file found or empty."
        
        # Get headers from the first row
        headers = list(data[0].keys()) if data else []
        schema_str = " | ".join(headers)
        
        # Filter for slugs
        matches = [row for row in data if row.get(slug_field) in slug_ids]
        
        if not matches:
             return f"Given {name}: No matching data found for selected cards.\nSchema: {schema_str}"

        rows_str = "\n".join([" | ".join([str(val) for val in row.values()]) for row in matches])
        
        return f"Given {name} for selected cards that follow the format below:\nSchema: {schema_str}\nRows:\n{rows_str}"

    def generate_prompt(self, slug_ids):
        # Ensure slug_ids is a list
        if isinstance(slug_ids, str):
            slug_ids = [slug_ids]
            
        # 1. Load All Data
        credit_cards = self._load_csv(self.files['credit_cards'])
        benefits = self._load_csv(self.files['benefits'])
        rates = self._load_csv(self.files['rates'])
        signup = self._load_csv(self.files['signup'])
        questions = self._load_csv(self.files['questions'])
        mapping = self._load_json(self.files['mapping'])
        
        # 2. Format Sections
        cards_section = self._format_csv_section("Credit Card Info", credit_cards, slug_ids, 'slug-id')
        benefits_section = self._format_csv_section("Benefits", benefits, slug_ids, 'slug-id')
        rates_section = self._format_csv_section("Rates", rates, slug_ids, 'slug-id')
        signup_section = self._format_csv_section("Signup Bonuses", signup, slug_ids, 'slug-id')
        questions_section = self._format_csv_section("Credit Card Questions", questions, slug_ids, 'slug-id')
        
        # Mapping (JSON dump)
        mapping_str = json.dumps(mapping, indent=2)

        today = datetime.now().strftime("%Y-%m-%d")

        # 3. Construct Prompt
        card_context_str = f"slugs: {', '.join(slug_ids)}" if len(slug_ids) < 10 else f"{len(slug_ids)} selected cards"

        prompt = f"""Context:
{cards_section}

{benefits_section}

{rates_section}

{signup_section}

{questions_section}

Given the current Category Mappings (JSON):
{mapping_str}

---

As of {today}, what are the latest and most accurate up-to-date data for the selected cards ({card_context_str})? 
Read from the original vendor's source to find the latest and most accurate data.

I want you to generate an "update file" containing the updated data.
The update file MUST follow the precise format below, using '---' as a separator between sections:

[Content for default_credit_cards.csv]
---
[Content for default_card_benefits.csv]
---
[Content for default_rates.csv]
---
[Content for default_signup.csv]
---
[Content for credit_card_questions.csv]
---
[Content for default_category_mapping.json]

**Format Rules:**
1. Each section must contain the full CSV or JSON content for that file, including headers.
2. Only include rows relevant to the selected cards.
3. Do not add markdown code blocks (like ```csv) inside the sections if possible, just the raw text.
4. Separators must be exactly '---' on a new line.
5. Do not modify the ImageURL in default_credit_cards.csv.
6. Do NOT output the file names or headers (e.g. "<updated ...>") before the content. Only the content itself.
7. For default_category_mapping.json, ONLY include NEW categories that need to be added. Do not output the full existing mapping.

**Specific Instructions for Rates:**
It is imperative to split rates into many rows if there is a multiplier or cashback that applies to multiple categories.
For example, if a rate is "6x miles for hotels, flights, streaming", I want to have:
- 1 row for 6x miles on hotels
- 1 row for 6x miles on flights
- 1 row for 6x miles on streaming
The categories for each should be as specific as possible based on the terms of the rate if there's branding associated with it.

**Specific Instructions for Benefits:**
The category list for Benefits should also be as specific as possible if there's branding associated.
Examples:
- Online Shopping vs In-Person Shopping (two different concepts)
- Groceries (be specific if it excludes superstores etc)
- Train vs Generic Transportation

Please generate the update file now.
"""
        return prompt
