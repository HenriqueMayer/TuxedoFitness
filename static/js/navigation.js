/* Shared Tuxedo contract: query changes preserve viewport and keyboard focus. */
(function () {
    'use strict';
    var view = null;
    var revision = document.querySelector('meta[name="frontend-version"]').content;
    document.addEventListener('htmx:configRequest', function (event) {
        event.detail.headers['X-Frontend-Version'] = revision;
    });
    document.addEventListener('htmx:historyRestore', function () {
        if (document.body.dataset.frontendVersion !== revision) location.reload();
    });
    function focusSelector(element) {
        if (!element || element === document.body) return null;
        var parts = [];
        while (element && element !== document.body) {
            if (element.id) { parts.unshift('#' + CSS.escape(element.id)); break; }
            var tag = element.tagName.toLowerCase();
            var siblings = Array.from(element.parentElement.children).filter(function (item) { return item.tagName === element.tagName; });
            parts.unshift(tag + ':nth-of-type(' + (siblings.indexOf(element) + 1) + ')');
            element = element.parentElement;
        }
        return parts.join(' > ');
    }
    document.addEventListener('htmx:beforeSwap', function (event) {
        var target = event.detail.target;
        if (!target) return;
        var response = event.detail.xhr && event.detail.xhr.responseURL;
        var same = !response || new URL(response, location.href).pathname === location.pathname;
        var active = document.activeElement;
        view = {same: same, x: scrollX, y: scrollY, focus: focusSelector(active)};
        if (same) event.detail.swapOverride = 'innerHTML show:none';
    });
    document.addEventListener('htmx:afterSettle', function () {
        if (!view) return;
        var saved = view; view = null;
        if (saved.same) {
            scrollTo(saved.x, saved.y);
            var control = saved.focus && document.querySelector(saved.focus);
            if (control) control.focus({preventScroll: true});
        } else {
            var heading = document.querySelector('main h1');
            if (heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); }
            scrollTo(0, 0);
        }
    });
    ['htmx:responseError', 'htmx:sendError', 'htmx:timeout'].forEach(function (name) {
        document.addEventListener(name, function () {
            var status = document.getElementById('navigation-status');
            if (status) status.textContent = document.documentElement.lang === 'pt-br' ? 'Não foi possível atualizar a página.' : 'Unable to update the page.';
        });
    });
})();
