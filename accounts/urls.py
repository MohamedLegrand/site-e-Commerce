from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),
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
]


    
