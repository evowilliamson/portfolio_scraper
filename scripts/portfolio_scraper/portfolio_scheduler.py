"""
Background scheduler for automatic portfolio scraping
"""
from apscheduler.schedulers.background import BackgroundScheduler
import json
import time
from datetime import datetime
from .jupiter_scraper import JupiterScraper
from .debank_scraper import DebankScraper
from .utils import is_solana_address
import atexit


class PortfolioScheduler:
    """Manages scheduled portfolio scraping"""
    
    def __init__(self, solana_addresses, evm_addresses, output_dir, 
                 scrape_interval_minutes, chrome_debug_port):
        self.solana_addresses = solana_addresses
        self.evm_addresses = evm_addresses
        self.output_dir = output_dir
        self.scrape_interval_minutes = scrape_interval_minutes
        self.chrome_debug_port = chrome_debug_port
        
        self.cached_portfolio_data = {}
        self.last_update_time = None
        self.jupiter_scraper = None
        self.scheduler = None
    
    def get_jupiter_scraper(self):
        """Get or create Jupiter scraper instance"""
        if self.jupiter_scraper is None:
            self.jupiter_scraper = JupiterScraper(debug_port=self.chrome_debug_port)
            if not self.jupiter_scraper.connect_to_chrome():
                return None
        return self.jupiter_scraper
    
    def scrape_and_cache(self):
        """Background task: Scrape all configured wallets and cache results"""
        all_addresses = self.solana_addresses + self.evm_addresses
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Starting background scrape for {len(all_addresses)} wallets...")
        
        success_count = 0
        
        # Scrape Solana addresses
        if self.solana_addresses:
            jupiter = self.get_jupiter_scraper()
            if jupiter:
                for idx, wallet_address in enumerate(self.solana_addresses, 1):
                    print(f"\n   [{idx}/{len(self.solana_addresses)}] Scraping Solana wallet: {wallet_address[:8]}...{wallet_address[-8:]}")
                    portfolio_data = jupiter.scrape_portfolio(wallet_address)
                    
                    if portfolio_data:
                        self.cached_portfolio_data[wallet_address] = portfolio_data
                        output_file = f"{self.output_dir}/solana_portfolio_{wallet_address[:8]}.json"
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
                        
                        projects_count = len(portfolio_data.get('projects', []))
                        print(f"      ✓ Scraped successfully - {projects_count} projects")
                        success_count += 1
                    else:
                        print(f"      ✗ Scraping failed")
        
        # Scrape EVM addresses
        for idx, wallet_address in enumerate(self.evm_addresses, 1):
            print(f"\n   [{idx}/{len(self.evm_addresses)}] Scraping EVM wallet: {wallet_address[:8]}...{wallet_address[-8:]}")
            
            max_retries = 2
            retry_count = 0
            portfolio_data = None
            
            while retry_count <= max_retries and portfolio_data is None:
                if retry_count > 0:
                    print(f"      ⟳ Retry attempt {retry_count}/{max_retries}...")
                    time.sleep(3)
                
                debank = DebankScraper()
                portfolio_data = debank.scrape_portfolio(wallet_address)
                retry_count += 1
            
            if portfolio_data:
                self.cached_portfolio_data[wallet_address] = portfolio_data
                output_file = f"{self.output_dir}/evm_portfolio_{wallet_address[:8]}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
                
                projects_count = len(portfolio_data.get('projects', []))
                print(f"      ✓ Scraped successfully - {projects_count} projects")
                success_count += 1
            else:
                print(f"      ✗ Scraping failed after {max_retries} retries")
        
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