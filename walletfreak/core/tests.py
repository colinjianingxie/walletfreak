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
