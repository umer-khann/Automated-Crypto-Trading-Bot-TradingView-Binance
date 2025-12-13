"""
Automated Trading Bot - Webhook Server
Receives TradingView alerts and executes trades on Binance Testnet
"""

import json
import logging
import csv
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from binance.client import Client
from binance.exceptions import BinanceAPIException
import requests

# Load environment variables from .env file FIRST (before reading env vars)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded environment variables from .env file")
except ImportError:
    print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
    print("⚠ Will try to use system environment variables instead")
except Exception as e:
    print(f"⚠ Warning: Could not load .env file: {e}")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load configuration from environment variables or config file
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', 'your_testnet_api_key')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', 'your_testnet_api_secret')

# Debug: Check if keys are loaded (without showing actual keys)
if BINANCE_API_KEY and BINANCE_API_KEY != 'your_testnet_api_key':
    print(f"✓ API Key loaded (length: {len(BINANCE_API_KEY)})")
else:
    print("⚠ API Key not found or using default placeholder")
    
if BINANCE_API_SECRET and BINANCE_API_SECRET != 'your_testnet_api_secret':
    print(f"✓ API Secret loaded (length: {len(BINANCE_API_SECRET)})")
else:
    print("⚠ API Secret not found or using default placeholder")
BINANCE_TESTNET = True  # Always use testnet

# Trading parameters
TRADING_PAIR = os.getenv('TRADING_PAIR', 'BTCUSDT')
TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', '0.001'))  # Amount in base currency (BTC)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

# Initialize Binance client
try:
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=BINANCE_TESTNET)
    logger.info("Binance Testnet client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Binance client: {e}")
    client = None

# ============================================================================
# TRADE HISTORY STORAGE
# ============================================================================

TRADE_HISTORY_FILE = 'trade_history.csv'

def init_trade_history():
    """Initialize CSV file for trade history if it doesn't exist"""
    if not os.path.exists(TRADE_HISTORY_FILE):
        with open(TRADE_HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'signal', 'symbol', 'price', 'order_id', 
                'status', 'quantity', 'error'
            ])
        logger.info(f"Created trade history file: {TRADE_HISTORY_FILE}")

def save_trade(timestamp, signal, symbol, price, order_id=None, status='pending', quantity=None, error=None):
    """Save trade to CSV file"""
    try:
        with open(TRADE_HISTORY_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, signal, symbol, price, order_id, status, quantity, error
            ])
        logger.info(f"Trade saved to history: {signal} {symbol} @ {price}")
    except Exception as e:
        logger.error(f"Failed to save trade to history: {e}")

# ============================================================================
# TRADING FUNCTIONS
# ============================================================================

def get_account_balance(symbol='USDT'):
    """Get account balance for a specific symbol"""
    try:
        if not client:
            return None
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == symbol:
                return float(balance['free'])
        return 0.0
    except Exception as e:
        logger.error(f"Failed to get account balance: {e}")
        return None

def execute_buy_order(symbol, quantity):
    """Execute a market buy order"""
    try:
        if not client:
            raise Exception("Binance client not initialized")
        
        logger.info(f"Executing BUY order: {quantity} {symbol}")
        
        # Place market buy order
        order = client.create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        
        logger.info(f"BUY order executed successfully: {order}")
        return order
    except BinanceAPIException as e:
        error_msg = f"Binance API error: {e.message}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to execute BUY order: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)

def execute_sell_order(symbol, quantity):
    """Execute a market sell order"""
    try:
        if not client:
            raise Exception("Binance client not initialized")
        
        logger.info(f"Executing SELL order: {quantity} {symbol}")
        
        # Place market sell order
        order = client.create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        
        logger.info(f"SELL order executed successfully: {order}")
        return order
    except BinanceAPIException as e:
        error_msg = f"Binance API error: {e.message}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to execute SELL order: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)

def get_base_currency_balance(symbol):
    """Get balance of base currency (e.g., BTC for BTCUSDT)"""
    base_currency = symbol.replace('USDT', '').replace('USD', '')
    return get_account_balance(base_currency)

# ============================================================================
# WEBHOOK ENDPOINT
# ============================================================================

def parse_tradingview_message(message):
    """Parse TradingView alert message in format: 'order buy @ 0.001 filled on BTCUSDT'"""
    try:
        import re
        # Pattern: "order buy @ 0.001 filled on BTCUSDT"
        # Handles: "order {{strategy.order.action}} @ {{strategy.order.contracts}} filled on {{ticker}}"
        # Extract signal (buy/sell)
        signal_match = re.search(r'order\s+(buy|sell)', message, re.IGNORECASE)
        if not signal_match:
            return None
        
        signal = signal_match.group(1).lower()
        
        # Extract symbol (ticker)
        symbol_match = re.search(r'filled\s+on\s+(\w+)', message, re.IGNORECASE)
        if not symbol_match:
            return None
        
        symbol = symbol_match.group(1).upper()
        
        # Extract quantity (contracts) - this is the amount, not price
        quantity_match = re.search(r'@\s+([\d.]+)', message)
        quantity = float(quantity_match.group(1)) if quantity_match else 0
        
        # Price is not in the message, we'll need to get it from the market
        # For now, set to 0 and it will be fetched if needed
        price = 0
        
        return {'signal': signal, 'symbol': symbol, 'price': price, 'quantity': quantity}
    except Exception as e:
        logger.warning(f"Failed to parse TradingView message: {e}")
    return None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive TradingView webhook alerts"""
    try:
        data = None
        raw_data = None
        
        # Try to get data based on Content-Type
        content_type = request.content_type or ''
        
        logger.info(f"Received webhook with Content-Type: {content_type}")
        
        # Try JSON first (if Content-Type is application/json)
        if 'application/json' in content_type:
            try:
                data = request.get_json()
                logger.info("Parsed as JSON")
            except Exception as e:
                logger.warning(f"JSON parsing failed: {e}")
        
        # If no JSON data, try form data
        if not data and request.form:
            logger.info("Trying to parse as form data")
            signal = request.form.get('signal', '').lower()
            if not signal:
                # Try to extract from message field (common in TradingView)
                message = request.form.get('message', '') or request.form.get('text', '')
                if message:
                    raw_data = message
                else:
                    # Try all form fields
                    signal = request.form.get('{{strategy.order.action}}', '').lower()
                    symbol = request.form.get('{{ticker}}', TRADING_PAIR)
            else:
                symbol = request.form.get('symbol', request.form.get('{{ticker}}', TRADING_PAIR))
                price = request.form.get('price', request.form.get('{{close}}', 0))
                try:
                    price = float(price) if price else 0
                except:
                    price = 0
                data = {'signal': signal, 'symbol': symbol, 'price': price}
                logger.info(f"Parsed from form data: {data}")
        
        # If still no data, try raw body
        if not data:
            try:
                raw_data = request.data.decode('utf-8')
                logger.info(f"Raw data received: {raw_data[:200]}")
            except:
                raw_data = str(request.data)
        
        # Try parsing raw data as JSON string
        if not data and raw_data:
            try:
                data = json.loads(raw_data)
                logger.info("Parsed raw data as JSON")
            except:
                pass
        
        # Try parsing as TradingView template message format
        if not data and raw_data:
            parsed = parse_tradingview_message(raw_data)
            if parsed:
                data = parsed
                logger.info(f"Parsed TradingView message format: {data}")
        
        # If still no data, try to extract from query parameters
        if not data:
            signal = request.args.get('signal', '').lower()
            if signal:
                data = {
                    'signal': signal,
                    'symbol': request.args.get('symbol', TRADING_PAIR),
                    'price': float(request.args.get('price', 0))
                }
                logger.info(f"Parsed from query params: {data}")
        
        # Final fallback - log everything for debugging
        if not data:
            logger.error(f"Could not parse webhook. Content-Type: {content_type}")
            logger.error(f"Form data: {dict(request.form)}")
            logger.error(f"Raw data: {raw_data[:500] if raw_data else 'None'}")
            logger.error(f"Headers: {dict(request.headers)}")
            return jsonify({
                'error': 'Could not parse webhook payload',
                'content_type': content_type,
                'hint': 'Make sure your TradingView alert sends data in JSON format or TradingView message format'
            }), 400
        
        logger.info(f"Received webhook: {json.dumps(data, indent=2)}")
        
        # Extract signal information
        signal = data.get('signal', '').lower()
        symbol = data.get('symbol', TRADING_PAIR)
        price = data.get('price', 0)
        quantity_from_alert = data.get('quantity', None)  # Quantity from TradingView alert
        timestamp = datetime.now().isoformat()
        
        # If price is 0, try to get current market price
        if price == 0 and client:
            try:
                ticker = client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                logger.info(f"Fetched current market price for {symbol}: {price}")
            except Exception as e:
                logger.warning(f"Could not fetch market price: {e}")
        
        if signal not in ['buy', 'sell']:
            error_msg = f"Invalid signal: {signal}. Must be 'buy' or 'sell'"
            logger.error(error_msg)
            save_trade(timestamp, signal, symbol, price, status='error', error=error_msg)
            return jsonify({'error': error_msg}), 400
        
        # Execute trade based on signal
        order = None
        order_id = None
        quantity = None
        status = 'success'
        error = None
        
        try:
            # Use quantity from alert if available, otherwise use default TRADE_AMOUNT
            trade_quantity = quantity_from_alert if quantity_from_alert else TRADE_AMOUNT
            
            if signal == 'buy':
                # Check USDT balance for buying
                balance = get_account_balance('USDT')
                if balance is None:
                    raise Exception("Failed to retrieve account balance")
                required = trade_quantity * price if price > 0 else trade_quantity
                if balance < required:
                    raise Exception(f"Insufficient USDT balance. Required: {required}, Available: {balance}")
                
                order = execute_buy_order(symbol, trade_quantity)
                order_id = order.get('orderId')
                quantity = order.get('executedQty')
                
            elif signal == 'sell':
                # Check base currency balance for selling
                base_balance = get_base_currency_balance(symbol)
                if base_balance is None:
                    raise Exception("Failed to retrieve account balance")
                if base_balance < trade_quantity:
                    raise Exception(f"Insufficient {symbol} balance. Required: {trade_quantity}, Available: {base_balance}")
                
                order = execute_sell_order(symbol, trade_quantity)
                order_id = order.get('orderId')
                quantity = order.get('executedQty')
            
            logger.info(f"Trade executed successfully: {signal} {quantity} {symbol}")
            
        except Exception as e:
            status = 'error'
            error = str(e)
            logger.error(f"Trade execution failed: {error}")
        
        # Save trade to history
        save_trade(timestamp, signal, symbol, price, order_id, status, quantity, error)
        
        # Return response
        response = {
            'status': status,
            'signal': signal,
            'symbol': symbol,
            'price': price,
            'order_id': order_id,
            'quantity': quantity,
            'timestamp': timestamp
        }
        
        if error:
            response['error'] = error
        
        return jsonify(response), 200 if status == 'success' else 500
        
    except Exception as e:
        error_msg = f"Webhook processing error: {e}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    binance_status = 'not_initialized'
    binance_error = None
    
    if client is None:
        binance_status = 'not_initialized'
        binance_error = 'Binance client not initialized. Check API keys.'
    else:
        try:
            # Try a simple API call to verify connection
            client.ping()
            binance_status = 'connected'
        except Exception as e:
            binance_status = 'error'
            binance_error = str(e)
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'binance_connected': client is not None,
        'binance_status': binance_status,
        'binance_error': binance_error,
        'api_key_set': bool(BINANCE_API_KEY and BINANCE_API_KEY != 'your_testnet_api_key'),
        'api_secret_set': bool(BINANCE_API_SECRET and BINANCE_API_SECRET != 'your_testnet_api_secret')
    }), 200

@app.route('/balance', methods=['GET'])
def balance():
    """Get account balances"""
    try:
        if not client:
            error_msg = 'Binance client not initialized. Please check your API keys in .env file.'
            logger.error(error_msg)
            return jsonify({'error': error_msg, 'details': 'Make sure BINANCE_API_KEY and BINANCE_API_SECRET are set correctly'}), 500
        
        try:
            account = client.get_account()
        except BinanceAPIException as e:
            error_msg = f"Binance API error: {e.message}"
            logger.error(error_msg)
            return jsonify({
                'error': error_msg,
                'details': 'Check your API keys and ensure they are for Binance Testnet',
                'code': e.code if hasattr(e, 'code') else None
            }), 500
        except Exception as e:
            error_msg = f"Failed to fetch account: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                'error': error_msg,
                'details': 'Network error or invalid API credentials'
            }), 500
        
        balances = {}
        # Top 5 trading assets to display (most commonly traded)
        trading_assets = ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD']
        
        try:
            # Collect all balances first
            all_balances = {}
            for balance in account['balances']:
                free_balance = float(balance['free'])
                if free_balance > 0:
                    all_balances[balance['asset']] = {
                        'free': balance['free'],
                        'locked': balance['locked']
                    }
            
            # Only show the top 5 trading assets that have balance
            for asset in trading_assets:
                if asset in all_balances:
                    balances[asset] = all_balances[asset]
            
            # If we have less than 5, show what we have
            # (This handles cases where testnet doesn't have all assets)
        except Exception as e:
            logger.error(f"Error processing balances: {e}")
            return jsonify({
                'error': 'Error processing account balances',
                'details': str(e)
            }), 500
        
        return jsonify({'balances': balances}), 200
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'error': error_msg,
            'details': 'An unexpected error occurred. Check server logs for details.'
        }), 500

@app.route('/history', methods=['GET'])
def history():
    """Get trade history"""
    try:
        if not os.path.exists(TRADE_HISTORY_FILE):
            return jsonify({'trades': []}), 200
        
        trades = []
        with open(TRADE_HISTORY_FILE, 'r') as f:
            reader = csv.DictReader(f)
            trades = list(reader)
        
        return jsonify({'trades': trades}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, etc.)"""
    return send_from_directory('static', path)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Initialize trade history file
    init_trade_history()
    
    logger.info("Starting Trading Bot Webhook Server...")
    logger.info(f"Trading Pair: {TRADING_PAIR}")
    logger.info(f"Trade Amount: {TRADE_AMOUNT}")
    logger.info("Server will listen on http://localhost:5000")
    logger.info("Dashboard available at: http://localhost:5000/")
    logger.info("Webhook endpoint: http://localhost:5000/webhook")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

