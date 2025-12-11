"""
Quick script to get your current ngrok public URL
Run this to get the webhook URL for TradingView configuration
"""

import requests
import json

def get_ngrok_url():
    """Get the public ngrok URL"""
    try:
        response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
        data = response.json()
        
        if data.get('tunnels'):
            tunnel = data['tunnels'][0]
            public_url = tunnel.get('public_url')
            proto = tunnel.get('proto', 'https')
            
            if public_url:
                webhook_url = f"{public_url}/webhook"
                print("=" * 60)
                print("Ngrok Tunnel Information")
                print("=" * 60)
                print(f"Public URL:     {public_url}")
                print(f"Protocol:       {proto}")
                print(f"Webhook URL:    {webhook_url}")
                print("=" * 60)
                print("\nUse this webhook URL in your TradingView alert settings:")
                print(f"\n  {webhook_url}\n")
                return webhook_url
            else:
                print("❌ No public URL found in ngrok tunnel")
                return None
        else:
            print("❌ No active tunnels found")
            print("Make sure ngrok is running: ngrok http 5000")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to ngrok API")
        print("Make sure ngrok is running: ngrok http 5000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    get_ngrok_url()

