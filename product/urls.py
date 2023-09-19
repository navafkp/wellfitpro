from django.urls import path
from . import views

urlpatterns = [
    path('shop/', views.shop, name='shop'),
    path('productdetail/', views.productdetail, name='productdetail'),
    path('category/', views.category, name='category'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.check_out, name = 'check_out'),
    path('paymentmode/<int:id>/', views.payment_mode, name = 'payment_mode'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('order-placed/', views.order_placed, name = 'order_placed'),
    path('save-payment/', views.save_payment, name='save_payment'),
    path('success', views.success, name='success'),
    path('add-review/', views.add_review, name='add_review'), 
       
]