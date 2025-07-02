import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from telegram import Document, Message

from herbabot.exif_utils import convert_heic_to_jpeg

logger = logging.getLogger(__name__)


def load_welcome_message() -> str:
    """Load the welcome message from the template file."""
    template_path = Path(__file__).parent.parent / "templates" / "bot_welcome.md"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Welcome message template not found at {template_path}")
        return "Welcome to Herbabot! Please send me a plant photo as a file."


async def process_incoming_file(message: Message) -> Optional[Path]:
    """Process and download an incoming file from Telegram."""
    document = message.document

    if not document:
        return None

    if not is_valid_image_document(document):
        await message.reply_text("❌ Please send an image file (JPEG, PNG, etc.). Other file types are not supported.")
        return None

    try:
        file = await document.get_file()
        media_dir = Path("media")
        media_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename and download
        filename = generate_filename(document.file_name or "")
        file_path = media_dir / filename
        await file.download_to_drive(file_path)

        logger.info(f"File successfully downloaded: {file_path}")

        # Convert HEIC if needed
        if filename.lower().endswith(".heic"):
            jpeg_path = convert_heic_to_jpeg(file_path)
            if jpeg_path:
                file_path = jpeg_path
                logger.info(f"HEIC converted to JPEG: {jpeg_path}")
            else:
                await message.reply_text("❌ Failed to convert HEIC image. Please try sending a JPEG or PNG image.")
                return None

        return file_path

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        await message.reply_text(
            "❌ Failed to download your file. Please try again.",
            parse_mode="Markdown",
        )
        return None


def is_valid_image_document(document: Document) -> bool:
    """Check if the document is a valid image file."""
    if not document:
        return False
    if not document.mime_type:
        return False
    return document.mime_type.startswith("image/")


def generate_filename(original_filename: str) -> str:
    """Generate a unique filename for the uploaded file."""
    is_heic = original_filename.lower().endswith(".heic")
    extension = ".heic" if is_heic else ".jpg"
    return f"{uuid.uuid4()}{extension}"


async def handle_exif_metadata(message: Message, exif_metadata: Dict[str, Any]) -> None:
    """Handle and log EXIF metadata from the image."""
    logger.debug(f"EXIF metadata: {exif_metadata}")

    if exif_metadata:
        log_exif_details(exif_metadata)
        await message.reply_text(
            "📊 *Image contains metadata* (location, date, etc.)",
            parse_mode="Markdown",
        )
    else:
        logger.debug("No EXIF metadata found in image")
        await message.reply_text("📊 *No metadata available* for this image", parse_mode="Markdown")


def log_exif_details(exif_metadata: Dict[str, Any]) -> None:
    """Log detailed EXIF metadata information."""
    logger.debug("Image contains EXIF metadata:")

    if exif_metadata.get("date_taken"):
        try:
            date_obj = datetime.fromisoformat(exif_metadata["date_taken"])
            formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
            logger.debug(f"Date taken: {formatted_date}")
        except Exception:
            logger.debug(f"Date taken: {exif_metadata['date_taken']}")

    if exif_metadata.get("gps_coords"):
        lat, lon = exif_metadata["gps_coords"]
        logger.debug(f"GPS coordinates: {lat:.6f}, {lon:.6f}")
        maps_url = f"https://maps.google.com/?q={lat},{lon}"
        logger.debug(f"Google Maps URL: {maps_url}")


def prepare_gps_data(exif_metadata: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """Prepare GPS data for plant entry creation."""
    if not exif_metadata or not exif_metadata.get("gps_coords"):
        return None

    lat, lon = exif_metadata["gps_coords"]
    gps_data = {
        "latitude": lat,
        "longitude": lon,
        "accuracy": exif_metadata.get("gps_accuracy"),
    }
    logger.info(f"GPS data prepared: lat={lat:.6f}, lon={lon:.6f}")
    return gps_data


def prepare_date(date_str: str | None) -> str | None:
    if not date_str:
        return None

    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def cleanup_temporary_directory(tmp_dir: Path) -> None:
    """Clean up the temporary directory."""
    if tmp_dir.exists():
        try:
            shutil.rmtree(tmp_dir)
            logger.info("Temporary directory cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to clean up temporary directory: {e}")
