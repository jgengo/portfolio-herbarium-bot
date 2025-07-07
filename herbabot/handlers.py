"""Telegram handlers for Herbabot."""

import logging
from functools import wraps
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from telegram import Message, Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from herbabot.config import ALLOWED_USER_IDS
from herbabot.exif_utils import extract_exif_metadata
from herbabot.github_pr import create_plant_pr
from herbabot.handlers_utils import (
    cleanup_temporary_directory,
    handle_exif_metadata,
    load_welcome_message,
    prepare_date,
    prepare_gps_data,
    process_incoming_file,
)
from herbabot.plant_entry import create_plant_entry, get_plant_entry_info
from herbabot.plant_id import identify_plant

logger = logging.getLogger(__name__)

# Type alias for telegram handler functions
HandlerFunc = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def require_authorized_user(func: HandlerFunc) -> HandlerFunc:
    """Restrict command handlers to authorized Telegram users."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user:
            logger.warning("No user found in update")
            return None

        user_id = update.effective_user.id

        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            if update.message:
                await update.message.reply_text(
                    "❌ *Access Denied*\n\nYou are not authorized to use this bot.", parse_mode="Markdown"
                )
            return None

        return await func(update, context)

    return wrapper


@require_authorized_user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message to the user."""

    welcome_message = load_welcome_message()
    if not update.message:
        return None

    await update.message.reply_text(welcome_message, parse_mode="MarkdownV2")


@require_authorized_user
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle an uploaded image, identify the plant and create a PR."""

    message = update.message
    tmp_dir = Path("tmp")

    if not message:
        return None

    try:
        # Validate and download the photo
        file_path = await process_incoming_file(message)
        if not file_path:
            return

        await message.reply_text(
            "📸 *Image received!* Processing your plant... 🌿",
            parse_mode="Markdown",
        )

        # Extract and handle EXIF metadata
        exif_metadata = extract_exif_metadata(file_path)
        await handle_exif_metadata(message, exif_metadata)

        # Identify the plant and create the portfolio entry
        await _process_plant_identification(
            message=message,
            file_path=file_path,
            exif_metadata=exif_metadata,
            tmp_dir=tmp_dir,
        )

    except Exception as e:  # pragma: no cover - network/IO errors
        logger.error(f"Error processing file: {e}")
        await message.reply_text(
            "❌ *An error occurred while processing your file*\n\nPlease try again.",
            parse_mode="Markdown",
        )
    finally:
        cleanup_temporary_directory(tmp_dir)


def register_handlers(app: Any) -> None:
    """Register bot command and message handlers."""

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ATTACHMENT, handle_file))


async def _process_plant_identification(
    message: Message,
    file_path: Path,
    exif_metadata: Dict[str, Any],
    tmp_dir: Path,
) -> None:
    """Identify the plant, create an entry and open a PR."""

    try:
        logger.info("Starting plant identification for file: %s", file_path)
        logger.debug("File size: %s bytes", file_path.stat().st_size)

        result = identify_plant(file_path)
        logger.info("Plant identification successful: %s", result.get("latin_name", "Unknown"))

        # Send plant identification results
        await _send_plant_identification_result(message, result)

        # Create plant entry and PR
        await _create_plant_entry_and_pr(message, result, file_path, exif_metadata, tmp_dir)

    except Exception as e:  # pragma: no cover - external service failures
        logger.error("Plant identification error", exc_info=True)
        logger.error("Plant identification failed for file: %s", file_path)
        logger.error("Error details: %s", e)
        await message.reply_text(
            "❌ *Could not identify the plant*\n\nPlease try another photo with better lighting and focus.",
            parse_mode="Markdown",
        )


async def _send_plant_identification_result(message: Message, result: Dict[str, Any]) -> None:
    """Send formatted plant identification results to the user."""
    plant_message = f"🌿 *{result['latin_name']}*"

    if result.get("common_name"):
        plant_message += f"\n🌸 _{result['common_name']}_"

    if result.get("family"):
        plant_message += f"\n🌳 **Family:** {result['family']}"

    plant_message += f"\n\n🎯 *Confidence:* {result['score']:.1%}"

    if result.get("description"):
        plant_message += f"\n\n📖 {result['description']}"

    await message.reply_text(plant_message, parse_mode="Markdown")


async def _create_plant_entry_and_pr(
    message: Message,
    result: Dict[str, Any],
    file_path: Path,
    exif_metadata: Dict[str, Any],
    tmp_dir: Path,
) -> None:
    """Create a plant entry from the photo and open a pull request."""

    gps_data = prepare_gps_data(exif_metadata)
    date = prepare_date(exif_metadata.get("date_taken"))

    # Create plant entry
    plant_entry_path = create_plant_entry(result, file_path, gps_data, date)
    if not plant_entry_path:
        await message.reply_text(
            "❌ Failed to create plant entry. Please try again.",
            parse_mode="Markdown",
        )
        return

    entry_info = get_plant_entry_info(result)
    logger.debug(f"Plant entry created: {entry_info['markdown_filename']}")

    # Create pull request
    pr_url = create_plant_pr(tmp_dir, result)
    if pr_url:
        await message.reply_text(
            f"✨ *Plant entry created successfully!*\n\n"
            f"🔗 [View Pull Request]({pr_url})\n"
            f"📝 Ready for review and merge",
            parse_mode="Markdown",
        )
    else:
        await message.reply_text("⚠️ Plant entry created, but failed to create pull request.")
