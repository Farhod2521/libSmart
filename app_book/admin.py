from django.contrib import admin
from .models import Book, CategoryBook, SearchHistory

from modeltranslation.admin import TranslationAdmin


@admin.register(CategoryBook)
class CategoryBookAdmin(TranslationAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('id',)


@admin.register(Book)
class BookAdmin(TranslationAdmin):
    list_display = ('id', 'title', 'creator', 'publisher', 'date', 'language')
    search_fields = ('title', 'creator', 'publisher', 'subject')
    list_filter = ('language', 'date')
    ordering = ('id',)


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('query', 'customer_display', 'book', 'searched_at')
    list_filter = ('searched_at',)
    search_fields = ('query', 'customer__user__full_name', 'book__title')
    autocomplete_fields = ('customer', 'book')
    ordering = ['-searched_at']

    def customer_display(self, obj):
        if obj.customer:
            return obj.customer.user.full_name
        return "Anonim"
    customer_display.short_description = "Foydalanuvchi"