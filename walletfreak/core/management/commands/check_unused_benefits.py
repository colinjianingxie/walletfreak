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
                
                for benefit in benefits:
                    # We are looking for monetary credits
                    # Usually indicated by 'dollar_value' > 0 and benefit_type='Credit' or just checking dollar_value
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
                        usage_key = benefit.get('description') 
                        
                        b_usage = usage_data.get(usage_key, {})
                        
                        used_amount = 0
                        if period_key:
                            # If structured with periods
                            if 'periods' in b_usage:
                                used_amount = b_usage['periods'].get(period_key, {}).get('used', 0)
                            else:
                                # Fallback or flat usage
                                used_amount = b_usage.get('used', 0)
                        else:
                            used_amount = b_usage.get('used', 0)
                            
                        # Calculate Per-Period limit if applicable
                        limit = dollar_val
                        if 'Monthly' in time_cat:
                             limit = dollar_val / 12
                        
                        unused = limit - used_amount
                        
                        if unused > 0:
                            item = {
                                'card_name': card_name,
                                'benefit': desc,
                                'limit': limit,
                                'time_cat': time_cat,
                                'used': used_amount,
                                'unused': unused
                            }
                            user_unused_items.append(item)
                            self.stdout.write(f"  - {card_name}: {desc}")
                            self.stdout.write(f"    Limit: ${limit:.2f} ({time_cat}) | Used: ${used_amount:.2f} | Unused: ${unused:.2f}")

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
                        result = self.send_unused_credits_email(user_email, username, user_unused_items)
                        if result:
                             db.update_last_benefit_notification_time(uid)
                    
                except Exception as e:
                    self.stdout.write(f"  [ERROR] Processing notification logic: {e}")
                    
            elif should_send and not user_unused_items:
                 self.stdout.write(f"  -> No unused credits to email.")

    def send_unused_credits_email(self, to_email, username, items):
        subject = "You have unused credit card benefits!"
        
        # Build HTML Table
        rows = ""
        for item in items:
            rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item['card_name']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item['benefit']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item['time_cat']}</td>
                 <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold; color: #d32f2f;">${item['unused']:.2f}</td>
            </tr>
            """
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; color: #333;">
            <h2>Hi {username},</h2>
            <p>You have unused benefits on your credit cards. Don't leave money on the table!</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #f5f5f5;">
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Card</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Benefit</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Period</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Unused Value</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            
            <p style="margin-top: 20px;">
                <a href="https://walletfreak.com/dashboard" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a>
            </p>
            
            <p>Cheers,<br>The WalletFreak Team</p>
        </div>
        """
        
        # Text fallback
        text_content = f"Hi {username},\n\nYou have unused benefits:\n\n"
        for item in items:
            text_content += f"- {item['card_name']}: {item['benefit']} - ${item['unused']:.2f} remaining ({item['time_cat']})\n"
        
        text_content += "\nCheck your dashboard: https://walletfreak.com/dashboard\n\nCheers,\nThe WalletFreak Team"
        
        try:
            db.send_email_notification(to=to_email, subject=subject, html_content=html_content, text_content=text_content)
            self.stdout.write(self.style.SUCCESS("     Email sent successfully."))
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