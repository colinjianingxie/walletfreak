from firebase_admin import firestore

class PersonalityMixin:
    def get_personalities(self):
        return self.get_collection('personalities')

    def get_personality_by_slug(self, slug):
        return self.get_document('personalities', slug)

    def determine_best_fit_personality(self, user_cards):
        """
        Determines the best personality fit based on user's active cards.
        user_cards: list of card objects (dicts containing at least 'card_id')
        """
        # RULE: <= 1 active card -> Always 'student-starter'
        if not user_cards or len(user_cards) <= 1:
            return self.get_personality_by_slug('student-starter')

        personalities = self.get_personalities()
        if not personalities:
            return None
            
        user_card_slugs = set(card.get('card_id') for card in user_cards)
        
        best_fit = None
        max_overlap = -1
        
        for personality in personalities:
            # Flatten all cards in all slots for this personality
            personality_cards = set()
            for slot in personality.get('slots', []):
                personality_cards.update(slot.get('cards', []))
            
            # Calculate overlap
            overlap = len(user_card_slugs.intersection(personality_cards))
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_fit = personality
            elif overlap == max_overlap and best_fit is None:
                 # Default to first one if tie and no best fit yet
                 best_fit = personality
                 
        return best_fit

    def update_user_personality(self, uid, personality_id, score=None):
        """
        Update user's assigned personality in their profile.
        """
        user_ref = self.db.collection('users').document(uid)
        update_data = {
            'assigned_personality': personality_id,
            'personality_assigned_at': firestore.SERVER_TIMESTAMP
        }
        
        if score is not None:
            update_data['personality_score'] = score
        
        # Check if user profile exists
        user_doc = user_ref.get()
        if user_doc.exists:
            user_ref.update(update_data)
        else:
            # Create user profile if it doesn't exist
            user_ref.set(update_data)
    
    def get_user_assigned_personality(self, uid):
        """
        Get user's assigned personality with full details.
        Returns personality object with additional 'match_score' field, or None.
        """
        active_cards = self.get_user_cards(uid, status='active')
        if not active_cards:
            personality = self.get_personality_by_slug('student-starter')
            if personality:
                 personality['match_score'] = 99 # Default high score for starter
                 personality['is_default_assignment'] = True
                 return personality
                 
        user = self.get_user_profile(uid)
        if user and user.get('assigned_personality'):
            personality_id = user.get('assigned_personality')
            personality = self.get_personality_by_slug(personality_id)
            
            if personality:
                # Add match score to personality object
                personality['match_score'] = user.get('personality_score', 0)
                personality['assigned_at'] = user.get('personality_assigned_at')
                
                # Add avatar URL
                # Assumes icon exists at static/images/personalities/{slug}.png
                personality['avatar_url'] = f"/static/images/personalities/{personality['slug']}.png"
            
                return personality

        return None
    
    def remove_user_personality(self, uid):
        """Remove user's assigned personality"""
        self.db.collection('users').document(uid).update({
            'assigned_personality': None,
            'personality_score': 0,
            'personality_assigned_at': None
        })

    def get_quiz_questions(self):
        """Get all quiz questions sorted by stage"""
        query = self.db.collection('quiz_questions').order_by('stage')
        return [doc.to_dict() | {'id': doc.id} for doc in query.stream()]

    # Personality Survey Methods
    def save_personality_survey(self, uid, personality_id, responses, card_ids, is_published=False):
        """
        Save a user's personality survey response.
        Returns the survey document ID.
        """
        survey_data = {
            'user_id': uid,
            'personality_id': personality_id,
            'responses': responses,
            'card_ids': card_ids,
            'is_published': is_published,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        # Add to surveys collection
        _, doc_ref = self.db.collection('personality_surveys').add(survey_data)
        
        # Update user profile with survey completion
        user_ref = self.db.collection('users').document(uid)
        user_ref.update({
            'survey_completed': True,
            'survey_personality': personality_id,
            'survey_completed_at': firestore.SERVER_TIMESTAMP
        })
        
        return doc_ref.id
    
    def get_user_survey(self, uid):
        """
        Get the most recent survey for a user.
        """
        from google.cloud.firestore import FieldFilter
        query = self.db.collection('personality_surveys').where(
            filter=FieldFilter('user_id', '==', uid)
        ).order_by('created_at', direction=firestore.Query.DESCENDING).limit(1)
        
        docs = list(query.stream())
        if docs:
            return {**docs[0].to_dict(), 'id': docs[0].id}
        return None
    
    def publish_user_personality(self, uid):
        """
        Mark user's most recent survey as published for crowd-sourcing.
        """
        survey = self.get_user_survey(uid)
        if survey:
            self.db.collection('personality_surveys').document(survey['id']).update({
                'is_published': True,
                'published_at': firestore.SERVER_TIMESTAMP
            })
            return True
        return False
    
    def calculate_match_scores(self, user_personality, user_cards, all_cards):
        """
        Calculate match scores for all cards based on user's personality and wallet.
        Returns a dictionary {card_id: score}.
        """
        scores = {}
        
        # 0. Check for Empty Wallet
        # If user has no cards, they match 0% with everything by default
        if not user_cards:
            for card in all_cards:
                scores[card['id']] = 0
            return scores

        if not user_personality:
            return scores

        # 1. Analyze User Wallet Gaps
        user_card_ids = set(c['card_id'] for c in user_cards) if user_cards else set()
        
        # Identify slots and their fill status
        personality_slots = user_personality.get('slots', [])
        # slots is a list of slot dicts
        
        slot_status = {} # slot_index: is_filled (bool)

        for i, slot in enumerate(personality_slots):
            cards_in_slot = set(slot.get('cards', []))
            
            # Check if ANY card from this slot is in user's wallet
            is_filled = not cards_in_slot.isdisjoint(user_card_ids)
            slot_status[i] = is_filled

        # 2. Derive Focus Categories
        focus_categories = set(user_personality.get('focus_categories', []))
        
        # 3. Grading Loop
        for card in all_cards:
            score = 0
            c_id = card['id']
            c_slug = card.get('slug', '')
            
            # Deterministic variance for "minute" matches (-3 to +3)
            # Use ASCII sum of ID
            variance = (sum(ord(c) for c in str(c_id)) % 7) - 3
            
            # Check if card is part of the personality
            in_personality = False
            target_slot_index = -1
            
            for i, slot in enumerate(personality_slots):
                if c_id in slot.get('cards', []) or c_slug in slot.get('cards', []):
                    in_personality = True
                    target_slot_index = i
                    break
            
            if in_personality:
                # TIER 1 & 2
                if not slot_status.get(target_slot_index, True):
                    # Tier 1: Empty Slot (Gap Filler) -> ~97%
                    score = 97 + variance
                else:
                    # Tier 2: Already Filled Slot (Alternative) -> ~87%
                    score = 87 + variance
            else:
                # TIER 3: Category Match
                # Base score for non-personality cards -> ~43%
                score = 43 + variance
                
                # Check category overlap
                card_categories = set(card.get('categories', []))
                if focus_categories:
                    overlap = len(card_categories.intersection(focus_categories))
                    # +12 per matching category, up to +36 max
                    score += min(36, overlap * 12)
            
            # 4. Adjustments
            annual_fee = card.get('annual_fee', 0)
            
            # Bonus for No Annual Fee
            if annual_fee == 0:
                score += 3
            # Penalty for High Annual Fee (unless it's a Tier 1 perfect match)
            elif annual_fee > 500 and score < 90:
                score -= 4
                
            # Clamp
            scores[c_id] = max(0, min(100, score))
            
            # Final Override: If card is already in wallet, match score is 0
            if c_id in user_card_ids or (c_slug and c_slug in user_card_ids):
                scores[c_id] = 0
            
        return scores
