from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class HomeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='password123',
            email='test@example.com'
        )
        self.home_url = reverse('home')
        self.dashboard_url = reverse('dashboard')

    def test_home_page_redirects_for_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        s = self.client.session
        s['uid'] = 'testuser_uid'
        s.save()
        
        response = self.client.get(self.home_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_home_page_renders_for_anonymous_user(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing.html')

class UsernameGenerationTest(TestCase):
    def test_username_generation(self):
        from core.services import db
        from unittest.mock import patch
        
        # Test basic generation
        # Mock is_username_taken to always return False (available)
        with patch.object(db, 'is_username_taken', return_value=False):
            username = db.generate_unique_username('John', 'Doe', 'uid123')
            # Should be johndoe + 4 digits
            self.assertTrue(username.startswith('johndoe'))
            self.assertEqual(len(username), 7 + 4)
            self.assertTrue(username[7:].isdigit())

    def test_username_generation_sanitization(self):
        from core.services import db
        from unittest.mock import patch
        
        with patch.object(db, 'is_username_taken', return_value=False):
            username = db.generate_unique_username('Jo hn', 'D-oe', 'uid123')
            # Should be johndoe + 4 digits (spaces/hyphens removed)
            self.assertTrue(username.startswith('johndoe'))
            
    def test_username_generation_collision(self):
        from core.services import db
        from unittest.mock import patch
        
        # Test collision retry
        # First call returns True (taken), subsequent return False (available)
        with patch.object(db, 'is_username_taken', side_effect=[True, False]):
            username = db.generate_unique_username('Jane', 'Doe', 'uid123')
            self.assertTrue(username.startswith('janedoe'))
            
    def test_username_generation_fallback(self):
        from core.services import db
        from unittest.mock import patch
        
        # Test exhausting retries
        with patch.object(db, 'is_username_taken', return_value=True):
            username = db.generate_unique_username('Bob', 'Smith', 'uid123456')
            # Fallback format: bobsmith_uid123 (6 chars of uid)
            self.assertEqual(username, 'bobsmith_uid123')
