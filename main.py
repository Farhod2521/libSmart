import asyncpg
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI()

# PostgreSQL ma'lumotlar bazasi ulanish konfiguratsiyasi
DATABASE_CONFIG = {
    'user': 'libsmartuser',
    'password': 'libSmart1234',
    'database': 'libsmart',
    'host': 'localhost',
    'port': 5432
}

# Natijani qaytarish uchun model
class BookOut(BaseModel):
    id: int
    title_uz: str
    title_ru: str
    title_en: str
    description_uz: str | None
    description_ru: str | None
    description_en: str | None

# Ulanuvchi obyektni olish funksiyasi
async def get_connection():
    return await asyncpg.connect(**DATABASE_CONFIG)

# Qidiruv endpointi
@app.get("/search", response_model=List[BookOut])
async def search_books(q: str = Query(..., min_length=1)):
    conn = await get_connection()

    # pg_trgm extension kerak bo'lsa
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Fuzzy qidiruv query
    query = """
        SELECT id, title_uz, title_ru, title_en,
               description_uz, description_ru, description_en
        FROM books_book
        WHERE
            similarity(title_uz, $1) > 0.3 OR
            similarity(title_ru, $1) > 0.3 OR
            similarity(title_en, $1) > 0.3 OR
            similarity(description_uz, $1) > 0.3 OR
            similarity(description_ru, $1) > 0.3 OR
            similarity(description_en, $1) > 0.3
        ORDER BY GREATEST(
            similarity(title_uz, $1),
            similarity(title_ru, $1),
            similarity(title_en, $1),
            similarity(description_uz, $1),
            similarity(description_ru, $1),
            similarity(description_en, $1)
        ) DESC
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

# Asosiy ishga tushirish nuqtasi
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
