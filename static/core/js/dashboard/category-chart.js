// ========== SALES BY CATEGORY — Radar with RdYlBu ==========
const CategoryChartManager = {
    chart: null,
    currentPeriod: 30,

    init: function() {
        if (!document.getElementById('categoryBarChart')) return;
        this.renderFromServerData();
    },

    renderFromServerData: function() {
        var data = window.categoryData || { labels: [], sales: [] };
        this.createChart(data);
    },

    fetchData: function() {
        var self = this;
        fetch('/api/dashboard/sales_by_category/?days=' + this.currentPeriod, {credentials: 'same-origin'})
            .then(function(r) { return r.json(); })
            .then(function(data) { self.createChart(data); })
            .catch(function() { self.renderFromServerData(); });
    },

    createChart: function(data) {
        var canvas = document.getElementById('categoryBarChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var labels = (data.labels && data.labels.length) ? data.labels : null;
        var values = (data.sales  && data.sales.length)  ? data.sales  : null;

        if (!labels || !values) { this.showNoData(); return; }

        var colors = window.rdylbuColors(labels.length);
        var colorsAlpha = window.rdylbuAlpha(labels.length, 0.3);

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sales (\u20B1)',
                    data: values,
                    backgroundColor: 'rgba(215,48,39,0.15)',
                    borderColor: colors[0] || '#d73027',
                    borderWidth: 2,
                    pointBackgroundColor: colors,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 800, easing: 'easeInOutQuart' },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#3d2010', titleColor: '#f7e4d8', bodyColor: '#fff',
                        borderColor: '#C98A6B', borderWidth: 1, padding: 12, cornerRadius: 10,
                        callbacks: { label: function(ctx) { return ' \u20B1' + ctx.raw.toFixed(2); } }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        ticks: { color: '#C98A6B', backdropColor: 'transparent', font: { size: 10 }, callback: function(v) { return '\u20B1' + v; } },
                        grid: { color: 'rgba(215,48,39,0.15)' },
                        angleLines: { color: 'rgba(215,48,39,0.2)' },
                        pointLabels: { color: '#7C4A2D', font: { size: 11, weight: '600' } }
                    }
                }
            }
        });
    },

    changePeriod: function(days) { this.currentPeriod = days; this.fetchData(); },
    showNoData: function() {
        var c = document.getElementById('categoryBarChart');
        var n = document.getElementById('categoryNoData');
        if (c) c.style.display = 'none';
        if (n) n.style.display = 'block';
    },
    destroy: function() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
};
