from django.test import TestCase, Client
from django.urls import reverse

# Create your tests here.

class RegisterViewTests(TestCase):
    def test_register_form_displayed(self):
        client = Client()
        response = client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')
        self.assertContains(response, 'username')
        self.assertContains(response, 'first_name')
        self.assertContains(response, 'last_name')

class LoginViewTests(TestCase):
    def test_login_form_displayed(self):
        client = Client()
        response = client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')
        self.assertContains(response, 'username')
        self.assertContains(response, 'password')
