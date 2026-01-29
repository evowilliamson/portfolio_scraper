"""
Utility functions for the portfolio scraper
"""
import os
import re
import socket
import subprocess
import time
import shutil
import psutil


def is_solana_address(address):
    """Check if address is Solana format (base58, ~44 chars)"""
    return len(address) > 30 and not address.startswith('0x')


def is_evm_address(address):
    """Check if address is EV format (0x + 40 hex chars)"""
    return address.startswith('0x') and len(address) == 42


def check_chrome_debug_port(port):
    """Check if Chrome debug port is accessible"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0


def kill_all_chrome_processes():
    """Kill ALL Chrome processes to ensure clean start"""
    print("🔍 Killing ALL Chrome processes for clean start...")
    killed = False
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                print(f"   Killing Chrome process (PID: {proc.info['pid']})")
                proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed:
        time.sleep(3)
        print("   ✓ All Chrome processes terminated")
    else:
        print("   No Chrome processes found")
    return killed


def get_chrome_major_version():
    """Return installed Chrome major version, or None if unknown."""
    candidates = [
        shutil.which('google-chrome'),
        shutil.which('google-chrome-stable'),
        shutil.which('chromium-browser'),
        shutil.which('chromium'),
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/opt/google/chrome/chrome',
    ]
    chrome_binary = None
    for candidate in candidates:
        if candidate and os.path.exists(candidate) and os.access(candidate, os.X_OK):
            chrome_binary = candidate
            break

    if not chrome_binary:
        return None

    try:
        result = subprocess.run(
            [chrome_binary, '--version'],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None

    version_text = (result.stdout or result.stderr or '').strip()
    match = re.search(r'(\d+)\.', version_text)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None
