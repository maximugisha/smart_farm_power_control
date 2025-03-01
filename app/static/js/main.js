/**
 * Main JavaScript for Smart Farm Power Control System
 */

// Token management
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function clearToken() {
    localStorage.removeItem('token');
}

// API client with auth header
const api = {
    get: function(url) {
        return fetch(url, {
            headers: {
                'Authorization': 'Bearer ' + getToken()
            }
        });
    },

    post: function(url, data) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getToken()
            },
            body: JSON.stringify(data)
        });
    },

    put: function(url, data) {
        return fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getToken()
            },
            body: JSON.stringify(data)
        });
    },

    delete: function(url) {
        return fetch(url, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + getToken()
            }
        });
    }
};

// Format utilities
function formatWatts(watts) {
    if (watts >= 1000) {
        return (watts / 1000).toFixed(2) + ' kW';
    }
    return watts.toFixed(1) + ' W';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatCurrency(amount) {
    return '$' + amount.toFixed(2);
}

function formatPercentage(value) {
    return value.toFixed(1) + '%';
}

// UI helper functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

function showAlert(message, type = 'success') {
    const alertPlaceholder = document.getElementById('alert-placeholder');
    if (!alertPlaceholder) return;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    alertPlaceholder.append(wrapper);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = wrapper.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Power color indicators
function getPowerClass(watts, maxPower) {
    if (!maxPower) return 'power-normal';

    const percentage = (watts / maxPower) * 100;

    if (percentage >= 90) {
        return 'power-critical';
    } else if (percentage >= 75) {
        return 'power-warning';
    } else {
        return 'power-normal';
    }
}

// Device status badge
function getStatusBadgeClass(status) {
    switch (status.toLowerCase()) {
        case 'online':
            return 'bg-success';
        case 'offline':
            return 'bg-secondary';
        case 'error':
            return 'bg-danger';
        case 'warning':
            return 'bg-warning';
        default:
            return 'bg-info';
    }
}

// Random color generator for charts
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Generate chart colors
function generateChartColors(count) {
    // Predefined colors for first few items
    const predefinedColors = [
        '#3498db', // blue
        '#e74c3c', // red
        '#2ecc71', // green
        '#f39c12', // orange
        '#9b59b6', // purple
        '#1abc9c', // teal
        '#d35400', // dark orange
        '#34495e'  // dark blue
    ];

    const colors = [];

    // Use predefined colors first
    for (let i = 0; i < count; i++) {
        if (i < predefinedColors.length) {
            colors.push(predefinedColors[i]);
        } else {
            colors.push(getRandomColor());
        }
    }

    return colors;
}

// Authentication check
document.addEventListener('DOMContentLoaded', function() {
    // Check if we need to be authenticated for this page
    const requiresAuth = document.body.classList.contains('requires-auth');

    if (requiresAuth && !getToken()) {
        // Redirect to login
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    }

    // Setup logout handler
    const logoutLink = document.querySelector('a[href="/auth/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            clearToken();
            window.location.href = '/auth/logout';
        });
    }
});