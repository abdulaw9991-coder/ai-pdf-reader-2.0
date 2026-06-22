# AI PDF Reader 2.0 — Vercel Deployment (Option B: Postgres + Vercel Blob)

This version replaces the original in-memory PDF_DATA dict and local
static/output/ image folder with real persistence, so the app works
correctly on Vercel's stateless serverless functions.

## What changed vs. the original project

| File | Status | Why |
|---|---|---|
| vercel.json | NEW | Tells Vercel how to run app.py as a Python function |
| requirements.txt | NEW | Lists Flask, PyMuPDF, psycopg2-binary, vercel-sdk |
| .vercelignore | NEW | Keeps local uploads/ and static/output/ sample data out of the deploy bundle |
| .env.example | NEW | Documents the 3 required environment variables |
| db.py | NEW | Saves/loads processed PDF data to/from Postgres |
| storage.py | NEW | Uploads extracted images to Vercel Blob, returns public URLs |
| app.py | UPDATED | Removed global PDF_DATA/BOOK_NAME; now uses db.py + session cookie (book_id) |
| pdf_processor.py | UPDATED | Images are uploaded via storage.py instead of written to local disk |
| templates/index.html | UPDATED | `<img src="{{ img }}">` instead of `<img src="/{{ img }}">` since images are now full external URLs |

## One-time setup (Vercel dashboard)

1. Push this project to a GitHub repository.
2. Import the repo into Vercel (vercel.com -> Add New -> Project).
3. In your new Vercel project, go to the **Storage** tab:
   - Create a **Postgres** database and attach it. Vercel auto-adds `DATABASE_URL`.
   - Create a **Blob** store and attach it. Vercel auto-adds `BLOB_READ_WRITE_TOKEN`.
4. Go to **Settings -> Environment Variables** and add one more manually:
   - `SECRET_KEY` = a random 64-character string
     (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
5. Redeploy (Vercel does this automatically after env vars change).

## Local development

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # macOS/Linux

pip install -r requirements.txt

cp .env.example .env              # then fill in real values
vercel env pull                   # or pull real values from your Vercel project

python app.py
```

## How data now flows

1. User uploads a PDF -> `/upload` saves it to `/tmp` (Vercel's only writable, temporary folder), processes it, then immediately persists the result to Postgres (`db.save_book`) and uploads every image to Vercel Blob (`storage.upload_image`).
2. A random `book_id` is generated and stored in the user's signed session cookie.
3. `/search` reads the same `book_id` from the cookie and loads the data back from Postgres (`db.load_book`) — no reliance on server memory.
4. Images render directly from their permanent Vercel Blob URLs.

## Known trade-off

Each browser session has its own `book_id` (via cookie), so each user's uploaded book is private to them, and a fresh upload always creates a new database row rather than overwriting one shared global — closer to how a real multi-user app should behave than the original prototype.
