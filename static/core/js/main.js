// ========== UTILITY FUNCTIONS ==========

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatCurrency(amount) {
    return '\u20B1' + parseFloat(amount).toFixed(2);
}

// ========== TOAST ==========
function showToast(message, type = 'success') {
    let container = document.getElementById('tw-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'tw-toast-container';
        container.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
        document.body.appendChild(container);
    }
    const colors = { success:'#7C4A2D', danger:'#c0392b', error:'#c0392b', warning:'#b7791f', info:'#2b6cb0' };
    const bg = colors[type] || colors.success;
    const toast = document.createElement('div');
    toast.style.cssText = 'background:' + bg + ';color:#fff;padding:0.75rem 1rem;border-radius:0.75rem;' +
        'font-size:0.875rem;display:flex;align-items:center;gap:0.75rem;min-width:260px;max-width:360px;' +
        'box-shadow:0 4px 12px rgba(0,0,0,0.15);animation:slideIn 0.2s ease;';
    toast.innerHTML = '<span style="flex:1">' + message + '</span>' +
        '<button onclick="this.parentElement.remove()" style="background:none;border:none;color:rgba(255,255,255,0.7);cursor:pointer;font-size:1rem;">\u2715</button>';
    container.appendChild(toast);
    setTimeout(function() { if (toast.parentNode) toast.remove(); }, 4000);
}

// ========== SIDEBAR TOGGLE ==========
document.addEventListener('DOMContentLoaded', function() {
    var sidebar = document.getElementById('sidebar');
    var btn     = document.getElementById('sidebarCollapse');
    var icon    = document.getElementById('sidebarToggleIcon');

    function applyState(collapsed) {
        if (!sidebar) return;
        if (collapsed) {
            sidebar.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
        }
    }

    // Default: expanded (ignore any stale localStorage)
    localStorage.removeItem('sidebarCollapsed');
    applyState(false);

    if (btn && sidebar) {
        btn.addEventListener('click', function() {
            var isNowCollapsed = !sidebar.classList.contains('collapsed');
            applyState(isNowCollapsed);
        });
    }
});

// ========== NOTIFICATION MANAGER ==========
const NotificationManager = {
    markAllAsRead: function() {
        fetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' }
        })
        .then(r => r.json())
        .then(data => { if (data.success) location.reload(); })
        .catch(e => console.error(e));
    },

    markAsRead: function(notificationId) {
        fetch('/api/notifications/' + notificationId + '/read/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' }
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const badge = document.querySelector('.notification-badge');
                if (badge) {
                    const count = parseInt(badge.textContent) - 1;
                    if (count > 0) badge.textContent = count;
                    else badge.style.display = 'none';
                }
            }
        })
        .catch(e => console.error(e));
    },

    getCount: function() {
        fetch('/api/notifications/count/')
            .then(r => r.json())
            .then(data => {
                const badge = document.querySelector('.notification-badge');
                if (!badge) return;
                if (data.count > 0) { badge.textContent = data.count; badge.style.display = 'inline'; }
                else badge.style.display = 'none';
            })
            .catch(e => console.error(e));
    }
};

setInterval(function() { NotificationManager.getCount(); }, 30000);
