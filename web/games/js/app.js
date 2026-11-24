"use strict";
/* ==========================================================================
   GameRank — js/app.js
   Boot + all UI event logic (filters, sorting, view toggle, stats, modal).
   v4.0.0 adds:
     - state.ownership : 'all' | 'owned' | 'wishlist' (Owned vs Wishlist split)
     - Disk Footprint & Hardware SSD/HDD Advisor wired to /api/pc?category=ssds
     - Live GPU hydration from /api/pc/gpus
   ========================================================================== */

window.state = {
  search: "",
  ownership: "all",
  genre: "all",
  setting: "all",
  price: "all",
  campaign: "all",
  compat: "all",
  players: "all",
  preset: "playable",
  gpu: "none",
  sort: "compat",
  dir: "desc",
  view: "cards"
};

window.PC_SSDS = [
  { id: "wd-sn580-1tb", name: "WD Blue SN580 1TB NVMe", capacity_gb: 1000, price_bdt: 7800 },
  { id: "samsung-990-pro-2tb", name: "Samsung 990 PRO 2TB NVMe", capacity_gb: 2000, price_bdt: 21500 },
  { id: "wd-black-sn850x-4tb", name: "WD Black SN850X 4TB NVMe", capacity_gb: 4000, price_bdt: 39500 }
];

document.addEventListener("DOMContentLoaded", function () {
  applyCompat(window.GAMES);
  wireFilters();
  update();
  hydrateLivePcGpus();
  hydrateLivePcStorage();
});

function hydrateLivePcGpus() {
  if (typeof fetch !== "function" || window.location.protocol === "file:") return;
  fetch("/api/pc/gpus", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (gpus) {
      if (!Array.isArray(gpus) || !gpus.length) return;
      var select = document.getElementById("gpu");
      var nextMap = {};
      var optsHtml = [];
      gpus.forEach(function (g) {
        if (!g || !g.id || g.id === "vega-7-igpu") return;
        var cleanName = String(g.name || g.id).replace(/^GeForce\s+|^Radeon\s+|^NVIDIA\s+GeForce\s+/i, "");
        nextMap[g.id] = {
          id: g.id,
          name: cleanName,
          short: cleanName.split(" ").slice(-2).join(" "),
          tier: Number(g.tier || 0),
          psuVerdict: g.psu_550w_verdict || "pass"
        };
        optsHtml.push({ id: g.id, label: "Simulate: + " + cleanName + (g.psu_550w_verdict === "fail" ? " (550W PSU Risk)" : "") });
      });
      if (!Object.keys(nextMap).length) return;
      window.UPGRADE_GPUS = nextMap;
      if (select) {
        var prev = select.value;
        while (select.options.length > 1) select.remove(1);
        optsHtml.forEach(function (item) {
          var opt = document.createElement("option");
          opt.value = item.id;
          opt.textContent = item.label;
          select.appendChild(opt);
        });
        if (prev && nextMap[prev]) select.value = prev;
      }
      if (state.gpu !== "none") {
        window.GAMES.forEach(function (g) {
          g.upCompat = window.computeUpgradedCompat(g, state.gpu);
        });
        update();
      }
    })
    .catch(function () {});
}

function hydrateLivePcStorage() {
  if (typeof fetch !== "function" || window.location.protocol === "file:") return;
  fetch("/api/pc?category=ssds", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (payload) {
      if (!payload || !Array.isArray(payload.items) || !payload.items.length) return;
      window.PC_SSDS = payload.items;
      renderStorageAdvisor(currentGames());
    })
    .catch(function () {});
}

function wireFilters() {
  var $ = function (id) { return document.getElementById(id); };
  $("search").addEventListener("input", function (e) { state.search = e.target.value; update(); });
  ["ownership", "genre", "setting", "price", "campaign", "compat", "players", "preset", "gpu", "sort", "view"].forEach(function (k) {
    $(k).addEventListener("change", function (e) {
      state[k] = e.target.value;
      if (k === "sort") {
        state.dir = ["name", "size", "price"].indexOf(state.sort) >= 0 ? "asc" : "desc";
      }
      if (k === "gpu") {
        window.GAMES.forEach(function (g) {
          g.upCompat = state.gpu === "none" ? null : window.computeUpgradedCompat(g, state.gpu);
        });
      }
      update();
    });
  });
  $("dirBtn").addEventListener("click", function () {
    state.dir = state.dir === "asc" ? "desc" : "asc";
    update();
  });
  $("reset").addEventListener("click", function () {
    Object.assign(state, { search: "", ownership: "all", genre: "all", setting: "all", price: "all",
      campaign: "all", compat: "all", players: "all", preset: "playable", gpu: "none",
      sort: "compat", dir: "desc" });
    window.GAMES.forEach(function (g) { g.upCompat = null; });
    $("search").value = "";
    ["ownership", "genre", "setting", "price", "campaign", "compat", "players", "preset", "gpu", "sort", "view"]
      .forEach(function (k) { $(k).value = state[k]; });
    update();
  });
  var resultsEl = document.getElementById("results");
  resultsEl.addEventListener("click", function (e) {
    if (e.target.closest("#emptyReset")) {
      $("reset").click();
      return;
    }
    if (e.target.closest("a")) return;
    var row = e.target.closest(".row");
    if (!row) return;
    var g = window.GAMES.find(function (x) { return x.id === row.getAttribute("data-id"); });
    if (g) showDetail(g, row);
  });
  resultsEl.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    if (e.target.closest("a")) return;
    var row = e.target.closest(".row");
    if (!row) return;
    e.preventDefault();
    var g = window.GAMES.find(function (x) { return x.id === row.getAttribute("data-id"); });
    if (g) showDetail(g, row);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      hideDetail();
      return;
    }
    if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) {
      var tag = (document.activeElement && document.activeElement.tagName) || "";
      if (tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") {
        e.preventDefault();
        $("search").focus();
      }
    }
  });
}

function activeTier(g) {
  return (state.gpu !== "none" && g.upCompat) ? g.upCompat : g.compat;
}

function currentGames() {
  var q = state.search.trim().toLowerCase();
  var out = window.GAMES.filter(function (g) {
    if (q && (g.name.toLowerCase().indexOf(q) < 0)) return false;
    if (state.ownership !== "all" && (g.ownership || "wishlist") !== state.ownership) return false;
    if (state.genre !== "all" && g.genre !== state.genre) return false;
    if (state.setting !== "all" && g.setting !== state.setting) return false;
    if (state.price !== "all") {
      if (state.price === "f2p" && g.priceModel !== "f2p") return false;
      if (state.price === "cheap" && g.priceModel !== "f2p" && g.priceUsd > 15) return false;
      if (state.price === "any" && g.priceModel === "f2p") return false;
    }
    if (state.campaign !== "all") {
      var c = g.campaign || {};
      if (state.campaign === "yes" && !c.exists) return false;
      if (state.campaign === "free" && !String(c.freeOrPaid || "").toLowerCase().startsWith("free")) return false;
      if (state.campaign === "none" && c.exists) return false;
    }
    if (state.compat !== "all" && activeTier(g).tier !== state.compat) return false;
    if (state.players !== "all") {
      var s = (g.players || {}).status;
      if (state.players === "mp-active" && ["very-active", "active"].indexOf(s) < 0) return false;
      if (state.players === "mp-any" && s === "n/a-sp") return false;
      if (state.players === "sp-only" && s !== "n/a-sp") return false;
    }
    return true;
  });

  var sorters = {
    compat:   function (a, b) { return activeTier(a).score - activeTier(b).score; },
    campaign: function (a, b) { return ((a.campaign || {}).quality || 0) - ((b.campaign || {}).quality || 0); },
    ai:       function (a, b) { return ((a.ai || {}).score || 0) - ((b.ai || {}).score || 0); },
    graphics: function (a, b) { return ((a.graphics || {}).score || 0) - ((b.graphics || {}).score || 0); },
    name:     function (a, b) { return a.name.localeCompare(b.name); },
    size:     function (a, b) { return (a.installGB || 0) - (b.installGB || 0); },
    price:    function (a, b) { return (a.priceUsd || 0) - (b.priceUsd || 0); },
    players:  function (a, b) {
      var order = ["very-active", "active", "moderate", "small", "inactive", "n/a-sp"];
      return order.indexOf((b.players || {}).status) - order.indexOf((a.players || {}).status);
    }
  };
  var cmp = sorters[state.sort] || sorters.compat;
  out.sort(function (a, b) { return state.dir === "asc" ? cmp(a, b) : -cmp(a, b); });
  return out;
}

function fmtSize(gb) {
  if (gb >= 1000) return (gb / 1024).toFixed(2) + " TB (" + Math.round(gb) + " GB)";
  return Math.round(gb * 10) / 10 + " GB";
}

function renderStorageAdvisor(filteredGames) {
  var box = document.getElementById("storage-advisor");
  if (!box) return;
  var totalFilteredGB = filteredGames.reduce(function (s, g) { return s + (Number(g.installGB) || 0); }, 0);
  var ssdPriorityGames = filteredGames.filter(function (g) {
    var v = (g.storageAdvice || {}).verdict;
    return v === "ssd-strongly-advised" || v === "ssd-helps";
  });
  var ssdPriorityGB = ssdPriorityGames.reduce(function (s, g) { return s + (Number(g.installGB) || 0); }, 0);
  var hddSafeGB = totalFilteredGB - ssdPriorityGB;

  var sortedSsds = (window.PC_SSDS || []).slice().sort(function (a, b) { return (a.capacity_gb || 0) - (b.capacity_gb || 0); });
  var recSsd = sortedSsds.find(function (d) { return (d.capacity_gb || 0) >= totalFilteredGB * 1.15; }) || sortedSsds[sortedSsds.length - 1];
  var hddFits = totalFilteredGB <= 850;

  box.replaceChildren();

  function addItem(label, val, cls) {
    var sp = document.createElement("span");
    if (cls) sp.className = "adv-chip " + cls;
    sp.appendChild(document.createTextNode(label + " "));
    var st = document.createElement("strong");
    st.textContent = val;
    sp.appendChild(st);
    box.appendChild(sp);
  }

  addItem("Filtered Footprint:", fmtSize(totalFilteredGB), hddFits ? "adv-good" : "adv-warn");
  addItem("SSD-Priority Titles (" + ssdPriorityGames.length + "):", fmtSize(ssdPriorityGB), ssdPriorityGB > 0 ? "adv-warn" : "adv-good");
  addItem("HDD-Fine Titles:", fmtSize(hddSafeGB), "adv-good");
  addItem("vs Baseline 1 TB HDD:", hddFits ? "Fits all filtered games" : "Exceeds 1 TB HDD (" + Math.round(totalFilteredGB / 931 * 100) + "% full)", hddFits ? "adv-good" : "adv-warn");
  if (recSsd) {
    var priceTxt = recSsd.price_bdt ? (" (\u09F3" + Number(recSsd.price_bdt).toLocaleString() + ")") : "";
    addItem("PC Storage Match:", recSsd.name + priceTxt, "");
  }
}

function update() {
  var games = currentGames();
  var $ = function (id) { return document.getElementById(id); };

  var total = window.GAMES.length;
  var owned = window.GAMES.filter(function (g) { return g.ownership === "owned"; }).length;
  var wishlist = total - owned;
  var great = games.filter(function (g) { return activeTier(g).tier === "great"; }).length;
  var f2p   = games.filter(function (g) { return g.priceModel === "f2p"; }).length;
  var gpuTxt = state.gpu !== "none" && window.UPGRADE_GPUS[state.gpu]
    ? " \u00B7 simulating <strong>" + esc(window.UPGRADE_GPUS[state.gpu].name) + "</strong>"
    : "";
  $("stats").innerHTML =
    "<strong>" + great + "</strong> of <strong>" + games.length + "</strong> shown run great on your PC" + gpuTxt +
    " \u00B7 <strong>" + owned + "</strong> owned (Steam) / <strong>" + wishlist + "</strong> wishlist \u00B7 " +
    "<strong>" + f2p + "</strong> free \u00B7 total catalog: <strong>" + total + "</strong>";

  renderStorageAdvisor(games);

  $("results").innerHTML =
    state.view === "table" ? renderTable(games) : renderCards(games);

  $("count").textContent = games.length + " / " + total + " games";
}
