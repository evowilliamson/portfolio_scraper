"""
Jupiter (Solana) Portfolio Scraper
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from datetime import datetime


class JupiterScraper:
    """Scraper for Jupiter (Solana) portfolio"""
    
    def __init__(self, debug_port=9222):
        self.debug_port = debug_port
        self.driver = None
        
    def connect_to_chrome(self):
        """Connect to existing Chrome debugging session"""
        print(f"[Jupiter] Connecting to Chrome on debug port {self.debug_port}...")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print(f"[Jupiter] ✓ Connected successfully")
            return True
        except Exception as e:
            print(f"[Jupiter] ✗ Failed to connect: {e}")
            return False
    
    def navigate_to_portfolio(self, wallet_address):
        """Navigate to portfolio page"""
        url = f"https://jup.ag/portfolio/{wallet_address}"
        print(f"[Jupiter] Navigating to {url}...")
        self.driver.get(url)
        
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "details.platform-detail"))
            )
            print("[Jupiter] ✓ Page loaded")
            return True
        except TimeoutException:
            print("[Jupiter] ✗ Page load timeout")
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
                    
                    if project_name.lower() == "holdings":
                        print(f"[Jupiter] [{idx+1}] Skipping Holdings project")
                        continue
                    
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
                            
                            if "farming" in summary_text:
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
