import os
import vercel_blob


def upload_image(image_bytes, book_name, chapter, topic, filename):

    token = os.environ.get("BLOB_READ_WRITE_TOKEN")

    if not token:
        raise RuntimeError("BLOB_READ_WRITE_TOKEN not set")

    safe_book    = book_name.replace(" ", "_")[:50]
    safe_chapter = chapter.replace(" ", "_")[:50]
    safe_topic   = topic.replace(" ", "_")[:50]

    blob_path = f"{safe_book}/{safe_chapter}/{safe_topic}/{filename}"

    result = vercel_blob.put(
        blob_path,
        image_bytes,
        options={
            "access": "public",
            "addRandomSuffix": False
        }
    )

    return result["url"]