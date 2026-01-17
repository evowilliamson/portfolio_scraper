"""Parsing helpers for Jupiter scraper."""
import re

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def parse_numeric_value(text):
    """Parse numeric value from text."""
    text = text.strip()
    if text.startswith('<'):
        return 0
    text = text.replace('$', '').replace(',', '')
    try:
        return float(text)
    except ValueError:
        return 0


def extract_token_info(cell):
    """Extract token name from cell."""
    try:
        token_elem = cell.find_element(By.CSS_SELECTOR, "p.text-sm")
        return token_elem.text.strip() or "Unknown"
    except NoSuchElementException:
        text = cell.text.strip().split('\n')[0]
        return text if text else "Unknown"


def extract_balance_only(balance_text):
    """Parse balance text (numeric only, no token name)."""
    lines = balance_text.strip().split('\n')
    if len(lines) >= 1:
        balance_str = lines[0].strip().replace(',', '')
        balance_str = re.sub(r'[^\d.-]', '', balance_str)
        try:
            return float(balance_str) if balance_str else 0
        except ValueError:
            return 0
    return 0


def extract_balance_and_token(balance_text):
    """Parse balance text like '46,172 CASH' into numeric balance."""
    lines = balance_text.strip().split('\n')
    if len(lines) >= 1:
        parts = lines[0].strip().rsplit(' ', 1)
        if len(parts) == 2:
            balance_str = parts[0].replace(',', '')
            try:
                return float(balance_str)
            except ValueError:
                return 0
        return extract_balance_only(balance_text)
    return 0


def extract_yield_value(cell):
    """Extract yield percentage as numeric value."""
    try:
        yield_elem = cell.find_element(By.CSS_SELECTOR, "span")
        yield_text = yield_elem.text.strip().replace('%', '').replace('+', '')
        return float(yield_text) if yield_text else 0
    except (NoSuchElementException, ValueError):
        return 0
