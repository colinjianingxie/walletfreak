import firebase_admin
from firebase_admin import firestore, storage
from django.conf import settings
from datetime import timedelta
import uuid

class FirestoreService:
    def __init__(self):
        # Ensure app is initialized (it should be in settings.py)
        if not firebase_admin._apps:
             # This fallback is mostly for local testing if settings didn't catch it
             pass
        self._db = None
        self._bucket = None

    @property
    def db(self):
        if self._db is None:
            self._db = firestore.client()
        return self._db
    
    @property
    def bucket(self):
        if self._bucket is None:
            self._bucket = storage.bucket()
        return self._bucket

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

    def get_blog_by_slug(self, slug):
        """Get blog post by slug"""
        blogs = self.db.collection('blogs').where('slug', '==', slug).limit(1).stream()
        for blog in blogs:
            return blog.to_dict() | {'id': blog.id}
        return None
    
    def get_blog_by_id(self, blog_id):
        """Get blog post by document ID"""
        doc = self.db.collection('blogs').document(blog_id).get()
        if doc.exists:
            return doc.to_dict() | {'id': doc.id}
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

    def get_quiz_questions(self):
        """Get all quiz questions sorted by stage"""
        query = self.db.collection('quiz_questions').order_by('stage')
        return [doc.to_dict() | {'id': doc.id} for doc in query.stream()]


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

    def update_benefit_usage(self, uid, user_card_id, benefit_name, usage_amount, period_key=None, is_full=False):
        card_ref = self.db.collection('users').document(uid).collection('user_cards').document(user_card_id)
        
        update_data = {
            f'benefit_usage.{benefit_name}.last_updated': firestore.SERVER_TIMESTAMP
        }
        
        if period_key:
            # Update specific period
            update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.used'] = usage_amount
            update_data[f'benefit_usage.{benefit_name}.periods.{period_key}.is_full'] = is_full
            
            # Also update the main 'used' field for backward compatibility or summary
            # For now, let's just update it to match the current period if it's the latest
            # But simpler: just update the 'used' field to be the amount of the current operation
            # The view logic will handle aggregation if needed.
            # actually, let's keep 'used' as the "current active period usage"
            update_data[f'benefit_usage.{benefit_name}.used'] = usage_amount
        else:
            # Legacy/Simple update
            update_data[f'benefit_usage.{benefit_name}.used'] = usage_amount
            
        card_ref.update(update_data)

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

    # Personality Assignment Methods

    
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
        user = self.get_user_profile(uid)
        if not user or not user.get('assigned_personality'):
            return None
        
        personality_id = user.get('assigned_personality')
        personality = self.get_personality_by_slug(personality_id)
        
        if personality:
            # Add match score to personality object
            personality['match_score'] = user.get('personality_score', 0)
            personality['assigned_at'] = user.get('personality_assigned_at')
        
        return personality
    
    
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

    # Media Asset Management Methods
    def upload_media_asset(self, file_obj, filename, content_type, uploaded_by_uid):
        """Upload a media file to Google Cloud Storage and track it in Firestore"""
        import uuid
        from datetime import datetime
        from google.cloud.firestore import Query
        
        # Generate unique filename to avoid collisions
        file_extension = filename.rsplit('.', 1)[-1] if '.' in filename else ''
        unique_filename = f"blog-assets/{uuid.uuid4()}.{file_extension}"
        
        # Upload to Cloud Storage
        blob = self.bucket.blob(unique_filename)
        blob.upload_from_file(file_obj, content_type=content_type)
        
        # Make the file publicly accessible
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        
        # Track in Firestore
        asset_data = {
            'filename': filename,
            'storage_path': unique_filename,
            'url': public_url,
            'content_type': content_type,
            'uploaded_by': uploaded_by_uid,
            'uploaded_at': datetime.now(),
            'size': blob.size
        }
        
        doc_ref = self.db.collection('media_assets').document()
        doc_ref.set(asset_data)
        
        return {
            'id': doc_ref.id,
            'url': public_url,
            **asset_data
        }
    
    def list_media_assets(self, limit=50):
        """List all media assets from Firestore"""
        from google.cloud.firestore import Query
        assets_ref = self.db.collection('media_assets').order_by('uploaded_at', direction=Query.DESCENDING).limit(limit)
        return [doc.to_dict() | {'id': doc.id} for doc in assets_ref.stream()]
    
    def delete_media_asset(self, asset_id):
        """Delete a media asset from both Storage and Firestore"""
        # Get asset info from Firestore
        asset_doc = self.db.collection('media_assets').document(asset_id).get()
        if not asset_doc.exists:
            return False
        
        asset_data = asset_doc.to_dict()
        storage_path = asset_data.get('storage_path')
        
        # Delete from Cloud Storage
        if storage_path:
            blob = self.bucket.blob(storage_path)
            try:
                blob.delete()
            except Exception as e:
                print(f"Error deleting from storage: {e}")
        
        # Delete from Firestore
        self.db.collection('media_assets').document(asset_id).delete()
        return True
    
    def get_media_url(self, storage_path):
        """Get public URL for a media asset"""
        blob = self.bucket.blob(storage_path)
        return blob.public_url

# Create singleton instance
db = FirestoreService()
