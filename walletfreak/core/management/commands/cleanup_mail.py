from django.core.management.base import BaseCommand
from core.services import db
from datetime import datetime, timedelta
from firebase_admin import firestore

class Command(BaseCommand):
    help = 'Cleans up delivered mail from Firestore to reduce storage usage.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of history to keep (default: 7)'
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually perform the deletion (default is dry-run)'
        )

    def handle(self, *args, **options):
        days = options['days']
        execute = options['execute']
        
        self.stdout.write(f"checking for delivered mail older than {days} days...")
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Query for delivered mail
        # delivery.state == 'SUCCESS'
        try:
            # Note: Complex queries might require compound indexes.
            # We will query by state and then filter by date in memory if needed, 
            # or try to use a compound query if index exists.
            # Given the likely volume, let's try to filter by state first.
            
            mail_ref = db.db.collection('mail')
            query = mail_ref.where('delivery.state', '==', 'SUCCESS')
            
            docs = query.stream()
            
            count = 0
            deleted_count = 0
            
            for doc in docs:
                data = doc.to_dict()
                
                # Check timestamp
                # The creation time is not always in the data, but we can use 'delivery.endTime' or check doc create time if available via standard fields?
                # Firestore python client doc.create_time is available.
                
                created_at = doc.create_time
                if not created_at:
                    # Fallback to delivery info if available
                    delivery = data.get('delivery', {})
                    end_time = delivery.get('endTime')
                    if end_time:
                         # timestamp usually
                         created_at = end_time
                
                if created_at:
                    # Ensure timezone awareness compatibility
                    # create_time is usually strict protobuf timestamp or datetime with timezone
                    if hasattr(created_at, 'timestamp'):
                        # Convert to naive or aware ensuring comparison works
                        # Firestore datetimes are usually aware (UTC)
                        pass
                    
                    # Simple comparison logic:
                    # If using 'days', we want to delete things OLDER than cutoff.
                    # so if created_at < cutoff_date
                    
                    # Allow for flexible type handling
                    dt_val = created_at
                    if isinstance(dt_val, datetime):
                        # Ensure cutoff is timezone aware if dt_val is
                        if dt_val.tzinfo and not cutoff_date.tzinfo:
                            from django.utils import timezone
                            cutoff_date = timezone.now() - timedelta(days=days)
                        
                        if dt_val < cutoff_date:
                            should_delete = True
                        else:
                            should_delete = False
                    else:
                        # Logic if we can't parse date? Skip to be safe.
                        should_delete = False
                        
                    if should_delete:
                        count += 1
                        if execute:
                            doc.reference.delete()
                            deleted_count += 1
                            if deleted_count % 100 == 0:
                                self.stdout.write(f"Deleted {deleted_count} emails...")
                        else:
                            self.stdout.write(f"[Dry Run] Would delete mail {doc.id} created at {created_at}")
                            
            if execute:
                self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} delivered emails."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Dry run complete. Found {count} emails that would be deleted."))
                self.stdout.write("Use --execute to perform the deletion.")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error cleaning up mail: {e}"))
