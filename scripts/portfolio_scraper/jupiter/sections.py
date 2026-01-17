"""Section scrapers for Jupiter portfolio pages."""
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .parsers import (
    extract_balance_and_token,
    extract_balance_only,
    extract_token_info,
    extract_yield_value,
    parse_numeric_value,
)

def _get_primary_rows(section_elem):
    """Return rows from the first tbody in the section table."""
    table = section_elem.find_element(By.CSS_SELECTOR, "table")
    tbodies = table.find_elements(By.TAG_NAME, "tbody")
    if not tbodies:
        return []
    return tbodies[0].find_elements(By.CSS_SELECTOR, "tr.transition-colors")


def _parse_lending_rows(rows, target_list, balance_idx=1, yield_idx=3, value_idx=4):
    """Parse lending rows into the provided list."""
    for row in rows:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 5:
                target_list.append({
                    "token": extract_token_info(cells[0]),
                    "balance": extract_balance_and_token(cells[balance_idx].text.strip()),
                    "yield": extract_yield_value(cells[yield_idx]),
                    "value": parse_numeric_value(cells[value_idx].text.strip())
                })
        except Exception as e:
            print(f"[Jupiter] Warning: Failed to parse lending row: {e}")


def _scrape_lending_like_section(section_elem, section_type, market_name):
    """Generic scraper for Lending and Leverage sections (same structure).
    
    Args:
        section_elem: Selenium element containing the section
        section_type: "Lending" or "Leverage"
        market_name: Name of the market/protocol
    
    Returns:
        dict with section_type, market_name, supplied, and borrowed lists
    """
    section_data = {
        "section_type": section_type,
        "market_name": market_name,
        "supplied": [],
        "borrowed": []
    }

    try:
        table = section_elem.find_element(By.CSS_SELECTOR, "table")
        theads = table.find_elements(By.TAG_NAME, "thead")
        tbodies = table.find_elements(By.TAG_NAME, "tbody")

        tbody_index = 0

        for thead in theads:
            thead_text = thead.text.lower()

            if "supplied" in thead_text:
                if tbody_index < len(tbodies):
                    tbody = tbodies[tbody_index]
                    rows = tbody.find_elements(By.CSS_SELECTOR, "tr.transition-colors")

                    _parse_lending_rows(rows, section_data["supplied"])
                    tbody_index += 1

            elif "borrowed" in thead_text:
                if tbody_index < len(tbodies):
                    tbody = tbodies[tbody_index]
                    rows = tbody.find_elements(By.CSS_SELECTOR, "tr.transition-colors")
                    _parse_lending_rows(rows, section_data["borrowed"])
                    tbody_index += 1
    except Exception as e:
        print(f"[Jupiter] Error scraping {section_type.lower()} section: {e}")

    return section_data


def scrape_wallet_section(section_elem):
    """Scrape wallet section data (similar to farming but without yield column)."""
    wallet_data = {
        "section_type": "Wallet",
        "assets": []
    }

    try:
        asset_rows = _get_primary_rows(section_elem)

        print(f"[Jupiter]     Wallet section found {len(asset_rows)} asset rows")

        for row_idx, row in enumerate(asset_rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                print(f"[Jupiter]       Row {row_idx+1}: {len(cells)} cells")

                if len(cells) >= 4:
                    token = extract_token_info(cells[0])
                    balance_text = cells[1].text.strip()
                    value = parse_numeric_value(cells[3].text.strip())
                    balance = extract_balance_only(balance_text)

                    print(
                        f"[Jupiter]       Token: {token}, Balance text: '{balance_text}', "
                        f"Balance: {balance}, Value: {value}"
                    )

                    wallet_data["assets"].append({
                        "token": token,
                        "balance": balance,
                        "value": value
                    })
            except Exception as e:
                print(f"[Jupiter] Warning: Failed to parse wallet asset row {row_idx+1}: {e}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        print(f"[Jupiter] Error scraping wallet section: {e}")
        import traceback
        traceback.print_exc()

    return wallet_data


def scrape_farming_section(section_elem):
    """Scrape farming section data."""
    farming_data = {
        "section_type": "Farming",
        "assets": []
    }

    try:
        asset_rows = _get_primary_rows(section_elem)

        for row in asset_rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 4:
                    farming_data["assets"].append({
                        "token": extract_token_info(cells[0]),
                        "balance": extract_balance_and_token(cells[1].text.strip()),
                        "yield": extract_yield_value(cells[2]),
                        "value": parse_numeric_value(cells[3].text.strip())
                    })
            except Exception as e:
                print(f"[Jupiter] Warning: Failed to parse asset row: {e}")
    except Exception as e:
        print(f"[Jupiter] Error scraping farming section: {e}")

    return farming_data


def scrape_lending_section(section_elem, market_name):
    """Scrape lending section data."""
    return _scrape_lending_like_section(section_elem, "Lending", market_name)


def scrape_leverage_section(section_elem, market_name):
    """Scrape leverage section data (same structure as lending)."""
    return _scrape_lending_like_section(section_elem, "Leverage", market_name)