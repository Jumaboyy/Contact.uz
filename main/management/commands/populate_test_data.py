import os
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files import File
from main.models import Region, District, BusinessCategory, Business, ContactUs, UserRegion, HotelRoomImage


class Command(BaseCommand):
    help = "Loyihani test ma'lumotlari bilan to'ldiradi"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Test ma'lumotlarini yuklash boshlandi..."))
        
        # 1. Test foydalanuvchilarni yaratish
        self.create_test_users()
        
        # 2. Business kategoriyalarini yaratish
        self.create_business_categories()
        
        # 3. Businesslarni yaratish
        self.create_businesses()
        
        # 4. ContactUs ma'lumotlarini yaratish
        self.create_contact_us()
        # 5. Hotel room images for hotels
        self.create_hotel_room_images()
        
        self.stdout.write(self.style.SUCCESS("✅ Test ma'lumotlari muvaffaqiyatli yuklandi!"))

    def create_test_users(self):
        self.stdout.write("\n👤 Test foydalanuvchilarni yaratish...")
        
        users_data = [
            {"username": "admin", "email": "admin@contact.uz", "password": "admin123", "is_superuser": True},
            {"username": "user1", "email": "user1@contact.uz", "password": "user123"},
            {"username": "user2", "email": "user2@contact.uz", "password": "user123"},
            {"username": "business_owner1", "email": "business1@contact.uz", "password": "biz123"},
            {"username": "business_owner2", "email": "business2@contact.uz", "password": "biz123"},
            {"username": "john_doe", "email": "john@example.com", "password": "john123"},
            {"username": "jane_smith", "email": "jane@example.com", "password": "jane123"},
            {"username": "akhmad_karimov", "email": "akhmad@contact.uz", "password": "akhmad123"},
        ]
        
        for user_data in users_data:
            is_superuser = user_data.pop("is_superuser", False)
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "is_superuser": is_superuser,
                    "is_staff": is_superuser
                }
            )
            if created:
                user.set_password(user_data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  ✅ Foydalanuvchi qo'shildi: {user.username}"))
            else:
                user.set_password(user_data["password"])
                user.save()
                self.stdout.write(f"  ℹ️  Foydalanuvchi mavjud: {user.username}")

    def create_business_categories(self):
        self.stdout.write("\n📁 Business kategoriyalarini yaratish...")
        
        categories_data = [
            {"name": "Restoranlar", "image": "restaran_category2.jpg"},
            {"name": "Mehmonxonalar", "image": "mehmonxona_category1.jpg"},
            {"name": "Savdo markazlari", "image": "Savdo_markazlari.jpg"},
            {"name": "Kafelar", "image": "kafe_cate.jpg"},
            {"name": "Tibbiyot markazlari", "image": "Medical_Center.jpg"},
            {"name": "Dorixonalar", "image": "Dorixonalar.webp"},
            {"name": "Muzeylar", "image": "muzey.webp"},
            {"name": "Fast Food", "image": "hamburger-emoji-clipart-lg.png"},
            {"name": "Sport maydonlari", "image": "football-field-clipart-lg.png"},
            {"name": "O'yin zonalari", "image": "playstation-icon-lg.png"},
            {"name": "Muzqaymoq", "image": "ice-cream-scoop-clipart-lg.png"},
            {"name": "Ichimliklar", "image": "cola1.jpg"},
        ]
        
        media_category_path = "media/category/"
        
        for cat_data in categories_data:
            category, created = BusinessCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={}
            )
            
            if created or not category.image:
                image_path = os.path.join(media_category_path, cat_data["image"])
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        category.image.save(cat_data["image"], File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Kategoriya qo'shildi: {category.name}"))
                else:
                    category.save()
                    self.stdout.write(f"  ⚠️  Kategoriya qo'shildi (rasm yo'q): {category.name}")
            else:
                self.stdout.write(f"  ℹ️  Kategoriya mavjud: {category.name}")

    def create_businesses(self):
        self.stdout.write("\n🏢 Businesslarni yaratish...")
        
        # Region va Districtlarni olish
        regions = list(Region.objects.all())
        districts = list(District.objects.all())
        categories = list(BusinessCategory.objects.all())
        users = list(User.objects.filter(username__startswith=["business", "admin", "user"]))
        
        if not regions:
            self.stdout.write(self.style.ERROR("  ❌ Regionlar topilmadi! Avval regionlarni yuklang."))
            return
        
        if not categories:
            self.stdout.write(self.style.ERROR("  ❌ Kategoriyalar topilmadi!"))
            return
        
        media_business_path = "media/business/"
        
        businesses_data = [
            {"name": "EVOS Fast Food", "category": "Fast Food", "region": "Toshkent", "district": "Toshkent shahri", "address": "Amir Temur ko'chasi, 15", "phone": "+998901234567", "image": "EVOS-01.png"},
            {"name": "Asia Hotel", "category": "Mehmonxonalar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Mustaqillik maydoni, 1", "phone": "+998902345678", "image": "asiahotel.webp"},
            {"name": "Kapadokya Restaurant", "category": "Restoranlar", "region": "Samarqand", "district": "Samarqand shahri", "address": "Registon maydoni, 5", "phone": "+998903456789", "image": "Kapadokya.webp"},
            {"name": "Fergana Hotel", "category": "Mehmonxonalar", "region": "Farg'ona", "district": "Farg'ona shahri", "address": "Markaziy ko'cha, 25", "phone": "+998904567890", "image": "ferganahotel.jpg"},
            {"name": "Grand Hotel", "category": "Mehmonxonalar", "region": "Buxoro", "district": "Buxoro shahri", "address": "Kalon minorasi yonida", "phone": "+998905678901", "image": "garandhotel.webp"},
            {"name": "Choynak Tea House", "category": "Kafelar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Chorsu bozori, 10", "phone": "+998906789012", "image": "choynak3.jpg"},
            {"name": "Club Hotel 777", "category": "Mehmonxonalar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Yunusobod tumani", "phone": "+998907890123", "image": "Club_Hotel_777.webp"},
            {"name": "Machu Picchu Restaurant", "category": "Restoranlar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Milliy bog', 3", "phone": "+998908901234", "image": "machu_picchu.jpg"},
            {"name": "Samarqand Medical Center", "category": "Tibbiyot markazlari", "region": "Samarqand", "district": "Samarqand shahri", "address": "Shohizinda, 8", "phone": "+998909012345", "image": "img2.webp"},
            {"name": "Andijon Savdo Markazi", "category": "Savdo markazlari", "region": "Andijon", "district": "Andijon shahri", "address": "Bog'ishamol ko'chasi", "phone": "+998910123456", "image": "download.jfif"},
            {"name": "Buxoro Dorixonasi", "category": "Dorixonalar", "region": "Buxoro", "district": "Buxoro shahri", "address": "Eski shahar", "phone": "+998911234567", "image": "download.jfif"},
            {"name": "Namangan Stadium", "category": "Sport maydonlari", "region": "Namangan", "district": "Namangan shahri", "address": "Sport kompleksi", "phone": "+998912345678", "image": "download.jfif"},
            {"name": "Qashqadaryo Museum", "category": "Muzeylar", "region": "Qashqadaryo", "district": "Qarshi shahri", "address": "Markaziy maydon", "phone": "+998913456789", "image": "download.jfif"},
            {"name": "Surxandaryo Ice Cream", "category": "Muzqaymoq", "region": "Surxandaryo", "district": "Termiz shahri", "address": "Markaziy ko'cha", "phone": "+998914567890", "image": "download.jfif"},
            {"name": "Xorazm PlayStation", "category": "O'yin zonalari", "region": "Xorazm", "district": "Xiva shahri", "address": "Ichan Qal'a", "phone": "+998915678901", "image": "download.jfif"},
            {"name": "Toshkent City Mall", "category": "Savdo markazlari", "region": "Toshkent", "district": "Toshkent shahri", "address": "Amir Temur ko'chasi, 107", "phone": "+998916789012", "image": "download.jfif"},
            {"name": "Navoiy Medical Center", "category": "Tibbiyot markazlari", "region": "Navoiy", "district": "Navoiy shahri", "address": "Mustaqillik ko'chasi", "phone": "+998917890123", "image": "download.jfif"},
            {"name": "Jizzax Dorixonasi", "category": "Dorixonalar", "region": "Jizzax", "district": "Jizzax shahri", "address": "Markaziy shifoxona", "phone": "+998918901234", "image": "download.jfif"},
            {"name": "Sirdaryo Stadium", "category": "Sport maydonlari", "region": "Sirdaryo", "district": "Guliston shahri", "address": "Sport maydoni", "phone": "+998919012345", "image": "download.jfif"},
            {"name": "Qoraqalpog'iston Museum", "category": "Muzeylar", "region": "Qoraqalpog'iston", "district": "Nukus shahri", "address": "Savitskiy muzeyi", "phone": "+998920123456", "image": "download.jfif"},
            {"name": "Burger King", "category": "Fast Food", "region": "Toshkent", "district": "Toshkent shahri", "address": "Buyuk Ipak Yuli ko'chasi", "phone": "+998921234567", "image": "EVOS-01.png"},
            {"name": "KFC Uzbekistan", "category": "Fast Food", "region": "Toshkent", "district": "Toshkent shahri", "address": "Sergeli tumani", "phone": "+998922345678", "image": "EVOS-01.png"},
            {"name": "McDonald's", "category": "Fast Food", "region": "Toshkent", "district": "Toshkent shahri", "address": "Chilonzor tumani", "phone": "+998923456789", "image": "EVOS-01.png"},
            {"name": "Intercontinental Hotel", "category": "Mehmonxonalar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Amir Temur shoh ko'chasi", "phone": "+998924567890", "image": "asiahotel.webp"},
            {"name": "Hyatt Regency", "category": "Mehmonxonalar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Bunyodkor shoh ko'chasi", "phone": "+998925678901", "image": "asiahotel.webp"},
            {"name": "Radisson Blu", "category": "Mehmonxonalar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Toshkent shahri, Navoiy ko'chasi", "phone": "+998926789012", "image": "asiahotel.webp"},
            {"name": "Afsona Restaurant", "category": "Restoranlar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Milliy bog' ichida", "phone": "+998927890123", "image": "Kapadokya.webp"},
            {"name": "Old City Restaurant", "category": "Restoranlar", "region": "Buxoro", "district": "Buxoro shahri", "address": "Eski shahar", "phone": "+998928901234", "image": "Kapadokya.webp"},
            {"name": "Plato Restaurant", "category": "Restoranlar", "region": "Samarqand", "district": "Samarqand shahri", "address": "Registon maydoni", "phone": "+998929012345", "image": "Kapadokya.webp"},
            {"name": "Starbucks Cafe", "category": "Kafelar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Amir Temur ko'chasi", "phone": "+998930123456", "image": "choynak3.jpg"},
            {"name": "Costa Coffee", "category": "Kafelar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Samarqand Darvoza", "phone": "+998931234567", "image": "choynak3.jpg"},
            {"name": "Coffee House", "category": "Kafelar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Yunusobod tumani", "phone": "+998932345678", "image": "choynak3.jpg"},
            {"name": "Tashkent Medical City", "category": "Tibbiyot markazlari", "region": "Toshkent", "district": "Toshkent shahri", "address": "Qatortol ko'chasi", "phone": "+998933456789", "image": "img2.webp"},
            {"name": "Andijon Medical Center", "category": "Tibbiyot markazlari", "region": "Andijon", "district": "Andijon shahri", "address": "Bog'bon ko'chasi", "phone": "+998934567890", "image": "img2.webp"},
            {"name": "Fergana Valley Pharmacy", "category": "Dorixonalar", "region": "Farg'ona", "district": "Farg'ona shahri", "address": "Markaziy dorixona", "phone": "+998935678901", "image": "download.jfif"},
            {"name": "Karakalpak Pharmacy", "category": "Dorixonalar", "region": "Qoraqalpog'iston", "district": "Nukus shahri", "address": "Mustaqillik ko'chasi", "phone": "+998936789012", "image": "download.jfif"},
            {"name": "Samarkand Bazaar", "category": "Savdo markazlari", "region": "Samarqand", "district": "Samarqand shahri", "address": "Siyob bozori", "phone": "+998937890123", "image": "download.jfif"},
            {"name": "Kashkadarya Shopping Center", "category": "Savdo markazlari", "region": "Qashqadaryo", "district": "Qarshi shahri", "address": "Markaziy savdo markazi", "phone": "+998938901234", "image": "download.jfif"},
            {"name": "Surkhandarya Bazaar", "category": "Savdo markazlari", "region": "Surxandaryo", "district": "Termiz shahri", "address": "Markaziy bozor", "phone": "+998939012345", "image": "download.jfif"},
            {"name": "Pakhtakor Stadium", "category": "Sport maydonlari", "region": "Toshkent", "district": "Toshkent shahri", "address": "Paxtakor ko'chasi", "phone": "+998940123456", "image": "download.jfif"},
            {"name": "Bunyodkor Stadium", "category": "Sport maydonlari", "region": "Toshkent", "district": "Toshkent shahri", "address": "Bunyodkor ko'chasi", "phone": "+998941234567", "image": "download.jfif"},
            {"name": "Ice Cream Palace", "category": "Muzqaymoq", "region": "Toshkent", "district": "Toshkent shahri", "address": "Amir Temur ko'chasi", "phone": "+998942345678", "image": "download.jfif"},
            {"name": "Gelato Shop", "category": "Muzqaymoq", "region": "Toshkent", "district": "Toshkent shahri", "address": "Chilonzor tumani", "phone": "+998943456789", "image": "download.jfif"},
            {"name": "PlayZone Arcade", "category": "O'yin zonalari", "region": "Toshkent", "district": "Toshkent shahri", "address": "Toshkent City", "phone": "+998944567890", "image": "download.jfif"},
            {"name": "Cyber Cafe Gaming", "category": "O'yin zonalari", "region": "Toshkent", "district": "Toshkent shahri", "address": "Sergeli tumani", "phone": "+998945678901", "image": "download.jfif"},
            {"name": "Coca Cola Bottling", "category": "Ichimliklar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Sergeli tumani", "phone": "+998946789012", "image": "download.jfif"},
            {"name": "Pepsi Factory", "category": "Ichimliklar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Zangiota tumani", "phone": "+998947890123", "image": "download.jfif"},
            {"name": "Juice Bar", "category": "Ichimliklar", "region": "Toshkent", "district": "Toshkent shahri", "address": "Milliy bog'", "phone": "+998948901234", "image": "download.jfif"},
        ]
        
        for biz_data in businesses_data:
            # Region topish
            region = next((r for r in regions if r.name == biz_data["region"]), regions[0])
            
            # District topish
            district = next((d for d in districts if d.name == biz_data["district"] and d.region == region), None)
            if not district:
                district = districts[0] if districts else None
            
            # Category topish
            category = next((c for c in categories if c.name == biz_data["category"]), categories[0])
            
            # User tanlash
            user = random.choice(users) if users else None
            
            business, created = Business.objects.get_or_create(
                name=biz_data["name"],
                defaults={
                    "user": user,
                    "category": category,
                    "region": region,
                    "district": district,
                    "address": biz_data["address"],
                    "phone": biz_data["phone"],
                }
            )
            
            if created or not business.image:
                image_path = os.path.join(media_business_path, biz_data["image"])
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        business.image.save(biz_data["image"], File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Business qo'shildi: {business.name}"))
                else:
                    business.save()
                    self.stdout.write(f"  ⚠️  Business qo'shildi (rasm yo'q): {business.name}")
            else:
                self.stdout.write(f"  ℹ️  Business mavjud: {business.name}")

    def create_contact_us(self):
        self.stdout.write("\n📧 ContactUs ma'lumotlarini yaratish...")
        
        contacts_data = [
            {"name": "Alisher Karimov", "email": "alisher@gmail.com", "phone": "+998901112233", "message": "Assalomu alaykum! Saytingiz juda zo'r. Ko'proq ma'lumot olishim mumkinmi?"},
            {"name": "Nigora Rahimova", "email": "nigora@yahoo.com", "phone": "+998902223344", "message": "Mening biznesimni ro'yxatdan o'tkazmoqchiman. Qanday qilib qilish mumkin?"},
            {"name": "Bekzod Toshmatov", "email": "bekzod@mail.ru", "phone": "+998903334455", "message": "Toshkent shahridagi eng yaxshi restoranlarni qidiryapman. Tavsiya bering."},
            {"name": "Dilnoza Azizova", "email": "dilnoza@inbox.uz", "phone": "+998904445566", "message": "Mehmonxona bron qilish xizmati bormi? Narxlarni bilishim kerak."},
            {"name": "Jamshid Ismoilov", "email": "jamshid@gmail.com", "phone": "+998905556677", "message": "Samarqandga sayohat rejalashtiryapman. Qanday maslahatlar bolasiz?"},
            {"name": "Zuhra Qodirova", "email": "zuhra@yahoo.com", "phone": "+998906667788", "message": "Dorixona ma'lumotlari to'liq emas. Qo'shimcha ma'lumot kerak."},
            {"name": "Sardor Nazarov", "email": "sardor@mail.ru", "phone": "+998907778899", "message": "Sport maydonlari bo'yicha ma'lumot olishmoqchiman."},
            {"name": "Malika Husanova", "email": "malika@inbox.uz", "phone": "+998908889900", "message": "Kafe va restoranlarning ish vaqtlarini bilishim mumkinmi?"},
            {"name": "Rustam Alimov", "email": "rustam@gmail.com", "phone": "+998909990011", "message": "Biznesimni reklama qilishni xohlayman. Narxlarni bilishim kerak."},
            {"name": "Sevara Nazarova", "email": "sevara@yahoo.com", "phone": "+998910001122", "message": "Saytdan foydalanish juda qulay. Raxmat!"},
        ]
        
        for contact_data in contacts_data:
            contact, created = ContactUs.objects.get_or_create(
                email=contact_data["email"],
                defaults={
                    "name": contact_data["name"],
                    "phone": contact_data["phone"],
                    "message": contact_data["message"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✅ ContactUs qo'shildi: {contact.name}"))
            else:
                self.stdout.write(f"  ℹ️  ContactUs mavjud: {contact.name}")

    def create_hotel_room_images(self):
        self.stdout.write("\n🖼️ Mehmonxonalar uchun xona rasmlarini yaratish...")
        # Only create for businesses flagged as hotels
        room_types = [
            ('Single (SGL)', 'download.jfif'),
            ('Double (DBL)', 'download_2CD2xp8.jfif'),
            ('Deluxe', 'download_ckZoChk.jfif'),
        ]
        media_business_path = 'media/business/'

        hotels = Business.objects.filter(category__name__icontains='Mehmonxonalar')
        for hotel in hotels:
            for room_type, filename in room_types:
                existing = HotelRoomImage.objects.filter(business=hotel, room_type=room_type).first()
                if existing:
                    self.stdout.write(f"  ℹ️ {hotel.name} uchun {room_type} rasm mavjud")
                    continue
                image_path = os.path.join(media_business_path, filename)
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        img = HotelRoomImage(business=hotel, room_type=room_type)
                        img.image.save(filename, File(f), save=True)
                        self.stdout.write(self.style.SUCCESS(f"  ✅ {hotel.name} - {room_type} rasm qo'shildi"))
                else:
                    self.stdout.write(f"  ⚠️ Rasm topilmadi: {image_path} uchun {hotel.name}")
