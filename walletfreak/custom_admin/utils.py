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
            'benefits': 'default_card_benefits.csv',
            'rates': 'default_rates.csv',
            'signup': 'default_signup.csv',
            'mapping': 'default_category_mapping.json',
            # 'questions': 'calculators/credit_card_questions.csv' # Not strictly used for output yet but available
        }
        
    def _load_csv(self, filename):
        path = os.path.join(settings.BASE_DIR, filename)
        data = []
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter='|')
                    for row in reader:
                        data.append(row)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        return data

    def _load_json(self, filename):
        path = os.path.join(settings.BASE_DIR, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        return {}

    def generate_prompt(self, slug_id):
        # 1. Gather Data
        benefits = [b for b in self._load_csv(self.files['benefits']) if b.get('slug-id') == slug_id]
        rates = [r for r in self._load_csv(self.files['rates']) if r.get('slug-id') == slug_id]
        signup = [s for s in self._load_csv(self.files['signup']) if s.get('slug-id') == slug_id]
        mapping = self._load_json(self.files['mapping'])
        
        # 2. Format Benefits
        benefits_str = ""
        if benefits:
            # Get headers from the first row to show schema
            headers = list(benefits[0].keys()) if benefits else []
            schema_str = " | ".join(headers)
            rows_str = "\n".join([" | ".join(b.values()) for b in benefits])
            benefits_str = f"Benefit Schema: {schema_str}\nCurrent Benefits Data:\n{rows_str}"
        else:
            benefits_str = "No existing benefits found."

        # 3. Format Rates (Split logic requested: "split it to many rows if there's a multiplier... applies to multiple categories")
        # The user wants the OUTPUT prompt to ask the AI to do this.
        # "For rates, it is imperative to split it to many rows... format <schema>..."
        # So we just provide the CURRENT rates and the INSTRUCTION.
        rates_str = ""
        if rates:
            headers = list(rates[0].keys()) if rates else []
            schema_str = " | ".join(headers)
            rows_str = "\n".join([" | ".join(r.values()) for r in rates])
            rates_str = f"Rate Schema: {schema_str}\nCurrent Rates Data:\n{rows_str}"
        else:
            rates_str = "No existing rates found."

        # 4. Signup Bonuses
        signup_str = ""
        if signup:
            headers = list(signup[0].keys()) if signup else []
            schema_str = " | ".join(headers)
            rows_str = "\n".join([" | ".join(s.values()) for s in signup])
            signup_str = f"Signup Bonus Schema: {schema_str}\nCurrent Signup Data:\n{rows_str}"
        else:
            signup_str = "No existing signup bonuses found."
            
        # 5. Mapping
        # Just Dump a snippet or instructions? "updated category mapping in their respective schemas"
        # Since mapping is global, maybe we just mention it exists or provide the relevant keys if possible?
        # User said: "The category mappings are located under... default_category_mapping.json"
        # "I want to return... updated category mapping..."
        # I'll include the whole file or a summary? It might be large.
        # Let's provide a clear instruction about the mapping file structure.
        # Or better, just include the JSON content if it's not too huge (5KB is fine).
        mapping_str = json.dumps(mapping, indent=2)

        today = datetime.now().strftime("%Y-%m-%d")

        # Construct the final prompt text
        prompt = f"""Context:
Given benefits for slug-id '{slug_id}' that follow the format below:

{benefits_str}

Given rates for slug-id '{slug_id}' that follow the format below:

{rates_str}

Given signup bonuses for slug-id '{slug_id}' that follow the format below:

{signup_str}

Given the current Category Mappings (JSON):
{mapping_str}

---

As of {today}, what are the latest and most accurate up-to-date data for the credit card with slug '{slug_id}'? 
Read from the original vendor's source to find the latest and most accurate data.

I want you to return the benefits, sign up bonuses, rates, and updated category mapping in their respective schemas (matching the formats provided above).

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

Please generate the update data now.
"""
        return prompt
