from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main import models
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate the database with sample regions, districts, categories, users and businesses.'

    def handle(self, *args, **options):
        self.stdout.write('Starting DB population...')

        # Regions and districts
        regions_data = {
            'Toshkent': ['Mirzo Ulugbek', 'Yunusobod', 'Chilonzor'],
            'Samarqand': ['Bulungur', 'Paxtachi', 'Urgut'],
            'Buxoro': ['Vobkent', 'Gijduvon'],
        }

        regions = {}
        for rname, dlist in regions_data.items():
            r, _ = models.Region.objects.get_or_create(name=rname)
            regions[rname] = r
            for dname in dlist:
                models.District.objects.get_or_create(name=dname, region=r)

        self.stdout.write(f'Created regions: {", ".join(regions.keys())}')

        # Categories
        category_names = ['Mehmonxona', 'Restoran', 'Dorixona', 'Salon', 'Cafe']
        categories = {}
        for cname in category_names:
            c, _ = models.BusinessCategory.objects.get_or_create(name=cname)
            categories[cname] = c

        self.stdout.write(f'Created categories: {", ".join(categories.keys())}')

        # Test user
        test_username = 'testuser'
        test_email = 'testuser@example.com'
        test_password = 'testpass123'
        user, created = User.objects.get_or_create(username=test_username, defaults={'email': test_email})
        if created:
            user.set_password(test_password)
            user.save()
            self.stdout.write(f'Created user {test_username} with password {test_password}')
        else:
            self.stdout.write(f'User {test_username} already exists')

        # Create sample businesses
        sample_businesses = [
            {'name': 'Grand Hotel Tashkent', 'category': 'Mehmonxona', 'region': 'Toshkent', 'district': 'Mirzo Ulugbek', 'address': 'Amir Temur 12', 'phone': '712345678', 'price': 200000},
            {'name': 'Samarqand Palace', 'category': 'Mehmonxona', 'region': 'Samarqand', 'district': 'Urgut', 'address': 'Registon 1', 'phone': '662223334', 'price': 180000},
            {'name': 'Central Restaurant', 'category': 'Restoran', 'region': 'Toshkent', 'district': 'Yunusobod', 'address': 'Bodomzor 5', 'phone': '712112233', 'price': 50000},
            {'name': 'City Pharmacy', 'category': 'Dorixona', 'region': 'Buxoro', 'district': 'Vobkent', 'address': 'Bozor 3', 'phone': '952223344', 'price': 0},
            {'name': 'Coffee Corner', 'category': 'Cafe', 'region': 'Toshkent', 'district': 'Chilonzor', 'address': 'Mustaqillik 10', 'phone': '712009988', 'price': 20000},
        ]

        created_count = 0
        for sb in sample_businesses:
            region = regions.get(sb['region'])
            district = models.District.objects.filter(name=sb['district'], region=region).first()
            category = categories.get(sb['category'])
            if not (region and district and category):
                continue
            biz, _ = models.Business.objects.get_or_create(
                name=sb['name'],
                defaults={
                    'user': user,
                    'category': category,
                    'region': region,
                    'district': district,
                    'address': sb['address'],
                    'phone': sb['phone'],
                    'price': sb['price'],
                }
            )
            created_count += 1

        self.stdout.write(f'Created or updated {created_count} businesses')

        # Optional: create a UserRegion for test user
        try:
            ur, _ = models.UserRegion.objects.get_or_create(user=user, defaults={'region': regions.get('Toshkent')})
            self.stdout.write('UserRegion set for testuser')
        except Exception:
            pass

        self.stdout.write('DB population finished.')