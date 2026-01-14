from firebase_admin import firestore
from datetime import datetime, timedelta

class LoyaltyMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loyalty_programs_cache = None
        self._loyalty_programs_cache_time = None
        self._loyalty_programs_cache_ttl = timedelta(minutes=60) # Cache for 1 hour

    def get_all_loyalty_programs(self):
        """
        Fetch all loyalty programs from 'program_loyalty' collection.
        Cached for performance as this data changes rarely.
        """
        if self._loyalty_programs_cache and self._loyalty_programs_cache_time:
             if datetime.now() - self._loyalty_programs_cache_time < self._loyalty_programs_cache_ttl:
                 return self._loyalty_programs_cache
        
        try:
            programs_ref = self.db.collection('program_loyalty')
            docs = programs_ref.stream()
            programs = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                programs.append(data)
            
            # Sort by name
            programs.sort(key=lambda x: x.get('program_name', ''))
            
            self._loyalty_programs_cache = programs
            self._loyalty_programs_cache_time = datetime.now()
            return programs
        except Exception as e:
            print(f"Error fetching loyalty programs: {e}")
            return []

    def get_user_loyalty_balances(self, uid):
        """
        Fetch user's specific loyalty balances from subcollection.
        """
        try:
            balances_ref = self.db.collection('users').document(uid).collection('loyalty_balances')
            docs = balances_ref.stream()
            balances = []
            for doc in docs:
                data = doc.to_dict()
                data['program_id'] = doc.id
                balances.append(data)
            return balances
        except Exception as e:
            print(f"Error fetching user balances for {uid}: {e}")
            return []

    def update_user_loyalty_balance(self, uid, program_id, balance, notes=None):
        """
        Update or create a loyalty balance entry for a user.
        """
        try:
            doc_ref = self.db.collection('users').document(uid).collection('loyalty_balances').document(program_id)
            data = {
                'balance': float(balance) if balance is not None else 0,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            if notes is not None:
                data['notes'] = notes
                
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            print(f"Error updating loyalty balance for {uid}/{program_id}: {e}")
            return False

    def remove_user_loyalty_program(self, uid, program_id):
        """
        Remove a loyalty program from user's collection.
        """
        try:
            doc_ref = self.db.collection('users').document(uid).collection('loyalty_balances').document(program_id)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error removing loyalty program {program_id} for {uid}: {e}")
            return False
