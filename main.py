import asyncpg
from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 PostgreSQL config
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
    title_ru: Optional[str]
    title_en: Optional[str]
    description_uz: Optional[str]
    description_ru: Optional[str]
    description_en: Optional[str]

# 🔌 Ulanuvchi olish
async def get_connection():
    return await asyncpg.connect(**DATABASE_CONFIG)

# 🔐 Token orqali foydalanuvchini aniqlash va Customer ID ni olish
async def get_customer_id_by_token(conn, token: str) -> Optional[int]:
    row = await conn.fetchrow("""
        SELECT cu.id AS customer_id
        FROM authtoken_token t
        JOIN app_user_user u ON u.id = t.user_id
        JOIN app_user_customer cu ON cu.user_id = u.id
        WHERE t.key = $1
    """, token)
    return row["customer_id"] if row else None

# 🔍 Qidiruv endpoint
@app.get("/search", response_model=List[BookOut])
async def search_books(q: str = Query(..., min_length=1), authorization: Optional[str] = Header(None)):
    conn = await get_connection()
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    search_term = q.strip().lower()
    customer_id = None

    # Token orqali customer_id ni aniqlash
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        customer_id = await get_customer_id_by_token(conn, token)

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

    books = [BookOut(**{k: v for k, v in dict(row).items() if k != 'sim_score'})
             for row in rows]

    try:
        book_id = rows[0]['id'] if rows else None
        await conn.execute("""
            INSERT INTO app_book_searchhistory (customer_id, query, searched_at, book_id)
            VALUES ($1, $2, $3, $4)
        """, customer_id, q, datetime.datetime.utcnow(), book_id)
    except Exception as e:
        print(f"[Xatolik] Qidiruv tarixini saqlashda muammo: {str(e)}")

    await conn.close()
    return books

# 🚀 Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
