
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name = 'register'),
    path('login/', views.login_user, name = 'login'),
    path('signout/', views.signout, name = 'signout'),
    path('otp/', views.verify_signup, name='otp'),
    path('verify_otp/',views.verify_signup,name='verify_signup'),
    path('verify_signin/',views.verify_signin,name='verify_signin'),
    path('otp/', views.verify_signin, name='loginotp'),
    path('loginVerify_otps/',views.verify_signin_email,name='verify_signin_email'),
    path('myaccount/', views.myaccount, name="myaccount"),
    path('reset-password/', views.reset_password, name="reset_password"),
    path('verify-resetotp/', views.verify_resetotp, name="verify_resetotp"),
    path('verify-password', views.verify_password, name = "verify_password"),
    path('user-order/', views.user_order, name='user_order'),
    path('order-detail-page/<int:id>/', views.order_detail_page, name='order_detail_page'),
    path('cancel-order/<int:id>/', views.user_cancel_order, name='user_cancel_order'),
    path('user-profile/', views.user_profile, name='user_profile'),
    path('update-address/<int:id>/', views.updateAddress, name='update_address'),
    path('delete-address/<int:id>/', views.deleteAddress, name='delete_address'),
    path('wallet/', views.wallet, name='wallet'),
    path('generate_pdf/<int:id>', views.generate_pdf, name="generate_pdf"),  
]
