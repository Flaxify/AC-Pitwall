from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from scrape.models import ModDetails, ModEntry


SCHEMA = """
CREATE TABLE IF NOT EXISTS mods (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT,
    type        TEXT,
    page_url    TEXT UNIQUE,
    scraped_at  TEXT
);

CREATE TABLE IF NOT EXISTS mods_metadata (
    mod_id      INTEGER PRIMARY KEY,
    filesize    TEXT,
    brand       TEXT,
    class       TEXT,
    version     TEXT,
    year        TEXT,
    top_speed   TEXT,
    power       TEXT,
    torque      TEXT,
    weight      TEXT,
    pw_ratio    TEXT,
    rating      TEXT,
    credits     TEXT,
    tags        TEXT,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mods_download_links (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    mod_id      INTEGER NOT NULL,
    url         TEXT NOT NULL,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE (mod_id, url)
);

CREATE INDEX IF NOT EXISTS idx_dl_mod_id ON mods_download_links(mod_id);

CREATE TABLE IF NOT EXISTS hashes (
    mod_id      INTEGER PRIMARY KEY,
    sha256      TEXT,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS files (
    mod_id      INTEGER PRIMARY KEY,
    file_path   TEXT,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS verification (
    mod_id          INTEGER PRIMARY KEY,
    sha_correct     INTEGER,
    ready_to_import INTEGER,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.executescript(SCHEMA)
    connection.commit()
    return connection


def load_done_urls(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT page_url FROM mods").fetchall()
    return {row[0] for row in rows if row[0]}


def persist_mod(
    connection: sqlite3.Connection,
    mod: ModEntry,
    details: ModDetails,
    db_type: str,
) -> int:
    scraped_at = datetime.now(timezone.utc).isoformat()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO mods (name, type, page_url, scraped_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(page_url) DO UPDATE SET
            name = excluded.name,
            type = excluded.type,
            scraped_at = excluded.scraped_at
        """,
        (mod.name, db_type, mod.page_url, scraped_at),
    )
    mod_id = cursor.execute(
        "SELECT id FROM mods WHERE page_url = ?",
        (mod.page_url,),
    ).fetchone()[0]

    metadata = details.metadata
    cursor.execute(
        """
        INSERT INTO mods_metadata (
            mod_id, filesize, brand, class, version, year, top_speed, power,
            torque, weight, pw_ratio, rating, credits, tags
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(mod_id) DO UPDATE SET
            filesize = excluded.filesize,
            brand = excluded.brand,
            class = excluded.class,
            version = excluded.version,
            year = excluded.year,
            top_speed = excluded.top_speed,
            power = excluded.power,
            torque = excluded.torque,
            weight = excluded.weight,
            pw_ratio = excluded.pw_ratio,
            rating = excluded.rating,
            credits = excluded.credits,
            tags = excluded.tags
        """,
        (
            mod_id,
            metadata.filesize,
            metadata.brand,
            metadata.class_name,
            metadata.version,
            metadata.year,
            metadata.top_speed,
            metadata.power,
            metadata.torque,
            metadata.weight,
            metadata.pw_ratio,
            metadata.rating,
            metadata.credits,
            metadata.tags,
        ),
    )

    cursor.executemany(
        "INSERT OR IGNORE INTO mods_download_links (mod_id, url) VALUES (?, ?)",
        [(mod_id, link) for link in details.download_links],
    )

    if details.canonical_sha256:
        cursor.execute(
            """
            INSERT INTO hashes (mod_id, sha256)
            VALUES (?, ?)
            ON CONFLICT(mod_id) DO UPDATE SET sha256 = excluded.sha256
            """,
            (mod_id, details.canonical_sha256),
        )

    connection.commit()
    return mod_id
