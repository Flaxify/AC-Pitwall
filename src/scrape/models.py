from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModEntry:
    name: str
    page_url: str


@dataclass(frozen=True)
class ModMetadata:
    filesize: str | None = None
    brand: str | None = None
    class_name: str | None = None
    version: str | None = None
    year: str | None = None
    top_speed: str | None = None
    power: str | None = None
    torque: str | None = None
    weight: str | None = None
    pw_ratio: str | None = None
    rating: str | None = None
    credits: str | None = None
    tags: str | None = None


@dataclass(frozen=True)
class ModDetails:
    metadata: ModMetadata
    download_links: list[str]
    canonical_sha256: str | None = None
