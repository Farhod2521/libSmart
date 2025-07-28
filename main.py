import asyncpg
from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import datetime
from jose import jwt
from jose.exceptions import JWTError

# 🔐 JWT konfiguratsiya
JWT_SECRET_KEY = 'django-insecure-&1kh%#40cdf1gcnv8ejh2k8gy0m3n*m-^1-7)(uo)o=6&3)1p7' # ⛔ bu joyga Django'dagi settings.SECRET_KEY ni yozing
JWT_ALGORITHM = "HS256"

app = FastAPI()

# ✅ CORS sozlamasi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Postgres sozlamasi
DATABASE_CONFIG = {
    'user': 'libsmartuser',
    'password': 'libSmart1234',
    'database': 'libsmart',
    'host': 'localhost',
    'port': 5432
}

# 📚 Kitob modeli
class BookOut(BaseModel):
    id: int
    title_uz: str
    title_ru: Optional[str]
    title_en: Optional[str]
    description_uz: Optional[str]
    description_ru: Optional[str]
    description_en: Optional[str]

# 🔌 Bazaga ulanish
async def get_connection():
    return await asyncpg.connect(**DATABASE_CONFIG)

# ✅ JWT token orqali Customer ID ni olish
async def get_customer_id_by_token(conn, token: str) -> Optional[int]:
    print(f"🔍 JWT TOKEN: {token}")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        print(f"✅ DECODED USER ID from JWT: {user_id}")
    except JWTError as e:
        print(f"❌ JWT decoding error: {str(e)}")
        return None

    row = await conn.fetchrow("SELECT id FROM app_user_customer WHERE user_id = $1", user_id)
    if row:
        print(f"✅ CUSTOMER ID: {row['id']}")
        return row['id']
    else:
        print("❌ USER exists but CUSTOMER not linked")
        return None

# 🔍 Qidiruv endpoint
@app.get("/search", response_model=List[BookOut])
async def search_books(q: str = Query(..., min_length=1), authorization: Optional[str] = Header(None)):
    conn = await get_connection()
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    search_term = q.strip().lower()
    customer_id = None

    # 🧠 Token bor bo‘lsa, dekodlab customer_id olish
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        customer_id = await get_customer_id_by_token(conn, token)
    else:
        print("❌ Authorization header yo'q yoki noto‘g‘ri formatda")

    # 🔎 Kitob qidirish
    if len(search_term) >= 3:
        query = """
            SELECT id, title_uz, title_ru, title_en,
                   description_uz, description_ru, description_en,
                   GREATEST(
                       similarity(LOWER(title_uz), $1),
                       similarity(LOWER(title_ru), $1),
                       similarity(LOWER(title_en), $1)
                   ) as sim_score
            FROM app_book_book
            WHERE
                LOWER(title_uz) LIKE '%' || $1 || '%' OR
                LOWER(title_ru) LIKE '%' || $1 || '%' OR
                LOWER(title_en) LIKE '%' || $1 || '%' OR
                LOWER(title_uz) % $1 OR
                LOWER(title_ru) % $1 OR
                LOWER(title_en) % $1
            ORDER BY sim_score DESC
            LIMIT 20;
        """
    else:
        query = """
            SELECT id, title_uz, title_ru, title_en,
                   description_uz, description_ru, description_en
            FROM app_book_book
            WHERE
                LOWER(title_uz) LIKE $1 || '%' OR
                LOWER(title_ru) LIKE $1 || '%' OR
                LOWER(title_en) LIKE $1 || '%'
            LIMIT 20;
        """

    try:
        rows = await conn.fetch(query, search_term)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Bazada xatolik: {str(e)}")

    books = [BookOut(**{k: v for k, v in dict(row).items() if k != 'sim_score'}) for row in rows]

    try:
        book_id = rows[0]['id'] if rows else None
        print(f"📘 QIDIRUV: '{q}' | BOOK ID: {book_id} | CUSTOMER ID: {customer_id}")
        await conn.execute("""
            INSERT INTO app_book_searchhistory (customer_id, query, searched_at, book_id)
            VALUES ($1, $2, $3, $4)
        """, customer_id, q, datetime.datetime.utcnow(), book_id)
    except Exception as e:
        print(f"❌ Qidiruv tarixini saqlashda muammo: {str(e)}")

    await conn.close()
    return books

# 🚀 Ishga tushirish
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
