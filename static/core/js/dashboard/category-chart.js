// ========== SALES BY CATEGORY — Doughnut ==========
const CategoryChartManager = {
    chart: null,
    currentPeriod: 30,
    currentType: 'sales',
    _cachedData: null,

    init: function() {
        if (!document.getElementById('categoryBarChart')) return;
        this._cachedData = window.categoryData || { labels: [], sales: [], quantities: [] };
        this.createChart(this._cachedData);
    },

    fetchData: function() {
        var self = this;
        fetch('/api/dashboard/sales_by_category/?days=' + this.currentPeriod, {credentials: 'same-origin'})
            .then(function(r) { return r.json(); })
            .then(function(data) {
                self._cachedData = data;
                self.createChart(data);
            })
            .catch(function() {
                self._cachedData = window.categoryData || { labels: [], sales: [], quantities: [] };
                self.createChart(self._cachedData);
            });
    },

    createChart: function(data) {
        var canvas = document.getElementById('categoryBarChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var labels = (data.labels && data.labels.length) ? data.labels : null;
        var isSales = this.currentType === 'sales';
        var values = isSales
            ? (data.sales && data.sales.length ? data.sales : null)
            : (data.quantities && data.quantities.length ? data.quantities : null);

        if (!labels || !values) { this.showNoData(); return; }

        // Restore canvas visibility
        canvas.style.display = '';
        var noData = document.getElementById('categoryNoData');
        if (noData) noData.classList.add('hidden');

        var colors = window.rdylbuColors(labels.length);
        var colorsAlpha = window.rdylbuAlpha(labels.length, 0.88);

        var total = values.reduce(function(a, b) { return a + b; }, 0);

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colorsAlpha,
                    borderColor: colors,
                    borderWidth: 2,
                    hoverOffset: 10,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '62%',
                animation: { animateRotate: true, animateScale: false, duration: 800, easing: 'easeInOutQuart' },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#7C4A2D',
                            padding: 14,
                            font: { size: 11, weight: '600' },
                            usePointStyle: true,
                            pointStyleWidth: 10,
                        }
                    },
                    tooltip: {
                        backgroundColor: '#3d2010',
                        titleColor: '#f7e4d8',
                        bodyColor: '#fff',
                        borderColor: '#C98A6B',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        callbacks: {
                            label: function(ctx) {
                                var pct = total ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                var val = isSales
                                    ? '₱' + ctx.raw.toLocaleString('en-PH', {minimumFractionDigits:2, maximumFractionDigits:2})
                                    : ctx.raw + ' units';
                                return '  ' + val + '  (' + pct + '%)';
                            }
                        }
                    }
                }
            }
        });
    },

    changePeriod: function(days) {
        this.currentPeriod = parseInt(days);
        this.fetchData();
    },

    toggleType: function() {
        this.currentType = this.currentType === 'sales' ? 'quantity' : 'sales';
        this.createChart(this._cachedData || window.categoryData || { labels: [], sales: [], quantities: [] });
    },

    setType: function(type) {
        this.currentType = type;
        this.createChart(this._cachedData || window.categoryData || { labels: [], sales: [], quantities: [] });
    },

    showNoData: function() {
        var c = document.getElementById('categoryBarChart');
        var n = document.getElementById('categoryNoData');
        if (c) c.style.display = 'none';
        if (n) n.classList.remove('hidden');
    },

    destroy: function() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
};
