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
    path('detail/', views.cart_detail, name='detail'),

    path('product-autocomplete/', views.product_autocomplete, name='product_autocomplete'),
    path('category/cosmetics/', views.category_cosmetics, name='category_cosmetics'),


    path('add_product/', views.add_product, name='add_product'),

    path('search_product/', views.search_product, name='search_product'),

    path('clear_cart/', views.clear_cart, name='clear_cart'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    
