from django.core.management.base import BaseCommand
from core.services import db

class Command(BaseCommand):
    help = 'Cleans up successfully sent emails from the mail collection'

    def handle(self, *args, **options):
        self.stdout.write("Checking for sent emails to clean up...")
        
        try:
            # Query for emails with delivery.state == 'SUCCESS'
            # Note: We need to use FieldPath for nested fields or just filter manually if index missing
            # But standard filtering works for maps if indexed.
            # However, to avoid index requirements for now, we can stream and check? 
            # Or assume 'delivery' exists.
            
            # Let's try basic query first.
            mails_ref = db.db.collection('mail')
            
            # Since 'delivery.state' might require a composite index if mixed with other filters,
            # but usually fine on its own.
            # Using basic where clause on nested field
            query = mails_ref.where('delivery.state', '==', 'SUCCESS')
            
            # Also clean up older ones where 'delivery.state' might not exist but it's old? 
            # No, safer to only delete confirmed success.
            
            # Batch delete
            batch_size = 50
            deleted_count = 0
            
            docs = list(query.stream())
            
            for i in range(0, len(docs), batch_size):
                batch = db.db.batch()
                chunk = docs[i:i + batch_size]
                
                for doc in chunk:
                    batch.delete(doc.reference)
                    
                batch.commit()
                deleted_count += len(chunk)
                
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} sent emails."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error cleaning up emails: {e}"))
