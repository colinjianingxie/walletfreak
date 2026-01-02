from firebase_admin import firestore
from datetime import datetime

class DataPointMixin:
    """
    Mixin for managing DataPoints in Firestore.
    """
    
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
            datapoint_data = {
                'user_id': user_uid,
                # 'user_display_name': Removed, computed at runtime
                'card_slug': data.get('card_slug'),
                'card_name': data.get('card_name'),
                'benefit_name': data.get('benefit_name'),
                'status': data.get('status', 'Success'),
                'content': data.get('content'),
                'date_posted': firestore.SERVER_TIMESTAMP,
                'upvote_count': 0,
                'upvoted_by': [] # List of UIDs
            }
            
            # Create document
            doc_ref = self.db.collection('datapoints').document()
            doc_ref.set(datapoint_data)
            return doc_ref.id
        except Exception as e:
            print(f"Error creating datapoint: {e}")
            return None
            
    def vote_datapoint(self, datapoint_id, user_uid):
        """
        Toggle upvote for a datapoint.
        """
        try:
            doc_ref = self.db.collection('datapoints').document(datapoint_id)
            
            # Use transaction to ensure consistency
            transaction = self.db.transaction()
            
            @firestore.transactional
            def toggle_vote_in_transaction(transaction, doc_ref, uid):
                snapshot = doc_ref.get(transaction=transaction)
                if not snapshot.exists:
                    raise Exception("Datapoint not found")
                    
                data = snapshot.to_dict()
                upvoted_by = data.get('upvoted_by', [])
                
                if uid in upvoted_by:
                    # Remove vote
                    upvoted_by.remove(uid)
                    voted = False
                else:
                    # Add vote
                    upvoted_by.append(uid)
                    voted = True
                    
                new_count = len(upvoted_by)
                
                transaction.update(doc_ref, {
                    'upvoted_by': upvoted_by,
                    'upvote_count': new_count
                })
                
                return voted, new_count

            voted, count = toggle_vote_in_transaction(transaction, doc_ref, user_uid)
            return {'success': True, 'voted': voted, 'count': count}
            
        except Exception as e:
            print(f"Error voting on datapoint: {e}")
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
