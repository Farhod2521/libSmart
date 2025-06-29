from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqam kiritilishi shart")
        extra_fields.setdefault('is_active', True)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Mijoz'),
        ('director', 'Direktor'),
        ('employee', 'Xodim'),
    )

    phone = models.CharField("Telefon raqam", max_length=20, unique=True)
    email = models.EmailField("Email", null=True, blank=True)
    full_name = models.CharField("F.I.O.", max_length=255)
    role = models.CharField("Rol", max_length=20, choices=ROLE_CHOICES, default='customer')
    
    is_active = models.BooleanField("Faolmi", default=True)
    is_staff = models.BooleanField("Staff huquqi", default=False)
    date_joined = models.DateTimeField("Ro'yxatdan o'tgan sana", default=timezone.now)

    # Verification
    sms_code = models.CharField("Tasdiqlash kodi", max_length=6, blank=True, null=True)
    is_verified = models.BooleanField("Tasdiqlangan", default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile', verbose_name="Foydalanuvchi")

    birth_date = models.DateField("Tug‘ilgan sana")
    gender = models.CharField("Jinsi", max_length=20)
    language = models.CharField("Tili", max_length=20)
    region = models.CharField("Yashash hududi", max_length=255)
    education = models.CharField("Ta’lim darajasi", max_length=50)
    occupation = models.CharField("Kasbi", max_length=255)
    interests = models.TextField("Qiziqishlari", blank=True)

    # ✅ Yangi maydon: yuz encoding vektori (text holatda)
    face_encoding = models.TextField("Yuz vektori (128 float)", blank=True, null=True)

    def __str__(self):
        return f"{self.user.full_name} - Customer"

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"