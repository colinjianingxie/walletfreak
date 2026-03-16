"""
Management command: send_benefit_notifications

Run daily (e.g. via Cloud Scheduler) to create in-app notifications for
benefits that are about to expire within each user's configured window.
"""

from datetime import datetime
from django.core.management.base import BaseCommand
from core.services import db
from core.benefit_periods import calculate_days_until_expiration, get_current_period_key


class Command(BaseCommand):
    help = 'Create in-app notifications for benefits approaching expiration.'

    def handle(self, *args, **options):
        now = datetime.now()
        users = list(db.db.collection('users').stream())
        self.stdout.write(f"Checking {len(users)} users for benefit expiration notifications...")

        total_created = 0

        for user_doc in users:
            uid = user_doc.id
            user_data = user_doc.to_dict()

            prefs = user_data.get('notification_preferences', {})
            benefit_pref = prefs.get('benefit_expiration', {})
            if not benefit_pref.get('enabled', True):
                continue

            start_days_before = benefit_pref.get('start_days_before', 7)
            repeat_frequency = benefit_pref.get('repeat_frequency', 1)

            # Get user's active wallet cards
            try:
                active_cards = db.get_user_cards(uid, status='active')
            except Exception as e:
                self.stderr.write(f"  Error fetching cards for {uid}: {e}")
                continue

            if not active_cards:
                continue

            for card in active_cards:
                card_id = card.get('card_id')
                card_details = db.get_card(card_id) if card_id else None
                if not card_details or not card_details.get('is_active', True):
                    continue

                # Parse anniversary
                ann_str = card.get('anniversary_date', '')
                if ann_str == 'default':
                    ann_month, ann_day, ann_year = 1, 1, now.year - 1
                elif ann_str:
                    try:
                        ann_dt = datetime.strptime(ann_str, '%Y-%m-%d')
                        ann_month, ann_day, ann_year = ann_dt.month, ann_dt.day, ann_dt.year
                    except ValueError:
                        ann_month, ann_day, ann_year = 1, 1, now.year
                else:
                    ann_month, ann_day, ann_year = 1, 1, now.year

                for idx, benefit in enumerate(card_details.get('benefits', [])):
                    if benefit.get('benefit_type') in ('Protection', 'Bonus', 'Perk', 'Lounge', 'Status', 'Insurance'):
                        continue

                    dollar_value = benefit.get('dollar_value', 0)
                    if not dollar_value or dollar_value <= 0:
                        continue

                    frequency = benefit.get('time_category', 'Annually (calendar year)')
                    days_left = calculate_days_until_expiration(
                        frequency, ann_month, ann_day, ann_year, now=now
                    )

                    if days_left is None or days_left > start_days_before:
                        continue

                    # Check current period status — skip if already full
                    benefit_id = benefit.get('id') or str(idx)
                    period_key = get_current_period_key(frequency, ann_month, ann_day, ann_year, now=now)
                    usage = card.get('benefit_usage', {}).get(benefit_id, {})
                    period_data = usage.get('periods', {}).get(period_key, {})
                    period_used = period_data.get('used', 0) or 0
                    is_full = period_data.get('is_full', False)
                    if is_full or period_used >= dollar_value:
                        continue

                    # Check for duplicate notification within repeat_frequency
                    from google.cloud.firestore import FieldFilter
                    from datetime import timedelta
                    cutoff = now - timedelta(days=repeat_frequency)
                    existing = (
                        db.db.collection('notifications')
                        .where(filter=FieldFilter('uid', '==', uid))
                        .where(filter=FieldFilter('type', '==', 'benefit_expiration'))
                        .where(filter=FieldFilter('metadata.benefit_id', '==', benefit_id))
                        .where(filter=FieldFilter('metadata.card_id', '==', card_id))
                        .order_by('created_at', direction='DESCENDING')
                        .limit(1)
                    )
                    skip = False
                    for doc in existing.stream():
                        doc_data = doc.to_dict()
                        created = doc_data.get('created_at')
                        if created:
                            created_naive = created.replace(tzinfo=None) if hasattr(created, 'tzinfo') and created.tzinfo else created
                            if created_naive > cutoff:
                                skip = True
                    if skip:
                        continue

                    benefit_name = benefit.get('description', 'Benefit')
                    card_name = card_details.get('name', 'Card')
                    db.create_notification(
                        uid=uid,
                        type='benefit_expiration',
                        title=f'{card_name} benefit expiring',
                        body=f'{benefit_name} — {days_left} day{"s" if days_left != 1 else ""} left (${dollar_value - period_used:.0f} remaining)',
                        metadata={
                            'card_id': card_id,
                            'card_name': card_name,
                            'benefit_id': benefit_id,
                            'benefit_name': benefit_name,
                            'days_remaining': days_left,
                        },
                        action_url=f'/dashboard/',
                        action_route=f'/stacks/wallet-card/{card.get("id")}',
                    )
                    total_created += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Created {total_created} benefit expiration notifications."))
