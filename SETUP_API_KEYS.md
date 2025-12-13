# Setup Binance Testnet API Keys

## Current Issue
Your server is showing: `API-key format invalid`

This means you need to set up your Binance Testnet API keys.

## Step-by-Step Guide

### Step 1: Get Binance Testnet API Keys

1. **Go to Binance Testnet:**
   - Visit: https://testnet.binance.vision/
   - Click "Generate HMAC_SHA256 Key" or "Create API Key"

2. **Create Account (if needed):**
   - You can use any email (it's testnet, no verification needed)
   - Log in to the testnet dashboard

3. **Create API Key:**
   - Go to API Management
   - Click "Create API Key"
   - **Important:** Enable these permissions:
     - ✅ Enable Reading
     - ✅ Enable Spot & Margin Trading
   - Copy your **API Key** and **Secret Key**
   - ⚠️ **Save the Secret Key immediately** - you can only see it once!

### Step 2: Create .env File

1. **Copy the example file:**
   ```bash
   copy config.example.env .env
   ```
   Or manually create a file named `.env` in your project folder.

2. **Edit .env file:**
   Open `.env` and replace the placeholder values:
   ```
   BINANCE_API_KEY=your_actual_api_key_here
   BINANCE_API_SECRET=your_actual_secret_key_here
   
   TRADING_PAIR=BTCUSDT
   TRADE_AMOUNT=0.001
   ```

   **Example:**
   ```
   BINANCE_API_KEY=abc123xyz789def456ghi012jkl345mno678pqr
   BINANCE_API_SECRET=xyz789abc123def456ghi012jkl345mno678pqr901stu234vwx567
   
   TRADING_PAIR=BTCUSDT
   TRADE_AMOUNT=0.001
   ```

### Step 3: Restart Server

After saving `.env` file:

1. **Stop the current server** (Ctrl+C in terminal)

2. **Restart the server:**
   ```bash
   python webhook_server.py
   ```

3. **Check the logs:**
   You should see:
   ```
   Binance Testnet client initialized successfully
   ```

   Instead of:
   ```
   Failed to initialize Binance client
   ```

### Step 4: Verify It Works

1. **Check health endpoint:**
   - Open: http://localhost:5000/health
   - Should show: `"binance_status": "connected"`

2. **Check balance:**
   - Open: http://localhost:5000/balance
   - Should show your testnet account balances (not an error)

3. **Test webhook:**
   - The webhook is already working (you saw it parse correctly)
   - Now it should execute trades successfully!

## Important Notes

✅ **Testnet Only:** These keys are for Binance Testnet only - they won't work on real Binance

✅ **Free Testnet Funds:** Binance Testnet provides free test funds - you don't need to deposit anything

✅ **Never Commit .env:** The `.env` file is in `.gitignore` - never commit it to version control!

✅ **Key Format:** Binance API keys are long alphanumeric strings (usually 64+ characters)

## Troubleshooting

### Still getting "API-key format invalid"?

1. **Check .env file exists:**
   ```bash
   dir .env
   ```
   (Should show the file)

2. **Check .env file content:**
   - Make sure there are no extra spaces
   - Make sure keys are on single lines
   - No quotes around the values

3. **Restart server:**
   - Environment variables are loaded at startup
   - You must restart after changing .env

4. **Verify keys are correct:**
   - Copy keys directly from Binance Testnet (no extra spaces)
   - Make sure you're using Testnet keys, not Mainnet keys

### Getting "Invalid API-key" or "Signature invalid"?

- Check that both API Key and Secret Key are correct
- Make sure you copied the full keys (they're long!)
- Verify keys are for Binance Testnet (testnet.binance.vision)

## Quick Test

Once set up, test with:
```bash
python test_webhook.py
```

This should execute a test trade successfully!

