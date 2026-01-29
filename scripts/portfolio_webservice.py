#!/usr/bin/env python3
"""
Simple Flask webservice that serves JSON files from feeds/ directory
NO SCRAPING - just reads and serves existing JSON files
"""
from flask import Flask, request, jsonify
from pyngrok import ngrok
import os
import json
from pathlib import Path

# Get feeds directory
FEEDS_DIR = Path(__file__).resolve().parent.parent / 'feeds'

app = Flask(__name__)

def setup_ngrok(port):
    """Set up ngrok tunnel"""
    ngrok_token = os.environ.get('NGROK_AUTHTOKEN')
    
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)
        print("✓ Ngrok auth token configured")
    else:
        print("⚠️  NGROK_AUTHTOKEN not set")
    
    print()
    
    try:
        # Kill any existing ngrok processes
        print("Stopping any existing ngrok tunnels...")
        try:
            ngrok.kill()
            import time
            time.sleep(2)  # Give ngrok time to fully shut down
        except:
            pass
        
        public_url = ngrok.connect(port, bind_tls=True)
        print("="*70)
        print("🌐 NGROK TUNNEL ACTIVE")
        print("="*70)
        print(f"Public URL: {public_url}")
        print(f"Local URL:  http://localhost:{port}")
        print()
        print("API Endpoints:")
        print(f"  {public_url}/portfolio?address=YOUR_WALLET")
        print(f"  {public_url}/health")
        print("="*70)
        print()
    except Exception as e:
        print(f"⚠️  Failed to start ngrok: {e}")
        print(f"Starting without ngrok (localhost only)...")
        print(f"Local endpoint: http://localhost:{port}/portfolio?address=YOUR_WALLET")
        print()

@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    """Serve portfolio JSON file for a wallet address"""
    wallet_address = request.args.get('address')
    
    if not wallet_address:
        return jsonify({
            "error": "Missing 'address' parameter",
            "message": "Please provide a wallet address."
        }), 400
    
    # Try to find the JSON file for this address
    # Files are named like: evm_portfolio_0x302d12.json or solana_portfolio_ARdaJWDo.json
    short_addr = wallet_address[:8]
    
    # Try EVM first
    evm_file = FEEDS_DIR / f"evm_portfolio_{short_addr}.json"
    if evm_file.exists():
        with open(evm_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data), 200
    
    # Try Solana
    solana_file = FEEDS_DIR / f"solana_portfolio_{short_addr}.json"
    if solana_file.exists():
        with open(solana_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data), 200
    
    # File not found
    return jsonify({
        "error": "Wallet not found",
        "message": f"No portfolio file found for address starting with {short_addr}"
    }), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Count available JSON files
    json_files = list(FEEDS_DIR.glob('*.json'))
    return jsonify({
        "status": "ok",
        "feeds_directory": str(FEEDS_DIR),
        "available_portfolios": len(json_files),
        "files": [f.name for f in json_files]
    }), 200

if __name__ == "__main__":
    print("\n" + "="*70)
    print("   PORTFOLIO WEBSERVICE - FILE SERVING ONLY")
    print("="*70)
    print(f"\nServing JSON files from: {FEEDS_DIR}")
    print("\nEndpoints:")
    print("  GET  /health")
    print("  GET  /portfolio?address=YOUR_WALLET_ADDRESS")
    print("\n" + "="*70 + "\n")
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    # Set up ngrok tunnel
    setup_ngrok(port)
    
    app.run(host=host, port=port, debug=False)
