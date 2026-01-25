from django.core.cache import cache
from firebase_admin import firestore
from datetime import datetime, timedelta

class LoyaltyMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Removed instance cache attributes
    
    def get_all_loyalty_programs(self):
        """
        Fetch all loyalty programs from 'program_loyalty' collection.
        Cached for performance as this data changes rarely.
        """
        cached = cache.get('all_loyalty_programs')
        if cached:
            return cached
        
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
            
            cache.set('all_loyalty_programs', programs, timeout=86400)
            return programs
        except Exception as e:
            print(f"Error fetching loyalty programs: {e}")
            return []

    def get_loyalty_valuations(self):
        """
        Returns a dictionary of program_id -> valuation (float).
        """
        cached = cache.get('loyalty_valuations')
        if cached:
            return cached

        programs = self.get_all_loyalty_programs()
        valuations = {}
        for p in programs:
            pid = p.get('program_id') or p.get('id')
            val = p.get('valuation')
            if pid:
                try:
                    valuations[pid] = float(val) if val is not None else 0.0
                except (ValueError, TypeError):
                    valuations[pid] = 0.0
        
        cache.set('loyalty_valuations', valuations, timeout=3600)
        return valuations

    def get_all_transfer_rules(self):
        """
        Fetch all transfer rules.
        Schema: Each document is a source program with a list of partners inside.
        """
        cached = cache.get('all_transfer_rules')
        if cached:
            return cached
            
        try:
            rules_ref = self.db.collection('transfer_rules')
            docs = rules_ref.stream()
            rules = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                rules.append(data)
                
            cache.set('all_transfer_rules', rules, timeout=86400)
            return rules
        except Exception as e:
            print(f"Error fetching transfer rules: {e}")
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
