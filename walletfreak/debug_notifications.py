
from core.services import db
import datetime

def debug_users():
    print("--- Debugging Users and Cards ---")
    users = db.db.collection('users').stream()
    for user_doc in users:
        data = user_doc.to_dict()
        uid = user_doc.id
        email = data.get('email', 'No Email')
        print(f"\nUser: {uid} ({email})")
        
        # Check preferences
        prefs = db.get_user_notification_preferences(uid)
        print(f"  Preferences: {prefs}")
        
        # Check cards
        cards = db.get_user_cards(uid)
        if not cards:
            print("  No cards found.")
        
        for card in cards:
            name = card.get('name', 'Unknown')
            added = card.get('added_at')
            anniversary = card.get('anniversary_date')
            print(f"  Card: {name} (ID: {card.get('card_id')})")
            print(f"    Added: {added}")
            print(f"    Anniversary: {anniversary}")
            
            # Simulate logic
            if anniversary:
                try:
                    next_anniv = datetime.datetime.strptime(anniversary, "%Y-%m-%d").date()
                    today = datetime.date.today()
                    days = (next_anniv - today).days
                    print(f"    Days until anniversary: {days}")
                except Exception as e:
                    print(f"    Error parsing anniversary: {e}")
            elif added:
                 # Logic from check_notifications
                 added_date = added.date()
                 today = datetime.date.today()
                 candidate = added_date.replace(year=today.year)
                 if candidate < today:
                     candidate = added_date.replace(year=today.year + 1)
                 days = (candidate - today).days
                 print(f"    Calculated days until anniversary (from added_at): {days}")

if __name__ == "__main__":
    debug_users()
