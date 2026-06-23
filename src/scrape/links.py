from __future__ import annotations

from urllib.parse import urljoin

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from core.browser import wait_for_clickable, wait_for_element, wait_for_url_part
from scrape.listing import BASE_URL


DOWNLOAD_BUTTON_XPATH = "//button[.//i[contains(@class,'fa-download')]]"
DOWNLOAD_LINK_SELECTOR = "div.download-buttons a[href]"


def scrape_download_links(driver, timeout: int) -> list[str]:
    button = wait_for_clickable(driver, (By.XPATH, DOWNLOAD_BUTTON_XPATH), timeout)
    if button is None:
        return []

    driver.execute_script("arguments[0].click();", button)
    wait_for_url_part(driver, "/download", timeout)

    if wait_for_element(driver, (By.CSS_SELECTOR, DOWNLOAD_LINK_SELECTOR), timeout) is None:
        return []

    links = []
    for anchor in driver.find_elements(By.CSS_SELECTOR, DOWNLOAD_LINK_SELECTOR):
        href = _href(anchor)
        if href:
            absolute = urljoin(BASE_URL, href)
            if absolute not in links:
                links.append(absolute)
    return links


def _href(anchor) -> str | None:
    try:
        return anchor.get_attribute("href")
    except StaleElementReferenceException:
        return None

