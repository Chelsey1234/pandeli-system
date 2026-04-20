// ========== TOP PRODUCTS — RdYlBu horizontal bars ==========
const ProductsChartManager = {
    chart: null,
    currentPeriod: 30,
    currentType: 'sales',

    init: function() {
        if (!document.getElementById('topProductsChart')) return;
        this.fetchData();
    },

    fetchData: function() {
        var self = this;
        fetch('/api/dashboard/top_products/?days=' + this.currentPeriod, {credentials: 'same-origin'})
            .then(function(r) { return r.json(); })
            .then(function(data) { self.createChart(data); })
            .catch(function() { self.showNoData(); });
    },

    createChart: function(data) {
        var canvas = document.getElementById('topProductsChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var labels = (data.labels && data.labels.length) ? data.labels : ['No data'];
        var values = (data.sales  && data.sales.length)  ? data.sales  : [0];

        // Highest value = red, lowest = blue (diverging intensity)
        var maxVal = Math.max.apply(null, values) || 1;
        var rdylbu = window.RDYLBU || ['#d73027','#f46d43','#fdae61','#fee090','#ffffbf','#e0f3f8','#abd9e9','#74add1','#4575b4','#313695'];
        var colors = values.map(function(v) {
            var t = v / maxVal; // 1 = red, 0 = blue
            var idx = Math.round((1 - t) * (rdylbu.length - 1));
            return rdylbu[idx];
        });

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: this.currentType === 'sales' ? 'Sales (\u20B1)' : 'Quantity',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: { topRight: 6, bottomRight: 6 },
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                animation: {
                    x: {
                        easing: 'easeOutQuart',
                        duration: function(ctx) { return 500 + ctx.dataIndex * 100; },
                        from: function(ctx) { return ctx.chart.scales.x.getPixelForValue(0); }
                    },
                    y: { duration: 0 }
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
                    x: {
                        beginAtZero: true,
                        grid: { color: 'rgba(69,117,180,0.08)', drawBorder: false },
                        border: { dash: [4,4], display: false },
                        ticks: { callback: function(v) { return '\u20B1' + v; }, color: '#74add1', font: { size: 11 } }
                    },
                    y: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: '#313695', font: { weight: '600', size: 11 } }
                    }
                }
            }
        });
    },

    changePeriod: function(days) { this.currentPeriod = days; this.fetchData(); },
    toggleType:   function()     { this.currentType = this.currentType === 'sales' ? 'quantity' : 'sales'; this.fetchData(); },
    showNoData:   function()     {
        var c = document.getElementById('topProductsChart');
        var n = document.getElementById('productsNoData');
        if (c) c.style.display = 'none';
        if (n) n.style.display = 'block';
    },
    destroy: function() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
};
