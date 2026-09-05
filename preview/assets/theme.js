(function () {
    document.addEventListener('click', function (event) {
        if (!event.target.closest('[data-theme-toggle]')) return;
        var dark = document.documentElement.classList.toggle('dark');
        document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
        document.dispatchEvent(new CustomEvent('tuxedo:themechange'));
        try {
            localStorage.setItem('theme', dark ? 'dark' : 'light');
        } catch (error) {
            return;
        }
    });
})();
