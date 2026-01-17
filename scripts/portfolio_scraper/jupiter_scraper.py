"""
Jupiter (Solana) Portfolio Scraper with Anti-Detection
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
from datetime import datetime


class JupiterScraper:
    """Scraper for Jupiter (Solana) portfolio with anti-bot detection"""
    
    def __init__(self, debug_port=9222, user_data_dir=None):
        self.debug_port = debug_port
        self.user_data_dir = user_data_dir or os.path.expanduser('~/.chrome_jupiter_scraper')
        self.driver = None
        
    def connect_to_chrome(self):
        """Start Chrome with undetected-chromedriver for anti-detection"""
        print(f"[Jupiter] Starting Chrome with anti-detection...")
        print(f"[Jupiter] Profile directory: {self.user_data_dir}")
        
        try:
            # undetected-chromedriver options
            options = uc.ChromeOptions()
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Start Chrome with anti-detection
            # Force ChromeDriver version 142 to match installed Chrome
            self.driver = uc.Chrome(
                options=options,
                version_main=142,  # Match Chrome 142.x
                use_subprocess=True
            )
            
            print(f"[Jupiter] ✓ Chrome started with anti-detection")
            print(f"[Jupiter] ℹ Profile persists at: {self.user_data_dir}")
            print(f"[Jupiter] ℹ You can manually configure wallet extensions in this Chrome")
            return True
        except Exception as e:
            print(f"[Jupiter] ✗ Failed to start Chrome: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_portfolio(self, wallet_address):
        """Navigate to portfolio page"""
        url = f"https://jup.ag/portfolio/{wallet_address}"
        print(f"[Jupiter] Navigating to {url}...")
        self.driver.get(url)
        
        # Check for captcha
        print("[Jupiter] Checking for captcha...")
        time.sleep(3)  # Give page time to load
        
        try:
            # Look for captcha iframe
            captcha_frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='captcha'], iframe[title*='captcha']")
            if captcha_frames:
                print("[Jupiter] ⚠️  CAPTCHA DETECTED!")
                print("[Jupiter] Please solve the captcha in the Chrome window...")
                print("[Jupiter] Waiting up to 120 seconds for you to complete it...")
                
                # Wait longer for captcha to be solved
                wait_time = 120
                start_time = time.time()
                
                while time.time() - start_time < wait_time:
                    try:
                        # Check if portfolio elements are present (captcha solved)
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "details.platform-detail"))
                        )
                        print("[Jupiter] ✓ Captcha solved! Page loaded successfully")
                        return True
                    except TimeoutException:
                        remaining = int(wait_time - (time.time() - start_time))
                        if remaining > 0 and remaining % 10 == 0:
                            print(f"[Jupiter]    Still waiting... {remaining}s remaining")
                        time.sleep(2)
                        continue
                
                print("[Jupiter] ✗ Captcha timeout - please solve faster next time")
                return False
        except Exception as e:
            print(f"[Jupiter] Captcha check error: {e}")
        
        # Normal page load (no captcha)
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "details.platform-detail"))
            )
            print("[Jupiter] ✓ Page loaded")
            return True
        except TimeoutException:
            print("[Jupiter] ✗ Page load timeout")
            print("[Jupiter] Tip: Make sure you solved any captcha in the Chrome window")
            return False
    
    def parse_numeric_value(self, text):
        """Parse numeric value from text"""
        text = text.strip()
        if text.startswith('<'):
            return 0
        text = text.replace('$', '').replace(',', '')
        try:
            return float(text)
        except ValueError:
            return 0
    
    def extract_token_info(self, cell):
        """Extract token name from cell"""
        try:
            token_elem = cell.find_element(By.CSS_SELECTOR, "p.text-sm")
            return token_elem.text.strip() or "Unknown"
        except NoSuchElementException:
            text = cell.text.strip().split('\n')[0]
            return text if text else "Unknown"
    
    def extract_balance_and_token(self, balance_text):
        """Parse balance text like '46,172 CASH' into numeric balance"""
        lines = balance_text.strip().split('\n')
        if len(lines) >= 1:
            parts = lines[0].strip().rsplit(' ', 1)
            if len(parts) == 2:
                balance_str = parts[0].replace(',', '')
                try:
                    return float(balance_str)
                except ValueError:
                    return 0
        return 0
    
    def extract_yield_value(self, cell):
        """Extract yield percentage as numeric value"""
        try:
            yield_elem = cell.find_element(By.CSS_SELECTOR, "span")
            yield_text = yield_elem.text.strip().replace('%', '').replace('+', '')
            return float(yield_text) if yield_text else 0
        except (NoSuchElementException, ValueError):
            return 0
    
    def scrape_wallet_section(self, section_elem):
        """Scrape wallet section data (similar to farming but without yield column)"""
        wallet_data = {
            "section_type": "Wallet",
            "assets": []
        }
        
        try:
            table = section_elem.find_element(By.CSS_SELECTOR, "table")
            tbodies = table.find_elements(By.TAG_NAME, "tbody")
            
            if len(tbodies) > 0:
                asset_rows = tbodies[0].find_elements(By.CSS_SELECTOR, "tr.transition-colors")
                
                for row in asset_rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 4:
                            # Extract token (column 0), balance (column 1), and value (column 3)
                            # Skip column 2 (Price/24hΔ)
                            asset_info = {
                                "token": self.extract_token_info(cells[0]),
                                "balance": self.extract_balance_and_token(cells[1].text.strip()),
                                "value": self.parse_numeric_value(cells[3].text.strip())
                            }
                            wallet_data["assets"].append(asset_info)
                    except Exception as e:
                        print(f"[Jupiter] Warning: Failed to parse wallet asset row: {e}")
        except Exception as e:
            print(f"[Jupiter] Error scraping wallet section: {e}")
        
        return wallet_data
    
    def scrape_farming_section(self, section_elem):
        """Scrape farming section data"""
        farming_data = {
            "section_type": "Farming",
            "assets": []
        }
        
        try:
            table = section_elem.find_element(By.CSS_SELECTOR, "table")
            tbodies = table.find_elements(By.TAG_NAME, "tbody")
            
            if len(tbodies) > 0:
                asset_rows = tbodies[0].find_elements(By.CSS_SELECTOR, "tr.transition-colors")
                
                for row in asset_rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 4:
                            asset_info = {
                                "token": self.extract_token_info(cells[0]),
                                "balance": self.extract_balance_and_token(cells[1].text.strip()),
                                "yield": self.extract_yield_value(cells[2]),
                                "value": self.parse_numeric_value(cells[3].text.strip())
                            }
                            farming_data["assets"].append(asset_info)
                    except Exception as e:
                        print(f"[Jupiter] Warning: Failed to parse asset row: {e}")
        except Exception as e:
            print(f"[Jupiter] Error scraping farming section: {e}")
        
        return farming_data
    
    def scrape_lending_section(self, section_elem, market_name):
        """Scrape lending section data"""
        lending_data = {
            "section_type": "Lending",
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
                        
                        for row in rows:
                            try:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) >= 5:
                                    asset_info = {
                                        "token": self.extract_token_info(cells[0]),
                                        "balance": self.extract_balance_and_token(cells[1].text.strip()),
                                        "yield": self.extract_yield_value(cells[3]),
                                        "value": self.parse_numeric_value(cells[4].text.strip())
                                    }
                                    lending_data["supplied"].append(asset_info)
                            except Exception as e:
                                print(f"[Jupiter] Warning: Failed to parse supplied row: {e}")
                        tbody_index += 1
                
                elif "borrowed" in thead_text:
                    if tbody_index < len(tbodies):
                        tbody = tbodies[tbody_index]
                        rows = tbody.find_elements(By.CSS_SELECTOR, "tr.transition-colors")
                        
                        for row in rows:
                            try:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) >= 5:
                                    asset_info = {
                                        "token": self.extract_token_info(cells[0]),
                                        "balance": self.extract_balance_and_token(cells[1].text.strip()),
                                        "yield": self.extract_yield_value(cells[3]),
                                        "value": self.parse_numeric_value(cells[4].text.strip())
                                    }
                                    lending_data["borrowed"].append(asset_info)
                            except Exception as e:
                                print(f"[Jupiter] Warning: Failed to parse borrowed row: {e}")
                        tbody_index += 1
        except Exception as e:
            print(f"[Jupiter] Error scraping lending section: {e}")
        
        return lending_data
    
    def scrape_portfolio(self, wallet_address):
        """Main scraping function"""
        print(f"\n{'='*60}")
        print("[Jupiter] SCRAPING SOLANA PORTFOLIO")
        print(f"{'='*60}")
        
        try:
            if not self.navigate_to_portfolio(wallet_address):
                return None
            
            time.sleep(3)
            
            all_details = self.driver.find_elements(By.CSS_SELECTOR, "details.platform-detail")
            print(f"[Jupiter] Found {len(all_details)} total details elements")
            
            projects = []
            first_skipped = False
            
            for idx, project_detail in enumerate(all_details):
                try:
                    open_attr = project_detail.get_attribute("open")
                    if not first_skipped and open_attr is not None and open_attr == "":
                        print(f"[Jupiter] [{idx+1}] Skipping wallet summary section")
                        first_skipped = True
                        continue
                except:
                    pass
                
                try:
                    project_name_elem = project_detail.find_element(By.CSS_SELECTOR, "summary p")
                    project_name = project_name_elem.text.strip()
                    
                    print(f"[Jupiter] [{idx+1}] Processing: {project_name}")
                    
                    project_info = {
                        "project_name": project_name,
                        "sections": []
                    }
                    
                    sections = project_detail.find_elements(By.CSS_SELECTOR, "details.group\\/inner")
                    print(f"[Jupiter]   Found {len(sections)} sections")
                    
                    for section in sections:
                        try:
                            summary_elem = section.find_element(By.CSS_SELECTOR, "summary")
                            summary_text = summary_elem.text.lower()
                            
                            if "wallet" in summary_text:
                                section_data = self.scrape_wallet_section(section)
                                project_info["sections"].append(section_data)
                            elif "farming" in summary_text:
                                section_data = self.scrape_farming_section(section)
                                project_info["sections"].append(section_data)
                            elif "lending" in summary_text:
                                market_name = "Unknown Market"
                                try:
                                    market_elem = summary_elem.find_element(
                                        By.CSS_SELECTOR,
                                        "div.flex.flex-row.items-center.text-sm p"
                                    )
                                    market_name = market_elem.text.strip()
                                except NoSuchElementException:
                                    try:
                                        market_elem = summary_elem.find_element(
                                            By.CSS_SELECTOR,
                                            "p.max-sm\\:hidden"
                                        )
                                        market_name = market_elem.text.strip()
                                    except:
                                        pass
                                
                                section_data = self.scrape_lending_section(section, market_name)
                                project_info["sections"].append(section_data)
                        except Exception as e:
                            print(f"[Jupiter]     Error processing section: {e}")
                            continue
                    
                    projects.append(project_info)
                except Exception as e:
                    print(f"[Jupiter]   Error processing project: {e}")
                    continue
            
            portfolio_data = {
                "blockchain": "solana",
                "timestamp": datetime.now().isoformat(),
                "wallet_address": wallet_address,
                "projects_count": len(projects),
                "projects": projects
            }
            
            print(f"[Jupiter] ✓ Scraping completed! Found {len(projects)} projects")
            return portfolio_data
        except Exception as e:
            print(f"[Jupiter] ✗ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("[Jupiter] ✓ Driver cleaned up")
            except:
                pass