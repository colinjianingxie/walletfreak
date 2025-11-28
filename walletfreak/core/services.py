import firebase_admin
from firebase_admin import firestore
from django.conf import settings

class FirestoreService:
    def __init__(self):
        # Ensure app is initialized (it should be in settings.py)
        if not firebase_admin._apps:
             # This fallback is mostly for local testing if settings didn't catch it
             pass
        self.db = firestore.client()

    def get_collection(self, collection_name, limit=None):
        ref = self.db.collection(collection_name)
        if limit:
            ref = ref.limit(limit)
        docs = ref.stream()
        return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

    def get_document(self, collection_name, doc_id):
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return {**doc.to_dict(), 'id': doc.id}
        return None

    def create_document(self, collection_name, data, doc_id=None):
        if doc_id:
            self.db.collection(collection_name).document(doc_id).set(data)
            return doc_id
        else:
            update_time, doc_ref = self.db.collection(collection_name).add(data)
            return doc_ref.id

    def update_document(self, collection_name, doc_id, data):
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.update(data)

    def delete_document(self, collection_name, doc_id):
        self.db.collection(collection_name).document(doc_id).delete()

    # Specific Helpers
    def get_personalities(self):
        return self.get_collection('personalities')

    def get_cards(self):
        return self.get_collection('credit_cards')
    
    def get_card_by_slug(self, slug):
        # Assuming doc ID is the slug
        return self.get_document('credit_cards', slug)

    def get_personality_by_slug(self, slug):
        return self.get_document('personalities', slug)

    # User Methods
    def get_user_profile(self, uid):
        return self.get_document('users', uid)

    def create_user_profile(self, uid, data):
        return self.create_document('users', data, doc_id=uid)

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
        
        user_ref.collection('user_cards').add(user_card_data)
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
        self.db.collection('users').document(uid).collection('user_cards').document(user_card_id).delete()

    def update_card_details(self, uid, user_card_id, data):
        # Generic update for user card (e.g. anniversary date)
        ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        ref.update(data)

    def update_benefit_usage(self, uid, user_card_id, benefit_name, usage_amount):
        card_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        card_ref.update({
            f'benefit_usage.{benefit_name}.used': usage_amount,
            f'benefit_usage.{benefit_name}.last_updated': firestore.SERVER_TIMESTAMP
        })

    # Super Staff Methods
    def is_super_staff(self, uid):
        user = self.get_user_profile(uid)
        return user.get('is_super_staff', False) if user else False

    def set_super_staff(self, uid, is_staff):
        self.db.collection('users').document(uid).update({'is_super_staff': is_staff})

    # Editor Methods
    def is_editor(self, uid):
        user = self.get_user_profile(uid)
        return user.get('is_editor', False) if user else False

    def set_editor(self, uid, is_editor):
        self.db.collection('users').document(uid).update({'is_editor': is_editor})

    def can_manage_blogs(self, uid):
        """Check if user can manage blogs (either super_staff or editor)"""
        user = self.get_user_profile(uid)
        if not user:
            return False
        return user.get('is_super_staff', False) or user.get('is_editor', False)

    # Blog Methods
    def get_blogs(self, status=None, limit=None):
        """Get blogs, optionally filtered by status"""
        from google.cloud.firestore import FieldFilter
        query = self.db.collection('blogs')
        if status:
            query = query.where(filter=FieldFilter('status', '==', status))
        query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
        if limit:
            query = query.limit(limit)
        return [doc.to_dict() | {'id': doc.id} for doc in query.stream()]

    def get_blog_by_id(self, blog_id):
        return self.get_document('blogs', blog_id)

    def get_blog_by_slug(self, slug):
        """Get blog by slug field"""
        from google.cloud.firestore import FieldFilter
        query = self.db.collection('blogs').where(filter=FieldFilter('slug', '==', slug)).limit(1)
        docs = list(query.stream())
        if docs:
            return docs[0].to_dict() | {'id': docs[0].id}
        return None

    def create_blog(self, data):
        """Create a new blog post"""
        return self.create_document('blogs', data)

    def update_blog(self, blog_id, data):
        """Update an existing blog post"""
        self.update_document('blogs', blog_id, data)

    def delete_blog(self, blog_id):
        """Delete a blog post"""
        self.delete_document('blogs', blog_id)

db = FirestoreService()
