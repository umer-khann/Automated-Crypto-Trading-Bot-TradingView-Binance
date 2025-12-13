"""
Verify Trades Using Binance Testnet API
Based on official Binance Spot API documentation:
https://developers.binance.com/docs/binance-spot-api-docs
"""

import os
import sys
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Binance client
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

if not BINANCE_API_KEY or BINANCE_API_KEY == 'your_testnet_api_key':
    print("❌ Error: Binance API keys not configured in .env file")
    print("   Please set BINANCE_API_KEY and BINANCE_API_SECRET in .env")
    sys.exit(1)

try:
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)
    print("✅ Connected to Binance Testnet\n")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

def format_timestamp(timestamp_ms):
    """Convert milliseconds timestamp to readable date"""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def verify_order(order_id, symbol='BTCUSDT'):
    """
    Verify a specific order using GET /api/v3/order endpoint
    Reference: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/query-order
    """
    print("=" * 80)
    print(f"VERIFYING ORDER: {order_id}")
    print("=" * 80)
    
    try:
        # GET /api/v3/order - Get order status
        order = client.get_order(symbol=symbol, orderId=order_id)
        
        print(f"\n✅ Order Found on Binance Testnet!")
        print(f"\n📋 Order Details:")
        print(f"   Order ID: {order['orderId']}")
        print(f"   Symbol: {order['symbol']}")
        print(f"   Status: {order['status']}")
        print(f"   Side: {order['side']}")
        print(f"   Type: {order['type']}")
        
        if order.get('price'):
            print(f"   Price: {order['price']} USDT")
        else:
            print(f"   Price: Market Order (executed at market price)")
        
        print(f"   Quantity: {order.get('executedQty', '0')} {symbol.replace('USDT', '')}")
        print(f"   Original Quantity: {order.get('origQty', '0')} {symbol.replace('USDT', '')}")
        
        if order.get('cummulativeQuoteQty'):
            print(f"   Total Value: {order['cummulativeQuoteQty']} USDT")
        
        print(f"   Created: {format_timestamp(order['time'])}")
        print(f"   Updated: {format_timestamp(order['updateTime'])}")
        
        # Status interpretation
        if order['status'] == 'FILLED':
            print(f"\n   ✅ Order Status: FILLED - Successfully executed!")
        elif order['status'] == 'NEW':
            print(f"\n   ⏳ Order Status: NEW - Pending execution")
        elif order['status'] == 'PARTIALLY_FILLED':
            print(f"\n   ⚠️  Order Status: PARTIALLY_FILLED - Partially executed")
        elif order['status'] == 'CANCELED':
            print(f"\n   ❌ Order Status: CANCELED - Order was canceled")
        else:
            print(f"\n   ⚠️  Order Status: {order['status']}")
        
        return order
        
    except BinanceAPIException as e:
        print(f"❌ Binance API Error: {e.message}")
        print(f"   Error Code: {e.code}")
        if e.code == -2013:
            print("   Order not found. Check if Order ID is correct.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_recent_orders(symbol='BTCUSDT', limit=10):
    """
    Get recent orders using GET /api/v3/allOrders endpoint
    Reference: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/all-orders
    """
    print("\n" + "=" * 80)
    print(f"RECENT ORDERS FOR {symbol}")
    print("=" * 80)
    
    try:
        # GET /api/v3/allOrders - Get all orders
        orders = client.get_all_orders(symbol=symbol, limit=limit)
        
        if not orders:
            print("No orders found.")
            return
        
        # Sort by time (newest first)
        orders.sort(key=lambda x: x['time'], reverse=True)
        
        filled_count = sum(1 for o in orders if o['status'] == 'FILLED')
        
        print(f"\n📊 Found {len(orders)} orders ({filled_count} filled)")
        print("\n" + "-" * 80)
        
        for order in orders:
            status_icon = "✅" if order['status'] == 'FILLED' else "⏳" if order['status'] == 'NEW' else "❌"
            print(f"\n{status_icon} Order ID: {order['orderId']}")
            print(f"   Status: {order['status']}")
            print(f"   Side: {order['side']} | Type: {order['type']}")
            print(f"   Executed: {order.get('executedQty', '0')} / {order.get('origQty', '0')}")
            print(f"   Time: {format_timestamp(order['time'])}")
            print("-" * 80)
            
    except BinanceAPIException as e:
        print(f"❌ Binance API Error: {e.message}")
    except Exception as e:
        print(f"❌ Error: {e}")

def get_recent_trades(symbol='BTCUSDT', limit=10):
    """
    Get recent trades using GET /api/v3/myTrades endpoint
    Reference: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/account-trade-list
    """
    print("\n" + "=" * 80)
    print(f"RECENT EXECUTED TRADES FOR {symbol}")
    print("=" * 80)
    print("(These are actual fills/executions)")
    
    try:
        # GET /api/v3/myTrades - Get account trade list
        trades = client.get_my_trades(symbol=symbol, limit=limit)
        
        if not trades:
            print("No trades found.")
            return
        
        # Sort by time (newest first)
        trades.sort(key=lambda x: x['time'], reverse=True)
        
        buys = sum(1 for t in trades if t['isBuyer'])
        sells = len(trades) - buys
        
        print(f"\n📊 Found {len(trades)} trades ({buys} buys, {sells} sells)")
        print("\n" + "-" * 80)
        
        for trade in trades:
            side = "BUY" if trade['isBuyer'] else "SELL"
            total_value = float(trade['price']) * float(trade['qty'])
            
            print(f"\n💰 Trade ID: {trade['id']}")
            print(f"   Order ID: {trade['orderId']}")
            print(f"   Side: {side}")
            print(f"   Price: {trade['price']} USDT")
            print(f"   Quantity: {trade['qty']} {symbol.replace('USDT', '')}")
            print(f"   Total: {total_value:.2f} USDT")
            print(f"   Time: {format_timestamp(trade['time'])}")
            print("-" * 80)
        
        return trades
        
    except BinanceAPIException as e:
        print(f"❌ Binance API Error: {e.message}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return []

def check_account_balance():
    """
    Get account information using GET /api/v3/account endpoint
    Reference: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/account-information
    """
    print("\n" + "=" * 80)
    print("ACCOUNT BALANCE")
    print("=" * 80)
    
    try:
        # GET /api/v3/account - Get account information
        account = client.get_account()
        
        # Show only assets with balance
        balances = []
        for balance in account['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                balances.append({
                    'asset': balance['asset'],
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                })
        
        # Sort by total balance (descending)
        balances.sort(key=lambda x: x['total'], reverse=True)
        
        print(f"\n📊 Assets with Balance:")
        print(f"\n{'Asset':<10} {'Free':<20} {'Locked':<20} {'Total':<20}")
        print("-" * 80)
        
        for balance in balances[:10]:  # Show top 10
            print(f"{balance['asset']:<10} {balance['free']:<20.8f} {balance['locked']:<20.8f} {balance['total']:<20.8f}")
        
        print(f"\n✅ Account Status: Trading Enabled" if account.get('canTrade') else "\n⚠️  Account Status: Trading Disabled")
        
    except BinanceAPIException as e:
        print(f"❌ Binance API Error: {e.message}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("BINANCE TESTNET TRADE VERIFICATION")
    print("Using Official Binance Spot API")
    print("=" * 80)
    
    # Check if specific order ID provided
    if len(sys.argv) > 1:
        try:
            order_id = int(sys.argv[1])
            verify_order(order_id)
        except ValueError:
            print(f"❌ Invalid Order ID: {sys.argv[1]}")
            print("   Order ID must be a number")
    else:
        # Show all information
        check_account_balance()
        get_recent_orders()
        get_recent_trades()
        
        print("\n" + "=" * 80)
        print("💡 USAGE:")
        print("   python verify_trade.py              - Show all recent orders and trades")
        print("   python verify_trade.py <ORDER_ID>    - Verify specific order")
        print("\n📚 API Documentation:")
        print("   https://developers.binance.com/docs/binance-spot-api-docs")
        print("=" * 80)

