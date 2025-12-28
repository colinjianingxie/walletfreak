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
        Calculate match scores for all cards based on user's personality and wallet using the 4-Dimension Algorithm:
        1. Incremental Utility (45%)
        2. Personality Alignment (35%)
        3. SUB ROI (15%)
        4. Fee Affinity (5%)
        
        Returns a dictionary {card_id: score}.
        """
        scores = {}
        
        # 0. Check for Empty Wallet logic no longer applies strictly as we need to recommend cards regardless
        # But if user_cards is empty, Incremental Utility is just absolute utility
        
        if not user_personality:
            # Fallback or simple score? For now return 0s
            for card in all_cards:
                scores[card['id']] = 0
            return scores

        # Pre-process User Best Rates for Dimension 1
        user_best_rates = self._get_user_best_rates(user_cards)
        
        # Pre-process User Avg Fee for Dimension 4
        user_avg_fee = 0
        if user_cards:
            total_fees = sum(float(c.get('annual_fee', 0) or 0) for c in user_cards)
            user_avg_fee = total_fees / len(user_cards)
        else:
            user_avg_fee = 95 # Default anchor if wallet is empty
            if not user_cards: user_avg_fee = 0

        for card in all_cards:
            c_id = card['id']
            # Skip if card is already in user's wallet
            is_owned = False
            for owned in user_cards:
                if owned.get('id') == c_id or owned.get('slug') == card.get('slug'):
                    is_owned = True
                    break
            
            if is_owned:
                scores[c_id] = 0
                continue

            # --- Dimension 1: Incremental Utility (45%) ---
            d1_score = self._calculate_incremental_utility(card, user_best_rates)
            
            # --- Dimension 2: Personality Alignment (35%) ---
            d2_score = self._calculate_personality_alignment(card, user_personality)
            
            # --- Dimension 3: SUB ROI (15%) ---
            d3_score = self._calculate_sub_roi(card)
            
            # --- Dimension 4: Fee Affinity (5%) ---
            d4_score = self._calculate_fee_affinity(card, user_avg_fee)
            
            # --- Weighted Aggregation ---
            final_score = (d1_score * 0.45) + (d2_score * 0.35) + (d3_score * 0.15) + (d4_score * 0.05)
            
            scores[c_id] = min(100.0, max(0.0, final_score))
            
        return scores

    def _get_user_best_rates(self, user_cards):
        """
        Returns a dictionary: { 'CategoryName': max_rate_found }
        """
        best_rates = {}
        if not user_cards:
            return best_rates
            
        for card in user_cards:
            rates = card.get('earning_rates', [])
            for r in rates:
                rate_val = float(r.get('rate', 0) or 0)
                cats = r.get('category', [])
                if isinstance(cats, str):
                    try:
                        import json
                        cats = json.loads(cats)
                    except:
                        cats = [cats]
                
                # Normalize cats to list
                if not isinstance(cats, list):
                    cats = [str(cats)]
                    
                for cat in cats:
                    current_max = best_rates.get(cat, 0.0)
                    if rate_val > current_max:
                        best_rates[cat] = rate_val
        return best_rates

    def _calculate_incremental_utility(self, card, user_best_rates):
        """
        Dimension 1: Incremental Utility
        Iterate through candidate card's earning rates.
        Delta = CardRate - UserBestRate (min 0)
        Score = sum(Delta * Weight)
        """
        total_utility = 0.0
        
        # Category Weights
        def get_weight(cat_name):
            cat_lower = cat_name.lower()
            if 'grocery' in cat_lower or 'groceries' in cat_lower or 'dining' in cat_lower or 'restaurant' in cat_lower:
                return 1.0
            if 'travel' in cat_lower or 'gas' in cat_lower or 'mobile wallet' in cat_lower or 'transit' in cat_lower or 'flight' in cat_lower or 'hotel' in cat_lower:
                return 0.8
            if 'online' in cat_lower or 'retail' in cat_lower or 'entertainment' in cat_lower or 'streaming' in cat_lower:
                return 0.5
            return 0.2

        rates = card.get('earning_rates', [])
        
        for r in rates:
            rate_val = float(r.get('rate', 0) or 0)
            cats = r.get('category', [])
            if isinstance(cats, str):
                try:
                    import json
                    cats = json.loads(cats)
                except:
                    cats = [cats]
            if not isinstance(cats, list):
                cats = [str(cats)]

            for cat in cats:
                if cat.lower() == 'all purchases':
                    user_best = user_best_rates.get('All Purchases', user_best_rates.get('General', 1.0))
                else:
                    user_best = user_best_rates.get(cat, user_best_rates.get('All Purchases', 1.0))
                
                delta = max(0.0, rate_val - user_best)
                weight = get_weight(cat)
                
                total_utility += delta * weight
                
        # Normalize to 0-100 scale based on max possible gap
        # Uses multiplier 20.0 as derived from example (1.2 raw -> 24 score)
        normalized_score = total_utility * 20.0
        return min(100.0, normalized_score)

    def _calculate_personality_alignment(self, card, personality):
        """
        Dimension 2: Personality Alignment
        % of BenefitCategory + Keywords matches.
        """
        # Targets: Personality Categories (Keywords)
        target_keywords = set([k.lower() for k in personality.get('categories', [])])
        
        # Sources: Card Benefit Categories + Short Titles + Name
        card_tags = set()
        
        # Benefits
        for b in card.get('benefits', []):
            # parse_updates.py normalizes to 'category' and 'short_description'
            cats = b.get('category', []) or b.get('benefit_category', [])
            if isinstance(cats, str): cats = [cats]
            for c in cats:
                card_tags.add(c.lower())
            
            short = b.get('short_description') or b.get('benefit_description_short')
            if short:
                card_tags.add(short.lower())
        
        # Earning Categories (Why not? If it earns on Apple, it aligns with Apple personality)
        for r in card.get('earning_rates', []):
            cats = r.get('category', [])
            if isinstance(cats, str):
                try:
                    import json
                    cats = json.loads(cats)
                except:
                    cats = [cats]
            if not isinstance(cats, list): cats = [str(cats)]
            for c in cats:
                card_tags.add(c.lower())

        card_tags.add(card.get('name', '').lower())
        
        # Match
        matches = 0
        if not target_keywords: 
            return 0.0

        for kw in target_keywords:
            for tag in card_tags:
                if kw in tag or tag in kw: # Loose match
                    matches += 1
                    break
        
        percent_match = 0
        if len(target_keywords) > 0:
            percent_match = (matches / len(target_keywords)) * 100.0
            
        # Slot Multiplier
        in_slot = False
        c_id = card.get('id')
        c_slug = card.get('slug')
        
        for slot in personality.get('slots', []):
            slot_cards = slot.get('cards', [])
            if c_id in slot_cards or (c_slug and c_slug in slot_cards):
                in_slot = True
                break
                
        if in_slot:
            percent_match *= 1.5
            
        return min(100.0, percent_match)

    def _calculate_sub_roi(self, card):
        """
        Dimension 3: Sign-Up Bonus ROI
        """
        sub = card.get('sign_up_bonus', {})
        if not sub:
            return 0.0
            
        try:
            value = float(sub.get('value', 0) or 0)
            spend = float(sub.get('spend_amount', 0) or 0)
            currency = sub.get('currency', 'Points')
            cpp = float(card.get('points_value_cpp', 1.0) or 1.0)
            af = float(card.get('annual_fee', 0) or 0)
        except:
            return 0.0
            
        if value == 0:
            return 0.0
            
        dollar_value = value
        if 'cash' not in str(currency).lower():
            dollar_value = value * (cpp / 100.0)
            
        net_value = dollar_value - af
        
        if spend <= 0:
            return 100.0 if net_value > 0 else 0.0
            
        roi = (net_value / spend) * 100.0
        
        # Cap ROI score at 100 for >100% ROI? 
        # Or should 20% ROI be a score of 20? 
        # Let's simple cap at 100.
        return min(100.0, roi)

    def _calculate_fee_affinity(self, card, user_avg_fee):
        """
        Dimension 4: Fee & Strategy Affinity
        Formula: 1 - (|CardFee - AvgFee| / 500)
        """
        card_fee = float(card.get('annual_fee', 0) or 0)
        
        diff = abs(card_fee - user_avg_fee)
        denom = 500.0
        
        similarity = 1.0 - (diff / denom)
        
        return max(0.0, similarity * 100.0)
