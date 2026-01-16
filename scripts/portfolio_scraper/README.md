# Portfolio Scraper Package

Modular portfolio scraper for Solana (Jupiter) and EVM (DeBank) portfolios.

## Structure

```
portfolio_scraper/
├── __init__.py           # Package exports
├── config.py             # Configuration constants
├── utils.py              # Utility functions
├── chrome_manager.py     # Chrome browser management
├── jupiter_scraper.py    # Solana/Jupiter scraper
├── debank_scraper.py     # EVM/DeBank scraper
├── scheduler.py          # Background scraping scheduler
├── flask_app.py          # Flask API routes and app setup
└── README.md             # This file
```

## Modules

### `config.py`
Contains all configuration constants:
- Wallet addresses (SOLANA_ADDRESSES, EVM_ADDRESSES)
- Scraping intervals
- Chrome settings
- Flask/ngrok configuration
- Output directories

### `utils.py`
Utility functions:
- `is_solana_address()` - Detect Solana wallet format
- `is_evm_address()` - Detect EVM wallet format
- `check_chrome_debug_port()` - Check Chrome debug port availability
- `kill_all_chrome_processes()` - Clean Chrome process cleanup

### `chrome_manager.py`
Chrome browser lifecycle management:
- `start_chrome_with_debug()` - Start Chrome with remote debugging
- `cleanup_chrome()` - Clean shutdown of Chrome
- Profile copying and management

### `jupiter_scraper.py`
Solana portfolio scraping via Jupiter:
- `JupiterScraper` class
- Connects to existing Chrome debug session
- Scrapes farming, lending, and yield data

### `debank_scraper.py`
EVM portfolio scraping via DeBank:
- `DebankScraper` class
- Creates headless Chrome instances
- Scrapes lending, yield, and deposit data

### `scheduler.py`
Background scraping automation:
- `PortfolioScheduler` class
- Automatic periodic scraping
- Data caching and JSON export
- Retry logic for failed scrapes

### `flask_app.py`
Flask API server:
- `create_app()` - Create Flask app instance
- `run_app()` - Main entry point
- Routes: `/portfolio`, `/health`, `/refresh`
- ngrok tunnel setup

## Usage

### As a script
```bash
cd /home/ivo/code/portfolio_scraper
source .venv/bin/activate
python scripts/portfolio_scraper.py
```

### As a module
```python
from portfolio_scraper import run_app

if __name__ == "__main__":
    run_app()
```

### Import specific components
```python
from portfolio_scraper import (
    JupiterScraper,
    DebankScraper,
    PortfolioScheduler,
    SOLANA_ADDRESSES,
    EVM_ADDRESSES
)

# Use components individually
scraper = JupiterScraper(debug_port=9222)
scraper.connect_to_chrome()
data = scraper.scrape_portfolio("YOUR_WALLET_ADDRESS")
```

## Configuration

Edit `config.py` to customize:
- Wallet addresses to scrape
- Scrape interval (minutes)
- Chrome profile and debug port
- Flask host/port
- Output directory
- ngrok auth token

## API Endpoints

### GET /portfolio?address=WALLET_ADDRESS
Get cached portfolio data for a wallet.

### GET /health
Health check and status information.

### POST /refresh
Manually trigger a scrape refresh.

## Dependencies

See `requirements.txt` in the project root:
- Flask
- pyngrok
- APScheduler
- selenium
- psutil

## Environment Variables

All configuration is loaded from a `.env` file in the project root.

### Required Variables
- `SOLANA_ADDRESSES` - Comma-separated list of Solana wallet addresses
- `EVM_ADDRESSES` - Comma-separated list of EVM wallet addresses

### Optional Variables
- `SCRAPE_INTERVAL_MINUTES` - Default: 15
- `CHROME_DEBUG_PORT` - Default: 9222
- `CHROME_STARTUP_TIMEOUT` - Default: 30
- `CHROME_PROFILE` - Default: "Profile 4"
- `FLASK_HOST` - Default: "0.0.0.0"
- `FLASK_PORT` - Default: 5000
- `NGROK_AUTHTOKEN` - Optional ngrok authentication token
- `OUTPUT_DIR` - Default: "/home/ivo/code/defi-yields/feeds/temp"

### Setup
```bash
cp .env.example .env
# Edit .env with your values
```

**Security:** The `.env` file is gitignored and should never be committed.
