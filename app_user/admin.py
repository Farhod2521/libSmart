from django.contrib import admin
from .models import User, Customer

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'role', 'is_active', 'date_joined')
    search_fields = ('full_name', 'phone')
    list_filter = ('role',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'gender', 'language', 'region')
    search_fields = ('user__full_name', 'region', 'occupation')
