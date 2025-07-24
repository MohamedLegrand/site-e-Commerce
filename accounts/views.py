from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, generate_qr_code
from django.core.mail import send_mail
from django.utils import timezone
import uuid

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            qr_data = f"UserID:{user.id},Points:{user.loyalty_points},Date:{timezone.now()}"
            generate_qr_code(qr_data, user, 'qr_code')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Identifiants incorrects.")
    return render(request, 'accounts/login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
        else:
            user = CustomUser.objects.create_user(username=username, email=email, password=password, role=role)
            qr_data = f"UserID:{user.id},Points:0,Date:{timezone.now()}"
            generate_qr_code(qr_data, user, 'qr_code')
            messages.success(request, "Inscription réussie. Connectez-vous.")
            return redirect('accounts:login')
    return render(request, 'accounts/register.html')

@login_required
def dashboard(request):
    user = request.user
    if user.loyalty_points >= 100:
        send_mail(
            'Réduction disponible !',
            'Vous avez atteint 100 points. Profitez de 10% de réduction !',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )
    return render(request, 'accounts/dashboard.html', {'user': user})

def user_logout(request):
    logout(request)
    return redirect('accounts:login')

def home(request):
    return render(request, 'accounts/home.html')