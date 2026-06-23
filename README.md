# pitwall

Automated, verified mod fetcher for **Assetto Corsa**, sourced from
[assettoworld.com](https://www.assettoworld.com) — one of the community's
primary, high-quality mod indexes.

`pitwall` automates exactly what a human with a browser and keyboard could do:
browse the listings, record where each mod lives, download it from the fastest
available host, and **cryptographically verify** the file before it ever
touches your game.

> **Why?** Pulling the top-rated cars/tracks from assettoworld gives you a
> curated, high-quality library without manually clicking through hundreds of
> pages and shady file hosts. `pitwall` does it reliably and proves every file
> is intact via SHA-256.

---

## Table of contents
- [Concept](#concept)
- [Project phases](#project-phases)
- [Quick start (OOBE)](#quick-start-oobe)
- [Layout](#layout)
- [Database schema](#database-schema)
- [Configuration](#configuration)
- [Phase reference](#phase-reference)
- [Design principles](#design-principles)
- [Roadmap / TBD](#roadmap--tbd)

---

## Concept

assettoworld lists mods on a clean, scrapable site but the actual files live on
third-party hosts (modsfire, modslocker, Google Drive, MEGA). Those hosts are
"second-hand" and untrusted — a downloaded archive could be incomplete or
tainted.

`pitwall` solves this with a **database-driven pipeline**:

1. **Map** every mod's assettoworld page → its download links + metadata (DB).
2. **Download** the file from the best-available host.
3. **Verify** the file's SHA-256 against the canonical hash published via
   assettoworld's VirusTotal scan link — *before* trusting it.

The same verification logic lets you **adopt an existing untrusted mod library**:
if a local file's hash matches the canonical hash, it becomes trusted without
re-downloading.

---

## Project phases

The pipeline runs in three independent, interlocking phases. Each phase reads
and writes the shared SQLite database, so phases can be run, re-run, and resumed
independently.

### Phase 1 — Scrape
Populate the database from assettoworld.
- **Listings:** walk `cars`/`tracks` pages (sortable: recent, downloads, rating)
  → `mods`.
- **Links:** scrape each mod's download links → `mods_download_links`.
- **Metadata:** scrape brand, power, torque, weight, top speed, year, class,
  version, credits, tags, filesize → `mods_metadata`.

Everything is in the DOM (no JS-gated data), so scraping is reliable.

### Phase 2 — Download
Fetch the actual mod files.
- All download links for a mod resolve to the **same file**, so the downloader
  tries hosts in **bandwidth-preference order** and stops at the first success.
- Each host has its own resolver module (the "generate download link" DOM
  dance differs per host).
- Downloaded files land in `download/cars/` or `download/tracks/`; path is
  recorded in `files`.

### Phase 3 — Verify
Prove every file is the genuine, intact mod.
1. **Canonical hash:** follow assettoworld's VirusTotal scan link through its
   redirect chain; the **final URL contains the SHA-256**. Stored in `hashes`.
2. **Checksum verify:** hash the downloaded file, compare to canonical →
   `verification.sha_correct`.
3. **Structure verify:** inspect the archive for expected Assetto Corsa mod
   layout → `verification.ready_to_import`.

**Adopt-existing workflow:** point Phase 3 at an existing untrusted mod
collection; any file whose hash matches a canonical hash is promoted to trusted
without re-downloading.

---

## Quick start (OOBE)

Clone and run the launcher. It sets up a virtualenv, installs dependencies,
checks for a debug-enabled Chromium, initializes the database, and runs the
requested phase.

**Linux / WSL / macOS:**
```bash
git clone https://github.com/Flaxify/AC-Pitwall.git pitwall
cd pitwall
./start.sh scrape --type cars --sort rating --start 1 --end 2
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/Flaxify/AC-Pitwall.git pitwall
cd pitwall
.\start.ps1 scrape --type cars --sort rating --start 1 --end 2
```

### Prerequisite: debug-enabled Chromium
Phase 1 & 2 attach to a running Chromium with remote debugging:
```bash
chromium --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```
The launcher warns if this endpoint is not reachable.

---

## Layout

```
pitwall/
├── start.sh              # Linux/WSL/macOS launcher
├── start.ps1             # Windows launcher
├── config.toml           # all tunables: page ranges, hosts, paths, rate limits
├── pyproject.toml        # dependencies + console entry point
├── src/
│   ├── core/
│   │   ├── db.py         # connection, PRAGMA foreign_keys, schema (shared)
│   │   ├── config.py     # loads config.toml
│   │   └── browser.py    # attach_to_chrome + wait helpers (shared)
│   ├── scrape/
│   │   ├── listing.py    # listing page → mod entries
│   │   ├── links.py      # mod page → download links
│   │   └── metadata.py   # mod page → brand/power/tags/filesize/…
│   ├── download/
│   │   ├── manager.py    # picks best host, retries, records files row
│   │   └── hosts/        # one resolver per host
│   │       ├── modsfire.py
│   │       ├── modslocker.py
│   │       ├── gdrive.py
│   │       └── mega.py
│   ├── verify/
│   │   ├── canonical.py  # VT redirect chain → SHA-256 → hashes table
│   │   ├── checksum.py   # local file SHA vs canonical → sha_correct
│   │   └── structure.py  # archive layout check → ready_to_import
│   └── cli.py            # `pitwall scrape|download|verify|adopt`
├── DB/
│   └── pitwall.sqlite
├── download/
│   ├── cars/
│   └── tracks/
└── logs/
```

---

## Database schema

SQLite. `mods.id` is the stable anchor every other table references.
`PRAGMA foreign_keys = ON` is enforced on every connection (see `core/db.py`).

```sql
-- Core entity
CREATE TABLE mods (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT,
    type        TEXT,                 -- 'car' | 'track'
    page_url    TEXT UNIQUE,          -- dedup / resume anchor
    scraped_at  TEXT
);

-- 1:1 extension — FK is the PK
CREATE TABLE mods_metadata (
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
    tags        TEXT,                 -- comma-separated
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);

-- 1:many — own id PK, UNIQUE dedups re-scrapes
CREATE TABLE mods_download_links (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    mod_id      INTEGER NOT NULL,
    url         TEXT NOT NULL,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE (mod_id, url)
);
CREATE INDEX idx_dl_mod_id ON mods_download_links(mod_id);

-- Canonical hash (1:1 — all links = same file = one SHA)
CREATE TABLE hashes (
    mod_id      INTEGER PRIMARY KEY,
    sha256      TEXT,                 -- from VirusTotal final URL
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);

-- Downloaded / adopted file location (1:1)
CREATE TABLE files (
    mod_id      INTEGER PRIMARY KEY,
    file_path   TEXT,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);

-- Verification state (1:1)
CREATE TABLE verification (
    mod_id          INTEGER PRIMARY KEY,
    sha_correct     INTEGER,          -- bool: file SHA == canonical
    ready_to_import INTEGER,          -- bool: archive structure valid
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE
);
```

**Schema is extensible:** new enrichment (ratings history, screenshots, authors)
attaches as a new table FK'd to `mods.id` — no migration of existing tables.

---

## Configuration

All tunables live in `config.toml`:

```toml
[browser]
debugger_address = "127.0.0.1:9222"
wait_timeout     = 15

[scrape]
type        = "cars"      # cars | tracks
sort        = "recent"    # recent | downloads | rating
start_page  = 1
end_page    = 10
page_delay  = 1.5

[download]
host_priority = ["modsfire", "modslocker", "gdrive", "mega"]
out_dir       = "download"

[paths]
db   = "DB/pitwall.sqlite"
logs = "logs"
```

---

## Phase reference

```bash
# Phase 1 — scrape listings, links, metadata
pitwall scrape --type cars  --sort rating --start 1 --end 10
pitwall scrape --type tracks --sort downloads

# Phase 2 — download files for mods in the DB
pitwall download --type cars

# Phase 3 — fetch canonical hashes + verify downloaded files
pitwall verify

# Adopt an existing untrusted library (hash-match → trusted, no re-download)
pitwall adopt /path/to/existing/mods
```

(Or just run `./start.sh` and use the menu.)

---

## Design principles

- **Modular, not monolithic.** Each phase and each host is its own module behind
  a shared core (`db`, `config`, `browser`). Adding a host = one file in
  `download/hosts/`.
- **Resume-safe.** `page_url UNIQUE` + per-record commits mean any phase can be
  killed and re-run without dupes or lost progress.
- **DB as source of truth.** Phases communicate only through the database, so
  they're independently runnable and testable.
- **Fail soft.** Per-mod errors are logged and skipped; one bad mod never aborts
  a run.
- **Trust through verification.** Nothing is "ready to import" until its SHA-256
  matches the canonical hash and its archive structure checks out.

---

## Roadmap / TBD

- [ ] **Paid-plan direct download** — assettoworld's premium direct-download path
  is JS-gated; the download layer is host-modular specifically to slot this in
  later as a preferred high-bandwidth source.
- [ ] Automatic import into the Assetto Corsa `content/` directory.
- [ ] Parallel downloads with global rate limiting.
