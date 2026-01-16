"""
Portfolio Scraper Package

Modular scraper for Solana (Jupiter) and EVM (DeBank) portfolios
"""

from .config import (
    SOLANA_ADDRESSES,
    EVM_ADDRESSES,
    SCRAPE_INTERVAL_MINUTES,
    CHROME_DEBUG_PORT,
    CHROME_PROFILE,
    FLASK_PORT,
    FLASK_HOST,
    OUTPUT_DIR,
    NGROK_AUTHTOKEN
)

from .utils import (
    is_solana_address,
    is_evm_address,
    check_chrome_debug_port,
    kill_all_chrome_processes
)

from .jupiter_scraper import JupiterScraper
from .rabby_scraper import RabbyScraper
from .chrome_manager import start_chrome_with_debug, cleanup_chrome
from .scheduler import PortfolioScheduler
from .flask_app import create_app, run_app

__version__ = '1.0.0'
__all__ = [
    'SOLANA_ADDRESSES',
    'EVM_ADDRESSES',
    'SCRAPE_INTERVAL_MINUTES',
    'CHROME_DEBUG_PORT',
    'CHROME_PROFILE',
    'FLASK_PORT',
    'FLASK_HOST',
    'OUTPUT_DIR',
    'NGROK_AUTHTOKEN',
    'is_solana_address',
    'is_evm_address',
    'check_chrome_debug_port',
    'kill_all_chrome_processes',
    'JupiterScraper',
    'RabbyScraper',
    'PortfolioScheduler',
    'start_chrome_with_debug',
    'cleanup_chrome',
    'create_app',
    'run_app'
]
