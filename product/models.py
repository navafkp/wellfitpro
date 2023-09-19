from django.db import models
from django.utils.text import slugify
from django.utils import timezone

from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='ctgy_img')
    is_featured = models.BooleanField(default = False)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.name
    
    
class FitProduct(models.Model):
    name = models.CharField(max_length=80)
    description = models.TextField()
    short_description = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits = 10, decimal_places=2)
    is_featured = models.BooleanField(default=False)
    tag = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    stock = models.IntegerField()
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    is_sale = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default = False)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(FitProduct, self).save(*args, **kwargs)
    
    def __str__(self) -> str:
        return self.name
    
    
class ProductImage(models.Model):
    product = models.ForeignKey(FitProduct, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="pdt_img")
    
    
    def __str__(self) -> str:
        return f"Image of {self.product.name}"
    

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField( default=timezone.now)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    def __str__(self) -> str:
        return self.user

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, default=9999)
    product = models.ForeignKey(FitProduct, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self) -> str:
        return self.product.name
    
    
class WishList(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at=  models.DateTimeField( default=timezone.now)

    def __str__(self) -> str:
        return self.user
    
class WishListItem(models.Model):
    wishlist = models.ForeignKey(WishList, on_delete=models.CASCADE, default = 9999)
    product = models.ForeignKey(FitProduct, on_delete=models.CASCADE)
    def __str__(self) -> str:
        return self.product.name
    
class Order(models.Model):
    
    STATUS_CHOICES = (
        (1, 'Order Initiated'),
        (2, 'Order Processing'),
        (3, 'Shipped'),
        (4, 'Delivered'),
    )
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    billing_email = models.CharField(default="None")
    billing_address1 = models.CharField(default="None")
    billing_address2 = models.CharField(default="None")
    billing_city = models.CharField(default="None")
    billing_state = models.CharField(default="None")
    billing_country = models.CharField(default="None")
    
    created_at = models.DateTimeField( default=timezone.now)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category_offer_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category_offer_name = models.TextField(null=True)
    refferal_offer = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_charge = models.DecimalField( max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(default="None")
    total_amout = models.DecimalField( max_digits=10, decimal_places=2, default=0.00)
    is_shipping = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.user.email
    
    
    
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(FitProduct, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField()
    
    def __str__(self) -> str:
        return self.product.name
    
    
class ShippingAddress(models.Model):
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    addressline1 = models.CharField(max_length=255)
    addressline2 = models.CharField(max_length=255)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    country = models.CharField(max_length=80)
    pin = models.IntegerField()
    def __str__(self) -> str:
        return f"{self.order.id} for {self.order.billing_email}"
    
class Coupon(models.Model):
    name = models.CharField(max_length=50)
    count = models.IntegerField()
    expired_date = models.DateField()
    discount_price  =models.CharField(max_length=30)
    is_percentage = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.name
    
    
class UsedCoupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    
    
class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razor_pay_order_id = models.CharField(max_length=100)
    razor_pay_payment_id = models.CharField(max_length=100)
    razor_pay_payment_signature = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        return self.order.id






   

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_credit = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self) -> str:
        return self.user.first_name
    
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(FitProduct, on_delete=models.CASCADE)
    comment = models.TextField()
    rate = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return str(self.id)
    
    
class Offer(models.Model):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    expired_date = models.DateField()
    discount_price  =models.CharField(max_length=30)
    is_percentage = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return self.name
    
    
    