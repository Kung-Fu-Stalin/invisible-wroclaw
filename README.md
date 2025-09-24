# Invisible Wrocław Bot

## Description

This project is a Telegram bot designed to showcase photos of Wrocław. It allows administrators to update the photo collection from a Google Drive archive and publish them to subscribed users.

## Prerequisites

- Python 3.12
- [uv](https://github.com/astral-sh/uv) package manager
- Telegram Bot token (obtained from BotFather)

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd invisible-wroclaw
    ```

2.  **Install dependencies:**

    Using uv:

    ```bash
    uv sync
    source .venv/bin/activate
    ```

    Alternatively, using pip:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r .
    ```

3.  **Configuration:**

    *   Create a `.env` file in the project root directory.
    *   Add your Telegram bot token to the `.env` file:

        ```
        TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
        ```

    *   Configure `settings.yaml` file:

        *   `images_archive`: Google Drive folder URL containing the images archive.
        *   `images_name`: Name of the images archive file.
        *   `images_dir`: Directory to store extracted images.
        *   `database`: Path to the SQLite database file.
        *   `admins`: List of Telegram usernames or user IDs with administrative privileges.

## Running the Bot

1.  **Start the bot:**

    Open Telegram and search for your bot.
    Send the /start command to the bot.
    Admin Commands:

    Admins can use the control panel to:
    Refresh photos from Google Drive.
    Control and publish photos to users.
    Purge all users and messages.
    Project Structure

```bash
python [main.py]
```
```
.
├── .env                      # Environment variables (Telegram token)
├── .gitignore                # Specifies intentionally untracked files that Git should ignore
├── .pre-commit-config.yaml   # Configuration for pre-commit hooks
├── .python-version           # Specifies the Python version for the project
├── bot                       # Telegram bot related files
│   ├── [__init__.py]
│   ├── [handlers.py]         # Bot command handlers
│   ├── [keyboard.py]         # Inline keyboard definitions
│   └── [photos.py]           # Photo publishing logic
├── [main.py]                 # Main application entry point
├── [pyproject.toml]          # Project metadata and dependencies
├── [README.md]               # Project documentation
├── resources                 # Additional resources
│   └── [ui.json]             # User interface strings
├── [settings.yaml]           # Project settings
├── utils                     # Utility modules
│   ├── [__init__.py]
│   ├── [config.py]           # Configuration management
│   ├── [db_manager.py]       # Database management
│   ├── [gdrive.py]           # Google Drive interaction
│   ├── [images_manager.py]   # Image file management
│   ├── [logger.py]           # Logging utility
│   └── [ui.py]               # UI strings management
└── [uv.lock]                 # Dependency lock file for uv
```
