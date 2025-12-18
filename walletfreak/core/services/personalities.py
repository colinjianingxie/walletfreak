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
