from firebase_admin import firestore

class CardMixin:
    def get_cards(self):
        return self.get_collection('credit_cards')
    
    def get_card_by_slug(self, slug):
        # Assuming doc ID is the slug
        return self.get_document('credit_cards', slug)

    def add_card_to_user(self, uid, card_id, status='active', anniversary_date=None):
        # status: 'active', 'inactive', 'eyeing'
        user_ref = self.db.collection('users').document(uid)
        card_ref = self.db.collection('credit_cards').document(card_id)
        card_snap = card_ref.get()
        
        if not card_snap.exists:
            return False
            
        card_data = card_snap.to_dict()
        
        # Add to subcollection
        user_card_data = {
            'card_id': card_id,
            'name': card_data.get('name'),
            'image_url': card_data.get('image_url'),
            'status': status,
            'added_at': firestore.SERVER_TIMESTAMP,
            'anniversary_date': anniversary_date, # YYYY-MM-DD string or None
            'benefit_usage': {} # Map of benefit_id -> usage
        }
        
        # Add returns a tuple (update_time, doc_ref)
        _, new_doc_ref = user_ref.collection('user_cards').add(user_card_data)
        
        # Auto-evaluate personality
        try:
            # 1. Get updated cards
            current_cards = self.get_user_cards(uid, status='active')
            
            # CONSISTENCY FIX: Ensure the new card is in the list (if active)
            # Firestore queries might be eventually consistent
            if status == 'active':
                # Check if card is already in list (by id check using new_doc_ref.id)
                if not any(c.get('id') == new_doc_ref.id for c in current_cards):
                    # Append it manually
                    new_card_entry = user_card_data.copy()
                    new_card_entry['id'] = new_doc_ref.id
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
        return [doc.to_dict() | {'id': doc.id} for doc in query.stream()]

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
