// Products Chart Manager
const ProductsChartManager = {
    chart: null,
    currentType: 'sales',
    
    init: function() {
        console.log('Initializing products chart...');
        const canvas = document.getElementById('topProductsChart');
        if (!canvas) {
            console.warn('Products chart canvas not found');
            return;
        }
        
        this.fetchData();
    },
    
    fetchData: function() {
        fetch('/api/dashboard/top_products/')
            .then(response => response.json())
            .then(data => {
                this.createChart(data);
            })
            .catch(error => {
                console.error('Error loading products chart:', error);
                this.showNoData();
            });
    },
    
    createChart: function(data) {
        const canvas = document.getElementById('topProductsChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const labels = data.labels && data.labels.length ? data.labels : ['No data'];
        const values = data.sales && data.sales.length ? data.sales : [0];
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sales ($)',
                    data: values,
                    backgroundColor: '#FF6384',
                    borderColor: '#2c3e50',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
            ticks: {
                callback: function(value) {
                    return '₱' + value;
                }
            }
                    }
                }
            }
        });
    },
    
    toggleType: function() {
        // Implementation for toggling between sales and quantity
    },
    
    showNoData: function() {
        const chart = document.getElementById('topProductsChart');
        const noData = document.getElementById('productsNoData');
        if (chart) chart.style.display = 'none';
        if (noData) noData.style.display = 'block';
    },
    
    destroy: function() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
};