from django.contrib import admin
from . import models

admin.site.register(models.Region)
admin.site.register(models.District)
from django.contrib import admin as dj_admin


class HotelRoomImageInline(dj_admin.TabularInline):
	model = models.HotelRoomImage
	extra = 1


class BusinessAdmin(dj_admin.ModelAdmin):
	list_display = ('name', 'category', 'region', 'district', 'price')
	inlines = [HotelRoomImageInline]

dj_admin.site.register(models.Business, BusinessAdmin)
admin.site.register(models.BusinessCategory)
admin.site.register(models.Booking)
# admin.site.register(models.UserRegion)
admin.site.register(models.ContactUs)