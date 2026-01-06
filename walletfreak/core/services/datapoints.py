from firebase_admin import firestore
from datetime import datetime, date

class DataPointMixin:
    """
    Mixin for managing DataPoints in Firestore.
    """
    
    def _ensure_datetime(self, val):
        if isinstance(val, date) and not isinstance(val, datetime):
            return datetime.combine(val, datetime.min.time())
        return val

    def get_datapoints(self, limit=50, sort_by='newest', card_slug=None):
        """
        Fetch datapoints with filtering and sorting.
        """
        try:
            query = self.db.collection('datapoints')
            
            # Filter by card
            if card_slug:
                query = query.where('card_slug', '==', card_slug)
                
            # Sorting
            if sort_by == 'popular':
                query = query.order_by('upvote_count', direction=firestore.Query.DESCENDING)
                query = query.order_by('date_posted', direction=firestore.Query.DESCENDING)
            elif sort_by == 'oldest':
                query = query.order_by('date_posted', direction=firestore.Query.ASCENDING)
            else: # newest
                query = query.order_by('date_posted', direction=firestore.Query.DESCENDING)
                
            if limit:
                query = query.limit(limit)
                
            docs = query.stream()
            datapoints = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                # Ensure date_posted is a datetime object
                if 'date_posted' in data and not isinstance(data['date_posted'], datetime):
                    # Handle string conversion if needed, though Firestore returns datetime
                    pass
                datapoints.append(data)
                
            return datapoints
        except Exception as e:
            print(f"Error fetching datapoints: {e}")
            return []
            
    def create_datapoint(self, user_uid, data):
        """
        Create a new datapoint.
        data matches the fields in the form/model.
        """
        try:
            # Fetch user profile to get display name
            user = self.get_user_profile(user_uid)
            user_display_name = user.get('username') if user else 'anonymous'
            
            t_date = self._ensure_datetime(data.get('transaction_date'))
            c_date = self._ensure_datetime(data.get('cleared_date'))
            
            datapoint_data = {
                'user_id': user_uid,
                'user_display_name': user_display_name,
                'card_slug': data.get('card_slug'),
                'card_name': data.get('card_name'),
                'benefit_name': data.get('benefit_name'),
                'status': data.get('status', 'Success'),
                'content': data.get('content'),
                'transaction_date': t_date,
                'cleared_date': c_date,
                'date_posted': firestore.SERVER_TIMESTAMP,
                'last_verified': None,
                'upvote_count': 0,
                'upvoted_by': [], # List of UIDs
                'outdated_count': 0,
                'outdated_by': [],
                'is_edited': False
            }
            
            # Create document
            doc_ref = self.db.collection('datapoints').document()
            doc_ref.set(datapoint_data)
            return doc_ref.id
        except Exception as e:
            print(f"Error creating datapoint: {e}")
            return None

    def update_datapoint(self, datapoint_id, user_uid, data):
        """
        Update an existing datapoint.
        Only the owner can update.
        """
        try:
            doc_ref = self.db.collection('datapoints').document(datapoint_id)
            snapshot = doc_ref.get()
            
            if not snapshot.exists:
                return {'success': False, 'error': 'Datapoint not found'}
                
            existing_data = snapshot.to_dict()
            if existing_data.get('user_id') != user_uid:
                return {'success': False, 'error': 'Permission denied'}
            
            t_date = self._ensure_datetime(data.get('transaction_date'))
            c_date = self._ensure_datetime(data.get('cleared_date'))

            update_data = {
                'content': data.get('content'),
                'status': data.get('status'),
                'transaction_date': t_date,
                'cleared_date': c_date,
                'is_edited': True,
                'edited_at': firestore.SERVER_TIMESTAMP
            }
            
            # Remove None values to avoid overwriting with null if intention was to keep
            # But form usually sends all or nothing. 
            # If status changed to Failed, cleared_date might be None.
            # So updating with None is valid for cleared_date.
            
            doc_ref.update(update_data)
            return {'success': True}
        except Exception as e:
            print(f"Error updating datapoint: {e}")
            return {'success': False, 'error': str(e)}
            
    def vote_datapoint(self, datapoint_id, user_uid):
        """
        Toggle upvote for a datapoint. Mutually exclusive with outdated.
        """
        try:
            doc_ref = self.db.collection('datapoints').document(datapoint_id)
            
            transaction = self.db.transaction()
            
            @firestore.transactional
            def toggle_vote_in_transaction(transaction, doc_ref, uid):
                snapshot = doc_ref.get(transaction=transaction)
                if not snapshot.exists:
                    raise Exception("Datapoint not found")
                    
                data = snapshot.to_dict()
                upvoted_by = data.get('upvoted_by', [])
                outdated_by = data.get('outdated_by', [])
                
                marked_outdated = False
                updated_verified = False
                
                if uid in upvoted_by:
                    # Remove vote
                    upvoted_by.remove(uid)
                    voted = False
                else:
                    # Add vote
                    upvoted_by.append(uid)
                    voted = True
                    updated_verified = True
                    # Remove from outdated if present
                    if uid in outdated_by:
                        outdated_by.remove(uid)
                
                # Check status of outdated (to return to frontend)
                marked_outdated = uid in outdated_by
                    
                upvote_count = len(upvoted_by)
                outdated_count = len(outdated_by)
                
                update_payload = {
                    'upvoted_by': upvoted_by,
                    'upvote_count': upvote_count,
                    'outdated_by': outdated_by,
                    'outdated_count': outdated_count
                }
                
                if updated_verified:
                    update_payload['last_verified'] = firestore.SERVER_TIMESTAMP
                
                transaction.update(doc_ref, update_payload)
                
                return {
                    'voted': voted, 
                    'upvote_count': upvote_count, 
                    'marked_outdated': marked_outdated, 
                    'outdated_count': outdated_count,
                    'updated_verified': updated_verified
                }

            return {'success': True, **toggle_vote_in_transaction(transaction, doc_ref, user_uid)}
            
        except Exception as e:
            print(f"Error voting on datapoint: {e}")
            return {'success': False, 'error': str(e)}

    def mark_outdated(self, datapoint_id, user_uid):
        """
        Toggle outdated flag for a datapoint. Mutually exclusive with upvote.
        """
        try:
            doc_ref = self.db.collection('datapoints').document(datapoint_id)
            
            transaction = self.db.transaction()
            
            @firestore.transactional
            def toggle_outdated_in_transaction(transaction, doc_ref, uid):
                snapshot = doc_ref.get(transaction=transaction)
                if not snapshot.exists:
                    raise Exception("Datapoint not found")
                    
                data = snapshot.to_dict()
                outdated_by = data.get('outdated_by', [])
                upvoted_by = data.get('upvoted_by', [])
                
                voted = False
                
                if uid in outdated_by:
                    outdated_by.remove(uid)
                    marked = False
                else:
                    outdated_by.append(uid)
                    marked = True
                    # Remove from upvoted if present
                    if uid in upvoted_by:
                        upvoted_by.remove(uid)
                
                # Check status of upvote
                voted = uid in upvoted_by
                    
                new_outdated_count = len(outdated_by)
                new_upvote_count = len(upvoted_by)
                
                transaction.update(doc_ref, {
                    'outdated_by': outdated_by,
                    'outdated_count': new_outdated_count,
                    'upvoted_by': upvoted_by,
                    'upvote_count': new_upvote_count
                })
                
                return {
                    'marked_outdated': marked, 
                    'outdated_count': new_outdated_count,
                    'voted': voted,
                    'upvote_count': new_upvote_count
                }

            return {'success': True, **toggle_outdated_in_transaction(transaction, doc_ref, user_uid)}
            
        except Exception as e:
            print(f"Error marking outdated: {e}")
            return {'success': False, 'error': str(e)}

    def get_active_card_slugs(self):
        """
        Fetch distinct card slugs from valid datapoints.
        Sorts alphabetically.
        """
        try:
            # Projection query - only fetch card_slug
            docs = self.db.collection('datapoints').select(['card_slug']).stream()
            slugs = {doc.to_dict().get('card_slug') for doc in docs}
            # Remove None if present
            slugs.discard(None)
            return sorted(list(slugs))
        except Exception as e:
            print(f"Error fetching active card slugs: {e}")
            return []
