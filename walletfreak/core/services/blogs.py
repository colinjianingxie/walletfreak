from firebase_admin import firestore
import uuid
from datetime import datetime
import threading

class BlogMixin:
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
            if data.get('author_uid'):
                 user = self.get_user_profile(data['author_uid'])
                 self._enrich_with_author_data(data, user)
            else:
                 self._enrich_with_author_data(data, None)
            return data
        return None

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
        """Soft delete a comment"""
        try:
            self.db.collection('blogs').document(blog_id).collection('comments').document(comment_id).update({
                'is_deleted': True,
                'content': '<deleted>',
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            # NOTE: We do NOT decrement the comment count, as the comment placeholder remains.
            
            return True
        except Exception as e:
            print(f"Error soft-deleting blog comment: {e}")
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
            if vote_type == 'upvote':
                blog = self.get_blog_by_id(blog_id)
                # Just return the count
                return blog.get('upvote_count', 0)
            return 0
        except Exception as e:
            print(f"Error getting blog vote count: {e}")
            return 0

    def get_user_vote_on_blog(self, uid, blog_id):
        """Get the user's vote on a specific blog post"""
        try:
            blog = self.get_blog_by_id(blog_id)
            if not blog:
                return None
            # We no longer track individual user votes in the backend
            return None
        except Exception as e:
            print(f"Error getting user vote on blog: {e}")
            return None

    def add_user_vote_on_blog(self, uid, blog_id, vote_type):
        """Add a user's vote on a blog post"""
        try:
            if vote_type != 'upvote':
                return False
                
            self.db.collection('blogs').document(blog_id).update({
                'upvote_count': firestore.Increment(1)
            })
            return True
        except Exception as e:
            print(f"Error adding user vote on blog: {e}")
            return False

    def update_user_vote_on_blog(self, uid, blog_id, vote_type):
        """Update a user's existing vote on a blog post"""
        # With simple upvotes, update is just adding if not present, but usually this isn't called for clear toggles
        # logic handled in view mostly.
        return self.add_user_vote_on_blog(uid, blog_id, vote_type)

    def remove_user_vote_on_blog(self, uid, blog_id):
        """Remove a user's vote on a blog post"""
        try:
            self.db.collection('blogs').document(blog_id).update({
                'upvote_count': firestore.Increment(-1)
            })
            return True
        except Exception as e:
            print(f"Error removing user vote on blog: {e}")
            return False
