(function () {
  'use strict';

  var toggle = document.querySelector('[data-password-toggle]');
  var password = document.getElementById('id_password');
  if (!toggle || !password) return;

  toggle.addEventListener('click', function () {
    var showPassword = password.type === 'password';
    password.type = showPassword ? 'text' : 'password';
    toggle.setAttribute('aria-pressed', String(showPassword));
    toggle.setAttribute('aria-label', showPassword ? 'Hide password' : 'Show password');
    toggle.setAttribute('title', showPassword ? 'Hide password' : 'Show password');
    toggle.querySelector('i').className = showPassword ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
    password.focus();
  });
})();
