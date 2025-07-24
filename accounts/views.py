from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, generate_qr_code, Product
from django.core.mail import send_mail
from django.utils import timezone
import uuid

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            qr_data = f"UserID:{user.id},Points:{user.loyalty_points},Date:{timezone.now()}"
            generate_qr_code(qr_data, user, 'qr_code')
            return redirect('accounts:page_principale')
        else:
            messages.error(request, "Identifiants incorrects.")
    return render(request, 'accounts/login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'client')  # Par défaut 'client' si non fourni
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
            fail_silently=True,  # Évite les erreurs si email non configuré
        )
    return render(request, 'accounts/dashboard.html', {'user': user})

@login_required
def page_principale(request):
    cart = request.session.get('cart', {})
    cart_item_count = sum(cart.values()) if cart else 0
    products = Product.objects.all()[:4]  # Affiche 4 produits en avant
    return render(request, 'accounts/page_principale.html', {
        'cart_item_count': cart_item_count,
        'products': products,
    })

@login_required
def products(request):
    products = Product.objects.all()
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if product_id and Product.objects.filter(id=product_id).exists():
            cart[product_id] = cart.get(product_id, 0) + 1
            request.session['cart'] = cart
            messages.success(request, "Produit ajouté au panier !")
        else:
            messages.error(request, "Produit invalide.")
        return redirect('accounts:products')
    return render(request, 'accounts/products.html', {
        'products': products,
        'cart': cart,
    })

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Votre panier est vide.")
        return redirect('accounts:products')
    # Logique de commande à implémenter (ex. : sauvegarde dans une table Order)
    del request.session['cart']
    messages.success(request, "Commande passée avec succès !")
    return redirect('accounts:dashboard')

def user_logout(request):
    logout(request)
    return redirect('accounts:login')

def home(request):
    return render(request, 'accounts/home.html')


def products(request):
    return render(request, 'accounts/products.html')

def contact(request):
    return render(request, 'accounts/contact.html')

def about(request):
    return render(request, 'accounts/about.html')

def terms(request):
    return render(request, 'accounts/terms.html')

def sold_products(request):
    return render(request, 'accounts/sold_products.html')

# Catégories
def category_cake(request):
    return render(request, 'accounts/category_cake.html')

def category_clothing(request):
    return render(request, 'accounts/category_clothing.html')

def category_alimentaire(request):
    return render(request, 'accounts/category_alimentaire.html')

 