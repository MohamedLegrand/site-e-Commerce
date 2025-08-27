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
from django.http import HttpResponse
from weasyprint import HTML
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from .models import Order
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
import requests


def user_login(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            qr_data = f"UserID:{user.id},Points:{getattr(user, 'loyalty_points', 0)},Date:{timezone.now()}"
            generate_qr_code(qr_data, user, 'qr_code')
            role = getattr(user, 'role', 'client')  # Gère le cas où role n'existe pas
            return JsonResponse({
                'success': True,
                'role': role,
                'message': 'Connexion réussie'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Identifiants incorrects.'
            })
    # Gère les requêtes GET pour afficher le formulaire
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


from django.db import transaction

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

        # Calculer le total pour vérification
        calculated_total = sum(float(item['product__price']) * item['quantity'] for item in cart_items) if cart_items else 0

        # Vérifier que le total est cohérent
        if abs(calculated_total - total) > 0.01:
            messages.error(request, f"Erreur dans le calcul du total. Calculé: {calculated_total}, Session: {total}. Veuillez réessayer.")
            return render(request, 'accounts/payment_page.html', {'montant': total, 'initial_data': initial_data})

        # Mise à jour utilisateur
        with transaction.atomic():
            user.purchase_count += 1
            user.total_sales += Decimal(str(total))
            user.save()
            user.refresh_from_db()

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
            'user': user.username,
            'invoice_number': f'ECH-{current_time.strftime("%Y%m%d")}-{user.id}'
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

        # Stocker les données dans la session SANS les supprimer
        request.session['invoice_data'] = invoice_data
        request.session['qr_code_image'] = qr_code_image
        Cart.objects.filter(user=request.user).delete()

        print(f"Invoice data: {request.session.get('invoice_data')}")
        print(f"QR code image: {request.session.get('qr_code_image')}")

        # CHANGEMENT : Rediriger vers payment_confirmation au lieu de invoice
        return redirect('accounts:payment_confirmation')

    return render(request, 'accounts/payment_page.html', {'montant': total, 'initial_data': initial_data})



@login_required
def invoice_view(request):
    invoice_data = request.session.get('invoice_data', {})
    qr_code_image = request.session.get('qr_code_image', '')
    
    if not invoice_data or not qr_code_image:
        messages.error(request, "Aucune donnée de facture disponible.")
        return redirect('accounts:payment_confirmation')

    context = {
        'invoice_data': invoice_data,
        'qr_code_image': qr_code_image
    }
    
    # Rendre la page d'abord, puis nettoyer la session après
    response = render(request, 'accounts/view_invoice.html', context)
    return redirect('accounts:clear_invoice_session')

    
def payment_confirmation(request):
    dernier_montant = request.session.get('dernier_montant', 0)
    has_invoice_data = bool(request.session.get('invoice_data'))
    return render(request, 'accounts/payment_confirmation.html', {
        'montant': dernier_montant,
        'has_invoice_data': has_invoice_data
    })


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





@login_required
def delivery_dashboard(request):
    if request.user.role != 'delivery':  # Vérifie si l'utilisateur est un livreur
        return render(request, 'accounts/access_denied.html', {
            'message': "Vous n'avez pas l'autorisation d'accéder à cette page."
        })

    # Récupérer toutes les commandes des clients en attente
    pending_orders = Order.objects.filter(status='pending').order_by('-created_at')
    orders_to_deliver = []
    total_to_deliver = 0

    for order in pending_orders:
        order_total = 0
        items_data = []
        for item in order.items.all():  # related_name = 'items' dans OrderItem
            line_total = float(item.price) * item.quantity
            items_data.append({
                'product': item.product.name,
                'quantity': item.quantity,
                'total': line_total
            })
            order_total += line_total

        orders_to_deliver.append({
            'order_id': order.id,
            'client': order.user.username,
            'items': items_data,
            'order_total': order_total,
            'created_at': order.created_at
        })
        total_to_deliver += order_total

    # Gestion de l'envoi de message au gestionnaire
    message_sent = False
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            managers = CustomUser.objects.filter(role='gestionnaire')
            if managers.exists():
                email_subject = f"Message du livreur {request.user.username}"
                email_message = (
                    f"Message: {message}\n"
                    f"Envoyé par: {request.user.username} ({request.user.email})\n"
                    f"Date: {timezone.now()}"
                )
                from_email = 'from@example.com'  # Remplace par un email configuré dans settings.py
                recipient_list = [manager.email for manager in managers]

                try:
                    send_mail(email_subject, email_message, from_email, recipient_list, fail_silently=False)
                    message_sent = True
                    messages.success(request, "Message envoyé avec succès au gestionnaire.")
                except Exception as e:
                    messages.error(request, f"Erreur lors de l'envoi du message : {str(e)}")

    # Retourner la réponse avec render
    return render(request, 'accounts/delivery_dashboard.html', {
        'orders_to_deliver': orders_to_deliver,
        'total_to_deliver': total_to_deliver,
        'message_sent': message_sent
    })


    
from django.contrib.auth.decorators import login_required
from .models import CustomUser

@login_required
def manage_profil(request):
    if request.user.role != 'gestionnaire':
        return render(request, 'accounts/access_denied.html', {'message': "Vous n'avez pas l'autorisation d'accéder à cette page."})

    user = request.user
    context = {
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'purchase_count': user.purchase_count,
        'total_sales': user.total_sales,
        'loyalty_points': user.loyalty_points,
    }
    return render(request, 'accounts/manage_profil.html', context)


@login_required
def invoice(request):
    # Récupérer la dernière commande de l'utilisateur
    order = Order.objects.filter(user=request.user).order_by('-created_at').first()
    if not order:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Aucune commande trouvée'}, status=404)
        messages.error(request, "Aucune commande trouvée.")
        return redirect('accounts:dashboard')

    # Générer le QR code pour la commande
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"Commande #{order.id} - {request.user.username}")
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Construire les produits
    products_data = []
    for item in order.items.all():  # items = related_name de OrderItem
        products_data.append({
            'name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price),
        })

    invoice_data = {
        'invoice_number': order.id,
        'user': request.user.username,
        'date': order.created_at.strftime('%d/%m/%Y'),
        'time': order.created_at.strftime('%H:%M'),
        'products': products_data,
        'total': float(order.total),
    }

    # Réponse JSON pour la modale
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'invoice_data': invoice_data,
            'qr_code_image': qr_code_base64
        })

    # Page HTML classique
    context = {
        'invoice_data': invoice_data,
        'qr_code_image': qr_code_base64
    }
    return render(request, 'accounts/invoice.html', context)


@login_required
def download_invoice(request):
    invoice_data = request.session.get('invoice_data', {})
    qr_code_image = request.session.get('qr_code_image', '')

    if not invoice_data or not qr_code_image:
        messages.error(request, "Aucune donnée de facture disponible.")
        return redirect('accounts:dashboard')

    # Créer le PDF avec ReportLab
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_echop_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.textColor = colors.red
    normal_style = styles['BodyText']

    # Ajouter le titre
    elements.append(Paragraph("Facture Echop", title_style))
    elements.append(Paragraph(f"Date: {invoice_data['date']} à {invoice_data['time']}", normal_style))
    elements.append(Paragraph(f"Client: {invoice_data['user']}", normal_style))
    elements.append(Paragraph("<br/><br/>", normal_style))

    # Tableau des produits
    data = [['Produit', 'Quantité', 'Prix unitaire (FCFA)', 'Total (FCFA)']]
    total = 0
    for product in invoice_data['products']:
        row_total = product['quantity'] * product['price']
        data.append([
            product['name'],
            str(product['quantity']),
            f"{product['price']:.2f}",
            f"{row_total:.2f}"
        ])
        total += row_total
    data.append(['', '', 'Total', f"{total:.2f}"])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    # Ajouter le QR code
    from reportlab.graphics.shapes import Image
    qr_image_data = base64.b64decode(qr_code_image)
    from io import BytesIO
    qr_image = BytesIO(qr_image_data)
    elements.append(Paragraph("QR Code:", normal_style))
    elements.append(Image(qr_image, width=100, height=100))

    # Construire le PDF
    doc.build(elements)

    # CHANGEMENT : Ne pas supprimer les données de session ici
    # Les données restent disponibles pour d'autres utilisations
    
    return response



# NOUVELLE FONCTION : Pour nettoyer la session après utilisation
@login_required
def clear_invoice_session(request):
    """Vue pour nettoyer les données de facture de la session"""
    if 'invoice_data' in request.session:
        del request.session['invoice_data']
    if 'qr_code_image' in request.session:
        del request.session['qr_code_image']
    if 'dernier_montant' in request.session:
        del request.session['dernier_montant']
    
    return JsonResponse({'status': 'success', 'message': 'Session nettoyée'})



def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Récupérer des données pour le tableau de bord
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'title': 'Tableau de bord Administrateur'
    }
    return render(request, 'accounts/admin_dashboard.html', context)



def verify_qr(request, user_id):
    # Récupérer l'utilisateur avec l'ID fourni
    user = get_object_or_404(User, id=user_id)
    
    # Préparer les données à afficher
    context = {
        'user': user,
        'username': user.username,
        'email': user.email if user.email else 'Non défini',
        'date_joined': user.date_joined.strftime('%B %Y'),
    }
    
    return render(request, 'accounts/verify_qr.html', context)



@login_required
def delivery_map(request):
    # Récupérer les commandes en attente
    pending_orders = Order.objects.filter(status='pending').order_by('-created_at')
    clients = []
    for order in pending_orders:
        address = order.client_address  # Champ adresse du client
        latitude, longitude = get_coordinates(address)
        if latitude and longitude:
            clients.append({
                'client_name': order.user.username,
                'address': address,
                'latitude': latitude,
                'longitude': longitude
            })

    context = {
        'city_name': "Yaoundé, Cameroun",
        'clients': clients
    }
    return render(request, 'accounts/delivery_map.html', context)

def get_coordinates(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "EchopDeliveryApp/1.0 (your_email@example.com)"  # Remplace par ton email
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data["lat"]), float(data["lon"])
    else:
        print(f"Erreur : {response.status_code}, {response.text}")
        return None, None
    


@login_required
def delivery_orders(request):
    # Filtrer les commandes en attente assignées au livreur connecté
    orders_to_deliver = Order.objects.filter(status='en_attente', delivery_person=request.user).order_by('-created_at')
    total_to_deliver = sum(order.total for order in orders_to_deliver if order.total is not None)
    current_date = timezone.now().strftime("%d/%m/%Y %H:%M")

    context = {
        'orders_to_deliver': orders_to_deliver,
        'total_to_deliver': total_to_deliver,
        'current_date': current_date
    }
    return render(request, 'accounts/delivery_orders.html', context)
