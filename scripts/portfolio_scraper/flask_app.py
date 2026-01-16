"""
Flask API for portfolio scraping
"""
from flask import Flask, request, jsonify
from pyngrok import ngrok
import os
import atexit
from .config import (
    SOLANA_ADDRESSES, 
    EVM_ADDRESSES, 
    SCRAPE_INTERVAL_MINUTES,
    CHROME_DEBUG_PORT,
    CHROME_PROFILE,
    FLASK_HOST,
    FLASK_PORT,
    NGROK_AUTHTOKEN
)
from .chrome_manager import start_chrome_with_debug, cleanup_chrome
from .scheduler import PortfolioScheduler
from .utils import is_solana_address, check_chrome_debug_port


def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    
    @app.route('/portfolio', methods=['GET'])
    def get_portfolio():
        """Get cached portfolio data for a wallet address"""
        from flask import current_app
        scheduler = current_app.scheduler
        
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
        from flask import current_app
        scheduler = current_app.scheduler
        
        status = scheduler.get_status()
        status['status'] = 'ok'
        return jsonify(status), 200
    
    @app.route('/refresh', methods=['POST'])
    def refresh():
        """Manually trigger a refresh"""
        from flask import current_app
        scheduler = current_app.scheduler
        
        scheduler.scrape_and_cache()
        return jsonify({"message": "Refresh triggered"}), 200
    
    return app


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


def run_app():
    """Main entry point to run the Flask app"""
    print("\n" + "="*70)
    print("   UNIFIED PORTFOLIO SCRAPER API - SOLANA & EVM")
    print("="*70)
    
    # ===========================================================================
    # AUTOMATIC MODE: Each scraper starts its own Chrome
    # ===========================================================================
    # Jupiter scraper → starts Chrome with undetected-chromedriver
    # Rabby scraper   → starts Chrome with undetected-chromedriver
    #
    # No manual Chrome startup needed!
    # Profiles persist at:
    #   - ~/.chrome_jupiter_scraper (for Solana/Jupiter)
    #   - ~/.chrome_rabby_scraper (for EVM/Rabby)
    # ===========================================================================
    
    print("\n✓ Scrapers will start Chrome automatically with anti-detection")
    print("  → Jupiter: ~/.chrome_jupiter_scraper")
    print("  → Rabby:   ~/.chrome_rabby_scraper")
    print()
    
    # Set up ngrok
    setup_ngrok()
    
    # Create Flask app
    app = create_app()
    
    # Create and start scheduler
    scheduler = PortfolioScheduler(
        solana_addresses=SOLANA_ADDRESSES,
        evm_addresses=EVM_ADDRESSES,
        scrape_interval_minutes=SCRAPE_INTERVAL_MINUTES,
        chrome_debug_port=CHROME_DEBUG_PORT
    )
    
    # Store scheduler in app for route handlers to access
    app.scheduler = scheduler
    
    scheduler.start()
    
    # Start Flask server
    print("🚀 Flask API server starting...")
    print(f"   API returns cached data (auto-refreshes every {SCRAPE_INTERVAL_MINUTES} min)")
    print()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
