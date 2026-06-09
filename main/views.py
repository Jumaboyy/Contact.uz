from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from . import models

import hashlib
import json
import re
import io
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    A4 = None
    canvas = None
    REPORTLAB_AVAILABLE = False
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from datetime import date


def normalize_phone(raw_phone: str) -> str | None:
    phone = re.sub(r'\D', '', raw_phone)

    if phone.startswith('998') and len(phone) == 12:
        phone = phone[3:]

    if re.fullmatch(r'\d{9}', phone):
        return phone

    return None


def categorize_business_category(category_name: str):
    category_name = category_name.lower() if category_name else ''
    is_pharmacy = 'dorixona' in category_name or 'pharmacy' in category_name
    is_medical_center = any(term in category_name for term in ['tibbiyot', 'medical', 'clinic', 'hospital', 'markaz', 'center'])
    is_museum = any(term in category_name for term in ['muzey', 'museum'])
    is_shopping_center = any(term in category_name for term in ['savdo markazi', 'shopping center', 'shopping mall', 'mall', 'bozor', 'market'])
    is_location_service = (
        is_pharmacy or
        is_medical_center or
        is_museum or
        is_shopping_center or
        any(term in category_name for term in ['bank', 'notarius', 'notary', 'sanatoriya', 'dam olish', 'resort'])
    )
    is_food_service = any(term in category_name for term in ['restoran', 'kafe', 'fast food', 'cafe', 'restaurant'])
    return {
        'is_pharmacy': is_pharmacy,
        'is_medical_center': is_medical_center,
        'is_museum': is_museum,
        'is_shopping_center': is_shopping_center,
        'is_location_service': is_location_service,
        'is_food_service': is_food_service,
    }


# ---------------Auth---------------
def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        # basic validation
        if not username:
            messages.error(request, 'Iltimos, foydalanuvchi nomini kiriting.')
            return render(request, 'auth/register.html')

        if password != password_confirm:
            messages.error(request, 'Parollar mos emas.')
            return render(request, 'auth/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu foydalanuvchi nomi band. Boshqasini tanlang.')
            return render(request, 'auth/register.html')

        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            login(request, user)
            messages.success(request, 'Ro\'yxatdan muvaffaqiyatli o\'tdingiz.')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Registratsiyada xatolik: {str(e)}')
            return render(request, 'auth/register.html')
    return render(request, 'auth/register.html')


def log_in(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
    return render(request, 'auth/auth-login.html')


@login_required(login_url='log_in')
def log_out(request):
    logout(request)
    return redirect('log_in')


@login_required(login_url='log_in')
def profile(request):
    user = request.user
    profile, _ = models.UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        passport_series = request.POST.get('passport_series', '').strip()
        jshshr = request.POST.get('jshshr', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Update user info
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username

        if password1:
            if password1 == password2:
                user.set_password(password1)
                messages.success(request, "Parol muvaffaqiyatli yangilandi.")
            else:
                messages.error(request, "Parollar mos kelmadi.")
                return redirect('profile')

        profile.passport_series = passport_series or None
        profile.jshshr = jshshr or None
        profile.save()

        user.save()
        messages.success(request, "Profil muvaffaqiyatli yangilandi.")
        return redirect('log_in') if password1 else redirect('profile')

    return render(request, 'auth/profile.html', {'user': user, 'profile': profile})


# ---------------Business---------------


@login_required(login_url='log_in')
def business_create(request):
    regions = models.Region.objects.all()
    districts = models.District.objects.all()
    categories = models.BusinessCategory.objects.all()
    context = {
        'regions': regions,
        'districts': districts,
        'categories': categories,
    }

    if request.user.is_authenticated:
        context['user'] = request.user

    if request.method == "POST":
        user = request.user
        name = request.POST.get('name')
        address = request.POST.get('address')
        location = request.POST.get('location', '').strip()
        region_id = request.POST.get('region')
        district_id = request.POST.get('district')
        category_id = request.POST.get('category')
        phone_input = request.POST.get('phone', '')
        phone = normalize_phone(phone_input)

        owner_first_name = request.POST.get('owner_first_name', '').strip()
        owner_last_name = request.POST.get('owner_last_name', '').strip()
        owner_passport = request.POST.get('owner_passport', '').strip()
        commission_input = request.POST.get('commission_percentage', '0')
        try:
            commission_percentage = Decimal(commission_input)
        except (TypeError, ValueError, InvalidOperation):
            commission_percentage = Decimal('0')

        website = request.POST.get('website', '').strip()
        instagram = request.POST.get('instagram', '').strip()

        if phone is None:
            return HttpResponse("❌ Telefon raqam noto'g'ri kiritilgan")

        image = request.FILES.get('image')
        price_input = request.POST.get('price', '0')
        try:
            price = float(price_input)
        except (TypeError, ValueError):
            price = 0
        region = models.Region.objects.get(id=region_id)
        district = models.District.objects.get(id=district_id)
        category = models.BusinessCategory.objects.get(id=category_id)

        business = models.Business.objects.create(
            user=user,
            name=name,
            address=address,
            location=location,
            owner_first_name=owner_first_name or None,
            owner_last_name=owner_last_name or None,
            owner_passport=owner_passport or None,
            phone=phone,
            region=region,
            district=district,
            image=image,
            category=category,
            price=price,
            website=website or None,
            instagram=instagram or None,
            commission_percentage=commission_percentage,
        )
        return redirect('home')
    return render(request, 'bussines/create.html', context=context)


def home(request):
    categories = models.BusinessCategory.objects.all()
    # limit and select_related to avoid N+1 when rendering latest cards
    latest_businesses = list(models.Business.objects.select_related('region', 'district').prefetch_related('room_images').order_by('-id')[:12])
    # attach single room image url to avoid calling queryset methods in templates
    for biz in latest_businesses:
        single = biz.room_images.filter(room_type='Single (SGL)').first()
        biz.single_room_image_url = single.image.url if single and getattr(single, 'image', None) else None
    businesses = models.Business.objects.all().count()
    regions = models.Region.objects.all().count()
    users = User.objects.all().count()
    context = {
        'categories': categories,
        'businesses_count': businesses,
        'regions_count': regions,
        'users_count': users,
        'latest_businesses': latest_businesses
    }
    return render(request, 'index.html', context=context)


@login_required(login_url='log_in')
def business_category(request):
    categories = models.BusinessCategory.objects.all()
    regions = models.Region.objects.all()
    districts = models.District.objects.all()
    user_region = models.UserRegion.objects.filter(user=request.user).first()

    context = {
        'categories': categories,
        'regions': regions,
        'districts': districts,
        'user_region': user_region,
    }
    return render(request, 'bussines/category.html', context=context)


@login_required(login_url='log_in')
def businees_list(request, category_id):
    user_region = models.UserRegion.objects.filter(user=request.user).first()
    category = models.BusinessCategory.objects.get(id=category_id)

    regions = models.Region.objects.all()
    districts = models.District.objects.all()

    context = {
        'category': category,
        'regions': regions,
        'districts': districts,
        'user_region': user_region,
    }

    # Use select_related to avoid per-row queries in templates (region/district)
    if user_region:
        region = user_region.region
        if user_region.district:
            district = user_region.district
            qs = models.Business.objects.filter(
                category=category,
                region=region,
                district=district
            )
        else:
            qs = models.Business.objects.filter(category=category, region=region)
    else:
        qs = models.Business.objects.filter(category=category)

    qs = qs.select_related('region', 'district').prefetch_related('room_images')

    # add simple pagination to avoid rendering too many items at once
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    page = request.GET.get('page', 1)
    paginator = Paginator(qs, 20)
    try:
        businesses_page = paginator.page(page)
    except PageNotAnInteger:
        businesses_page = paginator.page(1)
    except EmptyPage:
        businesses_page = paginator.page(paginator.num_pages)

    # attach single_room_image_url for each business on the page
    for biz in businesses_page.object_list:
        single = biz.room_images.filter(room_type='Single (SGL)').first()
        biz.single_room_image_url = single.image.url if single and getattr(single, 'image', None) else None

    context['businesses'] = businesses_page

    # provide Stripe publishable key for Elements if configured
    from django.conf import settings as _settings
    context['STRIPE_PUBLISHABLE_KEY'] = getattr(_settings, 'STRIPE_PUBLISHABLE_KEY', '')
    return render(request, 'bussines/list.html', context=context)


@login_required(login_url='log_in')
def set_user_region(request):
    region_id = request.GET.get('region')
    district_id = request.GET.get('district')

    user_region, created = models.UserRegion.objects.get_or_create(user=request.user)

    if region_id:
        user_region.region = models.Region.objects.get(id=region_id)

        if district_id:
            user_region.district = models.District.objects.get(id=district_id)
        else:
            user_region.district = None

        user_region.save()
    else:
        user_region.delete()

    return redirect(request.META.get('HTTP_REFERER', '/'))


def search_view(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = models.Business.objects.filter(
            name__icontains=query
        ) | models.Business.objects.filter(
            category__name__icontains=query
        ) | models.Business.objects.filter(
            district__name__icontains=query
        )

    # select_related where possible to reduce DB hits when rendering
    results = results.distinct().select_related('region', 'district', 'category')
    return render(request, 'search_results.html', {
        'results': results,
        'query': query
    })


@login_required(login_url='log_in')
def business_detail(request, business_id):
    business = get_object_or_404(models.Business, id=business_id)
    user_region = models.UserRegion.objects.filter(user=request.user).first() if request.user.is_authenticated else None

    category_flags = categorize_business_category(business.category.name)
    is_food_service = category_flags['is_food_service']
    is_pharmacy = category_flags['is_pharmacy']
    is_medical_center = category_flags['is_medical_center']
    is_location_service = category_flags['is_location_service']
    is_hotel = 'mehmonxona' in business.category.name.lower()

    if request.method != 'POST':
        return redirect('business_list', category_id=business.category.id)

    profile, _ = models.UserProfile.objects.get_or_create(user=request.user)
    if not request.user.first_name or not request.user.last_name or not profile.passport_series or not profile.jshshr:
        messages.error(request, 'Zakaz berish uchun profilga ism, familiya, pasport seriyasi va JSHSHR kiriting.')
        return redirect('profile')

    check_in = request.POST.get('check_in')
    check_out = request.POST.get('check_out')
    guests = request.POST.get('guests')
    payment_method = request.POST.get('payment_method')
    booking_type = request.POST.get('booking_type', 'reservation')
    if is_food_service:
        booking_type = 'reservation'
        payment_method = 'cash'
    seats = request.POST.get('seats')
    reservation_area = request.POST.get('reservation_area', '').strip()
    reservation_time = request.POST.get('reservation_time', '').strip()
    room_type = request.POST.get('room_type', '').strip()
    delivery_address = request.POST.get('delivery_address', '').strip()
    contact_phone = request.POST.get('contact_phone', '').strip()

    if not guests or (booking_type != 'delivery' and not check_in):
        messages.error(request, 'Iltimos, barcha maydonlarni to‘ldiring.')
        return redirect('business_list', category_id=business.category.id)

    if booking_type == 'delivery' and (not delivery_address or not contact_phone):
        messages.error(request, 'Dostafka uchun manzil va aloqa telefonni kiriting.')
        return redirect('business_list', category_id=business.category.id)

    # Ensure reservation_area has a sensible default for restaurants so form submissions don't fail
    if booking_type == 'reservation' and is_food_service and not reservation_area:
        reservation_area = request.POST.get('reservation_area', '').strip() or 'Ichki zal'

    if booking_type == 'reservation' and is_food_service and not reservation_time:
        messages.error(request, 'Iltimos, restoran uchun kelish vaqtini kiriting.')
        return redirect('business_list', category_id=business.category.id)

    if booking_type == 'reservation' and is_hotel and not room_type:
        messages.error(request, 'Iltimos, mehmonxona uchun xona turini tanlang.')
        return redirect('business_list', category_id=business.category.id)

    if is_hotel and payment_method == 'cash':
        messages.error(request, 'Mehmonxona rezervlari faqat karta orqali amalga oshiriladi.')
        return redirect('business_list', category_id=business.category.id)

    if booking_type == 'delivery':
        if not check_in:
            check_in = date.today().isoformat()
        if not check_out:
            check_out = check_in

    check_in_date = parse_date(check_in) if check_in else None
    check_out_date = parse_date(check_out) if check_out else None

    try:
        guests = int(guests)
    except (TypeError, ValueError):
        guests = 1

    try:
        seats_val = int(seats) if seats else guests
    except (TypeError, ValueError):
        seats_val = guests

    if is_hotel:
        if not check_in_date or not check_out_date:
            messages.error(request, 'Mehmonxona uchun kelish va ketish sanasini to‘liq kiriting.')
            return redirect('business_list', category_id=business.category.id)
        nights = (check_out_date - check_in_date).days
        if nights <= 0:
            messages.error(request, 'Ketish sanasi kelish sanasidan keyin bo‘lishi kerak.')
            return redirect('business_list', category_id=business.category.id)
    else:
        nights = 1
        if booking_type == 'reservation' and is_food_service:
            check_out = check_in

    if booking_type == 'delivery':
        total_price = Decimal(business.price or 0) * max(1, guests)
    elif is_food_service:
        total_price = Decimal('0')
    elif is_hotel:
        total_price = business.calculate_hotel_price(room_type, nights, guests)
    else:
        total_price = Decimal(business.price or 0) * max(1, seats_val)

    booking = models.Booking.objects.create(
        user=request.user,
        business=business,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        passport_series=profile.passport_series,
        jshshr=profile.jshshr,
        seats=seats_val,
        reservation_area=reservation_area if booking_type == 'reservation' else '',
        reservation_time=reservation_time if is_food_service else None,
        room_type=room_type if is_hotel else '',
        total_price=total_price,
        payment_method=payment_method,
        booking_type=booking_type,
        delivery_address=delivery_address if booking_type == 'delivery' else '',
        contact_phone=contact_phone if booking_type == 'delivery' else '',
        status='pending' if payment_method in ['stripe', 'click', 'payme'] else 'confirmed'
    )

    if payment_method == 'cash':
        if is_food_service:
            messages.success(request, 'Bron qabul qilindi. Bizga kelishingizni kutamiz!')
            return redirect('business_list', category_id=business.category.id)

        messages.success(request, f'Zakaz qabul qilindi. Umumiy summa: {total_price} so‘m. Status: {booking.get_status_display()}.')
        if is_hotel:
            return redirect('business_list', category_id=business.category.id)
        return redirect('my_bookings')

    # If stripe token was provided from Stripe Elements, attempt immediate charge server-side
    stripe_token = request.POST.get('stripeToken') or request.POST.get('stripe_token')
    if stripe_token and booking.payment_method == 'stripe':
        try:
            stripe = __import__('stripe')
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            if stripe.api_key:
                charge = stripe.Charge.create(
                    amount=int(booking.total_price * 100),
                    currency='uzs',
                    source=stripe_token,
                    description=f'Zakaz #{booking.id} - {booking.business.name}',
                    metadata={'booking_id': str(booking.id)}
                )
                booking.external_id = charge.id
                if charge.status in ('succeeded', 'paid'):
                    booking.status = 'paid'
                    booking.paid_at = timezone.now()
                    booking.save(update_fields=['status', 'paid_at', 'external_id'])
                    messages.success(request, 'Toʻlov muvaffaqiyatli amalga oshirildi. Zakaz tasdiqlandi.')
                    if is_hotel or is_food_service:
                        return redirect('business_list', category_id=business.category.id)
                    return redirect('my_bookings')
                else:
                    booking.status = 'failed'
                    booking.save(update_fields=['status', 'external_id'])
                    messages.error(request, 'Toʻlov amalga oshmadi. Iltimos, boshqa karta bilan urinib koʻring.')
                    return redirect('business_list', category_id=business.category.id)
        except ImportError:
            messages.error(request, 'Toʻlov kutubxonasi mavjud emas. Server sozlamalarini tekshiring.')
            booking.status = 'failed'
            booking.save(update_fields=['status'])
            return redirect('business_list', category_id=business.category.id)
        except Exception as e:
            booking.status = 'failed'
            booking.save(update_fields=['status'])
            messages.error(request, f'Toʻlovda xatolik: {str(e)}')
            return redirect('business_list', category_id=business.category.id)

    payment_url = get_payment_redirect_url(booking, request)
    if not payment_url:
        messages.error(request, 'Toʻlov xizmatiga ulanib boʻlmadi. Soʻngra qayta urinib koʻring.')
        booking.status = 'failed'
        booking.save()
        return redirect('business_list', category_id=business.category.id)

    return redirect(payment_url)


def get_payment_redirect_url(booking, request):
    if booking.payment_method == 'stripe':
        try:
            stripe = __import__('stripe')
        except ImportError:
            return None

        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not stripe.api_key:
            return None

        success_url = request.build_absolute_uri(reverse('payment_success')) + f'?booking_id={booking.id}'
        cancel_url = request.build_absolute_uri(reverse('payment_cancel')) + f'?booking_id={booking.id}'
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'uzs',
                    'product_data': {'name': booking.business.name},
                    'unit_amount': int(booking.total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'booking_id': str(booking.id)},
        )
        booking.external_id = session.id
        booking.gateway_response = {'checkout_session': session.id}
        booking.save(update_fields=['external_id', 'gateway_response'])
        return session.url

    if booking.payment_method == 'click':
        service_id = getattr(settings, 'CLICK_SERVICE_ID', '')
        merchant_id = getattr(settings, 'CLICK_MERCHANT_ID', '')
        secret_key = getattr(settings, 'CLICK_SECRET_KEY', '')
        return_url = request.build_absolute_uri(reverse('payment_success')) + f'?booking_id={booking.id}'
        params = {
            'service_id': service_id,
            'amount': int(booking.total_price),
            'merchant_id': merchant_id,
            'order_id': str(booking.id),
            'description': f'Zakaz #{booking.id} - {booking.business.name}',
            'return_url': return_url,
        }
        sign = hashlib.md5(f"{service_id}{params['amount']}{merchant_id}{params['order_id']}{secret_key}".encode('utf-8')).hexdigest()
        params['sign'] = sign
        booking.external_id = params['order_id']
        booking.gateway_response = {'type': 'click', 'params': params}
        booking.save(update_fields=['external_id', 'gateway_response'])
        return 'https://my.click.uz/services/pay?' + urlencode(params)

    if booking.payment_method == 'payme':
        merchant_id = getattr(settings, 'PAYME_MERCHANT_ID', '')
        secret_key = getattr(settings, 'PAYME_SECRET_KEY', '')
        return_url = request.build_absolute_uri(reverse('payment_success')) + f'?booking_id={booking.id}'
        params = {
            'merchant_id': merchant_id,
            'amount': int(booking.total_price * 100),
            'order_id': str(booking.id),
            'description': f'Zakaz #{booking.id} - {booking.business.name}',
            'return_url': return_url,
        }
        sign = hashlib.sha256(f"{merchant_id}{params['amount']}{params['order_id']}{secret_key}".encode('utf-8')).hexdigest()
        params['sign'] = sign
        booking.external_id = params['order_id']
        booking.gateway_response = {'type': 'payme', 'params': params}
        booking.save(update_fields=['external_id', 'gateway_response'])
        return 'https://checkout.paycom.uz/?' + urlencode(params)

    return None


def payment_success(request):
    booking_id = request.GET.get('booking_id')
    booking = get_object_or_404(models.Booking, id=booking_id)
    if booking.status != 'paid':
        booking.status = 'paid'
        booking.paid_at = timezone.now()
        booking.save(update_fields=['status', 'paid_at'])
    messages.success(request, 'Toʻlov muvaffaqiyatli amalga oshirildi. Zakaz holati yangilandi.')
    category_name = booking.business.category.name.lower() if booking.business.category else ''
    if 'mehmonxona' in category_name or any(term in category_name for term in ['restoran', 'kafe', 'fast food', 'cafe', 'restaurant']):
        return redirect('business_list', category_id=booking.business.category.id)
    return redirect('my_bookings')


def payment_cancel(request):
    booking_id = request.GET.get('booking_id')
    booking = get_object_or_404(models.Booking, id=booking_id)
    booking.status = 'failed'
    booking.save(update_fields=['status'])
    messages.error(request, 'Toʻlov bekor qilindi yoki xato yuz berdi.')
    return redirect('business_list', category_id=booking.business.category.id)


@csrf_exempt
def click_callback(request):
    order_id = request.GET.get('order_id') or request.POST.get('order_id')
    status = request.GET.get('status') or request.POST.get('status')
    if not order_id:
        return HttpResponse('missing order_id', status=400)
    booking = get_object_or_404(models.Booking, id=order_id)
    if status == 'success':
        booking.status = 'paid'
        booking.save(update_fields=['status'])
        return HttpResponse('OK')
    booking.status = 'failed'
    booking.save(update_fields=['status'])
    return HttpResponse('FAILED')


@csrf_exempt
def payme_callback(request):
    data = request.body.decode('utf-8')
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return HttpResponse('invalid json', status=400)
    order_id = payload.get('order_id')
    status = payload.get('status')
    if not order_id:
        return HttpResponse('missing order_id', status=400)
    booking = get_object_or_404(models.Booking, id=order_id)
    if status == 'paid':
        booking.status = 'paid'
        booking.save(update_fields=['status'])
        return HttpResponse('OK')
    booking.status = 'failed'
    booking.save(update_fields=['status'])
    return HttpResponse('FAILED')


@login_required(login_url='log_in')
def my_bookings(request):
    bookings = models.Booking.objects.filter(user=request.user).select_related('business').order_by('-created_at')
    active_bookings = bookings.exclude(status='failed')
    return render(request, 'bussines/bookings.html', {
        'bookings': bookings,
        'active_bookings': active_bookings,
    })


@login_required(login_url='log_in')
def booking_pdf(request, booking_id):
    if not REPORTLAB_AVAILABLE:
        messages.error(request, 'PDF yaratish uchun reportlab paketi o\'rnatilmagan. Iltimos, pip install reportlab bajarib qayta urinib ko\'ring.')
        return redirect('my_bookings')

    booking = get_object_or_404(models.Booking, id=booking_id, user=request.user)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin

    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(margin, y, 'Zakaz ma\'lumotlari')
    y -= 30
    pdf.setFont('Helvetica', 11)
    pdf.drawString(margin, y, f'Biznes: {booking.business.name}')
    y -= 20
    pdf.drawString(margin, y, f'Ism: {request.user.first_name} {request.user.last_name}')
    y -= 20
    pdf.drawString(margin, y, f'Pasport seriyasi: {booking.passport_series or "-"}')
    y -= 20
    pdf.drawString(margin, y, f'JSHSHR: {booking.jshshr or "-"}')
    y -= 20
    # Do not include internal status in the user-facing PDF
    # (avoids showing 'Rad etilgan' or other internal flags)
    pdf.drawString(margin, y, f'To\'lov usuli: {booking.get_payment_method_display()}')
    y -= 20
    pdf.drawString(margin, y, f'Jami summa: {int(booking.total_price):,} so\'m')
    y -= 20
    pdf.drawString(margin, y, f'Kelish sanasi: {booking.check_in}')
    y -= 20
    pdf.drawString(margin, y, f'Ketish sanasi: {booking.check_out}')
    y -= 20
    pdf.drawString(margin, y, f'Mehmonlar: {booking.guests}')
    y -= 20
    if booking.business.category.name.lower().find('mehmonxona') >= 0:
        pdf.drawString(margin, y, f'Xona turi: {booking.room_type}')
        y -= 20
    # Only show reservation area if it's provided and not the default filler
    if booking.reservation_area and booking.reservation_area.strip().lower() != 'ichki zal':
        pdf.drawString(margin, y, f'Rezerv joyi: {booking.reservation_area}')
        y -= 20
    if booking.reservation_time:
        pdf.drawString(margin, y, f'Rezerv vaqt: {booking.reservation_time}')
        y -= 20

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    # Do not expose booking ID in filename
    response['Content-Disposition'] = 'attachment; filename="zakaz.pdf"'
    return response


def contact_us(request):
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            models.ContactUs.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            messages.success(request, "Xabaringiz muvaffaqiyatli yuborildi.")
            return redirect('home')
        else:
            messages.error(request, "Iltimos, barcha majburiy maydonlarni to‘ldiring.")

    return render(request, 'contact_us.html')


# ---------------------mybusiness---------------------

def my_business(request):
    businesses = models.Business.objects.filter(user=request.user).select_related('region', 'district', 'category')
    return render(request, 'mybusiness/mybusiness.html', {'businesses': businesses})


def delete_business(request, business_id):
    business = models.Business.objects.get(id=business_id)
    business.delete()
    return redirect('my_business')


from django.shortcuts import get_object_or_404


def update_business(request, business_id):
    business = models.Business.objects.get(id=business_id)

    if request.method == 'POST':
        business.name = request.POST.get('name')

        # Bu yerda model instance'ni olishimiz kerak
        category_id = request.POST.get('category')
        region_id = request.POST.get('region')
        district_id = request.POST.get('district')

        business.category = get_object_or_404(models.BusinessCategory, id=category_id)
        business.region = get_object_or_404(models.Region, id=region_id)
        business.district = get_object_or_404(models.District, id=district_id)

        business.address = request.POST.get('address')
        business.location = request.POST.get('location', '').strip()
        business.owner_first_name = request.POST.get('owner_first_name', '').strip() or None
        business.owner_last_name = request.POST.get('owner_last_name', '').strip() or None
        business.owner_passport = request.POST.get('owner_passport', '').strip() or None
        commission_input = request.POST.get('commission_percentage', '0')
        try:
            business.commission_percentage = Decimal(commission_input)
        except (TypeError, ValueError, InvalidOperation):
            business.commission_percentage = Decimal('0')
        business.phone = request.POST.get('phone')
        business.website = request.POST.get('website', '').strip() or None
        business.instagram = request.POST.get('instagram', '').strip() or None
        price_input = request.POST.get('price', '0')
        try:
            business.price = float(price_input)
        except (TypeError, ValueError):
            business.price = 0
        business.save()

        return redirect('my_business')

    context = {
        'business': business,
        'categories': models.BusinessCategory.objects.all(),
        'regions': models.Region.objects.all(),
        'districts': models.District.objects.all(),
    }
    return render(request, 'mybusiness/update.html', context=context)
