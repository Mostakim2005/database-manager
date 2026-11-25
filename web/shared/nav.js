"use strict";
/* Shared Cross-Domain Top Navigation Bar for Standalone Database Manager Views.
 * Automatically skips rendering when inside the web/index.html portal iframe so
 * there are never duplicate toolbars. Uses strictly safe DOM construction.
 */
(function () {
  if (window.self !== window.top) return;

  var FALLBACK_DOMAINS = [
    { domain: "pc", short_label: "PC & PSU", display_name: "PC Parts & PSU Guard", web_path: "pc/index.html" },
    { domain: "games", short_label: "Games", display_name: "Games & Benchmarks", web_path: "games/index.html" },
    { domain: "ai", short_label: "AI Matrix", display_name: "AI Models & Pricing", web_path: "ai/index.html" },
    { domain: "media", short_label: "Media", display_name: "Media & Adaptations", web_path: "media/index.html" },
    { domain: "book", short_label: "Book", display_name: "Book Collection", web_path: "book/index.html" },
    { domain: "phone", short_label: "Phone", display_name: "Phone & Mobile", web_path: "phone/index.html" },
    { domain: "github", short_label: "GitHub", display_name: "GitHub Repositories", web_path: "github/index.html" }
  ];

  function detectCurrentDomain(domains) {
    var path = String(window.location.pathname || "").toLowerCase();
    for (var i = 0; i < domains.length; i += 1) {
      var d = domains[i].domain.toLowerCase();
      if (path.indexOf("/" + d + "/") >= 0 || path.endsWith("/" + d)) {
        return domains[i].domain;
      }
    }
    return "";
  }

  function injectStyles() {
    if (document.getElementById("dbm-shared-nav-style")) return;
    var style = document.createElement("style");
    style.id = "dbm-shared-nav-style";
    style.textContent = [
      ".dbm-shared-nav{position:sticky;top:0;z-index:950;background:#11161f;border-bottom:1px solid #30363d;",
      "padding:8px 18px;margin:-20px -24px 16px;display:flex;flex-wrap:wrap;align-items:center;",
      "justify-content:space-between;gap:10px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:12.5px;color:#e6edf3;}",
      ".dbm-shared-nav.flush{margin:0 0 0 0;}",
      ".dbm-nav-left,.dbm-nav-pills{display:flex;flex-wrap:wrap;align-items:center;gap:6px;}",
      ".dbm-nav-link{display:inline-flex;align-items:center;gap:5px;padding:5px 10px;border-radius:6px;",
      "border:1px solid #30363d;background:#161b22;color:#c9d1d9;text-decoration:none;font-weight:600;white-space:nowrap;}",
      ".dbm-nav-link:hover{border-color:#58a6ff;color:#58a6ff;background:#1c232e;}",
      ".dbm-nav-link.home{border-color:rgba(63,185,80,0.45);color:#7ee787;}",
      ".dbm-nav-link.active{background:rgba(88,166,255,0.16);border-color:#58a6ff;color:#58a6ff;}",
      ".dbm-nav-sep{color:#484f58;margin:0 2px;}"
    ].join("");
    document.head.appendChild(style);
  }

  function buildNav(domains) {
    injectStyles();
    var existing = document.getElementById("dbm-shared-nav");
    if (existing) existing.remove();

    var current = detectCurrentDomain(domains);
    var nav = document.createElement("nav");
    nav.id = "dbm-shared-nav";
    nav.className = "dbm-shared-nav";
    nav.setAttribute("aria-label", "Database Manager Global Navigation");

    var bodyStyle = window.getComputedStyle(document.body);
    if (parseFloat(bodyStyle.paddingLeft || "0") === 0) {
      nav.classList.add("flush");
    }

    var left = document.createElement("div");
    left.className = "dbm-nav-left";

    var homeLink = document.createElement("a");
    homeLink.className = "dbm-nav-link home";
    homeLink.href = "../index.html#home";
    homeLink.textContent = "Main Overview (0)";
    left.appendChild(homeLink);

    var portalLink = document.createElement("a");
    portalLink.className = "dbm-nav-link";
    portalLink.href = "../index.html" + (current ? "#" + encodeURIComponent(current) : "");
    portalLink.textContent = "Portal Tab View";
    left.appendChild(portalLink);

    var sep = document.createElement("span");
    sep.className = "dbm-nav-sep";
    sep.textContent = "|";
    left.appendChild(sep);

    var pills = document.createElement("div");
    pills.className = "dbm-nav-pills";
    domains.forEach(function (d, idx) {
      var a = document.createElement("a");
      a.className = "dbm-nav-link" + (d.domain === current ? " active" : "");
      a.href = "../" + (d.web_path || (d.domain + "/index.html"));
      a.title = (d.display_name || d.domain) + " (Shortcut: " + (idx + 1) + ")";
      a.textContent = d.short_label || d.display_name || d.domain;
      pills.appendChild(a);
    });

    nav.appendChild(left);
    nav.appendChild(pills);
    document.body.insertBefore(nav, document.body.firstChild);

    if (!window._dbmNavKeyWired) {
      window._dbmNavKeyWired = true;
      document.addEventListener("keydown", function (e) {
        if (e.altKey || e.ctrlKey || e.metaKey) return;
        var tag = (document.activeElement && document.activeElement.tagName) || "";
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
        if (e.key === "0") {
          window.location.href = "../index.html#home";
          return;
        }
        var num = parseInt(e.key, 10);
        if (num >= 1 && num <= window._dbmNavDomains.length) {
          var target = window._dbmNavDomains[num - 1];
          window.location.href = "../" + (target.web_path || (target.domain + "/index.html"));
        }
      });
    }
    window._dbmNavDomains = domains;
  }

  function initSharedNav() {
    window._dbmNavDomains = FALLBACK_DOMAINS;
    buildNav(FALLBACK_DOMAINS);
    if (typeof fetch === "function" && window.location.protocol !== "file:") {
      fetch("/api/status", { cache: "no-store" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (data && Array.isArray(data.domains) && data.domains.length) {
            var visible = data.domains.filter(function (d) { return d && d.show_in_portal !== false; });
            visible.sort(function (a, b) { return Number(a.tab_order || 999) - Number(b.tab_order || 999); });
            if (visible.length) buildNav(visible);
          }
        })
        .catch(function () {});
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSharedNav);
  } else {
    initSharedNav();
  }
})();
