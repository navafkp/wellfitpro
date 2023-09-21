from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
from .models import FitProduct, Category, ProductImage, Cart, CartItem, Order, OrderItem, ShippingAddress, WishList, WishListItem, Coupon, UsedCoupon,Payment, Wallet, Review, Offer
from accounts.models import State, Country, Address
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()
from django. contrib import messages
from decimal import Decimal, ROUND_HALF_UP
import razorpay
from django.http import JsonResponse
from django.conf import settings
import smtplib  
from decouple import config  

# index/home
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def home(request):
    # fetching category, offers and product detail for showing in index page
    ctgy = Category.objects.filter(Q(is_featured = True) & Q(is_deleted = False))
    offers = Offer.objects.filter(category__isnull=False, is_active = True).select_related('category')
    pdt = FitProduct.objects.filter(
        is_featured = True,
        is_active = True, 
        is_deleted = False
        ).prefetch_related('productimage_set')
    data = []    
    offer_dispaly = []
    # checking is there any offer price for each product based on category offer(offers from offer table used to check) or product offer(sale price)
    for product in pdt:
        cat_id=product.category.id
        cat_offer = Offer.objects.filter(category_id=cat_id, is_active = True).values('name', 'discount_price', 'is_active', 'is_percentage')
        price=product.sale_price
        price_discount = 0
        if cat_offer:
            discount_price = int(cat_offer[0]['discount_price'])
            if cat_offer[0]['is_percentage']:
                price_discount = price*discount_price/100
            else:
                price_discount = discount_price
            price-= price_discount
            offer_dispaly.append({
                'id':product.id,
                'display':cat_offer[0]['name'],
            })
        data.append({
            'id':product.id,
            'product_price_withoffer':price,
        })
                      
    context = {
        'ctgy':ctgy,
        'pdt':pdt,
        'offers':offers,
        'data':data,
        'offer_dispaly':offer_dispaly,
    }
    return render(request, 'product/index.html', context)

# shop page
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def shop(request):
    check_box_selection = ""
    box = []
   
    price_filter_value = None
    category_value_input = request.GET.get('offer')
    featured = request.GET.get('featured')
    min_price = request.GET.get('min')
    max_price = request.GET.get('max')
    user_input_search = request.GET.get('product')
    # filter product based on category offer
    if category_value_input:
        cat_offer = Offer.objects.get(id=category_value_input)
        category = cat_offer.category_id
        cat_obj = Category.objects.get(id=category)
        pdt = FitProduct.objects.filter(Q(category=cat_obj)& Q(is_active=True)).filter(is_deleted = False).prefetch_related('productimage_set')             
    # filter shop with min and max price
    elif min_price and max_price:
        user_input_category = request.GET.getlist('cat', [])
        for categoryID in user_input_category:
            categoryID = int(categoryID)
            box.append(categoryID)
        if not user_input_category:
            pdt = FitProduct.objects.filter(Q(price__gte=min_price) & Q(price__lte=max_price) & Q(is_active=True)).filter(is_deleted = False).prefetch_related('productimage_set')
        else:
            pdt = FitProduct.objects.filter(Q(category__in=user_input_category) & Q(price__gte=min_price) & Q(price__lte=max_price) & Q(is_active=True)).filter(is_deleted = False).prefetch_related('productimage_set')
    
    # filter product based on featured product
    elif featured:
        check_box_selection = featured
        pdt = FitProduct.objects.filter(Q(is_featured = True) & Q(is_active=True)).filter(is_deleted = False).prefetch_related('productimage_set')
    # search product with a user input coming from header section 
    elif user_input_search:
        user_input_search = user_input_search.strip()
        pdt_container =  FitProduct.objects.filter(Q(name__icontains=user_input_search) & Q(is_active = True)).filter(is_deleted = False)
        if pdt_container:
            pdt = pdt_container
        else:
            pdt = pdt_container
            messages.info(request, f"There is no product with this name '{user_input_search}'")
            
    #  filter product with high low price  
    elif request.GET.get('myselect') == 'high-low':
        price_filter_value = 'high-low'
        pdt = FitProduct.objects.order_by('-price').filter(is_deleted = False)
    # filter product with low high price
    elif request.GET.get('myselect') == 'low-high':
        price_filter_value = 'low-high'
        pdt = FitProduct.objects.order_by('price').filter(is_deleted = False)
    else:
        pdt = FitProduct.objects.filter(is_active=True).filter(is_deleted = False).prefetch_related('productimage_set')
         
    ctgy = Category.objects.filter(is_deleted = False)    
    data = []
    offer_dispaly = []
    for product in pdt:
        cat_id=product.category.id
        cat_offer = Offer.objects.filter(category_id=cat_id, is_active = True).values('name', 'discount_price', 'is_active', 'is_percentage')
        price=product.sale_price
        price_discount = 0
        if cat_offer:
            discount_price = int(cat_offer[0]['discount_price'])
            if cat_offer[0]['is_percentage']:
                price_discount = price*discount_price/100
            else:
                price_discount = discount_price
            price-= price_discount
           
            offer_dispaly.append({
                'id':product.id,
                'display':cat_offer[0]['name'],
            })
        data.append({
            'id':product.id,
            'product_price_withoffer':price,
        })   
 
    context = {
        'pdt': pdt,
        'ctgy':ctgy,
        'min_price': min_price,
        'max_price':max_price,
        'price_filter_value':price_filter_value,
        'offer_dispaly':offer_dispaly,
        'check_box_selection':check_box_selection,
        'data':data,
        'box':box,
    }
    
    return render(request, 'product/shop.html', context)

# product detail page
def productdetail(request):
    input_product_slug = request.GET.get('prodct')
    if input_product_slug:
        pdt = FitProduct.objects.filter(Q(slug=input_product_slug) & Q(is_active=True)).select_related('category').prefetch_related('productimage_set')
        data = FitProduct.objects.filter(Q(category=pdt[0].category)  & Q(is_active=True)).filter(is_deleted = False).exclude(slug=input_product_slug).prefetch_related('productimage_set')
        pdt_description = pdt[0].description.strip()
        cat_id = pdt[0].category.id
        p_p = pdt[0].sale_price
        category_obj = Category.objects.get(id=cat_id)
        cat_offer = Offer.objects.filter(category=category_obj, is_active = True).values('name', 'discount_price', 'is_active', 'is_percentage')
        price_discount = 0
        if cat_offer:  
            discount_price = int(cat_offer[0]['discount_price'])
            if cat_offer[0]['is_percentage']:
                price_discount = p_p*discount_price/100
            else:
                price_discount = discount_price
            p_p -= price_discount
        review_set = Review.objects.filter(product=pdt[0].id).values('comment','user_id', 'created_at', 'rate')
        for i in review_set:
            user_id=i['user_id']
            user_obj = User.objects.get(id=user_id)
        context = {
            'pdt':pdt,
            'data':data,
            'product_price_withoffer':p_p,
            'pdt_description': pdt_description,
            'review_set':review_set,
        }
        return render(request, 'product/productdetail.html', context)
    else:
        return render(request, 'product/shop.html', context)
    
# category page
def category(request):
    ctgy = Category.objects.filter(is_deleted=False).order_by('-id')
    context = {
        'ctgy':ctgy
    }
    return render(request, 'product/categories.html', context)

def add_to_cart(request): 
    cart_it = {}
    cart_it[str(request.GET['id'])]={
         'id':request.GET['id'],
         'qty':1,      
    }
    product_id=request.GET['id']
    product = FitProduct.objects.get(id=product_id)
    cart_data = request.session.get('cartdata', {})
    email = request.session.get('email', None)
    # if email in session, while adding item to cart, we consider all procut detail from cart_data session and update cartitem table also
    if email:
        user = User.objects.get(email=email)    
        cart, created = Cart.objects.get_or_create(user=user)
        existing_cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        if existing_cart_item:
            # Item already exists, update the quantity
            if existing_cart_item.quantity < product.stock:
                existing_cart_item.quantity += 1
                existing_cart_item.save()
                if cart_data: 
                    if str(product_id) in cart_data:
                        if int(cart_data[str(product_id)]['qty']) < product.stock:
                        
                            cart_data[str(product_id)]['qty'] = int(cart_data[str(product_id)]['qty'])+int(1)
                            cart_data.update(cart_data)
                            request.session['cartdata']=cart_data
                    else:
                        cart_data[str(product_id)] = {'qty': 1}
                        request.session['cartdata'] = cart_data
                else:
                    request.session['cartdata'] = cart_it         
            else:
                messages.info(request, "out of stock, cannot add to cart")         
        else:
            CartItem.objects.create(cart = cart,product = product,quantity = 1)
            if cart_data:   
                if str(product_id) in cart_data:
                    cart_data[int(product_id)]['qty']+=1
                    cart_data.update(cart_data)
                    request.session['cartdata'] = cart_data 
                else:
                    cart_data[str(product_id)] = {'qty': 1}
                    request.session['cartdata'] = cart_data        
            else:
                request.session['cartdata'] = cart_it               
    # if email not in session, we only focus on cartdata
    elif 'cartdata' in request.session:
        if str(product_id) in cart_data:
            if int(cart_data[str(product_id)]['qty']) < product.stock:
                cart_data[str(product_id)]['qty'] = int(cart_data[str(product_id)]['qty'])+int(1)
                cart_data.update(cart_data)
                request.session['cartdata']=cart_data
            else:
                messages.info(request, "out of stock, cannot add to cart")   
        else:     
            cart_data[str(product_id)] = {'qty': 1}
            request.session['cartdata'] = cart_data       
    #  if both cart_data and email not in session, while adding first item to cart, this case work  
    else:
        request.session['cartdata'] = cart_it     
    request.session['total_cart'] = len(request.session['cartdata'])
    request.session.save()
    return JsonResponse({'totallist': request.session['total_cart']})

def cart(request):
        
    email = request.session.get('email', None)
    cart_data = request.session.get('cartdata', {})
    if email:
        user = User.objects.get(email=email)     
    
    if request.GET.get('cartdel'):
        product_id = str(request.GET['cartdel'])
        if email:
            # Retrieve cart items for logged-in user from the database
            if user:
                onecart = Cart.objects.get(user = user)
                data = CartItem.objects.filter(cart=onecart, product_id = product_id).first()
                if data:
                    data.delete()
                    if str(product_id) in cart_data:
                        cart_data.pop(product_id)
                        request.session['cartdata'] = cart_data 
                    if 'total_cart' in request.session:
                            cart_number = request.session.get('total_cart')
                            cart_number = cart_number-1
                            request.session['total_cart'] = cart_number
                            request.session.save()
        else:    
            if str(product_id) in cart_data:
                cart_data.pop(product_id)
                request.session['cartdata'] = cart_data
                if 'total_cart' in request.session:
                    cart_number = request.session['total_cart']
                    cart_number = cart_number-1
                    request.session['total_cart'] = cart_number
                    request.session.save()
      
    cart_total = int(0)
    cart_items_list = []
    tax = 0  
    order_data = []
    discount = 0
    grant_total = 0
    order_sum = {}
    applied_referral = 0
    data = []
    # show all data if user logged in
    if email:
        cart, created = Cart.objects.get_or_create(user=user)
        if user:
            cart_items = CartItem.objects.filter(cart=cart).select_related('product')
            price_discount = 0   
            cat_offer = []
            for item in cart_items:
                qty = item.quantity  
                p_p = int(item.product.sale_price )
                cat_id = item.product.category_id
                category_obj = Category.objects.get(id=cat_id)
                cat_offer = Offer.objects.filter(category=category_obj, is_active = True).values('name', 'discount_price', 'is_active', 'is_percentage')
                if cat_offer:
                    discount_price = int(cat_offer[0]['discount_price'])
                    if cat_offer[0]['is_percentage']:
                        price_discount = p_p*discount_price/100
                    else:
                        price_discount = discount_price
                    p_p -= price_discount
                total_price = qty * p_p
                data.append({
                    'id':item.product.id,
                    'product_price_withoffer':p_p,
                })
                cart_total += total_price   
                product = item.product
                images = ProductImage.objects.filter(product_id=product.id).first()
                image = None
                if images:
                    image = images.image.url
            
                cart_items_list.append({
                    'product': product,
                    'qty': qty,
                    'img':image,
                    
                    'total_price': total_price,
                })
        # checking whether the user is reffered and is it his first order
        order_data = Order.objects.filter(user=user).first()
        if user.is_referred:
            if not order_data:
                first_offer = Offer.objects.filter(name='referral_offer', is_active=True).values('discount_price', 'is_percentage', 'is_active').first()
                if first_offer:
                    percentage = first_offer['is_percentage']
                    active = first_offer['is_active']
                    if active:
                        if percentage:
                            applied_referral = cart_total*20/100               
        tax = cart_total*10/100
        shipping=100
        grant_total = cart_total-applied_referral+tax+shipping    
        order_sum={
            'cart total':cart_total,
            'discount':discount,
            'tax':tax,
            'shipping':shipping,
            'refferal':applied_referral,
            'grant total':grant_total,    
        }  
        request.session['order_sum'] =order_sum
        request.session.save()
    # show all data if user not logged in, using cart_data
    elif 'cartdata' in request.session:
        for item_id, item_data in cart_data.items():
            price_discount = 0   
            cat_offer = []
            product = FitProduct.objects.filter(id=int(item_id)).first()
            product_image = ProductImage.objects.filter(product_id=product.id).first()        
            if product:
                image = None
                if product_image:
                    image = product_image.image.url          
            qty = int(item_data['qty'])
            cat_id = product.category_id
            category_obj = Category.objects.get(id=cat_id)
            p_p = float(product.sale_price)  
            cat_offer = Offer.objects.filter(category=category_obj, is_active=True).values('name', 'discount_price', 'is_active', 'is_percentage')
            if cat_offer:
                discount_price = int(cat_offer[0]['discount_price'])
                if cat_offer[0]['is_percentage']:
                    price_discount = p_p*discount_price/100
                else:
                    price_discount = discount_price
                p_p -= price_discount   
            total_price = qty * p_p
            data.append({
                'id':product.id,
                'product_price_withoffer':p_p,
            })
            cart_total += total_price        
            cart_items_list.append({
                'product': product,
                'qty': qty,
                'img':image,
                'total_price': total_price,
            })
        tax = cart_total*10/100
        shipping = 100
        grant_total = cart_total-applied_referral+tax+shipping
        order_sum={
            'cart total':cart_total,
            'discount':discount,
            'tax':tax,
            'shipping':shipping,
            'refferal':applied_referral,
            'grant total':grant_total,          
        }           
        request.session['order_sum'] =order_sum
        request.session.save()
    
    context = {
        'cart_items': cart_items_list,
        'cart_total':cart_total,
        'data':data,
    }
    request.session['cart_total'] = str(cart_total)
    request.session.save()
    
    if 'total_cart' in request.session:
        total = request.session['total_cart']
        if total == 0:
            del request.session['total_cart']
                
    return render(request, 'product/cart.html', context)



def update_cart_quantity(request):
    cart_total = int(0)
    cart_items_list = []
    tax = 0  
    order_data = []
    discount = 0
    grant_total = 0
    order_sum = {}
    applied_referral = 0
    data = []
    cart_data = request.session.get('cartdata', {})
    email = request.session.get('email', None)
    if email:
        user = User.objects.get(email=email)
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        new_quantity = request.POST.get("new_quantity")
        
        product = FitProduct.objects.get(id=product_id)
        qt = product.stock   
        if email:
                print("i ma here")
                onecart = Cart.objects.get(user = user)
                cart_item = CartItem.objects.filter(cart=onecart, product_id = product_id ).first()
                if cart_item:
                    # if qt > cart_item.quantity:
                    cart_item.quantity = int(new_quantity)
                    cart_item.save()   
                    if 'cartdata' in request.session:
            
                        if str(product_id) in cart_data:
                            if qt > cart_data[str(product_id)]['qty']:
                                cart_data[str(product_id)]['qty'] = int(new_quantity)
                                cart_data.update(cart_data)
                                request.session['cartdata']=cart_data
                    
                cart, created = Cart.objects.get_or_create(user=user)
                if user:
                    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
                    price_discount = 0   
                    cat_offer = []
                    for item in cart_items:
                        qty = item.quantity  
                        p_p = int(item.product.sale_price )
                        cat_id = item.product.category_id
                        category_obj = Category.objects.get(id=cat_id)
                        cat_offer = Offer.objects.filter(category=category_obj, is_active = True).values('name', 'discount_price', 'is_active', 'is_percentage')
                        if cat_offer:
                            discount_price = int(cat_offer[0]['discount_price'])
                            if cat_offer[0]['is_percentage']:
                                price_discount = p_p*discount_price/100
                            else:
                                price_discount = discount_price
                            p_p -= price_discount
                        total_price = qty * p_p
                        data.append({
                            'id':item.product.id,
                            'product_price_withoffer':p_p,
                        })
                        cart_total += total_price   
                        product = item.product
                        images = ProductImage.objects.filter(product_id=product.id).first()
                        image = None
                        if images:
                            image = images.image.url
                    
                        cart_items_list.append({
                            'product': product,
                            'qty': qty,
                            'img':image,
                            
                            'total_price': total_price,
                        })
                # checking whether the user is reffered and is it his first order
                order_data = Order.objects.filter(user=user).first()
                if user.is_referred:
                    if not order_data:
                        first_offer = Offer.objects.filter(name='referral_offer', is_active=True).values('discount_price', 'is_percentage', 'is_active').first()
                        if first_offer:
                            percentage = first_offer['is_percentage']
                            active = first_offer['is_active']
                            if active:
                                if percentage:
                                    applied_referral = cart_total*20/100               
                tax = cart_total*10/100
                shipping=100
                grant_total = cart_total-applied_referral+tax+shipping    
                order_sum={
                    'cart total':cart_total,
                    'discount':discount,
                    'tax':tax,
                    'shipping':shipping,
                    'refferal':applied_referral,
                    'grant total':grant_total,    
                }  
                request.session['order_sum'] =order_sum
                request.session.save()
                print(f"email order{request.session['order_sum']}")
            
        elif 'cartdata' in request.session:
            
            if str(product_id) in cart_data:
                if qt > cart_data[str(product_id)]['qty']:
                    
                    cart_data[str(product_id)]['qty'] = int(new_quantity)
                    cart_data.update(cart_data)
                   
                    request.session['cartdata']=cart_data
            for item_id, item_data in cart_data.items():
                price_discount = 0   
                cat_offer = []
                product = FitProduct.objects.filter(id=int(item_id)).first()
                product_image = ProductImage.objects.filter(product_id=product.id).first()        
                if product:
                    image = None
                    if product_image:
                        image = product_image.image.url          
                qty = int(item_data['qty'])
                cat_id = product.category_id
                category_obj = Category.objects.get(id=cat_id)
                p_p = float(product.sale_price)  
                cat_offer = Offer.objects.filter(category=category_obj, is_active=True).values('name', 'discount_price', 'is_active', 'is_percentage')
                if cat_offer:
                    discount_price = int(cat_offer[0]['discount_price'])
                    if cat_offer[0]['is_percentage']:
                        price_discount = p_p*discount_price/100
                    else:
                        price_discount = discount_price
                    p_p -= price_discount   
                total_price = qty * p_p
                data.append({
                    'id':product.id,
                    'product_price_withoffer':p_p,
                })
                cart_total += total_price        
                cart_items_list.append({
                    'product': product,
                    'qty': qty,
                    'img':image,
                    'total_price': total_price,
                })
               
            tax = cart_total*10/100
            shipping = 100
            grant_total = cart_total-applied_referral+tax+shipping
            order_sum={
                'cart total':cart_total,
                'discount':discount,
                'tax':tax,
                'shipping':shipping,
                'refferal':applied_referral,
                'grant total':grant_total,          
            }           
            request.session['order_sum'] =order_sum
            request.session.save()
            
    x_value  = request.session['order_sum']                 
    context = {
        'cart_items': cart_items_list,
        'cart_total':cart_total,
        'data':data,
    }
    request.session['cart_total'] = str(cart_total)
    request.session.save()
    
    if 'total_cart' in request.session:
        total = request.session['total_cart']
        if total == 0:
            del request.session['total_cart']
          
    return JsonResponse(x_value)

      

def get_cart_summary(request):
    # Retrieve the data you want to send to the client
    order_sum = request.session.get('order_sum', {})
    print(f"my ajax cart data is {order_sum}")
    
    # Create a JSON response with the data
    data = {
        'order_sum': order_sum
    }
    
    return JsonResponse(data)



def add_to_wishlist(request): 
    email = request.session.get('email', None)
    if email:
        user = User.objects.get(email=email) 
    wish_list = {}  
    wish_list[str(request.GET['id'])]={
         'id':request.GET['id'],          
    }
    product_id=request.GET['id']
    product = FitProduct.objects.get(id=product_id)
    if email: 
        wishbucket, created = WishList.objects.get_or_create(user=user) 
        existing_wishlistitem = WishListItem.objects.filter(wishlist = wishbucket, product=product).first()
        if not existing_wishlistitem:
            WishListItem.objects.create(wishlist = wishbucket,product = product)
            if 'wishdata' not in request.session:
                request.session['wishdata'] = wish_list
                request.session['total_wishdata'] = 1       
            elif 'wishdata' in request.session:
                wish_data = request.session.get('wishdata',{})
                if str(product_id) not in wish_data:
                    wish_data.update(wish_list)
                    request.session['wishdata'] = wish_data
                    request.session['total_wishdata'] = len(wish_data)                        
    elif 'wishdata' in request.session:
        wish_data = request.session.get('wishdata',{})
        if str(product_id) not in wish_data: 
            wish_data[str(product_id)] = {'id': product_id}
            request.session['wishdata'] = wish_data 
            request.session['total_wishdata'] = len(wish_data)       
    else:
        request.session['wishdata'] = wish_list
        request.session['total_wishdata'] = 1
    total_wishdata = request.session.get('total_wishdata', 0)
    request.session.save()
    return JsonResponse({'totallist': total_wishdata})

def wishlist(request):
    wish_data = request.session.get('wishdata', {})
    cart_data = request.session.get('cartdata', {}) 
    email = request.session.get('email', None)
    if email:
        user = User.objects.get(email=email) 
    if request.GET.get('addalltocart'):  
        if 'wishdata' in request.session:
            for product_id in wish_data:
                product = FitProduct.objects.get(id = int(product_id))
                cart_it={
                        'id':product_id,
                        'qty':1,         
                    }
                if email: 
                    cart, created = Cart.objects.get_or_create(user=user)
                    existing_cart_item = CartItem.objects.filter(cart=cart, product=product).first()
                    if existing_cart_item:
                        # Item already exists, update the quantity
                        if existing_cart_item.quantity < product.stock:
                            existing_cart_item.quantity += 1
                            existing_cart_item.save()
                            if str(product_id) in cart_data:
                                if int(cart_data[str(product_id)]['qty']) < product.stock:
                                    cart_data[str(product_id)]['qty'] = int(cart_data[str(product_id)]['qty'])+ int(1)
                                    cart_data.update(cart_data)
                                    request.session['cartdata']=cart_data
                                else:
                                    messages.info(request, "Out of stock")
                            else:
                                cart_data[str(product_id)] = {'qty': 1}
                                request.session['cartdata'] = cart_data
                        else:
                            messages.info(request, "Out of stock")       
                    else: 
                        CartItem.objects.create(cart = cart,product = product,quantity = 1)   
                        if 'cartdata' in request.session:   
                            if str(product_id) in cart_data:
                                if cart_data[str(product_id)]['qty'] < product.stock:
                                    cart_data[str(product_id)]['qty'] = int(cart_data[str(product_id)]['qty'])+int(1)
                                    cart_data.update(cart_data)
                                    request.session['cartdata'] = cart_data 
                                else:
                                    messages.info(request, "Out of stock")  
                            else:
                                cart_data[str(product_id)] = {'qty': 1}
                                request.session['cartdata'] = cart_data     
                        if 'total_cart' in request.session:
                            cart_number = request.session.get('total_cart')
                            cart_number = cart_number+1
                            request.session['total_cart'] = cart_number
                            request.session.save()
                        else:
                            request.session['total_cart'] = 1
                elif 'cartdata' in request.session:
                    if str(product_id) in cart_data:
                        if int(cart_data[str(product_id)]['qty']) < product.stock:
                            cart_data[str(product_id)]['qty'] = int(cart_data[str(product_id)]['qty'])+int(1)
                            cart_data.update(cart_data)
                            request.session['cartdata']=cart_data
                        else:
                            messages.info(request, "Out of stock")          
                    else:
                        cart_data[str(product_id)] = {'qty': 1}
                        request.session['cartdata'] = cart_data  
                        if 'total_cart' in request.session:
                            cart_number = request.session.get('total_cart')
                            cart_number = cart_number+1
                            request.session['total_cart'] = cart_number
                            request.session.save()
                        else:
                            request.session['total_cart'] = 1       
                else:
                    cart_data[str(product_id)] = {'qty': 1}
                    request.session['cartdata'] = cart_data  
                    if 'total_cart' in request.session:
                            cart_number = request.session.get('total_cart')
                            cart_number = cart_number+1
                            request.session['total_cart'] = cart_number
                            request.session.save()
                    else:
                        request.session['total_cart'] = 1   
            request.session.save()   
            messages.info(request, 'All items added to cart, please check in cart')
    if request.GET.get('wishdel'):
        product_id = request.GET.get('wishdel')
        if email:
            if user:
                wishlist = WishList.objects.get(user = user)
                data = WishListItem.objects.get(wishlist = wishlist, product_id = product_id)
                if data:
                    data.delete()
                    if 'wishdata' in request.session:              
                        if str(product_id) in wish_data:
                            wish_data.pop(product_id)
                            request.session['wishdata'] = wish_data                   
                        if 'total_wishdata' in request.session:
                            cart_number = request.session.get('total_wishdata')
                            cart_number = cart_number - 1
                            request.session['total_wishdata'] = cart_number
                            request.session.save()                                  
        else: 
            if str(product_id) in wish_data:
                wish_data.pop(product_id)
                request.session['wishdata'] = wish_data
                if 'total_wishdata' in request.session:
                    cart_number = request.session.get('total_wishdata')
                    cart_number = cart_number-1
                    request.session['total_wishdata'] = cart_number
                    request.session.save()                 
    wish_items_list = []
    if email:
        if user:
            wishbucket, created = WishList.objects.get_or_create(user=user)
            wish_items = WishListItem.objects.filter(wishlist = wishbucket).select_related('product')
            for item in wish_items:
                product = item.product
                prd = FitProduct.objects.filter(id = product.id).values('id', 'name', 'slug').first()
                images = ProductImage.objects.filter(product_id = product.id).first()
                image  = None
                if images:
                    image = images.image.url
                wish_items_list.append({
                    'product': prd,
                    'image':image, 
                })           
    elif 'wishdata' in request.session:    
        for p_id, item in request.session.get('wishdata', {}).items():
            product = FitProduct.objects.filter(id=int(item['id'])).values('id', 'name', 'slug').first()
            product_image = ProductImage.objects.filter(product_id=item['id']).first()  
            if product:
                image = None
                if product_image:
                    image = product_image.image.url         
            wish_items_list.append({
                    'product': product,
                    'image':image, 
                    })  
                  
    if 'total_wishdata' in request.session:
        total = request.session['total_wishdata']
        if total == 0:
            del request.session['total_wishdata']               
                  
    context = {
        'wish_items_list': wish_items_list,
    }           
    return render(request, 'product/wishlist.html', context)
                                           
@login_required(login_url='login')  # Use the URL of your login page here
def check_out(request):
    value = None
    b_address = [None]
    country = Country.objects.all().order_by('name')
    state = State.objects.all().order_by('name')
    email = request.session.get('email', None)
    user_obj = User.objects.get(email = email)
    b_address = Address.objects.filter(user_id = user_obj.id).values()
    cart = Cart.objects.get(user=user_obj)
    cartitem = CartItem.objects.filter(cart=cart).select_related('product') 
    addresses = Address.objects.filter(Q(user=user_obj) & Q(is_deleted = False)).order_by('-id').select_related('state', 'country')
    if addresses:
	value = addresses[0] 
    category_offer_name_set = set()
    cart_item_total = []
    cart_total = 0
    category_offer_discount = 0
    for item in cartitem:
        price_discount = 0
        item.quantity
        item.product.id
        product = item.product.name
        price = item.product.sale_price
        cat_id = item.product.category_id
        qty = item.quantity  
        p_p = int(price )
        category_obj = Category.objects.get(id=cat_id)         
        cat_offer = Offer.objects.filter(category=category_obj, is_active=True).values('name', 'discount_price', 'is_active', 'is_percentage')
        if cat_offer:
            for i in cat_offer:
                category_offer_name_set.add(i['name'])
            discount_price = int(cat_offer[0]['discount_price'])
            if cat_offer[0]['is_percentage']:
                price_discount = p_p*discount_price/100
            else:
                price_discount = discount_price
            category_offer_discount+=price_discount
            p_p -= price_discount
        total_price = qty * p_p 
        cart_total += total_price
        cart_item_total.append({
            'product': product,
            'total_price':total_price,     
        }) 
    category_offer_name = ' '.join(category_offer_name_set)
    request.session['order_sum']['category offer discount'] = category_offer_discount
    request.session['order_sum']['category offer name'] = category_offer_name
    request.session.save()
    coupon_percentage = 0
    coupon_fixedprice = 0
    if request.method == 'POST':
            coupon_name = request.POST.get('coupon')
            try:
                data_obj = Coupon.objects.get(name = coupon_name)
                # check the coupon already used by user
                try:
                    check = UsedCoupon.objects.get(user=user_obj, name=coupon_name )
                except UsedCoupon.DoesNotExist:
                    if data_obj.count !=0:
                        if data_obj.is_active:
                            if data_obj.is_percentage:
                                coupon_percentage = data_obj.discount_price
                                request.session['coupon'] = data_obj.name
                            else:
                                coupon_fixedprice = data_obj.discount_price
                                request.session['coupon'] = data_obj.name
                        else:
                            # messages.info(request, 'diccountined coupon')
                            pass
                    elif data_obj.count == 0:
                        data_obj.is_active == 'False'
                        data_obj.save()   
            except Coupon.DoesNotExist:
                pass

    order_detail = request.session['order_sum']
    cart_total = order_detail['cart total']
    tax =  order_detail['tax']
    shipping = order_detail['shipping']
    grant_total = order_detail['grant total']
    applied_referral = order_detail['refferal']
    if coupon_percentage:
            coupon_percentage = int(coupon_percentage)
            discount = cart_total*coupon_percentage/100
    else:
        discount = float(coupon_fixedprice)     
    grant_total = cart_total-applied_referral-discount+tax+shipping  
    request.session['order_sum']['discount'] = discount
    request.session['order_sum']['grant total'] = grant_total
    request.session.save()
    context = {
        'countries':country,
        'states': state,
        'cart_total':cart_total,
        'b_address': b_address,
        'addresses':addresses,
       'cart_item_total':cart_item_total,
        'value':value,
    }
    return render(request, 'product/checkout.html', context)

def payment_mode(request, id=None):
    if request.method == 'POST':      
        is_shipping = request.POST.get('is_shipping', False)
        is_shipping = is_shipping == 'on'
        addresses = Address.objects.filter(id=id).select_related('state', 'country')
        for address in addresses:  
            billing_address_sess = {
                'first_name': address.first_name,
                'last_name':address.last_name,
                'email': address.email,
                'phone_number': address.phoneNumber,
                'addressline1': address.addressline1,
                'addressline2':address.addressline2,
                'city':address.city,
                'state':address.state.name,
                'country':address.country.name,
                'pin':address.pin,
            }  
            request.session['billing_address'] = billing_address_sess
            request.session.save()   
        if is_shipping:
            shipaddressline1 = request.POST.get('Shipaddressline1')
            shipaddressline2 = request.POST.get('Shipaddressline2')
            shipcity = request.POST.get('Shipcity')
            shipstate = request.POST.get('Shipstate')
            shipcountry = request.POST.get('Shipcountry')
            shippin = request.POST.get('Shippin')
            state_obj = State.objects.get(id = shipstate)
            country_obj = Country.objects.get(id = shipcountry)
            state_obj=str(state_obj)
            country_obj=str(country_obj)
            if (shipaddressline1, shipaddressline2, shipcity,shipstate, shipcountry, shippin):
                shipping_address_sess = {
                    'shipaddressline1': shipaddressline1,
                    'shipaddressline2':shipaddressline2,
                    'shipcity':shipcity,
                    'shipstate':state_obj,
                    'shipcountry':country_obj,
                    'shippin':shippin,
                }
                request.session['shipping_address'] = shipping_address_sess
                request.session.save()      
    return render(request, 'product/paymentmode.html')   
               
def order_placed(request):
    order_sum_values = request.session['order_sum']
    email = request.session.get('email', None) 
    if email:
        user_obj = User.objects.get(email=email)
    coupon_name = request.session.get('coupon', None)
    if request.method == 'POST':
        client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
        total = int(order_sum_values['grant total'])
        final = total*100
        payment = client.order.create({'amount':  final, 'currency': 'INR', 'payment_capture':1})
        context = {
            'payment':payment
        }
        return render(request, 'product/paymentmode.html', context)  
    try:    
        cart_obj = Cart.objects.get(user=user_obj)
        if request.GET.get('cash'):
            val = False
            if 'billing_address' in request.session:
                bill_data = request.session['billing_address'] 
            if 'shipping_address' in request.session:
                ship_data = request.session['shipping_address'] 
                if ship_data:
                    val = True      
            if email:
                cartitems = CartItem.objects.filter(cart=cart_obj).select_related('product').values('product_id', 'quantity')
                order_obj = Order.objects.create(
                    user=user_obj, 
                    billing_email = bill_data['email'],
                    billing_address1 =bill_data['addressline1'],
                    billing_address2 = bill_data['addressline2'],
                    billing_city =bill_data['city'],
                    billing_state = bill_data['state'],
                    billing_country = bill_data['country'],
                    payment_method = 'COD',
                    discount = order_sum_values['discount'],
                    category_offer_discount = order_sum_values['category offer discount'],
                    category_offer_name = order_sum_values['category offer name'],
                    refferal_offer = order_sum_values['refferal'],
                    is_shipping = val,
                    shipping_charge = order_sum_values['shipping'],
                    total_amout = order_sum_values['grant total'],
                    tax = order_sum_values['tax']
                    ) 
                request.session['order_id'] = order_obj.id
                request.session.save()
                if 'coupon' in request.session:
                    UsedCoupon.objects.create(user = user_obj, name=coupon_name)
                    coupon = Coupon.objects.get(name = coupon_name)
                    coupon.count-=1
                    coupon.save()
                    del request.session['coupon']
                for item in cartitems:
                    qty = item['quantity']
                    item['product_id']
                    pdt = FitProduct.objects.get(id=item['product_id'])
                    cat_id = pdt.category_id
                    p_p = pdt.sale_price
                    category_obj = Category.objects.get(id=cat_id)
                    cat_offer = Offer.objects.filter(category=category_obj, is_active=True).values('name', 'discount_price', 'is_active', 'is_percentage')
                    if cat_offer:
                        discount_price = int(cat_offer[0]['discount_price'])
                        if cat_offer[0]['is_percentage']:
                            price_discount = p_p*discount_price/100
                        else:
                            price_discount = discount_price     
                        p_p -= price_discount
                    OrderItem.objects.create(order = order_obj,product = pdt,price = pdt.price,offer_price = p_p,quantity = qty)   
                if 'shipping_address' in request.session:           
                    ShippingAddress.objects.create(
                        order= order_obj,
                        addressline1 = ship_data['shipaddressline1'],
                        addressline2 = ship_data['shipaddressline2'],
                        city = ship_data['shipcity'],
                        state = ship_data['shipstate'],
                        country = ship_data['shipcountry'],
                        pin  = ship_data['shippin'],
                    )    
                if 'billing_address' in request.session:
                    del request.session['billing_address']
                if 'shipping_address' in request.session:
                    del request.session['shipping_address']
                if 'cartdata' in request.session:  
                    del request.session['cartdata']
                if 'order_sum' in request.session:
                    del request.session['order_sum']
                if 'total_cart' in request.session:
                    del request.session['total_cart']
                CartItem.objects.filter(cart=cart_obj).delete()
                Cart.objects.filter(user=user_obj).delete()
                return redirect('success')

        elif request.GET.get('wallet'):
            wallet_obj = Wallet.objects.filter(user=user_obj)
            total = Decimal(0.00)
            credit_total= Decimal(0.00)
            debit_total= Decimal(0.00)
            if wallet_obj:
                for item in wallet_obj:
                    if item.is_credit:
                        credit_total += item.amount
                    else:
                        debit_total+= item.amount
                total = credit_total - debit_total
                if total > Decimal(order_sum_values['grant total']):
                    val = False
                    if 'billing_address' in request.session:
                        bill_data = request.session['billing_address']
                    if 'shipping_address' in request.session:
                        ship_data = request.session['shipping_address']
                        if ship_data:
                            val = True
                    if email:
                        cartitems = CartItem.objects.filter(cart=cart_obj).select_related('product').values('product_id', 'quantity')
                        order_obj = Order.objects.create(
                            user=user_obj, 
                            billing_email = bill_data['email'],
                            billing_address1 =bill_data['addressline1'],
                            billing_address2 = bill_data['addressline2'],
                            billing_city =bill_data['city'],
                            billing_state = bill_data['state'],
                            billing_country = bill_data['country'],
                            payment_method = 'Wallet',
                            discount = order_sum_values['discount'],
                            category_offer_discount = order_sum_values['category offer discount'],
                            category_offer_name = order_sum_values['category offer name'],
                            refferal_offer = order_sum_values['refferal'],
                            is_shipping = val,
                            shipping_charge = order_sum_values['shipping'],
                            total_amout = order_sum_values['grant total'],
                            tax = order_sum_values['tax']
                            )
                        request.session['order_id'] = order_obj.id
                        request.session.save()  
                        if 'coupon' in request.session:
                            UsedCoupon.objects.create(user = user_obj,name=coupon_name)
                            coupon = Coupon.objects.get(name = coupon_name)
                            coupon.count-=1
                            coupon.save()
                            del request.session['coupon']

                        for item in cartitems:
                            qty = item['quantity']
                            item['product_id']
                            pdt = FitProduct.objects.get(id=item['product_id'])
                            cat_id = pdt.category_id
                            p_p = pdt.sale_price 
                            category_obj = Category.objects.get(id=cat_id)
                            cat_offer = Offer.objects.filter(category=category_obj, is_active=True).values('name', 'discount_price', 'is_active', 'is_percentage')
                            if cat_offer:
                                discount_price = int(cat_offer[0]['discount_price'])
                                if cat_offer[0]['is_percentage']:
                                    price_discount = p_p*discount_price/100
                                else:
                                    price_discount = discount_price 
                                p_p -= price_discount

                            OrderItem.objects.create(order = order_obj,product = pdt,price = pdt.price,offer_price = p_p,quantity = qty)
                        if 'shipping_address' in request.session:      
                            ShippingAddress.objects.create(
                                order= order_obj,
                                addressline1 = ship_data['shipaddressline1'],
                                addressline2 = ship_data['shipaddressline2'],
                                city = ship_data['shipcity'],
                                state = ship_data['shipstate'],
                                country = ship_data['shipcountry'],
                                pin = ship_data['shippin'],
                            )    
                        if 'billing_address' in request.session:
                            del request.session['billing_address']
                        if 'shipping_address' in request.session:
                            del request.session['shipping_address']
                        if 'cartdata' in request.session:  
                            del request.session['cartdata']
                        if 'order_sum' in request.session:
                            del request.session['order_sum']
                        if 'total_cart' in request.session:
                            del request.session['total_cart']
                        CartItem.objects.filter(cart=cart_obj).delete()
                        Cart.objects.filter(user=user_obj).delete()
                        Wallet.objects.create(user=user_obj, is_credit=False, order=order_obj, amount = Decimal(order_sum_values['grant total']) )
                        return redirect('success')
                else:
                    messages.info(request, "wallet has lesser amount that the purchase amount")
                    return render(request, 'product/paymentmode.html')
            else:
                messages.info(request, "wallet has no amount to make the purchase")
                return render(request, 'product/paymentmode.html')        
    except Cart.DoesNotExist:
        pass
    
    return render(request, 'success.html')
        
def save_payment(request):
    email = request.session.get('email', None)   
    user_obj = User.objects.get(email=email)
    cart_obj = Cart.objects.get(user=user_obj)
    order_sum_values = request.session['order_sum']
    coupon_name = request.session.get('coupon', None)
    val = False
    if 'billing_address' in request.session:
        bill_data = request.session['billing_address']   
    if 'shipping_address' in request.session:
        ship_data = request.session['shipping_address']
        if ship_data:
            val = True
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
            # Return an error response if any of the Razorpay data is missing
            return JsonResponse({'message': 'Razorpay data is missing'}, status=400)
        try:
            if email:
                cartitems = CartItem.objects.filter(cart=cart_obj).select_related('product').values('product_id', 'quantity')
                order_obj = Order.objects.create(
                    user=user_obj, 
                    billing_email = bill_data['email'],
                    billing_address1 =bill_data['addressline1'],
                    billing_address2 = bill_data['addressline2'],
                    billing_city =bill_data['city'],
                    billing_state = bill_data['state'],
                    billing_country = bill_data['country'],
                    payment_method = 'online paymenet',
                    discount = order_sum_values['discount'],
                    category_offer_discount = order_sum_values['category offer discount'],
                    category_offer_name = order_sum_values['category offer name'],
                    refferal_offer = order_sum_values['refferal'],
                    is_shipping = val,
                    shipping_charge = order_sum_values['shipping'],
                    total_amout = order_sum_values['grant total'],
                    tax = order_sum_values['tax']  
                    )   
                request.session['order_id'] = order_obj.id
                request.session.save() 
                Payment.objects.create(
                    order = order_obj,
                    amount = order_sum_values['grant total'],
                    razor_pay_order_id = razorpay_payment_id,
                    razor_pay_payment_id = razorpay_order_id,
                    razor_pay_payment_signature = razorpay_signature,
                )
                if 'coupon' in request.session:
                    UsedCoupon.objects.create(user = user_obj, name=coupon_name)
                    coupon = Coupon.objects.get(name = coupon_name)
                    coupon.count-=1
                    coupon.save()
                    del request.session['coupon']
                for item in cartitems:
                    qty = item['quantity']
                    item['product_id']
                    pdt = FitProduct.objects.get(id=item['product_id'])
                    cat_id = pdt.category_id
                    p_p = pdt.sale_price
                    category_obj = Category.objects.get(id=cat_id)
                    cat_offer = Offer.objects.filter(category=category_obj, is_active=True).values('name', 'discount_price', 'is_active', 'is_percentage')
                    if cat_offer:
                        discount_price = int(cat_offer[0]['discount_price'])
                        if cat_offer[0]['is_percentage']:
                            price_discount = p_p*discount_price/100
                        else:
                            price_discount = discount_price       
                        p_p -= price_discount
                    OrderItem.objects.create(
                        order = order_obj,
                        product = pdt,
                        price = pdt.price,
                        offer_price = p_p,
                        quantity = qty,       
                    )
                if 'shipping_address' in request.session:        
                    ShippingAddress.objects.create(
                        order= order_obj,
                        addressline1 = ship_data['shipaddressline1'],
                        addressline2 = ship_data['shipaddressline2'],
                        city = ship_data['shipcity'],
                        state = ship_data['shipstate'],
                        country = ship_data['shipcountry'],
                        pin = ship_data['shippin'],
                    )       
                if 'billing_address' in request.session:
                    del request.session['billing_address']
                if 'shipping_address' in request.session:
                    del request.session['shipping_address']
                if 'cartdata' in request.session:  
                    del request.session['cartdata']
                if 'order_sum' in request.session:
                    del request.session['order_sum']
                if 'total_cart' in request.session:
                    del request.session['total_cart']
                CartItem.objects.filter(cart=cart_obj).delete()
                Cart.objects.filter(user=user_obj).delete()
                return redirect('success')
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=400)
    else:
        return JsonResponse({'message': 'Invalid HTTP method'}, status=400)
    

def success(request):
    email = request.session.get('email', None)   
    if email:
        user_obj = User.objects.get(email=email)
    order_id = request.session['order_id']
    order = Order.objects.get(id=order_id)
    # order - email start here        
    order_message = "Thank you for your order!\n"
    order_message += "Order Details:\n"
    order_message += f"Order ID: {order.id} \n"
    order_message += f"Coupon discount received: {order.discount} \n"
    order_message += f"Category Offer received: RS{order.category_offer_discount}\n"
    order_message += f"Tax: {order.tax} \n"
    order_message += f"Shipping Charge: {order.shipping_charge} \n"
    order_message += f"Total Price: RS{order.total_amout}\n"
    order_message += f"Method of payment: {order.payment_method}\n"
    receiver_mail = email
    sender_email = config('sender_email', default='')
    password = config('password', default='')
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            email_subject = "Your Order Details"
            email_body = order_message
            server.sendmail(sender_email, receiver_mail, f"Subject: {email_subject}\n\n{email_body}")
    except smtplib.SMTPAuthenticationError:
        messages.error(request, 'Failed to send order details. Please check your email configuration.')
    # email end here
    try:
        cart_obj = Cart.objects.get(user=user_obj)
        if cart_obj: 
            cart_obj.delete()
            if 'order_id' in request.session:
                del request.session['order_id']
        return render(request, 'product/success.html')
    except Cart.DoesNotExist:
        return render(request, 'product/success.html')
       
def add_review(request):
    if request.method == 'POST':
        id = request.POST.get('p-id')
        slug = request.POST.get('p-slug')
        topic = request.POST.get('topic')
        rating = request.POST.get('rating')
        pdt = FitProduct.objects.filter(Q(slug=slug) & Q(is_active=True)).filter(is_deleted = False).select_related('category').prefetch_related('productimage_set')
        data = FitProduct.objects.filter(Q(category=pdt[0].category)  & Q(is_active=True)).filter(is_deleted = False).exclude(slug=slug).prefetch_related('productimage_set') 
        pdt_description = pdt[0].description.strip()
        email = request.session['email']
        user_obj = User.objects.get(email=email)
        product_obj = FitProduct.objects.get(id=id)
        Review.objects.create(
            user = user_obj,
            product = product_obj,
            comment = topic,
            rate = rating,
        ) 
        context = {
            'pdt':pdt,
            'data':data,
            'pdt_description': pdt_description,
        }
        return render(request, 'product/productdetail.html', context)
