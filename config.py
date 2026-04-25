"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _csv_env(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _path_env(name: str, default: str) -> Path:
    path = Path(os.getenv(name, default))
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


@dataclass(frozen=True)
class Settings:
    """Typed settings for the scraper, filter, database, and integrations."""

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    scrape_interval_seconds: int = _int_env("SCRAPE_INTERVAL_SECONDS", 600)
    database_path: Path = _path_env("DATABASE_PATH", "data/listings.sqlite3")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    enable_olx: bool = _bool_env("ENABLE_OLX", True)
    olx_search_url_template: str = os.getenv(
        "OLX_SEARCH_URL_TEMPLATE",
        "https://www.olx.in/chennai_g4059161/q-{query_slug}",
    )
    olx_search_queries: list[str] = None  # type: ignore[assignment]
    olx_request_delay_seconds: float = _float_env("OLX_REQUEST_DELAY_SECONDS", 2.0)
    request_timeout_seconds: int = _int_env("REQUEST_TIMEOUT_SECONDS", 20)
    user_agent: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )

    enable_reddit: bool = _bool_env("ENABLE_REDDIT", True)
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "pc-server-scrap-finder/1.0")
    reddit_subreddits: list[str] = None  # type: ignore[assignment]
    reddit_search_queries: list[str] = None  # type: ignore[assignment]
    reddit_limit_per_query: int = _int_env("REDDIT_LIMIT_PER_QUERY", 25)
    reddit_request_delay_seconds: float = _float_env("REDDIT_REQUEST_DELAY_SECONDS", 2.0)

    enable_telegram_scraper: bool = _bool_env("ENABLE_TELEGRAM_SCRAPER", True)
    telethon_api_id: int = _int_env("TELETHON_API_ID", 0)
    telethon_api_hash: str = os.getenv("TELETHON_API_HASH", "")
    telethon_session_name: str = os.getenv("TELETHON_SESSION_NAME", "pc_finder_telegram")
    telethon_phone: str = os.getenv("TELETHON_PHONE", "")
    telegram_scraper_bot_token: str = os.getenv("TELEGRAM_SCRAPER_BOT_TOKEN", "")
    telegram_channels: list[str] = None  # type: ignore[assignment]
    telegram_messages_per_channel: int = _int_env("TELEGRAM_MESSAGES_PER_CHANNEL", 50)

    component_keywords: list[str] = None  # type: ignore[assignment]
    condition_keywords: list[str] = None  # type: ignore[assignment]
    location_keywords: list[str] = None  # type: ignore[assignment]
    excluded_keywords: list[str] = None  # type: ignore[assignment]
    enterprise_network_keywords: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "olx_search_queries",
            _csv_env(
                "OLX_SEARCH_QUERIES",
                "free pc,dead server,scrap motherboard,free server,dead motherboard,"
                "scrap ram,broken gpu,free computer parts",
            ),
        )
        object.__setattr__(
            self,
            "reddit_subreddits",
            _csv_env("REDDIT_SUBREDDITS", "chennai,india,homelab,hardware"),
        )
        object.__setattr__(
            self,
            "reddit_search_queries",
            _csv_env(
                "REDDIT_SEARCH_QUERIES",
                "free pc,dead server,scrap motherboard,free server,broken gpu,"
                "for parts server,not working ram",
            ),
        )
        object.__setattr__(self, "telegram_channels", _csv_env("TELEGRAM_CHANNELS", ""))
        object.__setattr__(
            self,
            "component_keywords",
            _csv_env(
                "COMPONENT_KEYWORDS",
                "cpu,processor,motherboard,ram,memory,gpu,graphics,graphics card,"
                "psu,smps,power supply,hdd,hard disk,ssd,server,rack,raid,switch,"
                "router,blade,ecc",
            ),
        )
        object.__setattr__(
            self,
            "condition_keywords",
            _csv_env("CONDITION_KEYWORDS", "free,scrap,dead,not working,not-working,broken,for parts"),
        )
        object.__setattr__(
            self,
            "location_keywords",
            _csv_env("LOCATION_KEYWORDS", "chennai,tamil nadu,tn"),
        )
        object.__setattr__(
            self,
            "excluded_keywords",
            _csv_env(
                "EXCLUDED_KEYWORDS",
                "tv,television,mobile,phone,smartphone,charger,appliance,speaker,"
                "fridge,washing machine,microwave,tablet,nintendo,console",
            ),
        )
        object.__setattr__(
            self,
            "enterprise_network_keywords",
            _csv_env(
                "ENTERPRISE_NETWORK_KEYWORDS",
                "server,enterprise,rack,cisco,juniper,mikrotik,ubiquiti,omada,"
                "managed,prosafe,24 port,48 port,10g,sfp,dell,hp,hpe",
            ),
        )


settings = Settings()
