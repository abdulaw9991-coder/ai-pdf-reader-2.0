"""
storage.py
----------
Image storage layer for AI PDF Reader 2.0 on Vercel.
Uses vercel-blob package instead of vercel-sdk.
"""

import os
import vercel_blob


def upload_image(image_bytes, book_name, chapter, topic, filename):
    """
    Uploads a single extracted image to Vercel Blob and returns its
    permanent public URL.
    """

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