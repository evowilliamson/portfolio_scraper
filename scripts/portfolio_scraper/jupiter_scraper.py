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

from .jupiter.sections import (
    scrape_farming_section,
    scrape_lending_section,
    scrape_wallet_section,
)

class JupiterScraper:
    """Scraper for Jupiter (Solana) portfolio with anti-bot detection"""
    
    def __init__(self, debug_port=None, user_data_dir=None):
        self.driver = None
        self.debug_port = debug_port  # Not used anymore, kept for compatibility
        self.user_data_dir = user_data_dir or os.path.expanduser('~/.chrome_jupiter_scraper')
        self.min_usd_value = 5  # Minimum USD value threshold

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
            # Force ChromeDriver version 144 to match installed Chrome
            self.driver = uc.Chrome(
                options=options,
                version_main=144,  # Match Chrome 144.x
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
                                print(f"[Jupiter]   Processing Wallet section")
                                section_data = scrape_wallet_section(section)
                                project_info["sections"].append(section_data)
                            elif "farming" in summary_text:
                                section_data = scrape_farming_section(section)
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
                                
                                section_data = scrape_lending_section(section, market_name)
                                project_info["sections"].append(section_data)
                        except Exception as e:
                            print(f"[Jupiter]     Error processing section: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    projects.append(project_info)
                except Exception as e:
                    print(f"[Jupiter]   Error processing project: {e}")
                    import traceback
                    traceback.print_exc()
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