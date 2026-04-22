// ========== AJAX SETUP ==========
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

// ========== UTILITIES ==========
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showLoading() {
    $('#loadingOverlay').remove();
    $('body').append(
        '<div id="loadingOverlay" style="position:fixed;top:0;left:0;width:100%;height:100%;' +
        'background:rgba(255,255,255,0.8);z-index:9999;display:flex;align-items:center;justify-content:center;">' +
        '<div class="spinner"></div></div>'
    );
}

function hideLoading() {
    $('#loadingOverlay').remove();
}

function formatCurrency(amount) {
    return '₱' + parseFloat(amount).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function confirmAction(message, callback) {
    if (confirm(message)) { callback(); }
}

// ========== NOTIFICATIONS ==========
function updateNotificationCount() {
    $.ajax({
        url: '/api/notifications/count/',
        method: 'GET',
        success: function(response) {
            var count = response.count || 0;
            var badge = $('#notificationBadge');
            if (count > 0) { badge.text(count).show(); } else { badge.hide(); }
        }
    });
}

function markAllAsRead() {
    $.ajax({
        url: '/api/notifications/mark-all-read/',
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        success: function(response) {
            if (response.success) {
                updateNotificationCount();
                location.reload();
            }
        }
    });
}

// ========== DASHBOARD ==========
function refreshDashboard() {
    showLoading();
    $.ajax({
        url: '/api/dashboard/summary/',
        method: 'GET',
        success: function(response) {
            $('#dailySales').text(formatCurrency(response.daily_sales));
            $('#monthlySales').text(formatCurrency(response.monthly_sales));
            $('#totalOrders').text(response.total_orders);
            $('#pendingOrders').text(response.pending_orders);
            hideLoading();
        },
        error: function() {
            hideLoading();
        }
    });
}

// ========== INIT ==========
$(document).ready(function() {
    updateNotificationCount();

    // Bootstrap tooltips
    var tooltipEls = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipEls.forEach(function(el) { new bootstrap.Tooltip(el); });

    // Bootstrap popovers
    var popoverEls = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverEls.forEach(function(el) { new bootstrap.Popover(el); });
});

// Auto-refresh notification count every 30s
setInterval(updateNotificationCount, 30000);

// Auto-refresh dashboard every 5 min
setInterval(function() {
    if (window.location.pathname === '/dashboard/') { refreshDashboard(); }
}, 300000);
