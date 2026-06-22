import os
import vercel_blob

def upload_image(image_bytes, book_name, chapter, topic, filename):

    # Debug: print what token is available
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    print(f"Blob token present: {bool(token)}")

    safe_chapter = chapter.replace(" ", "_")
    safe_topic   = topic.replace(" ", "_")
    blob_path = f"{book_name}/{safe_chapter}/{safe_topic}/{filename}"

    result = vercel_blob.put(
        blob_path,
        image_bytes,
        options={
            "access":          "public",
            "addRandomSuffix": False
        }
    )

    return result["url"]