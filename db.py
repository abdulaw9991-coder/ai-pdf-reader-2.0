"""
db.py
-----
Persistence layer for AI PDF Reader 2.0 on Vercel.

WHY THIS FILE EXISTS:
The original app.py kept all processed PDF data in two plain Python
global variables (PDF_DATA, BOOK_NAME). That works fine on a normal
server that keeps running forever, but it breaks on Vercel because
every request can be served by a fresh, isolated function instance
with empty memory. To make /upload and /search agree on the same
data, we now save the processed structure to a real Postgres
database (keyed by a book_id) instead of relying on memory.

REQUIRED ENVIRONMENT VARIABLE:
  DATABASE_URL  - a standard Postgres connection string, e.g.
                  postgres://user:password@host:5432/dbname
                  (Vercel Postgres / Neon / Supabase all provide this
                  automatically as an environment variable once you
                  attach a Postgres database to your Vercel project.)
"""

import os
import json
import psycopg2
from psycopg2.extras import Json


def get_connection():
    """
    Opens a new connection to the Postgres database using the
    DATABASE_URL environment variable. A new connection is opened
    per request because serverless functions cannot safely reuse
    a single long-lived connection across invocations.
    """
    
    db_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "No Postgres URL found. Add a Postgres database in "
            "Vercel Storage tab (POSTGRES_URL) or set DATABASE_URL in .env"
        )
    return psycopg2.connect(db_url)


def init_db():
    """
    Creates the 'books' table if it does not already exist.
    Call this once (e.g. from a setup script, or lazily on first
    request) before saving/loading any data.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    book_id     TEXT PRIMARY KEY,
                    book_name   TEXT NOT NULL,
                    data        JSONB NOT NULL,
                    created_at  TIMESTAMP DEFAULT NOW()
                );
                """
            )
        conn.commit()
    finally:
        conn.close()


def save_book(book_id, book_name, data):
    """
    Saves (or overwrites) the processed PDF structure for a given
    book_id. 'data' is the nested dictionary returned by
    pdf_processor.process_pdf(): { chapter: { topic: {text, images} } }
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO books (book_id, book_name, data)
                VALUES (%s, %s, %s)
                ON CONFLICT (book_id)
                DO UPDATE SET book_name = EXCLUDED.book_name,
                              data = EXCLUDED.data,
                              created_at = NOW();
                """,
                (book_id, book_name, Json(data)),
            )
        conn.commit()
    finally:
        conn.close()


def load_book(book_id):
    """
    Loads a previously saved book by its book_id.
    Returns (data, book_name) or (None, None) if not found.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT book_name, data FROM books WHERE book_id = %s;",
                (book_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None, None
            book_name, data = row
            return data, book_name
    finally:
        conn.close()
