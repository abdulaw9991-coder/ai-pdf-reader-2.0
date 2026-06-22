import fitz
import re
import os
from storage import upload_image


def clean(text):
    return " ".join(text.split())


def detect_chapter(text):
    # Format: CHAPTER 1 or CHAPTER1
    match = re.search(r"(CHAPTER\s*\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Format: Chapter One, Chapter Two etc
    match = re.search(
        r"(CHAPTER\s+(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN))",
        text, re.IGNORECASE
    )
    if match:
        return match.group(1).upper()

    # Format: "1. Introduction" or "2. Background"
    match = re.search(r"^(\d+)\.\s+[A-Z][a-z]", text, re.MULTILINE)
    if match:
        return f"CHAPTER {match.group(1)}"

    # Format: UNIT 1, UNIT 2
    match = re.search(r"(UNIT\s*\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Format: PART 1, PART 2
    match = re.search(r"(PART\s*\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return None


def detect_topic(text):
    # Format: 1.1 or 2.3 or 12.10
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

    doc = fitz.open(pdf_path)
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    data = {}
    current_chapter = "UNKNOWN_CHAPTER"
    current_topic = "GENERAL"

    for page_num in range(len(doc)):

        page = doc.load_page(page_num)
        raw_text = page.get_text()
        text = clean(raw_text)

        chapter = detect_chapter(text)
        topic = detect_topic(text)

        if chapter:
            current_chapter = chapter
            print(f"Chapter detected: {chapter} on page {page_num}")

        if topic:
            current_topic = topic
            print(f"Topic detected: {topic} on page {page_num}")

        safe_init(data, current_chapter, current_topic)

        # Store full text
        data[current_chapter][current_topic]["text"] += text + "\n"

        # IMAGE EXTRACTION
        images = page.get_images(full=True)
        print(f"Page {page_num}: found {len(images)} images")

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
                print(f"Image uploaded OK: {image_url}")

            except Exception as e:
                print(f"Image FAILED page {page_num} img {i}: {e}")

    doc.close()
    return data, book_name