from firebase_admin import firestore
from google.cloud.firestore import FieldFilter
from django.core.cache import cache


class InAppNotificationMixin:
    """Mixin for in-app notification CRUD against the top-level notifications collection."""

    def create_notification(self, uid, type, title, body, metadata=None, action_url=None, action_route=None):
        """Create a single in-app notification and invalidate the unread cache."""
        doc_data = {
            'uid': uid,
            'type': type,
            'title': title,
            'body': body,
            'read': False,
            'created_at': firestore.SERVER_TIMESTAMP,
            'metadata': metadata or {},
            'action_url': action_url,
            'action_route': action_route,
        }
        _, doc_ref = self.db.collection('notifications').add(doc_data)
        cache.delete(f'notif_unread_{uid}')
        return doc_ref.id

    def get_user_notifications(self, uid, limit=20, start_after=None):
        """Return paginated notifications for a user, newest first."""
        query = (
            self.db.collection('notifications')
            .where(filter=FieldFilter('uid', '==', uid))
            .order_by('created_at', direction=firestore.Query.DESCENDING)
            .limit(limit)
        )

        if start_after:
            cursor_doc = self.db.collection('notifications').document(start_after).get()
            if cursor_doc.exists:
                query = query.start_after(cursor_doc)

        return [doc.to_dict() | {'id': doc.id} for doc in query.stream()]

    def get_unread_count(self, uid):
        """Return the number of unread notifications (cached 60s)."""
        cache_key = f'notif_unread_{uid}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        query = (
            self.db.collection('notifications')
            .where(filter=FieldFilter('uid', '==', uid))
            .where(filter=FieldFilter('read', '==', False))
        )
        count = sum(1 for _ in query.stream())
        cache.set(cache_key, count, 60)
        return count

    def mark_notification_read(self, uid, notification_id):
        """Mark a single notification as read (with uid ownership check)."""
        doc_ref = self.db.collection('notifications').document(notification_id)
        doc = doc_ref.get()
        if not doc.exists or doc.to_dict().get('uid') != uid:
            return False
        doc_ref.update({'read': True})
        cache.delete(f'notif_unread_{uid}')
        return True

    def mark_all_notifications_read(self, uid):
        """Mark every unread notification for uid as read."""
        query = (
            self.db.collection('notifications')
            .where(filter=FieldFilter('uid', '==', uid))
            .where(filter=FieldFilter('read', '==', False))
        )
        batch = self.db.batch()
        count = 0
        for doc in query.stream():
            batch.update(doc.reference, {'read': True})
            count += 1
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        if count % 500 != 0:
            batch.commit()
        cache.delete(f'notif_unread_{uid}')
        return count

    def delete_notification(self, uid, notification_id):
        """Delete a notification (with uid ownership check)."""
        doc_ref = self.db.collection('notifications').document(notification_id)
        doc = doc_ref.get()
        if not doc.exists or doc.to_dict().get('uid') != uid:
            return False
        was_unread = not doc.to_dict().get('read', True)
        doc_ref.delete()
        if was_unread:
            cache.delete(f'notif_unread_{uid}')
        return True

    def create_bulk_notifications(self, notifications_list):
        """Create many notifications using batched writes (max 500 per batch)."""
        batch = self.db.batch()
        uids_to_invalidate = set()
        count = 0

        for item in notifications_list:
            doc_ref = self.db.collection('notifications').document()
            doc_data = {
                'uid': item['uid'],
                'type': item['type'],
                'title': item['title'],
                'body': item['body'],
                'read': False,
                'created_at': firestore.SERVER_TIMESTAMP,
                'metadata': item.get('metadata', {}),
                'action_url': item.get('action_url'),
                'action_route': item.get('action_route'),
            }
            batch.set(doc_ref, doc_data)
            uids_to_invalidate.add(item['uid'])
            count += 1

            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()

        if count % 500 != 0:
            batch.commit()

        for uid in uids_to_invalidate:
            cache.delete(f'notif_unread_{uid}')

        return count
