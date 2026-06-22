from flask import Flask, render_template, request, session
from pdf_processor import process_pdf
import os
import uuid
import db

app = Flask(__name__)

# CHANGED FOR VERCEL:
# A SECRET_KEY is now required because Flask sessions are used to
# remember which book_id belongs to which visitor (signed, encrypted
# cookie - no server-side memory needed). Set this as an environment
# variable in your Vercel project settings; never hardcode it.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-fallback-change-me")

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CHANGED FOR VERCEL:
# PDF_DATA and BOOK_NAME are no longer global Python variables.
# All processed PDF data now lives in Postgres (see db.py) and is
# looked up by a book_id stored in the user's session cookie.
# This makes the app safe to run across many separate, stateless
# serverless function invocations.

db.init_db()


# ------------------ HOME ------------------
@app.route("/")
def home():
    data, book_name = _load_current_book()
    return render_template("index.html", data=data, book_name=book_name)


# ------------------ UPLOAD PDF ------------------
@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["pdf"]

    # CHANGED FOR VERCEL: only /tmp is writable, and it is wiped
    # after the request finishes. That is fine here because we only
    # need the file on disk long enough for PyMuPDF to read it -
    # the actual results are saved to Postgres + Blob right after.
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    data, book_name = process_pdf(path)

    # CHANGED FOR VERCEL: save to Postgres instead of a global dict,
    # keyed by a new random book_id stored in the session cookie.
    book_id = str(uuid.uuid4())
    db.save_book(book_id, book_name, data)
    session["book_id"] = book_id

    return render_template(
        "index.html",
        data=data,
        book_name=book_name
    )


# ------------------ SEARCH FUNCTION ------------------
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
                    results[f"{chapter} \u2192 {topic}"] = content

    return render_template(
        "index.html",
        data=data,
        search_results=results,
        book_name=book_name
    )


def _load_current_book():
    """
    CHANGED FOR VERCEL: replaces direct reads of the old global
    PDF_DATA / BOOK_NAME variables. Looks up the current visitor's
    book_id from their session cookie and loads the matching record
    from Postgres. Returns (None, None) if nothing has been
    uploaded yet in this session.
    """
    book_id = session.get("book_id")
    if not book_id:
        return None, None
    return db.load_book(book_id)


if __name__ == "__main__":
    app.run(debug=True)
