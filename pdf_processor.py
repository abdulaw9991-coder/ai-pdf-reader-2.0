import fitz
import re
import os
from storage import upload_image


def clean(text):
    return " ".join(text.split())


def detect_chapter(text):
    match = re.search(r"(CHAPTER\s*\d+)", text, re.IGNORECASE)
    return match.group(1).upper() if match else None


def detect_topic(text):
    match = re.search(r"\b(\d+\.\d+)\b", text)
    return match.group(1) if match else None


def safe_init(data, chapter, topic):

    if chapter not in data:
        data[chapter] = {}

    if topic not in data[chapter]:
        data[chapter][topic] = {
            "text": "",
            "images": []
        }


def process_pdf(pdf_path):
    """
    CHANGED FOR VERCEL:
    Images are no longer written to static/output/ on local disk
    (that folder is read-only and ephemeral on Vercel). Each
    extracted image is now uploaded to Vercel Blob via
    storage.upload_image(), and the returned permanent URL is stored
    in data[chapter][topic]["images"] instead of a local file path.
    Everything else (chapter/topic detection, text accumulation) is
    unchanged from the original project.
    """

    doc = fitz.open(pdf_path)

    book_name = os.path.splitext(os.path.basename(pdf_path))[0]

    data = {}

    current_chapter = "UNKNOWN_CHAPTER"
    current_topic = "GENERAL"

    for page_num in range(len(doc)):

        page = doc.load_page(page_num)
        text = clean(page.get_text())

        chapter = detect_chapter(text)
        topic = detect_topic(text)

        if chapter:
            current_chapter = chapter

        if topic:
            current_topic = topic

        safe_init(data, current_chapter, current_topic)

        # TEXT STORAGE
        data[current_chapter][current_topic]["text"] += text + "\n"

        # IMAGE EXTRACTION -> UPLOAD TO VERCEL BLOB
        images = page.get_images(full=True)

        for i, img in enumerate(images):

            try:
                xref = img[0]
                base = doc.extract_image(xref)

                img_bytes = base["image"]
                ext = base["ext"]

                filename = f"p{page_num}_{i}.{ext}"

                image_url = upload_image(
                    img_bytes,
                    book_name,
                    current_chapter,
                    current_topic,
                    filename
                )

                data[current_chapter][current_topic]["images"].append(image_url)

            except Exception:
                pass

    doc.close()

    return data, book_name
