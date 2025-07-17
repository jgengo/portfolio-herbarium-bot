import logging
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Template

from herbabot.plant_description import generate_plant_description

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    """Convert scientific name to a safe filename."""
    # Replace spaces and special characters with hyphens
    sanitized = re.sub(r"[^\w\s-]", "", name.lower())
    sanitized = re.sub(r"[-\s]+", "-", sanitized)
    return sanitized.strip("-") + ".jpg"


def create_plant_entry(
    result: Dict[str, Any],
    image_path: Path,
    gps_data: Dict[str, float] | None = None,
    date: str | None = None,
) -> Path | None:
    """
    Create a plant entry markdown file using the Jinja2 template.

    Args:
        result: Dictionary containing plant identification results
        image_path: Path to the original image file
        gps_data: Optional dictionary containing GPS coordinates
                  Expected format: {"latitude": float, "longitude": float, "accuracy": float}

    Returns:
        Path to the created plant entry markdown file, or None if creation failed
    """
    # Load the template
    template_path = Path(__file__).parent.parent / "templates" / "plant_entry.md.j2"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        logger.error(f"Plant entry template not found at {template_path}")
        return None

    # Create tmp directory
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from scientific name
    scientific_name = result.get("latin_name", "unknown-plant")
    filename = _sanitize_filename(scientific_name)

    # Create the plant entry file path
    plant_entry_path = tmp_dir / f"{_sanitize_filename(scientific_name).replace('.jpg', '')}.md"

    # Generate enhanced description using OpenAI
    logger.info(f"Generating OpenAI description for {scientific_name}")
    ai_description = generate_plant_description(result)

    # Use OpenAI description if available, otherwise fall back to existing description
    description = ai_description if ai_description else result.get("description")

    # Prepare template variables
    template_vars = {
        "name": result.get("common_name", scientific_name),
        "family": result.get("family", "Unknown"),  # Use family from Pl@ntNet response
        "scientificName": scientific_name,
        "fileName": filename,
        "description": description,
        "date": date,
    }

    # Add GPS data if available
    if gps_data:
        template_vars["latitude"] = gps_data.get("latitude")
        template_vars["longitude"] = gps_data.get("longitude")
        template_vars["accuracy"] = gps_data.get("accuracy")

    # Render the template
    template = Template(template_content)
    rendered_content = template.render(**template_vars)

    # Write the plant entry file
    try:
        with open(plant_entry_path, "w", encoding="utf-8") as f:
            f.write(rendered_content)

        # Copy the image to tmp directory with scientific name
        image_dest_path = tmp_dir / filename
        shutil.copy2(image_path, image_dest_path)

        logger.info(f"Plant entry created: {plant_entry_path}")
        logger.info(f"Image copied to: {image_dest_path}")

        return plant_entry_path
    except Exception as e:
        logger.error(f"Error creating plant entry: {e}")
        return None


def get_plant_entry_info(result: Dict[str, Any]) -> Dict[str, str]:
    """
    Get formatted information about the plant entry for display.

    Args:
        result: Dictionary containing plant identification results

    Returns:
        Dictionary with formatted strings for display
    """
    scientific_name = result.get("latin_name", "Unknown")
    filename = _sanitize_filename(scientific_name)

    return {
        "scientific_name": scientific_name,
        "filename": filename,
        "markdown_filename": f"{_sanitize_filename(scientific_name).replace('.jpg', '')}.md",
    }
