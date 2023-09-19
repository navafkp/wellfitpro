from django.contrib import admin
from .models import Category, FitProduct, Coupon, Offer
# Register your models here.

admin.site.register(Category)
admin.site.register(FitProduct)
admin.site.register(Coupon)
admin.site.register(Offer)