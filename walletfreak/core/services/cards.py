from firebase_admin import firestore
from datetime import datetime, timedelta
import ast
from google.cloud.firestore import FieldFilter

class CardMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cards_cache = None
from django.core.cache import cache

class CardMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Removed instance level cache attributes as we use django cache now
    
    def _invalidate_cards_cache(self):
        """Invalidate the cards cache (call this when cards are updated)"""
        cache.delete('all_cards')

    
    def get_cards_basic(self):
        """
        Get basic card info without subcollections (benefits, rates, bonuses).
        Use this when you only need card metadata (name, issuer, annual_fee, etc.)
        """
        cards_snapshot = self.get_collection('master_cards')
        return cards_snapshot

    def get_user_card_count(self, uid):
        """
        Efficiently count user cards using aggregation query.
        """
        try:
            query = self.db.collection('users').document(uid).collection('user_cards')
            # Use count() if available on the query object (newer clients)
            if hasattr(query, 'count'):
                return int(query.count().get()[0][0].value)
            
            # Fallback to AggregateQuery wrapper
            from google.cloud.firestore import AggregateQuery
            return int(AggregateQuery(query.count()).get()[0][0].value)
        except Exception as e:
            print(f"Error counting user cards for {uid}: {e}")
            return 0

    def get_specific_cards(self, slugs, include_subcollections=None):
        """
        Fetch full details for specific card slugs only.
        Much more efficient than get_cards() when we only need a few.
        include_subcollections: Optional list of subcollections to fetch. 
                               e.g. ['benefits']. specific others will be skipped.
                               If None, fetches ALL (default).
        """
        if not slugs:
            return []
            
        hydrated_cards = []
        slugs_to_fetch = []
        
        # 0. Check cache for each slug (ONLY IF we want FULL cards or if cache supports partial... 
        # For now, let's assume cache is always full card. 
        # If we request partial, using full cache is fine (oversupply is okay).
        # But if we rely on partial fetch to save reads, we must be careful not to trigger full fetch on miss if we only wanted partial.
        # But `get_structure` is complex. 
        # Simplification: If cache has it, return it (it's full). If not, we fetch what we asked.
        
        cached_cards_all = cache.get('all_cards')
        all_cards_map = {c['id']: c for c in cached_cards_all} if cached_cards_all else {}
        
        for slug in slugs:
            # Check Full List Cache first
            if slug in all_cards_map:
                hydrated_cards.append(all_cards_map[slug])
                continue
                
            # Check individual cache
            cache_key = f'card_{slug}'
            cached_single = cache.get(cache_key)
            if cached_single:
                hydrated_cards.append(cached_single)
            else:
                slugs_to_fetch.append(slug)
        
        if not slugs_to_fetch:
            return hydrated_cards

        # 1. Fetch Master Docs for remaining
        refs = [self.db.collection('master_cards').document(slug) for slug in slugs_to_fetch]
        # get_all handles multiple refs efficiently
        master_snaps = self.db.get_all(refs)
        
        for snap in master_snaps:
            if snap.exists:
                data = snap.to_dict()
                data['id'] = snap.id
                if 'slug' not in data: data['slug'] = snap.id
                
                # Enrich with subcollections
                # We reuse the existing enrichment logic. 
                # While this iterates per card, for N < 50 it is far more efficient 
                # than fetching all 1500+ cards and their subcollections.
                self._enrich_card_with_subcollections(snap.id, data, include_subcollections=include_subcollections)
                hydrated_cards.append(data)
                
                # Update individual cache ONLY IF full fetch
                # If partial, we shouldn't cache it as "the card" otherwise future requests might get incomplete data.
                if include_subcollections is None:
                    cache.set(f'card_{snap.id}', data, timeout=86400)
                
        return hydrated_cards

    def get_cards(self):
        """
        Get all cards with full subcollections (active benefits, earning_rates, sign_up_bonus).
        Returns hydrated card objects.
        """
        # Check cache first
        cached_cards = cache.get('all_cards')
        if cached_cards:
            return cached_cards
        
        # 1. Fetch all master cards
        cards_snapshot = self.get_collection('master_cards')
        # Sort cards by name for consistent ordering
        cards_snapshot.sort(key=lambda x: x.get('name', ''))
        
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
            c['sign_up_bonus'] = [] 
            c['card_questions'] = []
        
        # Collect all references to fetch
        refs_to_fetch = []
        ref_map = {} # path -> (card_id, type)

        for card_id, c in cards_map.items():
            indices = c.get('active_indices', {})
            
            def add_refs(type_key, collection_name):
                if indices.get(type_key):
                    for item_id in indices[type_key]:
                        ref = self.db.collection('master_cards').document(card_id).collection(collection_name).document(item_id)
                        refs_to_fetch.append(ref)
                        ref_map[ref.path] = (card_id, type_key)

            add_refs('benefits', 'benefits')
            add_refs('earning_rates', 'earning_rates')
            add_refs('sign_up_bonus', 'sign_up_bonus')
            # Removed card_questions from batch fetch based on indices
            # add_refs('card_questions', 'card_questions')

        if refs_to_fetch:
            # Batch Get - Chunking in groups of 100
            chunks = [refs_to_fetch[i:i + 100] for i in range(0, len(refs_to_fetch), 100)]
            
            for chunk in chunks:
                snaps = self.db.get_all(chunk)
                for snap in snaps:
                    if not snap.exists:
                        continue
                    
                    data = snap.to_dict()
                    data['id'] = snap.id
                    
                    # Identify owner
                    card_id, type_key = ref_map.get(snap.reference.path, (None, None))
                    
                    if card_id and card_id in cards_map:
                        container = cards_map[card_id].get(type_key)
                        if isinstance(container, list):
                            container.append(data)

        # 6. Process
        for card in cards_map.values():
            raw_bonuses = card.get('sign_up_bonus', []) if isinstance(card.get('sign_up_bonus'), list) else [] 
            # Note: in loop above we appended to list, but initialization was dict... wait.
            # Initialization above: c['sign_up_bonus'] = {} -> WRONG if used as list accumulator.
            # Let's check logic: `add_refs` uses `indices['sign_up_bonus']`.
            # We append to refs.
            # Then retrieve and append to `container`.
            # If `container` is dict, append fails.
            # FIX: Initialize all as lists.
            
            # Correcting processing logic:
            card['sign_up_bonus'] = self._process_signup_bonuses(card.get('sign_up_bonus', []))
            card['card_questions'] = self._process_card_questions(card.get('card_questions', []))
            card['benefits'].sort(key=lambda x: x.get('benefit_id') or '')

        result = list(cards_map.values())
        
        # Update cache
        # Update cache (Cache for 24 hours as per user request: "does not change very often")
        cache.set('all_cards', result, timeout=86400)
        
        return result
    
    def get_card_by_slug(self, slug):
        if not slug:
            return None
            
        # 1. Try to find in full cache first
        cached_cards = cache.get('all_cards')
        if cached_cards:
            for c in cached_cards:
                if c.get('slug') == slug or c.get('id') == slug:
                    return c
        
        # 2. Try specific cache
        cache_key = f'card_{slug}'
        cached_card = cache.get(cache_key)
        if cached_card:
            return cached_card

        # 3. Fetch from DB
        card_data = self.get_document('master_cards', slug)
        if card_data:
            self._enrich_card_with_subcollections(slug, card_data)
            cache.set(cache_key, card_data, timeout=86400)
            
        return card_data
        
    # Other methods... check _process_signup_bonuses etc are preserved in replacement if outside?
    # No, I am replacing from line 26 to 338 (get_user_card_count to get_user_cards)
    
    # Wait, I need to make sure I don't delete helper methods if they are in the range. 
    # _process_signup_bonuses, _process_card_questions, _enrich_card_with_subcollections, add_card_to_user ARE in the middle.
    # I should Only replace get_user_card_count and get_user_cards.
    # I will break this into chunks.
    
    # Chunk 1: get_user_card_count
    # Chunk 2: get_user_cards
    # And add get_specific_cards
    
    # I will use multi_replace.
    pass

    def get_user_cards(self, uid, status=None, hydrate=True, include_subcollections=None):
        """
        Get user cards.
        hydrate: If True, merges with Master Card data (Requires fetching Master Cards).
                 If False, returns only User Card data (Lightweight).
        include_subcollections: passed to get_specific_cards if hydrate is True.
        """
        query = self.db.collection('users').document(uid).collection('user_cards')
        if status:
            query = query.where(filter=FieldFilter('status', '==', status))
        
        # User Cards are small, stream is fine.
        user_cards_docs = list(query.stream())
        if not user_cards_docs:
            return []
            
        user_cards_map = {} 
        for doc in user_cards_docs:
            data = doc.to_dict()
            card_id = doc.id
            user_cards_map[card_id] = data
            
        if not hydrate:
             return [
                 {**data, 'id': cid, 'card_slug_id': cid} 
                 for cid, data in user_cards_map.items()
             ]
            
        # Get SPECIFIC master data only for efficiency
        # Optimization: Fetch only the cards the user has, avoiding the massive 1500+ card fetch.
        slugs_to_fetch = list(user_cards_map.keys())
        all_hydrated_cards = self.get_specific_cards(slugs_to_fetch, include_subcollections=include_subcollections)
        
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

    def _enrich_card_with_subcollections(self, card_id, card_data, include_subcollections=None):
        try:
            card_ref = self.db.collection('master_cards').document(card_id)
            indices = card_data.get('active_indices', {})
            
            # Prepare result containers
            if include_subcollections is None or 'benefits' in include_subcollections:
                card_data['benefits'] = []
            if include_subcollections is None or 'earning_rates' in include_subcollections:
                card_data['earning_rates'] = []
            if include_subcollections is None or 'sign_up_bonus' in include_subcollections:
                # bonuses list for processing
                pass # Initialized below if needed
            if include_subcollections is None or 'card_questions' in include_subcollections:
                # questions list for processing
                pass

            # Intermediate lists for bonuses/questions
            bonuses = []
            questions = []
            
            refs_to_fetch = []
            ref_type_map = {} # path -> type_key

            def add_refs(type_key, collection):
                if indices.get(type_key):
                    for iid in indices[type_key]:
                        ref = card_ref.collection(collection).document(iid)
                        refs_to_fetch.append(ref)
                        ref_type_map[ref.path] = type_key
            
            if include_subcollections is None or 'benefits' in include_subcollections:
                add_refs('benefits', 'benefits')
            
            if include_subcollections is None or 'earning_rates' in include_subcollections:
                add_refs('earning_rates', 'earning_rates')
            
            if include_subcollections is None or 'sign_up_bonus' in include_subcollections:
                add_refs('sign_up_bonus', 'sign_up_bonus')
            # card_questions fetched directly below

            if refs_to_fetch:
                snaps = self.db.get_all(refs_to_fetch)
                for snap in snaps:
                    if snap.exists:
                        type_key = ref_type_map.get(snap.reference.path)
                        data = {**snap.to_dict(), 'id': snap.id}
                        
                        if type_key == 'benefits':
                            card_data['benefits'].append(data)
                        elif type_key == 'earning_rates':
                            card_data['earning_rates'].append(data)
                        elif type_key == 'sign_up_bonus':
                            bonuses.append(data)
                        elif type_key == 'card_questions':
                            questions.append(data)

            # Process processed fields
            if include_subcollections is None or 'sign_up_bonus' in include_subcollections:
                card_data['sign_up_bonus'] = self._process_signup_bonuses(bonuses)
            
            # Direct Fetch for Questions (Source of Truth: Firestore Subcollection)
            # This bypasses active_indices completely for questions.
            if include_subcollections is None or 'card_questions' in include_subcollections:
                questions_ref = card_ref.collection('card_questions')
                questions_docs = questions_ref.stream()
                for q_doc in questions_docs:
                    q_data = q_doc.to_dict()
                    q_data['id'] = q_doc.id
                    questions.append(q_data)
                    
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
            
        try:
            # Auto-add loyalty program if applicable
            loyalty_program = master_snap.get('loyalty_program')
            if loyalty_program and hasattr(self, 'update_user_loyalty_balance'):
                # Initialize with 0 balance if not exists (merge=True in update_user_loyalty_balance handles preservation)
                # But wait, update_user_loyalty_balance overwrites balance if provided?
                # Let's check update_user_loyalty_balance implementation.
                # It does doc_ref.set(data, merge=True).
                # If I pass balance=0, it might overwrite existing balance if the user already had it?
                # Actually, if the user already has the program, we probably shouldn't reset it to 0.
                # We should check existence first or use a method that only adds if missing.
                # Since update_user_loyalty_balance sets 'balance': balance, it WOULD overwrite.
                # We need a safe add.
                
                # Let's do a direct check here or add a new method? direct check is fine.
                loyalty_ref = self.db.collection('users').document(uid).collection('loyalty_balances').document(loyalty_program)
                if not loyalty_ref.get().exists:
                    self.update_user_loyalty_balance(uid, loyalty_program, 0)
        except Exception as e:
            print(f"Error auto-adding loyalty program: {e}")

        return True



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
