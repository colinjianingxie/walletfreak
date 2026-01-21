from django.core.management.base import BaseCommand
from core.services import db
import datetime

class Command(BaseCommand):
    help = 'Checks for unused credits on user cards'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', type=str, help='Filter by specific User ID')
        parser.add_argument('--email', type=str, help='Filter by specific Email')
        parser.add_argument('--send-email', action='store_true', help='Send email to user with unused credits')

    def handle(self, *args, **options):
        self.stdout.write("Checking unused credits...")
        
        target_uid = options.get('user_id')
        target_email = options.get('email')
        should_send = options.get('send_email')

        # Container for our working data
        # Structure: { uid: { 'profile': user_dict, 'cards': [card_dicts] } }
        work_data = {}

        # 1. Fetch Data
        if target_uid or target_email:
            # --- TARGETED MODE (Existing Logic) ---
            users = []
            if target_uid:
                user = db.get_user_profile(target_uid)
                if user: users.append(user)
            elif target_email:
                # Still doing a scan for email if ID not provided, but it's rare operation
                all_users = db.db.collection('users').stream()
                for doc in all_users:
                    u = doc.to_dict() | {'id': doc.id}
                    if u.get('email') == target_email:
                        users.append(u)
                        break
            
            for user in users:
                uid = user['id']
                # Fetch active cards for this specific user
                raw_cards = db.get_user_cards(uid, status='active', hydrate=False) # Get lightweight first
                work_data[uid] = {
                    'profile': user,
                    'cards': raw_cards
                }
        else:
            # --- BULK MODE (Optimized) ---
            self.stdout.write("Running in BULK optimization mode...")
            
            # A. Collection Group Query for ALL active cards
            # Requires composite index on user_cards collection for 'status'
            from google.cloud.firestore import FieldFilter
            
            try:
                cards_query = db.db.collection_group('user_cards').where(filter=FieldFilter('status', '==', 'active'))
                active_card_docs = list(cards_query.stream())
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error executing Collection Group Query: {e}"))
                self.stdout.write(self.style.WARNING("Ensure a Composite Index exists for 'user_cards' collection on field 'status'."))
                return

            self.stdout.write(f"Found {len(active_card_docs)} active cards across system.")

            # B. Group by User and Collect Slugs to Hydrate
            all_slugs_to_hydrate = set()
            user_cards_map = {} # uid -> list of card data

            for doc in active_card_docs:
                # Path: users/{uid}/user_cards/{card_id}
                # parent is user_cards col, parent.parent is user doc
                uid = doc.reference.parent.parent.id
                data = doc.to_dict()
                card_id = doc.id 
                
                # Normalize data structure similar to get_user_cards(hydrate=False)
                card_entry = {**data, 'id': card_id, 'card_slug_id': card_id}
                
                if uid not in user_cards_map:
                    user_cards_map[uid] = []
                user_cards_map[uid].append(card_entry)
                
                all_slugs_to_hydrate.add(card_id)

            # C. Batch Fetch Users
            uids_to_fetch = list(user_cards_map.keys())
            users_map = {}
            
            # Fetch users in batches of 100
            for i in range(0, len(uids_to_fetch), 100):
                 batch_uids = uids_to_fetch[i:i + 100]
                 user_refs = [db.db.collection('users').document(uid) for uid in batch_uids]
                 user_snaps = db.db.get_all(user_refs)
                 for snap in user_snaps:
                     if snap.exists:
                         users_map[snap.id] = snap.to_dict() | {'id': snap.id}

            # Assemble Work Data
            for uid, cards in user_cards_map.items():
                if uid in users_map:
                    work_data[uid] = {
                        'profile': users_map[uid],
                        'cards': cards
                    }

            # D. Pre-Hydrate Master Cards Cache
            # This ensures subsequent get_specific_cards calls (or internal logic) hits cache
            if all_slugs_to_hydrate:
                self.stdout.write(f"Pre-hydrating {len(all_slugs_to_hydrate)} master cards...")
                db.get_specific_cards(list(all_slugs_to_hydrate))


        self.stdout.write(f"checking {len(work_data)} users with active cards.")
        
        # 2. Process Results
        
        # We need to manually hydrate the cards now using our efficient cache
        # Since we have the raw user card data, we need to merge it with master data
        # We can use db.get_specific_cards logic but efficiently
        
        # Gather all unique slugs again from the final work_set (redundant but safe)
        unique_slugs_in_batch = set()
        for data in work_data.values():
            for c in data['cards']:
                unique_slugs_in_batch.add(c['card_slug_id'])
        
        # Fetch all needed master data (should be cached now from step D)
        master_cards = db.get_specific_cards(list(unique_slugs_in_batch))
        master_map = {c['id']: c for c in master_cards}


        for uid, data in work_data.items():
            user = data['profile']
            raw_cards = data['cards']
            
            username = user.get('username', 'Unknown')
            first_name = user.get('first_name', '').strip()
            last_name = user.get('last_name', '').strip()
            user_email = user.get('email')
            
            # Hydrate cards manually
            user_cards = []
            for rc in raw_cards:
                 cid = rc['card_slug_id']
                 master = master_map.get(cid)
                 if master:
                     composite = master.copy()
                     composite.update({
                        'user_card_id': rc.get('id'), # doc id
                        'status': rc.get('status'),
                        'added_at': rc.get('added_at'),
                        'anniversary_date': rc.get('anniversary_date'),
                        'benefit_usage': rc.get('benefit_usage', {}),
                        'id': cid, # keep master id as main id
                        'card_id': cid,
                        'card_slug_id': cid
                     })
                     user_cards.append(composite)
                 # If master not found, skip or log (we skip to avoid errors)

            if not user_cards:
                continue

            self.stdout.write(f"\nUser: {username} ({uid})")
            
            user_unused_items = []
            
            for u_card in user_cards:
                card_slug = u_card.get('card_id')
                card_name = u_card.get('name')

                for idx, benefit in enumerate(u_card.get('benefits', [])):
                    # We are looking for monetary credits
                    # Usually indicated by 'dollar_value' > 0 and benefit_type='Credit' or 'Perk'
                    if benefit.get('benefit_type') not in ['Credit', 'Perk']:
                        continue

                    dollar_val = benefit.get('dollar_value')
                    
                    if dollar_val and dollar_val > 0:
                        credits_found = True
                        desc = benefit.get('short_description') or benefit.get('description')
                        time_cat = benefit.get('time_category', 'Annually')
                        
                        # Determine period key
                        # This logic mirrors parse_benefits_csv or usage logic
                        param_ann_date = u_card.get('anniversary_date')
                        period_key = self._get_current_period_key(time_cat, param_ann_date)
                        
                        # Check usage
                        usage_data = u_card.get('benefit_usage', {})
                        # KEY FIX: Use benefit['id'] (stable) instead of index
                        usage_key = benefit.get('id')
                        if not usage_key:
                            usage_key = str(idx) # Fallback
                        
                        b_usage = usage_data.get(usage_key, {})
                        
                        # Check if ignored
                        if b_usage.get('is_ignored', False):
                            continue
                        
                        used_amount = 0
                        is_full = False
                        
                        # Calculate Limit (Per-Period)
                        limit = dollar_val
                        period_values = benefit.get('period_values', {})
                        
                        if period_key:
                            # Use period specific limit if defined, else fallback
                            # e.g. Monthly -> /12, but period_values might have exact overrides
                            if period_key in period_values:
                                limit = period_values[period_key]
                            elif 'Monthly' in time_cat:
                                limit = dollar_val / 12
                            elif 'Quarterly' in time_cat:
                                limit = dollar_val / 4
                            elif 'Semi-annually' in time_cat:
                                limit = dollar_val / 2
                                
                            # If structured with periods
                            if 'periods' in b_usage:
                                p_data = b_usage['periods'].get(period_key, {})
                                used_amount = p_data.get('used', 0)
                                is_full = p_data.get('is_full', False)
                            else:
                                # Fallback or flat usage (unlikely if period_key is set correctly but safety net)
                                used_amount = b_usage.get('used', 0)
                                is_full = b_usage.get('is_full', False)
                        else:
                            used_amount = b_usage.get('used', 0)
                            is_full = b_usage.get('is_full', False)
                            
                        # If marked as full, assume fully used regardless of amount
                        unused = 0 if is_full else (limit - used_amount)
                        
                        # Fix: Include ALL benefits for the current period, regardless of usage
                        # But ensure we only show if there is a valid limit (i.e., it's a credit benefit)
                        # AND if there is unused value remaining (user requirement: "only want to send an email for the benefits that still need to be used")
                        if limit > 0 and unused > 0.01:
                            item = {
                                'card_name': card_name,
                                'benefit': desc,
                                'limit': limit,
                                'time_cat': time_cat,
                                'used': used_amount,
                                'unused': unused,
                                'is_full': is_full
                            }
                            user_unused_items.append(item)
                            self.stdout.write(f"  - {card_name}: {desc}")
                            self.stdout.write(f"    Limit: ${limit:.2f} ({time_cat}) | Used: ${used_amount:.2f} | Unused: ${unused:.2f}")
                            if is_full:
                                self.stdout.write(f"    (Marked as FULL)")

            # Send Email if requested and items found
            if should_send and user_unused_items and user_email:
                # Frequency Check logic
                try:
                    prefs = db.get_user_notification_preferences(uid)
                    benefit_prefs = prefs.get('benefit_expiration', {})
                    if not benefit_prefs.get('enabled', True):
                         self.stdout.write(f"  -> Skipping: Benefit notifications disabled.")
                         continue

                    last_sent = user.get('last_benefit_email_sent_at')
                    freq_days = float(benefit_prefs.get('repeat_frequency', 1))
                    
                    should_notify = True
                    if last_sent:
                        import datetime
                        # Ensure last_sent is timezone aware if using firestore
                        # But simple comparison:
                        now = datetime.datetime.now(datetime.timezone.utc)
                        next_run = last_sent + datetime.timedelta(days=freq_days)
                        
                        # Add buffer zone of 1 hour (as per user request)
                        # If the differential is within 1 hour, it is valid.
                        # So if we are at 23h elapsed for a 24h cycle, (now) vs (next_run - 1h).
                        # if now < (next_run - 1h) -> skip.
                        
                        buffer = datetime.timedelta(hours=1)
                        if now < (next_run - buffer):
                            should_notify = False
                            time_left = (next_run - buffer) - now
                            self.stdout.write(f"  -> Skipping: Recently notified. Next email in {time_left} (incl buffer).")
                    
                    if should_notify:
                        self.stdout.write(f"  -> Sending email to {user_email}...")
                        result = self.send_unused_credits_email(user_email, username, first_name, last_name, user_unused_items)
                        if result:
                             db.update_last_benefit_notification_time(uid)
                    
                except Exception as e:
                    self.stdout.write(f"  [ERROR] Processing notification logic: {e}")
                    
            elif should_send and not user_unused_items:
                 self.stdout.write(f"  -> No credits found to email.")

    def send_unused_credits_email(self, to_email, username, first_name, last_name, items):
        subject = "Your Credit Card Benefit Status Update"
        
        # Use username for greeting
        greeting = f"Hi {username},"
        
        # Build HTML Table
        rows = ""
        for item in items:
            # Color coding for unused
            unused_color = "#333"
            if item['unused'] > 0:
                unused_color = "#2e7d32" # Green for available money
            
            # Status badge
            status_text = ""
            if item['is_full'] or item['unused'] <= 0.01:
                status_text = '<span style="background-color: #eee; color: #666; padding: 2px 6px; border-radius: 4px; font-size: 0.85em;">Used</span>'
            else:
                status_text = '<span style="background-color: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-size: 0.85em;">Available</span>'

            rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{item['card_name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    <div style="font-weight: 500;">{item['benefit']}</div>
                    <div style="font-size: 0.85em; color: #777;">{item['time_cat']}</div>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">${item['limit']:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">${item['used']:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: {unused_color};">
                    ${item['unused']:.2f}
                    <div style="margin-top: 4px;">{status_text}</div>
                </td>
            </tr>
            """
        
        html_content = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a1a1a;">{greeting}</h2>
            <p>Here is your latest credit card benefit usage for this period:</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 25px; font-size: 14px; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background-color: #f8f9fa; border-bottom: 2px solid #eaeaea;">
                        <th style="padding: 12px 10px; text-align: left; font-weight: 600; color: #444;">Card</th>
                        <th style="padding: 12px 10px; text-align: left; font-weight: 600; color: #444;">Benefit</th>
                        <th style="padding: 12px 10px; text-align: left; font-weight: 600; color: #444;">Limit</th>
                        <th style="padding: 12px 10px; text-align: left; font-weight: 600; color: #444;">Used</th>
                        <th style="padding: 12px 10px; text-align: left; font-weight: 600; color: #444;">Left</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="https://walletfreak.com/wallet" style="background-color: #000; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500; display: inline-block;">Go to Wallet</a>
            </div>
            
            <p style="margin-top: 30px; font-size: 0.9em; color: #666;">
                Cheers,<br>The WalletFreak Team
            </p>
        </div>
        """
        
        # Text fallback
        text_content = f"{greeting}\n\nHere is your credit card benefit status:\n\n"
        for item in items:
            status = "USED" if (item['is_full'] or item['unused'] <= 0.01) else "AVAILABLE"
            text_content += f"{item['card_name']} - {item['benefit']} ({item['time_cat']})\n"
            text_content += f"Status: {status}\n"
            text_content += f"Limit: ${item['limit']:.2f} | Used: ${item['used']:.2f} | Left: ${item['unused']:.2f}\n"
            text_content += "-" * 30 + "\n"
        
        text_content += "\nCheck your wallet: https://walletfreak.com/wallet\n\nCheers,\nThe WalletFreak Team"
        
        try:
            db.send_email_notification(to=to_email, subject=subject, html_content=html_content, text_content=text_content)
            self.stdout.write(self.style.SUCCESS("     Email sent successfully (queued)."))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"     Failed to send email: {e}"))
            return False


    def _get_current_period_key(self, time_category, anniversary_date_str=None):
        today = datetime.date.today()
        year = today.year
        
        # Parse Anniversary
        ann_month = 1
        ann_year = year
        if anniversary_date_str and anniversary_date_str != 'default':
            try:
                ann_date = datetime.datetime.strptime(anniversary_date_str, '%Y-%m-%d').date()
                ann_month = ann_date.month
                ann_year = ann_date.year
            except ValueError:
                pass
        elif anniversary_date_str == 'default':
             # Default behavior from views.py: Jan 1st of previous year
             ann_month = 1
             ann_year = year - 1

        if 'Monthly' in time_category:
            return f"{year}_{today.month:02d}"
            
        elif 'Quarterly' in time_category:
            q = (today.month - 1) // 3 + 1
            return f"{year}_Q{q}"
            
        elif 'Semi-annually' in time_category:
            # H1 (Jan-Jun), H2 (Jul-Dec)
            # Standard calendar halves. 
            # Note: Dashboard has complex logic for 'availability' based on anniversary, 
            # but the KEYS are always Year_H1 or Year_H2 based on current month.
            h = 1 if today.month <= 6 else 2
            return f"{year}_H{h}"
            
        elif 'every 4 years' in time_category.lower():
            # Align to 4-year blocks from Card Open Year (or 2020)
            
            # 1. Determine local "annual" start year
            this_year_anniv = datetime.date(year, ann_month, 1) # Approximate day
            if today < this_year_anniv:
                annual_start_year = year - 1
            else:
                annual_start_year = year

            # 2. Base Year
            base_year = ann_year if ann_year else 2020
            
            # 3. Block
            block_idx = (annual_start_year - base_year) // 4
            block_start_year = base_year + (block_idx * 4)
            block_end_year = block_start_year + 4
            
            return f"{block_start_year}_{block_end_year}"

        elif 'Anniversary' in time_category:
            # Period is functional based on anniversary year
            # If today < anniversary in current year, we are in the period starting last year
            
            this_year_anniv = datetime.date(year, ann_month, 1) # Approx day
            # If we had the exact day it would be better, but 'anniversary_date_str' usually has it.
            if anniversary_date_str and anniversary_date_str != 'default':
                 try:
                     d = datetime.datetime.strptime(anniversary_date_str, '%Y-%m-%d').date()
                     this_year_anniv = datetime.date(year, d.month, d.day)
                 except:
                     pass

            if today < this_year_anniv:
                start_year = year - 1
            else:
                start_year = year
                
            return f"{start_year}"

        else:
            # Calendar Year
            return str(year)