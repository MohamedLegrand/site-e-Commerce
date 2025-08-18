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
from .models import Product, Category
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
import base64
import qrcode
from io import BytesIO
from django.contrib.auth.hashers import make_password

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            qr_data = f"UserID:{user.id},Points:{user.loyalty_points},Date:{timezone.now()}"
            generate_qr_code(qr_data, user, 'qr_code')
            if user.role == 'gestionnaire':
                return redirect('accounts:manager_dashboard')
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
    if user.purchase_count >= 5:  # Ajusté pour utiliser purchase_count au lieu de loyalty_points
        send_mail(
            'Réduction disponible !',
            'Vous avez effectué 5 achats. Profitez de 10% de réduction !',
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
        print(f"Utilisateur : {request.user}")
        product = get_object_or_404(Product, id=product_id)
        print(f"Produit trouvé : {product}")
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        print(f"Données reçues : {data}")
        action = data.get('action', 'add')  # 'add', 'update', ou 'remove'
        quantity = int(data.get('quantity', 1))

        if quantity < 0:
            return JsonResponse({'status': 'error', 'message': 'Quantité invalide'}, status=400)

        if action == 'remove':
            Cart.objects.filter(user=request.user, product=product).delete()
            print(f"Produit {product.name} retiré du panier")
            message = 'Produit retiré du panier'
        else:
            cart, created = Cart.objects.get_or_create(user=request.user, product=product)
            print(f"Panier créé/modifié : {cart}, Créé : {created}")
            if action == 'update':
                cart.quantity = max(0, quantity)
            else:  # action == 'add'
                if created:
                    cart.quantity = quantity
                else:
                    cart.quantity += quantity
            cart.save()
            print(f"Panier sauvegardé : {cart.quantity}")
            message = 'Produit ajouté' if created else 'Quantité mise à jour'

        cart_items = Cart.objects.filter(user=request.user).values('product__name', 'quantity', 'product__price')
        total = sum(float(Decimal(str(item['product__price'])) * item['quantity']) for item in cart_items) if cart_items else 0

        return JsonResponse({
            'status': 'success',
            'message': message,
            'cart_items': list(cart_items),
            'total': total,
            'cart_item_count': cart_items.count()
        })
    except Product.DoesNotExist:
        print("Produit non trouvé")
        return JsonResponse({'status': 'error', 'message': 'Produit non trouvé'}, status=404)
    except json.JSONDecodeError:
        print("Données JSON invalides")
        return JsonResponse({'status': 'error', 'message': 'Données JSON invalides'}, status=400)
    except ValueError as e:
        print(f"Erreur de conversion : {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Quantité invalide'}, status=400)
    except Exception as e:
        print(f"Exception capturée : {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Erreur serveur : {str(e)}'}, status=500)

@login_required
@require_POST
def clear_cart(request):
    try:
        print(f"Utilisateur : {request.user}")
        Cart.objects.filter(user=request.user).delete()
        print("Panier vidé avec succès")
        return JsonResponse({
            'status': 'success',
            'message': 'Panier vidé avec succès',
            'cart_items': [],
            'total': 0.0,
            'cart_item_count': 0
        })
    except Exception as e:
        print(f"Exception capturée : {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Erreur serveur : {str(e)}'}, status=500)

@login_required
def cart_detail(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(float(item.product.price) * item.quantity for item in cart_items) if cart_items.exists() else 0

    if request.method == 'POST' and request.POST.get('action') == 'proceed_to_payment':
        if not cart_items.exists():
            messages.error(request, "Votre panier est vide.")
            return redirect('accounts:cart_detail')
        request.session['panier_total'] = total  # Stocker le total converti en float
        return redirect('accounts:payment_page')

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
        query = request.GET.get('term', '').strip()
        products = Product.objects.filter(name__icontains=query)[:10]  # Limite à 10 suggestions
        suggestions = [
            {
                'label': product.name,
                'value': product.name,
                'price': str(product.price),
                'image': product.image.url if product.image else ''
            } for product in products
        ]
        return JsonResponse(suggestions, safe=False)
    return JsonResponse([], safe=False)

def category_cosmetics(request):
    try:
        category = Category.objects.get(name="Parfumerie et produits cosmétiques")
        products = Product.objects.filter(category=category)
    except ObjectDoesNotExist:
        category = None
        products = Product.objects.none()
    return render(request, 'accounts/category_cosmetics.html', {'products': products, 'category_name': category.name if category else "Catégorie non trouvée"})

def add_product(request):
    product_name = request.POST.get('product_name', '')
    if request.method == 'POST' and product_name:
        if 'temp_products' not in request.session:
            request.session['temp_products'] = []
        request.session['temp_products'].append(product_name)
        request.session.modified = True
    return render(request, 'accounts/add_product.html', {'product_name': product_name, 'temp_products': request.session.get('temp_products', [])})

def search_product(request):
    query = request.GET.get('query', '')
    products = Product.objects.filter(name__icontains=query) if query else []
    return render(request, 'accounts/search_results.html', {'products': products, 'query': query})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseBadRequest


@login_required
def payment_page(request):
    total = request.session.get('panier_total', 0)
    user = request.user
    initial_data = {'nom': user.username, 'email': user.email, 'telephone': ''}

    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        type_paiement = request.POST.get('type_paiement')
        numero = request.POST.get('numero')

        if not all([nom, email, type_paiement, numero]):
            messages.error(request, "Tous les champs sont requis.")
            return render(request, 'accounts/payment_page.html', {'montant': total, 'initial_data': initial_data})

        if not numero.isdigit() or len(numero) < 9:
            messages.error(request, "Numéro de paiement invalide. Utilisez un numéro de 9 chiffres minimum.")
            return render(request, 'accounts/payment_page.html', {'montant': total, 'initial_data': initial_data})

        # Récupérer les items du panier avant de les vider
        cart_items = Cart.objects.filter(user=request.user).values('product__name', 'quantity', 'product__price')
        products = [{"name": item['product__name'], "quantity": item['quantity'], "price": float(item['product__price'])} for item in cart_items]

        user.purchase_count += 1
        user.total_sales += Decimal(str(total))
        user.save()

        print(f"Paiement simulé pour {nom}, Email: {email}, Type: {type_paiement}, Numéro: {numero}")
        messages.success(request, "Paiement simulé avec succès.")
        request.session['dernier_montant'] = total

        # Préparer les données pour la facture
        current_time = timezone.now()
        invoice_data = {
            'date': current_time.strftime('%Y-%m-%d'),
            'time': current_time.strftime('%H:%M:%S'),
            'products': products,
            'total': total,
            'user': user.username
        }

        # Générer le QR code
        qr_data = f"User: {user.username}, Total: {total} FCFA, Date: {invoice_data['date']}, Time: {invoice_data['time']}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()

        # Stocker les données dans la session et vider le panier
        request.session['invoice_data'] = invoice_data
        request.session['qr_code_image'] = qr_code_image
        Cart.objects.filter(user=request.user).delete()

        print(f"Invoice data: {request.session.get('invoice_data')}")
        print(f"QR code image: {request.session.get('qr_code_image')}")

        return redirect('accounts:invoice_view')

    return render(request, 'accounts/payment_page.html', {'montant': total, 'initial_data': initial_data})

@login_required
def invoice_view(request):
    invoice_data = request.session.get('invoice_data', {})
    qr_code_image = request.session.get('qr_code_image', '')
    if not invoice_data or not qr_code_image:
        messages.error(request, "Aucune donnée de facture disponible.")
        return redirect('accounts:dashboard')

    context = {
        'invoice_data': invoice_data,
        'qr_code_image': qr_code_image
    }
    del request.session['invoice_data']
    del request.session['qr_code_image']
    return render(request, 'accounts/invoice.html', context)

def payment_confirmation(request):
    dernier_montant = request.session.get('dernier_montant', 0)
    return render(request, 'accounts/payment_confirmation.html', {'montant': dernier_montant})



def milk(request):
    return render(request, 'accounts/milk.html')

def vin(request):
    return render(request, 'accounts/vin.html')

def parfum(request):
    return render(request, 'accounts/parfum.html')

def menage(request):
    return render(request, 'accounts/menage.html')

def montre(request):
    return render(request, 'accounts/montre.html')

def viande(request):
    return render(request, 'accounts/viande.html')

def snacks(request):
    return render(request, 'accounts/snacks.html')

def glassware(request):
    return render(request, 'accounts/glassware.html')


@login_required
def manager_dashboard(request):
    if request.user.role != 'gestionnaire':
        return render(request, 'accounts/access_denied.html', {'message': "Vous n'avez pas l'autorisation d'accéder à cette page."})
    products = Product.objects.all()[:5]  # Affiche les 5 premiers produits pour un aperçu
    return render(request, 'accounts/manager_dashboard.html', {'products': products})



@login_required
def manage_accounts(request):
    if request.user.role != 'gestionnaire':
        return render(request, 'accounts/access_denied.html', {'message': "Vous n'avez pas l'autorisation d'accéder à cette page."})
    users = CustomUser.objects.all()  # Récupère tous les utilisateurs
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        if username and email and password and role:
            if not CustomUser.objects.filter(username=username).exists():
                CustomUser.objects.create_user(username=username, email=email, password=make_password(password), role=role)
                messages.success(request, "Utilisateur ajouté avec succès.")
            else:
                messages.error(request, "Ce nom d'utilisateur existe déjà.")
        else:
            messages.error(request, "Tous les champs sont requis.")
    return render(request, 'accounts/manage_accounts.html', {'users': users})

@login_required
def manage_products(request):
    if request.user.role != 'gestionnaire':
        return render(request, 'accounts/access_denied.html', {'message': "Vous n'avez pas l'autorisation d'accéder à cette page."})
    return render(request, 'accounts/manage_products.html', {'message': 'Page de gestion des produits en cours de développement.'})

@login_required
def manage_rewards(request):
    if request.user.role != 'gestionnaire':
        return render(request, 'accounts/access_denied.html', {'message': "Vous n'avez pas l'autorisation d'accéder à cette page."})
    return render(request, 'accounts/manage_rewards.html', {'message': 'Page de gestion des récompenses en cours de développement.'})

@login_required
def manage_questions(request):
    if request.user.role != 'gestionnaire':
        return render(request, 'accounts/access_denied.html', {'message': "Vous n'avez pas l'autorisation d'accéder à cette page."})
    return render(request, 'accounts/manage_questions.html', {'message': 'Page de gestion des questions en cours de développement.'})


@login_required
def manage_products(request):
    if request.user.role != 'gestionnaire':
        return render(request, 'accounts/access_denied.html', {'message': "Vous n'avez pas l'autorisation d'accéder à cette page."})
    products = Product.objects.all()  # Récupère tous les produits
    if request.method == 'POST' and request.POST.get('action') == 'add':
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        if name and price and stock:
            Product.objects.create(name=name, price=Decimal(price), stock=stock)
            messages.success(request, "Produit ajouté avec succès.")
        else:
            messages.error(request, "Données invalides.")
    return render(request, 'accounts/manage_products.html', {'products': products})