from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, generate_qr_code, Product, Cart
from django.core.mail import send_mail
from django.utils import timezone
import json
from django.views.decorators.http import require_POST

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
        role = request.POST.get('role', 'client')
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
            fail_silently=True,
        )
    return render(request, 'accounts/dashboard.html', {'user': user})

@login_required
def page_principale(request):
    cart_items = Cart.objects.filter(user=request.user)
    cart_item_count = cart_items.count()
    products = Product.objects.all()[:4]
    return render(request, 'accounts/page_principale.html', {
        'cart_item_count': cart_item_count,
        'products': products,
    })

@login_required
def products(request):
    products = Product.objects.all()
    cart_items = Cart.objects.filter(user=request.user)
    cart_item_count = cart_items.count()
    return render(request, 'accounts/products.html', {
        'products': products,
        'cart_item_count': cart_item_count,
    })

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Votre panier est vide.")
        return redirect('accounts:products')
    cart_items.delete()
    messages.success(request, "Commande passée avec succès !")
    return redirect('accounts:dashboard')

def user_logout(request):
    logout(request)
    return redirect('accounts:login')

def home(request):
    return render(request, 'accounts/home.html')

def product_list(request):
    return render(request, 'accounts/products.html')

def contact(request):
    return render(request, 'accounts/contact.html')

def about(request):
    return render(request, 'accounts/about.html')

def terms(request):
    return render(request, 'accounts/terms.html')

def sold_products(request):
    return render(request, 'accounts/sold_products.html')

def category_cake(request):
    product_names = [
        'Pain au Levain', 'Pain de Campagne', 'Baguette Tradition', 'Pain aux Céréales',
        'Pain Complet', 'Pain aux Noix (Pain)', 'Pain aux Olives', 'Pain de Seigle',
        'Pain aux Raisins (Pain)', 'Pain Brioché', 'Pain aux Graines',
        'Gâteau au Chocolat', 'Gâteau aux Fruits', 'Gâteau à la Vanille',
        'Gâteau au Citron', 'Gâteau aux Amandes', 'Gâteau Red Velvet',
        'Gâteau à la Noix de Coco', 'Gâteau aux Fraises', 'Gâteau au Caramel',
        'Gâteau aux Noisettes', 'Pain au Chocolat', 'Croissant Beurre',
        'Chausson aux Pommes', 'Pain aux Raisins (Viennoiserie)', 'Brioche Nature',
        'Pain Suisse', 'Croissant aux Amandes', 'Pain au Lait',
        'Chou à la Crème', 'Brioche aux Pralines', 'Pain aux Noix (Viennoiserie)'
    ]
    products = Product.objects.filter(name__in=product_names)
    pains = products.filter(name__in=product_names[:11])
    gateaux = products.filter(name__in=product_names[11:21])
    viennoiseries = products.filter(name__in=product_names[21:])
    cart_items = Cart.objects.filter(user=request.user)
    cart_item_count = cart_items.count()
    return render(request, 'accounts/category_cake.html', {
        'pains': pains,
        'gateaux': gateaux,
        'viennoiseries': viennoiseries,
        'cart_item_count': cart_item_count
    })

def category_clothing(request):
    return render(request, 'accounts/category_clothing.html')

def category_alimentaire(request):
    return render(request, 'accounts/category_alimentaire.html')

@login_required
@require_POST
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body) if request.body else {}
        quantity = int(data.get('quantity', 1))
        if quantity < 1:
            return JsonResponse({'status': 'error', 'message': 'Quantité invalide'}, status=400)
        cart, created = Cart.objects.get_or_create(user=request.user, product=product)
        cart.quantity += quantity
        cart.save()
        cart_items = Cart.objects.filter(user=request.user).values('product__name', 'quantity', 'product__price')
        total = sum(item['product__price'] * item['quantity'] for item in cart_items)
        return JsonResponse({
            'status': 'success',
            'message': 'Produit ajouté au panier',
            'cart_items': list(cart_items),
            'total': total,
            'cart_item_count': cart_items.count()
        })
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Produit non trouvé'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def cart_detail(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart/detail.html', {'cart_items': cart_items, 'total': total})



@login_required
def profil_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        user = request.user
        if username:
            user.username = username
        if email:
            user.email = email
        if password and password == password_confirm:
            user.set_password(password)
        elif password and password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('accounts:profil')

        user.save()
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect('accounts:profil')

    return render(request, 'accounts/profil.html')



def product_autocomplete(request):
    if 'term' in request.GET:
        query = request.GET.get('term')
        products = Product.objects.filter(name__icontains=query)[:10]  # Limite à 10 suggestions
        suggestions = [product.name for product in products]
        return JsonResponse(suggestions, safe=False)
    return JsonResponse([], safe=False)