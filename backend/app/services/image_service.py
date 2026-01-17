import os
from PIL import Image
import io

def split_comic_page(image_bytes: bytes) -> list[bytes]:
    """Splits a 2x2 grid comic page into 4 individual panel images (bytes)."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        mid_w = width // 2
        mid_h = height // 2

        quadrants = [
            (0, 0, mid_w, mid_h),       # Top-Left
            (mid_w, 0, width, mid_h),   # Top-Right
            (0, mid_h, mid_w, height),  # Bottom-Left
            (mid_w, mid_h, width, height) # Bottom-Right
        ]

        panels = []
        for box in quadrants:
            panel = img.crop(box)
            buf = io.BytesIO()
            panel.save(buf, format="PNG")
            panels.append(buf.getvalue())
            
        return panels
    except Exception as e:
        print(f"Failed to split image: {e}")
        return []
