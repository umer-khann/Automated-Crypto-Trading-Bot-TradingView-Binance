# Ngrok Setup Guide for Trading Bot

## Your Current Ngrok URL

**Public URL:** `https://dirgeful-lithographical-jenee.ngrok-free.dev`

**Webhook Endpoint:** `https://dirgeful-lithographical-jenee.ngrok-free.dev/webhook`

## Quick Setup Steps

### 1. Verify Your Webhook Server is Running

Make sure your Flask server is running on port 5000:
```bash
python webhook_server.py
```

You should see:
```
Starting Trading Bot Webhook Server...
Server will listen on http://localhost:5000/webhook
```

### 2. Verify Ngrok is Forwarding

Your ngrok should be forwarding `localhost:5000` to the public URL above.

If you need to restart ngrok:
```bash
ngrok http 5000
```

### 3. Test the Webhook Endpoint

Test that your webhook is accessible through ngrok:

```bash
# Test health endpoint
curl https://dirgeful-lithographical-jenee.ngrok-free.dev/health

# Test webhook endpoint
curl -X POST https://dirgeful-lithographical-jenee.ngrok-free.dev/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "buy", "symbol": "BTCUSDT", "price": 50000}'
```

### 4. Configure TradingView Alert

1. **Open TradingView** and go to your chart with the Pine Script strategy
2. **Right-click on the chart** → Select "Add Alert"
3. **Alert Settings:**
   - **Condition:** Select your strategy (e.g., "Automated Trading Bot Strategy")
   - **Webhook URL:** Enter:
     ```
     https://dirgeful-lithographical-jenee.ngrok-free.dev/webhook
     ```
   - **Message:** Use the JSON format from the Pine Script:
     ```
     {"signal": "{{strategy.order.action}}", "symbol": "{{ticker}}", "price": {{close}}, "time": "{{time}}"}
     ```
     Or use the alert message format from the Pine Script (which already includes JSON)
   - **Frequency:** "Once Per Bar Close"
4. **Click "Create"**

### 5. Important Notes

⚠️ **Ngrok Free Plan Limitations:**
- The URL changes every time you restart ngrok (unless you have a paid plan with static domain)
- You'll need to update the TradingView webhook URL if you restart ngrok
- Free plan has session time limits

💡 **Tip:** Keep ngrok running in a separate terminal window while testing.

### 6. Monitor Webhook Requests

You can monitor incoming webhook requests in two ways:

**A. Ngrok Web Interface:**
- Open: http://127.0.0.1:4040
- View all HTTP requests in real-time

**B. Server Logs:**
- Check `trading_bot.log` for detailed logs
- All webhook requests are logged with full details

### 7. Troubleshooting

**Problem: Webhook not receiving alerts**
- ✅ Check if Flask server is running: `python webhook_server.py`
- ✅ Check if ngrok is running: Look for "Session Status: online"
- ✅ Verify ngrok URL matches TradingView alert settings
- ✅ Check ngrok web interface (http://127.0.0.1:4040) for incoming requests

**Problem: "Tunnel not found" or connection errors**
- Restart ngrok: `ngrok http 5000`
- Update TradingView webhook URL with new ngrok URL
- Check firewall settings

**Problem: 404 Not Found**
- Ensure Flask server is running on port 5000
- Verify the endpoint is `/webhook` (not `/webhook/`)
- Check server logs for errors

## Alternative: Get Ngrok URL Programmatically

If you need to get your ngrok URL programmatically:

**PowerShell:**
```powershell
(Invoke-WebRequest -Uri http://127.0.0.1:4040/api/tunnels -UseBasicParsing).Content | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Select-Object -ExpandProperty public_url
```

**Python:**
```python
import requests
response = requests.get('http://127.0.0.1:4040/api/tunnels')
data = response.json()
ngrok_url = data['tunnels'][0]['public_url']
print(f"Webhook URL: {ngrok_url}/webhook")
```

## Next Steps

1. ✅ Start your webhook server
2. ✅ Keep ngrok running
3. ✅ Configure TradingView alert with the webhook URL
4. ✅ Monitor logs and trade history
5. ✅ Test with a manual webhook call first

---

**Current Webhook URL:** `https://dirgeful-lithographical-jenee.ngrok-free.dev/webhook`

**Remember:** This URL will change if you restart ngrok (on free plan). Update TradingView alerts accordingly.

