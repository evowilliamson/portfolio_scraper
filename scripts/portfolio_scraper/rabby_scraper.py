"""
Rabby (EVM) Portfolio Scraper with Anti-Detection - Multi-Wallet Support
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
from datetime import datetime
from .config import RABBY_PASSWORD


class RabbyScraper:
    """Scraper for Rabby (EVM) portfolio with anti-bot detection"""
    
    def __init__(self, debug_port=None, user_data_dir=None):
        self.driver = None
        self.debug_port = debug_port  # Not used anymore, kept for compatibility
        self.user_data_dir = user_data_dir or os.path.expanduser('~/.chrome_rabby_scraper')
        self.min_usd_value = 5  # Minimum USD value threshold
        self.password = RABBY_PASSWORD  # Use provided password or default from config
    
    def connect_to_chrome(self):
        """Start Chrome with undetected-chromedriver for anti-detection"""
        print("[Rabby] Starting Chrome with anti-detection...")
        print(f"[Rabby] Profile directory: {self.user_data_dir}")
        
        try:
            # undetected-chromedriver options
            options = uc.ChromeOptions()
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-software-rasterizer')
            
            # Start Chrome with anti-detection
            # Let undetected-chromedriver auto-detect Chrome version
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=False  # Avoid port conflicts
            )
            
            print(f"[Rabby] ✓ Chrome started with anti-detection")
            print(f"[Rabby] ℹ Profile persists at: {self.user_data_dir}")
            print(f"[Rabby] ℹ Install Rabby extension in this Chrome if not already installed")
            return True
        except Exception as e:
            print(f"[Rabby] ✗ Failed to start Chrome: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_rabby(self):
        """Navigate to Rabby extension DeFi page"""
        url = "chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch/desktop.html#/desktop/profile/difi"
        print(f"[Rabby] Navigating to {url}...")
        self.driver.get(url)
        
        # Check for and handle unlock screen first
        if not self.handle_unlock_screen():
            return False
        
        try:
            # Wait for wallet list to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='virtuoso-item-list']"))
            )
            print("[Rabby] ✓ Wallet list loaded")
            time.sleep(2)
            return True
        except TimeoutException:
            print("[Rabby] ✗ Failed to load wallet list")
            return False
    
    def handle_unlock_screen(self):
        """Check for and handle Rabby unlock screen if present"""
        print("[Rabby] Checking for unlock screen...")
        
        try:
            # Check if password input is present
            password_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#password"))
            )
            
            print("[Rabby] Unlock screen detected, entering password...")
            
            # Enter password
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)
            
            # Click unlock button
            unlock_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            unlock_button.click()
            
            print("[Rabby] ✓ Password entered, waiting for unlock...")
            
            # Wait for unlock to complete (password field should disappear)
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "input#password"))
            )
            
            print("[Rabby] ✓ Successfully unlocked!")
            time.sleep(2)  # Give it a moment to fully load
            return True
            
        except TimeoutException:
            # No unlock screen present, already unlocked
            print("[Rabby] No unlock screen detected (already unlocked)")
            return True
        except Exception as e:
            print(f"[Rabby] ✗ Error handling unlock screen: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def click_defi_tab(self):
        """Click the DeFi tab to ensure it's active"""
        print("[Rabby] Clicking DeFi tab...")
        
        try:
            # Find and click the DeFi tab button
            defi_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ant-tabs-tab-btn[id='rc-tabs-0-tab-difi']"))
            )
            defi_tab.click()
            print("[Rabby] ✓ DeFi tab clicked")
            time.sleep(2)
            return True
        except TimeoutException:
            print("[Rabby] ✗ Failed to find/click DeFi tab")
            return False
        except Exception as e:
            print(f"[Rabby] ✗ Error clicking DeFi tab: {e}")
            return False

    def click_token_tab(self):
        """Click the Token tab to load token balances"""
        print("[Rabby] Clicking Token tab...")
        
        try:
            # Find and click the Token tab button (try different possible IDs)
            token_tab = None
            try:
                token_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ant-tabs-tab-btn[id='rc-tabs-0-tab-token']"))
                )
            except TimeoutException:
                # Try alternative ID
                token_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ant-tabs-tab-btn[id='rc-tabs-0-tab-tokens']"))
                )
            
            token_tab.click()
            print("[Rabby] ✓ Token tab clicked")
            time.sleep(2)
            return True
        except TimeoutException:
            print("[Rabby] ✗ Failed to find/click Token tab")
            # Try to find all tabs and print them for debugging
            try:
                all_tabs = self.driver.find_elements(By.CSS_SELECTOR, "div.ant-tabs-tab-btn")
                print(f"[Rabby] Available tabs: {[tab.get_attribute('id') for tab in all_tabs]}")
            except:
                pass
            return False
        except Exception as e:
            print(f"[Rabby] ✗ Error clicking Token tab: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def click_wallet_by_address(self, target_address):
        """Click on wallet that matches the target address"""
        print(f"[Rabby] Looking for wallet with address: {target_address[:10]}...{target_address[-6:]}")
        
        try:
            # Find all wallet items
            wallet_items = self.driver.find_elements(By.CSS_SELECTOR, "div.desktop-account-item")
            print(f"[Rabby] Found {len(wallet_items)} wallet items")
            
            for idx, item in enumerate(wallet_items, 1):
                try:
                    # Find address viewer element within this wallet item
                    address_elem = item.find_element(By.CSS_SELECTOR, "div.address-viewer-text")
                    full_address = address_elem.get_attribute("title")
                    
                    if full_address and full_address.lower() == target_address.lower():
                        wallet_name_elem = item.find_element(By.CSS_SELECTOR, "div.truncate.text-\\[16px\\]")
                        wallet_name = wallet_name_elem.text.strip()
                        print(f"[Rabby] ✓ Found matching wallet: {wallet_name} ({full_address[:10]}...{full_address[-6:]})")
                        
                        # Click the wallet item
                        item.click()
                        print(f"[Rabby] ✓ Clicked wallet")
                        
                        # Wait for portfolio page to load (wait for tabs to appear)
                        time.sleep(3)
                        
                        # Wait for tab navigation to be ready
                        WebDriverWait(self.driver, 20).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ant-tabs-tab-btn"))
                        )
                        print("[Rabby] ✓ Portfolio page loaded")
                        time.sleep(2)
                        
                        return True
                        
                except NoSuchElementException:
                    continue
            
            print(f"[Rabby] ✗ No wallet found with address {target_address}")
            return False
            
        except Exception as e:
            print(f"[Rabby] ✗ Error clicking wallet: {e}")
            return False
    
    def parse_numeric_value(self, text):
        """Parse numeric value from text (remove $ and commas)"""
        text = text.strip()
        if text.startswith('<') or text.startswith('>'):
            return 0
        text = text.replace('$', '').replace(',', '')
        try:
            return float(text)
        except ValueError:
            return 0

    def parse_amount_value(self, text):
        """Parse numeric amount from text like '19,033.70 reUSDe'"""
        parts = text.strip().split()
        if not parts:
            return 0
        amount_text = parts[0].replace(',', '')
        try:
            return float(amount_text)
        except ValueError:
            return 0
    
    def extract_balance_value(self, balance_text):
        """Extract numeric balance from text like '99,453.1873 PT-sNUSD-5MAR2026' -> '99,453.1873'"""
        parts = balance_text.strip().split()
        if parts:
            return parts[0]
        return balance_text
    
    def extract_project_info(self, project_elem):
        """Extract project name, chain, and total value"""
        project_info = {
            "project_name": "Unknown",
            "chain": "unknown",
            "total_value": 0
        }
        
        try:
            # Extract project ID to get chain
            project_id = project_elem.get_attribute("id") or ""
            if "_" in project_id:
                project_info["chain"] = project_id.split("_")[0]
            
            # Extract project name
            name_elem = project_elem.find_element(By.CSS_SELECTOR, "span.name")
            project_info["project_name"] = name_elem.text.strip()
            
            # Extract total value (numeric only)
            value_elem = project_elem.find_element(By.CSS_SELECTOR, "div.flex.items-center.justify-end.flex-1 span")
            value_text = value_elem.text.strip()
            project_info["total_value"] = self.parse_numeric_value(value_text)
            
        except Exception as e:
            print(f"[Rabby]     Warning: Failed to extract project info: {e}")
        
        return project_info
    
    def scrape_lending_section(self, panel_elem):
        """Scrape Lending section"""
        lending_data = {
            "section_type": "Lending",
            "health_rate": None,
            "supplied": [],
            "borrowed": []
        }
        
        try:
            # Extract Health Rate if present
            try:
                health_rate_elem = panel_elem.find_element(By.CSS_SELECTOR, "span.rabby-KVValue-rabby--1n591ca")
                health_rate_text = health_rate_elem.text.strip()
                try:
                    lending_data["health_rate"] = float(health_rate_text)
                except ValueError:
                    lending_data["health_rate"] = health_rate_text
            except NoSuchElementException:
                pass
            
            # Find all table sections within the panel
            sections = panel_elem.find_elements(By.CSS_SELECTOR, "div.px-8")
            
            print(f"[Rabby]       Found {len(sections)} lending sections")
            
            for section_idx, section in enumerate(sections):
                try:
                    # Get header to determine if it's Supplied or Borrowed
                    header_row = section.find_element(By.CSS_SELECTOR, "div.rabby-HeaderRow-rabby--1yo6z9x")
                    header_text = header_row.text.lower()
                    
                    # Find content rows
                    content_div = section.find_element(By.CSS_SELECTOR, "div.rabby-Content-rabby--fixjhz")
                    rows = content_div.find_elements(By.CSS_SELECTOR, "div.rabby-ContentRow-rabby--e2twba")
                    
                    print(f"[Rabby]         Section '{header_text}': {len(rows)} rows")
                    
                    for row in rows:
                        try:
                            cells = row.find_elements(By.XPATH, "./div")
                            if len(cells) >= 3:
                                # Extract token name
                                token = None
                                try:
                                    token_elem = cells[0].find_element(By.CSS_SELECTOR, "span.ml-2")
                                    token = token_elem.text.strip()
                                except NoSuchElementException:
                                    token = cells[0].text.strip().split('\n')[0]
                                
                                # Extract balance (numeric value only)
                                balance_text = cells[1].text.strip().split('\n')[0]
                                balance_value = self.extract_balance_value(balance_text)
                                
                                # Extract USD value (numeric only)
                                usd_text = cells[2].text.strip()
                                usd_value = self.parse_numeric_value(usd_text)
                                
                                # Filter by minimum USD value
                                if token and balance_value and usd_value >= self.min_usd_value:
                                    asset_info = {
                                        "token": token,
                                        "balance": balance_value,
                                        "usd_value": usd_value
                                    }
                                    
                                    if "supplied" in header_text:
                                        lending_data["supplied"].append(asset_info)
                                        print(f"[Rabby]         ✓ Supplied: {token} - ${usd_value}")
                                    elif "borrowed" in header_text:
                                        lending_data["borrowed"].append(asset_info)
                                        print(f"[Rabby]         ✓ Borrowed: {token} - ${usd_value}")
                                elif usd_value < self.min_usd_value:
                                    print(f"[Rabby]         ⊘ Skipped (< ${self.min_usd_value}): {token} - ${usd_value}")
                        
                        except Exception as e:
                            print(f"[Rabby]         Warning: Failed to parse row: {e}")
                            continue
                
                except Exception as e:
                    print(f"[Rabby]       Warning: Failed to parse section: {e}")
                    continue
        
        except Exception as e:
            print(f"[Rabby]     Error scraping lending section: {e}")
        
        return lending_data
    
    def scrape_deposit_section(self, panel_elem):
        """Scrape Deposit section"""
        deposit_data = {
            "section_type": "Deposit",
            "assets": []
        }
        
        try:
            # Find content section
            content_div = panel_elem.find_element(By.CSS_SELECTOR, "div.rabby-Content-rabby--fixjhz")
            rows = content_div.find_elements(By.CSS_SELECTOR, "div.rabby-ContentRow-rabby--e2twba")
            
            print(f"[Rabby]       Found {len(rows)} deposit rows")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    if len(cells) >= 3:
                        # Extract pool name
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "span.ml-2")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[0].text.strip().split('\n')[0]
                        
                        # Extract balance (numeric value only)
                        balance_text = cells[1].text.strip().split('\n')[0]
                        balance_value = self.extract_balance_value(balance_text)
                        
                        # Extract USD value (numeric only)
                        usd_text = cells[2].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                        # Filter by minimum USD value
                        if pool and balance_value and usd_value >= self.min_usd_value:
                            asset_info = {
                                "pool": pool,
                                "balance": balance_value,
                                "usd_value": usd_value
                            }
                            deposit_data["assets"].append(asset_info)
                            print(f"[Rabby]       ✓ Parsed deposit: {pool} - ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[Rabby]       ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[Rabby]       Warning: Failed to parse deposit row: {e}")
                    continue
        
        except Exception as e:
            print(f"[Rabby]     Error scraping deposit section: {e}")
        
        return deposit_data





    def scrape_yield_section(self, panel_elem):
        """Scrape Yield section"""
        yield_data = {
            "section_type": "Yield",
            "assets": []
        }
        
        try:
            # Find content section
            content_div = panel_elem.find_element(By.CSS_SELECTOR, "div.rabby-Content-rabby--fixjhz")
            rows = content_div.find_elements(By.CSS_SELECTOR, "div.rabby-ContentRow-rabby--e2twba")
            
            print(f"[Rabby]       Found {len(rows)} yield rows")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    
                    # Handle both 3-column and 4-column layouts
                    if len(cells) >= 4:
                        # 4 columns: identifier, pool, balance, usd_value
                        identifier = cells[0].text.strip()
                        
                        pool = None
                        try:
                            pool_elem = cells[1].find_element(By.CSS_SELECTOR, "span.ml-2")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[1].text.strip().split('\n')[0]
                        
                        balance_text = cells[2].text.strip().split('\n')[0]
                        balance_value = self.extract_balance_value(balance_text)
                        
                        usd_text = cells[3].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                    elif len(cells) >= 3:
                        # 3 columns: pool, balance, usd_value (no identifier)
                        identifier = ""  # No identifier in this layout
                        
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "span.ml-2")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[0].text.strip().split('\n')[0]
                        
                        balance_text = cells[1].text.strip().split('\n')[0]
                        balance_value = self.extract_balance_value(balance_text)
                        
                        usd_text = cells[2].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                    else:
                        # Not enough columns, skip
                        continue
                    
                    # Filter by minimum USD value
                    if pool and balance_value and usd_value >= self.min_usd_value:
                        asset_info = {
                            "identifier": identifier,
                            "pool": pool,
                            "balance": balance_value,
                            "usd_value": usd_value
                        }
                        yield_data["assets"].append(asset_info)
                        print(f"[Rabby]       ✓ Parsed yield: {pool} - ${usd_value}")
                    elif usd_value < self.min_usd_value:
                        print(f"[Rabby]       ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[Rabby]       Warning: Failed to parse yield row: {e}")
                    continue
        
        except Exception as e:
            print(f"[Rabby]     Error scraping yield section: {e}")
        
        return yield_data




 
    def scrape_staked_section(self, panel_elem):
        """Scrape Staked section (same structure as Yield)"""
        staked_data = {
            "section_type": "Staked",
            "assets": []
        }
        
        try:
            # Find content section
            content_div = panel_elem.find_element(By.CSS_SELECTOR, "div.rabby-Content-rabby--fixjhz")
            rows = content_div.find_elements(By.CSS_SELECTOR, "div.rabby-ContentRow-rabby--e2twba")
            
            print(f"[Rabby]       Found {len(rows)} staked rows")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    
                    # Staked sections have 4 columns (identifier, pool, balance, usd_value)
                    if len(cells) >= 4:
                        # Extract identifier
                        identifier = cells[0].text.strip()
                        
                        # Extract pool name
                        pool = None
                        try:
                            pool_elem = cells[1].find_element(By.CSS_SELECTOR, "span.ml-2")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[1].text.strip().split('\n')[0]
                        
                        # Extract balance (numeric value only)
                        balance_text = cells[2].text.strip().split('\n')[0]
                        balance_value = self.extract_balance_value(balance_text)
                        
                        # Extract USD value (numeric only)
                        usd_text = cells[3].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                        # Filter by minimum USD value
                        if pool and balance_value and usd_value >= self.min_usd_value:
                            asset_info = {
                                "identifier": identifier,
                                "pool": pool,
                                "balance": balance_value,
                                "usd_value": usd_value
                            }
                            staked_data["assets"].append(asset_info)
                            print(f"[Rabby]       ✓ Parsed staked: {pool} - ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[Rabby]       ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[Rabby]       Warning: Failed to parse staked row: {e}")
                    continue
        
        except Exception as e:
            print(f"[Rabby]     Error scraping staked section: {e}")
        
        return staked_data
    
    def scrape_locked_section(self, panel_elem):
        """Scrape Locked section (Pool, Balance, USD Value - ignoring Unlock time)"""
        locked_data = {
            "section_type": "Locked",
            "assets": []
        }
        
        try:
            # Find content section
            content_div = panel_elem.find_element(By.CSS_SELECTOR, "div.rabby-Content-rabby--fixjhz")
            rows = content_div.find_elements(By.CSS_SELECTOR, "div.rabby-ContentRow-rabby--e2twba")
            
            print(f"[Rabby]       Found {len(rows)} locked rows")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    
                    # Locked sections have 4 columns (pool, balance, unlock_time, usd_value)
                    # We skip unlock_time (index 2)
                    if len(cells) >= 4:
                        # Extract pool name
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "span.ml-2")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[0].text.strip().split('\n')[0]
                        
                        # Extract balance (numeric value only)
                        balance_text = cells[1].text.strip().split('\n')[0]
                        balance_value = self.extract_balance_value(balance_text)
                        
                        # Skip unlock_time at cells[2]
                        
                        # Extract USD value (numeric only) from cells[3]
                        usd_text = cells[3].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                        # Filter by minimum USD value
                        if pool and balance_value and usd_value >= self.min_usd_value:
                            asset_info = {
                                "pool": pool,
                                "balance": balance_value,
                                "usd_value": usd_value
                            }
                            locked_data["assets"].append(asset_info)
                            print(f"[Rabby]       ✓ Parsed locked: {pool} - ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[Rabby]       ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[Rabby]       Warning: Failed to parse locked row: {e}")
                    continue
        
        except Exception as e:
            print(f"[Rabby]     Error scraping locked section: {e}")
        
        return locked_data

    def scrape_token_tab(self):
        """Scrape Token tab balances and return as a project dict"""
        if not self.click_token_tab():
            return None
        
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.rabby-TokenRowWrapper-rabby--1n616m8"))
            )
        except TimeoutException:
            print("[Rabby] ✗ Token rows not found")
            return None
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, "div.rabby-TokenRowWrapper-rabby--1n616m8")
        print(f"[Rabby] Found {len(rows)} token rows")
        
        assets = []
        total_value = 0
        
        for row in rows:
            try:
                cells = row.find_elements(By.XPATH, "./div")
                if len(cells) < 4:
                    continue
                
                # Token name
                token = None
                try:
                    token_elem = cells[0].find_element(By.CSS_SELECTOR, "span.ml-2")
                    token = token_elem.text.strip()
                except NoSuchElementException:
                    token = cells[0].text.strip().split('\n')[0]
                
                # Price
                price_text = cells[1].text.strip().split('\n')[0]
                price = self.parse_numeric_value(price_text)
                
                # Amount
                amount_text = cells[2].text.strip().split('\n')[0]
                amount = self.parse_amount_value(amount_text)
                
                # USD Value
                usd_text = cells[3].text.strip()
                usd_value = self.parse_numeric_value(usd_text)
                
                if token and usd_value >= self.min_usd_value:
                    assets.append({
                        "token": token,
                        "price": price,
                        "amount": amount,
                        "usd_value": usd_value
                    })
                    total_value += usd_value
                elif usd_value < self.min_usd_value:
                    print(f"[Rabby]       ⊘ Skipped token (< ${self.min_usd_value}): {token} - ${usd_value}")
            except Exception as e:
                print(f"[Rabby]       Warning: Failed to parse token row: {e}")
                continue
        
        return {
            "project_name": "Token",
            "chain": "evm",
            "total_value": total_value,
            "sections": [
                {
                    "section_type": "Token",
                    "assets": assets
                }
            ]
        }
    
    def scrape_current_portfolio(self, wallet_address):
        """Scrape portfolio for currently loaded wallet"""
        print(f"\n[Rabby] Scraping portfolio for {wallet_address[:10]}...{wallet_address[-6:]}")
        print(f"[Rabby] Filtering assets with USD value >= ${self.min_usd_value}")
        
        try:
            # First scrape Token tab
            token_project = self.scrape_token_tab()
            
            # Switch to DeFi tab to scrape DeFi projects
            if not self.click_defi_tab():
                print("[Rabby] ✗ Failed to return to DeFi tab after Token")
                return None
            
            # Wait for DeFi projects to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.rabby-ProtocolItemWrapper-rabby--utb8ns"))
                )
                print("[Rabby] ✓ DeFi projects loaded")
                time.sleep(2)
                
                # Scroll to trigger lazy loading of DeFi projects
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            except TimeoutException:
                print("[Rabby] ⚠ No DeFi projects found (timeout)")
            
            # Find all DeFi projects
            project_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.rabby-ProtocolItemWrapper-rabby--utb8ns")
            print(f"[Rabby] Found {len(project_elements)} DeFi projects")
            
            projects = []
            
            for idx, project_elem in enumerate(project_elements, 1):
                try:
                    # Extract project info from title section
                    project_title = project_elem.find_element(By.CSS_SELECTOR, "div.flex.items-center.justify-start")
                    project_info = self.extract_project_info(project_elem)
                    
                    print(f"[Rabby] [{idx}] Processing: {project_info['project_name']} ({project_info['chain']}) - ${project_info['total_value']}")
                    
                    project_data = {
                        "project_name": project_info["project_name"],
                        "chain": project_info["chain"],
                        "total_value": project_info["total_value"],
                        "sections": []
                    }
                    
                    # Find all sections within this project
                    try:
                        pool_container = project_elem.find_element(By.CSS_SELECTOR, "div.rabby-PoolListContainer-rabby--yotgd0")
                        panels = pool_container.find_elements(By.CSS_SELECTOR, "div.rabby-Container-rabby--1rr9ga5")
                        
                        print(f"[Rabby]   Found {len(panels)} sections")
                        
                        for panel in panels:
                            try:
                                # Get section type from bookmark
                                bookmark = panel.find_element(By.CSS_SELECTOR, "div.rabby-Bookmark-rabby--1kwtxm2")
                                section_type = bookmark.text.strip()
                                
                                print(f"[Rabby]     Processing section: {section_type}")
                                
                                if section_type == "Lending":
                                    section_data = self.scrape_lending_section(panel)
                                    project_data["sections"].append(section_data)
                                elif section_type == "Yield":
                                    section_data = self.scrape_yield_section(panel)
                                    project_data["sections"].append(section_data)
                                elif section_type == "Deposit":
                                    section_data = self.scrape_deposit_section(panel)
                                    project_data["sections"].append(section_data)
                                elif section_type == "Staked":
                                    section_data = self.scrape_staked_section(panel)
                                    project_data["sections"].append(section_data)
                                elif section_type == "Locked":
                                    section_data = self.scrape_locked_section(panel)
                                    project_data["sections"].append(section_data)
                                else:
                                    print(f"[Rabby]     Skipping unknown section type: {section_type}")
                                    
                            except Exception as e:
                                print(f"[Rabby]     Error processing section: {e}")
                                continue
                    
                    except NoSuchElementException:
                        print(f"[Rabby]   No sections found in project")
                    
                    projects.append(project_data)
                    
                except Exception as e:
                    print(f"[Rabby]   Error processing project: {e}")
                    continue

            if token_project:
                projects.insert(0, token_project)
            
            portfolio_data = {
                "blockchain": "evm",
                "timestamp": datetime.now().isoformat(),
                "wallet_address": wallet_address,
                "projects_count": len(projects),
                "projects": projects
            }
            
            print(f"[Rabby] ✓ Scraping completed! Found {len(projects)} projects")
            return portfolio_data
            
        except Exception as e:
            print(f"[Rabby] ✗ Fatal error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_portfolio(self, wallet_addresses):
        """Main scraping function - navigates to wallets and scrapes each one
        
        Args:
            wallet_addresses: Single address (str) or list of addresses to scrape
            
        Returns:
            Single portfolio dict if one address provided, list of dicts if multiple
        """
        print(f"\n{'='*60}")
        print("[Rabby] SCRAPING EVM PORTFOLIO")
        print(f"{'='*60}")
        
        # Handle single address
        if isinstance(wallet_addresses, str):
            wallet_addresses = [wallet_addresses]
            return_single = True
        else:
            return_single = False
        
        try:
            # Connect to Chrome if not already connected
            if not self.driver:
                if not self.connect_to_chrome():
                    return None
            
            # Navigate to Rabby extension
            if not self.navigate_to_rabby():
                return None
            
            # Click DeFi tab to ensure it's active
            if not self.click_defi_tab():
                return None
            
            # Process each wallet
            all_portfolios = []
            
            for idx, wallet_address in enumerate(wallet_addresses, 1):
                print(f"\n[Rabby] {'='*60}")
                print(f"[Rabby] Processing wallet {idx}/{len(wallet_addresses)}")
                print(f"[Rabby] {'='*60}")
                
                # Click on the wallet matching the address
                if not self.click_wallet_by_address(wallet_address):
                    print(f"[Rabby] ✗ Failed to load wallet {wallet_address}, skipping...")
                    all_portfolios.append(None)
                    continue
                
                # Scrape the portfolio
                portfolio_data = self.scrape_current_portfolio(wallet_address)
                all_portfolios.append(portfolio_data)
                
                # Navigate back to wallet list for next iteration (if not last wallet)
                if idx < len(wallet_addresses):
                    print(f"\n[Rabby] Returning to wallet list...")
                    if not self.navigate_to_rabby():
                        print(f"[Rabby] ✗ Failed to return to wallet list")
                        break
                    if not self.click_defi_tab():
                        print(f"[Rabby] ✗ Failed to click DeFi tab")
                        break
            
            # Return single portfolio or list based on input
            if return_single:
                return all_portfolios[0] if all_portfolios else None
            else:
                return all_portfolios
            
        except Exception as e:
            print(f"[Rabby] ✗ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("[Rabby] ✓ Driver cleaned up")
            except:
                pass