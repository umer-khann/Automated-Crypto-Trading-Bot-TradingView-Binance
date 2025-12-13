// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = window.location.origin; // Use same origin as frontend
const AUTO_REFRESH_INTERVAL = 5000; // 5 seconds
let autoRefreshEnabled = false;
let autoRefreshInterval = null;
let lastTradeCount = 0;
let webhookActivity = [];

// ============================================================================
// Utility Functions
// ============================================================================

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (e) {
        return dateString;
    }
}

function formatNumber(num) {
    if (!num) return '0';
    return parseFloat(num).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 8
    });
}

// ============================================================================
// API Calls
// ============================================================================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API call failed: ${endpoint}`, error);
        throw error;
    }
}

async function checkServerStatus() {
    try {
        const data = await apiCall('/health');
        const statusBadge = document.getElementById('server-status');
        
        if (data.binance_connected) {
            statusBadge.className = 'status-badge online';
            statusBadge.innerHTML = '<i class="fas fa-circle"></i> Online';
        } else {
            statusBadge.className = 'status-badge offline';
            statusBadge.innerHTML = '<i class="fas fa-circle"></i> Offline (Binance not connected)';
        }
        return true;
    } catch (error) {
        const statusBadge = document.getElementById('server-status');
        statusBadge.className = 'status-badge offline';
        statusBadge.innerHTML = '<i class="fas fa-circle"></i> Offline';
        return false;
    }
}

async function loadBalance() {
    try {
        const data = await apiCall('/balance');
        const balanceGrid = document.getElementById('balance-grid');
        
        if (!data.balances || Object.keys(data.balances).length === 0) {
            balanceGrid.innerHTML = '<div class="balance-loading">No balances found</div>';
            return;
        }
        
        // Show only top 5 trading assets (USDT, BTC, ETH, BNB, BUSD)
        const tradingAssets = ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD'];
        const sortedBalances = Object.entries(data.balances).filter(([asset]) => 
            tradingAssets.includes(asset)
        ).sort(([a], [b]) => {
            // Sort by trading priority order
            return tradingAssets.indexOf(a) - tradingAssets.indexOf(b);
        });
        
        balanceGrid.innerHTML = sortedBalances
            .map(([asset, balance]) => `
                <div class="balance-item">
                    <div class="asset">${asset}</div>
                    <div class="amount">${formatNumber(balance.free)}</div>
                </div>
            `).join('');
        
        // Show message if no trading assets found
        if (sortedBalances.length === 0) {
            balanceGrid.innerHTML = '<div class="balance-loading">No trading assets found. Check your Binance Testnet account.</div>';
        }
    } catch (error) {
        showToast('Failed to load balance: ' + error.message, 'error');
        document.getElementById('balance-grid').innerHTML = 
            '<div class="balance-loading">Error loading balances</div>';
    }
}

async function loadTradeHistory() {
    try {
        const data = await apiCall('/history');
        const tbody = document.getElementById('trade-history-body');
        
        if (!data.trades || data.trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">No trades yet</td></tr>';
            updateStats([]);
            return;
        }
        
        // Sort by timestamp (newest first)
        const trades = data.trades.sort((a, b) => 
            new Date(b.timestamp) - new Date(a.timestamp)
        );
        
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td>${formatDate(trade.timestamp)}</td>
                <td class="signal-${trade.signal}">${trade.signal.toUpperCase()}</td>
                <td>${trade.symbol || 'N/A'}</td>
                <td>${formatNumber(trade.price)}</td>
                <td>${trade.quantity || 'N/A'}</td>
                <td>${trade.order_id || 'N/A'}</td>
                <td class="status-${trade.status}">${trade.status}</td>
                <td>${trade.error || '-'}</td>
            </tr>
        `).join('');
        
        updateStats(trades);
    } catch (error) {
        showToast('Failed to load trade history: ' + error.message, 'error');
        document.getElementById('trade-history-body').innerHTML = 
            '<tr><td colspan="8" class="loading">Error loading trade history</td></tr>';
    }
}

function initializeActivityMonitor(trades) {
    const activityContainer = document.getElementById('activity-container');
    
    if (trades.length === 0) {
        activityContainer.innerHTML = `
            <div class="activity-item">
                <div class="activity-icon info"><i class="fas fa-info-circle"></i></div>
                <div class="activity-content">
                    <div class="activity-title">No webhook activity yet</div>
                    <div class="activity-time">Waiting for TradingView alerts or test webhooks...</div>
                </div>
            </div>
        `;
        return;
    }
    
    // Show last 10 trades in activity monitor
    const recentTrades = trades.slice(0, 10);
    activityContainer.innerHTML = recentTrades.map(trade => {
        const isSuccess = trade.status === 'success';
        const isBuy = trade.signal === 'buy';
        
        return `
            <div class="activity-item">
                <div class="activity-icon ${isSuccess ? 'success' : 'error'}">
                    <i class="fas fa-${isBuy ? 'arrow-up' : 'arrow-down'}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">
                        ${isBuy ? 'BUY' : 'SELL'} ${trade.symbol || 'N/A'} 
                        <span class="activity-status ${isSuccess ? 'success' : 'error'}">${trade.status}</span>
                    </div>
                    <div class="activity-details">
                        Price: ${formatNumber(trade.price)} | 
                        Quantity: ${trade.quantity || 'N/A'} | 
                        ${trade.order_id ? `Order ID: ${trade.order_id}` : ''}
                        ${trade.error ? `<span class="activity-error">Error: ${trade.error}</span>` : ''}
                    </div>
                    <div class="activity-time">${formatDate(trade.timestamp)}</div>
                </div>
            </div>
        `;
    }).join('');
    
    lastTradeCount = trades.length;
}

function updateStats(trades) {
    const buys = trades.filter(t => t.signal === 'buy').length;
    const sells = trades.filter(t => t.signal === 'sell').length;
    const successful = trades.filter(t => t.status === 'success').length;
    const failed = trades.filter(t => t.status === 'error').length;
    
    document.getElementById('total-buys').textContent = buys;
    document.getElementById('total-sells').textContent = sells;
    document.getElementById('successful-trades').textContent = successful;
    document.getElementById('failed-trades').textContent = failed;
    
    // Update Activity Monitor with existing trades
    updateActivityMonitor(trades);
}

function updateActivityMonitor(trades) {
    const activityContainer = document.getElementById('activity-container');
    
    if (!trades || trades.length === 0) {
        activityContainer.innerHTML = `
            <div class="activity-item">
                <div class="activity-icon info"><i class="fas fa-info-circle"></i></div>
                <div class="activity-content">
                    <div class="activity-title">No webhook activity yet</div>
                    <div class="activity-time">Waiting for TradingView alerts or test webhooks...</div>
                </div>
            </div>
        `;
        return;
    }
    
    // Show last 10 trades (most recent first)
    const recentTrades = trades.slice(0, 10);
    activityContainer.innerHTML = recentTrades.map(trade => {
        const isSuccess = trade.status === 'success';
        const isBuy = trade.signal === 'buy';
        
        return `
            <div class="activity-item">
                <div class="activity-icon ${isSuccess ? 'success' : 'error'}">
                    <i class="fas fa-${isBuy ? 'arrow-up' : 'arrow-down'}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">
                        ${isBuy ? 'BUY' : 'SELL'} ${trade.symbol || 'N/A'} 
                        <span class="activity-status ${isSuccess ? 'success' : 'error'}">${trade.status}</span>
                    </div>
                    <div class="activity-details">
                        Price: ${formatNumber(trade.price)} | 
                        Quantity: ${trade.quantity || 'N/A'} | 
                        ${trade.order_id ? `Order ID: ${trade.order_id}` : ''}
                        ${trade.error ? `<span class="activity-error">Error: ${trade.error}</span>` : ''}
                    </div>
                    <div class="activity-time">${formatDate(trade.timestamp)}</div>
                </div>
            </div>
        `;
    }).join('');
    
    lastTradeCount = trades.length;
}

async function testWebhook() {
    const signal = document.getElementById('test-signal').value;
    const symbol = document.getElementById('test-symbol').value;
    const price = parseFloat(document.getElementById('test-price').value);
    
    if (!symbol || !price) {
        showToast('Please fill in all fields', 'warning');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    
    try {
        const payload = {
            signal: signal,
            symbol: symbol,
            price: price,
            time: new Date().toISOString()
        };
        
        const data = await apiCall('/webhook', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if (data.status === 'success') {
            showToast(`Test ${signal} order executed successfully!`, 'success');
            // Refresh data
            setTimeout(() => {
                loadTradeHistory();
                loadBalance();
            }, 1000);
        } else {
            showToast(`Trade failed: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        showToast('Failed to send test webhook: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Test Webhook';
    }
}

// ============================================================================
// Refresh Functions
// ============================================================================

function refreshBalance() {
    // Get the button element (not the icon or text inside it)
    const btn = event.target.closest('button') || event.target;
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    loadBalance().finally(() => {
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    });
}

function refreshHistory() {
    // Get the button element (not the icon or text inside it)
    const btn = event.target.closest('button') || event.target;
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    loadTradeHistory().finally(() => {
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    });
}

function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;
    const icon = document.getElementById('auto-refresh-icon');
    const text = document.getElementById('auto-refresh-text');
    
    if (autoRefreshEnabled) {
        icon.className = 'fas fa-pause';
        text.textContent = 'Auto-refresh: ON';
        autoRefreshInterval = setInterval(() => {
            loadTradeHistory();
            loadBalance();
            checkServerStatus();
        }, AUTO_REFRESH_INTERVAL);
        
        // Also check for new trades immediately
        loadTradeHistory();
        showToast('Auto-refresh enabled', 'success');
    } else {
        icon.className = 'fas fa-play';
        text.textContent = 'Auto-refresh: OFF';
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
        showToast('Auto-refresh disabled', 'info');
    }
}

// ============================================================================
// Export Functions
// ============================================================================

function exportHistory() {
    apiCall('/history')
        .then(data => {
            if (!data.trades || data.trades.length === 0) {
                showToast('No trade history to export', 'warning');
                return;
            }
            
            // Convert to CSV
            const headers = ['timestamp', 'signal', 'symbol', 'price', 'quantity', 'order_id', 'status', 'error'];
            const csv = [
                headers.join(','),
                ...data.trades.map(trade => 
                    headers.map(header => {
                        const value = trade[header] || '';
                        return `"${value.toString().replace(/"/g, '""')}"`;
                    }).join(',')
                )
            ].join('\n');
            
            // Download
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `trade_history_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showToast('Trade history exported successfully', 'success');
        })
        .catch(error => {
            showToast('Failed to export history: ' + error.message, 'error');
        });
}

// ============================================================================
// Logs Functions
// ============================================================================

async function loadLogs() {
    // Note: In a real implementation, you might want to add a /logs endpoint
    // For now, we'll show a placeholder
    const logsContainer = document.getElementById('logs-container');
    logsContainer.innerHTML = `
        <div class="log-entry info">Logs are available in the trading_bot.log file</div>
        <div class="log-entry info">Check the server console or log file for detailed logs</div>
    `;
}

// ============================================================================
// Initialization
// ============================================================================

function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('last-update').textContent = 
        `Last updated: ${now.toLocaleString()}`;
}

async function initialize() {
    console.log('Initializing Trading Bot Dashboard...');
    
    // Check server status
    await checkServerStatus();
    
    // Load initial data
    await loadBalance();
    await loadTradeHistory();
    loadLogs();
    
    // Update timestamp
    updateLastUpdateTime();
    
    // Set up periodic status check
    setInterval(checkServerStatus, 30000); // Every 30 seconds
    
    showToast('Dashboard loaded successfully', 'success');
}

// ============================================================================
// Event Listeners
// ============================================================================

// Make functions globally available
window.refreshBalance = refreshBalance;
window.refreshHistory = refreshHistory;
window.testWebhook = testWebhook;
window.toggleAutoRefresh = toggleAutoRefresh;
window.exportHistory = exportHistory;

// Initialize on page load
document.addEventListener('DOMContentLoaded', initialize);

