from firebase_admin import firestore
from datetime import datetime, timedelta
import ast
from google.cloud.firestore import FieldFilter

class CardMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cards_cache = None
        self._cards_cache_time = None
        self._cards_cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
    
    def _invalidate_cards_cache(self):
        """Invalidate the cards cache (call this when cards are updated)"""
        self._cards_cache = None
        self._cards_cache_time = None
    
    def get_cards_basic(self):
        """
        Get basic card info without subcollections (benefits, rates, bonuses).
        Use this when you only need card metadata (name, issuer, annual_fee, etc.)
        """
        cards_snapshot = self.get_collection('master_cards')
        return cards_snapshot

    def get_cards(self):
        """
        Get all cards with full subcollections (active benefits, earning_rates, sign_up_bonus).
        Returns hydrated card objects.
        """
        # Check cache first
        if self._cards_cache is not None and self._cards_cache_time is not None:
            if datetime.now() - self._cards_cache_time < self._cards_cache_ttl:
                return self._cards_cache
        
        # 1. Fetch all master cards
        cards_snapshot = self.get_collection('master_cards')
        cards_map = {c['id']: c for c in cards_snapshot if 'id' in c}
        
        if not cards_map:
            return []

        # Ensure slug is present
        for c in cards_map.values():
            if 'slug' not in c:
                c['slug'] = c['id']
            
        # Initialize subcollection containers
        for c in cards_map.values():
            c['benefits'] = []
            c['earning_rates'] = []
            c['sign_up_bonus'] = {} 
            c['card_questions'] = []
            # We will populate these using active_indices if available
        
        # Collect all references to fetch
        stats_benefit_refs = []
        stats_rate_refs = []
        
        # We need to map back results to cards. 
        # Since getAll returns a list of snapshots, we need to know which snapshot belongs to which card?
        # Actually, snapshots contain the reference, and ref.parent.parent is the card.
        # BUT active_indices point to docs inside subcollections. 
        
        valid_indices_count = 0
        
        refs_to_fetch = []
        
        for card_id, c in cards_map.items():
            indices = c.get('active_indices', {})
            
            # Benefits
            if indices.get('benefits'):
                for b_id in indices['benefits']:
                    # Construct ref: master_cards/{card_id}/benefits/{b_id}
                    # Note: b_id in active_indices is the DOC ID (e.g. uber-cash-v1)
                    ref = self.db.collection('master_cards').document(card_id).collection('benefits').document(b_id)
                    refs_to_fetch.append(ref)
            
            # Earning Rates
            if indices.get('earning_rates'):
                for r_id in indices['earning_rates']:
                    ref = self.db.collection('master_cards').document(card_id).collection('earning_rates').document(r_id)
                    refs_to_fetch.append(ref)

            # Check if any indices were found to increment logic check
            if indices:
                valid_indices_count += 1
                
        # Fallback: If active_indices are missing (legacy or not seeded correctly), 
        # we might need the Collection Group query -> BUT that failed due to index.
        # So we MUST rely on active_indices for performance, or iterate linearly (slow).
        # Given we just refactored and seeded, active_indices SHOULD be there.
        # If headers are missing active_indices, we have a data problem.
        
        if refs_to_fetch:
            # Batch Get
            # Chunking in groups of 100
            chunks = [refs_to_fetch[i:i + 100] for i in range(0, len(refs_to_fetch), 100)]
            
            for chunk in chunks:
                snaps = self.db.get_all(chunk)
                for snap in snaps:
                    if not snap.exists:
                        continue
                    
                    data = snap.to_dict()
                    data['id'] = snap.id
                    data['slug'] = snap.id # Ensure slug is present as it is used in views
                    parent_coll = snap.reference.parent
                    card_id = parent_coll.parent.id
                    type_name = parent_coll.id # 'benefits' or 'earning_rates'
                    
                    if card_id in cards_map:
                        if type_name == 'benefits':
                            cards_map[card_id]['benefits'].append(data)
                        elif type_name == 'earning_rates':
                            cards_map[card_id]['earning_rates'].append(data)

        # 4. Fetch Sign Up Bonuses (Collection Group) - Usually small enough or can rely on active_indices too if added
        # current active_indices has 'sign_up_bonus' as single item or list?
        # In refactor script: `active_indices['sign_up_bonus'] = None`. 
        # So we rely on gathering all? Or just fetch the default one?
        # Let's keep Collection Group for SUBs and Questions as they are less frequent updates / fewer docs?
        # Or iterate cards. 
        # Let's simple iterate collection group for now but WITHOUT FILTER.
        # Simply get all SUBs. There aren't that many.
        try:
            bonus_docs = self.db.collection_group('sign_up_bonus').stream()
            for doc in bonus_docs:
                parent = doc.reference.parent.parent
                if parent and parent.id in cards_map:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    if '_raw_bonuses' not in cards_map[parent.id]:
                        cards_map[parent.id]['_raw_bonuses'] = []
                    cards_map[parent.id]['_raw_bonuses'].append(data)
        except Exception as e:
            print(f"Error fetching sign_up_bonus: {e}")

        # 5. Fetch Card Questions
        try:
            questions_docs = self.db.collection_group('card_questions').stream()
            for doc in questions_docs:
                parent = doc.reference.parent.parent
                if parent and parent.id in cards_map:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    if 'card_questions' not in cards_map[parent.id]:
                        cards_map[parent.id]['card_questions'] = []
                    cards_map[parent.id]['card_questions'].append(data)
        except Exception as e:
            print(f"Error fetching card_questions: {e}")

        # 6. Process
        for card in cards_map.values():
            raw_bonuses = card.get('_raw_bonuses', [])
            if '_raw_bonuses' in card: del card['_raw_bonuses']
            
            card['sign_up_bonus'] = self._process_signup_bonuses(raw_bonuses)
            card['card_questions'] = self._process_card_questions(card.get('card_questions', []))
            card['benefits'].sort(key=lambda x: x.get('benefit_id') or '')

        result = list(cards_map.values())
        
        # Update cache
        self._cards_cache = result
        self._cards_cache_time = datetime.now()
        
        return result
    
    def get_card_by_slug(self, slug):
        card_data = self.get_document('master_cards', slug)
        if card_data:
            self._enrich_card_with_subcollections(slug, card_data)
        return card_data

    def _process_signup_bonuses(self, bonuses):
        if not bonuses:
            return {}
        from datetime import datetime
        today_str = datetime.now().strftime('%Y-%m-%d')
        valid_bonuses = []
        default_bonus = None
        for b in bonuses:
            b_date = b.get('date') or b.get('effective_date') or b.get('id')
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

    def _process_card_questions(self, questions):
        processed = []
        for q in questions:
            choice_list = []
            try:
                raw_choices = q.get('ChoiceList')
                if isinstance(raw_choices, str):
                    choice_list = ast.literal_eval(raw_choices)
                elif isinstance(raw_choices, list):
                    choice_list = raw_choices
            except (ValueError, SyntaxError):
                choice_list = []

            choice_weights = []
            try:
                raw_weights = q.get('ChoiceWeight')
                if isinstance(raw_weights, str):
                    choice_weights = ast.literal_eval(raw_weights)
                elif isinstance(raw_weights, list):
                    choice_weights = raw_weights
            except (ValueError, SyntaxError):
                choice_weights = []
            item = {
                'short_desc': q.get('short_desc') or q.get('BenefitShortDescription', ''),
                'question_type': q.get('question_type') or q.get('QuestionType', 'yes_no'),
                'choices': q.get('choices') or choice_list,
                'weights': q.get('weights') or choice_weights,
                'question': q.get('question') or q.get('Question', ''),
                'category': q.get('benefit_category') or q.get('BenefitCategory', ''),
                'id': q.get('id')
            }
            processed.append(item)
        return processed

    def _enrich_card_with_subcollections(self, card_id, card_data):
        try:
            card_ref = self.db.collection('master_cards').document(card_id)
            
            # Using active_indices here for single card as well if available
            indices = card_data.get('active_indices', {})
            benefits = []
            earning_rates = []
            
            if indices.get('benefits'):
                # Fetch specific
                refs = [card_ref.collection('benefits').document(bid) for bid in indices['benefits']]
                for snap in self.db.get_all(refs):
                    if snap.exists:
                         benefits.append({**snap.to_dict(), 'id': snap.id})
            else:
                 # Fallback to query
                benefits = [{**doc.to_dict(), 'id': doc.id} 
                    for doc in card_ref.collection('benefits').where(filter=FieldFilter('is_active', '==', True)).stream()]
            
            card_data['benefits'] = benefits
            
            if indices.get('earning_rates'):
                 refs = [card_ref.collection('earning_rates').document(rid) for rid in indices['earning_rates']]
                 for snap in self.db.get_all(refs):
                    if snap.exists:
                         earning_rates.append({**snap.to_dict(), 'id': snap.id})
            else:
                earning_rates = [{**doc.to_dict(), 'id': doc.id} 
                    for doc in card_ref.collection('earning_rates').where(filter=FieldFilter('is_active', '==', True)).stream()]
            card_data['earning_rates'] = earning_rates
            
            bonuses = [{**doc.to_dict(), 'id': doc.id} for doc in card_ref.collection('sign_up_bonus').stream()]
            card_data['sign_up_bonus'] = self._process_signup_bonuses(bonuses)

            questions = [{**doc.to_dict(), 'id': doc.id} for doc in card_ref.collection('card_questions').stream()]
            card_data['card_questions'] = self._process_card_questions(questions)

        except Exception as e:
            print(f"Error enriching card {card_id}: {e}")

    def add_card_to_user(self, uid, card_id, status='active', anniversary_date=None):
        user_ref = self.db.collection('users').document(uid)
        master_ref = self.db.collection('master_cards').document(card_id)
        master_snap = master_ref.get()
        
        if not master_snap.exists:
            return False
        
        user_card_data = {
            'card_ref': master_ref,
            'card_slug_id': card_id, 
            'status': status,
            'added_at': firestore.SERVER_TIMESTAMP,
            'anniversary_date': anniversary_date,
            'benefit_usage': {}
        }
        
        user_card_ref = user_ref.collection('user_cards').document(card_id)
        user_card_ref.set(user_card_data, merge=True)
        
        try:
            current_cards = self.get_user_cards(uid, status='active')
            best_fit = self.determine_best_fit_personality(current_cards)
            if best_fit:
                user_card_slugs = set(c.get('card_id') for c in current_cards)
                personality_cards = set()
                for slot in best_fit.get('slots', []):
                    personality_cards.update(slot.get('cards', []))
                overlap = len(user_card_slugs.intersection(personality_cards))
                self.update_user_personality(uid, best_fit.get('id'), score=overlap)
        except Exception as e:
            print(f"Error auto-evaluating personality: {e}")
            
        return True

    def get_user_cards(self, uid, status=None):
        query = self.db.collection('users').document(uid).collection('user_cards')
        if status:
            query = query.where(filter=FieldFilter('status', '==', status))
        
        user_cards_docs = list(query.stream())
        if not user_cards_docs:
            return []
            
        user_cards_map = {} 
        for doc in user_cards_docs:
            data = doc.to_dict()
            card_id = doc.id
            user_cards_map[card_id] = data
            
        # Get cached master data for efficiency
        all_hydrated_cards = self.get_cards() 
        hydrated_map = {c['id']: c for c in all_hydrated_cards}
        
        results = []
        for card_id, user_data in user_cards_map.items():
            master_card = hydrated_map.get(card_id)
            if master_card:
                composite = master_card.copy()
                composite.update({
                    'user_card_id': card_id,
                    'status': user_data.get('status'),
                    'added_at': user_data.get('added_at'),
                    'anniversary_date': user_data.get('anniversary_date'),
                    'benefit_usage': user_data.get('benefit_usage', {}),
                    'id': card_id,
                    'card_id': card_id,
                    'card_slug_id': card_id,
                    'card_ref': user_data.get('card_ref') # Preserve ref
                })
                results.append(composite)
            else:
                results.append(user_data | {'id': card_id, 'name': 'Unknown Card'})

        return results

    def update_card_status(self, uid, user_card_id, new_status):
        ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        ref.update({'status': new_status})

    def remove_card_from_user(self, uid, user_card_id):
        doc_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        doc = doc_ref.get()
        card_slug = None
        
        if doc.exists:
            card_slug = doc_ref.id 
            doc_ref.delete()
        else:
            return None
        
        try:
            current_cards = self.get_user_cards(uid, status='active')
            current_cards = [c for c in current_cards if c.get('id') != user_card_id]
            best_fit = self.determine_best_fit_personality(current_cards)
            if best_fit:
                user_card_slugs = set(c.get('card_id') for c in current_cards)
                personality_cards = set()
                for slot in best_fit.get('slots', []):
                    personality_cards.update(slot.get('cards', []))
                overlap = len(user_card_slugs.intersection(personality_cards))
                self.update_user_personality(uid, best_fit.get('id'), score=overlap)
        except Exception as e:
            print(f"Error auto-evaluating personality on remove: {e}")

        return card_slug

    def update_card_details(self, uid, user_card_id, data):
        ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        ref.update(data)

    def update_benefit_usage(self, uid, user_card_id, benefit_name, usage_amount, period_key=None, is_full=False, increment=False):
        card_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        
        update_data = {
            f'benefit_usage.{benefit_name}.last_updated': firestore.SERVER_TIMESTAMP
        }
        
        if period_key:
            if increment:
                update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.used'] = firestore.Increment(usage_amount)
                update_data[f'benefit_usage.{benefit_name}.used'] = firestore.Increment(usage_amount)
            else:
                update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.used'] = usage_amount
                update_data[f'benefit_usage.{benefit_name}.used'] = usage_amount

            update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.is_full'] = is_full
        else:
            if increment:
                update_data[f'benefit_usage.{benefit_name}.used'] = firestore.Increment(usage_amount)
            else:
                update_data[f'benefit_usage.{benefit_name}.used'] = usage_amount
            
        card_ref.update(update_data)

    def toggle_benefit_ignore(self, uid, user_card_id, benefit_name, is_ignored):
        card_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        update_data = {
            f'benefit_usage.{benefit_name}.is_ignored': is_ignored,
            f'benefit_usage.{benefit_name}.last_updated': firestore.SERVER_TIMESTAMP
        }
        card_ref.update(update_data)
