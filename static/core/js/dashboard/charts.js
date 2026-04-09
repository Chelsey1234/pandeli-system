// ========== DASHBOARD CHARTS MANAGER ==========

const DashboardCharts = {
    initialized: false,
    
    init: function() {
        console.log('Initializing dashboard charts...');
        
        // First destroy any existing charts
        this.destroyAll();
        
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            // Initialize each chart if its manager exists
            if (typeof LineChartManager !== 'undefined') {
                try {
                    LineChartManager.init();
                } catch (e) {
                    console.error('Error initializing LineChartManager:', e);
                }
            }
            
            if (typeof CategoryChartManager !== 'undefined') {
                try {
                    CategoryChartManager.init();
                } catch (e) {
                    console.error('Error initializing CategoryChartManager:', e);
                }
            }
            
            if (typeof ProductsChartManager !== 'undefined') {
                try {
                    ProductsChartManager.init();
                } catch (e) {
                    console.error('Error initializing ProductsChartManager:', e);
                }
            }
            
            if (typeof BestSellersChartManager !== 'undefined') {
                try {
                    BestSellersChartManager.init();
                } catch (e) {
                    console.error('Error initializing BestSellersChartManager:', e);
                }
            }
            
            this.initialized = true;
            console.log('Dashboard charts initialized');
        }, 100);
    },
    
    destroyAll: function() {
        // Destroy all charts if they have destroy methods
        if (typeof LineChartManager !== 'undefined' && LineChartManager.destroy) {
            LineChartManager.destroy();
        }
        if (typeof CategoryChartManager !== 'undefined' && CategoryChartManager.destroy) {
            CategoryChartManager.destroy();
        }
        if (typeof ProductsChartManager !== 'undefined' && ProductsChartManager.destroy) {
            ProductsChartManager.destroy();
        }
        if (typeof BestSellersChartManager !== 'undefined' && BestSellersChartManager.destroy) {
            BestSellersChartManager.destroy();
        }
    },
    
    showNoData: function(chartId, messageId) {
        const chart = document.getElementById(chartId);
        const message = document.getElementById(messageId);
        if (chart) chart.style.display = 'none';
        if (message) message.style.display = 'block';
    },
    
    showChart: function(chartId, messageId) {
        const chart = document.getElementById(chartId);
        const message = document.getElementById(messageId);
        if (chart) chart.style.display = 'block';
        if (message) message.style.display = 'none';
    }
};

// Initialize when DOM is ready - ONLY ONCE
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        DashboardCharts.init();
    });
} else {
    DashboardCharts.init();
}