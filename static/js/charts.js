/* Delegated chart inspection survives HTMX navigation. Data is server-calculated. */
(function () {
    'use strict';
    function inspect(event) {
        var point = event.target.closest('[data-chart-value]');
        if (!point) return;
        var chart = point.closest('[data-chart]');
        chart.querySelectorAll('[data-selected]').forEach(function (item) { item.removeAttribute('data-selected'); });
        point.setAttribute('data-selected', '');
        chart.querySelector('[data-chart-readout]').textContent = point.dataset.chartValue;
    }
    document.addEventListener('keydown', function (event) {
        var point = event.target.closest('[data-chart-value]');
        if (!point) return;
        var points = Array.from(point.closest('[data-chart]').querySelectorAll('[data-chart-value]'));
        var index = points.indexOf(point);
        var next;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = Math.min(index + 1, points.length - 1);
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = Math.max(index - 1, 0);
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = points.length - 1;
        if (next !== undefined) { event.preventDefault(); points[next].focus({preventScroll: true}); }
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(event); }
    });
    ['pointerover', 'focusin', 'click'].forEach(function (name) { document.addEventListener(name, inspect); });
})();
