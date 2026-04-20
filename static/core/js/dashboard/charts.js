// ========== DASHBOARD CHARTS MANAGER ==========
// Palette: RdYlBu diverging (colorStart 0.1 → colorEnd 1.0)

window.RDYLBU = [
    '#d73027', // red
    '#f46d43', // orange-red
    '#fdae61', // orange
    '#fee090', // yellow-orange
    '#ffffbf', // pale yellow
    '#e0f3f8', // pale blue
    '#abd9e9', // light blue
    '#74add1', // medium blue
    '#4575b4', // blue
    '#313695'  // dark blue
];

// Pick N evenly-spaced colors from the palette
window.rdylbuColors = function(n) {
    var p = window.RDYLBU;
    if (n <= 1) return [p[0]];
    var result = [];
    for (var i = 0; i < n; i++) {
        var idx = Math.round(i * (p.length - 1) / (n - 1));
        result.push(p[idx]);
    }
    return result;
};

const DashboardCharts = {
    init: function() {
        Chart.defaults.font.family = "'Poppins', sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#a86b4e';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 16;
        Chart.defaults.animation.duration = 800;
        Chart.defaults.animation.easing = 'easeInOutQuart';

        setTimeout(function() {
            if (typeof LineChartManager !== 'undefined')        try { LineChartManager.init(); }        catch(e) { console.error(e); }
            if (typeof CategoryChartManager !== 'undefined')    try { CategoryChartManager.init(); }    catch(e) { console.error(e); }
            if (typeof ProductsChartManager !== 'undefined')    try { ProductsChartManager.init(); }    catch(e) { console.error(e); }
            if (typeof BestSellersChartManager !== 'undefined') try { BestSellersChartManager.init(); } catch(e) { console.error(e); }
        }, 120);
    }
};

document.addEventListener('DOMContentLoaded', function() { DashboardCharts.init(); });
