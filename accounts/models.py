from django.db import models
from django.contrib.auth.models import AbstractUser
import qrcode
from io import BytesIO
from django.core.files import File
from django.shortcuts import render

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('seller', 'Commerçant'),
        ('delivery', 'Livreur'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    loyalty_points = models.IntegerField(default=0)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups',  # Nom unique
        blank=True,
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',  # Nom unique
        blank=True,
        help_text='Specific permissions for this user.',
    )

    def __str__(self):
        return self.username

def generate_qr_code(data, model_instance, field_name):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    file_name = f'{field_name}_{model_instance.id}.png'
    model_instance.__setattr__(field_name, file_name)
    model_instance.save()
    return File(buffer, name=file_name)

def home(request):
       return render(request, 'accounts/home.html')
