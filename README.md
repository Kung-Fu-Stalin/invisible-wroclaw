# Invisible Wrocław Bot

## Description

This project is a Telegram bot designed to showcase photos of Wrocław. It allows administrators to update the photo collection from a Google Drive archive and publish them to subscribed users, and remove all posts if needed

<img src="docs/admin_panel.jpg" alt="Tour guide panel" width="300">

<p>And participants panel:</p>

<div style="display: flex; gap: 10px; align-items: flex-start;">
  <img src="docs/user_photos.png" alt="Tourist panel" width="300">
  <img src="docs/user_cleanup.png" alt="Tourist panel cleaned up" width="300">
</div>


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

## Running the Tests

```bash
uv run pytest
```

The tests never touch Telegram, Google Drive or your `bot.db`: they run the
handlers against a fake Bot API and a temporary database and photo folder.

## Glossary

*   **Guide** (admin): runs the tour; listed in `admins` by Telegram username
    or numeric id. Only guides can use the control panel.
*   **Tourist** (subscriber): anyone else who sent `/start`; receives the
    published photos.
*   **Photo library**: the `.jpg`, `.jpeg` and `.png` files in `images_dir`.
    Numbered photos come first, in number order, then the rest by name.
*   **Gallery**: a guide's message with ⬅️ / ➡️ / ✅ buttons. Every gallery
    message remembers which photo it shows.
*   **Publish**: send the photo a gallery shows to every tourist.
*   **Refresh**: replace the library with the photos of the shared Google
    Drive folder. The new set is built in a hidden staging folder and replaces
    the library only when download, extraction and resizing all succeeded.
*   **Finish the tour**: say goodbye to every tourist, delete the photos
    published to them and unsubscribe everyone.
