from modeltranslation.translator import translator, TranslationOptions
from .models import CategoryBook, Book


class CategoryBookTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class BookTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'creator',
        'subject',
        'description',
        'publisher',
        'contributor',
        'source',
        'relation',
        'coverage',
        'rights',
    )


translator.register(CategoryBook, CategoryBookTranslationOptions)
translator.register(Book, BookTranslationOptions)
