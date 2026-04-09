// AJAX Setup
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

// Get CSRF Token
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

// Show Loading Spinner
function showLoading() {
    $('#loadingOverlay').remove();
    var overlay = $('<div id="loadingOverlay" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(255,255,255,0.8); z-index:9999; display:flex; align-items:center; justify-content:center;">' +
        '<div class="spinner"></div>' +
        '</div>');
    $('body').append(overlay);
}

// Hide Loading Spinner
function hideLoading() {
    $('#loadingOverlay').remove();
}

// Show Toast Notification
function showToast(message, type = 'success') {
    var toast = $('<div class="toast align-items-center text-white bg-' + type + ' border-0" role="alert" aria-live="assertive" aria-atomic="true">' +
        '<div class="d-flex">' +
        '<div class="toast-body">' +
        message +
        '</div>' +
        '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
        '</div>' +
        '</div>');
    
    $('body').append(toast);
    var bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    setTimeout(function() {
        toast.remove();
    }, 3000);
}

// Format Currency
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

// Format Date
function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Confirm Action
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Load Notifications
function loadNotifications() {
    $.ajax({
        url: '/api/notifications/',
        method: 'GET',
        success: function(response) {
            // Update notification dropdown
            var dropdown = $('.notification-dropdown .dropdown-menu');
            dropdown.empty();
            
            if (response.length > 0) {
                $.each(response, function(i, notification) {
                    var item = $('<li>' +
                        '<a class="dropdown-item" href="/messages/?read=' + notification.id + '">' +
                        '<div class="d-flex align-items-center">' +
                        '<div class="flex-shrink-0">' +
                        (notification.is_read ? '' : '<span class="dot bg-primary"></span>') +
                        '</div>' +
                        '<div class="flex-grow-1 ms-2">' +
                        '<strong>' + notification.title + '</strong><br>' +
                        '<small>' + notification.message.substring(0, 50) + '...</small><br>' +
                        '<small class="text-muted">' + moment(notification.created_at).fromNow() + '</small>' +
                        '</div>' +
                        '</div>' +
                        '</a>' +
                        '</li>');
                    dropdown.append(item);
                });
            } else {
                dropdown.append('<li><span class="dropdown-item text-muted">No notifications</span></li>');
            }
            
            dropdown.append('<li><hr class="dropdown-divider"></li>');
            dropdown.append('<li><a class="dropdown-item text-center" href="/messages/">View All</a></li>');
            
            // Update badge count
            var unreadCount = response.filter(function(n) { return !n.is_read; }).length;
            $('.notification-badge').text(unreadCount);
            if (unreadCount > 0) {
                $('.notification-badge').show();
            } else {
                $('.notification-badge').hide();
            }
        }
    });
}

// Refresh Dashboard Data
function refreshDashboard() {
    showLoading();
    
    $.ajax({
        url: '/api/dashboard/summary/',
        method: 'GET',
        success: function(response) {
            // Update dashboard widgets
            $('#dailySales').text(formatCurrency(response.daily_sales));
            $('#monthlySales').text(formatCurrency(response.monthly_sales));
            $('#totalOrders').text(response.total_orders);
            $('#pendingOrders').text(response.pending_orders);
            
            hideLoading();
        },
        error: function() {
            hideLoading();
            showToast('Error refreshing dashboard', 'danger');
        }
    });
}

// Export Data
function exportData(type, format = 'excel') {
    window.location.href = '/export/?type=' + type + '&format=' + format;
}

// Import Data
function importData(file, importType) {
    var formData = new FormData();
    formData.append('file', file);
    formData.append('import_type', importType);
    
    showLoading();
    
    $.ajax({
        url: '/import/',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideLoading();
            showToast('Import completed successfully');
            setTimeout(function() {
                location.reload();
            }, 1500);
        },
        error: function(xhr) {
            hideLoading();
            showToast('Error importing data: ' + xhr.responseJSON.error, 'danger');
        }
    });
}

// Auto-refresh every 5 minutes
setInterval(function() {
    if (window.location.pathname === '/dashboard/') {
        refreshDashboard();
    }
}, 300000);

// Load notifications every minute
setInterval(loadNotifications, 60000);

// Initialize on document ready
$(document).ready(function() {
    // Load initial notifications
    loadNotifications();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

// ========== NOTIFICATION FUNCTIONS ==========

// Load notifications
function loadNotifications() {
    $.ajax({
        url: '/api/notifications/',
        method: 'GET',
        data: { limit: 5 },
        success: function(response) {
            updateNotificationDropdown(response.notifications);
        },
        error: function() {
            console.error('Failed to load notifications');
        }
    });
    
    // Also update the count
    updateNotificationCount();
}

// Update notification count
function updateNotificationCount() {
    $.ajax({
        url: '/api/notifications/count/',
        method: 'GET',
        success: function(response) {
            var count = response.count;
            var badge = $('#notificationBadge');
            
            if (count > 0) {
                badge.text(count).show();
            } else {
                badge.hide();
            }
        }
    });
}

// Update notification dropdown with data
function updateNotificationDropdown(notifications) {
    var list = $('#notificationList');
    list.empty();
    
    if (notifications.length === 0) {
        list.html('<li class="text-center py-4 text-muted"><i class="fas fa-bell-slash fa-2x mb-2"></i><br>No notifications</li>');
        return;
    }
    
    $.each(notifications, function(i, notification) {
        var priorityClass = '';
        if (notification.priority === 'urgent') priorityClass = 'border-danger';
        else if (notification.priority === 'high') priorityClass = 'border-warning';
        
        var item = $('<li class="dropdown-item ' + priorityClass + '" style="border-left: 3px solid; white-space: normal;">' +
            '<div class="d-flex align-items-start">' +
            '<div class="flex-shrink-0 me-2">' +
            (notification.is_read ? '' : '<span class="dot bg-primary" style="width: 8px; height: 8px; display: inline-block; border-radius: 50%;"></span>') +
            '</div>' +
            '<div class="flex-grow-1">' +
            '<strong>' + notification.title + '</strong><br>' +
            '<small class="text-muted">' + notification.message + '</small><br>' +
            '<small class="text-muted"><i class="far fa-clock"></i> ' + notification.time_ago + '</small>' +
            '</div>' +
            '</div>' +
            '</li>');
        
        // Make item clickable
        item.css('cursor', 'pointer');
        item.click(function() {
            markAsRead(notification.id);
            if (notification.link) {
                window.location.href = notification.link;
            }
        });
        
        list.append(item);
    });
}

// Mark single notification as read
function markAsRead(notificationId) {
    $.ajax({
        url: '/api/notifications/' + notificationId + '/read/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function() {
            updateNotificationCount();
            loadNotifications();
        }
    });
}

// Mark all notifications as read
function markAllAsRead() {
    $.ajax({
        url: '/api/notifications/mark-all-read/',
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        success: function(response) {
            if (response.success) {
                showToast('Marked ' + response.count + ' notifications as read', 'success');
                updateNotificationCount();
                loadNotifications();
            }
        }
    });
}

// Auto-refresh notifications every 30 seconds
setInterval(function() {
    updateNotificationCount();
    if ($('#notificationDropdown').hasClass('show')) {
        loadNotifications();
    }
}, 30000);

// Load notifications when dropdown is opened
$(document).ready(function() {
    $('#notificationDropdown').on('show.bs.dropdown', function() {
        loadNotifications();
    });
    
    // Initial load of notification count
    updateNotificationCount();


    $(document).ready(function() {
    $('#saveProduct').click(function() {
        var data = {
            name: $('#productName').val(),
            price: $('#productPrice').val(),
            stock: $('#productStock').val()
        };

        if (!data.name || !data.price || !data.stock) {
            alert('Please fill all fields');
            return;
        }

        $.ajax({
            url: '/api/products/',  // make sure your API endpoint exists
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}'
            },
            data: JSON.stringify(data),
            contentType: 'application/json',
            success: function(response) {
                $('#addProductModal').modal('hide');
                alert('Product added successfully!');
                location.reload(); // reload to see new product in the list
            },
            error: function(xhr) {
                alert('Error: ' + xhr.responseJSON.error);
            }
        });
    });
});

});

});