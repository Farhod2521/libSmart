from django.contrib import admin
from .models import Book, CategoryBook

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
    list_filter = ('language', 'date', 'type')
    ordering = ('id',)
