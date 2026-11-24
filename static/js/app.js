// Progressive AJAX navigation and forms for the server-rendered application.
(function () {
  'use strict';

  var activeRequest = null;
  var pageScripts = [];
  var contentSelector = '.app-content';
  var sidebar = document.querySelector('.app-sidebar');
  var backdrop = document.querySelector('.app-backdrop');

  function toggleSidebar(open) {
    if (!sidebar || !backdrop) return;
    sidebar.classList.toggle('open', open);
    backdrop.classList.toggle('open', open);
  }

  document.addEventListener('click', function (event) {
    var open = event.target.closest('[data-sidebar-open]');
    var close = event.target.closest('[data-sidebar-close]');
    if (open) toggleSidebar(true);
    if (close) toggleSidebar(false);
  });

  function isInternalPageLink(link, event) {
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if (link.target && link.target !== '_self') return false;
    if (link.hasAttribute('download') || link.hasAttribute('data-no-ajax')) return false;
    var url;
    try { url = new URL(link.href, window.location.href); } catch (_) { return false; }
    return url.origin === window.location.origin && !url.searchParams.has('download') && !/^mailto:|^tel:/i.test(link.href);
  }

  function canSwap(doc) {
    return !!(doc && doc.querySelector('.app-main') && doc.querySelector(contentSelector));
  }

  function setBusy(busy) {
    var main = document.querySelector('.app-main');
    if (!main) return;
    main.setAttribute('aria-busy', busy ? 'true' : 'false');
    main.classList.toggle('is-navigating', busy);
  }

  function loadScripts(doc) {
    pageScripts.forEach(function (script) { script.remove(); });
    pageScripts = [];
    var scripts = Array.prototype.slice.call(doc.querySelectorAll('body script'));
    return scripts.reduce(function (chain, source) {
      var src = source.getAttribute('src') || '';
      if (src.indexOf('/static/js/app.js') !== -1 || src.indexOf('bootstrap') !== -1 || src.indexOf('jquery') !== -1) return chain;
      return chain.then(function () {
        return new Promise(function (resolve) {
          var script = document.createElement('script');
          if (source.type) script.type = source.type;
          if (source.src) {
            script.src = new URL(source.getAttribute('src'), window.location.href).href;
            script.async = false;
            script.onload = resolve;
            script.onerror = resolve;
          } else {
            script.textContent = source.textContent;
            resolve();
          }
          document.body.appendChild(script);
          pageScripts.push(script);
        });
      });
    }, Promise.resolve());
  }

  // Bootstrap puts modal backdrops on <body>, outside the swapped content, so
  // an open dialog would leave a grey overlay behind after navigating.
  function closeOverlays() {
    document.querySelectorAll('.modal.show').forEach(function (el) {
      var instance = window.bootstrap && window.bootstrap.Modal.getInstance(el);
      if (instance) instance.dispose();
    });
    document.querySelectorAll('.modal-backdrop').forEach(function (el) { el.remove(); });
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('overflow');
    document.body.style.removeProperty('padding-right');
  }

  function swapResponse(response, options) {
    if (response.redirected && new URL(response.url).origin !== window.location.origin) {
      window.location.assign(response.url);
      return Promise.resolve(false);
    }
    return response.text().then(function (html) {
      var doc = new DOMParser().parseFromString(html, 'text/html');
      if (!canSwap(doc)) {
        window.location.assign(response.url || options.url);
        return false;
      }
      var current = document.querySelector(contentSelector);
      var incoming = doc.querySelector(contentSelector);
      if (!current || !incoming) {
        window.location.assign(response.url || options.url);
        return false;
      }
      closeOverlays();
      var currentSidebar = document.querySelector('.app-sidebar');
      var incomingSidebar = doc.querySelector('.app-sidebar');
      if (currentSidebar && incomingSidebar) {
        currentSidebar.replaceWith(incomingSidebar);
        sidebar = incomingSidebar;
      }
      current.replaceWith(incoming);
      document.title = doc.title || document.title;
      if (options.history !== false) {
        var finalUrl = response.url || options.url;
        window.history.pushState({ ajaxPage: true }, '', finalUrl);
      }
      toggleSidebar(false);
      setBusy(false);
      window.scrollTo(0, 0);
      return loadScripts(doc).then(function () { return true; });
    });
  }

  function request(url, init, options) {
    options = options || {};
    if (activeRequest) activeRequest.abort();
    activeRequest = new AbortController();
    setBusy(true);
    var headers = new Headers(init.headers || {});
    headers.set('X-Requested-With', 'XMLHttpRequest');
    headers.set('Accept', 'text/html, application/xhtml+xml');
    init.headers = headers;
    init.credentials = 'same-origin';
    init.signal = activeRequest.signal;
    return fetch(url, init).then(function (response) {
      if (!response.ok && response.status >= 500) throw new Error('The server could not complete this request.');
      return swapResponse(response, { url: url, history: options.history });
    }).catch(function (error) {
      if (error.name !== 'AbortError') {
        setBusy(false);
        window.location.assign(url);
      }
    });
  }

  document.addEventListener('click', function (event) {
    if (!document.querySelector('.app-main')) return;
    var link = event.target.closest('a[href]');
    if (!isInternalPageLink(link, event)) return;
    var url = new URL(link.href, window.location.href);
    if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return;
    event.preventDefault();
    request(url.href, { method: 'GET' });
  });

  document.addEventListener('submit', function (event) {
    if (!document.querySelector('.app-main')) return;
    // A page script (for example the point of sale) already handled this form.
    if (event.defaultPrevented) return;
    var form = event.target;
    if (!(form instanceof HTMLFormElement) || form.hasAttribute('data-no-ajax')) return;
    var url = new URL(form.action || window.location.href, window.location.href);
    if (url.origin !== window.location.origin || url.pathname.indexOf('/admin/') === 0) return;
    var method = (form.method || 'get').toUpperCase();
    if (method !== 'GET' && method !== 'POST') return;
    event.preventDefault();
    if (method === 'GET') {
      var params = new URLSearchParams(new FormData(form));
      params.forEach(function (value, key) { if (!value) params.delete(key); });
      url.search = params.toString();
      request(url.href, { method: 'GET' });
      return;
    }
    var data = new FormData(form);
    if (event.submitter && event.submitter.name) data.append(event.submitter.name, event.submitter.value);
    var headers = {};
    var csrf = data.get('csrfmiddlewaretoken');
    if (csrf) headers['X-CSRFToken'] = csrf;
    request(url.href, { method: 'POST', body: data, headers: headers });
  });

  window.addEventListener('popstate', function () {
    request(window.location.href, { method: 'GET' }, { history: false });
  });
})();
