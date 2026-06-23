from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


VALID_TYPES = ("cars", "tracks")
VALID_SORTS = ("recent", "downloads", "rating")


@dataclass(frozen=True)
class BrowserConfig:
    debugger_address: str
    wait_timeout: int


@dataclass(frozen=True)
class ScrapeConfig:
    type: str
    sort: str
    start_page: int
    end_page: int
    page_delay: float

    @property
    def db_type(self) -> str:
        return {"cars": "car", "tracks": "track"}[self.type]


@dataclass(frozen=True)
class PathsConfig:
    root: Path
    db: Path
    logs: Path


@dataclass(frozen=True)
class AppConfig:
    browser: BrowserConfig
    scrape: ScrapeConfig
    paths: PathsConfig


DEFAULT_CONFIG = {
    "browser": {
        "debugger_address": "localhost:9222",
        "wait_timeout": 15,
    },
    "scrape": {
        "type": "cars",
        "sort": "recent",
        "start_page": 1,
        "end_page": 1,
        "page_delay": 1.5,
    },
    "paths": {
        "db": "DB/pitwall.sqlite",
        "logs": "logs",
    },
}


def load_config(config_path: str | Path = "config.toml") -> AppConfig:
    path = Path(config_path)
    if not path.is_absolute():
        path = Path.cwd() / path

    data = DEFAULT_CONFIG | {}
    if path.exists():
        loaded = tomllib.loads(path.read_text(encoding="utf-8"))
        data = _deep_merge(DEFAULT_CONFIG, loaded)

    root = path.parent if path.exists() else Path.cwd()
    browser = data["browser"]
    scrape = data["scrape"]
    paths = data["paths"]

    scrape_config = ScrapeConfig(
        type=_require_choice(scrape["type"], VALID_TYPES, "scrape.type"),
        sort=_require_choice(scrape["sort"], VALID_SORTS, "scrape.sort"),
        start_page=int(scrape["start_page"]),
        end_page=int(scrape["end_page"]),
        page_delay=float(scrape["page_delay"]),
    )
    if scrape_config.start_page < 1 or scrape_config.end_page < scrape_config.start_page:
        raise ValueError("scrape page range must be positive and ordered")

    return AppConfig(
        browser=BrowserConfig(
            debugger_address=str(browser["debugger_address"]),
            wait_timeout=int(browser["wait_timeout"]),
        ),
        scrape=scrape_config,
        paths=PathsConfig(
            root=root,
            db=_resolve(root, paths["db"]),
            logs=_resolve(root, paths["logs"]),
        ),
    )


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _require_choice(value: str, choices: tuple[str, ...], name: str) -> str:
    if value not in choices:
        raise ValueError(f"{name} must be one of {', '.join(choices)}")
    return value


def _deep_merge(base: dict, override: dict) -> dict:
    merged = {key: value.copy() if isinstance(value, dict) else value for key, value in base.items()}
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged

