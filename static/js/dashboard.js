/**
 * HexStrike AI Dashboard - Shared Utilities
 * Common functions used across all dashboard pages
 */

// ============================================================
// API Helpers
// ============================================================

/**
 * Perform a GET request to a dashboard API endpoint.
 * Returns parsed JSON or null on error.
 */
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(endpoint, {
            headers: { 'Accept': 'application/json' }
        });
        if (!response.ok) {
            console.warn(`fetchAPI ${endpoint} returned ${response.status}`);
            return null;
        }
        return await response.json();
    } catch (e) {
        console.error(`fetchAPI error for ${endpoint}:`, e);
        return null;
    }
}

/**
 * Perform a POST request to a dashboard API endpoint.
 * Returns parsed JSON or null on error.
 */
async function postAPI(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data || {})
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            return { error: err.error || `HTTP ${response.status}`, success: false };
        }
        return await response.json();
    } catch (e) {
        console.error(`postAPI error for ${endpoint}:`, e);
        return { error: e.message, success: false };
    }
}

// ============================================================
// Navbar status indicator
// ============================================================

async function updateNavbarStatus() {
    const dot = document.getElementById('navStatusDot');
    const text = document.getElementById('navStatusText');
    if (!dot || !text) return;

    const status = await fetchAPI('/api/status');
    if (!status) return;

    if (status.online) {
        dot.className = 'status-dot online';
        text.textContent = `${status.response_time_ms}ms`;
    } else {
        dot.className = 'status-dot offline';
        text.textContent = 'Offline';
    }
}

// ============================================================
// Toast notifications
// ============================================================

/**
 * Show a Bootstrap toast notification.
 * @param {string} message - Message text
 * @param {string} type - 'success' | 'danger' | 'warning' | 'info'
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const iconMap = {
        success: 'bi-check-circle-fill',
        danger: 'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };

    const id = `toast-${Date.now()}`;
    const html = `
        <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="bi ${iconMap[type] || iconMap.info}"></i>
                    <span>${escapeHtml(message)}</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast"></button>
            </div>
        </div>`;

    container.insertAdjacentHTML('beforeend', html);
    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// ============================================================
// Utility helpers
// ============================================================

/**
 * Escape HTML special characters to prevent XSS.
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Format seconds into a human-readable uptime string.
 */
function formatUptime(seconds) {
    if (!seconds || isNaN(seconds)) return '—';
    const s = Math.floor(seconds);
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;

    if (d > 0) return `${d}d ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m ${sec}s`;
    if (m > 0) return `${m}m ${sec}s`;
    return `${sec}s`;
}

/**
 * Update the "last updated" footer text.
 */
function setLastUpdated() {
    const el = document.getElementById('lastUpdated');
    if (el) {
        el.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
}

/**
 * Reload the current page.
 */
function refreshPage() {
    window.location.reload();
}

// ============================================================
// Theme Toggle
// ============================================================

function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    const icon = document.getElementById('themeIcon');
    if (!toggle) return;

    const savedTheme = localStorage.getItem('hexstrike_theme') || 'dark';
    setTheme(savedTheme);

    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-bs-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        setTheme(next);
        localStorage.setItem('hexstrike_theme', next);
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
}

// ============================================================
// Initialization
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    updateNavbarStatus();
    // Refresh navbar status every 15 seconds
    setInterval(updateNavbarStatus, 15000);
});
