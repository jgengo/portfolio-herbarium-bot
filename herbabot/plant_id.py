import logging
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from herbabot.config import PLANTNET_API_KEY, PLANTNET_API_URL

logger = logging.getLogger(__name__)


def identify_plant(
    image_path: Path | str,
    organs: Optional[str] = None,
) -> Dict[str, Any]:
    if not PLANTNET_API_KEY:
        raise ValueError(
            "Missing PLANTNET_API_KEY environment variable for Pl@ntNet API access"
        )

    path = Path(image_path)
    if not path.is_file():
        raise ValueError(f"Image file not found: {image_path}")

    # Log request preparation
    logger.info(f"Preparing PlantNet API request for image: {path}")
    logger.info(f"Image file size: {path.stat().st_size} bytes")
    logger.info(f"Image file exists: {path.exists()}")

    params: Dict[str, Any] = {"api-key": PLANTNET_API_KEY}
    if organs:
        params["organs"] = organs

    logger.info(f"API parameters: {params}")
    logger.info(f"API URL: {PLANTNET_API_URL}")

    try:
        with path.open("rb") as f:
            files = {"images": f}
            logger.info("Sending request to PlantNet API...")
            response = requests.post(PLANTNET_API_URL, params=params, files=files)

        # Log response details
        logger.info(f"PlantNet API response status: {response.status_code}")
        logger.info(f"PlantNet API response headers: {dict(response.headers)}")

        if response.status_code != 200:
            logger.error(f"PlantNet API error response: {response.text}")
            logger.error(f"Request URL: {response.url}")
            logger.error(f"Request headers: {dict(response.request.headers)}")

        response.raise_for_status()
        data = response.json()

        logger.info(f"PlantNet API response received successfully")
        logger.info(f"Number of results: {len(data.get('results', []))}")

    except requests.exceptions.RequestException as e:
        logger.error(f"PlantNet API request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Error response status: {e.response.status_code}")
            logger.error(f"Error response text: {e.response.text}")
        raise

    results = data.get("results") or []
    if not results:
        logger.warning("No plant identification results returned from PlantNet API")
        raise ValueError("No plant identification results returned")

    top = results[0]
    score = top.get("score")
    species = top.get("species", {})
    latin_name = species.get("scientificNameWithoutAuthor")
    common_names = species.get("commonNames") or []
    common_name = common_names[0] if common_names else None
    family = (
        species.get("family", {}).get("scientificNameWithoutAuthor")
        if species.get("family")
        else None
    )

    logger.info(
        f"Top result - Latin name: {latin_name}, Common name: {common_name}, Family: {family}, Score: {score}"
    )

    description: Optional[str] = None
    gbif = top.get("gbif", {})
    wiki = gbif.get("wikiDescription")
    if isinstance(wiki, dict):
        description = wiki.get("value")

    return {
        "latin_name": latin_name,
        "common_name": common_name,
        "family": family,
        "description": description,
        "score": score,
        "raw": data,
    }
