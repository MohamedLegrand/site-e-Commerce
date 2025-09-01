from django.db import models
from django.contrib.auth.models import AbstractUser
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('seller', 'Commerçant'),
        ('livreur', 'Livreur'),
        ('admin', 'Admin'),
        ('gestionnaire', 'Gestionnaire'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='client')
    loyalty_points = models.IntegerField(default=0)
    purchase_count = models.PositiveIntegerField(default=0)  # Nouveau champ pour le nombre d'achats
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Nouveau champ pour le total cumulé
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Nouveau champ pour le numéro de téléphone
    address = models.CharField(max_length=255, blank=True, null=True)      # Nouveau champ pour l'adresse

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',
        blank=True,
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
    )

    def __str__(self):
        return self.username

class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)  # Nouveau champ pour l'image
    
    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Empêche plusieurs entrées pour le même utilisateur et produit
        indexes = [
            models.Index(fields=['user', 'product']),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

def generate_qr_code(data, model_instance, field_name):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    file_name = f'{field_name}_{model_instance.id}.png'
    model_instance.__setattr__(field_name, File(buffer, name=file_name))
    model_instance.save()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=(('en_attente', 'En attente'), ('en_livraison', 'En livraison'), ('livree', 'Livrée')), default='en_attente')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    client_address = models.CharField(max_length=255, default='Adresse par défaut')

    def assign_delivery_person(self):
        from django.db.models import Q
        available_delivery_person = CustomUser.objects.filter(role='livreur', is_active=True).first()
        if available_delivery_person and not self.delivery_person:
            self.delivery_person = available_delivery_person
            self.save()

    def __str__(self):
        return f"Commande {self.id} de {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # prix au moment de l'achat   

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Commande {self.order.id})"