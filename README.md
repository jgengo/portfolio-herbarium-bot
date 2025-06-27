<div align="center">
    <img src='.github/docs/logo.png' alt="herbarium's logo" /><br />
    <h1 align="center">Herbarium Bot</h1>
    <sub><em>A timeless notebook of leaves and memories, lovingly pressed by curious hands.</em></sub>
</div>


<div align="center">
  <sub>Created by <a href="https://github.com/jgengo">Jordane Gengo</a></sub>
</div>

<br /><br />

🌿 **Automated Plant Documentation Bot**

A Telegram bot that automatically processes plant photos, extracts metadata, identifies species, and updates my portfolio's herbarium collection.

> [!NOTE]
> This bot is designed to work with my personal portfolio repository.

<br>

## Features

* 📸 **Image Processing** - Receives and processes plant photos via Telegram
* 📍 **Location Extraction** - Extracts GPS coordinates and location data from EXIF metadata
* 📅 **Date Detection** - Automatically captures when the photo was taken
* 🌱 **Plant Identification** - Integrates with Pl@ntNet or OpenAI for species identification
* 📝 **Template Generation** - Fills markdown templates with plant information
* 🔄 **Portfolio Integration** - Creates pull requests to update my herbarium collection
* 🤖 **Automated Workflow** - Streamlines the entire process from photo to documentation

## Tech Stack

* **Language:** Python 3.12+
* **Telegram API:** python-telegram-bot
* **Image Processing:** Pillow (PIL)
* **EXIF Extraction:** ExifRead
* **Plant Identification:** Pl@ntNet API / OpenAI Vision API
* **Git Operations:** GitPython
* **Markdown Processing:** Custom templates
* **Package Management:** uv

## Getting Started

### Prerequisites

* Python 3.12 or higher
* Telegram Bot Token (from [@BotFather](https://t.me/botfather))
* Pl@ntNet API key or OpenAI API key
* GitHub Personal Access Token (for portfolio integration)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jgengo/portfolio-herbarium-bot.git
   cd portfolio-herbarium-bot
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   # Telegram Bot
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   
   # Plant Identification
   PLANTNET_API_KEY=your_plantnet_api_key
   # or
   OPENAI_API_KEY=your_openai_api_key
   
   # GitHub Integration
   GITHUB_TOKEN=your_github_personal_access_token
   GITHUB_REPO=your_username/your_portfolio_repo
   
   # Optional: Default location for unidentified photos
   DEFAULT_LOCATION="Unknown Location"
   ```

4. **Run the bot:**
   ```bash
   uv run python main.py
   ```

## Usage

1. **Send a photo** of a plant to the Telegram bot (as file!)
2. **Wait for processing** - The bot will:
   - Extract location and date from EXIF data
   - Identify the plant species
   - Generate a markdown entry
   - Create a pull request to my portfolio
3. **Review and merge** the pull request to add the plant to my herbarium

## Project Structure

```
portfolio-herbarium-bot/
├── herbabot/            # Core bot code
│   ├── config.py        # Environment & config loader
│   ├── exif_utils.py    # EXIF metadata extraction
│   ├── handlers.py      # Telegram bot handlers
│   ├── plant_id.py      # Pl@ntNet identification service
│   └── main.py          # Bot entry point
├── templates/           # Markdown templates (welcome, entries, etc.)
├── tests/               # Test suite
├── pyproject.toml       # Project configuration
└── README.md            # <-- YOU ARE HERE!
```

## Configuration

### Plant Identification Services

This bot currently uses the Pl@ntNet API to identify plant species from images. The `herbabot.plant_id` module wraps Pl@ntNet v2 and provides:

- `identify_plant(image_path, organs=None)` → returns a dict with:
  - `latin_name`: scientific name
  - `common_name`: a common name (if available)
  - `description`: Wikipedia description (if available)
  - `score`: confidence score
  - `raw`: full API response

Authentication is via the `PLANTNET_API_KEY` environment variable.

To switch to OpenAI Vision for identification, set `OPENAI_API_KEY` and adjust the handler logic accordingly.

### Template Customization

Customize the markdown templates in the `templates/` directory:

- `bot_welcome.md`: Welcome message template for the Telegram bot
- `plant_entry.md`: Markdown template for new herbarium entries (create as needed)

### GitHub Integration

The bot automatically:
- Creates feature branches for new plant entries
- Generates descriptive commit messages
- Opens pull requests with plant information

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## About

Created by [Jordane Gengo](https://github.com/jgengo)

Because documenting nature should be as effortless as taking a photo.


