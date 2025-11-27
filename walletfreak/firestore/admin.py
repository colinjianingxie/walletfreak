from django.contrib import admin
from django.core.paginator import Paginator
from django.utils.functional import cached_property
from .models import CreditCard, Personality
from core.services import db

class FirestorePaginator(Paginator):
    """
    Custom paginator that handles lists instead of QuerySets.
    """
    def _get_count(self):
        return len(self.object_list)
    count = property(_get_count)

class EmptyQuery:
    """
    Dummy query object to satisfy Django admin requirements.
    """
    select_related = False
    where = None
    order_by = []

class ListQuerySet:
    """
    A wrapper around a list that mimics a Django QuerySet.
    Handles filter(), order_by(), count(), and slicing.
    """
    def __init__(self, items, model=None):
        self.items = items
        self.model = model
        self.query = EmptyQuery()

    def all(self):
        return self

    def filter(self, *args, **kwargs):
        # Basic filtering support
        filtered_items = self.items
        for key, value in kwargs.items():
            # Handle __icontains
            if key.endswith('__icontains'):
                field = key.replace('__icontains', '')
                filtered_items = [
                    item for item in filtered_items 
                    if str(value).lower() in str(getattr(item, field, '')).lower()
                ]
            # Handle exact match
            else:
                filtered_items = [
                    item for item in filtered_items 
                    if getattr(item, key, None) == value
                ]
        return ListQuerySet(filtered_items, self.model)

    def none(self):
        return ListQuerySet([], self.model)

    def exists(self):
        return len(self.items) > 0

    def order_by(self, *args):
        # Basic ordering support
        if not args:
            return self
        
        sorted_items = self.items
        for field in reversed(args):
            reverse = field.startswith('-')
            key = field[1:] if reverse else field
            # Handle '?' for random (ignore for now)
            if key == '?':
                continue
            
            sorted_items = sorted(
                sorted_items, 
                key=lambda x: getattr(x, key, '') or '', 
                reverse=reverse
            )
        return ListQuerySet(sorted_items, self.model)

    def count(self):
        return len(self.items)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return ListQuerySet(self.items[k], self.model)
        return self.items[k]
    
    @property
    def ordered(self):
        return True  # Pretend we are ordered

class FirestoreModelAdmin(admin.ModelAdmin):
    """
    Base Admin class for Firestore-backed models.
    """
    paginator = FirestorePaginator
    list_per_page = 20

    def get_queryset(self, request):
        """
        Fetch all documents from Firestore and convert to model instances.
        """
        collection_name = self.get_collection_name()
        docs = db.get_collection(collection_name)
        
        instances = []
        for doc in docs:
            # Filter out fields that don't exist in the model to prevent TypeError
            model_fields = [f.name for f in self.model._meta.get_fields()]
            filtered_doc = {k: v for k, v in doc.items() if k in model_fields}
            
            instance = self.model(**filtered_doc)
            instances.append(instance)
            
        return ListQuerySet(instances, self.model)

    def get_object(self, request, object_id, from_field=None):
        """
        Fetch single document from Firestore.
        """
        collection_name = self.get_collection_name()
        doc = db.get_document(collection_name, object_id)
        
        if doc:
            # Filter out fields that don't exist in the model to prevent TypeError
            model_fields = [f.name for f in self.model._meta.get_fields()]
            filtered_doc = {k: v for k, v in doc.items() if k in model_fields}
            return self.model(**filtered_doc)
        return None

    def save_model(self, request, obj, form, change):
        """
        Save to Firestore.
        """
        collection_name = self.get_collection_name()
        data = {}
        
        # Convert model fields to dict
        for field in obj._meta.fields:
            value = getattr(obj, field.name)
            if value is not None:
                data[field.name] = value
                
        # Remove id from data if it's the same as the key (optional, but good for clean data)
        # But we need 'id' for the document ID.
        doc_id = data.pop('id', None)
        
        # If no doc_id (new object), use slug or generate one
        if not doc_id:
            if 'slug' in data and data['slug']:
                doc_id = data['slug']
            else:
                # Let Firestore generate ID or use name slugify
                from django.utils.text import slugify
                if 'name' in data:
                    doc_id = slugify(data['name'])
                    data['slug'] = doc_id
        
        if doc_id:
            db.create_document(collection_name, data, doc_id=doc_id)
            obj.id = doc_id
        else:
            # Should not happen if name is present
            pass

    def delete_model(self, request, obj):
        """
        Delete from Firestore.
        """
        collection_name = self.get_collection_name()
        if obj.id:
            db.delete_document(collection_name, obj.id)

    def get_collection_name(self):
        raise NotImplementedError("Subclasses must implement get_collection_name")

@admin.register(CreditCard)
class CreditCardAdmin(FirestoreModelAdmin):
    list_display = ('name', 'issuer', 'annual_fee', 'id')
    search_fields = ('name', 'issuer')
    
    def get_collection_name(self):
        return 'credit_cards'

@admin.register(Personality)
class PersonalityAdmin(FirestoreModelAdmin):
    list_display = ('name', 'tagline', 'id')
    search_fields = ('name',)
    
    def get_collection_name(self):
        return 'personalities'
