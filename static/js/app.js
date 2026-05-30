// === === ===
var STUDIOS = [];
var CURRENT_USER = null;
var USER_FAVORITES = [];

const RISK_LABEL = {
  safe: {text:"\u2705 \u5b89\u5168", cls:"risk-safe"},
  warning: {text:"\u26a0\ufe0f \u5b58\u7591", cls:"risk-warning"},
  danger: {text:"\u274c \u907f\u96f7", cls:"risk-danger"}
};
const LEVEL_MAP = {
  "platinum": {icon:"\ud83e\udd47", label:"\u91d1\u724c", cls:"tag-platinum"},
  "gold": {icon:"\ud83e\udd49", label:"\u9ec4\u724c", cls:"tag-gold"},
  "silver": {icon:"\ud83e\udd48", label:"\u94f6\u724c", cls:"tag-silver"}
};

function escHtml(t) {
  var d = document.createElement("div");
  d.textContent = t || "";
  return d.innerHTML;
}
function formatDate(d) {
  if (!d) return "-";
  return d.replace(/(\d{4})-(\d{2})-(\d{2}).*/, "$1.$2.$3") || d;
}

// === API ===
async function loadStudios() {
  try { var r = await fetch("/api/studios"); var d = await r.json(); STUDIOS = d.studios || []; }
  catch(e) { STUDIOS = []; }
}
async function checkLogin() {
  try { var r = await fetch("/api/session"); var d = await r.json(); CURRENT_USER = d.user || null; return CURRENT_USER; }
  catch(e) { CURRENT_USER = null; return null; }
}

// === Nav ===
async function updateNav() {
  var navEl = document.getElementById("navLogin");
  if (!navEl) return;
  var user = await checkLogin();
  var csLink = '<span style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;font-size:1rem;font-weight:700;color:rgba(255,255,255,0.9);">\ud83d\udd2a \u8dd1\u5200\u907f\u96f7\u6307\u5357</span>' + '<a href="/" style="display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border-radius:20px;font-size:0.82rem;color:rgba(255,255,255,0.65);text-decoration:none;font-weight:500;">\ud83c\udfe0 \u9996\u9875</a>' + '<a href="#" id="navCsLink" style="display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border-radius:20px;font-size:0.82rem;color:rgba(255,255,255,0.65);text-decoration:none;font-weight:500;cursor:pointer;">\ud83d\udcde \u5ba2\u670d</a>';
  if (user) {
    navEl.innerHTML = csLink +
      '<span class="nav-user-wrap"><span class="nav-user-icon">\ud83d\udc64</span><span class="nav-user-name">' + escHtml(user) + '</span></span>' +
      '<a href="/dashboard" class="nav-action-link">\U0001f4cb \u6211\u7684</a><a href="submit.html" class="nav-action-link">\u270f\ufe0f \u6295\u7a3f</a>' +
      '<a href="about.html" class="nav-action-link">\u2139\ufe0f \u5173\u4e8e</a>' +
      (user === "admin" ? '<a href="admin.html" class="nav-action-link">\u2699\ufe0f \u7ba1\u7406</a>' : "") +
      '<a href="/logout" class="nav-logout-link">\ud83d\udeaa</a>';
  } else {
    navEl.innerHTML = csLink + '<a href="/login" class="nav-login-link">\ud83d\udd11 \u767b\u5f55</a>';
  }
  var csl = document.getElementById("navCsLink");
  if (csl) csl.onclick = function(e) { e.preventDefault(); showCsModal(); };
}

// === Card ===
function renderCard(s) {
  var risk = RISK_LABEL[s.risk] || RISK_LABEL.danger;
  var badge = "";
  if (s.level && LEVEL_MAP[s.level]) {
    var lv = LEVEL_MAP[s.level];
    badge = "<span class=\"level-badge " + lv.cls + "\">" + lv.icon + " " + lv.label + "</span>";
  }
  var favStar = "";
  if (CURRENT_USER) {
    var isFav = USER_FAVORITES.indexOf(s.id) >= 0;
    favStar = "<span class=\"fav-btn\" style=\"cursor:pointer;font-size:1.1rem;margin-left:8px;position:relative;z-index:2;\" onclick=\"event.stopPropagation();toggleFav('" + s.id + "')\" title=\"" + (isFav ? "\u53d6\u6d88\u6536\u85cf" : "\u6536\u85cf") + "\">" + (isFav ? "\u2605" : "\u2606") + "</span>";
  }
  var contactHtml = "";
  if (s.contact && s.contact_hidden) {
    contactHtml = "<span style=\"color:#8a8aaa;font-size:0.82rem;\">\ud83d\udd12 <a href=\"/login\" style=\"color:#4a6cf7;\">\u767b\u5f55\u540e\u67e5\u770b\u8054\u7cfb\u65b9\u5f0f</a></span>";
  } else if (s.contact) {
    contactHtml = "<span>\ud83d\udd17 " + escHtml(s.contact) + "</span>";
  }
  return "<div class=\"card\" style=\"position:relative;cursor:pointer;\" onclick=\"location.href='/studio/" + s.id + "'\">" +
    "<div class=\"card-header\"><span class=\"card-name\">" + escHtml(s.name) + badge + favStar + "</span><span class=\"card-risk " + risk.cls + "\">" + risk.text + "</span></div>" +
    "<div class=\"card-detail\">" + escHtml(s.detail) + "</div>" +
    "<div class=\"card-meta\">" +
      (s.platform ? "<span>\ud83d\udcf1 " + escHtml(s.platform) + "</span>" : "") +
      contactHtml +
      "<span>\ud83d\udcc5 " + formatDate(s.date) + "</span>" +
      "<span>\ud83d\udcdd " + escHtml(s.source) + "</span>" +
    "</div></div>";
}

// === Favorites ===
async function loadFavorites() {
  if (!CURRENT_USER) { USER_FAVORITES = []; return; }
  try { var r = await fetch("/api/favorites"); var d = await r.json(); USER_FAVORITES = d.favorites || []; }
  catch(e) { USER_FAVORITES = []; }
}
async function toggleFav(studioId) {
  if (!CURRENT_USER) { window.location.href = "/login"; return; }
  try {
    var r = await fetch("/api/favorites/" + studioId, { method: "POST" });
    var d = await r.json();
    if (d.ok) {
      var idx = USER_FAVORITES.indexOf(studioId);
      if (idx >= 0) USER_FAVORITES.splice(idx, 1);
      else USER_FAVORITES.push(studioId);
      if (window.location.pathname === "/" || window.location.pathname === "/index.html") initHome();
      else if (window.location.pathname === "/list.html") renderFullList();
    }
  } catch(e) {}
}

// === Comments ===
async function loadComments(studioId) {
  try {
    var r = await fetch("/api/studios/" + studioId + "/comments");
    var d = await r.json();
    var el = document.getElementById("comments-" + studioId);
    if (!el) return;
    if (d.comments && d.comments.length > 0) {
      el.innerHTML = d.comments.map(function(c) {
        var badge = c.is_admin ? "<span style=\"display:inline-flex;align-items:center;gap:2px;margin-left:4px;padding:1px 6px;background:#4a6cf7;color:#fff;border-radius:4px;font-size:0.65rem;font-weight:600;vertical-align:middle;\">\ud83d\udee1\ufe0f \u7ba1\u7406\u5458</span>" : "";
        return "<div style=\"padding:6px 0;border-bottom:1px solid #f5f5f5;font-size:0.82rem;\"><strong style=\"color:#4a6cf7;\">" + escHtml(c.user) + badge + "</strong>: " + escHtml(c.content) + " <span style=\"color:#bbb;font-size:0.72rem;float:right;\">" + (c.date||"") + "</span></div>";
      }).join("");
    } else {
      el.innerHTML = "<span style=\"font-size:0.78rem;color:#bbb;\">\u6682\u65e0\u8bc4\u8bba</span>";
    }
  } catch(e) {}
}
function sdci(sid) {
  var inp = document.getElementById("ci_" + sid);
  if (!inp || !inp.value.trim()) return;
  var x = new XMLHttpRequest();
  x.open("POST", "/api/comments", true);
  x.setRequestHeader("Content-Type", "application/json");
  x.onload = function() { if (x.status === 200) { inp.value = ""; loadComments(sid); } };
  x.send(JSON.stringify({studio_id:sid, content:inp.value.trim()}));
}

// === Search ===
function doSearch() {
  var q = document.getElementById("searchInput");
  if (!q || !q.value.trim()) return;
  var kw = q.value.trim().toLowerCase();
  var results = STUDIOS.filter(function(s){ return s.name.toLowerCase().indexOf(kw) >= 0 || (s.detail||"").toLowerCase().indexOf(kw) >= 0; });
  var el = document.getElementById("searchResults");
  var modal = document.getElementById("searchModal");
  if (!el || !modal) return;
  if (results.length === 0) {
    el.innerHTML = "<div style=\"padding:40px 20px;text-align:center;color:#8a8aaa;\">\ud83d\ude15 \u6ca1\u6709\u627e\u5230 <strong>" + escHtml(kw) + "</strong> \u7684\u76f8\u5173\u8bb0\u5f55</div>";
    modal.style.display = "flex";
    return;
  }
  el.innerHTML = results.map(function(s) {
    var risk = RISK_LABEL[s.risk] || RISK_LABEL.danger;
    var badge = "";
    if (s.level && LEVEL_MAP[s.level]) {
      var lv = LEVEL_MAP[s.level];
      badge = "<span class=\"level-badge " + lv.cls + "\">" + lv.icon + " " + lv.label + "</span>";
    }
    return "<div class=\"card\" style=\"margin-bottom:10px;cursor:pointer;\" onclick=\"closeSearch();showStudioDetail(\'" + s.id + "\')\">" +
      "<div class=\"card-header\"><span class=\"card-name\">" + escHtml(s.name) + badge + "</span><span class=\"card-risk " + risk.cls + "\">" + risk.text + "</span></div>" +
      "<div class=\"card-detail\">" + escHtml(s.detail) + "</div>" +
      "<div class=\"card-meta\">" +
      (s.platform ? "<span>\ud83d\udcf1 " + escHtml(s.platform) + "</span>" : "") +
      "<span>\ud83d\udcc5 " + formatDate(s.date) + "</span>" +
      "<span>\ud83d\udcdd " + escHtml(s.source) + "</span>" +
      "</div></div>";
  }).join("");
  modal.style.display = "flex";
}
function showStudioDetail(studioId) {
  window.location.href = "/studio/" + encodeURIComponent(studioId);
}
function closeSearch() {
  var modal = document.getElementById("searchModal");
  if (modal) modal.style.display = "none";
}


// === Home ===

async function loadSettings() {
  try {
    var r = await fetch("/api/settings");
    var s = await r.json();
    if (!s) return;
    // Page title
    if (s.site_name) document.title = s.site_name + " \u00b7 \u4e09\u89d2\u6d32\u884c\u52a8\u5de5\u4f5c\u5ba4\u7ea2\u9ed1\u699c";
    // OG meta
    var mt = document.querySelector("meta[name=\u0027description\u0027]");
    if (mt && s.site_description) mt.content = s.site_description;
    // Logo
    var li = document.querySelector(".logo-icon");
    if (li && s.logo_emoji) li.textContent = s.logo_emoji;
    var lt = document.querySelector(".logo-text");
    if (lt && s.site_name) lt.textContent = s.site_name;
    // Hero
    var ht = document.querySelector(".hero h1");
    if (ht) {
      if (s.hero_title && s.hero_highlight) {
        ht.innerHTML = s.hero_title + " <span class=\u0027highlight\u0027>" + s.hero_highlight + "</span>";
      } else if (s.hero_title) {
        ht.textContent = s.hero_title;
      }
    }
    // Primary color
    if (s.primary_color) {
      document.documentElement.style.setProperty("--primary", s.primary_color);
    }
    // Footer
    var ft = document.querySelector(".footer p");
    if (ft && s.footer_text) ft.textContent = s.footer_text;
  } catch(e) {}
}

async function initHome() {
  await loadStudios(); await loadSettings();
  await checkLogin();
  await loadFavorites();
  updateNav();
  // Platform grid
  var pg = document.getElementById("platformGrid");
  if (pg) {
    pg.innerHTML = '<a href="/list.html?platform=xianyu" class="platform-item">' +
      '<span class="pi-icon">\ud83d\uded2</span><span class="pi-name">\u95f2\u9c7c</span><span class="pi-count">' + STUDIOS.filter(function(s){ return s.platform === "\u95f2\u9c7c" || s.platform === "xianyu"; }).length + '\u5bb6</span></a>' +
      '<a href="/list.html?platform=douyin" class="platform-item">' +
      '<span class="pi-icon">\ud83c\udfa5</span><span class="pi-name">\u6296\u97f3</span><span class="pi-count">' + STUDIOS.filter(function(s){ return s.platform === "\u6296\u97f3" || s.platform === "douyin"; }).length + '\u5bb6</span></a>' +
      '<a href="/list.html?platform=bilibili" class="platform-item">' +
      '<span class="pi-icon">\ud83d\udcfa</span><span class="pi-name">B\u7ad9</span><span class="pi-count">' + STUDIOS.filter(function(s){ return s.platform === "B\u7ad9" || s.platform === "bilibili"; }).length + '\u5bb6</span></a>' +
      '<a href="/list.html?platform=xiaohongshu" class="platform-item">' +
      '<span class="pi-icon">🍠</span><span class="pi-name">\u5c0f\u7ea2\u4e66</span><span class="pi-count">' + STUDIOS.filter(function(s){ return s.platform === "\u5c0f\u7ea2\u4e66" || s.platform === "xiaohongshu"; }).length + '\u5bb6</span></a>';
  }
  var total = document.getElementById("totalCount");
  var black = document.getElementById("blackCount");
  var white = document.getElementById("whiteCount");
  var report = document.getElementById("reportCount");
  var list = document.getElementById("recentList");
  if (total) total.textContent = STUDIOS.length;
  if (black) black.textContent = STUDIOS.filter(function(s){ return s.risk === "danger"; }).length;
  if (white) white.textContent = STUDIOS.filter(function(s){ return s.risk === "safe"; }).length;
  if (report) report.textContent = STUDIOS.length;
  if (list) {
    var recent = [].concat(STUDIOS).reverse();
    list.innerHTML = recent.map(renderCard).join("");
    recent.forEach(function(s){ loadComments(s.id); });
  }
  var platforms = ["\u95f2\u9c7c", "\u6296\u97f3", "B\u7ad9", "\u5c0f\u7ea2\u4e66"];
  var platIds = ["xianyu", "douyin", "bilibili", "xiaohongshu"];
  for (var i = 0; i < platforms.length; i++) {
    var el = document.getElementById("plat-" + platIds[i]);
    if (!el) continue;
    var filtered = STUDIOS.filter(function(s){ return s.platform === platforms[i] || s.platform === platIds[i]; });
    if (filtered.length > 0) {
      el.innerHTML = filtered.map(renderCard).join("");
      filtered.forEach(function(s){ loadComments(s.id); });
    } else {
      el.innerHTML = "<p class=\"loading\" style=\"padding:40px 0;\">\ud83d\ude15 \u8fd9\u4e2a\u677f\u5757\u8fd8\u6ca1\u6709\u6570\u636e</p>";
    }
  }
}

// === List ===
var _currentPlatform = null;
var _currentRisk = "all";
async function initFullList() {
  await loadStudios(); await loadSettings();
  await checkLogin();
  await loadFavorites();
  updateNav();
  var urlParams = new URLSearchParams(window.location.search);
  var detail = urlParams.get("detail");
  if (detail) {
    showDetailView(detail);
    return;
  }
  var plat = urlParams.get("platform");
  if (plat) { _currentPlatform = plat; filterPlatform(plat, null); }
  else { filterList(_currentRisk, null); }
}

function showDetailView(studioId) {
  var list = document.getElementById("fullList");
  if (!list) return;
  // Hide filter bars, show detail
  var filters = document.querySelectorAll(".filter-bar");
  filters.forEach(function(f){ f.style.display = "none"; });
  var headings = document.querySelectorAll("section h2");
  headings.forEach(function(h){ h.style.display = "none"; });
  var found = STUDIOS.filter(function(s2){ return s2.id === studioId; })[0];
  if (!found) {
    list.innerHTML = "<p style=\"padding:40px;text-align:center;color:#e74c3c;\">\u274c \u672a\u627e\u5230\u8be5\u5de5\u4f5c\u5ba4</p>";
    return;
  }
  list.innerHTML = renderCard(found) + "<div style=\"margin-top:12px;text-align:center;\"><a href=\"/list.html\" style=\"display:inline-block;padding:8px 20px;background:#4a6cf7;color:#fff;border-radius:8px;font-size:0.85rem;text-decoration:none;\">\u2190 \u8fd4\u56de\u5217\u8868</a></div>";
  loadComments(found.id);
}
function filterList(risk, btn) {
  _currentRisk = risk || "all";
  var buttons = document.querySelectorAll(".filter-btn");
  if (btn) { buttons.forEach(function(b){ b.classList.remove("active"); }); btn.classList.add("active"); }
  var list = document.getElementById("fullList");
  if (!list) return;
  var pmap = {xianyu:"\u95f2\u9c7c",douyin:"\u6296\u97f3",bilibili:"B\u7ad9",xiaohongshu:"\u5c0f\u7ea2\u4e66"};
  var data = _currentPlatform ? STUDIOS.filter(function(s){ return s.platform === _currentPlatform || s.platform === pmap[_currentPlatform]; }) : STUDIOS;
  if (risk && risk !== "all") data = data.filter(function(s){ return s.risk === risk; });
  var q = document.getElementById("listSearch");
  if (q && q.value.trim()) {
    var kw = q.value.trim().toLowerCase();
    data = data.filter(function(s){ return s.name.toLowerCase().indexOf(kw) >= 0 || (s.detail||"").toLowerCase().indexOf(kw) >= 0; });
  }
  if (data.length === 0) { list.innerHTML = "<p class=\"loading\" style=\"padding:40px 20px;text-align:center;color:#8a8aaa;\">\ud83d\ude15 \u6ca1\u6709\u5339\u914d\u7684\u5de5\u4f5c\u5ba4</p>"; return; }
  list.innerHTML = data.map(renderCard).join("");
  data.forEach(function(s){ loadComments(s.id); });
}

function renderFullList() {
  var list = document.getElementById("fullList");
  if (!list) return;
  var pmap = {xianyu:"\u95f2\u9c7c",douyin:"\u6296\u97f3",bilibili:"B\u7ad9",xiaohongshu:"\u5c0f\u7ea2\u4e66"};
  var data = _currentPlatform ? STUDIOS.filter(function(s){ return s.platform === _currentPlatform || s.platform === pmap[_currentPlatform]; }) : STUDIOS;
  if (data.length === 0) { list.innerHTML = "<p style=\"padding:40px 20px;text-align:center;color:#8a8aaa;\">\ud83d\ude15 \u8fd9\u4e2a\u677f\u5757\u8fd8\u6ca1\u6709\u6570\u636e</p>"; return; }
  list.innerHTML = data.map(renderCard).join("");
  data.forEach(function(s){ loadComments(s.id); });
}
function filterPlatform(platform, el) {
  if (platform === "all") { _currentPlatform = null; }
  else { _currentPlatform = platform; }
  var platBtns = document.querySelectorAll("#platformFilters .filter-btn");
  platBtns.forEach(function(b){ b.classList.remove("active"); });
  if (el) el.classList.add("active");
  filterList(_currentRisk, null);
}

// === CS Modal ===
function showCsModal() {
  var o = document.getElementById("csModalOverlay");
  if (o) { o.style.display = "flex"; return; }
  o = document.createElement("div");
  o.id = "csModalOverlay";
  o.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;";
  o.onclick = function(e) { if (e.target === o) o.style.display = "none"; };
  o.innerHTML = "<div style=\"background:#fff;border-radius:16px;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.3);overflow:hidden;\">" +
    "<div style=\"padding:16px 20px;background:#4a6cf7;color:#fff;display:flex;justify-content:space-between;align-items:center;\">" +
      "<span style=\"font-weight:600;font-size:1rem;\">\ud83d\udcde \u8054\u7cfb\u5ba2\u670d</span>" +
      "<span id=\"csClose\" style=\"color:rgba(255,255,255,0.8);font-size:1.2rem;cursor:pointer;\">\u2715</span>" +
    "</div>" +
    "<div style=\"padding:16px 20px;\">" +
      "<div style=\"font-size:0.85rem;color:#555;margin-bottom:12px;line-height:1.8;\">" +
        "<strong>\ud83d\udce6 \u90ae\u7bb1\uff1a</strong>contact@bileizhinan.top<br>" +
        "<strong>\ud83d\udcf1 \u6296\u97f3\uff1a</strong>\u79c1\u4fe1 @\u4e09\u89d2\u6d32\u8dd1\u5200\u907f\u96f7\u6307\u5357<br>" +
        "<strong>\ud83d\udcfa B\u7ad9\uff1a</strong>\u79c1\u4fe1 @\u4e09\u89d2\u6d32\u8dd1\u5200\u6d4b\u8bc4" +
      "</div>" +
      "<div style=\"border-top:1px solid #eee;padding-top:12px;\">" +
        "<p style=\"font-size:0.8rem;color:#8a8aaa;margin-bottom:8px;\">\u6216\u8005\u76f4\u63a5\u7559\u8a00\uff1a</p>" +
        "<input id=\"csName\" placeholder=\"\u600e\u4e48\u79f0\u547c\u4f60\uff08\u9009\u586b\uff09\" style=\"width:100%;padding:8px 10px;border:1.5px solid #ddd;border-radius:8px;font-size:0.85rem;outline:none;margin-bottom:8px;box-sizing:border-box;\">" +
        "<input id=\"csContact\" placeholder=\"\u8054\u7cfb\u65b9\u5f0f\uff08\u9009\u586b\uff09\" style=\"width:100%;padding:8px 10px;border:1.5px solid #ddd;border-radius:8px;font-size:0.85rem;outline:none;margin-bottom:8px;box-sizing:border-box;\">" +
        "<textarea id=\"csMsg\" placeholder=\"\u6709\u4ec0\u4e48\u95ee\u9898\u6216\u5efa\u8bae\uff1f\" style=\"width:100%;padding:8px 10px;border:1.5px solid #ddd;border-radius:8px;font-size:0.85rem;outline:none;resize:none;min-height:70px;font-family:inherit;box-sizing:border-box;\"></textarea>" +
        "<button id=\"csSend\" style=\"margin-top:8px;width:100%;padding:9px;background:#4a6cf7;color:#fff;border:none;border-radius:8px;font-size:0.9rem;font-weight:600;cursor:pointer;\">\u2709\ufe0f \u53d1\u9001</button>" +
        "<div id=\"csSuc\" style=\"display:none;text-align:center;padding:20px;color:#27ae60;font-size:0.9rem;\">\u2705 \u5df2\u6536\u5230\u4f60\u7684\u6d88\u606f\uff01\u6211\u4eec\u4f1a\u5c3d\u5feb\u56de\u590d</div>" +
      "</div>" +
    "</div>" +
  "</div>";
  document.body.appendChild(o);
  document.getElementById("csClose").onclick = function() { o.style.display = "none"; };
  document.getElementById("csSend").onclick = function() {
    var name = document.getElementById("csName").value.trim();
    var contact = document.getElementById("csContact").value.trim();
    var msg = document.getElementById("csMsg").value.trim();
    if (!msg) { alert("\u8bf7\u586b\u5199\u5185\u5bb9"); return; }
    var btn = document.getElementById("csSend");
    btn.disabled = true; btn.textContent = "\u53d1\u9001\u4e2d...";
    var x = new XMLHttpRequest();
    x.open("POST", "/api/contact", true);
    x.setRequestHeader("Content-Type", "application/json");
    x.onload = function() {
      btn.disabled = false; btn.textContent = "\u2709\ufe0f \u53d1\u9001";
      if (x.status === 200) {
        document.getElementById("csName").style.display = "none";
        document.getElementById("csContact").style.display = "none";
        document.getElementById("csMsg").style.display = "none";
        document.getElementById("csSend").style.display = "none";
        document.getElementById("csSuc").style.display = "";
        var pp = document.getElementById("csMsg").parentElement.querySelector("p");
        if (pp) pp.style.display = "none";
      } else { alert("\u53d1\u9001\u5931\u8d25"); }
    };
    x.onerror = function() { btn.disabled = false; btn.textContent = "\u2709\ufe0f \u53d1\u9001"; alert("\u7f51\u7edc\u9519\u8bef"); };
    x.send(JSON.stringify({name:name, content:msg, contact:contact}));
  };
}

// === Init ===
(function() {
  var p = window.location.pathname;
  if (p === "/" || p === "/index.html") initHome();
  else if (p === "/list.html") initFullList();
})();
