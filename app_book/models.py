from django.db import models

# Create your models here.

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
    identifier = models.URLField(max_length=500, verbose_name="Identifikator / Manzil")
    source = models.CharField(max_length=255, blank=True, null=True, verbose_name="Manba")
    language = models.CharField(max_length=50, verbose_name="Til")
    relation = models.CharField(max_length=255, blank=True, null=True, verbose_name="Aloqa / Bog‘liqlik")
    coverage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Qamrov (mintaqa yoki vaqt)")
    rights = models.CharField(max_length=255, verbose_name="Huquqlar / Litsenziya")
    image = models.FileField(upload_to='books/', validators=[validate_file_size], verbose_name="Kitob rasmi", blank=True, null=True)


    file = models.FileField(upload_to='books/', validators=[validate_file_size], verbose_name="Kitob fayli", blank=True, null=True)

    class Meta:
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"

    def __str__(self):
        return self.title
