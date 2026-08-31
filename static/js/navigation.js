/* Stable HTMX navigation and focused dashboard-island continuity. */
(function () {
    'use strict';

    var preservedResultsView = null;

    function finishRequest() {
        var body = document.body;
        if (body) body.removeAttribute('aria-busy');
        document.querySelectorAll('[data-request-status]').forEach(function (status) {
            status.setAttribute('aria-hidden', 'true');
        });
    }

    function announceFailure() {
        finishRequest();
        var status = document.getElementById('navigation-status');
        if (status) status.textContent = 'Não foi possível atualizar a página. Tente novamente.';
    }

    document.addEventListener('htmx:beforeRequest', function (event) {
        var target = event.detail.target;
        if (target === document.body) {
            document.body.setAttribute('aria-busy', 'true');
            return;
        }
        if (!target || target.id !== 'overview-results') return;

        var active = document.activeElement;
        preservedResultsView = {
            top: window.scrollY,
            focusId: active && active.id ? active.id : null,
        };
        target.setAttribute('aria-busy', 'true');
        document.querySelectorAll('[data-request-status]').forEach(function (status) {
            status.setAttribute('aria-hidden', 'false');
        });
    });

    document.addEventListener('htmx:afterSwap', function (event) {
        var target = event.detail.target;
        if (target === document.body) {
            finishRequest();
            window.requestAnimationFrame(function () {
                var heading = document.querySelector('main h1');
                if (!heading) return;
                heading.setAttribute('tabindex', '-1');
                heading.focus({preventScroll: true});
                heading.addEventListener('blur', function () {
                    heading.removeAttribute('tabindex');
                }, {once: true});
            });
            return;
        }
        if (!target || target.id !== 'overview-results' || !preservedResultsView) return;

        var view = preservedResultsView;
        preservedResultsView = null;
        target.removeAttribute('aria-busy');
        finishRequest();
        window.requestAnimationFrame(function () {
            window.scrollTo(0, view.top);
            if (!view.focusId) return;
            var field = document.getElementById(view.focusId);
            if (field) field.focus({preventScroll: true});
        });
    });

    ['htmx:responseError', 'htmx:sendError', 'htmx:timeout'].forEach(function (name) {
        document.addEventListener(name, announceFailure);
    });
    document.addEventListener('htmx:beforeHistorySave', finishRequest);
})();
