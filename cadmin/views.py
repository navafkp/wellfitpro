from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
User = get_user_model()
from django.http import HttpResponse  
from django.contrib import messages
from django.views.decorators.cache import cache_control, never_cache
from product.models import FitProduct, Category, ProductImage, Order, OrderItem, Coupon, Wallet, Offer

from accounts.models import Notifications, State, Country
# from validate_email import validate_email
# from validate_email_address import validate_email
from django.core.validators import validate_email
from dateutil import parser as date_parser
import time
from django.db.models.functions import Concat  
from django.db.models import F, Value
from decimal import Decimal
import csv
from django.db.models import Q
from datetime import datetime, date, timedelta
from django.core.exceptions import ValidationError
import datetime
from django.core.exceptions import ValidationError
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def adminsignin(request):
    if 'email' in request.session:
        return redirect('home')
    elif 'adminemail' in request.session:
        return redirect('ahome')
    elif request.method == 'POST':
        email = request.POST.get('Email')
        password = request.POST.get('Password')  
        if not (email and password):
            messages.error(request, "Please fill in all the required fields")
            return redirect('adminsignin')
        email = email.strip()
        try:
            validate_email(email)
            
        except ValidationError:
            messages.info(request, "Please enter a valid email address")    

        else:
            admin = authenticate(request, email=email, password=password)
            if admin is not None:
                if admin.is_staff:
                    request.session['adminemail'] = email
                    login(request, admin)
                    return redirect('ahome')
                else:
                    messages.info(request, "You are not authorized to access the admin page")
                    return redirect('adminsignin')       
            else: 
                messages.info(request, "Invalid username or password.")

                return redirect('adminsignin') 
        # else:
        #     messages.info(request, 'enter a valid email ID')

    return render(request, 'admin/adminsignin.html')

def datetime_serializer(obj):
            if isinstance(obj, datetime.datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def ahome(request):
    order_info = []
    orders = Order.objects.all().values('id', 'created_at', 'status', 'total_amout').order_by('-id')
    total_sale = 0
    today_total = 0
    for order in orders:
        order_id = order['id']
        date = order['created_at'].date()
        status = order['status']
        total = order['total_amout']
        if status != 5:
            total_sale+=total
        if date == date.today() and status != 5:
            today_total +=total
        order_info.append({
                'order_id': order_id,
                'date':date,
                'status':status,
                'total':total,   
            })  
        
    notifications = list(Notifications.objects.all().values('message', 'timestamp').order_by('-timestamp'))
    for item in notifications:
        item['timestamp'] = datetime_serializer(item['timestamp'])
    request.session['admin_notifications'] = notifications
    request.session.save() 
    print(request.session['admin_notifications'])
    context = {
        'order_info': order_info,
        'total_sale':total_sale,
        'today_total':today_total,
    }
    return render(request, 'admin/adminindex.html', context )

def admin_sales_report(request):
    return render(request, 'admin/adminsalesreport.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def users(request):
    data = []
    if request.GET.get('user'):
        value = request.GET.get('user')
        data = User.objects.filter(Q(first_name__icontains = value) | Q(last_name__icontains = value)) 
    elif request.GET.get('filter_user'):
        value = request.GET.get('filter_user')
        if value == 'first_name':
            data = User.objects.filter(is_staff = False).order_by('first_name')
        elif value == 'last_name': 
            data = User.objects.filter(is_staff = False).order_by('last_name')
        elif value == 'ID':
            data = User.objects.filter(is_staff = False).order_by('id')
    else:    
        data = User.objects.filter(is_staff = False).order_by('-id')
    context = {
        'data':data
    }
    return render (request, 'admin/adminusers.html' , context)
def product(request):
    ctgy = Category.objects.all().order_by('-id')
    pdt = []
    if request.GET.get('search_product'):
        value = request.GET.get('search_product')
        pdt = FitProduct.objects.filter(Q(name__icontains = value) | Q(category__name__icontains=value)).filter(is_deleted = False).order_by('-id').prefetch_related('productimage_set').select_related('category')   
    elif request.GET.get('filter_product'):
        value = request.GET.get('filter_product') 
        if value == 'name':
            pdt = FitProduct.objects.filter(is_deleted = False).order_by('name').prefetch_related('productimage_set').select_related('category')
        elif value == 'created_at':
            pdt = FitProduct.objects.filter(is_deleted = False).order_by('created_at').prefetch_related('productimage_set').select_related('category')
        elif value == 'category':
            pdt = FitProduct.objects.filter(is_deleted = False).order_by('category__name').prefetch_related('productimage_set').select_related('category')
        elif value == 'price':
            pdt = FitProduct.objects.filter(is_deleted = False).order_by('price').prefetch_related('productimage_set').select_related('category')   
    else:   
        pdt = FitProduct.objects.filter(is_deleted = False).order_by('-id').prefetch_related('productimage_set').select_related('category')
    
    context = {
        'pdt': pdt,
        'ctgy' : ctgy   
    }
    return render(request, 'admin/adminproducts.html', context)

def all_category(request):
    ctgy = []
    if request.GET.get('search_category'):
        value = request.GET.get('search_category')
        ctgy = Category.objects.filter(Q(name__icontains = value) & Q(is_deleted = False))
    elif request.GET.get('filter_category'):
           value = request.GET.get('filter_category')
           if value == 'name':
               ctgy = Category.objects.filter(is_deleted = False).order_by('name')
           elif value == 'featured':
               ctgy = Category.objects.filter(is_deleted = False).order_by('-is_featured')   
    else:
        ctgy = Category.objects.filter(is_deleted = False).order_by('-id')
    context = {   
        'ctgy' : ctgy
    }
    return render(request, 'admin/admincategory.html', context)

def createProduct(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        short_description = request.POST.get('shortdescription') 
        price = request.POST.get('price')
        sale_price= request.POST.get('sale_price')
        images= request.FILES.getlist('images')
        tag = request.POST.get('tag')
        stock= request.POST.get('stock')
        category_id= request.POST.get('category')
        is_active= request.POST.get('is_active', False)
        is_active = is_active == 'on'
        is_featured = request.POST.get('is_featured', False)
        is_featured = is_featured == 'on'
        is_sale = request.POST.get('is_sale', False)
        is_sale = is_sale == 'on'
        
        category_id = int(category_id) if category_id else None
        if not all([name, description, short_description, price, sale_price, images, tag, stock, category_id]):
            messages.error(request, "Please fill all details to add a new product")
            return redirect('product')  
        category = Category.objects.get(id=category_id)
        pdt = FitProduct.objects.create(
                name =name,
                description = description,
                price = price,
                sale_price=sale_price,
                tag = tag,
                stock = stock, 
                short_description = short_description,
                category = category,
                is_active = is_active,
                is_sale = is_sale,                          
        )
        for image in images:
            ProductImage.objects.create(product=pdt, image=image)
        pdt.save()
        messages.info(request, 'product added')
        return redirect('product')
    return render(request, 'admin/adminproducts.html')


def createCetegory(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image= request.FILES.get('image')
        is_featured = request.POST.get('is_featured', False)
        is_featured = is_featured == 'on'
        if not (name, image):
            messages.info(request, "please fill all details")
            return redirect('all_category')
        else:  
            ctgy = Category.objects.create(name=name,image=image,is_featured=is_featured)
            messages.info(request, "Category added")
            return redirect('all_category')
    return render(request, 'admin/admincategory.html')
               
def updateProduct(request, id):
    if request.method == 'POST':
        pdt = FitProduct.objects.get(id=id)
        pdt.name = request.POST.get('name')
        pdt.description = request.POST.get('description')
        pdt.short_description = request.POST.get('shortdescription')
        pdt.price = request.POST.get('price')
        pdt.sale_price = request.POST.get('sale_price')
        pdt.tag = request.POST.get('tag')
        pdt.stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        pdt.is_active = request.POST.get('is_active', False)
        pdt.is_active = pdt.is_active == 'on'
        pdt.is_featured = request.POST.get('is_featured', False)
        pdt.is_featured = pdt.is_featured == 'on'
        pdt.is_sale = request.POST.get('is_sale', False)
        pdt.is_sale = pdt.is_sale == 'on'
        images = request.FILES.getlist('images')
        category_id = int(category_id) if category_id else None
        pdt.category = Category.objects.get(id=category_id)
        pdt.save()
        if images:
            pdt.productimage_set.all().delete()
        
            for image in images:
                ProductImage.objects.create(product=pdt, image=image)
        messages.info(request, f'{pdt}  has been updated')
        return redirect('product')
      
def deleteProduct(request, id):
    pdt =FitProduct.objects.get(id=id)
    pdt.is_deleted = True
    pdt.save()
    messages.info(request, f'{pdt} has been deleted')
    return redirect('product')

def updateCategory(request,id):
    if request.method == 'POST':
        ctgy = Category.objects.get(id=id)
        ctgy.name = request.POST.get('name')
        image = request.FILES.get('new_image')     
        ctgy.is_featured = request.POST.get('is_featured', False)
        ctgy.is_featured = ctgy.is_featured == 'on'  
        if image is not None:
            ctgy.image = image
        ctgy.save()
        messages.info(request, "Category updated")
        return redirect('all_category')
    return render(request, 'admin/admincategory.html')
       
def deleteCategory(request, id):
    data = Category.objects.get(id=id)
    data.is_deleted = True
    data.save()
    messages.info(request, f'{data}product has been deleted') 
    return redirect('all_category')
       
def handle_user_status(request, id):
    user = User.objects.get(id=id)
    if request.method == 'POST':
        action = request.POST.get('action')   
        if action == 'activate':
            user.is_blocked = False  
            user.save()
        elif action == 'block':
            user.is_blocked = True
            user.save()
        return redirect('users')
    return HttpResponse(status=400) 

def productactivate(request, id):
    pdt = FitProduct.objects.get(id=id) 
    if request.method == 'POST':
        action = request.POST.get('action')  
        if action == 'activate':
            pdt.is_active = True  
            pdt.save()
        elif action == 'hide':
            pdt.is_active = False   
            pdt.save()   
        return redirect('product')
    return HttpResponse(status=400) 

def split_number(number):
    number_str = str(number)
    if len(number_str) < 2:
        print("The number must have at least two digits.")
    else:
        first_part = int(number_str[0])
        second_part = int(number_str[1:])
        return first_part, second_part
    
def admin_order(request):
    if request.GET.get('chnageorder'):
        value = request.GET.get('chnageorder')
        status, order_id = split_number(value)
        try:
            order = Order.objects.get(id=order_id)
            order.status = status
            order.save()
        except Order.DoesNotExist:
            messages.info(request, 'No order in this ID')    
    order_info = []             
    if request.GET.get('order'):
        id = request.GET.get('order')
        orders = Order.objects.filter(id=id).values('id', 'created_at', 'status', 'total_amout')
        for order in orders:
            order_id = order['id']
            date = order['created_at']
            status = order['status']
            total = order['total_amout']
            order_info.append({
                    'order_id': order_id,
                    'date':date,
                    'status':status,
                    'total':total,
                })     
    elif request.GET.get('filter_order'):
        orders = []
        value = request.GET.get('filter_order')  
        if value == 'Status':     
            orders = Order.objects.all().values('id', 'created_at', 'status', 'total_amout').order_by('status') 
        elif value == 'ID':
            orders = Order.objects.all().values('id', 'created_at', 'status', 'total_amout').order_by('id') 
        for order in orders:
            order_id = order['id']
            date = order['created_at']
            status = order['status']
            total = order['total_amout']  
            order_info.append({
                    'order_id': order_id,
                    'date':date,
                    'status':status,
                    'total':total,
                })
    else:  
        orders = Order.objects.all().values('id', 'created_at', 'status', 'total_amout').order_by('-id')
        for order in orders:
            order_id = order['id']
            date = order['created_at']
            status = order['status']
            total = order['total_amout'] 
            order_info.append({
                    'order_id': order_id,
                    'date':date,
                    'status':status,
                    'total':total
                })         
    context = {
        'order_info': order_info
    }
    return render(request, 'admin/adminorder.html', context)

def download_filtered_sales(request):
    if request.method == 'GET' and request.GET.get('sales_report'):
        value = request.GET.get('sales_report')
        if value == 'curret_month':
            current_date = date.today()
            first_day_of_month = current_date.replace(day=1)
            if first_day_of_month.month == 12:
                last_day_of_month = first_day_of_month.replace(year=first_day_of_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day_of_month = first_day_of_month.replace(month=first_day_of_month.month + 1, day=1) - timedelta(days=1)
            start_datetime = first_day_of_month
            end_datetime = last_day_of_month   
        elif value == 'last_month':
            current_date = date.today()
            first_day_of_month = current_date.replace(day=1)
            last_day_of_last_month = first_day_of_month - timedelta(days=1)
            first_day_of_last_month = last_day_of_last_month.replace(day=1)
            start_datetime = first_day_of_last_month
            end_datetime = last_day_of_last_month
        elif value == 'choose_date':
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')   
            try:
                start_datetime = date_parser.parse(start_date_str)
                end_datetime = date_parser.parse(end_date_str)
            except ValueError:
                return HttpResponse("Invalid date format. Please use YYYY-MM-DD.")
        # Filter orders - date only
        orders_in_date_range = Order.objects.filter(created_at__date__range=(start_datetime, end_datetime))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=allorders_{start_datetime}_{end_datetime}.csv'
        # Create a CSV writer and write header row
        writer = csv.writer(response)
        writer.writerow(['user id', 'billing_email', 'billing_address1', 'billing_address2', 'discount', 'payment_method', 'total_amout', 'created_at'])   
        # Write data rows
        for order in orders_in_date_range:
            writer.writerow([order.user_id, order.billing_email, order.billing_address1, order.billing_address2, order.discount, order.payment_method, order.total_amout, order.created_at.date()])  
        return response
    else:
        return HttpResponse('')


def setup_country(request):
    
    countries = Country.objects.all().values()
    states = State.objects.all().select_related('country')
    
    if request.method ==  'POST':
        if 'add-country' in request.POST:
            country = request.POST.get('name')
            Country.objects.create(name=country)
            
    if request.method ==  'POST':
        if 'add-state' in request.POST:
            state = request.POST.get('name')
            country = request.POST.get('country')
            
            country_obj = Country.objects.get(id=country)
            State.objects.create(name=state, country=country_obj)
            
    print(states)
    
        
    context = {
       'countries':countries, 
       'states':states,
    }
    return render(request, 'admin/stateandcountry.html', context)


def update_country(request, id):
    if request.method == 'POST':
        name = request.POST.get('name')
        country = Country.objects.get(id=id)
        country.name = name
        country.save()
        return redirect('setup_country')
    
    
def delete_country(request, id):
    country = Country.objects.get(id=id)
    country.delete()
    return redirect('setup_country')
    
        
def update_state(request, id):
    if request.method == 'POST':
        name = request.POST.get('name')
        country = request.POST.get('country')
        country_obj = Country.objects.get(id=country)
        
        state = State.objects.get(id=id)
        state.name = name
        state.country = country_obj
        state.save()
        return redirect('setup_country')
    
def delete_state(request, id):
    state = State.objects.get(id=id)
    state.delete()
    return redirect('setup_country')

    
def coupon(request):
    Coupons = []
    if request.GET.get('search_coupon'):
        value = request.GET.get('search_coupon')
        Coupons = Coupon.objects.filter(name__icontains = value)    
    elif request.GET.get('filter_coupon'):
        value = request.GET.get('filter_coupon')
        if value == 'name':
            Coupons = Coupon.objects.all().order_by('name')
        elif value == 'active':
            Coupons = Coupon.objects.all().order_by('-is_active')
        elif value == 'expiry_date':
            Coupons = Coupon.objects.all().order_by('expired_date')
        elif value == 'discounted_price':
            Coupons = Coupon.objects.all().order_by('-discount_price')
    else:
        Coupons = Coupon.objects.all().order_by('-id')
    context = {
        'Coupons':Coupons 
    }
    return render(request, 'admin/admincoupon.html', context)
    
def add_coupon(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        count = request.POST.get('count')
        expiry_date = request.POST.get('expiry_date')
        discounted_price = request.POST.get('discounted_price')
        is_active = request.POST.get('is_active', False)
        is_active = is_active == 'on'
        is_percentage = request.POST.get('is_percentage', False)
        is_percentage = is_percentage == 'on' 
        Coupon.objects.create(name = name, count = count, expired_date = expiry_date, discount_price = discounted_price, is_active = is_active, is_percentage = is_percentage)
        return redirect('coupon')
    
def update_coupon(request, id):
    if request.method == 'POST':
        data = Coupon.objects.get(id=id)
        data.name = request.POST.get('name')
        data.count = request.POST.get('count')
        data.expired_date = request.POST.get('expiry_date')
        data.discount_price = request.POST.get('discounted_price')
        data.is_active = request.POST.get('is_active', False)
        data.is_active = data.is_active == 'on'
        data.is_percentage = request.POST.get('is_percentage', False)
        data.is_percentage = data.is_percentage == 'on'
        data.save()
        return redirect('coupon')
    
def delete_coupon(request, id):
    Coupon.objects.get(id=id).delete()
    return redirect('coupon')
    
def couponactivate(request, id):   
    coupon = Coupon.objects.get(id=id)   
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'active':
            coupon.is_active = True
            coupon.save()
        elif action == 'nonactive':
            coupon.is_active = False
            coupon.save()  
        return redirect('coupon')
       
def admin_order_detail_page(request, id):
    name = ''
    order_instance = Order.objects.get(id=id)
    user = User.objects.get(id=order_instance.user_id)
    if user:
        user_full_name = User.objects.filter(id=user.id).annotate(full_name=Concat(F('first_name'), Value(''), F('last_name') )).first()   
    if user_full_name:
            name = user_full_name.full_name
    shipping_addresses = None   
    if order_instance.is_shipping:
        shipping_addresses = order_instance.shippingaddress_set.all()
    product_item = OrderItem.objects.filter(order_id=id)
    product_bucket = []
    for i in product_item:   
        id = i.product_id
        pdt = FitProduct.objects.get(id=id)
        images = ProductImage.objects.filter(product_id=id).first()
        image = None
        if images:
            image = images.image.url
        product_bucket.append({
            'name':pdt.name,
            'price':pdt.price,
            'image':image
        })
    context = {
        'order_instance' :order_instance,
        'shipping_addresses':shipping_addresses,
        'product_bucket':product_bucket,
        'name' :name,
        'phone':user.phone,
    }
    return render(request, 'admin/adminorderdetailpage.html', context)

def cancel_order(request, id):
    order = Order.objects.get(id=id)
    user_obj = User.objects.get(id=order.user_id)
    wallet = Wallet.objects.create(user=user_obj)
    order.status = 5
    order.save()
    if order.status == 5:
        if wallet:
            total= Decimal(order.total_amout)
            amount = Decimal(wallet.amount)
            wallet.amount = amount + total
            wallet.order = order
            wallet.save()
    return redirect('admin_order')

def offers(request):
    offers = []
    category = Category.objects.all()
    if request.GET.get('search_offer'):
        value = request.GET.get('search_offer')
        offers = Offer.objects.filter(name__icontains=value).select_related('category').filter(is_deleted=False)
        value = request.GET.get('filter_offer')
        if value == 'name':
           offers= Offer.objects.all().order_by('name').select_related('category').filter(is_deleted=False)
        elif value == 'category':
           offers= Offer.objects.all().order_by('category').select_related('category').filter(is_deleted=False)
        elif value == 'active':
           offers= Offer.objects.all().order_by('is_active').select_related('category').filter(is_deleted=False)
        elif value == 'expiry_date':
           offers= Offer.objects.all().order_by('expired_date').select_related('category').filter(is_deleted=False)
        elif value == 'discounted_price':
           offers= Offer.objects.all().order_by('discount_price').select_related('category').filter(is_deleted=False) 
    else:
        offers = Offer.objects.all().select_related('category').filter(is_deleted=False)
    context = {
        'offers':offers,
        'category':category,
    }
    return render(request, 'admin/adminoffer.html', context)

def add_offer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        expired_date = request.POST.get('expiry_date')
        discount_price = request.POST.get('discounted_price')
        is_active = request.POST.get('is_active', False)
        is_active = is_active == 'on'
        is_percentage = request.POST.get('is_percentage', False)
        is_percentage = is_percentage == 'on'
        if category:
            category_obj = Category.objects.get(id=category)
            Offer.objects.create(
                name = name,
                category = category_obj,
                expired_date = expired_date,
                discount_price  = discount_price,
                is_percentage =is_percentage,
                is_active = is_active,
            ) 
        else:
            Offer.objects.create(
                name = name,
                expired_date = expired_date,
                discount_price  = discount_price,
                is_percentage =is_percentage,
                is_active = is_active,
            ) 
        return redirect('offers')
    
def activate_offer(request, id):
    offer = Offer.objects.get(id=id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'nonactive':
            offer.is_active = False
            offer.save()   
        elif action == "active":
            offer.is_active = True
            offer.save()    
        return redirect('offers')
     
def update_offer(request, id):
    offer = Offer.objects.get(id=id)
    if request.method == 'POST':
        offer.name = request.POST.get('name')
        category = request.POST.get('category')
        offer.expired_date = request.POST.get('expiry_date')
        offer.discount_price  = request.POST.get('discounted_price')
        is_active = request.POST.get('is_active', False)
        is_active = is_active == 'on'
        offer.is_active = is_active
        is_percentage = request.POST.get('is_percentage', False)
        is_percentage = is_percentage == 'on'
        offer.is_percentage = is_percentage
        if category:  
            category_obj = Category.objects.get(id=category)
            offer.category= category_obj
        else:
            pass
        offer.save()
        
        return redirect('offers')
        
def offer_delete(request, id):
    offer = Offer.objects.get(id=id)
    offer.is_deleted = True
    offer.save()
    return redirect('offers')

