// ========== CATEGORY CHART — RdYlBu staggered bars ==========
const CategoryChartManager = {
    chart: null,
    currentPeriod: 30,
    currentType: 'sales',

    init: function() {
        if (!document.getElementById('categoryBarChart')) return;
        this.fetchData();
    },

    fetchData: function() {
        var self = this;
        fetch('/api/dashboard/sales_by_category/?days=' + this.currentPeriod)
            .then(function(r) { return r.json(); })
            .then(function(data) { self.createChart(data); })
            .catch(function() { self.showNoData(); });
    },

    createChart: function(data) {
        var canvas = document.getElementById('categoryBarChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var labels = (data.labels && data.labels.length) ? data.labels : ['No data'];
        var values = (data.sales  && data.sales.length)  ? data.sales  : [0];
        var colors = window.rdylbuColors ? window.rdylbuColors(labels.length) : ['#d73027','#fdae61','#abd9e9','#4575b4'];

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: this.currentType === 'sales' ? 'Sales (\u20B1)' : 'Quantity',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: { topLeft: 6, topRight: 6 },
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    y: {
                        easing: 'easeOutBounce',
                        duration: function(ctx) { return 400 + ctx.dataIndex * 80; },
                        from: function(ctx) { return ctx.chart.scales.y.getPixelForValue(0); }
                    },
                    x: { duration: 0 }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#313695',
                        titleColor: '#fee090',
                        bodyColor: '#fff',
                        borderColor: '#74add1',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        displayColors: false,
                        callbacks: {
                            label: function(ctx) { return ' \u20B1' + ctx.raw.toFixed(2); }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(69,117,180,0.08)', drawBorder: false },
                        border: { dash: [4,4], display: false },
                        ticks: { callback: function(v) { return '\u20B1' + v; }, color: '#74add1', font: { size: 11 } }
                    },
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: '#74add1', font: { size: 11 } }
                    }
                }
            }
        });
    },

    changePeriod: function(days) { this.currentPeriod = days; this.fetchData(); },
    toggleType:   function()     { this.currentType = this.currentType === 'sales' ? 'quantity' : 'sales'; this.fetchData(); },
    showNoData:   function()     {
        var c = document.getElementById('categoryBarChart');
        var n = document.getElementById('categoryNoData');
        if (c) c.style.display = 'none';
        if (n) n.style.display = 'block';
    },
    destroy: function() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
};
