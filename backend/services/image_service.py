import io
from PIL import Image


def remove_background(image_bytes: bytes) -> bytes:
    """Remove background from clothing photo using rembg."""
    try:
        from rembg import remove
        output_bytes = remove(image_bytes)
        return output_bytes
    except ImportError:
        # rembg not installed — return original (fallback during dev)
        return image_bytes


def validate_and_resize(image_bytes: bytes, max_size: int = 1200) -> bytes:
    """Resize image to max_size on longest edge and convert to JPEG."""
    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA to RGB for JPEG output
    if img.mode in ("RGBA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            bg.paste(img, mask=img.split()[3])
        else:
            bg.paste(img)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize keeping aspect ratio
    w, h = img.size
    if max(w, h) > max_size:
        if w > h:
            img = img.resize((max_size, int(h * max_size / w)), Image.LANCZOS)
        else:
            img = img.resize((int(w * max_size / h), max_size), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def remove_background_png(image_bytes: bytes) -> bytes:
    """Remove background and return PNG with transparency."""
    try:
        from rembg import remove
        return remove(image_bytes)
    except ImportError:
        return image_bytes
