import asyncpg
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI()

# 🌍 CORS qo‘shamiz (hamma domenlarga ruxsat beriladi)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # barcha domenlarga ruxsat
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, DELETE, va boshqalar
    allow_headers=["*"],  # barcha headerlarga ruxsat
)

# 📦 PostgreSQL sozlamalari
DATABASE_CONFIG = {
    'user': 'libsmartuser',
    'password': 'libSmart1234',
    'database': 'libsmart',
    'host': 'localhost',
    'port': 5432
}

# 📘 Kitob modeli
class BookOut(BaseModel):
    id: int
    title_uz: str
    title_ru: str | None
    title_en: str | None
    description_uz: str | None
    description_ru: str | None
    description_en: str | None

# 🔌 Ulanuvchi olish
async def get_connection():
    return await asyncpg.connect(**DATABASE_CONFIG)

# 🔍 Qidiruv endpoint
@app.get("/search", response_model=List[BookOut])
async def search_books(q: str = Query(..., min_length=1)):
    conn = await get_connection()
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    
    # Agar so'z 3 harfdan kam bo'lsa, faqat boshlanishiga qarab qidiruv
    if len(q) < 3:
        query = """
            SELECT id, title_uz, title_ru, title_en,
                   description_uz, description_ru, description_en
            FROM app_book_book
            WHERE
                title_uz ILIKE $1 || '%' OR
                title_ru ILIKE $1 || '%' OR
                title_en ILIKE $1 || '%'
            LIMIT 20;
        """
    else:
        # 3 yoki undan ortiq harflar uchun trigram qidiruv
        query = """
            SELECT id, title_uz, title_ru, title_en,
                   description_uz, description_ru, description_en,
                   GREATEST(
                       similarity(title_uz, $1),
                       similarity(title_ru, $1),
                       similarity(title_en, $1),
                       similarity(description_uz, $1),
                       similarity(description_ru, $1),
                       similarity(description_en, $1)
                   ) as sim_score
            FROM app_book_book
            WHERE
                title_uz % $1 OR
                title_ru % $1 OR
                title_en % $1 OR
                description_uz % $1 OR
                description_ru % $1 OR
                description_en % $1
            ORDER BY sim_score DESC
            LIMIT 20;
        """
    
    try:
        rows = await conn.fetch(query, q)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Bazada xatolik: {str(e)}")
    
    await conn.close()
    books = [BookOut(**dict(row)) for row in rows]
    return books

# 🚀 Ishga tushirish
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
