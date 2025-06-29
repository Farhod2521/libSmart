import random
import base64
import io
import json
from PIL import Image
import face_recognition
from rest_framework import serializers
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .models import User, Customer
from PIL import Image


class RegisterSerializer(serializers.ModelSerializer):
    # Customer uchun qo‘shimcha maydonlar
    birth_date = serializers.DateField()
    gender = serializers.CharField()
    language = serializers.CharField()
    region = serializers.CharField()
    education = serializers.CharField()
    occupation = serializers.CharField()
    interests = serializers.CharField(required=False, allow_blank=True)

    # 🔹 Yuz rasmi (base64 formatda yuboriladi)
    image_base64 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'phone', 'password', 'full_name', 'email',
            'birth_date', 'gender', 'language', 'region', 'education',
            'occupation', 'interests', 'image_base64'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        # Customer ma'lumotlarini ajratib olamiz
        customer_data = {
            key: validated_data.pop(key)
            for key in [
                'birth_date', 'gender', 'language', 'region',
                'education', 'occupation', 'interests',
            ]
        }

        image_base64 = validated_data.pop('image_base64')
        password = validated_data.pop('password')
        verification_code = str(random.randint(10000, 99999))

        # ✅ Rasmni base64 dan ochish
        try:
            image_bytes = base64.b64decode(image_base64)
            image_file = io.BytesIO(image_bytes)
            image_np = face_recognition.load_image_file(image_file)
            encodings = face_recognition.face_encodings(image_np)
        except Exception:
            raise serializers.ValidationError("Yuz rasmi noto‘g‘ri formatda yoki o‘qib bo‘lmadi.")

        if not encodings:
            raise serializers.ValidationError("Yuz aniqlanmadi.")

        face_encoding = json.dumps(encodings[0].tolist())  # JSON formatga aylantiramiz

        # ✅ Foydalanuvchini yaratish
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.role = 'customer'
        user.sms_code = verification_code
        user.save()

        # ✅ Customer profilini yaratish
        Customer.objects.create(
            user=user,
            face_encoding=face_encoding,
            **customer_data
        )

        # ✅ Email orqali kod yuborish
        subject = '📩 Ro‘yxatdan o‘tish uchun tasdiqlash kodi'
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [user.email]
        text_content = f"Sizning tasdiqlash kodingiz: {verification_code}"

        html_content = f"""
        <html><body>
        <div style="font-family:Arial;padding:20px;background:#fff;border-radius:10px">
        <h3 style="color:#333">📚 Kutubxonaga hush kelibsiz!</h3>
        <p style="font-size:16px;color:#555">
        Hurmatli <strong>{user.full_name}</strong>, quyidagi tasdiqlash kodini kiriting:</p>
        <div style="font-size:30px;color:#1a73e8;text-align:center;margin:20px 0;">{verification_code}</div>
        </div></body></html>
        """

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return user

    
class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()
    sms_code = serializers.CharField()

    def validate(self, attrs):
        phone = attrs.get("phone")
        code = attrs.get("sms_code")

        try:
            user = User.objects.get(phone=phone, sms_code=code)
        except User.DoesNotExist:
            raise serializers.ValidationError("Telefon raqam yoki kod noto‘g‘ri.")

        user.is_verified = True
        user.sms_code = None
        user.save()

        return {"message": "Tasdiqlash muvaffaqiyatli yakunlandi."}

class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate(self, attrs):
        phone = attrs.get("phone")

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Foydalanuvchi topilmadi.")

        code = str(random.randint(10000, 99999))
        user.sms_code = code
        user.save()

        # Send reset email
        subject = '🔐 Parolni tiklash'
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [user.email]
        text_content = f"Parolni tiklash kodingiz: {code}"

        html_content = f"""
        <html><body>
        <div style="font-family:Arial;padding:20px;background:#fff;border-radius:10px">
        <h3>Parolni tiklash uchun kod:</h3>
        <div style="font-size:30px;color:#d9534f;text-align:center;margin:20px 0;">{code}</div>
        </div></body></html>
        """

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return {"message": "Kod emailga yuborildi."}

class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    sms_code = serializers.CharField()
    new_password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, attrs):
        phone = attrs.get("phone")
        code = attrs.get("sms_code")
        new_password = attrs.get("new_password")

        try:
            user = User.objects.get(phone=phone, sms_code=code)
        except User.DoesNotExist:
            raise serializers.ValidationError("Noto‘g‘ri kod yoki telefon raqam.")

        user.set_password(new_password)
        user.sms_code = None
        user.save()

        return {"message": "Parol muvaffaqiyatli tiklandi."}
