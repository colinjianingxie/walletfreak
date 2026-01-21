from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Notification
from blog.models import Blog
import json

class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

    def test_create_notification(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title="Test Notification",
            message="This is a test",
            notification_type="system"
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notif.recipient, self.user)

    def test_get_notifications_api(self):
        Notification.objects.create(
            recipient=self.user,
            title="Test 1",
            message="Msg 1"
        )
        response = self.client.get('/notifications/api/get/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['unread_count'], 1)
        self.assertEqual(data['notifications'][0]['title'], "Test 1")

    def test_mark_read_api(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title="Test 1",
            message="Msg 1"
        )
        
        # Mark specific one read
        response = self.client.post(
            '/notifications/api/mark-read/',
            data=json.dumps({'id': notif.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

        # Create another and mark all read
        notif2 = Notification.objects.create(
            recipient=self.user,
            title="Test 2",
            message="Msg 2"
        )
        response = self.client.post(
            '/notifications/api/mark-read/',
            data=json.dumps({'all': True}),
            content_type='application/json'
        )
        notif2.refresh_from_db()
        self.assertTrue(notif2.is_read)

    def test_signal_on_blog_creation(self):
        # Create a new published blog post
        blog = Blog.objects.create(
            title="New Blog Post",
            slug="new-blog-post",
            content="Content",
            author_uid="123",
            author_name="Admin",
            status="published"
        )
        
        # Check if notification was created for the user
        self.assertEqual(Notification.objects.filter(recipient=self.user, notification_type='blog').count(), 1)
        notif = Notification.objects.get(recipient=self.user, title__contains="New Article")
        self.assertEqual(notif.link, "/blog/new-blog-post/")
