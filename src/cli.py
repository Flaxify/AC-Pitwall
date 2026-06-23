from __future__ import annotations

import argparse
import sys

from core.browser import attach_to_chrome
from core.config import VALID_SORTS, VALID_TYPES, load_config
from core.db import connect
from scrape.runner import run_scrape


def main() -> int:
    _prefer_utf8_stdio()

    parser = argparse.ArgumentParser(prog="pitwall")
    parser.add_argument("--config", default="config.toml")
    subcommands = parser.add_subparsers(dest="command", required=True)

    scrape = subcommands.add_parser("scrape", help="scrape AssettoWorld metadata and links")
    scrape.add_argument("--type", choices=VALID_TYPES)
    scrape.add_argument("--sort", choices=VALID_SORTS)
    scrape.add_argument("--start", type=int)
    scrape.add_argument("--end", type=int)

    subcommands.add_parser("download", help="download phase placeholder")
    subcommands.add_parser("verify", help="verify phase placeholder")
    adopt = subcommands.add_parser("adopt", help="adopt phase placeholder")
    adopt.add_argument("path")

    args = parser.parse_args()
    config = load_config(args.config)

    if args.command == "scrape":
        config = _apply_scrape_overrides(config, args)
        driver = attach_to_chrome(config.browser.debugger_address)
        connection = connect(config.paths.db)
        try:
            run_scrape(driver, connection, config)
        finally:
            connection.close()
        return 0

    raise NotImplementedError(f"{args.command} is not implemented yet")


def _apply_scrape_overrides(config, args):
    scrape = config.scrape
    values = {
        "type": args.type or scrape.type,
        "sort": args.sort or scrape.sort,
        "start_page": args.start or scrape.start_page,
        "end_page": args.end or scrape.end_page,
        "page_delay": scrape.page_delay,
    }
    return config.__class__(
        browser=config.browser,
        scrape=scrape.__class__(**values),
        paths=config.paths,
    )


def _prefer_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    raise SystemExit(main())
