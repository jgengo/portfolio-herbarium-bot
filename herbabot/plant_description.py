import logging
from typing import Any, Dict, Optional

from openai import OpenAI

from herbabot.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


def generate_plant_description(plant_data: Dict[str, Any]) -> Optional[str]:
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured, skipping description generation")
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Extract plant information
        latin_name = plant_data.get("latin_name", "Unknown")
        common_name = plant_data.get("common_name", "")
        family = plant_data.get("family", "")
        existing_description = plant_data.get("description", "")

        # Build the prompt
        prompt = f"""Write a detailed and informative description for the plant {latin_name}"""

        if common_name:
            prompt += f" (commonly known as {common_name})"

        if family:
            prompt += f" from the {family} family"

        prompt += """.

The description should be:
- Educational and informative
- Suitable for a botanical herbarium entry
- 2 paragraphs maximum
- Include information about appearance, habitat, distribution, and interesting facts
- Written in a clear, accessible style
- Factually accurate"""

        if existing_description:
            prompt += f"\n\nExisting description from PlantNet: {existing_description}"
            prompt += "\n\nPlease expand on this information or provide a more comprehensive description."

        logger.info(f"Generating OpenAI description for {latin_name}")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a botanical expert writing informative plant descriptions for a herbarium collection. Provide accurate, educational content suitable for plant enthusiasts and researchers.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.7,
        )

        if response.choices and response.choices[0].message.content:
            description = response.choices[0].message.content.strip()
            logger.info(f"OpenAI description generated successfully for {latin_name}")
            return description
        else:
            logger.warning(f"OpenAI returned empty response for {latin_name}")
            return None

    except Exception as e:
        logger.error(f"Error generating OpenAI description for {latin_name}: {e}")
        return None
