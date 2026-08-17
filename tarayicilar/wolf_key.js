/*!
 * wolf_key.js — Wolf Terminal erisim kodu tasiyicisi
 * -------------------------------------------------------------
 * tarayicilar/*.html dosyalarinda <head> icindeki EN ILK <script>
 * olarak yuklenmelidir:
 *
 *     <head>
 *       <meta charset="utf-8">
 *       <script src="wolf_key.js"></script>     <-- diger her seyden ONCE
 *       ...
 *
 * Neden: MTF Dashboard gibi araclar acilir acilmaz fetch atiyor.
 * Yama parent'tan (iframe load olayi) yapilirsa o ilk istek yamasiz
 * cikip 401 yiyor. Buraya konunca yarisma durumu tamamen ortadan kalkar.
 *
 * Ayni origin oldugu icin localStorage parent ile ortaktir; arac
 * dogrudan URL ile acilsa bile ayni kodu kullanir.
 */
(function () {
  'use strict';

  var PROXY = 'web-production-2bdde.up.railway.app';
  var LS    = 'wolf_access_key';

  function key() {
    try { return localStorage.getItem(LS) || ''; } catch (e) { return ''; }
  }
  function keySil() {
    try { localStorage.removeItem(LS); } catch (e) {}
  }

  // Parent'a haber ver: kod gecersiz -> ust pencere giris ekranini acsin
  function parentUyar(tur) {
    try {
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({ wolf: tur }, '*');
      }
    } catch (e) {}
  }

  // ---- fetch yamasi ----
  if (!window.__wolfKeyPatched && window.fetch) {
    window.__wolfKeyPatched = true;
    var orig = window.fetch.bind(window);

    window.fetch = function (input, init) {
      try {
        var url = (typeof input === 'string') ? input : (input && input.url) || '';
        if (url.indexOf(PROXY) !== -1) {
          if (typeof input !== 'string') input = url;
          init = init ? Object.assign({}, init) : {};
          var h = new Headers(init.headers || {});
          h.set('X-Wolf-Key', key());
          init.headers = h;
        }
      } catch (e) {}

      return orig(input, init).then(function (res) {
        try {
          if (res.url && res.url.indexOf(PROXY) !== -1) {
            if (res.status === 401) { keySil(); parentUyar('gecersiz'); }
            else if (res.status === 429) { parentUyar('limit'); }
            else if (res.status === 503) { parentUyar('mesgul'); }
          }
        } catch (e) {}
        return res;
      });
    };
  }

  // ---- XMLHttpRequest yamasi (guvenlik agi) ----
  // Su an araclar sadece fetch kullaniyor, ama ileride XHR eklenirse
  // sessizce 401 yemesin diye.
  if (!window.__wolfXhrPatched && window.XMLHttpRequest) {
    window.__wolfXhrPatched = true;
    var Open = XMLHttpRequest.prototype.open;
    var Send = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (m, u) {
      try { this.__wolfProxy = (String(u).indexOf(PROXY) !== -1); } catch (e) {}
      return Open.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function () {
      try {
        if (this.__wolfProxy) this.setRequestHeader('X-Wolf-Key', key());
      } catch (e) {}
      return Send.apply(this, arguments);
    };
  }
})();
