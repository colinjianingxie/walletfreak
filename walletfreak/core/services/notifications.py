from firebase_admin import firestore

class NotificationMixin:
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

    def update_last_benefit_notification_time(self, uid):
        """Update user's last benefit email sent time"""
        self.db.collection('users').document(uid).update({
            'last_benefit_email_sent_at': firestore.SERVER_TIMESTAMP
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
            'from': 'walletfreak@gmail.com', 
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
