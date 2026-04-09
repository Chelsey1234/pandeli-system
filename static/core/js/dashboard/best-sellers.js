// Best Sellers Chart Manager
const BestSellersChartManager = {
    chart: null,
    initialized: false,  // Add this flag
    
    init: function() {
        // Prevent multiple initializations
        if (this.initialized) {
            console.log('Best sellers chart already initialized');
            return;
        }
        
        console.log('Initializing best sellers chart...');
        const canvas = document.getElementById('bestSellersChart');
        if (!canvas) {
            console.warn('Best sellers chart canvas not found');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        // Get data from window object - show placeholder when empty
        const data = window.bestSellers || [];
        const labels = data.length ? data.map(item => item.name) : ['No sales yet'];
        const values = data.length ? data.map(item => item.quantity) : [0];
        
        this.hideNoData();
        
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Quantity Sold',
                    data: values,
                    backgroundColor: '#FFCE56',
                    borderColor: '#2c3e50',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1.2,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true },
                    x: { maxRotation: 45, minRotation: 0 }
                }
            }
        });
        
        this.initialized = true;
        console.log('Best sellers chart initialized');
    },
    
    showNoData: function() {
        const chart = document.getElementById('bestSellersChart');
        const noData = document.getElementById('bestSellersNoData');
        if (chart) chart.style.display = 'none';
        if (noData) noData.style.display = 'block';
    },
    
    hideNoData: function() {
        const chart = document.getElementById('bestSellersChart');
        const noData = document.getElementById('bestSellersNoData');
        if (chart) chart.style.display = 'block';
        if (noData) noData.style.display = 'none';
    },
    
    // Add destroy method
    destroy: function() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        this.initialized = false;
        console.log('Best sellers chart destroyed');
    }
};