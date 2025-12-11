"""
Automated Trading Bot - Webhook Server
Receives TradingView alerts and executes trades on Binance Testnet
"""

import json
import logging
import csv
import os
from datetime import datetime
from flask import Flask, request, jsonify
from binance.client import Client
from binance.exceptions import BinanceAPIException
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load configuration from environment variables or config file
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', 'your_testnet_api_key')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', 'your_testnet_api_secret')
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
app = Flask(__name__)

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

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive TradingView webhook alerts"""
    try:
        # Parse incoming JSON
        data = request.get_json()
        
        if not data:
            # Try to parse as raw string if JSON parsing fails
            raw_data = request.data.decode('utf-8')
            logger.warning(f"Received non-JSON data, attempting to parse: {raw_data}")
            try:
                data = json.loads(raw_data)
            except:
                return jsonify({'error': 'Invalid JSON payload'}), 400
        
        logger.info(f"Received webhook: {json.dumps(data, indent=2)}")
        
        # Extract signal information
        signal = data.get('signal', '').lower()
        symbol = data.get('symbol', TRADING_PAIR)
        price = data.get('price', 0)
        timestamp = datetime.now().isoformat()
        
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
            if signal == 'buy':
                # Check USDT balance for buying
                balance = get_account_balance('USDT')
                if balance is None:
                    raise Exception("Failed to retrieve account balance")
                if balance < TRADE_AMOUNT * price:
                    raise Exception(f"Insufficient USDT balance. Required: {TRADE_AMOUNT * price}, Available: {balance}")
                
                order = execute_buy_order(symbol, TRADE_AMOUNT)
                order_id = order.get('orderId')
                quantity = order.get('executedQty')
                
            elif signal == 'sell':
                # Check base currency balance for selling
                base_balance = get_base_currency_balance(symbol)
                if base_balance is None:
                    raise Exception("Failed to retrieve account balance")
                if base_balance < TRADE_AMOUNT:
                    raise Exception(f"Insufficient {symbol} balance. Required: {TRADE_AMOUNT}, Available: {base_balance}")
                
                order = execute_sell_order(symbol, TRADE_AMOUNT)
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
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'binance_connected': client is not None
    }), 200

@app.route('/balance', methods=['GET'])
def balance():
    """Get account balances"""
    try:
        if not client:
            return jsonify({'error': 'Binance client not initialized'}), 500
        
        account = client.get_account()
        balances = {}
        for balance in account['balances']:
            if float(balance['free']) > 0:
                balances[balance['asset']] = {
                    'free': balance['free'],
                    'locked': balance['locked']
                }
        
        return jsonify({'balances': balances}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Initialize trade history file
    init_trade_history()
    
    logger.info("Starting Trading Bot Webhook Server...")
    logger.info(f"Trading Pair: {TRADING_PAIR}")
    logger.info(f"Trade Amount: {TRADE_AMOUNT}")
    logger.info("Server will listen on http://localhost:5000/webhook")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

