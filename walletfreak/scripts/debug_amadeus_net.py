import os
import sys
import logging
from amadeus import Client, ResponseError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("amadeus_debug")

# Load env vars manually for script or assume they are in env
client_id = os.environ.get('AMADEUS_CLIENT_ID')
client_secret = os.environ.get('AMADEUS_CLIENT_SECRET')

if not client_id or not client_secret:
    print("❌ Missing API Keys in environment variables.")
    sys.exit(1)

print(f"Testing connection with ID: {client_id[:4]}***")

amadeus = Client(
    client_id=client_id,
    client_secret=client_secret,
    hostname='test', # Sandbox
    log_level='debug' # Enable SDK debug logging
)

try:
    print("Attempting to fetch locations...")
    # Using the exact call the user asked about (ignoring subtype difference for now, just testing network)
    response = amadeus.reference_data.locations.get(
        keyword='LON',
        subType='CITY'
    )
    print("✅ Success!")
    print(response.data[0])
except ResponseError as error:
    print(f"❌ Error: {error}")
    print(f"❌ Error Code: {error.code if hasattr(error, 'code') else 'N/A'}")
    # Print the underlying cause if network error
    # The Amadeus SDK wraps connection errors; let's try to inspect it
    import pprint
    pprint.pprint(error.__dict__)
except Exception as e:
    import traceback
    traceback.print_exc()
