# PC / Server Scrap Finder

Continuously monitors OLX, Reddit, and Telegram channels for free, scrap, dead, or not-working desktop PC and server hardware.

## Project Structure

```text
PC Finder/
├── .env.example
├── .dockerignore
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.py
├── db.py
├── filter.py
├── main.py
├── models.py
├── notifier.py
└── sources/
    ├── __init__.py
    ├── base.py
    ├── olx.py
    ├── reddit.py
    └── telegram_scraper.py
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `TELETHON_API_ID`
- `TELETHON_API_HASH`
- `TELEGRAM_CHANNELS`

## Run

```powershell
python main.py
```

The scraper runs every 10 minutes by default and stores seen listings in `data/listings.sqlite3`.

## Docker On Ubuntu Server

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"
newgrp docker
```

Copy `.env.example` to `.env`, fill the API keys, then run:

```bash
docker compose up -d --build
docker compose logs -f pc-finder
```

Scale local workers:

```bash
docker compose up -d --scale pc-finder=3
```

All replicas share the same Docker volume and SQLite database. SQLite runs in WAL mode, so `link` remains the primary-key dedupe guard across replicas.

For scaled mode, prefer disabling `ENABLE_TELEGRAM_SCRAPER` or using `TELEGRAM_SCRAPER_BOT_TOKEN`; multiple user-session Telethon workers should not share one session file.

Stop:

```bash
docker compose down
```

## Add A New Source

Create a new file in `sources/`, subclass `BaseSource`, return `Listing` objects from `fetch()`, then register it in `build_sources()` inside `main.py`.
