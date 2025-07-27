from django.db import models
from  app_user.models  import  Customer
# Create your models here.
from django.db.models import Avg
class CategoryBook(models.Model):
    name = models.CharField(max_length=255, verbose_name="Kategoriya nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Kategoriya tavsifi")

    class Meta:
        verbose_name = "Kitob kategoriyasi"
        verbose_name_plural = "Kitob kategoriyalari"

    def __str__(self):
        return self.name


from django.core.exceptions import ValidationError

def validate_file_size(value):
    max_size_mb = 50
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Fayl hajmi {max_size_mb}MB dan oshmasligi kerak.")


class Book(models.Model):
    category = models.ForeignKey(CategoryBook, on_delete=models.CASCADE, related_name='books', verbose_name="Kategoriya")

    title = models.CharField(max_length=255, verbose_name="Sarlavha / Nomi")
    creator = models.CharField(max_length=255, verbose_name="Muallif / Yaratgan shaxs")
    subject = models.CharField(max_length=255, verbose_name="Mavzu / Kalit so‘zlar")
    description = models.TextField(verbose_name="Tavsif / Annotatsiya")
    publisher = models.CharField(max_length=255, verbose_name="Nashr etuvchi")
    contributor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Hissa qo‘shganlar")
    date = models.DateField(verbose_name="Sana")
    type = models.CharField(max_length=100, verbose_name="Resurs turi")
    format = models.CharField(max_length=100, verbose_name="Format / Fayl turi")
    identifier = models.URLField(max_length=500, verbose_name="Identifikator / Manzil", blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True, verbose_name="Manba")
    language = models.CharField(max_length=50, verbose_name="Til")
    relation = models.CharField(max_length=255, blank=True, null=True, verbose_name="Aloqa / Bog‘liqlik")
    coverage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Qamrov (mintaqa yoki vaqt)")
    rights = models.CharField(max_length=255, verbose_name="Huquqlar / Litsenziya")
    image = models.FileField(upload_to='books/', validators=[validate_file_size], verbose_name="Kitob rasmi", blank=True, null=True)
    file = models.FileField(upload_to='books/', validators=[validate_file_size], verbose_name="Kitob fayli", blank=True, null=True)
    download_count = models.PositiveIntegerField(default=0, verbose_name="Yuklab olinganlar soni")
    is_download_allowed = models.BooleanField(default=True, verbose_name="Yuklab olishga ruxsat berilsinmi?")

    class Meta:
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"

    def __str__(self):
        return self.title
    @property
    def average_rating(self):
        return self.ratings.aggregate(Avg('rating'))['rating__avg'] or 0




from django.core.validators import MinValueValidator, MaxValueValidator

class BookRating(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='book_ratings', verbose_name="Mijoz")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='ratings', verbose_name="Kitob")
    rating = models.IntegerField("Baho (1-5)", validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField("Izoh", blank=True, null=True)
    created_at = models.DateTimeField("Qo‘yilgan vaqti", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan vaqti", auto_now=True)

    class Meta:
        verbose_name = "Kitob Bahosi"
        verbose_name_plural = "Kitob Baholari"
        unique_together = ('customer', 'book')  # Har bir mijoz bir kitobga faqat bir marta baho bera oladi

    def __str__(self):
        return f"{self.customer.user.full_name} - {self.book.title} ({self.rating}⭐)"
    

class BookLike(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='liked_books', verbose_name="Mijoz")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='likes', verbose_name="Kitob")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yoqtirilgan vaqti")

    class Meta:
        verbose_name = "Yoqtirilgan kitob"
        verbose_name_plural = "Yoqtirilgan kitoblar"
        unique_together = ('customer', 'book')  # Har bir kitob faqat 1 marta like qilinadi

    def __str__(self):
        return f"{self.customer.user.full_name} → {self.book.title}"



from django.utils import timezone

class SearchHistory(models.Model):
    customer = models.ForeignKey(
        "app_user.Customer", on_delete=models.SET_NULL,
        null=True, blank=True, related_name='search_histories',
        verbose_name="Foydalanuvchi"
    )
    query = models.CharField(max_length=255, verbose_name="Qidiruv matni")
    searched_at = models.DateTimeField(default=timezone.now, verbose_name="Qidirilgan vaqt")
    
    book = models.ForeignKey(
        Book, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='search_histories',
        verbose_name="Qidirilgan kitob (agar aniqlansa)"
    )

    def __str__(self):
        return f"{self.query} - {self.customer if self.customer else 'Anonim'}"

    class Meta:
        verbose_name = "Qidiruv tarixi"
        verbose_name_plural = "Qidiruv tarixlari"
        ordering = ['-searched_at']
