"""
Test script for webhook endpoint
Run this to test your webhook server locally
"""

import requests
import json
import sys

WEBHOOK_URL = "http://localhost:5000/webhook"

def test_webhook(signal="buy", symbol="BTCUSDT", price=50000):
    """Test the webhook endpoint with a sample payload"""
    
    payload = {
        "signal": signal,
        "symbol": symbol,
        "price": price,
        "time": "2024-01-01T12:00:00"
    }
    
    print(f"Testing webhook with payload:")
    print(json.dumps(payload, indent=2))
    print(f"\nSending POST request to {WEBHOOK_URL}...")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server.")
        print("Make sure the webhook server is running: python webhook_server.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        print("Health Check:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_balance():
    """Test the balance endpoint"""
    try:
        response = requests.get("http://localhost:5000/balance", timeout=5)
        print("\nAccount Balance:")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Balance check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Trading Bot Webhook Test Script")
    print("=" * 50)
    
    # Test health endpoint first
    print("\n1. Testing health endpoint...")
    if not test_health():
        print("\n⚠️  Server might not be running. Start it with: python webhook_server.py")
        sys.exit(1)
    
    # Test balance endpoint
    print("\n2. Testing balance endpoint...")
    test_balance()
    
    # Test buy signal
    print("\n3. Testing BUY signal...")
    test_webhook("buy", "BTCUSDT", 50000)
    
    # Test sell signal
    print("\n4. Testing SELL signal...")
    test_webhook("sell", "BTCUSDT", 51000)
    
    # Test invalid signal
    print("\n5. Testing invalid signal (should fail)...")
    test_webhook("invalid", "BTCUSDT", 50000)
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

