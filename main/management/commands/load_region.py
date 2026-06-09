import json
import os
from django.core.management.base import BaseCommand
from main.models import Region, District  # Model nomlari to‘g‘ri bo‘lishi kerak


class Command(BaseCommand):
    help = "Yuqoridagi regions.json fayldan Region va District ma'lumotlarini bazaga yuklaydi"

    def handle(self, *args, **kwargs):
        json_path = os.path.join('main', 'region.json')

        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"{json_path} topilmadi."))
            return

        # 1. Regionlarni yuklash
        for region_data in data.get('regions', []):
            region, created = Region.objects.get_or_create(
                id=region_data['id'],
                defaults={'name': region_data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Region qo‘shildi: {region.name}"))
            else:
                self.stdout.write(f"Region mavjud: {region.name}")

        # 2. Districtlarni yuklash
        for district_data in data.get('districts', []):
            try:
                region = Region.objects.get(id=district_data['region_id'])
                district, created = District.objects.get_or_create(
                    id=district_data['id'],
                    defaults={'name': district_data['name'], 'region': region}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"  Tuman qo‘shildi: {district.name} ({region.name})"))
                else:
                    self.stdout.write(f"  Tuman mavjud: {district.name}")
            except Region.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Region topilmadi: ID {district_data['region_id']}"))
