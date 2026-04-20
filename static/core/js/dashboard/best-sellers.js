// ========== BEST SELLERS — RdYlBu doughnut ==========
const BestSellersChartManager = {
    chart: null,

    init: function() {
        var canvas = document.getElementById('bestSellersChart');
        if (!canvas) return;
        if (this.chart) { this.chart.destroy(); this.chart = null; }

        var raw    = window.bestSellers || [];
        var labels = raw.length ? raw.map(function(i) { return i.name; }) : ['No data'];
        var values = raw.length ? raw.map(function(i) { return i.quantity; }) : [0];
        var colors = window.rdylbuColors ? window.rdylbuColors(labels.length) : ['#d73027','#fdae61','#ffffbf','#abd9e9','#4575b4'];

        var totalDuration = 1000;
        var delayPerArc   = totalDuration / labels.length;

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: '#F5EDE8',
                    borderWidth: 3,
                    hoverOffset: 12,
                    hoverBorderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                animation: {
                    animateRotate: true,
                    animateScale: false,
                    duration: function(ctx) { return delayPerArc * (ctx.dataIndex + 1); },
                    easing: 'easeInOutBack'
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#4575b4',
                            padding: 14,
                            font: { size: 11, weight: '500' },
                            boxWidth: 10,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#313695',
                        titleColor: '#fee090',
                        bodyColor: '#fff',
                        borderColor: '#74add1',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        callbacks: {
                            label: function(ctx) {
                                var total = ctx.dataset.data.reduce(function(a,b){return a+b;},0);
                                var pct   = total ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                return ' ' + ctx.raw + ' sold (' + pct + '%)';
                            }
                        }
                    }
                }
            },
            plugins: [{
                id: 'centreLabel',
                afterDraw: function(chart) {
                    var total = chart.data.datasets[0].data.reduce(function(a,b){return a+b;},0);
                    if (!total) return;
                    var ctx2 = chart.ctx;
                    var cx = chart.chartArea.left + (chart.chartArea.right  - chart.chartArea.left) / 2;
                    var cy = chart.chartArea.top  + (chart.chartArea.bottom - chart.chartArea.top)  / 2;
                    ctx2.save();
                    ctx2.textAlign = 'center'; ctx2.textBaseline = 'middle';
                    ctx2.fillStyle = '#313695';
                    ctx2.font = "bold 20px 'Poppins', sans-serif";
                    ctx2.fillText(total, cx, cy - 8);
                    ctx2.fillStyle = '#74add1';
                    ctx2.font = "11px 'Poppins', sans-serif";
                    ctx2.fillText('total sold', cx, cy + 12);
                    ctx2.restore();
                }
            }]
        });
    },

    destroy: function() { if (this.chart) { this.chart.destroy(); this.chart = null; } }
};
