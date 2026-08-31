(function () {
    var stored;
    try {
        stored = localStorage.getItem('theme');
    } catch (error) {
        stored = null;
    }
    var dark = stored
        ? stored === 'dark'
        : window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.classList.toggle('dark', dark);
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
})();
