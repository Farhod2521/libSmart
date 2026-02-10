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
from .models import  User, Customer, Notification
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
                "role": user.role,
                'user': {
                    'id': user.id,
                    'phone': user.phone,
                    'full_name': user.full_name,
                    'email': user.email,
                    'role': user.role,
                },
                'message': '✅ Tizimga muvaffaqiyatli kirildi!'
            })

        return Response(
            {'error': '⛔ Telefon raqam yoki parol noto‘g‘ri!'},
            status=status.HTTP_400_BAD_REQUEST
        )

class LoginWithPhoneAdminAPIView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        user = authenticate(request, phone=phone, password=password)
        if user is not None:
            if user.role not in ['admin', 'director']:
                return Response(
                    {'error': '⛔ Sizning rolingiz tizimga kirish uchun ruxsat etilmagan!'},
                    status=status.HTTP_403_FORBIDDEN
                )

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
                "role": user.role,
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
        phone = request.data.get("phone")
        image_base64 = request.data.get("image_base64")
        liveness_required = request.data.get("liveness", True)

        if not image_base64:
            return Response(
                {"error": "Rasm yuborilmadi"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Rasmni qayta ishlash
            try:
                img = self.base64_to_image(image_base64)
            except Exception:
                return Response(
                    {"error": "Rasmni o'qib bo'lmadi. Base64 formatni tekshiring."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 1. Yuzni aniqlash
            face_locations = face_recognition.face_locations(img)
            if not face_locations:
                return Response(
                    {"error": "Yuz aniqlanmadi. Iltimos, to'g'ri qarang"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 2. Yuz encodinglarini olish (eng katta yuzni olamiz)
            face_locations = [self.pick_largest_face(face_locations)]
            face_encodings = face_recognition.face_encodings(img, face_locations)
            if not face_encodings:
                return Response(
                    {"error": "Yuz xususiyatlari aniqlanmadi"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            unknown_encoding = face_encodings[0]
            
            # 3. Liveness tekshiruvi (oddiy versiya)
            if liveness_required and not self.check_liveness(img):
                return Response(
                    {"error": "Hayotiy belgilar aniqlanmadi"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. Foydalanuvchini aniqlash: telefon bo'lsa shu user, bo'lmasa face bo'yicha qidiramiz
            if phone:
                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    return Response(
                        {"error": "Foydalanuvchi topilmadi"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                if user.role != 'customer':
                    return Response(
                        {"error": "Ushbu login faqat mijozlar uchun"},
                        status=status.HTTP_403_FORBIDDEN
                    )

                try:
                    customer = user.customer_profile
                except Customer.DoesNotExist:
                    return Response(
                        {"error": "Mijoz profili topilmadi"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                if not customer.face_encoding:
                    return Response(
                        {"error": "Mijoz uchun yuz ma'lumoti mavjud emas"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not self.is_same_user_face(unknown_encoding, customer):
                    return Response(
                        {"error": "Yuz mos kelmadi"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            else:
                customer = self.find_best_match(unknown_encoding)
                if not customer:
                    return Response(
                        {"error": "Yuz mos kelmadi"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                user = customer.user
            
            # 5. Login qilish va JWT token yaratish
            login(request, user)
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
                "role": user.role,
                'message': '✅ Tizimga muvaffaqiyatli kirildi!'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Xato yuz berdi: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def base64_to_image(self, image_base64):
        """Base64 ni face_recognition uchun RGB formatiga o'tkazish"""
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]
        image_base64 = re.sub(r'\s+', '', image_base64)
        missing_padding = len(image_base64) % 4
        if missing_padding:
            image_base64 += "=" * (4 - missing_padding)
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        return np.ascontiguousarray(image.convert("RGB"))

    def check_liveness(self, image):
        """Oddiy liveness tekshiruvi"""
        # 1. Yuz joylashuvi va o'lchami
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            return True
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return False
        
        # 2. Ko'zlar mavjudligi
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        if eye_cascade.empty():
            return True
        eyes = eye_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(eyes) < 1:
            return False
        
        # 3. Yuz teksturasi analizi (oddiy versiya)
        # Haqiqiy loyihada bu aniqroq bo'lishi kerak
        return True

    def is_same_user_face(self, unknown_encoding, customer):
        """Faqat berilgan mijozning yuzini tekshiradi"""
        try:
            known_encoding = self.parse_face_encoding(customer.face_encoding)
            if known_encoding is None:
                return False
            distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
            # 0.6 - standart masofa, loyihangizga qarab o'zgartirishingiz mumkin
            return distance < 0.6
        except Exception as e:
            print(f"Xato customer {customer.id}: {str(e)}")
            return False

    def parse_face_encoding(self, value):
        if value is None:
            return None
        if isinstance(value, (list, tuple, np.ndarray)):
            return np.array(value, dtype=np.float32)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                decoded = json.loads(text)
            except Exception:
                return None
            return np.array(decoded, dtype=np.float32)
        return None

    def pick_largest_face(self, face_locations):
        # face_locations: [(top, right, bottom, left), ...]
        def area(loc):
            top, right, bottom, left = loc
            return max(0, bottom - top) * max(0, right - left)
        return max(face_locations, key=area)

    def find_best_match(self, unknown_encoding):
        best_customer = None
        best_distance = 1.0
        customers = Customer.objects.select_related("user").exclude(face_encoding__isnull=True).exclude(face_encoding="")
        for customer in customers:
            known_encoding = self.parse_face_encoding(customer.face_encoding)
            if known_encoding is None:
                continue
            try:
                distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
            except Exception:
                continue
            if distance < best_distance:
                best_distance = distance
                best_customer = customer
        if best_customer and best_distance < 0.6:
            return best_customer
        return None



class CustomerProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Admin uchun maxsus ma'lumot
        if user.role == 'admin':
            admin_data = {
                'full_name': user.full_name,
                'phone': user.phone,
                'email': user.email,
                'role': user.role
            }
            return Response(admin_data, status=status.HTTP_200_OK)

        # Faqat 'customer' roliga ruxsat
        if user.role != 'customer':
            return Response(
                {'error': 'Sizda ushbu sahifaga ruxsat yo‘q.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            customer_profile = user.customer_profile
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Profil topilmadi.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CustomerProfileSerializer(customer_profile)
        customer_data = serializer.data
        customer_data['role'] = user.role  # Rol qo'shish
        return Response(customer_data, status=status.HTTP_200_OK)

class AdminProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Faqat 'customer' roliga ruxsat
        if user.role != 'admin':
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
        user = request.user

        if user.role != 'customer':
            return Response(
                {'error': 'Sizda ushbu sahifaga ruxsat yo‘q.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            customer = user.customer_profile
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Profil topilmadi.'},
                status=status.HTTP_404_NOT_FOUND
            )

        notifications = Notification.objects.filter(
            customer=customer
        ).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    

class NotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.role != 'customer':
            return Response(
                {'error': 'Sizda ushbu sahifaga ruxsat yo‘q.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            notification = Notification.objects.get(pk=pk, customer__user=request.user)
        except Notification.DoesNotExist:
            return Response({'detail': 'Bildirishnoma topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save()

        return Response({'detail': 'Bildirishnoma o\'qilgan deb belgilandi.'}, status=status.HTTP_200_OK)
