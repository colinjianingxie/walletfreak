import json
import os
import threading
from django.conf import settings
from core.services import db
from core.card_pipeline.grok_client import GrokClient
from .prompts import STRATEGY_ANALYSIS_PROMPT_TEMPLATE

class StrategyAnalysisService:
    def __init__(self):
        pass

    def call_grok_analysis(self, prompt):
        """
        Calls Grok API with web search enabled to analyze hotel strategies.
        Uses the REST-based GrokClient for reliability.
        """
        api_key = os.environ.get('GROK_API_KEY')
        if not api_key:
            print("GROK_API_KEY not found.")
            return None

        try:
            client = GrokClient(api_key=api_key)
            result = client.call_with_usage(prompt)

            if result.data:
                print(f"Grok analysis cost: ${result.usage.total_cost:.4f}")
                return result.data.get('analysis_results', [])

            print("Grok returned no data for strategy analysis")
            return None

        except Exception as e:
            print(f"Grok API Error: {e}")
            return None

    def run_analysis_in_background(self, prompt_text, user_id, strat_id):
        """Background worker function."""
        print(f"Starting background analysis for strategy {strat_id}...")
        try:
            results = self.call_grok_analysis(prompt_text)

            if not results:
                print(f"Analysis failed for {strat_id}")
                self._update_strategy_status(user_id, strat_id, 'failed')
                return

            strategies_ref = db.db.collection('users').document(user_id).collection('hotel_strategies').document(strat_id)
            strategies_ref.update({
                'status': 'ready',
                'analysis_results': results,
                'hotel_count': len(results)
            })
            print(f"Updated strategy {strat_id} with results.")
        except Exception as e:
            print(f"Background analysis error for {strat_id}: {e}")
            self._update_strategy_status(user_id, strat_id, 'failed')

    def _update_strategy_status(self, user_id, strat_id, status):
        """Helper to update strategy status in Firestore."""
        try:
            strategies_ref = db.db.collection('users').document(user_id).collection('hotel_strategies').document(strat_id)
            update_data = {'status': status}
            if status == 'failed':
                update_data['analysis_results'] = []
            strategies_ref.update(update_data)
        except Exception as e:
            print(f"Failed to update strategy {strat_id} to {status}: {e}")

    def prepare_prompt(self, check_in, check_out, guests, user_cards, wallet_balances, transfer_rules, selected_hotels, valuations):
        """
        Constructs the prompt for the AI.
        """
        # Minify user cards
        user_cards_minified = []
        for c in user_cards:
            rates = []
            for r in c.get('earning_rates', []):
                rates.append(f"{r.get('multiplier')}x on {', '.join(r.get('category', []))}")
            
            user_cards_minified.append({
                'name': c.get('name'),
                'slug_id': c.get('slug-id'),
                'bank': c.get('issuer'),
                'earning_rates': rates,
                'is_travel_portal_eligible': 'Safire' in c.get('name') or 'Plat' in c.get('name') or 'Venture' in c.get('name') # heuristic
            })

        return STRATEGY_ANALYSIS_PROMPT_TEMPLATE.format(
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            user_cards_json=json.dumps(user_cards_minified, indent=2),
            loyalty_balances_json=json.dumps(wallet_balances, indent=2),
            transfer_rules_json=json.dumps(transfer_rules, indent=2),
            selected_hotels_json=json.dumps(selected_hotels, indent=2),
            valuations_json=json.dumps(valuations, indent=2)
        )

    def initiate_strategy(self, uid, location, check_in, check_out, guests, selected_hotels_raw):
        """
        Main entry point to start a strategy analysis.
        Returns the strategy ID or raises Exception.
        """
        # 1. Fetch User Data
        user_cards = db.get_user_cards(uid, status='active', hydrate=True) if uid else []
        user_balances_raw = db.get_user_loyalty_balances(uid) if uid else []
        wallet_balances = {b['program_id']: int(b.get('balance', 0)) for b in user_balances_raw}
        
        # 2. Transfer Rules
        raw_rules = db.get_all_transfer_rules()
        transfer_rules = {}
        for r in raw_rules:
            sid = r.get('source_program_id')
            if sid:
                partners = []
                for p in r.get('transfer_partners', []):
                    partners.append({
                        'dest': p.get('destination_program_id'),
                        'ratio': p.get('ratio'),
                        'time': p.get('transfer_time', 'Instant')
                    })
                transfer_rules[sid] = partners
        
        # 3. Dynamic Valuations
        valuations = db.get_loyalty_valuations()

        # 4. Parse Selected Hotels (premium_programs already included from search)
        selected_hotels = []
        if selected_hotels_raw:
            for json_str in selected_hotels_raw:
                try:
                    hotel_dict = json.loads(json_str)
                    hotel_dict.pop('price', None)
                    selected_hotels.append(hotel_dict)
                except:
                    pass
        
        # 5. Prepare Prompt
        prompt = self.prepare_prompt(
            check_in, check_out, guests, 
            user_cards, wallet_balances, transfer_rules, selected_hotels, valuations
        )

        # 6. Save Initial Record
        strategy_record = {
            'location_text': location,
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests,
            'hotel_count': len(selected_hotels),
            'analysis_results': [],
            'status': 'processing',
            'prompt_used': prompt
        }
        strategy_id = db.save_hotel_strategy(uid, strategy_record)

        # 7. Launch Background Thread
        t = threading.Thread(target=self.run_analysis_in_background, args=(prompt, uid, strategy_id))
        t.daemon = True
        t.start()
        
        return strategy_id

    def run_anonymous_strategy(self, location, check_in, check_out, guests, selected_hotels_raw):
        """
        Runs strategy synchronously for non-logged-in users (Demo mode).
        In real prod you might want to disable this or limit it.
        """
        # We use empty user data for anonymous
        valuations = db.get_loyalty_valuations() # Still need global valuations
        
        selected_hotels = []
        if selected_hotels_raw:
            for json_str in selected_hotels_raw:
                try:
                    hotel_dict = json.loads(json_str)
                    hotel_dict.pop('price', None)
                    selected_hotels.append(hotel_dict)
                except: 
                    pass
        
        prompt = self.prepare_prompt(
            check_in, check_out, guests, 
            [], {}, {}, selected_hotels, valuations
        )
        
        return self.call_grok_analysis(prompt)
