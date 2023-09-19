
from django.urls import path
from . import views

urlpatterns = [
    path('', views.adminsignin, name = 'adminsignin'),
    path('home/', views.ahome, name = 'ahome'),
    path('users/', views.users, name = 'users'),
    path('users/block/<int:id>/', views.handle_user_status, name='block'),
    path('products', views.product, name = 'product'),
    path('product/activate/<int:id>/', views.productactivate,name = 'productactivate'),
    path('add-product/', views.createProduct, name='add-product'),
    path('update-product/<int:id>/', views.updateProduct, name='update-product'),
    path('delete-product/<int:id>/', views.deleteProduct, name='delete-product'),
    path('all-category', views.all_category, name = 'all_category'),
    path('add-category/', views.createCetegory, name='add-category'),
    path('update-category/<int:id>/', views.updateCategory, name='update-category'),
    path('delete-category/<int:id>/', views.deleteCategory, name='delete-category'),
    path('admin-order/', views.admin_order, name="admin_order"),
    path('admin-order-detail-page/<int:id>', views.admin_order_detail_page, name="admin_order_detail_page"),
    path('admin-cancel-order/<int:id>/', views.cancel_order, name='cancel_order'),
    path('admin-sales-report/', views.admin_sales_report, name="admin_sales_report"),
    path('download/', views.download_filtered_sales, name='download_filtered_sales'),
    path('coupon/', views.coupon, name='coupon'),
    path('add-coupon/', views.add_coupon, name='add_coupon'),
    path('update-coupon/<int:id>/', views.update_coupon, name='update_coupon'),
    path('delete-coupon/<int:id>/', views.delete_coupon, name='delete_coupon'),
    path('coupon/activate/<int:id>/', views.couponactivate,name = 'couponactivate'),
    path('offers/', views.offers, name='offers'),
    path('add-offer/', views.add_offer, name='add_offer'),
    path('update-offer/<int:id>/', views.update_offer, name='update_offer'),
    path('offer-delete/<int:id>/', views.offer_delete, name='offer_delete'),
    path('activate-offer/<int:id>/', views.activate_offer, name='activateoffer'),
]
