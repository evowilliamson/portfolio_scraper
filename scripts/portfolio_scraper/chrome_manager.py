"""
Chrome browser management for debugging
"""
import os
import subprocess
import time
import shutil
import atexit
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from .utils import check_chrome_debug_port, kill_all_chrome_processes


chrome_process = None


def get_chrome_binary():
    """Find Chrome binary on the system"""
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/opt/google/chrome/chrome',
    ]
    
    for path in chrome_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # Try 'which' command
    for name in ['google-chrome', 'google-chrome-stable']:
        result = subprocess.run(['which', name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    
    return None


def copy_profile_data(source_profile, dest_dir):
    """Copy essential profile data to debug directory"""
    items_to_copy = [
        'Cookies',
        'Local Storage',
        'Session Storage',
        'IndexedDB',
        'Local Extension Settings',
        'Preferences',
        'Extensions',
    ]
    
    copied_items = []
    for item in items_to_copy:
        src = os.path.join(source_profile, item)
        dst = os.path.join(dest_dir, item)
        
        if os.path.exists(src):
            try:
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                copied_items.append(item)
            except Exception as e:
                print(f"   Warning: Could not copy {item}: {e}")
    
    return copied_items


def test_selenium_connection(debug_port):
    """Test if Selenium can connect to Chrome"""
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("about:blank")
        driver.quit()
        return True
    except Exception as e:
        print(f"   Selenium test failed: {e}")
        return False


def start_chrome_with_debug(debug_port, chrome_profile, copy_profile=True, startup_timeout=30):
    """Start Chrome with remote debugging
    
    Args:
        debug_port: Port for remote debugging
        chrome_profile: Chrome profile name to copy from
        copy_profile: If True, copy profile data to debug directory
        startup_timeout: Maximum seconds to wait for Chrome startup
    """
    global chrome_process
    
    print("\n" + "="*70)
    print("🚀 STARTING CHROME WITH REMOTE DEBUGGING")
    print("="*70)
    
    kill_all_chrome_processes()
    
    chrome_binary = get_chrome_binary()
    if not chrome_binary:
        print("❌ Chrome not found!")
        return False
    
    print(f"✓ Found Chrome: {chrome_binary}")
    
    debug_data_dir = os.path.expanduser('~/.chrome_debug_profile')
    
    if copy_profile:
        main_chrome_dir = os.path.expanduser('~/.config/google-chrome')
        source_profile = os.path.join(main_chrome_dir, chrome_profile)
        
        if os.path.exists(source_profile):
            print(f"📋 Copying profile data from: {chrome_profile}")
            os.makedirs(debug_data_dir, exist_ok=True)
            
            copied = copy_profile_data(source_profile, debug_data_dir)
            if copied:
                print(f"   ✓ Copied: {', '.join(copied)}")
            else:
                print("   ⚠️  No profile data copied (starting fresh)")
        else:
            print(f"⚠️  Source profile not found: {source_profile}")
            print("   Starting with fresh profile")
    else:
        print("🆕 Starting with fresh profile (no data copied)")
    
    print(f"✓ Using debug directory: {debug_data_dir}")
    
    chrome_cmd = [
        chrome_binary,
        f'--remote-debugging-port={debug_port}',
        f'--user-data-dir={debug_data_dir}',
        '--headless=new',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--remote-allow-origins=*',
        '--window-size=1920,1080',
        '--no-first-run',
        '--no-default-browser-check',
    ]
    
    print("\n🔧 Starting Chrome process...")
    print(f"   Command: {chrome_cmd[0]} (+ {len(chrome_cmd)-1} flags)")
    
    log_dir = os.path.expanduser('~/chrome_debug_logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'chrome_debug.log')
    
    try:
        with open(log_file, 'w') as log:
            chrome_process = subprocess.Popen(
                chrome_cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
        
        print(f"   Chrome process started (PID: {chrome_process.pid})")
        print(f"   Logs: {log_file}")
        
        print(f"\n⏳ Waiting for debug port {debug_port}...")
        start_time = time.time()
        
        while time.time() - start_time < startup_timeout:
            if chrome_process.poll() is not None:
                print(f"\n❌ Chrome process died! Exit code: {chrome_process.returncode}")
                print(f"\n📋 Last 50 lines of Chrome log:")
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-50:]:
                            print(f"   {line.rstrip()}")
                except Exception as e:
                    print(f"   Could not read log: {e}")
                return False
            
            if check_chrome_debug_port(debug_port):
                elapsed = time.time() - start_time
                print(f"   ✓ Debug port accessible after {elapsed:.1f}s")
                
                time.sleep(1)
                
                print("\n🧪 Testing Selenium connection...")
                if test_selenium_connection(debug_port):
                    print("   ✓ Selenium can connect to Chrome!")
                    print("\n" + "="*70)
                    print("✅ CHROME STARTED SUCCESSFULLY")
                    print("="*70)
                    return True
                else:
                    print("   ✗ Selenium connection failed")
                    return False
            
            time.sleep(0.5)
        
        print(f"\n❌ Timeout waiting for Chrome after {startup_timeout}s")
        return False
        
    except Exception as e:
        print(f"\n❌ Failed to start Chrome: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_chrome():
    """Clean up Chrome process on exit"""
    global chrome_process
    if chrome_process:
        print("\n🧹 Shutting down Chrome...")
        try:
            chrome_process.terminate()
            try:
                chrome_process.wait(timeout=5)
                print("   ✓ Chrome terminated gracefully")
            except subprocess.TimeoutExpired:
                chrome_process.kill()
                chrome_process.wait()
                print("   ✓ Chrome force killed")
        except Exception as e:
            print(f"   Error during cleanup: {e}")


# Register cleanup on module import
atexit.register(cleanup_chrome)