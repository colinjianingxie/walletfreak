from firebase_admin import firestore

class CardMixin:
    def get_cards(self):
        # optimized: Use Collection Group queries to fetch all subcollections in 3 requests total
        # instead of N * 3 requests.
        
        # 1. Fetch all cards
        cards_snapshot = self.get_collection('credit_cards')
        cards_map = {c['id']: c for c in cards_snapshot if 'id' in c}
        
        if not cards_map:
            return []
            
        # Initialize subcollection containers
        for c in cards_map.values():
            c['benefits'] = []
            c['earning_rates'] = []
            c['sign_up_bonus'] = {} 
            c['_raw_bonuses'] = []

        # 2. Fetch Benefits (Collection Group)
        try:
            benefits_docs = self.db.collection_group('benefits').stream()
            for doc in benefits_docs:
                # doc.reference.parent.parent is the Card Document Reference
                parent = doc.reference.parent.parent
                if parent and parent.id in cards_map:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    cards_map[parent.id]['benefits'].append(data)
        except Exception as e:
            print(f"Error fetching benefits collection group: {e}")

        # 3. Fetch Earning Rates (Collection Group)
        try:
            earning_docs = self.db.collection_group('earning_rates').stream()
            for doc in earning_docs:
                parent = doc.reference.parent.parent
                if parent and parent.id in cards_map:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    cards_map[parent.id]['earning_rates'].append(data)
        except Exception as e:
            print(f"Error fetching earning_rates collection group: {e}")

        # 4. Fetch Sign Up Bonuses (Collection Group)
        try:
            bonus_docs = self.db.collection_group('sign_up_bonus').stream()
            for doc in bonus_docs:
                parent = doc.reference.parent.parent
                if parent and parent.id in cards_map:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    cards_map[parent.id]['_raw_bonuses'].append(data)
        except Exception as e:
            print(f"Error fetching sign_up_bonus collection group: {e}")

        # 5. Process Bonuses per card
        for card in cards_map.values():
            raw_bonuses = card.pop('_raw_bonuses')
            card['sign_up_bonus'] = self._process_signup_bonuses(raw_bonuses)

        return list(cards_map.values())
    
    def get_card_by_slug(self, slug):
        card_data = self.get_document('credit_cards', slug)
        if card_data:
            self._enrich_card_with_subcollections(slug, card_data)
        return card_data

    def _process_signup_bonuses(self, bonuses):
        """
        Helper to select the correct bonus from a list of bonus dicts.
        """
        if not bonuses:
            return {}
            
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        valid_bonuses = []
        default_bonus = None
        
        for b in bonuses:
            b_date = b.get('date') or b.get('id')
            
            if b_date == 'default' or b.get('id') == 'default':
                default_bonus = b
            else:
                if b_date and b_date <= today_str:
                    b['resolved_date'] = b_date
                    valid_bonuses.append(b)
        
        valid_bonuses.sort(key=lambda x: x.get('resolved_date', ''), reverse=True)
        
        if valid_bonuses:
            return valid_bonuses[0]
        elif default_bonus:
            return default_bonus
        return {}

    def _enrich_card_with_subcollections(self, card_id, card_data):
        """
        Fetches benefits, earning_rates, and sign_up_bonus from subcollections
        and populates the card_data dictionary in-place.
        (Used for single card fetch)
        """
        try:
            card_ref = self.db.collection('credit_cards').document(card_id)
            
            # 1. Benefits
            benefits = [{**doc.to_dict(), 'id': doc.id} for doc in card_ref.collection('benefits').stream()]
            card_data['benefits'] = benefits
            
            # 2. Earning Rates
            earning_rates = [{**doc.to_dict(), 'id': doc.id} for doc in card_ref.collection('earning_rates').stream()]
            card_data['earning_rates'] = earning_rates
            
            # 3. Sign Up Bonus
            bonuses = [{**doc.to_dict(), 'id': doc.id} for doc in card_ref.collection('sign_up_bonus').stream()]
            card_data['sign_up_bonus'] = self._process_signup_bonuses(bonuses)

        except Exception as e:
            print(f"Error enriching card {card_id}: {e}")

    def add_card_to_user(self, uid, card_id, status='active', anniversary_date=None):
        # status: 'active', 'inactive', 'eyeing'
        user_ref = self.db.collection('users').document(uid)
        card_ref = self.db.collection('credit_cards').document(card_id)
        card_snap = card_ref.get()
        
        if not card_snap.exists:
            return False
            
        card_data = card_snap.to_dict()
        
        # Add to subcollection
        # Add to subcollection
        user_card_data = {
            # 'card_id': card_id,      # REMOVED: Stored as Document ID
            # 'card_slug_id': card_id, # REMOVED: Stored as Document ID
            'name': card_data.get('name'),
            'image_url': card_data.get('image_url'),
            'status': status,
            'added_at': firestore.SERVER_TIMESTAMP,
            'anniversary_date': anniversary_date, # YYYY-MM-DD string or None
            'benefit_usage': {} # Map of benefit_id -> usage
        }
        
        # Add to subcollection using explicit ID (slug)
        # This replaces the correct random ID logic with the Slug ID as Primary Key
        user_card_ref = user_ref.collection('user_cards').document(card_id)
        user_card_ref.set(user_card_data)
        
        # Auto-evaluate personality
        try:
            # 1. Get updated cards
            current_cards = self.get_user_cards(uid, status='active')
            
            # CONSISTENCY FIX: Ensure the new card is in the list (if active)
            # Firestore queries might be eventually consistent
            if status == 'active':
                # Check if card is already in list (by id check using slug)
                if not any(c.get('id') == card_id for c in current_cards):
                    # Append it manually
                    new_card_entry = user_card_data.copy()
                    new_card_entry['id'] = card_id
                    current_cards.append(new_card_entry)
            
            # 2. Determine best fit (handles <= 1 logic internally)
            best_fit = self.determine_best_fit_personality(current_cards)
            
            # 3. Update profile if found
            if best_fit:
                user_card_slugs = set(c.get('card_id') for c in current_cards)
                personality_cards = set()
                for slot in best_fit.get('slots', []):
                    personality_cards.update(slot.get('cards', []))
                overlap = len(user_card_slugs.intersection(personality_cards))
                
                # If student-starter (implicit match), score might be irrelevant or we can set strict defaults
                # The logic above calculates overlap, but for student-starter it might be 0 overlap if it has no defined cards
                # Let's ensure we update regardless.
                
                self.update_user_personality(uid, best_fit.get('id'), score=overlap)
                print(f"Auto-assigned personality {best_fit.get('id')} to user {uid} with score {overlap}")
        except Exception as e:
            print(f"Error auto-evaluating personality: {e}")
            
        return True

    def get_user_cards(self, uid, status=None):
        query = self.db.collection('users').document(uid).collection('user_cards')
        if status:
            # Use FieldFilter to avoid UserWarning about positional arguments
            from google.cloud.firestore import FieldFilter
            query = query.where(filter=FieldFilter('status', '==', status))
        
        # Inject card_id and card_slug_id from doc.id for compatibility
        return [
            doc.to_dict() | {
                'id': doc.id, 
                'card_id': doc.id, 
                'card_slug_id': doc.id
            } 
            for doc in query.stream()
        ]

    def update_card_status(self, uid, user_card_id, new_status):
        ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        ref.update({'status': new_status})

    def remove_card_from_user(self, uid, user_card_id):
        # 1. Fetch doc to get card_slug before deleting
        doc_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        doc = doc_ref.get()
        card_slug = None
        
        if doc.exists:
            card_slug = doc.to_dict().get('card_id') # This is the generic card slug
            doc_ref.delete()
        else:
            # Document might be gone or invalid ID
            return None
        
        # Auto-evaluate personality
        try:
            # 1. Get updated cards (active only)
            current_cards = self.get_user_cards(uid, status='active')
            
            # CONSISTENCY FIX: Explicitly remove the deleted card from the list if present
            # Firestore queries might return the deleted document if eventually consistent
            current_cards = [c for c in current_cards if c.get('id') != user_card_id]
            
            # 2. Determine best fit (handles <= 1 logic internally)
            best_fit = self.determine_best_fit_personality(current_cards)
            
            # 3. Update profile if found
            if best_fit:
                user_card_slugs = set(c.get('card_id') for c in current_cards)
                personality_cards = set()
                for slot in best_fit.get('slots', []):
                    personality_cards.update(slot.get('cards', []))
                overlap = len(user_card_slugs.intersection(personality_cards))
                
                self.update_user_personality(uid, best_fit.get('id'), score=overlap)
                print(f"Auto-assigned personality {best_fit.get('id')} to user {uid} with score {overlap}")
        except Exception as e:
            print(f"Error auto-evaluating personality on remove: {e}")

        return card_slug

    def update_card_details(self, uid, user_card_id, data):
        # Generic update for user card (e.g. anniversary date)
        ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        ref.update(data)

    def update_benefit_usage(self, uid, user_card_id, benefit_name, usage_amount, period_key=None, is_full=False, increment=False):
        card_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        
        update_data = {
            f'benefit_usage.{benefit_name}.last_updated': firestore.SERVER_TIMESTAMP
        }
        
        if period_key:
            # Update specific period
            if increment:
                update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.used'] = firestore.Increment(usage_amount)
                # Note: We cannot increment the main 'used' field accurately if it's just a snapshot, 
                # but we can increment it too assuming it tracks the same period
                update_data[f'benefit_usage.{benefit_name}.used'] = firestore.Increment(usage_amount)
            else:
                update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.used'] = usage_amount
                update_data[f'benefit_usage.{benefit_name}.used'] = usage_amount

            update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.is_full'] = is_full
        else:
            # Legacy/Simple update
            if increment:
                update_data[f'benefit_usage.{benefit_name}.used'] = firestore.Increment(usage_amount)
            else:
                update_data[f'benefit_usage.{benefit_name}.used'] = usage_amount
            
        card_ref.update(update_data)

    def toggle_benefit_ignore(self, uid, user_card_id, benefit_name, is_ignored):
        """Toggle the ignore status of a benefit"""
        card_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        
        update_data = {
            f'benefit_usage.{benefit_name}.is_ignored': is_ignored,
            f'benefit_usage.{benefit_name}.last_updated': firestore.SERVER_TIMESTAMP
        }
        
        card_ref.update(update_data)
