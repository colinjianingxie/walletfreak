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

        # 1. Fetch Users
        if target_uid:
            user = db.get_user_profile(target_uid)
            users = [user] if user else []
        elif target_email:
            # Not efficient but fine for tool
            all_users = db.db.collection('users').stream()
            users = []
            for doc in all_users:
                u = doc.to_dict() | {'id': doc.id}
                if u.get('email') == target_email:
                    users.append(u)
                    break
        else:
            users_ref = db.db.collection('users')
            users = [doc.to_dict() | {'id': doc.id} for doc in users_ref.stream()]

        self.stdout.write(f"Found {len(users)} users to check.")
        
        # Cache card definitions to avoid repeated fetches
        card_defs = {}

        for user in users:
            uid = user['id']
            username = user.get('username', 'Unknown')
            first_name = user.get('first_name', '').strip()
            last_name = user.get('last_name', '').strip()
            user_email = user.get('email')
            
            # Fetch active cards
            user_cards = db.get_user_cards(uid, status='active')
            
            if not user_cards:
                continue

            self.stdout.write(f"\nUser: {username} ({uid})")
            
            user_unused_items = []
            
            for u_card in user_cards:
                card_slug = u_card.get('card_id')
                card_name = u_card.get('name')
                
                # Fetch/Cache definition
                if card_slug not in card_defs:
                    def_doc = db.get_card_by_slug(card_slug)
                    card_defs[card_slug] = def_doc
                
                card_def = card_defs[card_slug]
                if not card_def:
                    self.stdout.write(f"  [WARN] Definition not found for card: {card_slug}")
                    continue

                # Analyze benefits
                benefits = card_def.get('benefits', [])
                credits_found = False
                
                for idx, benefit in enumerate(benefits):
                    # We are looking for monetary credits
                    # Usually indicated by 'dollar_value' > 0 and benefit_type='Credit' or just checking dollar_value
                    if benefit.get('benefit_type') != 'Credit':
                        continue

                    dollar_val = benefit.get('dollar_value')
                    
                    if dollar_val and dollar_val > 0:
                        credits_found = True
                        desc = benefit.get('short_description') or benefit.get('description')
                        time_cat = benefit.get('time_category', 'Annually')
                        
                        # Determine period key
                        # This logic mirrors parse_benefits_csv or usage logic
                        period_key = self._get_current_period_key(time_cat)
                        
                        # Check usage
                        usage_data = u_card.get('benefit_usage', {})
                        # KEY FIX: Use benefit_{idx} to match dashboard/views.py
                        usage_key = f"benefit_{idx}"
                        
                        b_usage = usage_data.get(usage_key, {})
                        
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
                        if limit > 0:
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
                    freq_days = float(benefit_prefs.get('repeat_frequency', 7))
                    
                    should_notify = True
                    if last_sent:
                        import datetime
                        # Ensure last_sent is timezone aware if using firestore
                        # But simple comparison:
                        now = datetime.datetime.now(datetime.timezone.utc)
                        next_run = last_sent + datetime.timedelta(days=freq_days)
                        
                        if now < next_run:
                            should_notify = False
                            time_left = next_run - now
                            self.stdout.write(f"  -> Skipping: Recently notified. Next email in {time_left}.")
                    
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
        
        # Determine Greeting
        greeting_name = username
        if first_name or last_name:
            greeting_name = f"{first_name} {last_name}".strip()
        
        greeting = f"Hi {greeting_name},"
        
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


    def _get_current_period_key(self, time_category):
        today = datetime.date.today()
        year = today.year
        
        if 'Monthly' in time_category:
            return f"{year}_{today.month:02d}"
        elif 'Quarterly' in time_category:
            q = (today.month - 1) // 3 + 1
            return f"{year}_Q{q}"
        elif 'Semi-annually' in time_category:
            h = 1 if today.month <= 6 else 2
            return f"{year}_H{h}"
        else:
            return str(year)