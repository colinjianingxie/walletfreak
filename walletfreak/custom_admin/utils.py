import os
from datetime import datetime
from django.conf import settings

class PromptGenerator:
    def __init__(self):
        self.cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards')
        
    def generate_prompt(self, slug_ids):
        # Ensure slug_ids is a list
        if isinstance(slug_ids, str):
            slug_ids = [slug_ids]
            
        today = datetime.now().strftime("%Y-%m-%d")
        
        context_content = ""
        for slug in slug_ids:
            filename = f"{slug}.txt"
            path = os.path.join(self.cards_dir, filename)
            
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                context_content += f"{content}\n\n"
            else:
                context_content += f"File: {filename} NOT FOUND.\n\n"

        prompt = f"""Given:
{context_content}

I want to get the latest updates for this card as of {today}. When looking up the latest updates for the card, go to the original vendor of the card to search. Each section is separated by "---". The first section is the card details. The CardName, Vendor, slug-id, ImageURL should never change. In the first section, check for any updates to the Annual Fee, PointsValueCpp (The average value per point), any updates to credit scores, and any updates to the ApplicationLink.

For the second section, these are the benefits, check whether there are any updated benefits for the card. The categories should be specific, but not too specific. For example, the respective categories would then be: ["Disney"], ["Online Groceries"] (because there can be online and regular), and ["Generic Dining"] as restaurants is very generic.

In the third section, these are earning rates. Be as accurate and up-to-date as possible with these earning rates. IsDefault represents the "everything else" spend (default spending rate). There should only be 1 IsDefault for each card. If there is 1 rate for multiple services like: 3x points for Disney streaming, online groceries, restaurants -> separate it out into three rows: one row for 3x Disney streaming, one row for 3x online groceries, one row for restaurants. The categories should be specific, but not too specific. For example, the respective categories would then be: ["Disney"], ["Online Groceries"] (because there can be online and regular), and ["Generic Dining"] as restaurants is very generic. 

In the fourth section, the signup bonus needs to be up to date. Give me a new EffectiveDate (if the sign up bonus has changed).

In the fifth section, these are questions based off of the second section's benefits. These are used to help gauge whether the card is a good fit. Rather than asking direct questions on whether they will use the benefit, be a bit more "generic" with the questions to gauge user interest. The weights will ultimately determine how much the user values the benefit (1.0 is max). 

In the sixth section, these are the freak verdicts. My honest opinion on the card. Give a rating and generate an opinion on the card.

Finally in the seventh section, these are categories. Categories are very important (especially in Rates and Benefits). Try to be specific in the Rates and Benefits category. Feel free to add to the CategoryNameDetailed if there are any additions to the Categories. 

Generate me the SAME format of txt I have provided earlier (section 1 is the card with schema, section 2 is benefits, section 3 is rates, etc...). Each section is separated with ---. The categories at the end are in JSON. 

If there are no updates that you found for the card, feel free to return the ORIGINAL txt file. 
"""
        return prompt
