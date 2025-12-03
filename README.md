# JellyfinTV
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Spaces-yellow?style=flat&logo=huggingface)](https://huggingface.co/spaces/drewThomasson/JellfinTV)
[![Docker Pulls](https://img.shields.io/docker/pulls/athomasson2/jellyfintv?style=flat&logo=docker&color=lightseagreen)](https://hub.docker.com/r/athomasson2/jellyfintv)

JellyfinTV simulates a linear TV experience using your existing Jellyfin library. Create virtual channels based on genres, studios, or tags, and the app will schedule programming that runs continuously in the background.

## Features

- **Virtual Channels**: Create channels from specific genres, years, studios, or tags.
- **Continuous Scheduling**: Content is scheduled 24/7. Tuning in at any time starts playback exactly where the "live" broadcast would be.
- **Auto-Refill**: Schedules are automatically topped up as you watch.
- **Auto-Ads**: Put ad files in the respective year folder in `./ads`
- **Direct Streaming**: Plays content directly from your Jellyfin server to your browser.

<p align="center">
<img src="https://github.com/user-attachments/assets/68b37b7c-0777-4f14-aa7c-4904f97ae641" width="32%" alt="Detailed Screenshot 1" />
<img src="https://github.com/user-attachments/assets/6a8bff3d-5bed-4ba4-9106-ca490a74f73c" width="32%" alt="Detailed Screenshot 2" />
<img src="https://github.com/user-attachments/assets/f45852de-449b-429f-bbe4-f254b5b643dd" width="32%" alt="Detailed Screenshot 3" />
</p>

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
