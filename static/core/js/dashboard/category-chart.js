// Category Chart Manager
const CategoryChartManager = {
    chart: null,
    currentType: 'sales',
    
    init: function() {
        console.log('Initializing category chart...');
        const canvas = document.getElementById('categoryBarChart');
        if (!canvas) {
            console.warn('Category chart canvas not found');
            return;
        }
        
        this.fetchData();
    },
    
    fetchData: function() {
        fetch('/api/dashboard/sales_by_category/')
            .then(response => response.json())
            .then(data => {
                this.createChart(data);
            })
            .catch(error => {
                console.error('Error loading category chart:', error);
                this.showNoData();
            });
    },
    
    createChart: function(data) {
        const canvas = document.getElementById('categoryBarChart');
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
                    backgroundColor: '#36A2EB',
                    borderColor: '#2c3e50',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
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
        const chart = document.getElementById('categoryBarChart');
        const noData = document.getElementById('categoryNoData');
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