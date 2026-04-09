// Line Chart Manager
const LineChartManager = {
    chart: null,
    
    init: function() {
        console.log('Initializing line chart...');
        const canvas = document.getElementById('salesLineChart');
        if (!canvas) {
            console.warn('Sales line chart canvas not found');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Get data from window object (passed from Django template)
        const labels = window.salesLabels || [];
        const data = window.salesData || [];
        
        // Always show chart - use zeros if no data (better than empty gray block)
        const hasRealData = labels.length && data.length && !data.every(val => val === 0);
        const displayLabels = labels.length ? labels : [];
        const displayData = data.length ? data : (Array(7).fill(0));
        const fallbackLabels = displayLabels.length ? displayLabels : Array.from({length: 7}, (_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - (6 - i));
            return d.toISOString().slice(0, 10);
        });
        
        this.hideNoData();
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: fallbackLabels,
                datasets: [{
                    label: hasRealData ? 'Sales ($)' : 'Sales ($) - No data yet',
                    data: displayData.length ? displayData : Array(7).fill(0),
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Sales: ₱' + context.raw.toFixed(2);
                            }
                        }
                    }
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
        
        console.log('Line chart initialized successfully');
    },
    
    refresh: function(days = 7) {
        fetch(`/api/dashboard/sales_chart/?days=${days}`)
            .then(response => response.json())
            .then(data => {
                const labels = data.map(item => item.date);
                const values = data.map(item => item.total);
                
                if (this.chart) {
                    this.chart.data.labels = labels;
                    this.chart.data.datasets[0].data = values;
                    this.chart.update();
                }
            })
            .catch(error => {
                console.error('Error refreshing line chart:', error);
            });
    },
    
    destroy: function() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    },
    
    showNoData: function() {
        const chart = document.getElementById('salesLineChart');
        const noData = document.getElementById('lineChartNoData');
        if (chart) chart.style.display = 'none';
        if (noData) noData.style.display = 'block';
    },
    
    hideNoData: function() {
        const chart = document.getElementById('salesLineChart');
        const noData = document.getElementById('lineChartNoData');
        if (chart) chart.style.display = 'block';
        if (noData) noData.style.display = 'none';
    }
};