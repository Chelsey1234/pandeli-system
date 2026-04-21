// ========== BEST SELLERS — Polar Area with RdYlBu ==========
const BestSellersChartManager = {
    chart: null,

    init: function() {
        var canvas = document.getElementById('bestSellersChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var raw = (window.bestSellers || []).filter(function(i) { return i.quantity > 0; });

        if (!raw.length) {
            var noData = document.getElementById('bestSellersNoData');
            if (noData) noData.classList.remove('hidden');
            canvas.style.display = 'none';
            return;
        }

        var labels = raw.map(function(i) { return i.name; });
        var values = raw.map(function(i) { return i.quantity; });
        var colors = window.rdylbuColors(labels.length);
        var colorsAlpha = window.rdylbuAlpha(labels.length, 0.8);

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'polarArea',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colorsAlpha,
                    borderColor: colors,
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { animateRotate: true, animateScale: true, duration: 900, easing: 'easeInOutQuart' },
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#7C4A2D', padding: 12, font: { size: 11, weight: '500' }, usePointStyle: true } },
                    tooltip: {
                        backgroundColor: '#3d2010', titleColor: '#f7e4d8', bodyColor: '#fff',
                        borderColor: '#C98A6B', borderWidth: 1, padding: 12, cornerRadius: 10,
                        callbacks: {
                            label: function(ctx) {
                                var total = ctx.dataset.data.reduce(function(a,b){return a+b;},0);
                                var pct = total ? ((ctx.raw/total)*100).toFixed(1) : 0;
                                return ' ' + ctx.raw + ' orders (' + pct + '%)';
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        ticks: { color: '#C98A6B', backdropColor: 'transparent', font: { size: 10 } },
                        grid: { color: 'rgba(201,138,107,0.2)' },
                        pointLabels: { display: false }
                    }
                }
            }
        });
    },

    destroy: function() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
};
