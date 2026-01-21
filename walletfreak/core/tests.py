from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from io import StringIO
from unittest.mock import MagicMock, patch

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

class CheckUnusedBenefitsTest(TestCase):
    def test_check_unused_benefits_optimization(self):
        from core.services import db
        
        # Mock Firestore
        mock_client = MagicMock()
        with patch.object(db, '_db', mock_client):
            mock_db = mock_client
            # Mock Collection Group Query
            mock_query = MagicMock()
            mock_db.collection_group.return_value.where.return_value = mock_query
            
            # Create mock user card docs
            mock_card_doc = MagicMock()
            mock_card_doc.id = 'card_123'
            mock_card_doc.to_dict.return_value = {'status': 'active'}
            # Mock parent hierarchy: doc -> col -> doc (user)
            mock_card_doc.reference.parent.parent.id = 'user_123'
            
            mock_query.stream.return_value = [mock_card_doc]
            
            # Mock User Batch Fetch
            mock_user_snap = MagicMock()
            mock_user_snap.exists = True
            mock_user_snap.id = 'user_123'
            mock_user_snap.to_dict.return_value = {'username': 'testuser', 'email': 'test@example.com'}
            
            mock_db.get_all.return_value = [mock_user_snap]
            
            # Mock Master Card Fetch (via service method)
            with patch.object(db, 'get_specific_cards') as mock_get_specific:
                mock_get_specific.return_value = [{
                    'id': 'card_123',
                    'name': 'Test Card',
                    'slug': 'card_123',
                    'benefits': [{
                        'id': 'ben_1',
                        'benefit_type': 'Credit',
                        'dollar_value': 100,
                        'description': 'Test Credit',
                        'time_category': 'Annually'
                    }]
                }]
                
                out = StringIO()
                call_command('check_unused_benefits', stdout=out)
                
                output = out.getvalue()
                
                # Check that optimization mode was triggered
                self.assertIn("Running in BULK optimization mode", output)
                
                # Check that Collection Group was called
                mock_db.collection_group.assert_called_with('user_cards')
                
                # Check that we found the user
                self.assertIn("User: testuser (user_123)", output)
                self.assertIn("Test Card: Test Credit", output)

