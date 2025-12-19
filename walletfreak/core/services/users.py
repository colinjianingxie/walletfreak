from firebase_admin import firestore

class UserMixin:
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

    def get_total_user_count(self):
        """Get total number of registered users"""
        try:
            # Using aggregation query for efficiency if available
            # Note: count() aggregation is available in newer google-cloud-firestore
            # Fallback to streaming stream() if count() not available in installed version
            try:
                from google.cloud.firestore import AggregateQuery
                users_ref = self.db.collection('users')
                count_query = users_ref.count()
                return count_query.get()[0][0].value
            except Exception:
                # Fallback slightly less efficient but works
                users_ref = self.db.collection('users')
                return len(list(users_ref.stream()))
        except Exception as e:
            print(f"Error getting total user count: {e}")
            return 0

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

    def generate_unique_username(self, first_name, last_name, uid):
        """
        Generate a unique username based on first and last name.
        Format: <firstname><lastname><4 digit number>
        """
        import random
        # Sanitize inputs
        first = ''.join(e for e in first_name if e.isalnum()).lower()
        last = ''.join(e for e in last_name if e.isalnum()).lower()
        
        base_name = f"{first}{last}"
        if not base_name:
            base_name = "user"
            
        # Try up to 20 times to find a unique random suffix
        for _ in range(20):
            suffix = random.randint(1000, 9999)
            proposal = f"{base_name}{suffix}"
            
            if not self.is_username_taken(proposal, exclude_uid=uid):
                return proposal
                
        # Fallback: use base_name + part of uid if random fail
        # This is extremely unlikely but good safe guard
        proposal = f"{base_name}_{uid[:6]}"
        return proposal

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
