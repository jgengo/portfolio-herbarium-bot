import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple

import piexif
from PIL import Image
from pillow_heif import register_heif_opener

logger = logging.getLogger(__name__)
register_heif_opener()


def extract_exif_metadata(image_path: Path) -> dict[str, Any]:
    if not image_path.exists():
        logger.warning(f"Image file does not exist: {image_path}")
        return {}

    exif = _get_exif_data(image_path)
    if not exif:
        return {}

    date_taken = _get_date_taken(exif)
    gps_coords = _get_gps_coords(exif)

    return {
        "date_taken": date_taken,
        "gps_coords": gps_coords,  # (lat, lon)
    }


def convert_heic_to_jpeg(heic_path: Path) -> Path | None:
    if not heic_path.exists():
        logger.error(f"HEIC file does not exist: {heic_path}")
        return None

    try:
        with Image.open(heic_path) as image:
            # Convert to RGB mode if necessary (HEIC images might be in RGBA or other modes)
            if image.mode in ("RGBA", "LA", "P"):
                # Create a white background for transparent images
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            exif_data = image.info.get("exif")
            out_path = heic_path.with_suffix(".jpg")
            image.save(
                out_path, format="JPEG", exif=exif_data, optimize=True, quality=95
            )
            logger.info(f"Successfully converted {heic_path} to {out_path}")
            return out_path
    except (OSError, ValueError, IOError) as e:
        logger.error(f"Failed to convert HEIC {heic_path}: {e}")
        return None


def _get_exif_data(image_path: Path) -> dict[str, Any] | None:
    try:
        with Image.open(image_path) as img:
            exif_dict = piexif.load(img.info.get("exif", b""))
            return exif_dict
    except (OSError, ValueError, IOError) as e:
        logger.error(f"Error reading EXIF data from {image_path}: {e}")
        return None


def _get_date_taken(exif_data: dict[str, Any]) -> str | None:
    try:
        date_str = exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal].decode()
        # Convert to ISO 8601 format: "2023:10:22 15:34:21" → "2023-10-22T15:34:21"
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").isoformat()
    except (KeyError, ValueError, UnicodeDecodeError) as e:
        logger.debug(f"Could not extract date from EXIF data: {e}")
        return None


def convert_gps_coord(
    coord: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]], ref: str
) -> float:
    deg, min_, sec = coord
    value = deg[0] / deg[1] + min_[0] / min_[1] / 60 + sec[0] / sec[1] / 3600
    return -value if ref in ["S", "W"] else value


def _get_gps_coords(exif_data: dict[str, Any]) -> Tuple[float, float] | None:
    try:
        gps = exif_data["GPS"]
        lat = convert_gps_coord(
            gps[piexif.GPSIFD.GPSLatitude], gps[piexif.GPSIFD.GPSLatitudeRef].decode()
        )
        lon = convert_gps_coord(
            gps[piexif.GPSIFD.GPSLongitude], gps[piexif.GPSIFD.GPSLongitudeRef].decode()
        )
        return (lat, lon)
    except (KeyError, ValueError, UnicodeDecodeError) as e:
        logger.debug(f"Could not extract GPS coordinates from EXIF data: {e}")
        return None
