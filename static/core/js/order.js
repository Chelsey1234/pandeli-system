// ========== ORDER MANAGEMENT ==========

const OrderManager = {
    init: function() {
        console.log('OrderManager initializing...');
        this.bindEvents();
        console.log('OrderManager initialized');
    },
    
    bindEvents: function() {
        const self = this;
        const $modal = $('#newOrderModal');
        if (!$modal.length) return;
        console.log('Binding order events...');

        // Add item row (scope to modal)
        $modal.find('#addItem').off('click').on('click', function(e) {
            e.preventDefault();
            self.addItemRow();
        });

        // Remove item row (delegate within modal)
        $modal.off('click', '.remove-item').on('click', '.remove-item', function(e) {
            e.preventDefault();
            self.removeItemRow($(this));
        });

        // Product selection change
        $modal.off('change', '.product-select').on('change', '.product-select', function() {
            self.onProductSelect($(this));
        });

        // Quantity change
        $modal.off('input', '.quantity').on('input', '.quantity', function() {
            self.onQuantityChange($(this));
        });

        // Save order
        $modal.find('#saveOrder').off('click').on('click', function(e) {
            e.preventDefault();
            self.saveOrder();
        });

        // Reset modal on close
        $modal.off('hidden.bs.modal').on('hidden.bs.modal', function() {
            self.resetModal();
        });

        console.log('Order events bound successfully');
    },
    
    addItemRow: function() {
        const $modal = $('#newOrderModal');
        const $first = $modal.find('.item-row:first');
        if (!$first.length) return;
        const newRow = $first.clone();
        newRow.find('input').val('');
        newRow.find('select').val('');
        newRow.find('.price').val('');
        newRow.find('.subtotal').val('');
        newRow.find('.quantity').val(1).removeAttr('max');
        $modal.find('#orderItemsBody').append(newRow);
    },

    removeItemRow: function(button) {
        const $modal = $('#newOrderModal');
        if ($modal.find('.item-row').length <= 1) return;
        button.closest('.item-row').remove();
        this.calculateTotal();
    },
    
    // Helper function to convert any price to a number
    parsePrice: function(price) {
        if (price === null || price === undefined) return 0;
        
        // If it's already a number, return it
        if (typeof price === 'number') return price;
        
        // If it's a string, clean it and parse
        if (typeof price === 'string') {
            // Remove any non-numeric characters except decimal point
            const cleaned = price.replace(/[^0-9.-]/g, '');
            const parsed = parseFloat(cleaned);
            return isNaN(parsed) ? 0 : parsed;
        }
        
        // Try direct parse
        const parsed = parseFloat(price);
        return isNaN(parsed) ? 0 : parsed;
    },
    
    onProductSelect: function(select) {
        const row = select.closest('.item-row');
        const selectedOption = select.find('option:selected');
        
        // Get price from data attribute
        let price = selectedOption.data('price');
        console.log('Raw price from data():', price, 'type:', typeof price);
        
        // If data() returns undefined, try attr()
        if (price === undefined) {
            price = selectedOption.attr('data-price');
            console.log('Price from attr():', price);
        }
        
        // Parse the price using our helper
        const priceNum = this.parsePrice(price);
        console.log('Parsed price:', priceNum);
        
        // Set the price field
        if (priceNum > 0) {
            row.find('.price').val(priceNum.toFixed(2));
            console.log('✅ Price set to:', priceNum.toFixed(2));
        } else {
            row.find('.price').val('');
            console.warn('❌ Invalid price:', price);
        }
        
        // Get stock
        let stock = selectedOption.data('stock');
        if (stock === undefined) {
            stock = selectedOption.attr('data-stock');
        }
        
        const stockNum = parseInt(stock) || 0;
        const quantityInput = row.find('.quantity');
        
        if (stockNum > 0) {
            quantityInput.attr('max', stockNum);
            quantityInput.attr('title', 'Max available: ' + stockNum);
        } else {
            quantityInput.removeAttr('max');
        }
        
        // Reset quantity to 1
        quantityInput.val(1);
        this.calculateSubtotal(row);
    },
    
    onQuantityChange: function(input) {
        const row = input.closest('.item-row');
        const max = parseInt(input.attr('max')) || 9999;
        let value = parseInt(input.val()) || 0;
        
        if (value < 1) {
            input.val(1);
            value = 1;
        }
        
        if (max < 9999 && value > max) {
            input.val(max);
            alert('Only ' + max + ' items available in stock');
            value = max;
        }
        
        this.calculateSubtotal(row);
    },
    
    calculateSubtotal: function(row) {
        const quantity = parseFloat(row.find('.quantity').val()) || 0;
        const priceStr = row.find('.price').val();
        const price = parseFloat(priceStr) || 0;
        const subtotal = quantity * price;
        row.find('.subtotal').val(subtotal.toFixed(2));
        this.calculateTotal();
    },

    calculateTotal: function() {
        const $modal = $('#newOrderModal');
        let total = 0;
        $modal.find('.subtotal').each(function() {
            total += parseFloat($(this).val()) || 0;
        });
        $modal.find('#orderTotal').val(total.toFixed(2));
    },

    validateOrder: function() {
        const $modal = $('#newOrderModal');
        const items = [];
        let hasItems = false;
        $modal.find('.item-row').each(function() {
            const productId = $(this).find('.product-select').val();
            const quantity = $(this).find('.quantity').val();
            if (productId && quantity) {
                hasItems = true;
                items.push({
                    product_id: parseInt(productId, 10),
                    quantity: parseInt(quantity, 10)
                });
            }
        });
        if (!hasItems) {
            return { isValid: false, errorMessage: 'Please add at least one product and quantity.', items: [] };
        }
        return { isValid: true, errorMessage: '', items: items };
    },
    
    saveOrder: function() {
        const $modal = $('#newOrderModal');
        const validation = this.validateOrder();
        if (!validation.isValid) {
            alert(validation.errorMessage);
            return;
        }

        const saveBtn = $modal.find('#saveOrder');
        const originalText = saveBtn.html();
        saveBtn.html('<i class="fas fa-spinner fa-spin"></i> Processing...').prop('disabled', true);

        const csrftoken = $modal.find('[name=csrfmiddlewaretoken]').val();
        if (!csrftoken) {
            alert('Session expired. Please refresh the page and try again.');
            saveBtn.html(originalText).prop('disabled', false);
            return;
        }

        const orderData = {
            order_type: $modal.find('#orderType').val() || 'walk_in',
            notes: $modal.find('#orderNotes').val() || '',
            items: validation.items
        };

        $.ajax({
            url: '/api/orders/',
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
            data: JSON.stringify(orderData),
            success: function(response) {
                $('#newOrderModal').modal('hide');
                alert('Order created: #' + (response.order_number || response.id));
                setTimeout(function() { location.reload(); }, 1000);
            },
            error: function(xhr) {
                let errorMsg = 'Error creating order.';
                try {
                    const data = JSON.parse(xhr.responseText);
                    errorMsg = data.error || data.detail || data.message || errorMsg;
                } catch (e) {
                    if (xhr.responseText) errorMsg = xhr.responseText.substring(0, 100);
                }
                alert(errorMsg);
                saveBtn.html(originalText).prop('disabled', false);
            }
        });
    },
    
    resetModal: function() {
        const $modal = $('#newOrderModal');
        const $body = $modal.find('#orderItemsBody');
        $body.find('.item-row:not(:first)').remove();
        const $first = $body.find('.item-row:first');
        $first.find('.product-select').val('');
        $first.find('.quantity').val(1).removeAttr('max');
        $first.find('.price').val('');
        $first.find('.subtotal').val('');
        $modal.find('#orderTotal').val('0.00');
        $modal.find('#orderType').val('walk_in');
        $modal.find('#orderNotes').val('');
    }
};

$(document).ready(function() {
    console.log('Document ready - initializing OrderManager');
    OrderManager.init();
});