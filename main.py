import asyncpg
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI()

# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 DB
DATABASE_CONFIG = {
    'user': 'libsmartuser',
    'password': 'libSmart1234',
    'database': 'libsmart',
    'host': 'localhost',
    'port': 5432
}

# 📘 Schema
class BookOut(BaseModel):
    id: int
    title_uz: str
    title_ru: str | None
    title_en: str | None
    description_uz: str | None
    description_ru: str | None
    description_en: str | None

async def get_connection():
    return await asyncpg.connect(**DATABASE_CONFIG)

@app.get("/search", response_model=List[BookOut])
async def search_books(q: str = Query(..., min_length=1)):
    conn = await get_connection()

    # Endi faqat ILIKE %q% bo‘yicha qidiruv qilamiz
    query = """
        SELECT id, title_uz, title_ru, title_en,
               description_uz, description_ru, description_en
        FROM app_book_book
        WHERE
            title_uz ILIKE $1 OR
            title_ru ILIKE $1 OR
            title_en ILIKE $1 OR
            description_uz ILIKE $1 OR
            description_ru ILIKE $1 OR
            description_en ILIKE $1
        LIMIT 20;
    """

    try:
        rows = await conn.fetch(query, f"%{q}%")
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Bazada xatolik: {str(e)}")

    await conn.close()
    books = [BookOut(**dict(row)) for row in rows]
    return books

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
