from django.core.management.base import BaseCommand
from core.services import db

class Command(BaseCommand):
    help = 'Cleans up successfully sent emails from the mail collection'

    def handle(self, *args, **options):
        self.stdout.write("Checking for sent emails to clean up...")
        
        try:
            mails_ref = db.db.collection('mail')
            
        
            # Query for emails. 
            # To be robust against missing 'state' field (as seen in some extension versions),
            # we will fetch and filter in Python.
            # We filter for docs that have 'delivery' field.
            # Using limit to prevent memory issues, we can run this command multiple times or in a loop.
            # But for a daily cron, a loop until done or max count is good.
            
            MAX_DELETE = 500
            batch = db.db.batch()
            count = 0
            deleted_count = 0
            
            # Get docs that have delivery info (implies attempt made)
            # We can't easily query for "has delivery" without index, but we can query order by delivery.endTime?
            # Or just stream the collection (assuming 'mail' is mostly ephemeral).
            
            docs = list(mails_ref.limit(500).stream())
            self.stdout.write(f"Scanned {len(docs)} documents.")
            
            for doc in docs:
                data = doc.to_dict()
                delivery = data.get('delivery')
                
                should_delete = False
                
                if delivery:
                    state = delivery.get('state')
                    error = delivery.get('error')
                    end_time = delivery.get('endTime')
                    
                    # Criteria 1: Explicit SUCCESS state
                    if state == 'SUCCESS':
                        should_delete = True
                        
                    # Criteria 2: Finished with no error (implicit success)
                    elif end_time and error is None:
                         should_delete = True
                         
                if should_delete:
                    batch.delete(doc.reference)
                    count += 1
                    
                    if count >= 400: # Commit batches of 400
                        batch.commit()
                        deleted_count += count
                        count = 0
                        batch = db.db.batch()
            
            if count > 0:
                batch.commit()
                deleted_count += count
                
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} sent emails."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error cleaning up emails: {e}"))
