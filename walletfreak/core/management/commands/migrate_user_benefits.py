import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from core.services import db # Assuming this exposes the firestore client as db.db
from core.management.commands.parse_updates import generate_cards_from_files

class Command(BaseCommand):
    help = 'Migrates user benefit usage from index keys to stable BenefitId keys'

    def add_arguments(self, parser):
        parser.add_argument(
             '--dry-run',
             action='store_true',
             help='Simulate migration without writing to DB',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be saved"))

        # 1. Build the Mapping: Slug -> { '0': 'benefit-id-1', '1': 'benefit-id-2' }
        cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards')
        self.stdout.write("Reading card definitions...")
        
        # We assume generate_cards_from_files returns cards with 'benefits' lists in the CORRECT order
        # matching the current deployment.
        card_docs, _, _ = generate_cards_from_files(cards_dir)
        
        # Map: CardSlug -> Map[IndexString -> BenefitId]
        id_mapping = {} 
        
        for card in card_docs:
            slug = card.get('slug')
            benefits = card.get('benefits', [])
            
            card_map = {}
            for idx, b in enumerate(benefits):
                b_id = b.get('benefit_id')
                if b_id:
                    card_map[str(idx)] = b_id
            
            if card_map:
                id_mapping[slug] = card_map
                
        self.stdout.write(f"Built mappings for {len(id_mapping)} cards.")

        # 2. Iterate Users
        users_ref = db.db.collection('users')
        users = list(users_ref.stream())
        self.stdout.write(f"Scanning {len(users)} users...")
        
        total_migrated_cards = 0
        
        for user in users:
            uid = user.id
            user_cards_ref = users_ref.document(uid).collection('user_cards')
            user_cards = list(user_cards_ref.stream())
            
            for uc in user_cards:
                data = uc.to_dict()
                # Document ID of user_card is the Card Slug
                card_slug = uc.id 
                
                # Check if we have a mapping for this card
                if card_slug not in id_mapping:
                    continue
                    
                mapping = id_mapping[card_slug]
                benefit_usage = data.get('benefit_usage', {})
                if not benefit_usage:
                    continue
                
                # Check needed updates
                updates = {}
                needs_update = False
                
                # Create a new usage map
                new_usage = {}
                
                # We want to preserve any usage that is ALREADY migrated (unlikely but safe)
                # And migrate any integer keys
                
                for key, val in benefit_usage.items():
                    if key in mapping:
                        # It's an index! Migrate it.
                        new_id = mapping[key]
                        new_usage[new_id] = val
                        needs_update = True
                    else:
                        # Assume it's already a slug or unknown, keep it
                        new_usage[key] = val
                        
                if needs_update:
                    if dry_run:
                        self.stdout.write(f"[Dry Run] User {uid} Card {card_slug}: Migrating keys {list(benefit_usage.keys())} -> {list(new_usage.keys())}")
                    else:
                        # Full replace of benefit_usage field
                        user_cards_ref.document(uc.id).update({'benefit_usage': new_usage})
                        total_migrated_cards += 1
                        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Successfully migrated {total_migrated_cards} user cards."))
        else:
            self.stdout.write(self.style.SUCCESS(f"[Dry Run] Would migrate {total_migrated_cards} user cards."))
