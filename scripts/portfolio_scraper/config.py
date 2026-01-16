"""
Configuration for Portfolio Scraper

Contains all configuration constants for the application.
"""

import os

# Wallet addresses to scrape automatically
SOLANA_ADDRESSES = [
    "ERKdjoj6UHoPiwXv784SAnHowc4E5AJFUErWJCCFtga",
    "ARdaJWDopB4J8ukZe7q3s6yZmJjoTF3PhoeeYYVQ9sWh"
]

EVM_ADDRESSES = [
    "0xb77cb8f81a0f704e1e858eba57c67c072abbfcad",
    "0x302d129011fb164d8d5fe93cd1e8795d61c4f76f"
]

# Scraping configuration
SCRAPE_INTERVAL_MINUTES = 15

# Chrome configuration
CHROME_DEBUG_PORT = 9222
CHROME_STARTUP_TIMEOUT = 30
CHROME_PROFILE = "Profile 4"

# Flask configuration
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

# ngrok configuration
NGROK_AUTHTOKEN = os.environ.get('NGROK_AUTHTOKEN', '38IGBNqHGnyaKnmhnzcsdNJHXXa_3a2EKxJ6ev19sbiUhKYBv')

# Output directory for JSON files
OUTPUT_DIR = "/home/ivo/code/defi-yields/feeds/temp"
