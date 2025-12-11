# Frontend Dashboard Guide

## 🚀 Quick Start

1. **Start the server:**
   ```bash
   python webhook_server.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5000/`

3. **That's it!** The dashboard will automatically load all data.

## 📊 Dashboard Sections

### 1. Header
- **Title:** Shows "Automated Trading Bot" with robot icon
- **Status Indicator:** 
  - 🟢 Green = Server online and Binance connected
  - 🔴 Red = Server offline or Binance not connected
  - Updates every 30 seconds

### 2. Statistics Cards
Four key metrics displayed in colorful cards:
- **Total Buys:** Number of buy orders executed
- **Total Sells:** Number of sell orders executed
- **Successful Trades:** Trades that completed successfully
- **Failed Trades:** Trades that encountered errors

### 3. Account Balance
- Shows all assets with non-zero balances
- Displays free balance for each asset
- Click "Refresh" to update manually
- Auto-updates when auto-refresh is enabled

### 4. Trade History Table
Complete log of all trades with:
- **Timestamp:** When the trade was executed
- **Signal:** BUY or SELL (color-coded)
- **Symbol:** Trading pair (e.g., BTCUSDT)
- **Price:** Execution price
- **Quantity:** Amount traded
- **Order ID:** Binance order ID
- **Status:** success or error (color-coded)
- **Error:** Error message if trade failed

**Features:**
- Sorted by newest first
- Export to CSV button
- Manual refresh button
- Auto-refresh support

### 5. Test Webhook
Manual testing interface:
- **Signal:** Select Buy or Sell
- **Symbol:** Enter trading pair (default: BTCUSDT)
- **Price:** Enter test price (default: 50000)
- **Send Test Webhook:** Executes a test trade

**Use Cases:**
- Test your webhook endpoint
- Verify Binance connection
- Test trade execution without TradingView

### 6. Recent Logs
- Shows log information
- Links to `trading_bot.log` file for detailed logs
- Check server console for real-time logs

## 🎨 Features

### Auto-Refresh
- Toggle button in the Logs section header
- When enabled, refreshes data every 5 seconds
- Updates:
  - Trade history
  - Account balances
  - Server status

### Export Functionality
- Export trade history to CSV
- File named: `trade_history_YYYY-MM-DD.csv`
- Includes all trade data

### Toast Notifications
- Success messages (green)
- Error messages (red)
- Warning messages (yellow)
- Auto-dismiss after 3 seconds

### Responsive Design
- Works on desktop, tablet, and mobile
- Adapts layout for smaller screens
- Touch-friendly buttons

## 🎯 Usage Tips

1. **Monitor Trades in Real-Time:**
   - Enable auto-refresh
   - Keep dashboard open
   - Watch for new trades as they happen

2. **Test Your Setup:**
   - Use "Test Webhook" section
   - Send a test buy/sell order
   - Verify it appears in trade history

3. **Check Balances:**
   - Monitor your testnet account balance
   - Ensure sufficient funds for trading
   - Refresh manually if needed

4. **Export Data:**
   - Export trade history for analysis
   - Use CSV file in Excel or Google Sheets
   - Track performance over time

## 🔧 Troubleshooting

### Dashboard Not Loading
- Check if server is running: `python webhook_server.py`
- Verify URL: `http://localhost:5000/`
- Check browser console for errors (F12)

### Data Not Updating
- Click manual refresh buttons
- Enable auto-refresh
- Check server logs for errors
- Verify API endpoints are working

### Styling Issues
- Clear browser cache (Ctrl+F5)
- Check if CSS file is loading
- Verify static files are in `static/` directory

### API Errors
- Check server status indicator
- Verify Binance API keys are configured
- Check `trading_bot.log` for detailed errors

## 🌐 Accessing via Ngrok

If you're using ngrok to expose your server:

1. Get your ngrok URL: `python get_ngrok_url.py`
2. Access dashboard at: `https://your-ngrok-url.ngrok-free.dev/`
3. Share the URL to access from anywhere

**Note:** The dashboard will work through ngrok, but make sure:
- Server is running locally
- Ngrok is forwarding to port 5000
- Both are running simultaneously

## 📱 Mobile Access

The dashboard is fully responsive and works on mobile devices:
- Open `http://localhost:5000/` on your phone (same network)
- Or use ngrok URL for remote access
- Touch-friendly interface
- Optimized for small screens

---

**Enjoy monitoring your trading bot!** 🤖📈

