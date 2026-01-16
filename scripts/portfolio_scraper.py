#!/usr/bin/env python3
"""
Unified Portfolio Flask API - Solana (Jupiter) & EVM (DeBank)

Flask API that scrapes portfolio data from both Jupiter and DeBank.

Usage:
    1. Run this Flask app:
       python portfolio_scraper.py
    
    2. Call the endpoint:
       http://localhost:5000/portfolio?address=YOUR_WALLET_ADDRESS
"""

from flask import Flask, request, jsonify
from pyngrok import ngrok
import os
import sys
import atexit

# Import from portfolio_scraper module
from portfolio_scraper.config import (
    SOLANA_ADDRESSES, EVM_ADDRESSES, SCRAPE_INTERVAL_MINUTES,
    CHROME_DEBUG_PORT, CHROME_PROFILE, FLASK_PORT, FLASK_HOST,
    NGROK_AUTHTOKEN, OUTPUT_DIR
)
from portfolio_scraper.chrome_manager import start_chrome_with_debug, cleanup_chrome
from portfolio_scraper.scheduler import PortfolioScheduler


app = Flask(__name__)

# Global scheduler instance
scheduler = None


@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    """Get cached portfolio data for a wallet address"""
    wallet_address = request.args.get('address')
    
    if not wallet_address:
        all_addresses = SOLANA_ADDRESSES + EVM_ADDRESSES
        return jsonify({
            "error": "Missing 'address' parameter",
            "message": f"Please provide a wallet address.",
            "configured_addresses": all_addresses
        }), 400
    
    # Return cached data
    data = scheduler.get_cached_data(wallet_address)
    if data:
        response_data = data.copy()
        response_data['cached_at'] = scheduler.last_update_time.isoformat() if scheduler.last_update_time else None
        response_data['scrape_interval_minutes'] = SCRAPE_INTERVAL_MINUTES
        return jsonify(response_data), 200
    else:
        all_addresses = SOLANA_ADDRESSES + EVM_ADDRESSES
        if wallet_address in all_addresses:
            return jsonify({
                "error": "Data not yet available",
                "message": "This wallet is configured but data is still being scraped. Please try again in a moment.",
                "configured_addresses": all_addresses
            }), 503
        else:
            return jsonify({
                "error": "Wallet not configured",
                "message": f"This wallet address is not in the configured list.",
                "configured_addresses": all_addresses,
                "cached_wallets": list(scheduler.cached_portfolio_data.keys())
            }), 404


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    status = scheduler.get_status()
    status['status'] = 'ok'
    return jsonify(status), 200


@app.route('/refresh', methods=['POST'])
def refresh():
    """Manually trigger a refresh"""
    scheduler.scrape_and_cache()
    return jsonify({"message": "Refresh triggered"}), 200


def setup_ngrok():
    """Set up ngrok tunnel"""
    ngrok_token = os.environ.get('NGROK_AUTHTOKEN') or NGROK_AUTHTOKEN
    
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)
        print("✓ Ngrok auth token configured")
    
    print()
    
    try:
        ngrok.kill()
        public_url = ngrok.connect(FLASK_PORT, bind_tls=True)
        print("="*70)
        print("🌐 NGROK TUNNEL ACTIVE")
        print("="*70)
        print(f"Public URL: {public_url}")
        print(f"Local URL:  http://localhost:{FLASK_PORT}")
        print()
        print("Configured Wallets:")
        print(f"  Solana ({len(SOLANA_ADDRESSES)}): {', '.join([f'{a[:8]}...' for a in SOLANA_ADDRESSES])}")
        print(f"  EVM ({len(EVM_ADDRESSES)}): {', '.join([f'{a[:8]}...' for a in EVM_ADDRESSES])}")
        print()
        print("API Endpoints:")
        print(f"  {public_url}/portfolio?address=YOUR_WALLET")
        print(f"  {public_url}/health")
        print("="*70)
        print()
    except Exception as e:
        print(f"⚠️  Failed to start ngrok: {e}")
        print(f"Starting without ngrok (localhost only)...")
        print(f"Local endpoint: http://localhost:{FLASK_PORT}/portfolio?address=YOUR_WALLET")
        print()


def main():
    """Main entry point"""
    global scheduler
    
    print("\n" + "="*70)
    print("   UNIFIED PORTFOLIO SCRAPER API - SOLANA & EVM")
    print("="*70)
    
    # Register cleanup handler
    atexit.register(cleanup_chrome)
    
    # Start Chrome with debugging
    if not start_chrome_with_debug(
        debug_port=CHROME_DEBUG_PORT,
        chrome_profile=CHROME_PROFILE,
        copy_profile=True
    ):
        print("\n" + "="*70)
        print("❌ CHROME STARTUP FAILED")
        print("="*70)
        print("\nThe Chrome startup process failed.")
        print("Check the logs above for details.")
        print("="*70)
        sys.exit(1)
    
    print()
    
    # Set up ngrok
    setup_ngrok()
    
    # Create and start scheduler
    scheduler = PortfolioScheduler(
        solana_addresses=SOLANA_ADDRESSES,
        evm_addresses=EVM_ADDRESSES,
        output_dir=OUTPUT_DIR,
        scrape_interval_minutes=SCRAPE_INTERVAL_MINUTES,
        chrome_debug_port=CHROME_DEBUG_PORT
    )
    scheduler.start()
    
    # Start Flask server
    print("🚀 Flask API server starting...")
    print(f"   API returns cached data (auto-refreshes every {SCRAPE_INTERVAL_MINUTES} min)")
    print()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)


if __name__ == "__main__":
    main()