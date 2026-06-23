from __future__ import annotations

from pathlib import Path
import hashlib
import sqlite3


ROOT = Path.cwd()
DB_PATH = ROOT / "DB" / "pitwall.sqlite"
DOWNLOAD_DIR = ROOT / "download" / "cars"
OUT_PATH = ROOT / "tmp" / "file.txt"


def main() -> int:
    db_hashes = _load_db_hashes()
    results = []

    for path in sorted(DOWNLOAD_DIR.iterdir()):
        if not path.is_file():
            continue
        sha256 = _sha256(path)
        status = "verified" if sha256 in db_hashes else "failed"
        results.append((status, path.name, sha256, db_hashes.get(sha256)))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(_format_results(results), encoding="utf-8")

    verified = sum(1 for status, *_ in results if status == "verified")
    failed = len(results) - verified
    print(f"wrote {OUT_PATH}")
    print(f"{verified} verified {failed} failed")
    return 0 if failed == 0 else 1


def _load_db_hashes() -> dict[str, str]:
    connection = sqlite3.connect(DB_PATH)
    rows = connection.execute(
        """
        SELECT h.sha256, m.name
        FROM hashes h
        JOIN mods m ON m.id = h.mod_id
        """
    ).fetchall()
    connection.close()
    return {sha256.lower(): name for sha256, name in rows if sha256}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _format_results(results: list[tuple[str, str, str, str | None]]) -> str:
    lines = []
    for status, filename, sha256, mod_name in results:
        lines.append(f"{status}\t{sha256}\t{filename}\t{mod_name or ''}")
    return "\n".join(lines) + ("\n" if lines else "")


if __name__ == "__main__":
    raise SystemExit(main())
