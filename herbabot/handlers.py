import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from herbabot.config import GITHUB_TOKEN
from herbabot.exif_utils import convert_heic_to_jpeg, extract_exif_metadata
from herbabot.github_pr import create_plant_pr
from herbabot.plant_entry import create_plant_entry, get_plant_entry_info
from herbabot.plant_id import identify_plant

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = _load_welcome_message()
    await update.message.reply_text(welcome_message, parse_mode="MarkdownV2")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming file uploads for plant image processing."""
    message = update.message
    tmp_dir = Path("tmp")

    try:
        # Check if the document is an image file
        document = message.document
        if (
            not document
            or not document.mime_type
            or not document.mime_type.startswith("image/")
        ):
            await update.message.reply_text(
                "❌ Please send an image file (JPEG, PNG, etc.). Other file types are not supported."
            )
            return

        file = await message.document.get_file()

        media_dir = Path("media")
        media_dir.mkdir(parents=True, exist_ok=True)

        # Check if the original file is HEIC format
        original_filename = document.file_name or ""
        is_heic = original_filename.lower().endswith(".heic")

        # Download with original extension or .jpg as fallback
        if is_heic:
            filename = f"{uuid.uuid4()}.heic"
        else:
            filename = f"{uuid.uuid4()}.jpg"

        file_path = media_dir / filename
        await file.download_to_drive(file_path)

        logger.info(f"File successfully downloaded: {file_path}")

        # Convert HEIC to JPEG if needed
        if is_heic:
            jpeg_path = convert_heic_to_jpeg(file_path)
            if jpeg_path:
                file_path = jpeg_path
                logger.info(f"HEIC converted to JPEG: {jpeg_path}")
            else:
                await update.message.reply_text(
                    "❌ Failed to convert HEIC image. Please try sending a JPEG or PNG image."
                )
                return

        await update.message.reply_text(
            "📸 *Image received!* Processing your plant... 🌿", parse_mode="Markdown"
        )

        exif_metadata = extract_exif_metadata(file_path)
        logger.debug(f"EXIF metadata: {exif_metadata}")

        # Log detailed EXIF information for debugging
        if exif_metadata:
            logger.debug("Image contains EXIF metadata:")
            if exif_metadata.get("date_taken"):
                try:
                    date_obj = datetime.fromisoformat(exif_metadata["date_taken"])
                    formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
                    logger.debug(f"Date taken: {formatted_date}")
                except:
                    logger.debug(f"Date taken: {exif_metadata['date_taken']}")

            if exif_metadata.get("gps_coords"):
                lat, lon = exif_metadata["gps_coords"]
                logger.debug(f"GPS coordinates: {lat:.6f}, {lon:.6f}")
                maps_url = f"https://maps.google.com/?q={lat},{lon}"
                logger.debug(f"Google Maps URL: {maps_url}")

            # Simple user message about EXIF data
            await update.message.reply_text(
                "📊 *Image contains metadata* (location, date, etc.)",
                parse_mode="Markdown",
            )
        else:
            logger.debug("No EXIF metadata found in image")
            await update.message.reply_text(
                "📊 *No metadata available* for this image", parse_mode="Markdown"
            )

        # Plant identification
        try:
            logger.info(f"Starting plant identification for file: {file_path}")
            logger.debug(f"File size: {file_path.stat().st_size} bytes")

            result = identify_plant(file_path)

            logger.info(
                f"Plant identification successful: {result.get('latin_name', 'Unknown')}"
            )

            # Create aesthetic plant identification message
            plant_message = f"🌿 *{result['latin_name']}*"

            if result.get("common_name"):
                plant_message += f"\n🌸 _{result['common_name']}_"

            plant_message += f"\n\n🎯 *Confidence:* {result['score']:.1%}"

            if result.get("description"):
                plant_message += f"\n\n📖 {result['description']}"

            await message.reply_text(plant_message, parse_mode="Markdown")

            # Create plant entry using the new module
            plant_entry_path = create_plant_entry(result, file_path)
            if plant_entry_path:
                entry_info = get_plant_entry_info(result)
                logger.debug(f"Plant entry created: {entry_info['markdown_filename']}")

                # Create GitHub PR if token is available
                github_token = GITHUB_TOKEN

                pr_url = create_plant_pr(tmp_dir, github_token)
                if pr_url:
                    await message.reply_text(
                        f"✨ *Plant entry created successfully!*\n\n"
                        f"🔗 [View Pull Request]({pr_url})\n"
                        f"📝 Ready for review and merge",
                        parse_mode="Markdown",
                    )
                else:
                    await message.reply_text(
                        "⚠️ Plant entry created, but failed to create pull request."
                    )
        except Exception as e:
            logger.error("Plant identification error", exc_info=True)
            logger.error(f"Plant identification failed for file: {file_path}")
            logger.error(f"Error details: {str(e)}")
            await message.reply_text(
                "❌ *Could not identify the plant*\n\nPlease try another photo with better lighting and focus.",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text(
            "❌ *An error occurred while processing your file*\n\nPlease try again.",
            parse_mode="Markdown",
        )
    finally:
        # Clean up tmp directory
        if tmp_dir.exists():
            try:
                shutil.rmtree(tmp_dir)
                logger.info("Temporary directory cleaned up successfully")
            except Exception as e:
                logger.error(f"Failed to clean up temporary directory: {e}")


def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ATTACHMENT, handle_file))


def _load_welcome_message() -> str:
    """Load the welcome message from the markdown template file."""
    template_path = Path(__file__).parent.parent / "templates" / "bot_welcome.md"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Welcome message template not found at {template_path}")
        return "Welcome to Herbabot! Please send me a plant photo as a file."
