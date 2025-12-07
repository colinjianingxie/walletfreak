from django.core.management.base import BaseCommand
from core.services import db
from firebase_admin import firestore

class Command(BaseCommand):
    help = 'Fixes blog comment and upvote counts by recounting them'

    def handle(self, *args, **options):
        self.stdout.write('Starting blog count fix...')
        
        try:
            # Get all blogs
            blogs_ref = db.db.collection('blogs')
            blogs = blogs_ref.stream()
            
            count = 0
            for doc in blogs:
                blog_id = doc.id
                data = doc.to_dict()
                title = data.get('title', 'Unknown')
                
                self.stdout.write(f'Processing: {title} ({blog_id})')
                
                # 1. Count Comments
                comments_ref = blogs_ref.document(blog_id).collection('comments')
                # Note: getting all docs to count is not ideal for massive collections but fine for repair script
                comments = list(comments_ref.stream())
                real_comment_count = len(comments)
                
                # 2. Count Upvotes
                votes_ref = db.db.collection('blog_votes')
                upvotes_query = votes_ref.where('blog_id', '==', blog_id).where('vote_type', '==', 'upvote').stream()
                real_upvote_count = len(list(upvotes_query))
                
                downvotes_query = votes_ref.where('blog_id', '==', blog_id).where('vote_type', '==', 'downvote').stream()
                real_downvote_count = len(list(downvotes_query))
                
                # 3. Update Blog
                blogs_ref.document(blog_id).update({
                    'comment_count': real_comment_count,
                    'upvote_count': real_upvote_count,
                    'downvote_count': real_downvote_count
                })
                
                self.stdout.write(f'  -> Updated: {real_comment_count} comments, {real_upvote_count} upvotes')
                count += 1
                
            self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} blogs'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
