from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth import authenticate, login, logout, get_user_model
User = get_user_model()
from django.db.models import Q
import smtplib
from smtplib import SMTPConnectError, SMTPResponseException, SMTPAuthenticationError
from decouple import config
import secrets
import random
from decimal import Decimal
from django.core.validators import validate_email
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import copy
from django.conf import settings
import re
from django.core.exceptions import ValidationError
from product.models import Cart, CartItem, FitProduct, WishList, WishListItem, Order, ShippingAddress, OrderItem, ProductImage, Wallet
from accounts.models import State, Country, Address, CustomUser, Notifications
from django.db.models import F, Value
from django.db.models.functions import Concat  
from django.core import serializers
from django.db.models.signals import post_save
from django.dispatch import receiver
import json
import datetime
import urllib.parse   
import reportlab
import io
import os
from django.http import FileResponse
from reportlab.pdfgen import canvas


# user registration, need to validate using OTP, then only user can register
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def register(request):
    if 'email' in request.session:
        return redirect('home')
    elif 'adminemail' in request.session:
        return redirect('ahome')
    # post request, checking a few conditions in post request before registering user and also there is a error messages if required, it will shows in html page based on the error
    elif request.method == 'POST':
        email = request.POST.get('Email')
        first_name = request.POST.get('First_name')
        last_name = request.POST.get('Last_name')
        phone_number = request.POST.get('Phone_number')
        password1 = request.POST.get('Password1')
        password2 = request.POST.get('Password2')
        referral_code = request.POST.get('referralcode')
        # checking all data is given by user
        if not all([email, first_name and last_name  and phone_number and password1 and password2]):
            messages.info(request, "Please fill in all the required fields")
        elif password1 != password2:  
             messages.info(request, "password not matching")
        # if all data and password1 and 2 is matching, then trying to validate email
        else:
            try:
                validate_email(email)
            except ValidationError:
                messages.info(request, "Please enter a valid email address")
            else:    
                # checking user existence in database
                if User.objects.filter(email=email).exists():
                    messages.info(request, "Email ID already taken")
                # if refferal available, add it in session for further use
                elif referral_code:
                    refered = CustomUser.objects.filter(referral_code = referral_code).first()
                    if refered:
                        request.session['refered'] = serializers.serialize('json', [refered])
                    else:
                        messages.info(request, "Please enter correct referal code")
                        return redirect('register')
                message = generate_otp()
                receiver_mail = email
                sender_email = config('sender_email', default='')
                password = config('password', default='')
                # sending email to user and handling exception if required
                try:
                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.starttls()
                        server.login(sender_email, password)
                        server.sendmail(sender_email, receiver_mail, message)      
                except SMTPConnectError:
                    messages.error(request, 'Failed to connect to the SMTP server.')
                except SMTPAuthenticationError:
                    messages.error(request, 'Failed to send OTP email. Please check your email configuration.')
                    return redirect('register')
                # saving user without activating, once the user submit OTP, we will make the user active
                user = User.objects.create_user( email=email, first_name=first_name, last_name=last_name, phone=phone_number, is_active = False)
                user.set_password(password1)
                user.save()
                request.session['email'] =  email
                request.session['otp']   =  message
                messages.success (request, 'OTP is sent to your email')
                return redirect('verify_signup')
    return render(request, 'user/signup.html')

# generate OTP for sending OTP
def generate_otp(length = 6):      
    return ''.join(secrets.choice("0123456789") for i in range(length)) 

# OTP verify and registering user here
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def verify_signup(request):
    message_data = messages.get_messages(request)
    context = {
        'messages' : message_data,
    } 
    if request.method == 'POST':
        email = request.session.get('email')
        code = request.session.get('otp')
        OTP = request.POST.get('otp')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.info(request, 'User not found')
            return redirect('register')
        # User entered OTP and generated OTP cross check, if matching   
        if OTP == code:
            user.is_active = True
            user.save()
            # After activating user, taking the refferal data and doing action like wallet amount increase for refferer and updating user section in database.
            refered_json = request.session.get('refered')
            if refered_json:
                refered_deserialize_obj = list(serializers.deserialize('json', refered_json))
                if refered_deserialize_obj:
                    refered = refered_deserialize_obj[0].object
                    Wallet.objects.create(user=refered, amount = 100)  
                    message = "The refferal amount of 100 RS credited to your wallet"
                    Notifications.objects.create(user=refered, message=message)
                    user.refered_by = refered
                    user.is_referred = True
                    user.save()
                    del request.session['refered']
            del request.session['email']
            del request.session['otp']
            messages.info(request, 'signup successful')
            return redirect('login')
        else:
            user.delete()
            messages.info(request, 'invalid otp')
            del request.session['email']
            del request.session['otp']
            return redirect('register')
    return render(request,'user/verify_otp.html', context)
    
def validate_phone_number(value):
    phone_number_regex = re.compile(r"^(?:\+?91[\-\s]?)?[789]\d{9}$")
    if phone_number_regex.match(value):
        return True
    else:
        return False  
    
# whoever registered, they can log in with OTP only
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def login_user(request):
    next_url = request.GET.get('next')
    if next_url is not None:
        request.session['next_url'] = next_url
    if 'email' in request.session:
        return redirect('home')
    elif 'adminemail' in request.session:
        return redirect('ahome')
    elif request.method == 'POST':
        input_value  = request.POST.get('input')
        if not input_value :
            messages.info(request, 'please fill the email ID or Phone Number')
            return redirect('login')
        is_mobile = validate_phone_number(input_value )
        # mobile is a bool true from validation
        if is_mobile:
            user = None
            try:
                user = User.objects.get(phone=input_value )
            except User.DoesNotExist:
                messages.info(request, 'Invalid phone number')
                return redirect('login')
            request.session['email'] = user.email
            return redirect('verify_signin')
        # email process started
        elif '@' in input_value:
            try:
                user = User.objects.filter(email = input_value).first()
            except User.DoesNotExist:
                messages.info(request, "Enter a valid email ID")
                return redirect('login')
            message = generate_otp()
            receiver_mail = input_value
            sender_email = config('sender_email', default='')
            password = config('password', default='')
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_mail, message)       
            except SMTPConnectError:
                messages.error(request, 'Failed to connect to the SMTP server.')     
            except smtplib.SMTPAuthenticationError:
                messages.error(request, 'Failed to send OTP email. Please check your email configuration.')
                return redirect('login')
            request.session['email'] =  input_value
            request.session['otp']   =  message
            messages.success (request, 'OTP is sent to your email')
            return redirect('verify_signin_email')
        else:
            messages.info(request, 'Please enter a valid email or mobile number')
            return redirect('login')              
        
    return render(request, 'user/signin.html')

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def verify_signin(request):
    try:
        if 'sent_otp' not in request.session:
            otp = random.randint(1000, 9999)  # Generate a random OTP
            request.session['sent_otp'] = otp
            email = request.session['email'] 
            try:
                user = User.objects.get(email=email)
                phone_number = user.phone
            except User.DoesNotExist:
                messages.info(request, 'User not found')
            phone = str(phone_number)
            # using TWILIO for mobile OTP
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            msg = client.messages.create(body=f"Your OTP is: {otp}",from_="+16187624743",to = phone)
        # checking user entered OTP with shared OTP via twilio
        if request.method == 'POST':
            user_provided_otp = request.POST.get('mobileotp')  
            if 'email' in request.session:
                email = request.session.get('email')
                user = User.objects.filter(email=email).first()
                if not user:
                    raise ValidationError("User not found")  
                stored_otp = request.session['sent_otp']
                if int(user_provided_otp) == stored_otp:
                    messages.info(request, 'Signin successful')
                    login(request, user)
                    del request.session['sent_otp']
                # if any cartdata, transfer to cartitem database
                    email=request.session['email']
                    user_obj = User.objects.get(email=email)
                    if 'cartdata' in request.session:
                        id = user_obj.id
                        user_cart, created = Cart.objects.get_or_create(user=user_obj)
                        session_cart = request.session['cartdata']
                        for product_id, item in session_cart.items():
                            product_obj = FitProduct.objects.get(id=product_id)
                            product_id = product_obj.id
                            existing_cart_item = CartItem.objects.filter(cart=user_cart, product=product_id).first()
                            if existing_cart_item:
                                if int(existing_cart_item.quantity) > int(item['qty']):
                                    existing_cart_item.quantity = int(existing_cart_item.quantity)
                                else:
                                    existing_cart_item.quantity = int(item['qty'])
                                existing_cart_item.save()
                            else:  
                                CartItem.objects.create(cart=user_cart,product=product_obj,quantity=int(item['qty']))
                    if 'wishdata' in request.session:
                        id = user_obj.id
                        user_wishbucket, created = WishList.objects.get_or_create(user=user_obj)
                        session_wish_data = request.session['wishdata']
                        for product_id, item in session_wish_data.items():
                            product_obj = FitProduct.objects.get(id=item['id'])
                            product_id = product_obj.id
                            existing_wish_item = WishListItem.objects.filter(wishlist=user_wishbucket, product=product_id).first()
                            if not existing_wish_item: 
                                WishListItem.objects.create(wishlist = user_wishbucket,product=product_obj)            
                    if 'next_url' in request.session:
                        return redirect('check_out')
                    else:
                        return redirect('home')  
                else:
                    messages.error(request, 'Invalid OTP, please try again')
                    del request.session['email']
                    del request.session['sent_otp']
                    return redirect('login')
            else:
                # session expired, redirecting to login
                del request.session['email']
                del request.session['sent_otp']
                messages.error(request, 'Session expired, please try again')
                return redirect('login')        
    except TwilioRestException as e:
        del request.session['email']
        del request.session['sent_otp'] 
    return render(request, 'user/verify_sigin.html')
    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def verify_signin_email(request):
    message_data = messages.get_messages(request)
    context = {
        'messages' : message_data,
    }
    if request.method == 'POST':
        email = request.session.get('email')
        user = User.objects.get(email=email)
        code = request.session.get('otp')
        OTP= request.POST.get('emailotp')
        if OTP == code:
            del request.session['otp']
            messages.info(request, 'signup successful')
            login(request, user)
            email=request.session['email']
            user_obj = User.objects.get(email=email)
            # updating cart with cartdata
            if 'cartdata' in request.session:
                id = user_obj.id
                user_cart, created = Cart.objects.get_or_create(user=user_obj)
                session_cart = request.session['cartdata']
                for product_id, item in session_cart.items():
                    product_obj = FitProduct.objects.get(id=product_id)
                    product_id = product_obj.id
                    existing_cart_item = CartItem.objects.filter(cart=user_cart, product=product_id).first()
                    if existing_cart_item:
                        if int(existing_cart_item.quantity) > int(item['qty']):
                            existing_cart_item.quantity = int(existing_cart_item.quantity)
                            existing_cart_item.save()
                        else:
                            existing_cart_item.quantity = int(item['qty'])
                            existing_cart_item.save()
                    else: 
                        CartItem.objects.create(cart=user_cart,product=product_obj,quantity=int(item['qty']))
            if 'wishdata' in request.session:
                id = user_obj.id
                user_wishbucket, created = WishList.objects.get_or_create(user=user_obj)
                session_wish_data = request.session['wishdata']
                for product_id, item in session_wish_data.items():
                    product_obj = FitProduct.objects.get(id=item['id'])
                    product_id = product_obj.id
                    existing_wish_item = WishListItem.objects.filter(wishlist=user_wishbucket, product=product_id).first()
                    if not existing_wish_item: 
                        WishListItem.objects.create(wishlist = user_wishbucket, product=product_obj)
            if 'next_url' in request.session:
                return redirect('check_out')     
            else:
                return redirect('home')
        else:
            messages.info(request, 'invalid otp')
            del request.session['email']
            del request.session['otp']
            return redirect('login')
    return render(request,'user/verify_otpforsignin.html')
       
# signout of admin or user  - cleared session and logout done here
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def signout(request):
    if 'email' in request.session:
        cart_data = request.session.get(settings.CART_SESSION_ID, {})
        wish_data = request.session.get(settings.WISHLIST_SESSION_ID, {})
        cart_counter = request.session.get(settings.CARTCOUNTER_SESSION_ID, {})
        del request.session['email']
        logout(request)
        if cart_data:
            request.session[settings.CART_SESSION_ID] = cart_data
            request.session.modified = True
        if wish_data:
            request.session[settings.WISHLIST_SESSION_ID] = wish_data
            request.session.modified = True
        if cart_counter:
           request.session[settings.CARTCOUNTER_SESSION_ID] = cart_counter   
           request.session.modified = True
    elif 'adminemail' in request.session:
        del request.session['adminemail']
    elif 'next_url' in request.session:
        del request.session['next_url']  
    return redirect('home')

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs): 
    if created:
        user = instance.user
        message = f"Your order with Order ID {instance.id} has been received."
        Notifications.objects.create(user=user, message=message)
               
def datetime_serializer(obj):
            if isinstance(obj, datetime.datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
# user dashbord/profile page     
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache  
def myaccount(request):
    if 'adminemail' in request.session:
        return redirect('ahome')
    else:
        email = request.session['email']
        refer = CustomUser.objects.get(email=email)
        referral_code = refer.referral_code
        query = f"You can register using my referral and earn 50 RS.\n\nMy referral code is {referral_code}.\n\nRegister here: {'http://127.0.0.1:8000/accounts/register/'}"
        data = urllib.parse.quote(query)
        notifications = list(Notifications.objects.filter(user=refer).values('message', 'timestamp').order_by('-timestamp'))
        for item in notifications:
            item['timestamp'] = datetime_serializer(item['timestamp'])
        request.session['notifications'] = notifications
        request.session.save() 
        context = {
            'referral_code': referral_code,
            'data': data,
        }
        return render(request, 'user/userindex.html',context)
def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('Email')
        if not email:
            messages.info(request, "Please enter your email ID")
        # if email is available, send OTP  
        else:
            try:
                validate_email(email)
            except ValidationError:
                messages.info(request, "Please enter a valid email address")
            else:
                user_exists = User.objects.filter(email=email).exists()
                if not user_exists:
                    messages.info(request, "Please enter valid email ID")
                else:
                    message = generate_otp()
                    receiver_mail = email
                    sender_email = config('sender_email', default='')
                    password = config('password', default='')
                    try:
                        with smtplib.SMTP("smtp.gmail.com", 587) as server:
                            server.starttls()
                            server.login(sender_email, password)
                            server.sendmail(sender_email, receiver_mail, message)
                    except smtplib.SMTPAuthenticationError:
                        messages.error(request, 'Failed to send OTP email. Please check your email configuration.')
                        return redirect('reset_password')
                    request.session['email'] =  receiver_mail
                    request.session['otp']   =  message
                    messages.success (request, 'OTP is sent to your email')
                    return redirect('verify_resetotp') 
    return render(request, 'user/resetPassword.html')

def verify_resetotp(request):
    email = request.session.get('email')  
    if request.method == 'POST':
        user = User.objects.get(email = email)
        code = request.session.get('otp')
        OTP= request.POST.get('otp')
        # if user is active only, we are checking OTP
        if user.is_active == True:
            if OTP == code:
                return redirect('verify_password')
            else:
                messages.info(request, 'invalid otp')
                del  request.session['email']
                del request.session['otp']  
                return redirect('reset_password')        
        else:
            messages.info(request, 'the user is already blocked')
            del  request.session['email']
            del request.session['otp']  
            return redirect('reset_password')
    return render(request, 'user/passwordOtp.html')

def verify_password(request):
    if request.method == 'POST':
        password1  =request.POST.get('Password1')
        password2  =request.POST.get('Password2')
        if password1 == password2:
            email = request.session.get('email')
            if email:
                user = User.objects.get(email=email)
                user.set_password(password1)
                user.save()
                del request.session['email']
                del request.session['otp']
                return redirect('login')
        else:
            messages.info(request, 'invalid email ID')
    return render(request,'user/verifyPassword.html')

def user_order(request):
    # Dashborad - Orders
    email = request.session.get('email')
    user_obj = User.objects.get(email=email)
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
                    'total':total           
                })       
    elif request.GET.get('filter_order'):
        orders = []
        value = request.GET.get('filter_order')
        if value == 'Status':
            orders = Order.objects.filter(user_id=user_obj).values('id', 'created_at', 'status', 'total_amout').order_by('status') 
        elif value == 'ID':
            orders = Order.objects.filter(user_id=user_obj).values('id', 'created_at', 'status', 'total_amout').order_by('id') 
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
    else:
        orders = Order.objects.filter(user_id=user_obj).values('id', 'created_at', 'status', 'total_amout').order_by('-id')
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
    context = {
        'order_info': order_info,
    }
    return render(request, 'user/userorder.html', context)
    

def order_detail_page(request, id):
    name = ''
    email = request.session['email']
    if email:
        user = User.objects.get(email=email)
        user_full_name = User.objects.filter(id=user.id).annotate(full_name=Concat(F('first_name'), Value(''), F('last_name') )).first()   
    if user_full_name:
            name = user_full_name.full_name
    shipping_addresses = None   
    order_instance = Order.objects.get(id=id)
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
    return render(request, 'user/userorderdetailpage.html', context)

def user_profile(request):
    countries = Country.objects.all().order_by('name')
    states = State.objects.all().order_by('name')
    email_id = request.session['email']
    user_obj = User.objects.get(email =email_id)
    addresses = Address.objects.filter(Q(user=user_obj) & Q(is_deleted = False)).select_related('state', 'country').order_by('-id')
    if request.method == 'POST':
        if 'update_user' in request.POST:
            user_obj.email = request.POST.get('Email')
            user_obj.first_name = request.POST.get('First_name')
            user_obj.last_name = request.POST.get('Last_name')
            user_obj.phone = request.POST.get('Phone_number')
            user_obj.save()
            message = "You profile has been updated"
            Notifications.objects.create(user=user_obj, message = message)
    if request.method == 'POST':
        if 'add_address' in request.POST:
            first_name = request.POST.get('First_name')
            last_name = request.POST.get('Last_name')
            email = request.POST.get('Email')
            phone_number = request.POST.get('Phone_number')
            addressline1 = request.POST.get('Addressline1')
            addressline2 = request.POST.get('Addressline2')
            city = request.POST.get('City')
            state = request.POST.get('State')
            country = request.POST.get('Country')
            pin = request.POST.get('pin')
            state_obj = State.objects.get(id = state)
            country_obj = Country.objects.get(id = country)   
            Address.objects.create(
                user = user_obj,
                first_name = first_name,
                last_name = last_name,
                email = email,
                phoneNumber = phone_number,
                addressline1 = addressline1,
                addressline2 = addressline2,
                city = city,
                state = state_obj,
                country = country_obj,
                pin = pin,
                )
            message = "A new address has been added to your profile"
            Notifications.objects.create(user=user_obj, message=message)
            source = request.POST.get('source', '')
            if source == 'checkout':  
                # Redirect to the checkout page after coming from checkout
                return redirect('check_out')
            else:
                # Redirect to the user profile page
                return redirect('user_profile')
    context = {
        'countries':countries,
        'states': states,
        'addresses':addresses,
        'user_obj':user_obj,
    }
    return render(request, 'user/userprofileaddress.html', context)

def updateAddress(request, id):
    email = request.session['email']
    user_obj = User.objects.get(email=email)
    if request.method == 'POST':
        address = Address.objects.get(id=id)
        address.first_name = request.POST.get('First_name')
        address.last_name = request.POST.get('Last_name')
        address.email= request.POST.get('Email')
        address.phoneNumber= request.POST.get('Phone_number')
        address.addressline1= request.POST.get('Addressline1')
        address.addressline2= request.POST.get('Addressline2')
        address.city= request.POST.get('City')
        state= request.POST.get('State')
        country= request.POST.get('Country')
        address.pin= request.POST.get('pin')
        address.state = State.objects.get(id = state)
        address.country = Country.objects.get(id = country)
        address.save()
        message = f"Address of the {address.first_name} has been updated"
        Notifications.objects.create(user=user_obj, message=message)
        return redirect('user_profile')
      
def deleteAddress(request, id):
    address  = Address.objects.get(id=id)    
    address.is_deleted = True
    address.save()
    return redirect('user_profile')
      
def user_cancel_order(request, id):
    try:
        email = request.session['email']
        user_obj = User.objects.get(email=email)
        order = Order.objects.get(id=id)
        order.status = 5
        order.save()
        if order.status == 5:
            if order.payment_method !="COD":
                wallet = Wallet.objects.create(user=user_obj)
                if wallet:
                    total= Decimal(order.total_amout)
                    amount = Decimal(wallet.amount)
                    wallet.amount = amount + total
                    wallet.order = order
                    wallet.save()
                    message = f"The order has been canceled for the id : {id} and the amount {order.total_amout} trandferred to your wallet "
                    Notifications.objects.create(user=user_obj, message=message)
        return redirect('user_order')
    except KeyError:
        messages.info(request, 'session expired, please re-login')
        return redirect('login')

def wallet(request):
    email = request.session['email']
    user_obj = User.objects.get(email=email)
    wallet = Wallet.objects.filter(user=user_obj)
    debit_total = Decimal(0.00)
    credit_total = Decimal(0.00)
    total= Decimal(0.00)
    for item in wallet:
        if item.is_credit:
            credit_total += item.amount
        else:
            debit_total+= item.amount
    total = credit_total - debit_total
    context = {
        'wallet': wallet,
        'total':total    
    }
    return render(request, 'user/userwallet.html', context)

def generate_pdf(request, id):
    
    name = ''
    email = request.session['email']
    if email:
        user = User.objects.get(email=email)
        user_full_name = User.objects.filter(id=user.id).annotate(full_name=Concat(F('first_name'), Value(''), F('last_name') )).first()   
    if user_full_name:
            name = user_full_name.full_name
    shipping_addresses = None   
    order_instance = Order.objects.get(id=id)
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
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer)
    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(100, 750, f"order id: {order_instance.id}")
    p.drawString(100, 730, f"Ordered date: {order_instance.created_at}")
    p.drawString(100, 710, f"User Name: {name}")
    p.drawString(100, 690, f"User Phone: {user.phone}")
    if order_instance.status == 1:
        ord_status = "Order Initiated"
    elif order_instance.status == 2:
        ord_status = "Order eProcessing"
    elif order_instance.status == 3:
        ord_status = "Shipped"
    elif order_instance.status == 4:
        ord_status = "Delivered"
    else:
        ord_status = "Cancelled"    
    p.drawString(100, 650, f"Status of the order: {ord_status}")
    p.drawString(100, 630, f"Address Line 1: {order_instance.billing_address1}")
    p.drawString(100, 610, f"Address Line 2: {order_instance.billing_address2}")
    p.drawString(100, 590, f"City: {order_instance.billing_city}")
    p.drawString(100, 570, f"State: {order_instance.billing_state}")
    p.drawString(100, 550, f"Country: {order_instance.billing_country}")
    p.drawString(100, 525, f"Payment Method: {order_instance.payment_method }")
    if order_instance.discount:
        p.drawString(100, 500, f"Coupon Dicount: {order_instance.discount}")     
    p.drawString(100, 480, f"Tax: {order_instance.tax}")
    p.drawString(100, 460, f"Shipping Charge: {order_instance.shipping_charge}")
    p.drawString(100, 440, f"Total Amount: {order_instance.total_amout}")
    if shipping_addresses:
        print(shipping_addresses)
        print("sdsdsdsdsds")
        for shipping in shipping_addresses:
            p.drawString(100, 410, f"Shipping address 1 : {shipping.addressline1}")
            p.drawString(100, 390, f"Shipping address 2: {shipping.addressline2}")
            p.drawString(100, 370, f"City: {shipping.city}")
    if product_bucket:
        print(product_bucket)
        y_position = 360
        for product in product_bucket:
            p.drawString(x=100, y =y_position- 20, text=f"Product name : {product['name']}")
            y_position-=20
            p.drawString(x=100, y=y_position-20, text=f"Product price: {product['price']}")
            y_position-=20        
    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Order details for the order id: {order_instance.id}.pdf")