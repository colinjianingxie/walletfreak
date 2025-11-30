from django.core.management.base import BaseCommand
from core.services import db
from core.quiz_data import PERSONALITIES, QUIZ_QUESTIONS

class Command(BaseCommand):
    help = 'Seeds personalities and quiz questions to Firestore'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Personalities...')
        
        # Seed Personalities
        for p in PERSONALITIES:
            try:
                # Use slug as document ID
                doc_id = p['slug']
                db.db.collection('personalities').document(doc_id).set(p)
                self.stdout.write(self.style.SUCCESS(f'Successfully seeded personality: {p["name"]}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error seeding personality {p["name"]}: {e}'))

        self.stdout.write('Seeding Quiz Questions...')
        
        # Seed Quiz Questions
        for q in QUIZ_QUESTIONS:
            try:
                # Use stage_N as document ID for easy ordering/retrieval if needed, 
                # though we query by stage field usually.
                doc_id = f"stage_{q['stage']}"
                db.db.collection('quiz_questions').document(doc_id).set(q)
                self.stdout.write(self.style.SUCCESS(f'Successfully seeded question stage: {q["stage"]}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error seeding question stage {q["stage"]}: {e}'))

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
