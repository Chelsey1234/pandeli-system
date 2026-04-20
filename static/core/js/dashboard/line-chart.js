// ========== SALES LINE CHART — RdYlBu, sequential point animation ==========
const LineChartManager = {
    chart: null,

    init: function() {
        var canvas = document.getElementById('salesLineChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var labels = window.salesLabels || [];
        var data   = window.salesData   || [];

        var fallbackLabels = labels.length ? labels : (function() {
            return Array.from({ length: 7 }, function(_, i) {
                var d = new Date(); d.setDate(d.getDate() - (6 - i));
                return d.toISOString().slice(0, 10);
            });
        })();
        var displayData = data.length ? data : Array(7).fill(0);

        var ctx = canvas.getContext('2d');

        // RdYlBu gradient: red (high) → yellow → blue (low) top to bottom
        var gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0,   'rgba(215,48,39,0.35)');   // red top
        gradient.addColorStop(0.5, 'rgba(254,224,144,0.2)');  // yellow mid
        gradient.addColorStop(1,   'rgba(69,117,180,0.05)');  // blue bottom

        var totalDuration = 1200;
        var delayPerPt = totalDuration / displayData.length;
        var previousY = {};

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: fallbackLabels,
                datasets: [{
                    label: 'Sales',
                    data: displayData,
                    borderColor: '#d73027',
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#4575b4',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#d73027',
                    tension: 0.45,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    x: {
                        type: 'number', easing: 'linear', duration: delayPerPt, from: NaN,
                        delay: function(ctx) {
                            if (ctx.type !== 'data' || ctx.xStarted) return 0;
                            ctx.xStarted = true;
                            return ctx.index * delayPerPt;
                        }
                    },
                    y: {
                        type: 'number', easing: 'easeInOutQuart', duration: delayPerPt,
                        from: function(ctx) {
                            if (ctx.index === 0) return ctx.chart.scales.y.getPixelForValue(100);
                            return previousY[ctx.index - 1];
                        },
                        delay: function(ctx) {
                            if (ctx.type !== 'data' || ctx.yStarted) return 0;
                            ctx.yStarted = true;
                            return ctx.index * delayPerPt;
                        }
                    }
                },
                interaction: { mode: 'index', intersect: false },
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
                        ticks: { color: '#74add1', maxRotation: 30, font: { size: 11 } }
                    }
                }
            },
            plugins: [{
                id: 'captureY',
                afterDatasetsDraw: function(chart) {
                    chart.data.datasets[0].data.forEach(function(_, i) {
                        var meta = chart.getDatasetMeta(0);
                        if (meta.data[i]) previousY[i] = meta.data[i].y;
                    });
                }
            }]
        });
    },

    refresh: function(days) {
        days = days || 7;
        var self = this;
        fetch('/api/dashboard/sales_chart/?days=' + days, {credentials: 'same-origin'})
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!self.chart) return;
                self.chart.data.labels = data.map(function(i) { return i.date; });
                self.chart.data.datasets[0].data = data.map(function(i) { return i.total; });
                self.chart.update('active');
            })
            .catch(function(e) { console.error(e); });
    },

    destroy: function() {
        if (this.chart) { this.chart.destroy(); this.chart = null; }
    }
};
