import os
import django
import sys

sys.path.append('/Users/xie/Desktop/projects/walletfreak/walletfreak')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services.amadeus_service import AmadeusService
try:
    service = AmadeusService()
    print("✅ AmadeusService initialized successfully.")
except Exception as e:
    print(f"❌ AmadeusService initialization failed: {e}")
