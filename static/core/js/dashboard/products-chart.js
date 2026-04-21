// ========== TOP PRODUCTS — Horizontal Bar with RdYlBu gradient ==========
const ProductsChartManager = {
    chart: null,
    currentPeriod: 30,
    currentType: 'sales',

    init: function() {
        if (!document.getElementById('topProductsChart')) return;
        this.renderFromServerData();
    },

    renderFromServerData: function() {
        var data = window.topProductsData || { labels: [], sales: [], quantities: [] };
        this.createChart(data);
    },

    fetchData: function() {
        var self = this;
        fetch('/api/dashboard/top_products/?days=' + this.currentPeriod, {credentials: 'same-origin'})
            .then(function(r) { return r.json(); })
            .then(function(data) { self.createChart(data); })
            .catch(function() { self.renderFromServerData(); });
    },

    createChart: function(data) {
        var canvas = document.getElementById('topProductsChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var labels = (data.labels && data.labels.length) ? data.labels : null;
        var values = this.currentType === 'sales'
            ? (data.sales && data.sales.length ? data.sales : null)
            : (data.quantities && data.quantities.length ? data.quantities : null);

        if (!labels || !values) { this.showNoData(); return; }

        // RdYlBu: highest value = red (0.1), lowest = blue (1.0)
        var maxVal = Math.max.apply(null, values) || 1;
        var colors = values.map(function(v) {
            var t = 0.1 + (1 - v / maxVal) * 0.9; // high value → low t → red
            return typeof d3 !== 'undefined' ? d3.interpolateRdYlBu(t) : '#C98A6B';
        });

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: this.currentType === 'sales' ? 'Sales (\u20B1)' : 'Orders',
                    data: values,
                    backgroundColor: colors.map(function(c) { return c.replace('rgb(','rgba(').replace(')',',0.85)'); }),
                    borderColor: colors,
                    borderWidth: 1,
                    borderRadius: { topRight: 8, bottomRight: 8 },
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                animation: {
                    x: { easing: 'easeOutQuart', duration: function(ctx) { return 400 + ctx.dataIndex * 80; }, from: function(ctx) { return ctx.chart.scales.x.getPixelForValue(0); } },
                    y: { duration: 0 }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#3d2010', titleColor: '#f7e4d8', bodyColor: '#fff',
                        borderColor: '#C98A6B', borderWidth: 1, padding: 12, cornerRadius: 10,
                        displayColors: false,
                        callbacks: { label: function(ctx) { return this.currentType === 'sales' ? ' \u20B1' + ctx.raw.toFixed(2) : ' ' + ctx.raw + ' orders'; }.bind(this) }
                    }
                },
                scales: {
                    x: { beginAtZero: true, grid: { color: 'rgba(215,48,39,0.08)' }, ticks: { callback: function(v) { return '\u20B1' + v; }, color: '#C98A6B', font: { size: 11 } } },
                    y: { grid: { display: false }, ticks: { color: '#7C4A2D', font: { size: 11, weight: '600' } } }
                }
            }
        });
    },

    changePeriod: function(days) { this.currentPeriod = days; this.fetchData(); },
    toggleType: function() { this.currentType = this.currentType === 'sales' ? 'quantity' : 'sales'; this.renderFromServerData(); },
    showNoData: function() {
        var c = document.getElementById('topProductsChart');
        var n = document.getElementById('productsNoData');
        if (c) c.style.display = 'none';
        if (n) n.style.display = 'block';
    },
    destroy: function() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
};
