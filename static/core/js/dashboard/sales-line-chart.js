// Sales Line Chart Manager
const LineChartManager = {
    chart: null,
    currentPeriod: 7,
    
    // Initialize chart with data
    init: function(data) {
        this.setupPeriodButtons();
        this.createChart(data);
        this.updateStats(data.data);
    },
    
    // Create the chart
    createChart: function(data) {
        const ctx = document.getElementById('salesLineChart').getContext('2d');
        
        // Check if we have data
        if (data.data.length === 0 || data.data.every(val => val === 0)) {
            this.showNoData();
            return;
        }
        
        this.hideNoData();
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Sales',
                    data: data.data,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Sales: $' + context.raw.toFixed(2);
                            }
                        },
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#667eea',
                        borderWidth: 2
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                },
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10
                    }
                }
            }
        });
    },
    
    // Setup period selector buttons
    setupPeriodButtons: function() {
        const buttons = document.querySelectorAll('.period-btn');
        const self = this;
        
        buttons.forEach(btn => {
            btn.addEventListener('click', function() {
                // Update active state
                buttons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // Refresh chart with new period
                self.currentPeriod = this.dataset.period;
                self.refresh();
            });
        });
        
        // Set default active
        const defaultBtn = document.querySelector('.period-btn[data-period="7"]');
        if (defaultBtn) defaultBtn.classList.add('active');
    },
    
    // Refresh chart with new data
    refresh: function() {
        const self = this;
        
        fetch(`/api/dashboard/sales_chart/?days=${this.currentPeriod}`)
            .then(response => response.json())
            .then(data => {
                const labels = data.map(item => item.date);
                const values = data.map(item => item.total);
                
                // Check if we have data
                if (values.length === 0 || values.every(val => val === 0)) {
                    this.showNoData();
                    return;
                }
                
                this.hideNoData();
                
                // Update chart
                if (this.chart) {
                    this.chart.data.labels = labels;
                    this.chart.data.datasets[0].data = values;
                    this.chart.update();
                }
                
                // Update stats
                this.updateStats(values);
            })
            .catch(error => {
                console.error('Error refreshing chart:', error);
                this.showNoData();
            });
    },
    
    // Show no data message
    showNoData: function() {
        document.getElementById('salesLineChart').style.display = 'none';
        document.getElementById('lineChartNoData').style.display = 'block';
        document.getElementById('chartStats').style.display = 'none';
    },
    
    // Hide no data message
    hideNoData: function() {
        document.getElementById('salesLineChart').style.display = 'block';
        document.getElementById('lineChartNoData').style.display = 'none';
        document.getElementById('chartStats').style.display = 'flex';
    },
    
    // Update statistics
    updateStats: function(data) {
        if (!data || data.length === 0) {
            return;
        }
        
        // Calculate average
        const sum = data.reduce((a, b) => a + b, 0);
        const avg = sum / data.length;
        document.getElementById('avgDaily').textContent = '$' + avg.toFixed(2);
        
        // Find peak day
        const max = Math.max(...data);
        const maxIndex = data.indexOf(max);
        const labels = this.chart ? this.chart.data.labels : [];
        const peakDay = labels[maxIndex] || 'N/A';
        document.getElementById('peakDay').textContent = peakDay;
        
        // Total sales
        document.getElementById('totalSales').textContent = '$' + sum.toFixed(2);
    },
    
    // Export chart as image
    exportAsImage: function() {
        if (!this.chart) return;
        
        const link = document.createElement('a');
        link.download = 'sales-chart.png';
        link.href = this.chart.toBase64Image();
        link.click();
    },
    
    // Print chart
    print: function() {
        if (!this.chart) return;
        
        const win = window.open('');
        win.document.write('<img src="' + this.chart.toBase64Image() + '"/>');
        win.print();
        win.close();
    }
};