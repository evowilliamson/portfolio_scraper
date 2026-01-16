#!/usr/bin/env python3
"""
Unified Portfolio Flask API - Solana (Jupiter) & EVM (Rabby)

Flask API that scrapes portfolio data from both Jupiter and Rabby.

Usage:
    1. Run this Flask app:
       python portfolio_scraper.py
    
    2. Call the endpoint:
       http://localhost:5000/portfolio?address=YOUR_WALLET_ADDRESS
"""

from portfolio_scraper import run_app


if __name__ == "__main__":
    run_app()
