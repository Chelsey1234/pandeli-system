// ========== NEW ORDER MODAL ==========
// This file handles the new order modal initialization and interactions

console.log('📦 New Order Modal JS loaded');

// Wait for jQuery to be fully loaded
(function() {
    // Check if jQuery is available
    function checkJQuery() {
        if (typeof jQuery === 'undefined' && typeof $ === 'undefined') {
            console.log('⏳ Waiting for jQuery to load...');
            setTimeout(checkJQuery, 50);
            return false;
        }
        
        console.log('✅ jQuery detected, version:', ($.fn && $.fn.jquery) ? $.fn.jquery : 'unknown');
        
        // jQuery is now available, initialize everything
        initializeModalHandlers();
        return true;
    }
    
    // Initialize all modal handlers
    function initializeModalHandlers() {
        console.log('🔧 Initializing modal handlers...');
        
        // Make sure DOM is ready
        $(document).ready(function() {
            console.log('📄 DOM ready in modal');
            
            // Set up all event listeners
            setupModalEvents();
            
            // Log success
            console.log('✅ Modal handlers initialized');
        });
    }
    
    // Set up modal events
    function setupModalEvents() {
        console.log('🔗 Setting up modal events');
        
        // When modal is about to open, rebind order form events (scoped to this modal)
        $('#newOrderModal').on('show.bs.modal', function() {
            if (typeof OrderManager !== 'undefined' && typeof OrderManager.bindEvents === 'function') {
                setTimeout(function() {
                    try {
                        OrderManager.bindEvents();
                    } catch (e) {
                        console.error('Order modal bindEvents error:', e);
                    }
                }, 50);
            }
        });
        
        // When modal is fully shown, always load products via AJAX so dropdown works on every page
        $('#newOrderModal').on('shown.bs.modal', function() {
            console.log('✅ New Order Modal fully shown');
            loadProductsForModal();
        });
        
        // When modal is closed
        $('#newOrderModal').on('hidden.bs.modal', function() {
            console.log('🔒 New Order Modal closed');
        });
        
        // Also handle any clicks on elements that open the modal
        $(document).on('click', '[data-target="#newOrderModal"], [data-bs-target="#newOrderModal"]', function() {
            console.log('👆 Modal trigger clicked');
        });
    }
    
    // Always load products via AJAX when modal opens (works on every page, single source of truth)
    function loadProductsForModal() {
        var $modal = $('#newOrderModal');
        var $selects = $modal.find('.product-select');
        if ($selects.length === 0) return;

        $modal.find('.alert-warning, .alert-danger').remove();
        var $first = $selects.first();
        $first.prop('disabled', true).empty().append('<option value="">Loading products...</option>');
        $selects.not(':first').each(function() {
            $(this).prop('disabled', true).empty().append('<option value="">Loading...</option>');
        });

        function fillProductDropdown(list) {
            var placeholder = '<option value="">-- Select Product --</option>';
            var opts = (list || []).map(function(p) {
                var price = p.price != null ? parseFloat(p.price) : 0;
                var stock = p.stock != null ? parseInt(p.stock, 10) : 0;
                var name = (p.name || 'Product #' + (p.id || '')).replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return '<option value="' + p.id + '" data-price="' + price + '" data-stock="' + stock + '">' +
                    name + ' - $' + price.toFixed(2) + ' (Stock: ' + stock + ')</option>';
            });
            var html = placeholder + opts.join('');
            $selects.each(function() {
                $(this).prop('disabled', false).empty().append(html);
            });
            if ((list || []).length === 0) {
                $modal.find('.modal-body').prepend(
                    '<div class="alert alert-warning alert-dismissible fade show mt-2" role="alert">' +
                    '<i class="fas fa-exclamation-triangle me-2"></i>No products found. Add products on the <a href="/products/">Products</a> page, then open this modal again.' +
                    '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
                );
            }
        }

        function showLoadError(msg) {
            $selects.each(function() {
                $(this).prop('disabled', false).empty().append(
                    '<option value="">-- Select Product --</option>' +
                    '<option value="" disabled>Could not load products.</option>'
                );
            });
            $modal.find('.modal-body').prepend(
                '<div class="alert alert-danger alert-dismissible fade show mt-2" role="alert">' +
                '<i class="fas fa-exclamation-circle me-2"></i>' + msg +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>'
            );
        }

        var ajaxOpts = {
            method: 'GET',
            dataType: 'json',
            cache: false,
            xhrFields: { withCredentials: true },
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
        };

        // 1) Try dedicated modal endpoint
        $.ajax($.extend({}, ajaxOpts, {
            url: '/api/order-modal-products/?_=' + (new Date().getTime()),
            success: function(data) {
                var list = data && data.products && Array.isArray(data.products) ? data.products : [];
                if (list.length > 0) {
                    fillProductDropdown(list);
                    return;
                }
                // 2) Fallback: use DRF products list (same auth, paginated)
                $.ajax($.extend({}, ajaxOpts, {
                    url: '/api/products/?_=' + (new Date().getTime()),
                    success: function(drf) {
                        var results = (drf && drf.results && Array.isArray(drf.results)) ? drf.results : [];
                        fillProductDropdown(results);
                    },
                    error: function() { fillProductDropdown([]); }
                }));
            },
            error: function(xhr) {
                var msg = 'Could not load products. ';
                if (xhr.status === 401) msg = 'Please log in again, then try opening Create New Order.';
                else if (xhr.status === 403 || xhr.status === 302) msg += 'Make sure you are logged in.';
                else if (xhr.status >= 500) msg += 'Server error. Try again later.';
                showLoadError(msg);
            }
        }));
    }

    // Start checking for jQuery
    checkJQuery();
})();

// ========== DEBUG FUNCTIONS ==========
// These can be called from the console for troubleshooting

window.checkModalState = function() {
    console.log('🔍 Checking modal state:');
    
    if (typeof $ === 'undefined') {
        console.log('❌ jQuery is NOT loaded');
        return { error: 'jQuery not loaded' };
    }
    
    const state = {
        jQuery: $.fn.jquery,
        modal: $('#newOrderModal').length > 0,
        addItem: $('#addItem').length > 0,
        saveOrder: $('#saveOrder').length > 0,
        orderManager: typeof OrderManager !== 'undefined',
        productRows: $('.item-row').length,
        productSelect: $('.product-select').length > 0,
    };
    
    // Count products
    if (state.productSelect) {
        const options = $('.product-select option');
        state.totalOptions = options.length;
        state.products = options.length - ($('.product-select option[value=""]').length ? 1 : 0);
    }
    
    console.table(state);
    return state;
};

window.fixModal = function() {
    console.log('🔧 Attempting to fix modal...');
    
    if (typeof $ === 'undefined') {
        console.log('❌ Cannot fix: jQuery not loaded');
        return false;
    }
    
    // Re-initialize OrderManager if it exists
    if (typeof OrderManager !== 'undefined') {
        console.log('✅ Re-initializing OrderManager');
        OrderManager.init();
    } else {
        console.log('❌ OrderManager not found');
    }
    
    // Force bind events
    if (typeof OrderManager !== 'undefined' && OrderManager.bindEvents) {
        OrderManager.bindEvents();
    }
    
    console.log('✅ Fix attempt complete');
    return true;
};

window.resetModal = function() {
    console.log('🔄 Resetting modal');
    
    if (typeof $ === 'undefined') {
        console.log('❌ Cannot reset: jQuery not loaded');
        return false;
    }
    
    if (typeof OrderManager !== 'undefined' && OrderManager.resetModal) {
        OrderManager.resetModal();
        console.log('✅ Modal reset');
        return true;
    } else {
        console.log('❌ OrderManager.resetModal not available');
        return false;
    }
};

console.log('✅ New Order Modal JS setup complete');
console.log('ℹ️ Debug commands: checkModalState(), fixModal(), resetModal()');