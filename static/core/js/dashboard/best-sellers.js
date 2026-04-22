// ========== BEST SELLERS — Doughnut with centre label, RdYlBu, staggered arcs ==========
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

        var labels  = raw.map(function(i) { return i.name; });
        var values  = raw.map(function(i) { return i.quantity; });
        var total   = values.reduce(function(a, b) { return a + b; }, 0);
        var colors  = window.rdylbuColors(labels.length);
        var colorsAlpha = window.rdylbuAlpha(labels.length, 0.88);

        // ── Custom centre-label plugin ──────────────────────────────────
        var centreLabelPlugin = {
            id: 'centreLabel',
            afterDraw: function(chart) {
                var ctx  = chart.ctx;
                var area = chart.chartArea;
                var cx   = (area.left + area.right)  / 2;
                var cy   = (area.top  + area.bottom) / 2;

                ctx.save();
                ctx.textAlign    = 'center';
                ctx.textBaseline = 'middle';

                // Total number — large & bold
                ctx.font      = "bold 26px 'Poppins', sans-serif";
                ctx.fillStyle = '#3d2010';
                ctx.fillText(total.toLocaleString('en-PH'), cx, cy - 10);

                // "total sold" label — small & muted
                ctx.font      = "500 11px 'Poppins', sans-serif";
                ctx.fillStyle = '#C98A6B';
                ctx.fillText('total sold', cx, cy + 14);

                ctx.restore();
            }
        };

        // ── Staggered arc delay ─────────────────────────────────────────
        var arcDuration = 600;
        var arcDelay    = 120; // ms between each arc start

        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data:            values,
                    backgroundColor: colorsAlpha,
                    borderColor:     colors,
                    borderWidth:     2.5,
                    hoverOffset:     12,
                    hoverBorderWidth: 3,
                }]
            },
            options: {
                responsive:          true,
                maintainAspectRatio: false,
                cutout:              '65%',

                // Staggered animation via per-arc delay
                animation: {
                    duration: arcDuration,
                    easing:   'easeInOutBack',
                    delay: function(ctx) {
                        // Only stagger on initial draw (not hover updates)
                        if (ctx.type === 'data' && ctx.mode === 'default') {
                            return ctx.dataIndex * arcDelay;
                        }
                        return 0;
                    }
                },

                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color:          '#7C4A2D',
                            padding:        14,
                            font:           { size: 11, weight: '500' },
                            usePointStyle:  true,
                            pointStyleWidth: 10,
                            // Truncate long names in legend
                            generateLabels: function(chart) {
                                var data = chart.data;
                                return data.labels.map(function(label, i) {
                                    var ds  = data.datasets[0];
                                    var val = ds.data[i];
                                    var pct = total ? ((val / total) * 100).toFixed(1) : 0;
                                    return {
                                        text:            (label.length > 18 ? label.slice(0, 17) + '…' : label) + '  ' + pct + '%',
                                        fillStyle:       ds.backgroundColor[i],
                                        strokeStyle:     ds.borderColor[i],
                                        lineWidth:       ds.borderWidth,
                                        pointStyle:      'circle',
                                        hidden:          false,
                                        index:           i,
                                        datasetIndex:    0,
                                    };
                                });
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#3d2010',
                        titleColor:      '#f7e4d8',
                        bodyColor:       '#fff',
                        borderColor:     '#C98A6B',
                        borderWidth:     1,
                        padding:         12,
                        cornerRadius:    10,
                        displayColors:   true,
                        callbacks: {
                            label: function(ctx) {
                                var pct = total ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                return '  ' + ctx.raw.toLocaleString('en-PH') + ' units sold  (' + pct + '%)';
                            }
                        }
                    }
                }
            },
            plugins: [centreLabelPlugin]
        });
    },

    destroy: function() {
        if (this.chart) { this.chart.destroy(); this.chart = null; }
    }
};
