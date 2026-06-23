from __future__ import annotations

from urllib.parse import urljoin

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from core.browser import wait_for_element
from scrape.models import ModEntry


BASE_URL = "https://www.assettoworld.com"
MOD_CARD_SELECTOR = "div.mod-card"


def listing_url(type_segment: str, page: int, sort_segment: str) -> str:
    sort = "" if sort_segment == "recent" else f"/{sort_segment}"
    return f"{BASE_URL}/{type_segment}/{page}{sort}"


def scrape_listing_page(driver, type_segment: str, page: int, sort_segment: str, timeout: int) -> list[ModEntry]:
    url = listing_url(type_segment, page, sort_segment)
    print(f"[list] {url}")
    driver.get(url)
    if wait_for_element(driver, (By.CSS_SELECTOR, MOD_CARD_SELECTOR), timeout) is None:
        return []

    entries = []
    for card in driver.find_elements(By.CSS_SELECTOR, MOD_CARD_SELECTOR):
        entry = parse_mod_card(card)
        if entry:
            entries.append(entry)
    return entries


def parse_mod_card(card) -> ModEntry | None:
    try:
        link = card.find_element(By.CSS_SELECTOR, "a[href]")
        href = link.get_attribute("href")
        name = link.get_attribute("title") or link.text
    except (NoSuchElementException, StaleElementReferenceException):
        return None

    if not href:
        return None
    return ModEntry(name=(name or "").strip(), page_url=urljoin(BASE_URL, href))

