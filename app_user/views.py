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


class FaceLoginAPIView(APIView):
    def post(self, request):
        image_base64 = request.data.get("image_base64")

        if not image_base64:
            return Response({"error": "Rasm yuborilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image_bytes = base64.b64decode(image_base64)
            image_file = io.BytesIO(image_bytes)
            image_np = face_recognition.load_image_file(image_file)
            unknown_encodings = face_recognition.face_encodings(image_np)
        except Exception as e:
            return Response({"error": "Yuz rasmni o‘qib bo‘lmadi."}, status=status.HTTP_400_BAD_REQUEST)

        if not unknown_encodings:
            return Response({"error": "Yuz aniqlanmadi."}, status=status.HTTP_400_BAD_REQUEST)

        unknown_encoding = unknown_encodings[0]

        # 🔍 Barcha mijozlarning encodinglarini tekshiramiz
        customers = Customer.objects.exclude(face_encoding__isnull=True).exclude(face_encoding="")

        for customer in customers:
            try:
                known_encoding = np.array(json.loads(customer.face_encoding))
                match = face_recognition.compare_faces([known_encoding], unknown_encoding)[0]

                if match:
                    # ✅ Login qilish
                    login(request, customer.user)
                    return Response({
                        "message": "Tizimga muvaffaqiyatli kirildi.",
                        "user": {
                            "id": customer.user.id,
                            "full_name": customer.user.full_name,
                            "phone": customer.user.phone,
                            "email": customer.user.email,
                        }
                    }, status=status.HTTP_200_OK)
            except Exception:
                continue

        return Response({"error": "Yuz hech bir foydalanuvchiga mos kelmadi."}, status=status.HTTP_401_UNAUTHORIZED)
    


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