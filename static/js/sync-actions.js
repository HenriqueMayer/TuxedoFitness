(function () {
  'use strict';

  document.addEventListener('submit', function (event) {
    var form = event.target.closest('[data-busy-form]');
    if (!form) return;
    var button = form.querySelector('button[type="submit"]');
    var status = document.getElementById('sync-status');
    if (button) button.disabled = true;
    if (status) status.textContent = form.dataset.loadingMessage || 'Processando…';
  });
})();
