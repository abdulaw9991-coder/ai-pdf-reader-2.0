import os
from flask import Flask, render_template, request, session
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback")

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

try:
    import db
    db.init_db()
    DB_AVAILABLE = True
except Exception as e:
    print(f"DB init failed: {e}")
    DB_AVAILABLE = False

try:
    from pdf_processor import process_pdf
    PDF_AVAILABLE = True
except Exception as e:
    print(f"pdf_processor import failed: {e}")
    PDF_AVAILABLE = False


@app.route("/")
def home():
    data, book_name = _load_current_book()
    return render_template("index.html", data=data, book_name=book_name)


@app.route("/upload", methods=["POST"])
def upload():
    if not PDF_AVAILABLE:
        return "PDF processing unavailable. Check server logs.", 500

    file = request.files["pdf"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    data, book_name = process_pdf(path)

    if DB_AVAILABLE:
        book_id = str(uuid.uuid4())
        db.save_book(book_id, book_name, data)
        session["book_id"] = book_id
    else:
        return "Database unavailable. Check DATABASE_URL env var.", 500

    return render_template("index.html", data=data, book_name=book_name)


@app.route("/search", methods=["POST"])
def search():
    query = request.form["query"].lower()
    data, book_name = _load_current_book()
    results = {}

    if data:
        for chapter, topics in data.items():
            for topic, content in topics.items():
                if (
                    query in chapter.lower()
                    or query in topic.lower()
                    or query in content["text"].lower()
                ):
                    results[f"{chapter} → {topic}"] = content

    return render_template(
        "index.html",
        data=data,
        search_results=results,
        book_name=book_name
    )


def _load_current_book():
    book_id = session.get("book_id")
    if not book_id or not DB_AVAILABLE:
        return None, None
    return db.load_book(book_id)


if __name__ == "__main__":
    app.run(debug=True)