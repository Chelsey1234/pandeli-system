// ========== NEW ORDER MODAL ==========

(function() {
    function checkJQuery() {
        if (typeof jQuery === 'undefined') {
            setTimeout(checkJQuery, 50);
            return;
        }
        $(document).ready(function() {
            setupModalEvents();
        });
    }

    function setupModalEvents() {
        $('#newOrderModal').on('show.bs.modal', function() {
            if (typeof OrderManager !== 'undefined' && typeof OrderManager.bindEvents === 'function') {
                setTimeout(function() {
                    try { OrderManager.bindEvents(); } catch(e) { console.error(e); }
                }, 50);
            }
        });

        $('#newOrderModal').on('shown.bs.modal', function() {
            loadProductsForModal();
        });
    }

    function loadProductsForModal() {
        var $modal = $('#newOrderModal');
        var $selects = $modal.find('.product-select');
        if (!$selects.length) return;

        $selects.prop('disabled', true).empty().append('<option value="">Loading products...</option>');

        function fillDropdowns(list) {
            var placeholder = '<option value="">-- Select Product --</option>';
            var opts = (list || []).map(function(p) {
                var price = parseFloat(p.price) || 0;
                var stock = parseInt(p.stock, 10) || 0;
                var name = (p.name || 'Product #' + p.id).replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return '<option value="' + p.id + '" data-price="' + price + '" data-stock="' + stock + '">'
                    + name + ' \u2014 \u20B1' + price.toLocaleString('en-PH', {minimumFractionDigits:2, maximumFractionDigits:2}) + ' (Stock: ' + stock + ')</option>';
            });
            $selects.prop('disabled', false).empty().append(placeholder + opts.join(''));
        }

        function showError(msg) {
            $selects.prop('disabled', false).empty()
                .append('<option value="">-- Select Product --</option>');
            console.warn('Product load error:', msg);
        }

        var opts = { method: 'GET', dataType: 'json', cache: false,
            xhrFields: { withCredentials: true },
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' } };

        $.ajax($.extend({}, opts, {
            url: '/api/order-modal-products/?_=' + Date.now(),
            success: function(data) {
                var list = data && Array.isArray(data.products) ? data.products : [];
                if (list.length > 0) { fillDropdowns(list); return; }
                // fallback to DRF products list
                $.ajax($.extend({}, opts, {
                    url: '/api/products/?_=' + Date.now(),
                    success: function(drf) {
                        fillDropdowns(Array.isArray(drf) ? drf : (drf.results || []));
                    },
                    error: function() { fillDropdowns([]); }
                }));
            },
            error: function(xhr) {
                var msg = 'Could not load products.';
                if (xhr.status === 401 || xhr.status === 403) msg = 'Please log in again.';
                else if (xhr.status >= 500) msg = 'Server error. Try again later.';
                showError(msg);
            }
        }));
    }

    checkJQuery();
})();
