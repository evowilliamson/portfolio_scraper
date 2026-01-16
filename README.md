# Portfolio Scraper

Unified portfolio scraper for Solana (Jupiter) and EVM (DeBank) wallets with Flask API.

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your wallet addresses and tokens
nano .env  # or use your preferred editor

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the scraper
python scripts/portfolio_scraper.py
```

## Project Structure

```
portfolio_scraper/
├── .venv/                          # Virtual environment
├── scripts/
│   ├── portfolio_scraper.py        # Main entry point
│   └── portfolio_scraper/          # Modular package
│       ├── __init__.py
│       ├── config.py               # Configuration
│       ├── utils.py                # Utility functions
│       ├── chrome_manager.py       # Chrome lifecycle
│       ├── jupiter_scraper.py      # Solana scraper
│       ├── debank_scraper.py       # EVM scraper
│       ├── scheduler.py            # Background scheduler
│       ├── flask_app.py            # Flask API
│       └── README.md               # Package documentation
├── requirements.txt                # Python dependencies
├── .gitignore
└── README.md                       # This file
```

## Features

- **Multi-chain support**: Solana (Jupiter) and EVM (DeBank)
- **Automatic scraping**: Background scheduler with configurable intervals
- **REST API**: Flask endpoints for portfolio data access
- **Public access**: ngrok tunnel for external access
- **Data caching**: JSON export and in-memory caching
- **Retry logic**: Automatic retries for failed scrapes

## Configuration

Configuration is managed via a `.env` file (not committed to git):

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your values:**
   ```bash
   # Wallet addresses (comma-separated)
   SOLANA_ADDRESSES=wallet1,wallet2
   EVM_ADDRESSES=0xwallet1,0xwallet2
   
   # Scraping interval (minutes)
   SCRAPE_INTERVAL_MINUTES=15
   
   # Chrome settings
   CHROME_DEBUG_PORT=9222
   CHROME_PROFILE=Profile 4
   
   # Flask settings
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   
   # ngrok token (optional)
   NGROK_AUTHTOKEN=your_token_here
   
   # Output directory
   OUTPUT_DIR=/path/to/output
   ```

> **Note:** Never commit `.env` to git. It's already in `.gitignore`.

## API Endpoints

### GET /portfolio?address=WALLET_ADDRESS
Returns cached portfolio data for the specified wallet.

**Response:**
```json
{
  "blockchain": "solana",
  "timestamp": "2026-01-16T10:00:00",
  "wallet_address": "...",
  "projects_count": 3,
  "projects": [...]
}
```

### GET /health
Returns scraper status and health information.

### POST /refresh
Manually triggers a scrape refresh for all configured wallets.

## Development

### Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running
```bash
# From project root
python scripts/portfolio_scraper.py

# Or from scripts directory
cd scripts
python portfolio_scraper.py
```

## Dependencies

- Flask >= 3.0
- pyngrok >= 7.0
- APScheduler >= 3.10
- selenium >= 4.0
- psutil >= 5.9

## License

Private project
