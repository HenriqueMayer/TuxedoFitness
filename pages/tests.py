from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class LandingPageTests(TestCase):
    @override_settings(ALLOW_SIGNUPS=True)
    def test_landing_is_public_and_offers_signup(self):
        response = self.client.get(reverse('pages:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seu histórico de treino')
        self.assertContains(response, reverse('accounts:signup'))
        self.assertContains(response, reverse('accounts:login'))

    @override_settings(ALLOW_SIGNUPS=True)
    def test_landing_keeps_signup_after_a_user_exists(self):
        get_user_model().objects.create_user('owner')

        response = self.client.get(reverse('pages:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Criar conta')

    @override_settings(ALLOW_SIGNUPS=False)
    def test_landing_hides_signup_when_disabled(self):
        response = self.client.get(reverse('pages:landing'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Criar conta')
