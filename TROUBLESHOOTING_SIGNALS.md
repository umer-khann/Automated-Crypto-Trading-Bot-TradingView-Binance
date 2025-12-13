# Troubleshooting: No Signals Being Sent

## 🔍 Step-by-Step Debugging

### Step 1: Check if Strategy is Generating Signals

**In TradingView:**
1. Look at your chart - do you see:
   - ✅ Green triangles (▲) below bars = Buy signals
   - ✅ Red triangles (▼) above bars = Sell signals
   - ❌ No triangles = Strategy not generating signals

**If no signals on chart:**
- Strategy conditions might be too strict
- Not enough historical data
- Indicators not aligned

### Step 2: Check Strategy Settings

**In TradingView Pine Editor:**
1. Click "Settings" (gear icon) on your strategy
2. Check:
   - ✅ Strategy is enabled
   - ✅ "Calculate On" is set correctly
   - ✅ "On chart" is enabled

### Step 3: Verify Alert is Active

**In TradingView:**
1. Look for alert icon in top toolbar
2. Click it - you should see your alert listed
3. Check alert status:
   - ✅ Green = Active
   - ⚠️ Yellow = Pending
   - ❌ Red = Error

### Step 4: Test Alert Manually

**Option A: Force a Signal (Easiest)**
1. In Pine Editor, temporarily modify buy condition to always true:
   ```pine
   buy_signal = true  // Force buy signal for testing
   ```
2. Save and add to chart
3. Alert should fire immediately
4. **Remember to change it back!**

**Option B: Use Dashboard Test**
1. Go to http://localhost:5000/
2. Use "Test Webhook" section
3. Send a test buy/sell
4. Verify it appears in Activity Monitor

### Step 5: Check Server is Receiving

**Check Server Logs:**
```bash
# Look for incoming requests
Get-Content trading_bot.log -Tail 20
```

**Look for:**
- `Received webhook with Content-Type:`
- `Received webhook:`
- `Parsed as JSON`

**If you see nothing:**
- Webhook not reaching server
- Check ngrok is running
- Verify webhook URL is correct

### Step 6: Check Ngrok Status

**Verify ngrok is running:**
```bash
# Check ngrok status
curl http://127.0.0.1:4040/api/tunnels
```

**Or check ngrok web interface:**
- Open: http://127.0.0.1:4040
- Look for incoming requests
- If you see requests, webhook is being sent
- If no requests, TradingView isn't sending

### Step 7: Simplify Strategy Conditions

**Your current strategy requires ALL conditions:**
- EMA crossover
- MACD bullish
- RSI bullish
- Bollinger Bands bullish

**This might be too strict! Try:**
1. Temporarily use only ONE condition for testing:
   ```pine
   buy_signal = ema_bullish  // Just EMA crossover
   sell_signal = ema_bearish
   ```
2. This will generate more signals
3. Test if webhook works
4. Then add conditions back

### Step 8: Check Alert Message Format

**In TradingView Alert Settings → Message tab:**
- Current: `{"signal": "{{strategy.order.action}}", "symbol": "{{ticker}}", "price": {{close}}}`
- ✅ This is correct

**Alternative (if above doesn't work):**
```
{{strategy.order.action}}|{{ticker}}|{{close}}
```

Then update server to parse this format.

### Step 9: Verify Strategy is on Correct Chart

**Make sure:**
- ✅ Strategy is added to BTCUSDT chart
- ✅ Chart has enough historical data
- ✅ Timeframe matches your strategy (1D, 1H, etc.)

### Step 10: Check Alert Frequency

**In Alert Settings:**
- Current: "1s" (every second)
- Better: "Once Per Bar Close"
- This prevents duplicate alerts

## 🚀 Quick Fix: Force a Test Signal

**Temporary Pine Script Modification:**

```pine
// Add this at the top of your signal conditions
// FOR TESTING ONLY - REMOVE AFTER TESTING!

// Force a buy signal on current bar
buy_signal = barstate.isconfirmed  // Triggers on bar close

// Or force immediately
buy_signal = true

// Remember to change back to your real conditions!
```

## 📊 What to Check in Dashboard

1. **Server Status:** Should be green "Online"
2. **Activity Monitor:** Should show incoming webhooks
3. **Trade History:** Should show executed trades
4. **Server Logs:** Should show "Received webhook"

## 🔧 Common Issues & Fixes

### Issue: No signals on chart
**Fix:** Strategy conditions too strict - simplify temporarily

### Issue: Signals on chart but no webhook
**Fix:** 
- Check alert is active (green status)
- Verify webhook URL is correct
- Check ngrok is running

### Issue: Webhook sent but server not receiving
**Fix:**
- Check ngrok URL matches TradingView
- Verify server is running
- Check firewall/network

### Issue: Server receives but trade fails
**Fix:**
- Check API keys are valid
- Verify account has balance
- Check error message in logs

## 🧪 Test Checklist

- [ ] Strategy shows signals on chart
- [ ] Alert is active (green status)
- [ ] Webhook URL is correct
- [ ] Ngrok is running
- [ ] Server is running
- [ ] Dashboard shows server online
- [ ] Test webhook from dashboard works
- [ ] Server logs show incoming requests

## 💡 Pro Tips

1. **Start Simple:**
   - Use only EMA crossover first
   - Test if webhook works
   - Then add more conditions

2. **Use Dashboard Test:**
   - Always test with dashboard first
   - This verifies server works
   - Then test with TradingView

3. **Check Ngrok Web Interface:**
   - http://127.0.0.1:4040
   - Shows all HTTP requests
   - See if TradingView is sending

4. **Monitor Logs:**
   - Keep `trading_bot.log` open
   - Watch for incoming webhooks
   - See exact error messages

---

**Still not working?** Share:
1. Do you see signals on the chart?
2. Is the alert active (green)?
3. What do server logs show?
4. What does ngrok web interface show?

