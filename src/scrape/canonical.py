from __future__ import annotations

import re

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
VIRUSTOTAL_LINK_SELECTOR = "a[href*='virustotal.com/gui/file/']"


def scrape_canonical_sha256(driver, timeout: int) -> str | None:
    try:
        href = driver.find_element(By.CSS_SELECTOR, VIRUSTOTAL_LINK_SELECTOR).get_attribute("href")
    except NoSuchElementException:
        return None

    if not href:
        return None

    direct = _sha_from_text(href)
    if direct:
        return direct

    current_handle = driver.current_window_handle
    try:
        driver.switch_to.new_window("tab")
        new_handle = driver.current_window_handle
        driver.switch_to.window(new_handle)
        driver.get(href)
        return _wait_for_sha_in_url(driver, timeout)
    finally:
        if driver.current_window_handle != current_handle:
            driver.close()
        driver.switch_to.window(current_handle)


def _wait_for_sha_in_url(driver, timeout: int) -> str | None:
    try:
        WebDriverWait(driver, timeout).until(lambda active_driver: _sha_from_text(active_driver.current_url))
    except TimeoutException:
        return None
    return _sha_from_text(driver.current_url)


def _sha_from_text(value: str) -> str | None:
    match = SHA256_RE.search(value)
    return match.group(0).lower() if match else None
