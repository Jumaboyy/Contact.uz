# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class UserRegion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)  # <-- muhim

    def __str__(self):
        return f"{self.user} - {self.region} - {self.district}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    passport_series = models.CharField(max_length=50, blank=True, null=True)
    jshshr = models.CharField(max_length=25, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class BusinessCategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category/', null=True, blank=True)

    def __str__(self):
        return self.name


class Business(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(BusinessCategory, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    address = models.TextField()
    location = models.CharField(max_length=255, blank=True, null=True)
    owner_first_name = models.CharField(max_length=100, blank=True, null=True)
    owner_last_name = models.CharField(max_length=100, blank=True, null=True)
    owner_passport = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    website = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    image = models.ImageField(upload_to='business/', null=True, blank=True)

    @property
    def category_name_lower(self):
        return self.category.name.lower() if self.category else ''

    @property
    def is_pharmacy(self):
        category_name = self.category_name_lower
        return 'dorixona' in category_name or 'pharmacy' in category_name

    @property
    def is_medical_center(self):
        category_name = self.category_name_lower
        return any(term in category_name for term in ['tibbiyot', 'medical', 'clinic', 'hospital', 'markaz', 'center'])

    @property
    def is_museum(self):
        category_name = self.category_name_lower
        return any(term in category_name for term in ['muzey', 'museum'])

    @property
    def is_shopping_center(self):
        category_name = self.category_name_lower
        return any(term in category_name for term in ['savdo markazi', 'shopping center', 'shopping mall', 'mall', 'bozor', 'market'])

    @property
    def is_location_service(self):
        category_name = self.category_name_lower
        return (
            self.is_pharmacy or
            self.is_medical_center or
            self.is_museum or
            self.is_shopping_center or
            any(term in category_name for term in ['bank', 'notarius', 'notary', 'sanatoriya', 'dam olish', 'resort'])
        )

    @property
    def is_food_service(self):
        category_name = self.category_name_lower
        return any(term in category_name for term in ['restoran', 'kafe', 'fast food', 'cafe', 'restaurant'])

    @property
    def is_hotel(self):
        category_name = self.category_name_lower
        return 'mehmonxona' in category_name or 'hotel' in category_name

    def get_hotel_room_multiplier(self, room_type: str) -> Decimal:
        multiplier_map = {
            'Single (SGL)': Decimal('1.0'),
            'Double (DBL)': Decimal('1.4'),
            'Twin (TWN)': Decimal('1.4'),
            'Triple (TRPL)': Decimal('1.8'),
            'Quadruple (QDPL)': Decimal('2.2'),
            'Family Room': Decimal('2.4'),
            'Standard': Decimal('1.2'),
            'Superior': Decimal('1.5'),
            'Deluxe': Decimal('1.8'),
            'Suite / Luxe': Decimal('2.8'),
            'Junior Suite': Decimal('2.2'),
            'Apartment / Studio': Decimal('2.6'),
        }
        return multiplier_map.get(room_type, Decimal('1.0'))

    def calculate_hotel_price(self, room_type: str, nights: int, guests: int) -> Decimal:
        base_price = Decimal(self.price or 0)
        multiplier = self.get_hotel_room_multiplier(room_type)
        nights = max(1, nights)
        guests = max(1, guests)
        return (base_price * multiplier * nights * guests).quantize(Decimal('1'))

    def calculate_commission_amount(self, total_price: Decimal) -> Decimal:
        commission = Decimal(self.commission_percentage or 0) / Decimal('100')
        return (total_price * commission).quantize(Decimal('1'))

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutish'),
        ('confirmed', 'Tasdiqlangan'),
        ('paid', 'Toʻlangan'),
        ('failed', 'Rad etilgan'),
    ]
    PAYMENT_METHODS = [
        ('cash', 'Naqd pul'),
        ('stripe', 'Stripe'),
        ('click', 'Click'),
        ('payme', 'Payme'),
    ]
    BOOKING_TYPES = [
        ('reservation', 'Joyda rezerv'),
        ('delivery', 'Dostafka'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(default=1)
    passport_series = models.CharField(max_length=50, blank=True, null=True)
    jshshr = models.CharField(max_length=25, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPES, default='reservation')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    external_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    # For restaurants: seats means number of persons for reservation
    seats = models.PositiveIntegerField(default=1)
    # For restaurants: reservation area / zone selection
    reservation_area = models.CharField(max_length=100, blank=True, null=True)
    reservation_time = models.TimeField(blank=True, null=True)
    room_type = models.CharField(max_length=100, blank=True, null=True)
    # For delivery bookings: delivery address and contact phone
    delivery_address = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f'{self.business.name} - {self.user.username} ({self.check_in} - {self.check_out})'


class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()

    def __str__(self):
        return self.name


ROOM_TYPE_CHOICES = [
    ('Single (SGL)', '1kishilik xona (SGL)'),
    ('Double (DBL)', '2kishilik xona (DBL)'),
    ('Twin (TWN)', '2kishilik tosak (TWN)'),
    ('Triple (TRPL)', '3kishilik (TRPL)'),
    ('Quadruple (QDPL)', '4kishilik (QDPL)'),
    ('Family Room', 'Oila xonasi'),
    ('Standard', 'Standart'),
    ('Superior', 'Superior'),
    ('Deluxe', 'Deluxe'),
    ('Suite / Luxe', 'Suit/Lyuks'),
    ('Junior Suite', 'Kichik Suit'),
    ('Apartment / Studio', 'Apartament/Studio'),
]


class HotelRoomImage(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='room_images')
    room_type = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES)
    image = models.ImageField(upload_to='business/rooms/')

    class Meta:
        verbose_name = 'Hotel Room Image'
        verbose_name_plural = 'Hotel Room Images'

    def __str__(self):
        return f"{self.business.name} - {self.room_type}"
