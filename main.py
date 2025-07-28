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

DATABASE_CONFIG = {
    'user': 'libsmartuser',
    'password': 'libSmart1234',
    'database': 'libsmart',
    'host': 'localhost',
    'port': 5432
}

class BookOut(BaseModel):
    id: int
    title_uz: str
    title_ru: Optional[str]
    title_en: Optional[str]
    description_uz: Optional[str]
    description_ru: Optional[str]
    description_en: Optional[str]

async def get_connection():
    return await asyncpg.connect(**DATABASE_CONFIG)

async def get_user_id_by_token(conn, token: str) -> Optional[int]:
    try:
        row = await conn.fetchrow(
            "SELECT user_id FROM authtoken_token WHERE key = $1",
            token
        )
        return row['user_id'] if row else None
    except asyncpg.PostgresError:
        return None

@app.get("/search", response_model=List[BookOut])
async def search_books(
    q: str = Query(..., min_length=1),
    authorization: Optional[str] = Header(None)
):
    conn = None
    try:
        conn = await get_connection()
        # Ensure pg_trgm extension is available
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        
        # Process authorization header
        user_id = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            user_id = await get_user_id_by_token(conn, token)
        
        search_term = q.strip().lower()
        book_id = None

        # Determine query based on search term length
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

        rows = await conn.fetch(query, search_term)
        books = [
            BookOut(
                id=row['id'],
                title_uz=row['title_uz'],
                title_ru=row['title_ru'],
                title_en=row['title_en'],
                description_uz=row['description_uz'],
                description_ru=row['description_ru'],
                description_en=row['description_en']
            ) for row in rows
        ]
        
        # Get first book ID if available
        book_id = rows[0]['id'] if rows else None

        # Save search history
        try:
            await conn.execute(
                """
                INSERT INTO app_book_searchhistory 
                    (customer_id, query, searched_at, book_id)
                VALUES ($1, $2, $3, $4)
                """,
                user_id,  # Will be NULL if no token/user
                q,
                datetime.datetime.utcnow(),
                book_id
            )
        except Exception as e:
            # Log but don't fail the request
            print(f"Search history save error: {str(e)}")

        return books
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        )
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)