/* Tema visual del sistema. Se carga en el <head> (AMCSS.html) para fijar el tema antes del primer pintado.
   El tema vive en <html data-am-theme>, se recuerda en localStorage y, si hay sesion, en las preferencias del usuario. */
var AmTheme = (function () {
    var THEMES = { corp: 'Corp', modern: 'Modern' };
    var DEFAULT = 'corp';
    var KEY = 'amachine_theme';
    var cfg = window.AM_THEME_CONFIG || {};

    function valid(name) { return Object.prototype.hasOwnProperty.call(THEMES, name) ? name : null; }

    function current() { return valid(document.documentElement.getAttribute('data-am-theme')) || DEFAULT; }

    function next() {
        var names = Object.keys(THEMES);
        return names[(names.indexOf(current()) + 1) % names.length];
    }

    // Botones del toolbar: <button class="am-theme-toggle"><i></i><span class="am-theme-label"></span></button>
    function refreshButtons() {
        document.querySelectorAll('.am-theme-toggle').forEach(function (btn) {
            var label = btn.querySelector('.am-theme-label');
            if (label) label.textContent = THEMES[current()];
            btn.title = 'Estilo ' + THEMES[current()] + ' — cambiar a ' + THEMES[next()];
        });
    }

    function apply(name) {
        document.documentElement.setAttribute('data-am-theme', valid(name) || DEFAULT);
        refreshButtons();
    }

    function save(name) {
        localStorage.setItem(KEY, name);
        if (!cfg.saveUrl || typeof axios === 'undefined') return;
        var fdata = new FormData();
        fdata.append('module', 'OptsIO');
        fdata.append('package', 'mng_user_profile');
        fdata.append('attr', 'MUserProfile');
        fdata.append('mname', 'set_preference');
        fdata.append('key', 'theme');
        fdata.append('value', name);
        axios.post(cfg.saveUrl, fdata, { headers: { 'X-CSRFToken': cfg.csrf() } });
    }

    function set(name) {
        if (!valid(name)) return;
        apply(name);
        save(name);
    }

    // La preferencia guardada en el servidor manda (sigue al usuario entre equipos); si no hay, la de este navegador
    apply(valid(cfg.userTheme) || valid(localStorage.getItem(KEY)) || DEFAULT);

    document.addEventListener('click', function (evt) {
        if (evt.target.closest && evt.target.closest('.am-theme-toggle')) set(next());
    });
    document.addEventListener('DOMContentLoaded', refreshButtons);

    return { set: set, toggle: function () { set(next()); }, current: current, refreshButtons: refreshButtons, themes: THEMES };
})();
