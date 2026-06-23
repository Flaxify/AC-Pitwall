from __future__ import annotations

import re
import unicodedata

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from scrape.models import ModMetadata


ARCHIVE_SIZE_XPATH = (
    "//div[contains(@class,'file-meta')]"
    "[.//i[contains(@class,'fa-file-archive')]]"
)

LABEL_TO_FIELD = {
    "Brand": "brand",
    "Class": "class_name",
    "Version": "version",
    "Top Speed": "top_speed",
    "Year": "year",
    "Power": "power",
    "Torque": "torque",
    "Weight": "weight",
    "PW Ratio": "pw_ratio",
    "Rating": "rating",
    "Credits": "credits",
    "Tags": "tags",
}
LABEL_PATTERN = "|".join(re.escape(label) for label in LABEL_TO_FIELD)


def scrape_metadata(driver) -> ModMetadata:
    data = _generic_metadata_from_dom(driver)
    filesize = _file_size(driver)
    if filesize:
        data["filesize"] = filesize
    return ModMetadata(**data)


def _file_size(driver) -> str | None:
    try:
        text = driver.find_element(By.XPATH, ARCHIVE_SIZE_XPATH).text.strip()
    except (NoSuchElementException, StaleElementReferenceException):
        return None
    return text or None


def _generic_metadata_from_dom(driver) -> dict[str, str | None]:
    text = driver.execute_script("return document.body.innerText")
    text = _clean_text(text)
    details = _details_region(text)
    if not details:
        return {}

    found: dict[str, str | None] = {}
    for match in re.finditer(
        rf"({LABEL_PATTERN}):\s*(.*?)(?=\s*(?:{LABEL_PATTERN}):|\nReviews\b|\nDescription\b|\Z)",
        details,
        re.DOTALL,
    ):
        label = match.group(1)
        value = _clean_value(match.group(2))
        if value:
            found[LABEL_TO_FIELD[label]] = value
    return found


def _details_region(text: str) -> str | None:
    match = re.search(
        r"\bDETAILS\b.*?\bBrand:\s*(.*?)(?:\nReviews\b|\nDescription\b|\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return None
    return "Brand: " + match.group(1)


def _clean_text(value: str) -> str:
    without_marks = "".join(
        character for character in value if unicodedata.category(character) != "Cf"
    )
    return without_marks.replace("\r\n", "\n").replace("\r", "\n")


def _clean_value(value: str) -> str | None:
    clean = re.sub(r"[ \t]+", " ", value)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    clean = clean.strip(" \t\n,")
    return clean or None
