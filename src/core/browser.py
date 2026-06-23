from __future__ import annotations

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def attach_to_chrome(debugger_address: str) -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", debugger_address)
    return webdriver.Chrome(options=options)


def wait_for_element(driver: webdriver.Chrome, locator: tuple[str, str], timeout: int):
    try:
        return WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))
    except TimeoutException:
        return None


def wait_for_clickable(driver: webdriver.Chrome, locator: tuple[str, str], timeout: int):
    try:
        return WebDriverWait(driver, timeout).until(ec.element_to_be_clickable(locator))
    except TimeoutException:
        return None


def wait_for_url_part(driver: webdriver.Chrome, fragment: str, timeout: int) -> bool:
    try:
        WebDriverWait(driver, timeout).until(ec.url_contains(fragment))
        return True
    except TimeoutException:
        return False

