"""
Configuration for Portfolio Scraper

Contains all configuration constants loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def _parse_list(env_var: str, default: list = None) -> list:
    """Parse comma-separated list from environment variable"""
    value = os.getenv(env_var, '')
    if not value.strip():
        return default or []
    return [item.strip() for item in value.split(',') if item.strip()]


def _parse_int(env_var: str, default: int) -> int:
    """Parse integer from environment variable"""
    value = os.getenv(env_var, '')
    if not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


# Wallet addresses to scrape automatically
SOLANA_ADDRESSES = _parse_list('SOLANA_ADDRESSES', default=[])
EVM_ADDRESSES = _parse_list('EVM_ADDRESSES', default=[])

# Scraping configuration
SCRAPE_INTERVAL_MINUTES = _parse_int('SCRAPE_INTERVAL_MINUTES', default=15)

# Chrome configuration
CHROME_DEBUG_PORT = _parse_int('CHROME_DEBUG_PORT', default=9222)
CHROME_STARTUP_TIMEOUT = _parse_int('CHROME_STARTUP_TIMEOUT', default=30)
CHROME_PROFILE = os.getenv('CHROME_PROFILE', 'Profile 4')

# Flask configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = _parse_int('FLASK_PORT', default=5000)

# ngrok configuration
NGROK_AUTHTOKEN = os.getenv('NGROK_AUTHTOKEN')

# Output directory for JSON files
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/home/ivo/code/defi-yields/feeds/temp')
