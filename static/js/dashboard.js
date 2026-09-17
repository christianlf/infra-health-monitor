// Dashboard JavaScript
const API_BASE = '';
let refreshInterval;

// Fetch and update dashboard data
async function updateDashboard() {
    try {
        // Update summary stats
        const summaryResponse = await fetch(`${API_BASE}/api/summary`);
        const summaryData = await summaryResponse.json();
        
        if (summaryData.status === 'ok') {
            document.getElementById('overall-uptime').textContent = 
                summaryData.summary.overall_uptime.toFixed(1) + '%';
            document.getElementById('total-checks').textContent = 
                summaryData.summary.total_checks.toLocaleString();
            document.getElementById('total-targets').textContent = 
                summaryData.summary.total_targets;
        }
        
        // Update targets status
        const statusResponse = await fetch(`${API_BASE}/api/status`);
        const statusData = await statusResponse.json();
        
        if (statusData.status === 'ok') {
            renderTargets(statusData.targets);
            updateLastUpdated();
        }
    } catch (error) {
        console.error('Failed to update dashboard:', error);
        document.getElementById('targets-grid').innerHTML = 
            '<div class="loading">❌ Failed to load data. Check if monitor is running.</div>';
    }
}

// Render target cards
function renderTargets(targets) {
    const grid = document.getElementById('targets-grid');
    
    if (targets.length === 0) {
        grid.innerHTML = '<div class="loading">No targets monitored yet. Add targets to targets.yaml</div>';
        return;
    }
    
    grid.innerHTML = targets.map(target => `
        <div class="target-card">
            <div class="target-header">
                <div class="target-name">${escapeHtml(target.name)}</div>
                <div class="status-indicator ${target.status === 'success' ? 'status-online' : 'status-offline'}"></div>
            </div>
            
            <div class="target-info">
                <div class="info-row">
                    <span class="info-label">Status</span>
                    <span class="info-value">${target.status === 'success' ? '✅ ONLINE' : '❌ OFFLINE'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Latency</span>
                    <span class="info-value">${target.latency_ms}ms</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Last Check</span>
                    <span class="info-value">${formatTimestamp(target.last_check)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Total Checks</span>
                    <span class="info-value">${target.total_checks.toLocaleString()}</span>
                </div>
            </div>
            
            <div class="uptime-bar">
                <div class="uptime-label">Uptime: ${target.uptime_percent.toFixed(2)}%</div>
                <div class="uptime-progress">
                    <div class="uptime-fill" style="width: ${target.uptime_percent}%"></div>
                </div>
            </div>
            
            ${target.last_error ? `
                <div class="error-message">
                    ⚠️ ${escapeHtml(target.last_error)}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Helper functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    
    return date.toLocaleString();
}

function updateLastUpdated() {
    const now = new Date();
    document.getElementById('last-updated').textContent = now.toLocaleTimeString();
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    updateDashboard();
    
    // Auto-refresh every 10 seconds
    refreshInterval = setInterval(updateDashboard, 10000);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
