
from core.services import db
from datetime import datetime
import time

print("--- Starting Verification ---")

# 1. Verify Total User Count (Aggregation)
print("\nTesting get_total_user_count...")
try:
    start_time = time.time()
    count = db.get_total_user_count()
    duration = time.time() - start_time
    print(f"Total Users: {count} (Time: {duration:.4f}s)")
    if isinstance(count, int):
        print("SUCCESS: Result is an integer.")
    else:
        print(f"FAILURE: Result is {type(count)}")
except Exception as e:
    print(f"FAILURE: Error calling get_total_user_count: {e}")

# 2. Verify User Card Count (Aggregation)
print("\nTesting get_user_card_count...")
try:
    # Get a sample user
    users = list(db.db.collection('users').limit(1).stream())
    if users:
        uid = users[0].id
        print(f"Using sample User ID: {uid}")
        
        start_time = time.time()
        card_count = db.get_user_card_count(uid)
        duration = time.time() - start_time
        print(f"User Cards: {card_count} (Time: {duration:.4f}s)")
        
        if isinstance(card_count, int):
            print("SUCCESS: Result is an integer.")
        else:
            print(f"FAILURE: Result is {type(card_count)}")
    else:
        print("SKIPPING: No users found to test card count.")
except Exception as e:
    print(f"FAILURE: Error calling get_user_card_count: {e}")

# 3. Verify Active Card Slugs (Caching)
print("\nTesting get_active_card_slugs...")
try:
    # First call (uncached)
    start_time = time.time()
    slugs = db.get_active_card_slugs()
    duration = time.time() - start_time
    print(f"First Call (Uncached): {len(slugs)} slugs (Time: {duration:.4f}s)")
    
    # Second call (Cached)
    start_time = time.time()
    slugs_cached = db.get_active_card_slugs()
    duration = time.time() - start_time
    print(f"Second Call (Cached): {len(slugs_cached)} slugs (Time: {duration:.4f}s)")
    
    if duration < 0.1:
         print("SUCCESS: Second call was instant (Cached).")
    else:
         print("WARNING: Second call took time, caching might not be working or cache backend is slow.")

except Exception as e:
    print(f"FAILURE: Error calling get_active_card_slugs: {e}")

print("\n--- Verification Complete ---")
