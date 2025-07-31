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
        # Faqat 1 ta rasm qabul qilamiz
        image_base64 = request.data.get("image_base64")
        
        if not image_base64:
            return Response(
                {"error": "Rasm yuborilmadi"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Rasmni qayta ishlash
            img = self.base64_to_image(image_base64)
            
            # 1. Yuzni aniqlash
            face_locations = face_recognition.face_locations(img)
            if not face_locations:
                return Response(
                    {"error": "Yuz aniqlanmadi. Iltimos, to'g'ri qarang"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 2. Yuz encodinglarini olish
            face_encodings = face_recognition.face_encodings(img, face_locations)
            if not face_encodings:
                return Response(
                    {"error": "Yuz xususiyatlari aniqlanmadi"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            unknown_encoding = face_encodings[0]
            
            # 3. Liveness tekshiruvi (oddiy versiya)
            if not self.check_liveness(img):
                return Response(
                    {"error": "Hayotiy belgilar aniqlanmadi"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. Bazadagi foydalanuvchilarni tekshirish
            user = self.find_matching_user(unknown_encoding)
            if not user:
                return Response(
                    {"error": "Foydalanuvchi topilmadi"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 5. Login qilish
            login(request, user)
            return Response({
                "success": "Muvaffaqiyatli kirish",
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "phone": user.phone,
                    "email": user.email,
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Xato yuz berdi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def base64_to_image(self, image_base64):
        """Base64 ni OpenCV formatiga o'tkazish"""
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]
        
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    def check_liveness(self, image):
        """Oddiy liveness tekshiruvi"""
        # 1. Yuz joylashuvi va o'lchami
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return False
        
        # 2. Ko'zlar mavjudligi
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        eyes = eye_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(eyes) < 2:
            return False
        
        # 3. Yuz teksturasi analizi (oddiy versiya)
        # Haqiqiy loyihada bu aniqroq bo'lishi kerak
        return True

    def find_matching_user(self, unknown_encoding):
        """Bazadan mos keladigan foydalanuvchini qidirish"""
        customers = Customer.objects.exclude(face_encoding__isnull=True).exclude(face_encoding="")
        
        for customer in customers:
            try:
                known_encoding = np.array(json.loads(customer.face_encoding))
                distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
                
                # 0.6 - standart masofa, loyihangizga qarab o'zgartirishingiz mumkin
                if distance < 0.6:
                    return customer.user
            except Exception as e:
                print(f"Xato customer {customer.id}: {str(e)}")
                continue
        
        return None


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