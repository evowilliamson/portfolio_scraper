"""
DeBank (EVM) Portfolio Scraper
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from datetime import datetime


class DebankScraper:
    """Scraper for DeBank (EVM) portfolio"""
    
    def __init__(self):
        self.driver = None
    
    def create_headless_browser(self):
        """Create headless Chrome browser"""
        print("[DeBank] Creating headless browser...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("[DeBank] ✓ Browser created")
            return True
        except Exception as e:
            print(f"[DeBank] ✗ Failed to create browser: {e}")
            return False
    
    def navigate_to_portfolio(self, wallet_address):
        """Navigate to DeBank portfolio page"""
        url = f"https://debank.com/profile/{wallet_address}"
        print(f"[DeBank] Navigating to {url}...")
        self.driver.get(url)
        
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.Project_project__GCrhx, div.TokenWallet_container__FUGTE"))
            )
            print("[DeBank] ✓ Initial elements loaded")
            
            time.sleep(5)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            print("[DeBank] ✓ Page fully loaded")
            return True
        except TimeoutException:
            print("[DeBank] ✗ Page load timeout")
            return False
    
    def parse_numeric_value(self, text):
        """Parse numeric value from text"""
        text = text.strip()
        if text.startswith('<') or text.startswith('>'):
            return 0
        text = text.replace('$', '').replace(',', '')
        try:
            return float(text)
        except ValueError:
            return 0
    
    def extract_balance_value(self, balance_text):
        """Extract numeric balance from text"""
        parts = balance_text.strip().split()
        if parts:
            return parts[0]
        return balance_text
    
    def extract_project_info(self, project_elem):
        """Extract project name, chain, and total value"""
        project_info = {
            "project_name": "Unknown",
            "chain": "unknown",
            "total_value": "$0"
        }
        
        try:
            project_id = project_elem.get_attribute("id") or ""
            if "_" in project_id:
                project_info["chain"] = project_id.split("_")[0]
            
            name_elem = project_elem.find_element(By.CSS_SELECTOR, "span.ProjectTitle_protocolLink__4Yqn3")
            project_info["project_name"] = name_elem.text.strip()
            
            value_elem = project_elem.find_element(By.CSS_SELECTOR, "div.projectTitle-number")
            project_info["total_value"] = value_elem.text.strip()
        except Exception as e:
            print(f"[DeBank]     Warning: Failed to extract project info: {e}")
        
        return project_info
    
    def scrape_lending_section(self, panel_elem):
        """Scrape Lending section"""
        lending_data = {
            "section_type": "Lending",
            "supplied": [],
            "borrowed": []
        }
        
        try:
            try:
                WebDriverWait(panel_elem, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.table_header__onfbK"))
                )
            except TimeoutException:
                print("[DeBank]     No content found in lending section")
                return lending_data
            
            tables = panel_elem.find_elements(By.CSS_SELECTOR, "div.table_header__onfbK")
            print(f"[DeBank]       Found {len(tables)} lending tables")
            
            for table_idx, table_header in enumerate(tables):
                header_text = table_header.text.lower()
                
                try:
                    parent = table_header.find_element(By.XPATH, "..")
                    content_div = parent.find_element(By.CSS_SELECTOR, "div.table_content__53NAZ")
                    rows = content_div.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
                    
                    print(f"[DeBank]         Table '{header_text}': {len(rows)} rows")
                    
                    for row_idx, row in enumerate(rows):
                        try:
                            cells = row.find_elements(By.XPATH, "./div")
                            if len(cells) >= 3:
                                token = None
                                try:
                                    token_elem = cells[0].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                                    token = token_elem.text.strip()
                                except NoSuchElementException:
                                    try:
                                        token_elem = cells[0].find_element(By.CSS_SELECTOR, "div.LabelWithIcon_container__-yKOy")
                                        token = token_elem.text.strip()
                                    except NoSuchElementException:
                                        token = cells[0].text.strip().split('\n')[0]
                                
                                balance_text = cells[1].text.strip().split('\n')[0]
                                balance_value = self.extract_balance_value(balance_text)
                                
                                usd_text = cells[2].text.strip()
                                usd_value = self.parse_numeric_value(usd_text)
                                
                                if token and balance_value:
                                    asset_info = {
                                        "token": token,
                                        "balance": balance_value,
                                        "usd_value": usd_value
                                    }
                                    
                                    if "supplied" in header_text:
                                        lending_data["supplied"].append(asset_info)
                                        print(f"[DeBank]         ✓ Supplied: {token} - ${usd_value}")
                                    elif "borrowed" in header_text:
                                        lending_data["borrowed"].append(asset_info)
                                        print(f"[DeBank]         ✓ Borrowed: {token} - ${usd_value}")
                                
                        except Exception as e:
                            print(f"[DeBank]         Warning: Failed to parse row {row_idx}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"[DeBank]       Warning: Failed to find content for table: {e}")
                    continue
                    
        except Exception as e:
            print(f"[DeBank]     Error scraping lending section: {e}")
        
        return lending_data
    
    def scrape_yield_section(self, panel_elem):
        """Scrape Yield section"""
        yield_data = {
            "section_type": "Yield",
            "assets": []
        }
        
        try:
            try:
                WebDriverWait(panel_elem, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.table_content__53NAZ"))
                )
            except TimeoutException:
                print("[DeBank]     No content found in yield section")
                return yield_data
            
            content_div = panel_elem.find_element(By.CSS_SELECTOR, "div.table_content__53NAZ")
            rows = content_div.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
            
            print(f"[DeBank]       Found {len(rows)} yield rows")
            
            for row_idx, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    if len(cells) >= 4:
                        identifier = cells[0].text.strip()
                        
                        pool = None
                        try:
                            pool_elem = cells[1].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            try:
                                pool_elem = cells[1].find_element(By.CSS_SELECTOR, "div.LabelWithIcon_container__-yKOy")
                                pool = pool_elem.text.strip()
                            except NoSuchElementException:
                                pool = cells[1].text.strip().split('\n')[0]
                        
                        balance_text = cells[2].text.strip().split('\n')[0]
                        balance_value = self.extract_balance_value(balance_text)
                        
                        usd_text = cells[3].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                        if pool and balance_value:
                            asset_info = {
                                "identifier": identifier,
                                "pool": pool,
                                "balance": balance_value,
                                "usd_value": usd_value
                            }
                            yield_data["assets"].append(asset_info)
                            print(f"[DeBank]       ✓ Parsed yield: {pool} - ${usd_value}")
                        
                except Exception as e:
                    print(f"[DeBank]       Warning: Failed to parse yield row {row_idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[DeBank]     Error scraping yield section: {e}")
        
        return yield_data
    
    def scrape_deposit_section(self, panel_elem):
        """Scrape Deposit section"""
        deposit_data = {
            "section_type": "Deposit",
            "assets": []
        }
        
        try:
            try:
                WebDriverWait(panel_elem, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.table_content__53NAZ"))
                )
            except TimeoutException:
                print("[DeBank]     No content found in deposit section")
                return deposit_data
            
            content_div = panel_elem.find_element(By.CSS_SELECTOR, "div.table_content__53NAZ")
            rows = content_div.find_elements(By.CSS_SELECTOR, "div.table_contentRow__Mi3k5")
            
            print(f"[DeBank]       Found {len(rows)} deposit rows")
            
            for row_idx, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.XPATH, "./div")
                    if len(cells) >= 3:
                        pool = None
                        try:
                            pool_elem = cells[0].find_element(By.CSS_SELECTOR, "a.utils_detailLink__XnB7N")
                            pool = pool_elem.text.strip()
                        except NoSuchElementException:
                            try:
                                pool_elem = cells[0].find_element(By.CSS_SELECTOR, "div.LabelWithIcon_container__-yKOy")
                                pool = pool_elem.text.strip()
                            except NoSuchElementException:
                                pool = cells[0].text.strip().split('\n')[0]
                        
                        if not pool:
                            print(f"[DeBank]       Warning: Could not extract pool name from row {row_idx}")
                            continue
                        
                        balance_text = cells[1].text.strip().split('\n')[0]
                        balance_value = self.extract_balance_value(balance_text)
                        
                        usd_text = cells[2].text.strip()
                        usd_value = self.parse_numeric_value(usd_text)
                        
                        if pool and balance_value:
                            asset_info = {
                                "pool": pool,
                                "balance": balance_value,
                                "usd_value": usd_value
                            }
                            deposit_data["assets"].append(asset_info)
                            print(f"[DeBank]       ✓ Parsed deposit: {pool} - ${usd_value}")
                        
                except Exception as e:
                    print(f"[DeBank]       Warning: Failed to parse deposit row {row_idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[DeBank]     Error scraping deposit section: {e}")
        
        return deposit_data
    
    def scrape_portfolio(self, wallet_address):
        """Main scraping function"""
        print(f"\n{'='*60}")
        print("[DeBank] SCRAPING EVM PORTFOLIO")
        print(f"{'='*60}")
        
        try:
            if not self.create_headless_browser():
                return None
            
            if not self.navigate_to_portfolio(wallet_address):
                if self.driver:
                    self.driver.quit()
                return None
            
            try:
                wallet_section = self.driver.find_element(By.CSS_SELECTOR, "div.TokenWallet_container__FUGTE")
                print("[DeBank] ✓ Found wallet section (skipping)")
            except:
                print("[DeBank] ℹ No wallet section found")
            
            project_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.Project_project__GCrhx")
            print(f"[DeBank] Found {len(project_elements)} projects")
            
            projects = []
            
            for idx, project_elem in enumerate(project_elements, 1):
                try:
                    project_title = project_elem.find_element(By.CSS_SELECTOR, "div.ProjectTitle_projectTitle__yC5VD")
                    project_info = self.extract_project_info(project_title)
                    
                    print(f"[DeBank] [{idx}] Processing: {project_info['project_name']} ({project_info['chain']}) - {project_info['total_value']}")
                    
                    project_data = {
                        "project_name": project_info["project_name"],
                        "chain": project_info["chain"],
                        "total_value": project_info["total_value"],
                        "sections": []
                    }
                    
                    panels = project_elem.find_elements(By.CSS_SELECTOR, "div.Panel_container__Vltd1")
                    print(f"[DeBank]   Found {len(panels)} sections")
                    
                    for panel in panels:
                        try:
                            bookmark = panel.find_element(By.CSS_SELECTOR, "div.BookMark_bookmark__UG5a4")
                            section_type = bookmark.text.strip()
                            
                            print(f"[DeBank]     Processing section: {section_type}")
                            
                            if section_type == "Lending":
                                section_data = self.scrape_lending_section(panel)
                                project_data["sections"].append(section_data)
                            elif section_type == "Yield":
                                section_data = self.scrape_yield_section(panel)
                                project_data["sections"].append(section_data)
                            elif section_type == "Deposit":
                                section_data = self.scrape_deposit_section(panel)
                                project_data["sections"].append(section_data)
                        except Exception as e:
                            print(f"[DeBank]     Error processing section: {e}")
                            continue
                    
                    projects.append(project_data)
                except Exception as e:
                    print(f"[DeBank]   Error processing project: {e}")
                    continue
            
            portfolio_data = {
                "blockchain": "evm",
                "timestamp": datetime.now().isoformat(),
                "wallet_address": wallet_address,
                "projects_count": len(projects),
                "projects": projects
            }
            
            print(f"[DeBank] ✓ Scraping completed! Found {len(projects)} projects")
            
            if self.driver:
                self.driver.quit()
            
            return portfolio_data
        except Exception as e:
            print(f"[DeBank] ✗ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            if self.driver:
                self.driver.quit()
            return None