from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('register', views.register, name='register'),
    path('log_in', views.log_in, name='log_in'),
    path('log_out', views.log_out, name='log_out'),
    path('business_create', views.business_create, name='business_create'),
    path('business_category', views.business_category, name='business_category'),
    path('business_list/<int:category_id>', views.businees_list, name='business_list'),
    path('business/<int:business_id>/', views.business_detail, name='business_detail'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment/click/callback/', views.click_callback, name='click_callback'),
    path('payment/payme/callback/', views.payme_callback, name='payme_callback'),
    path('my_bookings', views.my_bookings, name='my_bookings'),
    path('booking_pdf/<int:booking_id>/', views.booking_pdf, name='booking_pdf'),
    path('set-region/', views.set_user_region, name='set_user_region'),
    path('profile', views.profile, name='profile'),
    path('search/', views.search_view, name='search'),
    path('contact_us', views.contact_us, name='contact_us'),
    path('business_delete/<int:business_id>', views.delete_business, name='business_delete'),
    path('my_businesses', views.my_business, name='my_business'),
    path('business_update/<int:business_id>', views.update_business, name='business_update'),


]