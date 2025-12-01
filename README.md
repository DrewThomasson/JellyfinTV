# JellyfinTV

JellyfinTV simulates a linear TV experience using your existing Jellyfin library. Create virtual channels based on genres, studios, or tags, and the app will schedule programming that runs continuously in the background.

## Features

- **Virtual Channels**: Create channels from specific genres, years, studios, or tags.
- **Continuous Scheduling**: Content is scheduled 24/7. Tuning in at any time starts playback exactly where the "live" broadcast would be.
- **Auto-Refill**: Schedules are automatically topped up as you watch.
- **Direct Streaming**: Plays content directly from your Jellyfin server to your browser.

## Quick Start (Docker)

The easiest way to run JellyfinTV is with Docker.

1.  Ensure Docker and Docker Compose are installed.
2.  Run the application:
    ```bash
    docker-compose up -d
    ```
3.  Open your browser to `http://localhost:8000`.

## Manual Installation

If you prefer to run without Docker:

1.  **Prerequisites**: Python 3.11+
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Server**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
4.  Open `http://localhost:8000` in your browser.

## Usage

1.  **Connect**: Enter your Jellyfin Server URL, Username, and Password.
2.  **Create Channel**:
    -   Name your channel (e.g., "90s Action").
    -   Select filters (Genres, Years, Studios, Ratings).
    -   (Optional) Select specific shows to include.
3.  **Watch**: Click "Watch" to start streaming.
4.  **Manage**: View the upcoming schedule or delete channels from the dashboard.
