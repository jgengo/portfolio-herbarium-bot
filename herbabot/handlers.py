import logging
import os
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
            "📸 File received! Processing your plant image... 🌿"
        )

        exif_metadata = extract_exif_metadata(file_path)
        logger.info(f"EXIF metadata: {exif_metadata}")

        # Create an aesthetic EXIF metadata display
        if exif_metadata:
            exif_display = "*Image Details*\n\n"

            if exif_metadata.get("date_taken"):
                # Format the date nicely
                try:
                    date_obj = datetime.fromisoformat(exif_metadata["date_taken"])
                    formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
                    exif_display += f"📅 *Taken:* {formatted_date}\n"
                except:
                    exif_display += f"📅 *Taken:* {exif_metadata['date_taken']}\n"

            if exif_metadata.get("gps_coords"):
                lat, lon = exif_metadata["gps_coords"]
                exif_display += f"📍 *Location:* {lat:.6f}, {lon:.6f}\n"
                # Add a Google Maps link
                maps_url = f"https://maps.google.com/?q={lat},{lon}"
                exif_display += f"🗺️ [View on Google Maps]({maps_url})\n"

            await update.message.reply_text(exif_display, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "*Image Details*\n\nℹ️ No metadata available for this image."
            )

        # Plant identification
        try:
            logger.info(f"Starting plant identification for file: {file_path}")
            logger.info(
                f"File size before identification: {file_path.stat().st_size} bytes"
            )
            logger.info(f"File exists before identification: {file_path.exists()}")

            result = identify_plant(file_path)

            logger.info(
                f"Plant identification successful: {result.get('latin_name', 'Unknown')}"
            )

            caption = (
                f"🌿 *{result['latin_name']}*"
                + (
                    f" — _{result['common_name']}_\n"
                    if result.get("common_name")
                    else "\n"
                )
                + f"🔎 Confidence: {result['score']:.2%}\n"
                + (result.get("description") or "")
            )
            await message.reply_text(caption, parse_mode="Markdown")

            # Create plant entry using the new module
            plant_entry_path = create_plant_entry(result, file_path)
            if plant_entry_path:
                entry_info = get_plant_entry_info(result)
                await message.reply_text(
                    f"📝 Plant entry created successfully!\n"
                    f"📄 Markdown file: `{entry_info['markdown_filename']}`\n"
                    f"🖼️ Image file: `{entry_info['filename']}`\n"
                    f"📁 Location: `tmp/` directory",
                    parse_mode="Markdown",
                )

                # Create GitHub PR if token is available
                github_token = GITHUB_TOKEN

                pr_url = create_plant_pr(tmp_dir, github_token)
                if pr_url:
                    await message.reply_text(
                        f"🔗 Pull request created!\n" f"📋 Review and merge: {pr_url}",
                        parse_mode="Markdown",
                    )
                else:
                    await message.reply_text(
                        "⚠️ Failed to create pull request. Check logs for details."
                    )
        except Exception as e:
            logger.error("Plant identification error", exc_info=True)
            logger.error(f"Plant identification failed for file: {file_path}")
            logger.error(f"Error details: {str(e)}")
            await message.reply_text(
                "❌ Could not identify the plant. Please try another photo."
            )

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your file. Please try again."
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
