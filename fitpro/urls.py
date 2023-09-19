"""
URL configuration for fitpro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from product import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('product.urls')),
    path('cadmin/', include('cadmin.urls')),
    path('add-to-cart', views.add_to_cart, name='add_to_cart'),
    path('add-to-wishlist', views.add_to_wishlist, name='add_to_wishlist'),  
    
    path('update-cart-quantity', views.update_cart_quantity, name='update_cart_quantity'), 
    path('get-cart-summary', views.get_cart_summary, name='get_cart_summary'), 

]

urlpatterns= urlpatterns + static(settings.MEDIA_URL, document_root =settings.MEDIA_ROOT)
