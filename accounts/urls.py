from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name = 'accounts'

urlpatterns = [ 
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('checkout/', views.checkout, name='checkout'),
    path('logout/', views.user_logout, name='logout'),
    path('page_principale/', views.page_principale, name='page_principale'),



    path('products/', views.products, name='products'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('sold-products/', views.sold_products, name='sold_products'),

    # Routes pour les catégories
    path('category/cake/', views.category_cake, name='category_cake'),
    path('category/clothing/', views.category_clothing, name='category_clothing'),
    path('category/alimentaire/', views.category_alimentaire, name='category_alimentaire'),



    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),



    path('profil/', views.profil_view, name='profil'),
   

    path('product-autocomplete/', views.product_autocomplete, name='product_autocomplete'),
    path('category/cosmetics/', views.category_cosmetics, name='category_cosmetics'),


    path('add_product/', views.add_product, name='add_product'),

    path('search_product/', views.search_product, name='search_product'),

    path('clear_cart/', views.clear_cart, name='clear_cart'),

    path('payer/', views.payment_page, name='payment_page'),

    path('payment_confirmation/', views.payment_confirmation, name='payment_confirmation'),

   



    path('milk', views.milk, name='milk'),
    path('vin', views.vin, name='vin'),
    path('parfum', views.parfum, name='parfum'),
    path('menage', views.menage, name='menage'),
    path('montre', views.montre, name='montre'),
    path('viande', views.viande, name='viande'),
    path('snacks', views.snacks, name='snacks'),
    path('glassware', views.glassware, name='glassware'),


    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manage_accounts/', views.manage_accounts, name='manage_accounts'),
    path('manage_products/', views.manage_products, name='manage_products'),
    path('manage_rewards/', views.manage_rewards, name='manage_rewards'),
    path('manage_questions/', views.manage_questions, name='manage_questions'),


    path('delivery_dashboard/', views.delivery_dashboard, name='delivery_dashboard'),

    path('manage_profil/', views.manage_profil, name='manage_profil'),

    path('invoice/', views.invoice, name='invoice'),
    path('download_invoice/', views.download_invoice, name='download_invoice'),
    path('clear_invoice_session/', views.clear_invoice_session, name='clear_invoice_session'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('verify-qr/<int:user_id>/', views.verify_qr, name='verify_qr'),

    path('delivery_map/', views.delivery_map, name='delivery_map'),
    path('delivery_orders/', views.delivery_orders, name='delivery_orders'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),  # Nouvelle URL
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),  # Nouvelle URL


    path('recommandations/', views.recommandations, name='recommandations'),
    path('purchase_history/', views.purchase_history, name='purchase_history'),
    path('checkout/', views.checkout, name='checkout'),

   


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    
