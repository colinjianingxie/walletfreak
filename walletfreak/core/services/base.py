import firebase_admin
from firebase_admin import firestore, storage
from django.conf import settings

class BaseFirestoreService:
    def __init__(self):
        # Ensure app is initialized (it should be in settings.py)
        if not firebase_admin._apps:
             # This fallback is mostly for local testing if settings didn't catch it
             pass
        self._db = None
        self._bucket = None

    @property
    def db(self):
        if self._db is None:
            self._db = firestore.client()
        return self._db
    
    @property
    def bucket(self):
        if self._bucket is None:
            self._bucket = storage.bucket()
        return self._bucket

    def get_collection(self, collection_name, limit=None):
        ref = self.db.collection(collection_name)
        if limit:
            ref = ref.limit(limit)
        docs = ref.stream()
        return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

    def get_document(self, collection_name, doc_id):
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return {**doc.to_dict(), 'id': doc.id}
        return None

    def create_document(self, collection_name, data, doc_id=None):
        if doc_id:
            self.db.collection(collection_name).document(doc_id).set(data)
            return doc_id
        else:
            update_time, doc_ref = self.db.collection(collection_name).add(data)
            return doc_ref.id

    def update_document(self, collection_name, doc_id, data):
        doc_ref = self.db.collection(collection_name).document(doc_id)
        doc_ref.update(data)

    def delete_document(self, collection_name, doc_id):
        self.db.collection(collection_name).document(doc_id).delete()
