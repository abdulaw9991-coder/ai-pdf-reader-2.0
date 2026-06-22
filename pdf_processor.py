import fitz
import re
import os
from storage import upload_image


def detect_chapter(text):
    patterns = [
        r"(CHAPTER\s*\d+)",
        r"(CHAPTER\s+(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN))",
        r"(UNIT\s*\d+)",
        r"(PART\s*\d+)",
        r"(SECTION\s*\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


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

    doc = fitz.open(pdf_path)
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    data = {}
    current_chapter = "UNKNOWN_CHAPTER"
    current_topic = "GENERAL"

    for page_num in range(len(doc)):

        page = doc.load_page(page_num)

        # Get raw text with proper line breaks preserved
        raw_text = page.get_text("text")

        chapter = detect_chapter(raw_text)
        topic = detect_topic(raw_text)

        if chapter:
            current_chapter = chapter

        if topic:
            current_topic = topic

        safe_init(data, current_chapter, current_topic)

        # Store FULL raw text — no cleaning, no truncation
        data[current_chapter][current_topic]["text"] += raw_text

        # IMAGE EXTRACTION
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
                print(f"IMG OK: {image_url}")

            except Exception as e:
                print(f"IMG FAIL p{page_num} i{i}: {e}")

    doc.close()
    return data, book_name