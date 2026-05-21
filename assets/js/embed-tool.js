(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var tool = document.querySelector('.pj-embed-tool');
    if (!tool) return;

    var fab = tool.querySelector('.pj-embed-fab');
    var panel = tool.querySelector('.pj-embed-panel');
    var closeBtn = tool.querySelector('.pj-embed-close');
    var tabs = tool.querySelectorAll('.pj-embed-tab');
    var helps = tool.querySelectorAll('.pj-embed-tab-help');
    var code = tool.querySelector('.pj-embed-code');
    var copyBtn = tool.querySelector('.pj-embed-copy');

    var url = window.location.origin + window.location.pathname;
    var origin = window.location.origin;
    function escapeAttr(s) {
      return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }
    var title = escapeAttr(tool.getAttribute('data-recipe-title') || document.title || '');

    var snippets = {
      simple:
        '<iframe src="' + url + '" width="100%" height="2400" ' +
        'style="border:0;max-width:860px;display:block;margin:0 auto" ' +
        'loading="lazy" title="' + title + '"></iframe>',
      responsive:
        '<iframe src="' + url + '" width="100%" ' +
        'style="border:0;display:block;max-width:860px;margin:0 auto" ' +
        'loading="lazy" title="' + title + '"></iframe>\n' +
        '<script>\n' +
        '(function () {\n' +
        '  window.addEventListener("message", function (e) {\n' +
        '    if (e.origin !== "' + origin + '") return;\n' +
        '    var d = e.data || {};\n' +
        '    if (d.type !== "tasteoflux:embed-height") return;\n' +
        '    var ifr = document.querySelectorAll("iframe");\n' +
        '    for (var i = 0; i < ifr.length; i++) {\n' +
        '      if (ifr[i].contentWindow === e.source) {\n' +
        '        ifr[i].style.height = d.height + "px"; break;\n' +
        '      }\n' +
        '    }\n' +
        '  });\n' +
        '})();\n' +
        '<\/script>'
    };

    function setTab(name) {
      for (var i = 0; i < tabs.length; i++) {
        var active = tabs[i].getAttribute('data-tab') === name;
        tabs[i].classList.toggle('actif', active);
        tabs[i].setAttribute('aria-selected', active ? 'true' : 'false');
      }
      for (var j = 0; j < helps.length; j++) {
        helps[j].hidden = helps[j].getAttribute('data-help') !== name;
      }
      code.value = snippets[name];
    }

    function openPanel() {
      panel.hidden = false;
      fab.setAttribute('aria-expanded', 'true');
      setTimeout(function () { code.focus(); code.select(); }, 0);
    }

    function closePanel() {
      panel.hidden = true;
      fab.setAttribute('aria-expanded', 'false');
      fab.focus();
    }

    setTab('simple');

    fab.addEventListener('click', function () {
      if (panel.hidden) openPanel(); else closePanel();
    });

    closeBtn.addEventListener('click', closePanel);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) closePanel();
    });

    for (var k = 0; k < tabs.length; k++) {
      (function (tab) {
        tab.addEventListener('click', function () {
          setTab(tab.getAttribute('data-tab'));
          code.focus();
          code.select();
        });
      })(tabs[k]);
    }

    var originalCopyLabel = copyBtn.textContent;
    var resetTimer = null;
    copyBtn.addEventListener('click', function () {
      var done = function () {
        copyBtn.textContent = 'Copié !';
        copyBtn.classList.add('ok');
        if (resetTimer) clearTimeout(resetTimer);
        resetTimer = setTimeout(function () {
          copyBtn.textContent = originalCopyLabel;
          copyBtn.classList.remove('ok');
        }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(code.value).then(done, fallbackCopy);
      } else {
        fallbackCopy();
      }
      function fallbackCopy() {
        code.focus();
        code.select();
        try { document.execCommand('copy'); done(); } catch (e) { /* noop */ }
      }
    });
  });
})();
