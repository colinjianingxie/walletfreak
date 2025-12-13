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

    def _enrich_with_author_data(self, data, user):
        """Helper to inject standardized author data into a dict."""
        if user:
            data['author_username'] = user.get('username') or 'Unknown'
            # Construct real name
            real_name = user.get('name')
            if not real_name:
                first = user.get('first_name', '').strip()
                last = user.get('last_name', '').strip()
                real_name = f"{first} {last}".strip()
            
            # Fallback to username if real name is still empty
            if not real_name:
                real_name = user.get('username', 'Unknown')
                
            data['author_real_name'] = real_name
            
            # Support legacy 'author_name' using the best available name
            data['author_name'] = data['author_real_name']
            
            data['author_avatar'] = user.get('photo_url')
        else:
            # User lookup failed (or no user)
            # Try to preserve legacy author_name if available
            legacy_name = data.get('author_name', 'Unknown')
            
            # Use legacy name as username fallback (removing spaces to make it handle-like)
            data['author_username'] = legacy_name.replace(' ', '') if legacy_name != 'Unknown' else 'Unknown'
            data['author_real_name'] = legacy_name
            
            # Don't overwrite author_name with 'Unknown' if we have a value
            if 'author_name' not in data:
                data['author_name'] = 'Unknown'
                
            data['author_avatar'] = None
        return data

    def get_blog_by_slug(self, slug):
        """Get blog post by slug with dynamic author info"""
        blogs = self.db.collection('blogs').where('slug', '==', slug).limit(1).stream()
        for blog in blogs:
            data = blog.to_dict() | {'id': blog.id}
            # Fetch author info
            uid = data.get('author_uid')
            if uid:
                user = self.get_user_profile(uid)
                self._enrich_with_author_data(data, user)
            else:
                self._enrich_with_author_data(data, None)
            return data
        return None
    
    def get_blog_by_id(self, blog_id):
        """Get blog post by document ID with dynamic author info"""
        doc = self.db.collection('blogs').document(blog_id).get()
        if doc.exists:
            data = doc.to_dict() | {'id': doc.id}
            # Fetch author info
            # Fetch author info
            if data.get('author_uid'):
                 user = self.get_user_profile(data['author_uid'])
                 self._enrich_with_author_data(data, user)
            else:
                 self._enrich_with_author_data(data, None)
            return data
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
        
    def update_user_email(self, uid, email):
        """Update user email in Firestore"""
        self.db.collection('users').document(uid).update({'email': email})

    def get_users_by_ids(self, uids):
        """Get multiple user profiles by IDs"""
        if not uids:
            return {}
            
        try:
            # Firestore 'in' query is limited to 30 items
            # We need to chunk the requests
            unique_uids = list(set(uids))
            users_map = {}
            # Chunk into groups of 30
            chunk_size = 30
            for i in range(0, len(unique_uids), chunk_size):
                chunk = unique_uids[i:i + chunk_size]
                if not chunk:
                    continue
                    
                # Use '__name__' sentinel for document ID filtering
                # Note: For 'in' queries with document IDs, we might need to use references or just try __name__
                # But '__name__' usually expects full paths (collection/id).
                # A safer way with the python client is often just FieldPath.document_id() but imports are failing.
                # Let's try importing FieldPath from google.cloud.firestore_v1
                try:
                    from google.cloud.firestore_v1.field_path import FieldPath
                    query = self.db.collection('users').where(FieldPath.document_id(), 'in', chunk)
                except ImportError:
                    # Fallback to string literal if import fails (though __name__ might behave differently depending on client version)
                    query = self.db.collection('users').where('__name__', 'in', chunk)
                    
                docs = query.stream()
                
                for doc in docs:
                    users_map[doc.id] = doc.to_dict()
                    
            return users_map
        except Exception as e:
            print(f"Error getting users by IDs: {e}")
            return {}

    def is_username_taken(self, username, exclude_uid=None):
        """Check if a username is already taken by another user"""
        try:
            # Case insensitive check would be better but requires specific index or storing lowercase
            # For MVP we will assume exact match or rely on client sending lowercase/standardized
            # Ideally we store a 'username_lower' field.
            
            # Simple query on 'username' field
            users_ref = self.db.collection('users')
            query = users_ref.where('username', '==', username).limit(1)
            docs = list(query.stream())
            
            if not docs:
                return False
                
            # If we found a doc, check if it's the same user (in case they are saving same name)
            if exclude_uid and docs[0].id == exclude_uid:
                return False
                
            return True
        except Exception as e:
            print(f"Error checking username availability: {e}")
            return True # Fail safe

    def update_user_username(self, uid, username):
        """Update user username in Firestore"""
        # 0. Check uniqueness again (race condition minimal but possible)
        if self.is_username_taken(username, exclude_uid=uid):
             raise ValueError("Username is already taken")

        # 1. Update user profile
        self.db.collection('users').document(uid).set({'username': username}, merge=True)
        

    def update_user_avatar(self, uid, photo_url):
        """Update user avatar in Firestore"""
        self.db.collection('users').document(uid).update({'photo_url': photo_url})

    def determine_best_fit_personality(self, user_cards):
        """
        Determines the best personality fit based on user's active cards.
        user_cards: list of card objects (dicts containing at least 'card_id')
        """
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


    def get_user_notification_preferences(self, uid):
        """Get user notification preferences"""
        user = self.get_user_profile(uid)
        default_prefs = {
            'benefit_expiration': {
                'enabled': True,
                'start_days_before': 7,
                'repeat_frequency': 1 
            },
            'annual_fee': {
                'enabled': True,
                'start_days_before': 30,
                'repeat_frequency': 7
            },
            'blog_updates': {
                'enabled': False
            }
        }
        
        if user and 'notification_preferences' in user:
            user_prefs = user['notification_preferences']
            # Handle case where user_prefs itself might be None or not a dict
            if not isinstance(user_prefs, dict):
                 return default_prefs

            # Deep merge with defaults to ensure structure
            for key, default_val in default_prefs.items():
                if key not in user_prefs or user_prefs[key] is None:
                    user_prefs[key] = default_val
                elif isinstance(default_val, dict):
                    # Ensure it is a dict
                    if not isinstance(user_prefs[key], dict):
                        user_prefs[key] = default_val
                    else:
                        # Ensure all subkeys exist
                        for subkey, subval in default_val.items():
                            if subkey not in user_prefs[key]:
                                user_prefs[key][subkey] = subval
            
            return user_prefs
            
        return default_prefs

    def update_user_notification_preferences(self, uid, preferences):
        """Update user notification preferences"""
        self.db.collection('users').document(uid).update({
            'notification_preferences': preferences
        })

    def send_email_notification(self, to, subject, html_content=None, text_content=None, bcc=None):
        """
        Send an email via the Firebase Trigger Email Extension by writing to the 'mail' collection.
        Supports single 'to' address and optional list of 'bcc' addresses.
        """
        if not to and not bcc:
            return None
            
        email_data = {
            'to': to if to else [], # Extension might require 'to', often UIDs or emails. If using BCC only, 'to' can be admin or empty list if allowed.
            'from': 'notifications@walletfreak.com', 
            'message': {
                'subject': subject,
            }
        }
        
        # Ensure 'to' is a list if it's a single string, or handle as extension expects (usually supports string or list)
        # For BCC, we pass it in the message object or top level depending on extension version.
        # Standard Firebase Trigger Email extension usually looks at top level 'to', 'cc', 'bcc'.
        if bcc:
            email_data['bcc'] = bcc
        
        if html_content:
             email_data['message']['html'] = html_content
        
        if text_content:
             email_data['message']['text'] = text_content
             
        # Add to 'mail' collection
        try:
            _, doc_ref = self.db.collection('mail').add(email_data)
            return doc_ref.id
        except Exception as e:
            print(f"Error queuing email to Firestore: {e}")
            return None

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
        """Get blogs, optionally filtered by status, with dynamic author info"""
        from google.cloud.firestore import FieldFilter
        query = self.db.collection('blogs')
        if status:
            query = query.where(filter=FieldFilter('status', '==', status))
        query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
        if limit:
            query = query.limit(limit)
            
        blogs = [doc.to_dict() | {'id': doc.id} for doc in query.stream()]
        
        # Batch fetch authors
        author_uids = list(set(b.get('author_uid') for b in blogs if b.get('author_uid')))
        if author_uids:
            users_map = self.get_users_by_ids(author_uids)
            for blog in blogs:
                uid = blog.get('author_uid')
                if uid and uid in users_map:
                    user = users_map[uid]
                    self._enrich_with_author_data(blog, user)
                else:
                    self._enrich_with_author_data(blog, None)
                    
        return blogs



    def create_blog(self, data):
        """Create a new blog post"""
        # Ensure we have a doc ID (slug) if possible, but create_document handles it if passed as ID or data
        # data usually contains 'slug'
        doc_id = data.get('slug')
        
        # Trigger notification if published immediately
        if data.get('status') == 'published':
             # We need to ensure we don't block the request. 
             # In production, use a task queue. 
             # Here, we can use threading similar to the signal, or just let it be sync if acceptable (might slow down publish).
             # Let's use threading to be safe.
             import threading
             threading.Thread(target=self._trigger_blog_notification, args=(data,)).start()

        return self.create_document('blogs', data, doc_id=doc_id)

    def update_blog(self, blog_id, data):
        """Update an existing blog post"""
        # Check if we are publishing
        # We rely on the caller to set 'published_at' or we can check status transition if we fetched validation.
        # But 'data' here is the *update* dict.
        # If 'status' is 'published' in the update dict, we should check if we should notify.
        # To avoid duplicate emails on every edit of a published post, we should check if 'published_at' is in data (meaning it just got set)
        # OR if we want to be robust, fetch the current doc.
        
        should_notify = False
        if data.get('status') == 'published':
            # Option A: Check if 'published_at' is in update data (implies new publish logic from views)
            if 'published_at' in data:
                should_notify = True
            else:
                 # Option B: Fetch current to be sure? 
                 # If user manually edits a published post but doesn't change published_at, we don't want to re-notify.
                 pass
        
        if should_notify:
             # We need full blog data for the email (title, excerpt, slug)
             # 'data' might be partial. Merge with existing or fetch after update?
             # Let's fetch the full updated doc *after* the update to be sure we have everything.
             # Actually, we can just pass 'data' if it has title/slug, but safe to fetch.
             import threading
             def notify_after_update():
                 # Small delay or just fetch (consistency might be eventually consistent but usually fine)
                 full_blog = self.get_blog_by_id(blog_id)
                 if full_blog:
                     self._trigger_blog_notification(full_blog)
             
             threading.Thread(target=notify_after_update).start()

        self.update_document('blogs', blog_id, data)

    def delete_blog(self, blog_id):
        """Delete a blog post"""
        self.delete_document('blogs', blog_id)
        
    def _trigger_blog_notification(self, blog_data):
        """
        Internal helper to send blog notifications via BCC.
        """
        print(f"Starting blog notification for: {blog_data.get('title')}")
        
        try:
            # 1. Fetch all users who have blog_updates enabled
            users_ref = self.db.collection('users')
            # Filter in memory for MVP
            users = users_ref.stream()
            
            emails_to_send = []
            
            for user_doc in users:
                user_data = user_doc.to_dict()
                prefs = user_data.get('notification_preferences', {})
                email = user_data.get('email')
                
                # Check preference (robustly)
                blog_updates = prefs.get('blog_updates')
                if blog_updates and isinstance(blog_updates, dict) and blog_updates.get('enabled'):
                    if email:
                        emails_to_send.append(email)
            
            if not emails_to_send:
                print("No subscribers found.")
                return

            print(f"Found {len(emails_to_send)} subscribers.")
            
            title = blog_data.get('title', 'New Post')
            slug = blog_data.get('slug', '')
            excerpt = blog_data.get('excerpt', '')
            
            subject = f"New on WalletFreak: {title}"
            message = f"""
Hi there!

We just published a new article on WalletFreak:

{title}
{excerpt}

Read more here: https://walletfreak.com/blog/{slug}

Cheers,
The WalletFreak Team
            """
            
            html_message = message.replace('\n', '<br>')
            
            # Send one email with BCC
            try:
                self.send_email_notification(
                    to="notifications@walletfreak.com",
                    bcc=emails_to_send,
                    subject=subject,
                    text_content=message,
                    html_content=html_message
                )
                print(f"Sent blog notification to {len(emails_to_send)} subscribers via BCC.")
            except Exception as e:
                print(f"Failed to queue blog notification email: {e}")
                
        except Exception as e:
            print(f"Error in blog notification thread: {e}")

    def increment_blog_view_count(self, blog_id):
        """Increment the view count for a blog post"""
        try:
            doc_ref = self.db.collection('blogs').document(blog_id)
            doc_ref.update({'view_count': firestore.Increment(1)})
            return True
        except Exception as e:
            print(f"Error incrementing view count: {e}")
            return False

    # Comment Methods
    def get_blog_comments(self, blog_id):
        """Get all comments for a blog post, ordered by date"""
        try:
            comments_ref = self.db.collection('blogs').document(blog_id).collection('comments')
            query = comments_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
            comments = [doc.to_dict() | {'id': doc.id} for doc in query.stream()]
            
            # Collect author UIDs using a set to handle duplicates
            author_uids = []
            for c in comments:
                if c.get('author_uid'):
                    author_uids.append(c.get('author_uid'))
            
            if not author_uids:
                return comments
                
            # Fetch user profiles
            users_map = self.get_users_by_ids(author_uids)
            
            # Map user data to comments
            for c in comments:
                uid = c.get('author_uid')
                if uid and uid in users_map:
                    user = users_map[uid]
                    # Dynamic author data
                    self._enrich_with_author_data(c, user)
                    # Backward compat for templates expecting 'author_name'
                    c['author_name'] = c['author_real_name']
                else:
                    self._enrich_with_author_data(c, None)
                    c['author_name'] = 'Anonymous'
            
            return comments
        except Exception as e:
            print(f"Error getting blog comments: {e}")
            return []

    def add_blog_comment(self, blog_id, user_uid, content, parent_id=None):
        """Add a comment to a blog post"""
        try:
            comment_data = {
                'content': content,
                'author_uid': user_uid,
                # 'author_name': author_name, # Removed storage of static author data
                # 'author_avatar': author_avatar, # Removed storage of static author data
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'parent_id': parent_id,
                'upvote_count': 0,
                'downvote_count': 0
            }
            
            comments_ref = self.db.collection('blogs').document(blog_id).collection('comments')
            _, doc_ref = comments_ref.add(comment_data)
            
            # Increment comment count on blog
            self.db.collection('blogs').document(blog_id).update({
                'comment_count': firestore.Increment(1)
            })
            
            return {**comment_data, 'id': doc_ref.id}
        except Exception as e:
            print(f"Error adding blog comment: {e}")
            return None

    def delete_blog_comment(self, blog_id, comment_id):
        """Delete a comment"""
        try:
            self.db.collection('blogs').document(blog_id).collection('comments').document(comment_id).delete()
            
            # Decrement comment count on blog
            self.db.collection('blogs').document(blog_id).update({
                'comment_count': firestore.Increment(-1)
            })
            
            return True
        except Exception as e:
            print(f"Error deleting blog comment: {e}")
            return False

    def vote_comment(self, blog_id, comment_id, user_uid, vote_type):
        """Vote on a comment (upvote/downvote)"""
        if vote_type not in ['upvote', 'downvote']:
            return False
            
        try:
            # simple implementation: store votes in a subcollection of the comment
            comment_ref = self.db.collection('blogs').document(blog_id).collection('comments').document(comment_id)
            vote_ref = comment_ref.collection('votes').document(user_uid)
            
            doc = vote_ref.get()
            old_vote = doc.to_dict().get('type') if doc.exists else None
            
            if old_vote == vote_type:
                # Toggle off (remove vote)
                vote_ref.delete()
                # Decrement count
                if vote_type == 'upvote':
                    comment_ref.update({'upvote_count': firestore.Increment(-1)})
                else:
                    comment_ref.update({'downvote_count': firestore.Increment(-1)})
                return 'removed'
            else:
                # Set new vote
                vote_ref.set({
                    'type': vote_type,
                    'timestamp': firestore.SERVER_TIMESTAMP
                })
                
                # Update counts
                if old_vote:
                    # Switch vote
                    if vote_type == 'upvote':
                        comment_ref.update({
                            'upvote_count': firestore.Increment(1),
                            'downvote_count': firestore.Increment(-1)
                        })
                    else:
                        comment_ref.update({
                            'upvote_count': firestore.Increment(-1),
                            'downvote_count': firestore.Increment(1)
                        })
                else:
                    # New vote
                    if vote_type == 'upvote':
                        comment_ref.update({'upvote_count': firestore.Increment(1)})
                    else:
                        comment_ref.update({'downvote_count': firestore.Increment(1)})
                return 'voted'
                
        except Exception as e:
            print(f"Error voting on comment: {e}")
            return False

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

    # User Saved Posts Methods
    def save_post_for_user(self, uid, blog_id):
        """Save a blog post for a user"""
        try:
            # Add to user's saved_posts subcollection
            user_ref = self.db.collection('users').document(uid)
            saved_posts_ref = user_ref.collection('saved_posts')
            
            # Check if already saved
            existing = saved_posts_ref.document(blog_id).get()
            if existing.exists:
                return True  # Already saved
            
            # Save the post reference
            saved_posts_ref.document(blog_id).set({
                'blog_id': blog_id,
                'saved_at': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error saving post for user: {e}")
            return False

    def unsave_post_for_user(self, uid, blog_id):
        """Remove a saved blog post for a user"""
        try:
            # Remove from user's saved_posts subcollection
            user_ref = self.db.collection('users').document(uid)
            saved_posts_ref = user_ref.collection('saved_posts')
            saved_posts_ref.document(blog_id).delete()
            return True
        except Exception as e:
            print(f"Error unsaving post for user: {e}")
            return False

    def get_user_saved_post_ids(self, uid):
        """Get list of blog post IDs that user has saved"""
        try:
            user_ref = self.db.collection('users').document(uid)
            saved_posts_ref = user_ref.collection('saved_posts')
            saved_docs = saved_posts_ref.stream()
            return [doc.id for doc in saved_docs]
        except Exception as e:
            print(f"Error getting user saved post IDs: {e}")
            return []

    def get_user_saved_posts(self, uid):
        """Get full blog post objects that user has saved"""
        try:
            # Get saved post IDs
            saved_post_ids = self.get_user_saved_post_ids(uid)
            if not saved_post_ids:
                return []
            
            # Get the actual blog posts
            saved_posts = []
            for blog_id in saved_post_ids:
                blog = self.get_blog_by_id(blog_id)
                if blog and blog.get('status') == 'published':  # Only include published posts
                    saved_posts.append(blog)
            
            # Sort by saved date (most recent first)
            # Since we don't have saved_at in the blog object, sort by published_at
            saved_posts.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            return saved_posts
        except Exception as e:
            print(f"Error getting user saved posts: {e}")
            return []

    # Blog Voting Methods
    def get_blog_vote_count(self, blog_id, vote_type):
        """Get the count of votes for a blog post by type"""
        try:
            votes_ref = self.db.collection('blog_votes')
            votes = votes_ref.where('blog_id', '==', blog_id).where('vote_type', '==', vote_type).stream()
            return len(list(votes))
        except Exception as e:
            print(f"Error getting blog vote count: {e}")
            return 0

    def get_user_vote_on_blog(self, uid, blog_id):
        """Get the user's vote on a specific blog post"""
        try:
            votes_ref = self.db.collection('blog_votes')
            votes = votes_ref.where('user_uid', '==', uid).where('blog_id', '==', blog_id).limit(1).stream()
            for vote in votes:
                return vote.to_dict().get('vote_type')
            return None
        except Exception as e:
            print(f"Error getting user vote on blog: {e}")
            return None

    def add_user_vote_on_blog(self, uid, blog_id, vote_type):
        """Add a user's vote on a blog post"""
        try:
            vote_data = {
                'user_uid': uid,
                'blog_id': blog_id,
                'vote_type': vote_type,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            self.db.collection('blog_votes').add(vote_data)
        
            # Increment updated count on blog
            if vote_type == 'upvote':
                self.db.collection('blogs').document(blog_id).update({
                    'upvote_count': firestore.Increment(1)
                })
            elif vote_type == 'downvote':
                 self.db.collection('blogs').document(blog_id).update({
                    'downvote_count': firestore.Increment(1)
                })
                
            return True
        except Exception as e:
            print(f"Error adding user vote on blog: {e}")
            return False

    def update_user_vote_on_blog(self, uid, blog_id, vote_type):
        """Update a user's existing vote on a blog post"""
        try:
            votes_ref = self.db.collection('blog_votes')
            votes = votes_ref.where('user_uid', '==', uid).where('blog_id', '==', blog_id).limit(1).stream()
            
            for vote in votes:
                vote.reference.update({
                    'vote_type': vote_type,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                return True
            return False
        except Exception as e:
            print(f"Error updating user vote on blog: {e}")
            return False

    def remove_user_vote_on_blog(self, uid, blog_id):
        """Remove a user's vote on a blog post"""
        try:
            votes_ref = self.db.collection('blog_votes')
            votes = votes_ref.where('user_uid', '==', uid).where('blog_id', '==', blog_id).limit(1).stream()
            
            for vote in votes:
                # Check type before deleting to decrement correct counter
                data = vote.to_dict()
                vote_type = data.get('vote_type')
                
                vote.reference.delete()
                
                # Decrement counter
                if vote_type == 'upvote':
                    self.db.collection('blogs').document(blog_id).update({
                        'upvote_count': firestore.Increment(-1)
                    })
                elif vote_type == 'downvote':
                    self.db.collection('blogs').document(blog_id).update({
                        'downvote_count': firestore.Increment(-1)
                    })
                    
                return True
            return False
        except Exception as e:
            print(f"Error removing user vote on blog: {e}")
            return False

# Create singleton instance
db = FirestoreService()
