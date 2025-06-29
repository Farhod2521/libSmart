# 📚 LibSmart – Kutubxonalar uchun Veb Platforma

**LibSmart** — bu kutubxonalar faoliyatini raqamlashtirish va foydalanuvchilarga qulay xizmat ko‘rsatishni maqsad qilgan zamonaviy veb platformadir.

## 🎯 Loyihaning asosiy maqsadi

- Kutubxona a'zolari va xodimlari uchun yagona boshqaruv tizimini taqdim etish
- Kitoblarni qidirish, ro‘yxatdan o‘tish, ijaraga olish va qaytarish jarayonlarini avtomatlashtirish
- Kutubxona direktoriga va administratorlarga statistikani kuzatish imkonini berish
- Foydalanuvchi tajribasini (UX) soddalashtirish va tezlashtirish

## ⚙️ Texnologiyalar

- **Backend:** Python, Django REST Framework
- **Frontend:** HTML/CSS, JavaScript (yoki boshqa UI framework)
- **Ma'lumotlar bazasi:** PostgreSQL yoki MySQL
- **Admin panel:** Django Admin (Jazzmin orqali bezatilgan)
- **Autentifikatsiya:** SMS yoki parol orqali kirish

## 🚀 Ishga tushirish

1. Repozitoriyani klonlang:
    ```bash
    git clone https://github.com/your-username/libsmart.git
    ```

2. Virtual muhit yarating va faollashtiring:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3. Kerakli kutubxonalarni o‘rnating:
    ```bash
    pip install -r requirements.txt
    ```

4. Migratsiyalarni bajaring:
    ```bash
    python manage.py migrate
    ```

5. Superuser yarating:
    ```bash
    python manage.py createsuperuser
    ```

6. Serverni ishga tushiring:
    ```bash
    python manage.py runserver
    ```

## 🧾 Litsenziya

Ushbu loyiha [MIT](https://opensource.org/licenses/MIT) litsenziyasi asosida tarqatiladi.
