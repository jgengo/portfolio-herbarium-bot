from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import piexif
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()


def extract_exif_metadata(image_path: Path) -> dict:
    exif = _get_exif_data(image_path)
    if not exif:
        return {}

    date_taken = _get_date_taken(exif)
    gps_coords = _get_gps_coords(exif)

    return {
        "date_taken": date_taken,
        "gps_coords": gps_coords,  # (lat, lon)
    }


def convert_heic_to_jpeg(heic_path: Path) -> Optional[Path]:
    try:
        img = Image.open(heic_path)
        out_path = heic_path.with_suffix(".jpg")
        img.save(out_path, format="JPEG")
        return out_path
    except Exception as e:
        print(f"Failed to convert HEIC: {e}")
        return None


def _get_exif_data(image_path: Path) -> Optional[dict]:
    try:
        img = Image.open(image_path)
        exif_dict = piexif.load(img.info.get("exif", b""))
        return exif_dict
    except Exception as e:
        print(f"Error reading EXIF data: {e}")
        return None


def _get_date_taken(exif_data: dict) -> Optional[str]:
    try:
        date_str = exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal].decode()
        # Convert to ISO 8601 format: "2023:10:22 15:34:21" → "2023-10-22T15:34:21"
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").isoformat()
    except Exception:
        return None


def convert_gps_coord(coord, ref):
    deg, min_, sec = coord
    value = deg[0] / deg[1] + min_[0] / min_[1] / 60 + sec[0] / sec[1] / 3600
    return -value if ref in ["S", "W"] else value


def _get_gps_coords(exif_data: dict) -> Optional[Tuple[float, float]]:
    try:
        gps = exif_data["GPS"]
        lat = convert_gps_coord(
            gps[piexif.GPSIFD.GPSLatitude], gps[piexif.GPSIFD.GPSLatitudeRef].decode()
        )
        lon = convert_gps_coord(
            gps[piexif.GPSIFD.GPSLongitude], gps[piexif.GPSIFD.GPSLongitudeRef].decode()
        )
        return (lat, lon)
    except Exception:
        return None
