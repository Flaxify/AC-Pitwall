from __future__ import annotations

import time

from selenium.webdriver.remote.webdriver import WebDriver

from core import db
from core.config import AppConfig, ScrapeConfig
from scrape.canonical import scrape_canonical_sha256
from scrape.links import scrape_download_links
from scrape.listing import scrape_listing_page
from scrape.metadata import scrape_metadata
from scrape.models import ModDetails, ModEntry


def run_scrape(driver: WebDriver, connection, config: AppConfig) -> None:
    done_urls = db.load_done_urls(connection)
    scrape = config.scrape
    total_seen = 0
    total_saved = 0

    print(
        f"[plan] type={scrape.type} sort={scrape.sort} "
        f"pages={scrape.start_page}-{scrape.end_page}"
    )

    for page in range(scrape.start_page, scrape.end_page + 1):
        entries = scrape_listing_page(
            driver,
            type_segment=scrape.type,
            page=page,
            sort_segment=scrape.sort,
            timeout=config.browser.wait_timeout,
        )
        if not entries:
            print(f"[list] no entries on page {page}; stopping")
            break

        for entry in entries:
            total_seen += 1
            if entry.page_url in done_urls:
                print(f"[skip] {entry.name}")
                continue
            if scrape_one_mod(driver, connection, entry, scrape, config.browser.wait_timeout):
                total_saved += 1
                done_urls.add(entry.page_url)
            time.sleep(scrape.page_delay)

    print(f"[done] seen={total_seen} saved={total_saved}")


def scrape_one_mod(
    driver: WebDriver,
    connection,
    entry: ModEntry,
    scrape: ScrapeConfig,
    timeout: int,
) -> bool:
    print(f"[mod] {entry.name} -> {entry.page_url}")
    try:
        driver.get(entry.page_url)
        metadata = scrape_metadata(driver)
        canonical_sha256 = scrape_canonical_sha256(driver, timeout)
        links = scrape_download_links(driver, timeout)
        details = ModDetails(
            metadata=metadata,
            download_links=links,
            canonical_sha256=canonical_sha256,
        )
        db.persist_mod(connection, entry, details, scrape.db_type)
        sha_status = "sha=yes" if canonical_sha256 else "sha=no"
        print(f"[saved] links={len(links)} {sha_status}")
        return True
    except Exception as error:  # noqa: BLE001 - fail soft per mod in POC scraper
        print(f"[error] {entry.page_url}: {type(error).__name__}: {error}")
        return False
