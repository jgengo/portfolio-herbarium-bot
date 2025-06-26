import logging
import time
import uuid
from pathlib import Path

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from herbabot.exif_utils import convert_heic_to_jpeg, extract_exif_metadata

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = _load_welcome_message()
    await update.message.reply_text(welcome_message, parse_mode="MarkdownV2")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming file uploads for plant image processing."""
    message = update.message

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

    try:
        file = await message.document.get_file()

        media_dir = Path("media")
        media_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}.jpg"
        file_path = media_dir / filename

        if file_path.suffix.lower() == ".heic":
            jpeg_path = convert_heic_to_jpeg(file_path)
            if jpeg_path:
                file_path = jpeg_path

        await file.download_to_drive(file_path)

        logger.info(f"File successfully downloaded: {file_path}")

        await update.message.reply_text(
            "📸 File received! Processing your plant image... 🌿"
        )

        exif_metadata = extract_exif_metadata(file_path)
        logger.info(f"EXIF metadata: {exif_metadata}")

        await update.message.reply_text(f"EXIF metadata: {exif_metadata}")

        # TODO: Implement image processing pipeline
        # - Extract EXIF data (GPS, timestamp)
        # - Perform plant identification
        # - Generate documentation

        # Simulate processing time (remove later)
        time.sleep(5)

        await message.reply_text("✅ Processing completed successfully! 🌿")

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your file. Please try again."
        )


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
