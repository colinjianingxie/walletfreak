from django.core.management.base import BaseCommand
from django.conf import settings
from core.services import db
import json
import os

class Command(BaseCommand):
    help = 'Seeds personalities and quiz questions to Firestore'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Personalities...')
        
        # Load personalities from JSON file
        json_path = os.path.join(settings.BASE_DIR, 'default_personalities.json')
        try:
            with open(json_path, 'r') as f:
                personalities = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Could not find {json_path}'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in {json_path}'))
            return

        # Seed Personalities
        for p in personalities:
            try:
                # Use slug as document ID
                doc_id = p['slug']
                db.db.collection('personalities').document(doc_id).set(p)
                self.stdout.write(self.style.SUCCESS(f'Successfully seeded personality: {p["name"]}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error seeding personality {p["name"]}: {e}'))

        self.stdout.write('Seeding Quiz Questions...')
        
        # Load quiz questions from JSON file
        quiz_json_path = os.path.join(settings.BASE_DIR, 'default_quiz_questions.json')
        try:
            with open(quiz_json_path, 'r') as f:
                quiz_questions = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Could not find {quiz_json_path}'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in {quiz_json_path}'))
            return

        # Seed Quiz Questions
        for q in quiz_questions:
            try:
                # Use stage_N as document ID for easy ordering/retrieval if needed, 
                # though we query by stage field usually.
                doc_id = f"stage_{q['stage']}"
                db.db.collection('quiz_questions').document(doc_id).set(q)
                self.stdout.write(self.style.SUCCESS(f'Successfully seeded question stage: {q["stage"]}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error seeding question stage {q["stage"]}: {e}'))

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
