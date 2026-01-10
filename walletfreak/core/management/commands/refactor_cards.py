import os
import json
import datetime
import shutil
from django.core.management.base import BaseCommand
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Refactors existing card JSON blobs into relational structure'

    def handle(self, *args, **options):
        # Base directory for existing cards
        base_dir = os.path.join(os.getcwd(), 'walletfreak_credit_cards')
        master_dir = os.path.join(base_dir, 'master')
        
        if not os.path.exists(master_dir):
            os.makedirs(master_dir)
            
        # Iterate over all JSON files in the directory
        for filename in os.listdir(base_dir):
            if not filename.endswith('.json') or filename == 'master':
                continue
                
            file_path = os.path.join(base_dir, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    self.stdout.write(self.style.ERROR(f"Skipping invalid JSON: {filename}"))
                    continue
            
            # Use existing slug or filename
            card_slug = data.get('slug-id')
            if not card_slug:
                 # Fallback to filename without extension
                 card_slug = filename.replace('.json', '')

            self.stdout.write(f"Processing: {card_slug}")
            
            # Create card-specific directory
            card_dir = os.path.join(master_dir, card_slug)
            
            # CLEANUP: Remove existing directory to ensure no stale files (mixed underscores/hyphens)
            if os.path.exists(card_dir):
                shutil.rmtree(card_dir)
            
            os.makedirs(card_dir)
            
            # 1. Create Header (card.json)
            # Remove the large arrays from the header
            header_data = data.copy()
            
            # Normalize Fields
            field_map = {
                'CardName': 'name',
                'ImageURL': 'image_url',
                'Vendor': 'issuer', # Map Vendor to issuer as used in templates
                'AnnualFee': 'annual_fee',
                'ApplicationLink': 'application_link',
                'RewardsStructure': 'rewards_structure',
                'UserType': 'user_type',
                'MinCreditScore': 'min_credit_score',
                'MaxCreditScore': 'max_credit_score',
                'Is524': 'is_524',
                'FreakVerdict': 'freak_verdict',
                'PointsValueCpp': 'points_value_cpp',
                'ShowInCalculators': 'show_in_calculators'
            }
            
            for old_key, new_key in field_map.items():
                if old_key in header_data:
                    header_data[new_key] = header_data.pop(old_key)

            header_data.pop('Benefits', None)
            header_data.pop('EarningRates', None)
            header_data.pop('SignUpBonuses', None)
            header_data.pop('Questions', None) 
            header_data.pop('Categories', None) 
            
            # Calculate active indices (pointers to current versions)
            active_indices = {
                'benefits': [],
                'earning_rates': [],
                'sign_up_bonus': []
            }
            
            # Write Header
            with open(os.path.join(card_dir, 'header.json'), 'w') as f:
                json.dump(header_data, f, indent=4)
                
            # 2. Process Benefits
            benefits_dir = os.path.join(card_dir, 'benefits')
            if not os.path.exists(benefits_dir):
                os.makedirs(benefits_dir)
                
            existing_benefits = data.get('Benefits', [])
            for i, benefit in enumerate(existing_benefits):
                b_id = benefit.get('BenefitId', f"benefit-{i}")
                # Create a versioned ID
                version = "v1"
                versioned_id = f"{b_id}-{version}"
                
                benefit_doc = benefit.copy()
                benefit_doc['benefit_id'] = b_id 
                benefit_doc['version'] = version
                benefit_doc['valid_from'] = "2020-01-01" 
                benefit_doc['valid_until'] = None 
                benefit_doc['is_active'] = True
                
                # Normalize Benefit Fields
                benefit_map = {
                    'BenefitDescriptionShort': 'short_description',
                    'BenefitDescription': 'description',
                    'AdditionalDetails': 'additional_details',
                    'BenefitCategory': 'benefit_category',
                    'BenefitType': 'benefit_type',
                    'NumericValue': 'numeric_value',
                    'NumericType': 'numeric_type',
                    'DollarValue': 'dollar_value',
                    'TimeCategory': 'time_category',
                    'EnrollmentRequired': 'enrollment_required',
                    'EffectiveDate': 'effective_date'
                }
                for old, new in benefit_map.items():
                    if old in benefit_doc:
                        benefit_doc[new] = benefit_doc.pop(old)

                # Save - USE HYPHEN to match versioned_id
                b_filename = f"{versioned_id}.json"
                with open(os.path.join(benefits_dir, b_filename), 'w') as f:
                    json.dump(benefit_doc, f, indent=4)
                    
                # Deduplication logic
                if versioned_id not in active_indices['benefits']:
                    active_indices['benefits'].append(versioned_id)

            # 3. Process Earning Rates
            rates_dir = os.path.join(card_dir, 'earning_rates')
            if not os.path.exists(rates_dir):
                os.makedirs(rates_dir)
                
            existing_rates = data.get('EarningRates', [])
            for i, rate in enumerate(existing_rates):
                # Generate a meaningful ID for the rate (e.g., "dining", "travel")
                categories = rate.get('RateCategory', [])
                cat_slug = "base"
                if categories:
                    # Simplify category name for slug
                    cat_name = categories[0].replace('Generic ', '').replace(' ', '-').lower()
                    cat_slug = cat_name
                
                r_id = cat_slug
                version = "v1"
                versioned_id = f"{r_id}-{version}"
                
                rate_doc = rate.copy()
                rate_doc['rate_id'] = r_id
                rate_doc['version'] = version
                rate_doc['valid_from'] = "2020-01-01"
                rate_doc['valid_until'] = None
                rate_doc['is_active'] = True
                
                # Normalize Earning Rate Fields
                rate_map = {
                    'EarningRate': 'multiplier', # Intentionally map to multiplier (or rate? JS handles both but multiplier is clearer)
                    'RateCategory': 'category',
                    'Currency': 'currency',
                    'AdditionalDetails': 'additional_details',
                    'IsDefault': 'is_default'
                }
                for old, new in rate_map.items():
                    if old in rate_doc:
                        rate_doc[new] = rate_doc.pop(old)
                
                # Save - USE HYPHEN
                r_filename = f"{versioned_id}.json"
                with open(os.path.join(rates_dir, r_filename), 'w') as f:
                    json.dump(rate_doc, f, indent=4)

                if versioned_id not in active_indices['earning_rates']:
                    active_indices['earning_rates'].append(versioned_id)

            # 4. Process Sign Up Bonuses
            sub_dir = os.path.join(card_dir, 'sign_up_bonus')
            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir)
                
            existing_subs = data.get('SignUpBonuses', [])
            for i, sub in enumerate(existing_subs):
                # SUBs are often date-based or just one active one
                sub_id = f"offer-{i+1}"
                version = "v1"
                
                sub_doc = sub.copy()
                sub_doc['offer_id'] = sub_id
                sub_doc['is_active'] = True # Assume current one is active
                
                # Normalize SUB Fields
                sub_map = {
                   'SignUpBonusValue': 'value',
                   'Terms': 'terms',
                   'SignUpBonusType': 'currency',
                   'SpendAmount': 'spend_amount',
                   'SignupDurationMonths': 'duration_months',
                   'EffectiveDate': 'effective_date'
                }
                for old, new in sub_map.items():
                    if old in sub_doc:
                        sub_doc[new] = sub_doc.pop(old)
                
                # Save
                s_filename = f"{sub_id}.json"
                with open(os.path.join(sub_dir, s_filename), 'w') as f:
                    json.dump(sub_doc, f, indent=4)
                    
                if sub_id not in active_indices['sign_up_bonus']:
                     active_indices['sign_up_bonus'].append(sub_id)
                    
            # 5. Process Questions involves specific logic, maybe keep in header or separate?
            # User request said: "The prompt / card document becomes a header... details move to sub-collections"
            # Questions are relatively static unless benefits change. 
            # Let's put questions in a sub-collection 'card_questions' as they are benefit-linked usually.
            
            questions_dir = os.path.join(card_dir, 'card_questions')
            if not os.path.exists(questions_dir):
                os.makedirs(questions_dir)
                
            existing_questions = data.get('Questions', [])
            for i, q in enumerate(existing_questions):
                q_id = f"q-{i}"
                q_doc = q.copy()
                q_doc['question_id'] = q_id
                
                # Normalize Question Fields
                q_map = {
                    'BenefitShortDescription': 'short_desc',
                    'Question': 'question',
                    'QuestionType': 'question_type',
                    'ChoiceList': 'choices',
                    'ChoiceWeight': 'weights',
                    'BenefitCategory': 'benefit_category'
                }
                for old, new in q_map.items():
                    if old in q_doc:
                        q_doc[new] = q_doc.pop(old)
                
                with open(os.path.join(questions_dir, f"{q_id}.json"), 'w') as f:
                    json.dump(q_doc, f, indent=4)

            # Update header with active indices (optional, strictly speaking we query subcollections, but good for quick reference)
            # The plan mentioned "active_indices" in header.
            
            # Re-save header with indices
            header_data['active_indices'] = active_indices
            with open(os.path.join(card_dir, 'header.json'), 'w') as f:
                json.dump(header_data, f, indent=4)
            
        self.stdout.write(self.style.SUCCESS('Successfully refactored cards!'))
