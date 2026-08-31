(function () {
    'use strict';

    function elements() {
        return {
            menu: document.getElementById('mobile-menu'),
            openButton: document.getElementById('menu-btn'),
            closeButton: document.getElementById('close-menu-btn'),
        };
    }

    function backgroundInert(inert, menu) {
        Array.prototype.forEach.call(document.body.children, function (element) {
            if (element === menu || element.tagName === 'SCRIPT') return;
            if (inert && !element.hasAttribute('inert')) {
                element.dataset.menuInert = '';
                element.setAttribute('inert', '');
            } else if (!inert && element.hasAttribute('data-menu-inert')) {
                element.removeAttribute('inert');
                delete element.dataset.menuInert;
            }
        });
    }

    function focusable(menu) {
        return menu.querySelectorAll(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
    }

    function setOpen(open, restoreFocus) {
        var current = elements();
        var menu = current.menu;
        var openButton = current.openButton;
        var closeButton = current.closeButton;
        if (!menu || !openButton || !closeButton) return;
        menu.classList.toggle('translate-x-full', !open);
        menu.toggleAttribute('inert', !open);
        menu.setAttribute('aria-hidden', String(!open));
        openButton.setAttribute('aria-expanded', String(open));
        closeButton.setAttribute('aria-expanded', String(open));
        document.body.classList.toggle('overflow-hidden', open);
        backgroundInert(open, menu);
        if (open) closeButton.focus();
        if (!open && restoreFocus) openButton.focus();
    }

    document.addEventListener('click', function (event) {
        if (event.target.closest('#menu-btn')) setOpen(true, false);
        if (event.target.closest('#close-menu-btn')) setOpen(false, true);
        if (event.target.closest('#mobile-menu .mobile-link')) setOpen(false, false);
    });

    document.addEventListener('keydown', function (event) {
        var menu = document.getElementById('mobile-menu');
        if (!menu) return;
        if (menu.hasAttribute('inert')) return;
        if (event.key === 'Escape') {
            event.preventDefault();
            setOpen(false, true);
            return;
        }
        if (event.key !== 'Tab') return;
        var items = focusable(menu);
        if (!items.length) return;
        var first = items[0];
        var last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    });
})();
