from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RegisterSerializer,
    VerifyCodeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, CustomerProfileSerializer, NotificationSerializer,
    CustomerSerializer
)
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from PIL import Image
import numpy as np
import io 
from .models import  User, Customer
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta 
import base64
import json
import face_recognition

from django.contrib.auth import login

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Ro‘yxatdan o‘tildi. Email orqali kod yuborildi."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyCodeAPIView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestAPIView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmAPIView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class LoginWithPhoneAPIView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        user = authenticate(request, phone=phone, password=password)
        if user is not None:
            # JWT tokenlar yaratish
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token.set_exp(lifetime=timedelta(hours=13))  # Token muddati
            expires_in = timedelta(hours=13).total_seconds()

            return Response({
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'expires_in': expires_in,
                'phone': user.phone,
                'full_name': user.full_name,
                'message': '✅ Tizimga muvaffaqiyatli kirildi!'
            })

        return Response(
            {'error': '⛔ Telefon raqam yoki parol noto‘g‘ri!'},
            status=status.HTTP_400_BAD_REQUEST
        )


import re

import cv2
import numpy as np


class FaceLoginAPIView(APIView):
    def post(self, request):
        # 3 ta ketma-ket rasm olish talab qilinadi
        images = request.data.get('images', [])
        if len(images) < 3:
            return Response(
                {"error": "Kamida 3 ta rasm yuborishingiz kerak"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rasmlarni tekshirish
        try:
            # 1. Harakatni aniqlash
            if not self.detect_movement(images):
                return Response(
                    {"error": "Harakat aniqlanmadi. Iltimos, bosh harakat qiling"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Yuz pozitsiyasini tekshirish
            if not self.check_face_consistency(images):
                return Response(
                    {"error": "Yuz pozitsiyasi noto'g'ri. Iltimos, to'g'ri turib oling"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. Blink (ko'z ochish-yumish) aniqlash
            if not self.detect_blink(images):
                return Response(
                    {"error": "Ko'z qimirlashi aniqlanmadi. Iltimos, ko'zingizni bir marta yuming"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Agar barcha testlardan o'tsa
            return Response(
                {"success": "Hayotiy belgilar tasdiqlandi. Face login davom ettirilishi mumkin"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Liveness detection xatosi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def base64_to_image(self, image_base64):
        """Base64 ni OpenCV formatiga o'tkazish"""
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]
        
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    def detect_movement(self, images):
        """Rasmlar orasidagi harakatni aniqlash"""
        # Birinchi va oxirgi rasmlarni solishtirish
        img1 = self.base64_to_image(images[0])
        img2 = self.base64_to_image(images[-1])
        
        # Farqni hisoblash
        diff = cv2.absdiff(img1, img2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
        
        # O'zgarishlar soni
        change_pixels = np.sum(threshold) / 255
        return change_pixels > 500  # Empirik qiymat

    def check_face_consistency(self, images):
        """Barcha rasmlarda bir xil yuz borligini tekshirish"""
        face_encodings = []
        
        for img_base64 in images:
            img = self.base64_to_image(img_base64)
            encodings = face_recognition.face_encodings(img)
            
            if not encodings:
                return False
                
            face_encodings.append(encodings[0])
        
        # Barcha yuzlar o'rtasidagi o'xshashlik
        for i in range(1, len(face_encodings)):
            distance = face_recognition.face_distance([face_encodings[0]], face_encodings[i])[0]
            if distance > 0.6:  # Juda farq qiladi
                return False
                
        return True

    def detect_blink(self, images):
        """Ketma-ket rasmlarda ko'z yumish harakatini aniqlash"""
        eye_status = []
        
        for img_base64 in images:
            img = self.base64_to_image(img_base64)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Ko'zni aniqlash (haarcascade yordamida)
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 4)
            
            eye_status.append(len(eyes) < 2)  # Agar 2 ko'z aniqlanmasa (yumilgan)
        
        # Kamida bir marta ko'z yumilgan bo'lishi kerak
        return any(eye_status)


class CustomerProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Faqat 'customer' roliga ruxsat
        if user.role != 'customer':
            return Response({'error': 'Sizda ushbu sahifaga ruxsat yo‘q.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            customer_profile = user.customer_profile
        except Customer.DoesNotExist:
            return Response({'error': 'Profil topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerProfileSerializer(customer_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CustomerProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            customer = request.user.customer_profile
        except Customer.DoesNotExist:
            return Response({"detail": "Profil topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = request.user.customer_profile
        notifications = customer.notifications.all().order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)