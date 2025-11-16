#!/usr/bin/env python3
"""
Auto-update ngrok URL on VPS whenever ngrok restarts
"""

import requests
import paramiko
import time
import sys

# VPS Configuration
VPS_HOST = "167.172.30.134"
VPS_USER = "deploy"
VPS_PASSWORD = None  # Set this or use SSH key
VPS_KEY_PATH = "~/.ssh/id_rsa"  # Path to your SSH key

# File to update on VPS
VIEWS_FILE = "/opt/az_sunshine/backend/transparency/views.py"

def get_ngrok_url():
    """Get current ngrok URL from local API"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        data = response.json()
        
        for tunnel in data.get("tunnels", []):
            if tunnel.get("proto") == "https":
                return tunnel.get("public_url")
        
        print("❌ No HTTPS tunnel found")
        return None
    except Exception as e:
        print(f"❌ Error getting ngrok URL: {e}")
        return None

def update_vps_config(ngrok_url):
    """SSH to VPS and update views.py with new ngrok URL"""
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect using SSH key
        ssh.connect(
            VPS_HOST,
            username=VPS_USER,
            key_filename=VPS_KEY_PATH.replace("~", __import__("os").path.expanduser("~"))
        )
        
        print(f"✅ Connected to VPS: {VPS_HOST}")
        
        # Command to update the file
        sed_command = f'''sudo sed -i 's|NGROK_URL = "https://.*ngrok-free.app/run-scraper"|NGROK_URL = "{ngrok_url}/run-scraper"|g' {VIEWS_FILE}'''
        
        stdin, stdout, stderr = ssh.exec_command(sed_command)
        
        # Wait for command to complete
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print(f"✅ Updated views.py with: {ngrok_url}/run-scraper")
            
            # Restart Gunicorn
            print("🔄 Restarting Gunicorn...")
            stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart az_sunshine_gunicorn")
            stdout.channel.recv_exit_status()
            
            print("✅ Gunicorn restarted successfully!")
            return True
        else:
            error = stderr.read().decode()
            print(f"❌ Error updating file: {error}")
            return False
            
    except Exception as e:
        print(f"❌ SSH Error: {e}")
        return False
    finally:
        ssh.close()

def main():
    print("\n" + "="*70)
    print("🔄 Ngrok URL Auto-Updater")
    print("="*70 + "\n")
    
    # Wait a moment for ngrok to fully start
    print("⏳ Waiting for ngrok to start...")
    time.sleep(3)
    
    # Get ngrok URL
    print("📡 Fetching ngrok URL...")
    ngrok_url = get_ngrok_url()
    
    if not ngrok_url:
        print("\n❌ Failed to get ngrok URL. Make sure ngrok is running!")
        print("   Start ngrok: ngrok http 5001")
        sys.exit(1)
    
    print(f"✅ Found ngrok URL: {ngrok_url}")
    
    # Update VPS
    print(f"\n🚀 Updating VPS configuration...")
    success = update_vps_config(ngrok_url)
    
    if success:
        print("\n" + "="*70)
        print("✅ SUCCESS! VPS is now configured with the new ngrok URL")
        print("="*70)
        print(f"\n🌐 Your scraper is accessible at: {ngrok_url}")
        print("\n✨ You can now use the 'Scrape Now' button in your frontend!")
    else:
        print("\n❌ Failed to update VPS. Please update manually:")
        print(f"   NGROK_URL = \"{ngrok_url}/run-scraper\"")
        sys.exit(1)

if __name__ == "__main__":
    main()

