"""
Background scheduler for automatic portfolio scraping
"""
from apscheduler.schedulers.background import BackgroundScheduler
import json
import time
import atexit
from datetime import datetime
from .jupiter_scraper import JupiterScraper
from .debank_scraper import DebankScraper
from .utils import is_solana_address
from .config import OUTPUT_DIR


class PortfolioScheduler:
    """Manages scheduled portfolio scraping"""
    
    def __init__(self, solana_addresses, evm_addresses, scrape_interval_minutes, chrome_debug_port):
        self.solana_addresses = solana_addresses
        self.evm_addresses = evm_addresses
        self.scrape_interval_minutes = scrape_interval_minutes
        self.chrome_debug_port = chrome_debug_port
        
        self.cached_portfolio_data = {}
        self.last_update_time = None
        self.jupiter_scraper = None
        self.debank_scraper = None
        self.scheduler = None
    
    def get_jupiter_scraper(self):
        """Get or create Jupiter scraper instance with health check"""
        # Check if existing scraper is alive
        if self.jupiter_scraper is not None:
            if not self.jupiter_scraper.is_driver_alive():
                print("[Scheduler] ⚠️ Jupiter driver is stale, reconnecting...")
                try:
                    self.jupiter_scraper.cleanup()
                except:
                    pass
                self.jupiter_scraper = None
        
        # Create new scraper if needed
        if self.jupiter_scraper is None:
            self.jupiter_scraper = JupiterScraper(debug_port=self.chrome_debug_port)
            if not self.jupiter_scraper.connect_to_chrome():
                return None
        
        return self.jupiter_scraper
    
    def get_debank_scraper(self):
        """Get or create DeBank scraper instance with health check"""
        # Check if existing scraper is alive
        if self.debank_scraper is not None:
            if not self.debank_scraper.is_driver_alive():
                print("[Scheduler] ⚠️ DeBank driver is stale, reconnecting...")
                try:
                    self.debank_scraper.cleanup()
                except:
                    pass
                self.debank_scraper = None
        
        # Create new scraper if needed
        if self.debank_scraper is None:
            self.debank_scraper = DebankScraper(debug_port=self.chrome_debug_port)
            if not self.debank_scraper.connect_to_chrome():
                return None
        
        return self.debank_scraper
    
    def scrape_and_cache(self):
        """Background task: Scrape all configured wallets and cache results"""
        all_addresses = self.solana_addresses + self.evm_addresses
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting background scrape for {len(all_addresses)} wallets...")
        
        success_count = 0
        
        # Scrape Solana addresses (FIRST)
        if self.solana_addresses:
            jupiter = self.get_jupiter_scraper()
            if jupiter:
                for idx, wallet_address in enumerate(self.solana_addresses, 1):
                    print(f"\n   [{idx}/{len(self.solana_addresses)}] Scraping Solana wallet: {wallet_address[:8]}...{wallet_address[-8:]}")
                    portfolio_data = jupiter.scrape_portfolio(wallet_address)
                    
                    if portfolio_data:
                        self.cached_portfolio_data[wallet_address] = portfolio_data
                        output_file = f"{OUTPUT_DIR}/solana_portfolio_{wallet_address[:8]}.json"
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
                        
                        projects_count = len(portfolio_data.get('projects', []))
                        print(f"      ✓ Scraped successfully - {projects_count} projects")
                        success_count += 1
                    else:
                        print(f"      ✗ Scraping failed")
            else:
                print(f"\n   ✗ Failed to initialize Jupiter scraper")
        
        # Scrape EVM addresses using DeBank (SECOND)
        if self.evm_addresses:
            debank = self.get_debank_scraper()
            if debank:
                for idx, wallet_address in enumerate(self.evm_addresses, 1):
                    print(f"\n   [{idx}/{len(self.evm_addresses)}] Scraping EVM wallet: {wallet_address[:8]}...{wallet_address[-8:]}")
                    
                    portfolio_data = debank.scrape_portfolio(wallet_address)
                    
                    if portfolio_data:
                        self.cached_portfolio_data[wallet_address] = portfolio_data
                        output_file = f"{OUTPUT_DIR}/evm_portfolio_{wallet_address[:8]}.json"
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
                        
                        projects_count = len(portfolio_data.get('projects', []))
                        print(f"      ✓ Scraped successfully - {projects_count} projects")
                        success_count += 1
                    else:
                        print(f"      ✗ Scraping failed")
            else:
                print(f"\n   ✗ Failed to initialize DeBank scraper")
        
        if success_count > 0:
            self.last_update_time = datetime.now()
            print(f"\n   ✓ Completed: {success_count}/{len(all_addresses)} wallets scraped successfully")
        else:
            print(f"\n   ✗ Failed: No wallets were scraped successfully")
    
    def start(self):
        """Start the background scheduler"""
        print(f"⏰ Setting up automatic scraping (every {self.scrape_interval_minutes} minutes)...")
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            func=self.scrape_and_cache,
            trigger="interval",
            minutes=self.scrape_interval_minutes,
            id='portfolio_scraper',
            name='Scrape Portfolio',
            replace_existing=True
        )
        self.scheduler.start()
        print("   ✓ Scheduler started")
        print()
        
        # Register shutdown
        atexit.register(lambda: self.scheduler.shutdown())
        
        # Initial scrape
        print("🔄 Performing initial scrape...")
        self.scrape_and_cache()
        print()
    
    def get_cached_data(self, wallet_address):
        """Get cached portfolio data for a wallet"""
        return self.cached_portfolio_data.get(wallet_address)
    
    def get_status(self):
        """Get scheduler status"""
        all_addresses = self.solana_addresses + self.evm_addresses
        wallet_status = {}
        
        for wallet in all_addresses:
            blockchain_type = "solana" if is_solana_address(wallet) else "evm"
            short_addr = f"{wallet[:8]}...{wallet[-8:]}"
            wallet_status[short_addr] = {
                "full_address": wallet,
                "blockchain": blockchain_type,
                "cached": wallet in self.cached_portfolio_data,
                "projects": len(self.cached_portfolio_data.get(wallet, {}).get('projects', []))
            }
        
        return {
            "last_update": self.last_update_time.isoformat() if self.last_update_time else None,
            "configured_wallets": len(all_addresses),
            "solana_wallets": len(self.solana_addresses),
            "evm_wallets": len(self.evm_addresses),
            "cached_wallets": len(self.cached_portfolio_data),
            "scrape_interval_minutes": self.scrape_interval_minutes,
            "wallet_status": wallet_status
        }