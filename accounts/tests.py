from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import CustomUser, generate_qr_code, Product, Cart
import json
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import time
from decimal import Decimal

class AuthenticationTestCase(TestCase):
    def setUp(self):
        """Configuration initiale avant chaque test."""
        self.client = Client()
        # Créer un utilisateur de test avec rôle 'client'
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            email='testuser@example.com',
            role='client'
        )
        # URLs pour les tests
        self.login_url = reverse('accounts:login')
        self.register_url = reverse('accounts:register')
        self.logout_url = reverse('accounts:logout')
        self.page_principale_url = reverse('accounts:page_principale')
        self.dashboard_url = reverse('accounts:dashboard')

    def test_user_creation_via_register(self):
        """Teste l'inscription d'un nouvel utilisateur."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role': 'client'
        }
        response = self.client.post(self.register_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())
        # Vérifier que le message de succès est présent dans les messages de la session
        messages = list(response.context['messages']) if 'messages' in response.context else []
        success_message = any("Inscription réussie" in str(m) for m in messages)
        self.assertTrue(success_message, "Le message 'Inscription réussie' n'a pas été trouvé dans les messages.")

    def test_login_success(self):
        """Teste la connexion avec des identifiants valides."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['role'], 'client')
        self.assertTrue(response_data['message'], 'Connexion réussie')
        # Vérifier que le QR code est généré
        user = CustomUser.objects.get(username='testuser')
        self.assertIsNotNone(user.qr_code)

    def test_login_failure(self):
        """Teste la connexion avec des identifiants invalides."""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Identifiants incorrects.')

    def test_logout_success(self):
        """Teste la déconnexion d'un utilisateur connecté."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertRedirects(response, self.login_url)

    def test_login_required_view(self):
        """Teste que les vues nécessitent une authentification."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirection vers login si non connecté
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_qr_code_generation(self):
        """Teste la génération du QR code après connexion."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        self.client.post(self.login_url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        user = CustomUser.objects.get(username='testuser')
        self.assertIsNotNone(user.qr_code)
        
        with default_storage.open(user.qr_code.name, 'rb') as f:
            self.assertTrue(len(f.read()) > 0)

    def tearDown(self):
        """Nettoyage après chaque test."""
        # Supprimer les fichiers QR générés
        user = CustomUser.objects.get(username='testuser')
        if user.qr_code and default_storage.exists(user.qr_code.name):
            default_storage.delete(user.qr_code.name)

class IntegrationTestCase(TestCase):
    def setUp(self):
        """Configuration initiale pour les tests d'intégration."""
        self.client = Client()
        # Créer des utilisateurs de test avec différents rôles
        self.client_user = CustomUser.objects.create_user(
            username='clientuser',
            password='clientpass123',
            email='client@example.com',
            role='client'
        )
        self.delivery_user = CustomUser.objects.create_user(
            username='deliveryuser',
            password='deliverypass123',
            email='delivery@example.com',
            role='delivery'
        )
        # URLs pour les tests
        self.login_url = reverse('accounts:login')
        self.delivery_dashboard_url = reverse('accounts:delivery_dashboard')
        self.page_principale_url = reverse('accounts:page_principale')

    def test_complete_login_flow(self):
        """Teste le flux complet de connexion pour un client."""
        # Données de connexion pour un client
        login_data = {
            'username': 'clientuser',
            'password': 'clientpass123'
        }
        # Soumettre le formulaire de connexion avec AJAX
        response = self.client.post(self.login_url, login_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['role'], 'client')
        self.assertTrue(response_data['message'], 'Connexion réussie')

        # Vérifier que l'utilisateur est connecté
        self.assertTrue(self.client.session.get('_auth_user_id'))
        user = CustomUser.objects.get(username='clientuser')
        self.assertIsNotNone(user.qr_code)

        
        # Vérifier la redirection vers page_principale pour un client
        response = self.client.get(self.page_principale_url)
        self.assertEqual(response.status_code, 200)

    def test_login_with_delivery_role(self):
        """Teste le flux de connexion pour un livreur avec redirection appropriée."""
        login_data = {
            'username': 'deliveryuser',
            'password': 'deliverypass123'
        }
        response = self.client.post(self.login_url, login_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['role'], 'delivery')
        self.assertTrue(response_data['message'], 'Connexion réussie')

        # Vérifier la redirection vers delivery_dashboard
        response = self.client.get(self.delivery_dashboard_url)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        """Nettoyage après chaque test."""
        users = CustomUser.objects.all()
        for user in users:
            if user.qr_code and default_storage.exists(user.qr_code.name):
                default_storage.delete(user.qr_code.name)

class PerformanceTestCase(TestCase):
    def setUp(self):
        """Configuration initiale pour les tests de performance."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='perfuser',
            password='perfpass123',
            email='perfuser@example.com',
            role='client'
        )
        from accounts.models import Product
        self.product = Product.objects.create(name="Perf Product", price=Decimal('10.00'))
        self.add_to_cart_url = reverse('accounts:add_to_cart', args=[self.product.id])
        self.client.login(username='perfuser', password='perfpass123')

    def test_add_to_cart_performance(self):
        """Mesure le temps d'exécution de l'ajout au panier."""
        start_time = time.time()
        for _ in range(100):  
            response = self.client.post(
                self.add_to_cart_url,
                json.dumps({'action': 'add', 'quantity': 1}),
                content_type='application/json',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            self.assertEqual(response.status_code, 200)
        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = 100 / total_time
        print(f"Temps total pour 100 requêtes : {total_time:.2f} secondes")
        print(f"Requêtes par seconde : {requests_per_second:.2f}")
        self.assertLess(total_time, 10.0)  

    def tearDown(self):
        """Nettoyage après chaque test."""
        user = CustomUser.objects.get(username='perfuser')
        if user.qr_code and default_storage.exists(user.qr_code.name):
            default_storage.delete(user.qr_code.name)
        Cart.objects.filter(user=self.user).delete()

if __name__ == '__main__':
    import unittest
    unittest.main()                          