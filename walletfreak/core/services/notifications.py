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
            'to': to if to else [], 
            'from': 'Wallet Freak <walletfreak@gmail.com>', 
            'message': {
                'subject': subject,
            }
        }
        
        # Centralized Yahoo Routing Logic
        # If any recipient is a Yahoo address, send to self and BCC the user to avoid DMARC/Spam issues
        # Standardize 'to' as list for checking
        to_list = [to] if isinstance(to, str) else (to or [])
        
        has_yahoo = any('yahoo.com' in str(t).lower() for t in to_list)
        
        if has_yahoo:
            print(f"     [INFO] Yahoo email detected in {to_list}. Rerouting to walletfreak@gmail.com with BCC.")
            # Set TO to system address
            email_data['to'] = ['walletfreak@gmail.com']
            
            # Add original TO recipients to BCC
            current_bcc = []
            if bcc:
                current_bcc = [bcc] if isinstance(bcc, str) else (bcc or [])
            
            # Combine existing BCC with original TOs
            final_bcc = list(set(current_bcc + to_list))
            email_data['bcc'] = final_bcc
        elif bcc:
             final_bcc = [bcc] if isinstance(bcc, str) else (bcc or [])
             email_data['bcc'] = final_bcc
        else:
             final_bcc = []

        # Assign content before batching so it is copied to all batches
        if html_content:
             email_data['message']['html'] = html_content
        
        if text_content:
             email_data['message']['text'] = text_content

        # BATCHING LOGIC
        # Firestore/SMTP often has limits (e.g. 500 recipients). User requested 250.
        try:
            BATCH_SIZE = 250
            if len(final_bcc) > BATCH_SIZE:
                print(f"     [INFO] Large BCC list ({len(final_bcc)}). Splitting into batches of {BATCH_SIZE}.")
                
                doc_ids = []
                # Chunk the BCC list
                for i in range(0, len(final_bcc), BATCH_SIZE):
                    chunk = final_bcc[i:i + BATCH_SIZE]
                    
                    # Create a copy of the base email data (which now includes content)
                    batch_data = email_data.copy()
                    batch_data['bcc'] = chunk
                    
                    _, doc_ref = self.db.collection('mail').add(batch_data)
                    doc_ids.append(doc_ref.id)
                    print(f"     [INFO] Sent batch {i//BATCH_SIZE + 1} with {len(chunk)} BCC recipients.")
                
                return doc_ids # Return list of IDs (truthy)
            else:
                # Normal single send
                email_data['bcc'] = final_bcc
                     
                _, doc_ref = self.db.collection('mail').add(email_data)
                return doc_ref.id

        except Exception as e:
            print(f"Error queuing email to Firestore: {e}")
            return None
