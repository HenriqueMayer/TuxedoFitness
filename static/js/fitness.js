(function () {
    'use strict';
    if (window.tuxedoFitnessReady) return;
    window.tuxedoFitnessReady = true;
    var syncing = false;
    var dirty = false;
    function disclosure(clear) {
        var mode = document.getElementById('id_period_mode');
        if (!mode) return;
        document.querySelectorAll('[data-period-branch]').forEach(function (branch) {
            var active = branch.dataset.periodBranch === mode.value;
            branch.hidden = !active && !branch.querySelector('.errorlist');
            if (clear && !active) branch.querySelectorAll('input').forEach(function (input) { input.value = ''; });
        });
    }
    async function synchronize(manual) {
        var form = document.getElementById('automatic-sync');
        if (!form || syncing) return;
        syncing = true;
        try {
            var body = new FormData(form);
            if (manual) body.append('manual', '1');
            var response = await fetch(form.action, {method:'POST', body:body, credentials:'same-origin', headers:{'Accept':'application/json'}});
            var result = await response.json();
            var status = document.getElementById('sync-status');
            if (status && result.status === 'updated') status.textContent = status.dataset.updated;
            if (status && !response.ok) status.textContent = status.dataset.failed;
            if (result.status === 'updated' && !dirty && document.querySelector('[data-read-surface]') && window.htmx) {
                await window.htmx.ajax('GET', location.href, {target:'body', swap:'innerHTML show:none'});
            }
        } catch (_) {
            var status = document.getElementById('sync-status');
            if (status) status.textContent = status.dataset.failed;
        } finally { syncing = false; }
    }
    function ready() { document.querySelectorAll("[data-js-only]").forEach(function(element){element.classList.remove("hidden");}); dirty = false; disclosure(false); synchronize(false); }
    document.addEventListener('change', function (event) {
        if (event.target.matches('[data-language]')) event.target.form.requestSubmit();
        if (event.target.id === 'id_period_mode') disclosure(true);
    });
    document.addEventListener('input', function () { dirty = true; });
    document.addEventListener('submit', function (event) {
        if (event.target.id === 'automatic-sync') { event.preventDefault(); synchronize(true); }
    });
    document.addEventListener('click', async function (event) {
        var button = event.target.closest('[data-copy]');
        if (!button) return;
        var element = document.getElementById(button.dataset.copy);
        try { await navigator.clipboard.writeText(element.value || element.textContent); button.textContent = button.dataset.copied; }
        catch (_) { if (element.select) element.select(); }
    });
    document.addEventListener('htmx:afterSwap', function (event) { if (event.detail.target === document.body) ready(); });
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready); else ready();
})();
