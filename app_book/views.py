from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CategoryBook, Book, BookRating, BookLike, SearchHistory, DownloadHistory
from .serializers import CategoryBookSerializer, BookSerializer, BookRatingSerializer,  BookShortSerializer,BookListSerializer, BookDetailSerializer, BookLikeSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
import random
from app_user.models import Customer,  Notification
from django.db.models import Avg, Q
from .pagination import  BookPagination
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

class CategoryBookListAPIView(APIView):
    def get(self, request):
        categories = CategoryBook.objects.all()
        serializer = CategoryBookSerializer(categories, many=True)
        return Response(serializer.data)


class CategoryBookCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CategoryBookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryBookUpdateAPIView(APIView):
    def put(self, request, pk):
        category = get_object_or_404(CategoryBook, pk=pk)
        serializer = CategoryBookSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryBookDeleteAPIView(APIView):
    def delete(self, request, pk):
        category = get_object_or_404(CategoryBook, pk=pk)
        category.delete()
        return Response({"detail": "Deleted"}, status=status.HTTP_204_NO_CONTENT)


# ---------- Book Views ----------

class BookListAPIView(APIView):
    def get(self, request):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class BookCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save()

            # 🔔 Yangi kitob haqida barcha mijozlarga bildirishnoma yaratamiz
            customers = Customer.objects.all()
            for customer in customers:
                Notification.objects.create(
                    customer=customer,
                    message=f"Yangi kitob qo‘shildi: {book.title_uz}"
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.parsers import MultiPartParser, FormParser

class BookUpdateAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookDeleteAPIView(APIView):
    def delete(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        book.delete()
        return Response({"detail": "Kitob muvaffaqiyatli o‘chirildi."}, status=status.HTTP_200_OK)


class RandomBookListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            customer = user.customer_profile
            interests = customer.interests
        except Customer.DoesNotExist:
            # Agar profil yo'q bo‘lsa, random kitoblar chiqariladi
            books = list(Book.objects.all())
            random_books = random.sample(books, min(len(books), 20))
            serializer = BookSerializer(random_books, many=True)
            return Response(serializer.data)

        if interests:
            interest_list = [interest.strip() for interest in interests.split(',')]
            query = Q()
            for interest in interest_list:
                query |= Q(relation__icontains=interest)
            matched_books = Book.objects.filter(query).distinct()

            if matched_books.exists():
                books = list(matched_books)
                selected_books = random.sample(books, min(len(books), 20))
            else:
                # Agar qiziqishlar bo‘yicha hech narsa topilmasa, random kitoblar chiqariladi
                books = list(Book.objects.all())
                selected_books = random.sample(books, min(len(books), 20))
        else:
            # Agar qiziqishlar bo‘sh bo‘lsa, random kitoblar chiqariladi
            books = list(Book.objects.all())
            selected_books = random.sample(books, min(len(books), 20))

        serializer = BookSerializer(selected_books, many=True)
        return Response(serializer.data)
    
from random import sample
class BookDetailAPIView(APIView):
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        serializer = BookDetailSerializer(book)

        similar_books = []

        # --- 1. Title-ga yaqin kitoblar ---
        title_filter = Q()
        if book.title_uz:
            title_filter |= Q(title_uz__icontains=book.title_uz)
        if book.title_ru:
            title_filter |= Q(title_ru__icontains=book.title_ru)
        if book.title_en:
            title_filter |= Q(title_en__icontains=book.title_en)

        if title_filter:
            title_books_qs = Book.objects.filter(title_filter).exclude(id=book.id)
            title_books = list(title_books_qs)
            similar_books += title_books[:10]  # title-ga mos kitoblarni birinchi qo'shish

        # --- Agar 10 taga yetmagan bo'lsa, author bo'yicha qo'shish ---
        if len(similar_books) < 10:
            author_filter = Q()
            if book.creator_uz:
                author_filter |= Q(creator_uz=book.creator_uz)
            if book.creator_ru:
                author_filter |= Q(creator_ru=book.creator_ru)
            if book.creator_en:
                author_filter |= Q(creator_en=book.creator_en)

            if author_filter:
                author_books_qs = Book.objects.filter(author_filter).exclude(
                    id__in=[b.id for b in similar_books] + [book.id]
                )
                author_books = list(author_books_qs)
                remaining_slots = 10 - len(similar_books)
                similar_books += author_books[:remaining_slots]

        # --- Agar hali ham yetarli bo'lmasa, relation bo'yicha qo'shish ---
        if len(similar_books) < 10:
            relation_books_qs = Book.objects.filter(relation=book.relation).exclude(
                id__in=[b.id for b in similar_books] + [book.id]
            )
            relation_books = list(relation_books_qs)
            remaining_slots = 10 - len(similar_books)
            similar_books += relation_books[:remaining_slots]

        similar_books_serializer = BookShortSerializer(similar_books, many=True)

        return Response({
            "book": serializer.data,
            "similar_books": similar_books_serializer.data
        }, status=status.HTTP_200_OK)
##############################  BOOK RATING ###################################
class BookRatingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Foydalanuvchi Customer ekanligini tekshiramiz
        try:
            customer = user.customer_profile
        except Customer.DoesNotExist:
            return Response({'error': 'Faqat mijozlar baho bera oladi.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BookRatingSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.validated_data['book']

            # Oldin baho berilganmi, tekshiramiz
            if BookRating.objects.filter(customer=customer, book=book).exists():
                return Response({'error': 'Siz bu kitobga allaqachon baho bergansiz.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(customer=customer)
            return Response({'message': 'Baho muvaffaqiyatli qo‘shildi.'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
from django.utils import timezone
from .uztranslit import UzTranslit 
import requests
class AllBookListAPIView(APIView):
    permission_classes = []  # Allow public access

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        category_id = request.query_params.get('category')
        min_rating = request.query_params.get('min_rating')
        ordering = request.query_params.get('ordering')

        # 1️⃣ Mahalliy bazadan olish
        books = Book.objects.annotate(avg_rating=Avg('ratings__rating'))

        if search:
            def is_cyrillic(text):
                return any('А' <= c <= 'я' or c in 'ЎўҒғҚқҲҳЁё' for c in text)

            if is_cyrillic(search):
                search = UzTranslit.to_latin(search)

            books = books.filter(
                Q(title__icontains=search) |
                Q(creator__icontains=search) |
                Q(subject__icontains=search) |
                Q(description__icontains=search)
            )

            # Qidiruv tarixini saqlash
            self._save_search_history(request, search, books.first())

        if category_id:
            books = books.filter(category_id=category_id)

        if min_rating:
            try:
                min_rating = float(min_rating)
                books = books.filter(avg_rating__gte=min_rating)
            except ValueError:
                return Response({'error': 'Rating raqam bo‘lishi kerak.'}, status=status.HTTP_400_BAD_REQUEST)

        # Tartiblash
        if ordering == 'random':
            books = list(books)
            random.shuffle(books)
        elif ordering == 'rating':
            books = books.order_by('avg_rating')
        elif ordering == '-rating':
            books = books.order_by('-avg_rating')
        else:
            books = books.order_by('-id')

        # 🔹 Mahalliy bazadagi natijalar
        serializer = BookListSerializer(books, many=True)
        local_data = serializer.data

        # 2️⃣ Tashqi API'dan ma’lumot olish
        external_data = []
        try:
            response = requests.get("https://api.miku.uz/convert/all", timeout=10)
            if response.status_code == 200:
                api_data = response.json().get("data", [])
                if search:
                    search_lower = search.lower()
                    # Qidiruvni tashqi ma’lumotlarda ham bajarish
                    for item in api_data:
                        text = " ".join([
                            str(item.get("title_uz", "")),
                            str(item.get("creator_uz", "")),
                            str(item.get("subject_uz", "")),
                            str(item.get("description_uz", "")),
                        ]).lower()
                        if search_lower in text:
                            external_data.append(item)
                else:
                    external_data = api_data
        except Exception as e:
            print(f"Tashqi API xatolik: {e}")

        # 🔹 Ikkala manba birlashtirish
        combined_data = list(local_data) + list(external_data)

        # Sahifalash
        paginator = BookPagination()
        page = paginator.paginate_queryset(combined_data, request)
        return paginator.get_paginated_response(page)

    def _save_search_history(self, request, query, book=None):
        try:
            customer = None
            if request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
                customer = request.user.customer_profile
            SearchHistory.objects.create(
                customer=customer,
                query=query,
                book=book,
                searched_at=timezone.now()
            )
        except Exception as e:
            print(f"Error saving search history: {str(e)}")




class BookLikeCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        book_id = request.data.get("book")

        if not book_id:
            return Response({"error": "Kitob ID jo'natilmagan."}, status=status.HTTP_400_BAD_REQUEST)

        book = get_object_or_404(Book, id=book_id)

        # oldin yoqtirilgan bo'lsa, error qaytaramiz
        if BookLike.objects.filter(customer=customer, book=book).exists():
            return Response({"error": "Bu kitob allaqachon yoqtirilgan."}, status=status.HTTP_400_BAD_REQUEST)

        book_like = BookLike.objects.create(customer=customer, book=book)
        serializer = BookLikeSerializer(book_like)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 📄 2. Yoqtirgan kitoblar ro'yxati
class BookLikeListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        likes = BookLike.objects.filter(customer=customer)
        serializer = BookLikeSerializer(likes, many=True)
        return Response(serializer.data)

# ❌ 3. Yoqtirgan kitobni o'chirish
class BookLikeDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, book_id):
        customer = get_object_or_404(Customer, user=request.user)
        book = get_object_or_404(Book, id=book_id)

        like = BookLike.objects.filter(customer=customer, book=book).first()
        if not like:
            return Response({"error": "Bu kitob yoqtirilmagan."}, status=status.HTTP_404_NOT_FOUND)

        like.delete()
        return Response({"message": "Kitob yoqtirishlardan o'chirildi."}, status=status.HTTP_204_NO_CONTENT)
    








class BookDownloadAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            raise Http404("Kitob topilmadi.")

        if not book.is_download_allowed:
            return Response({"detail": "Bu kitobni yuklab olishga ruxsat berilmagan."}, status=status.HTTP_403_FORBIDDEN)

        if not book.file:
            return Response({"detail": "Bu kitobda fayl mavjud emas."}, status=status.HTTP_404_NOT_FOUND)

        # Yuklab olish sonini oshirish
        book.download_count += 1
        book.save(update_fields=["download_count"])

        # Yuklab olish tarixini saqlash
        customer = None
        if request.user.is_authenticated:
            customer = getattr(request.user, 'customer_profile', None)

        DownloadHistory.objects.create(
            customer=customer,
            book=book,
            device_info=request.META.get('HTTP_USER_AGENT', '')  # Qurilma haqida info
        )

        return FileResponse(book.file.open(), as_attachment=True, filename=book.file.name.split("/")[-1])
    




class DownloadedBooksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = getattr(request.user, 'customer_profile', None)
        if not customer:
            return Response({"detail": "Foydalanuvchi aniqlanmadi."}, status=400)

        # Takrorlanmas kitoblar ro‘yxati
        downloaded_books = DownloadHistory.objects.filter(customer=customer).values_list("book", flat=True).distinct()

        # Kitoblarni yuklash
        from .models import Book
        books = Book.objects.filter(id__in=downloaded_books)

        serializer = BookSerializer(books, many=True, context={'request': request})
        return Response(serializer.data)
    



import fitz  # PyMuPDF
from django.http import JsonResponse
import concurrent.futures
import re
class BookSearchLargeTextAPIView(APIView):
    def post(self, request):
        query = request.data.get('matn', '').strip().lower()
        
        if not query:
            return JsonResponse({"error": "Qidirish matni kerak"}, status=400)
        
        # Pre-compile regex pattern for case-insensitive search
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        # Get all books with PDF files (only necessary fields)
        books = Book.objects.filter(
            Q(file__isnull=False) & ~Q(file="")
        ).only('id', 'title', 'creator', 'file')
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.process_book, book, pattern) for book in books]
            results = [future.result() for future in concurrent.futures.as_completed(futures) if future.result()]
        
        return JsonResponse({"count": len(results), "results": results})
    
    def process_book(self, book, pattern):
        try:
            with fitz.open(book.file.path) as doc:
                matches = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text("text")
                    
                    # Use regex to find all matches
                    for match in pattern.finditer(text):
                        matches.append({
                            "page": page_num + 1,
                            "snippet": self.get_snippet(text, match.start(), match.end())
                        })
                
                if matches:
                    return {
                        "id": book.id,
                        "title": book.title,
                        "creator": book.creator,
                        "matches": matches
                    }
        except Exception as e:
            print(f"Xato: {book.title} - {e}")
        return None
    
    def get_snippet(self, text, start_idx, end_idx, context_length=120):
        """Get context around the match"""
        start = max(start_idx - context_length // 2, 0)
        end = min(end_idx + context_length // 2, len(text))
        return text[start:end].replace("\n", " ").strip()