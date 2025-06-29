from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RegisterSerializer,
    VerifyCodeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from deepface import DeepFace
from PIL import Image
import numpy as np
import io 
from .models import  User
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta 


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

class LoginWithFaceAPIView(APIView):
    def post(self, request):
        image = request.FILES.get('image')
        phone = request.data.get('phone')

        if not image or not phone:
            return Response({'error': 'Telefon raqam va rasm kerak!'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone=phone)
            customer = user.customer_profile
            saved_image_path = customer.face_image.path
        except User.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        try:
            input_image = np.array(Image.open(image).convert('RGB'))

            result = DeepFace.verify(
                img1_path=saved_image_path,
                img2_path=input_image,
                model_name='ArcFace',
                enforce_detection=True
            )

            if result['verified']:
                # JWT tokenlar yaratish
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                access_token.set_exp(lifetime=timedelta(hours=13))
                expires_in = timedelta(hours=13).total_seconds()

                return Response({
                    'access_token': str(access_token),
                    'refresh_token': str(refresh),
                    'expires_in': expires_in,
                    'phone': user.phone,
                    'full_name': user.full_name,
                    'message': '✅ Tizimga muvaffaqiyatli kirildi!'
                })

            return Response({'error': '⛔ Yuzlar mos emas!'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({'error': f'❌ Yuzni solishtirishda xatolik: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
