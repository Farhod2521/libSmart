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

class FaceLoginAPIView(APIView):
    def post(self, request):
        image_base64 = request.data.get("image_base64")

        if not image_base64:
            return Response({"error": "Rasm yuborilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Base64 ni tozalash
            if "base64," in image_base64:
                image_base64 = image_base64.split("base64,")[1]
            
            # Bo'sh joylarni olib tashlash
            image_base64 = re.sub(r'\s+', '', image_base64)
            
            # Base64 dekod qilish
            image_bytes = base64.b64decode(image_base64)
            image_file = io.BytesIO(image_bytes)
            
            # Rasmni yuklash
            image_np = face_recognition.load_image_file(image_file)
            
            # Yuzlarni aniqlash
            face_locations = face_recognition.face_locations(image_np)
            if not face_locations:
                return Response({"error": "Yuz aniqlanmadi. Iltimos, yuzingizni to'g'ri joylashtiring."}, status=status.HTTP_400_BAD_REQUEST)
            
            unknown_encodings = face_recognition.face_encodings(image_np, face_locations)
            if not unknown_encodings:
                return Response({"error": "Yuz xususiyatlari aniqlanmadi."}, status=status.HTTP_400_BAD_REQUEST)

            unknown_encoding = unknown_encodings[0]

            # Barcha mijozlarni tekshirish
            customers = Customer.objects.exclude(face_encoding__isnull=True).exclude(face_encoding="")
            best_match = None
            best_distance = 0.6  # Standart masofa

            for customer in customers:
                try:
                    known_encoding = np.array(json.loads(customer.face_encoding))
                    distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match = customer
                except Exception as e:
                    print(f"Error processing customer {customer.id}: {str(e)}")
                    continue

            if best_match:
                login(request, best_match.user)
                return Response({
                    "message": "Tizimga muvaffaqiyatli kirildi.",
                    "user": {
                        "id": best_match.user.id,
                        "full_name": best_match.user.full_name,
                        "phone": best_match.user.phone,
                        "email": best_match.user.email,
                    },
                    "confidence": 1 - best_distance
                }, status=status.HTTP_200_OK)

            return Response({"error": "Yuz hech bir foydalanuvchiga mos kelmadi."}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            print(f"Face login error: {str(e)}")
            return Response({"error": f"Yuz tanish jarayonida xatolik yuz berdi: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


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