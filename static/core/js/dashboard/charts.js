// ========== DASHBOARD CHARTS MANAGER ==========
// Uses d3.interpolateRdYlBu: colorStart=0.1, colorEnd=1.0, useEndAsStart=false

// Generate N colors from RdYlBu scale
window.rdylbuColors = function(n) {
    if (typeof d3 === 'undefined') {
        // Fallback palette if d3 not loaded
        return ['#d73027','#f46d43','#fdae61','#fee090','#ffffbf','#e0f3f8','#abd9e9','#74add1','#4575b4','#313695'].slice(0, n);
    }
    var colors = [];
    for (var i = 0; i < n; i++) {
        var t = n === 1 ? 0.1 : 0.1 + (i / (n - 1)) * 0.9;
        colors.push(d3.interpolateRdYlBu(t));
    }
    return colors;
};

// Convert rgb() to rgba() with alpha
window.rdylbuAlpha = function(n, alpha) {
    return window.rdylbuColors(n).map(function(c) {
        return c.replace('rgb(', 'rgba(').replace(')', ',' + (alpha || 0.8) + ')');
    });
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
