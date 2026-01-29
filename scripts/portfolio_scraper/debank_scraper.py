"""
DeBank Portfolio Scraper with Anti-Detection - Multi-Wallet Support
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
from datetime import datetime
from .utils import get_chrome_major_version


class DebankScraper:
    """Scraper for DeBank portfolio with anti-bot detection"""
    
    def __init__(self, debug_port=None, user_data_dir=None):
        self.driver = None
        self.debug_port = debug_port  # Not used anymore, kept for compatibility
        self.user_data_dir = user_data_dir or os.path.expanduser('~/.chrome_debank_scraper')
        self.min_usd_value = 5  # Minimum USD value threshold
    
    def is_driver_alive(self):
        """Check if the driver is still responsive"""
        if not self.driver:
            return False
        try:
            # Try a simple command to check if driver is responsive
            _ = self.driver.current_url
            return True
        except Exception:
            return False
    
    def connect_to_chrome(self):
        """Start Chrome with undetected-chromedriver for anti-detection"""
        print("[DeBank] Starting Chrome with anti-detection...")
        print(f"[DeBank] Profile directory: {self.user_data_dir}")
        
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
            version_main = get_chrome_major_version()
            if version_main:
                print(f"[DeBank] ℹ Using detected Chrome major version: {version_main}")
                self.driver = uc.Chrome(
                    options=options,
                    version_main=version_main,
                    use_subprocess=False  # Avoid port conflicts
                )
            else:
                print("[DeBank] ℹ Chrome version unknown; using auto-detection")
                self.driver = uc.Chrome(
                    options=options,
                    use_subprocess=False  # Avoid port conflicts
                )
            
            print(f"[DeBank] ✓ Chrome started with anti-detection")
            print(f"[DeBank] ℹ Profile persists at: {self.user_data_dir}")
            return True
        except Exception as e:
            print(f"[DeBank] ✗ Failed to start Chrome: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_debank(self, wallet_address):
        """Navigate to DeBank profile page for given address"""
        url = f"https://debank.com/profile/{wallet_address}"
        print(f"[DeBank] Navigating to {url}...")
        self.driver.get(url)
        
        try:
            # Wait for page to load - look for the Wallet section
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProjectTitle_projectTitle__yC5VD"))
            )
            print("[DeBank] ✓ Profile page loaded")
            time.sleep(3)  # Give extra time for dynamic content
            
            # Scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            return True
        except TimeoutException:
            print("[DeBank] ✗ Failed to load profile page")
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
    
    def scrape_wallet_section(self):
        """Scrape Wallet section (equivalent to Token tab in Rabby)"""
        print("[DeBank] Scraping Wallet section...")
        
        wallet_data = {
            "project_name": "Token",
            "chain": "evm",
            "total_value": 0,
            "sections": [
                {
                    "section_type": "Token",
                    "assets": []
                }
            ]
        }
        
        try:
            # Find Wallet section
            wallet_section = self.driver.find_element(By.CSS_SELECTOR, "div.ProjectTitle_projectTitle__yC5VD#Wallet")
            
            # Extract total value from Wallet header
            try:
                total_value_elem = wallet_section.find_element(By.CSS_SELECTOR, "div.projectTitle-number")
                total_value_text = total_value_elem.text.strip()
                wallet_data["total_value"] = self.parse_numeric_value(total_value_text)
                print(f"[DeBank]   Wallet total value: ${wallet_data['total_value']}")
            except NoSuchElementException:
                print("[DeBank]   Warning: Could not find wallet total value")
            
            # Find the wallet table
            wallet_card = self.driver.find_element(By.CSS_SELECTOR, "div.Card_card__pSup9.TokenWallet_card__teb0g")
            
            # Find all asset rows
            asset_rows = wallet_card.find_elements(By.CSS_SELECTOR, "div.db-table-wrappedRow")
            print(f"[DeBank]   Found {len(asset_rows)} wallet assets")
            
            for row in asset_rows:
                try:
                    # Get all cells in the row
                    cells = row.find_elements(By.CSS_SELECTOR, "div.db-table-cell")
                    
                    if len(cells) >= 4:
                        # Extract token name
                        token = None
                        try:
                            token_elem = cells[0].find_element(By.CSS_SELECTOR, "a.TokenWallet_detailLink__goYJR")
                            token = token_elem.text.strip()
                        except NoSuchElementException:
                            token = cells[0].text.strip()
                        
                        # Extract price
                        price_text = cells[1].text.strip()
                        price = self.parse_numeric_value(price_text)
                        
                        # Extract amount
                        amount_text = cells[2].text.strip()
                        amount = self.parse_amount_value(amount_text)
                        
                        # Extract USD value
                        usd_text = cells[3].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                        # Filter by minimum USD value
                        if token and usd_value >= self.min_usd_value:
                            wallet_data["sections"][0]["assets"].append({
                                "token": token,
                                "price": price,
                                "amount": amount,
                                "usd_value": usd_value
                            })
                            print(f"[DeBank]     ✓ {token}: ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[DeBank]     ⊘ Skipped (< ${self.min_usd_value}): {token} - ${usd_value}")
                
                except Exception as e:
                    print(f"[DeBank]     Warning: Failed to parse wallet asset: {e}")
                    continue
        
        except NoSuchElementException:
            print("[DeBank]   ⚠ Wallet section not found")
        except Exception as e:
            print(f"[DeBank]   Error scraping wallet section: {e}")
        
        return wallet_data
    
    def scrape_lending_section(self, section_elem):
        """Scrape Lending section"""
        lending_data = {
            "section_type": "Lending",
            "health_rate": None,
            "supplied": [],
            "borrowed": []
        }
        
        try:
            # Extract Health Rate if present (look for it in the section)
            try:
                # Health rate might be in a KV display or similar element
                # This selector may need adjustment based on actual DeBank HTML
                health_rate_elem = section_elem.find_element(By.XPATH, ".//span[contains(text(), 'Health')]/..//span[not(contains(text(), 'Health'))]")
                health_rate_text = health_rate_elem.text.strip()
                try:
                    lending_data["health_rate"] = float(health_rate_text)
                except ValueError:
                    lending_data["health_rate"] = health_rate_text
            except NoSuchElementException:
                pass
            
            # Find all tables within this section (Supplied and Borrowed)
            tables = section_elem.find_elements(By.CSS_SELECTOR, "div.table_header__onfbK")
            
            for table_idx, table_header in enumerate(tables):
                try:
                    # Get header text to determine if it's Supplied or Borrowed
                    header_text = table_header.text.lower()
                    
                    # Find the parent container and then get content rows
                    table_container = table_header.find_element(By.XPATH, "./..")
                    content_rows = table_container.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
                    
                    print(f"[DeBank]         Table '{header_text}': {len(content_rows)} rows")
                    
                    for row in content_rows:
                        try:
                            cells = row.find_elements(By.XPATH, "./div")
                            
                            if len(cells) >= 3:
                                # Extract token name
                                token = None
                                try:
                                    token_elem = cells[0].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                                    token = token_elem.text.strip()
                                except NoSuchElementException:
                                    token = cells[0].text.strip()
                                
                                # Extract balance (numeric value only)
                                balance_text = cells[1].text.strip()
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
                                    
                                    if "supplied" in header_text or "supply" in header_text:
                                        lending_data["supplied"].append(asset_info)
                                        print(f"[DeBank]           ✓ Supplied: {token} - ${usd_value}")
                                    elif "borrowed" in header_text or "borrow" in header_text:
                                        lending_data["borrowed"].append(asset_info)
                                        print(f"[DeBank]           ✓ Borrowed: {token} - ${usd_value}")
                                elif usd_value < self.min_usd_value:
                                    print(f"[DeBank]           ⊘ Skipped (< ${self.min_usd_value}): {token} - ${usd_value}")
                        
                        except Exception as e:
                            print(f"[DeBank]           Warning: Failed to parse row: {e}")
                            continue
                
                except Exception as e:
                    print(f"[DeBank]         Warning: Failed to parse table: {e}")
                    continue
        
        except Exception as e:
            print(f"[DeBank]       Error scraping lending section: {e}")
        
        return lending_data
    
    def scrape_deposit_section(self, section_elem):
        """Scrape Deposit section"""
        deposit_data = {
            "section_type": "Deposit",
            "assets": []
        }
        
        try:
            # Find content rows (they're inside the panel)
            content_rows = section_elem.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
            
            print(f"[DeBank]         Found {len(content_rows)} deposit rows")
            
            for row in content_rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    
                    if len(cells) >= 3:
                        # Extract pool name
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[0].text.strip()
                        
                        # Extract balance (numeric value only)
                        balance_text = cells[1].text.strip()
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
                            print(f"[DeBank]         ✓ Parsed deposit: {pool} - ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[DeBank]         ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[DeBank]         Warning: Failed to parse deposit row: {e}")
                    continue
        
        except Exception as e:
            print(f"[DeBank]       Error scraping deposit section: {e}")
        
        return deposit_data
    
    def scrape_yield_section(self, section_elem):
        """Scrape Yield section"""
        yield_data = {
            "section_type": "Yield",
            "assets": []
        }
        
        try:
            # Find content rows
            content_rows = section_elem.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
            
            print(f"[DeBank]         Found {len(content_rows)} yield rows")
            
            for row in content_rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    
                    # Handle both 3-column and 4-column layouts
                    if len(cells) >= 4:
                        # 4 columns: identifier, pool, balance, usd_value
                        identifier = cells[0].text.strip()
                        
                        pool = None
                        try:
                            pool_elem = cells[1].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[1].text.strip()
                        
                        balance_text = cells[2].text.strip()
                        balance_value = self.extract_balance_value(balance_text)
                        
                        usd_text = cells[3].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                    elif len(cells) >= 3:
                        # 3 columns: pool, balance, usd_value (no identifier)
                        identifier = ""
                        
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[0].text.strip()
                        
                        balance_text = cells[1].text.strip()
                        balance_value = self.extract_balance_value(balance_text)
                        
                        usd_text = cells[2].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                    else:
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
                        print(f"[DeBank]         ✓ Parsed yield: {pool} - ${usd_value}")
                    elif usd_value < self.min_usd_value:
                        print(f"[DeBank]         ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[DeBank]         Warning: Failed to parse yield row: {e}")
                    continue
        
        except Exception as e:
            print(f"[DeBank]       Error scraping yield section: {e}")
        
        return yield_data
    
    def scrape_staked_section(self, section_elem):
        """Scrape Staked section"""
        staked_data = {
            "section_type": "Staked",
            "assets": []
        }
        
        try:
            # Find content rows
            content_rows = section_elem.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
            
            print(f"[DeBank]         Found {len(content_rows)} staked rows")
            
            for row in content_rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    
                    if len(cells) >= 4:
                        # Extract identifier
                        identifier = cells[0].text.strip()
                        
                        # Extract pool name
                        pool = None
                        try:
                            pool_elem = cells[1].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[1].text.strip()
                        
                        # Extract balance (numeric value only)
                        balance_text = cells[2].text.strip()
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
                            print(f"[DeBank]         ✓ Parsed staked: {pool} - ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[DeBank]         ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[DeBank]         Warning: Failed to parse staked row: {e}")
                    continue
        
        except Exception as e:
            print(f"[DeBank]       Error scraping staked section: {e}")
        
        return staked_data
    
    def scrape_locked_section(self, section_elem):
        """Scrape Locked section"""
        locked_data = {
            "section_type": "Locked",
            "assets": []
        }
        
        try:
            # Find content rows
            content_rows = section_elem.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
            
            print(f"[DeBank]         Found {len(content_rows)} locked rows")
            
            for row in content_rows:
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    
                    if len(cells) >= 4:
                        # 4 columns: pool, balance, unlock_time, usd_value
                        # Extract pool name
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[0].text.strip()
                        
                        # Extract balance (numeric value only)
                        balance_text = cells[1].text.strip()
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
                            print(f"[DeBank]         ✓ Parsed locked: {pool} - ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[DeBank]         ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                    
                    elif len(cells) >= 3:
                        # 3 columns: pool, balance, usd_value (no unlock_time)
                        # Extract pool name
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            pool = cells[0].text.strip()
                        
                        # Extract balance (numeric value only)
                        balance_text = cells[1].text.strip()
                        balance_value = self.extract_balance_value(balance_text)
                        
                        # Extract USD value (numeric only) from cells[2]
                        usd_text = cells[2].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                        # Filter by minimum USD value
                        if pool and balance_value and usd_value >= self.min_usd_value:
                            asset_info = {
                                "pool": pool,
                                "balance": balance_value,
                                "usd_value": usd_value
                            }
                            locked_data["assets"].append(asset_info)
                            print(f"[DeBank]         ✓ Parsed locked: {pool} - ${usd_value}")
                        elif usd_value < self.min_usd_value:
                            print(f"[DeBank]         ⊘ Skipped (< ${self.min_usd_value}): {pool} - ${usd_value}")
                
                except Exception as e:
                    print(f"[DeBank]         Warning: Failed to parse locked row: {e}")
                    continue
        
        except Exception as e:
            print(f"[DeBank]       Error scraping locked section: {e}")
        
        return locked_data
    
    def scrape_current_portfolio(self, wallet_address):
        """Scrape portfolio for currently loaded wallet"""
        print(f"\n[DeBank] Scraping portfolio for {wallet_address[:10]}...{wallet_address[-6:]}")
        print(f"[DeBank] Filtering assets with USD value >= ${self.min_usd_value}")
        
        try:
            # First scrape Wallet section
            wallet_project = self.scrape_wallet_section()
            
            # Find all project containers (exclude Wallet which has id="Wallet")
            # Each project is in a div.ProjectTitle_projectTitle__yC5VD that's NOT the Wallet
            all_project_titles = self.driver.find_elements(By.CSS_SELECTOR, "div.ProjectTitle_projectTitle__yC5VD")
            
            # Filter out the Wallet section
            project_containers = [p for p in all_project_titles if p.get_attribute("id") != "Wallet"]
            
            print(f"[DeBank] Found {len(project_containers)} DeFi projects")
            
            projects = []
            
            for idx, project_title_elem in enumerate(project_containers, 1):
                try:
                    # Extract project name
                    project_name = "Unknown"
                    try:
                        project_name_elem = project_title_elem.find_element(By.CSS_SELECTOR, "span.ProjectTitle_protocolLink__4Yqn3")
                        project_name = project_name_elem.text.strip()
                    except NoSuchElementException:
                        # Try alternative - just get the name div
                        try:
                            project_name_elem = project_title_elem.find_element(By.CSS_SELECTOR, "div.ProjectTitle_name__x2ZNR")
                            project_name = project_name_elem.text.strip()
                        except NoSuchElementException:
                            pass
                    
                    print(f"[DeBank] [{idx}] Processing: {project_name}")
                    
                    # Extract total value
                    total_value = 0
                    try:
                        total_value_elem = project_title_elem.find_element(By.CSS_SELECTOR, "div.projectTitle-number")
                        total_value = self.parse_numeric_value(total_value_elem.text.strip())
                    except NoSuchElementException:
                        pass
                    
                    # Extract chain from ID if available
                    chain = "evm"
                    project_id = project_title_elem.get_attribute("id") or ""
                    if "_" in project_id:
                        chain = project_id.split("_")[0]
                    
                    project_data = {
                        "project_name": project_name,
                        "chain": chain,
                        "total_value": total_value,
                        "sections": []
                    }
                    
                    # Find Panel containers that follow this project title
                    # Structure: ProjectTitle -> (sibling) Panel_container__Vltd1 (one for each section)
                    try:
                        # Find all Panel_container elements that are siblings following the project title
                        # Use XPath to get following-sibling panels
                        panel_containers = project_title_elem.find_elements(By.XPATH, "./following-sibling::div[contains(@class, 'Panel_container')]")
                        
                        print(f"[DeBank]     Found {len(panel_containers)} panel containers")
                        
                        for panel in panel_containers:
                            try:
                                # Find the BookMark (section type) within this panel
                                bookmark_elem = panel.find_element(By.CSS_SELECTOR, "div.BookMark_bookmark__UG5a4")
                                section_type = bookmark_elem.text.strip()
                                
                                print(f"[DeBank]       Processing section: {section_type}")
                                
                                # The panel itself is the container with the table data
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
                                    print(f"[DeBank]       Skipping unknown section type: {section_type}")
                            
                            except NoSuchElementException:
                                # Panel might not have a bookmark (unusual but handle it)
                                print(f"[DeBank]       Warning: Panel without BookMark found")
                                continue
                            except Exception as e:
                                print(f"[DeBank]       Error processing panel: {e}")
                                import traceback
                                traceback.print_exc()
                                continue
                    
                    except Exception as e:
                        print(f"[DeBank]     Error finding panels: {e}")
                    
                    projects.append(project_data)
                
                except Exception as e:
                    print(f"[DeBank]     Error processing project: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Insert wallet project at the beginning
            if wallet_project:
                projects.insert(0, wallet_project)
            
            portfolio_data = {
                "blockchain": "evm",
                "timestamp": datetime.now().isoformat(),
                "wallet_address": wallet_address,
                "projects_count": len(projects),
                "projects": projects
            }
            
            print(f"[DeBank] ✓ Scraping completed! Found {len(projects)} projects")
            return portfolio_data
        
        except Exception as e:
            print(f"[DeBank] ✗ Fatal error during scraping: {e}")
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
        print("[DeBank] SCRAPING EVM PORTFOLIO")
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
            
            # Process each wallet
            all_portfolios = []
            
            for idx, wallet_address in enumerate(wallet_addresses, 1):
                print(f"\n[DeBank] {'='*60}")
                print(f"[DeBank] Processing wallet {idx}/{len(wallet_addresses)}")
                print(f"[DeBank] {'='*60}")
                
                # Navigate to DeBank profile page
                if not self.navigate_to_debank(wallet_address):
                    print(f"[DeBank] ✗ Failed to load wallet {wallet_address}, skipping...")
                    all_portfolios.append(None)
                    continue
                
                # Scrape the portfolio
                portfolio_data = self.scrape_current_portfolio(wallet_address)
                all_portfolios.append(portfolio_data)
            
            # Return single portfolio or list based on input
            if return_single:
                return all_portfolios[0] if all_portfolios else None
            else:
                return all_portfolios
        
        except Exception as e:
            print(f"[DeBank] ✗ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("[DeBank] ✓ Driver cleaned up")
            except:
                pass