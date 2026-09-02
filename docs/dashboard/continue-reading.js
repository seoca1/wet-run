/* dashboard/continue-reading.js — Personalized Continue Reading widget
 *
 * Reads from localStorage sprawl-reading-pos to display recently-read
 * stories with their saved scroll position. Used by index.html.
 */

(function () {
  "use strict";

  const POS_KEY = "sprawl-reading-pos";
  const STATS_KEY = "sprawl-stats-v1";
  const LIST_PATH = "data/search_index.json";

  let stories = null;
  let pos = {};
  let stats = {};

  function escHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function formatTimeAgo(ts) {
    if (!ts) return "—";
    const diff = Date.now() - ts;
    if (diff < 60000) return "just now";
    if (diff < 3600000) return Math.floor(diff / 60000) + "m ago";
    if (diff < 86400000) return Math.floor(diff / 3600000) + "h ago";
    if (diff < 604800000) return Math.floor(diff / 86400000) + "d ago";
    return new Date(ts).toLocaleDateString();
  }

  function load() {
    try { pos = JSON.parse(localStorage.getItem(POS_KEY) || "{}"); } catch (e) { pos = {}; }
    try { stats = JSON.parse(localStorage.getItem(STATS_KEY) || "{}"); } catch (e) { stats = {}; }
  }

  function render() {
    if (!stories) return;
    const list = document.getElementById("cr-list");
    const empty = document.getElementById("cr-empty");
    if (!list || !empty) return;

    // Sort by lastRead descending
    const items = stories
      .map(function (s) {
        const stat = (stats.page && stats.page.by_event && stats.page.by_event["page.view"]) || 0;
        const p = pos[s.url] || {};
        return Object.assign({}, s, {
          y: p.y || 0,
          pct: p.pct || 0,
          saved: p.saved || 0,
        });
      })
      .filter(function (s) { return s.saved > 0; })
      .sort(function (a, b) { return b.saved - a.saved; })
      .slice(0, 6);

    if (items.length === 0) {
      list.innerHTML = "";
      empty.style.display = "block";
      return;
    }
    empty.style.display = "none";

    list.innerHTML = items.map(function (s) {
      const lang = s.lang === "en" ? "EN" : "KO";
      const title = s.title || s.id;
      const stem = s.id;
      const last = formatTimeAgo(s.saved);
      const pctTxt = Math.round(s.pct || 0);
      return '<div class="cr-item" style="background:#06090f;border:1px solid #1a2530;border-radius:5px;padding:12px">' +
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">' +
          '<span style="font-size:10px;color:#ffaa55">[' + lang + '] ' + escHtml(stem) + '</span>' +
          '<span style="font-size:10px;color:#6a7888">' + last + '</span>' +
        '</div>' +
        '<div style="font-size:13px;color:#c5d4e3;margin-bottom:8px"><a href="' + escHtml(s.url) + '" style="color:#66ffcc;text-decoration:none">' + escHtml(title) + '</a></div>' +
        '<div style="display:flex;align-items:center;gap:8px">' +
          '<div style="flex:1;height:3px;background:#1a2530;border-radius:2px;overflow:hidden">' +
            '<div style="width:' + pctTxt + '%;height:100%;background:linear-gradient(90deg,#66ffcc,#88dd44)"></div>' +
          '</div>' +
          '<span style="font-size:10px;color:#88dd44;min-width:36px">' + pctTxt + '%</span>' +
        '</div>' +
        '<div style="margin-top:8px;font-size:11px"><a href="' + escHtml(s.url) + '?pct=' + pctTxt + '" style="color:#00ccff;text-decoration:none">↪ Resume from ' + pctTxt + '%</a></div>' +
      '</div>';
    }).join("");
  }

  function refresh() {
    load();
    render();
  }

  document.addEventListener("DOMContentLoaded", function () {
    load();
    fetch(LIST_PATH, { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        stories = d.stories || [];
        render();
      });

    // Refresh every 5s so changes from other tabs reflect
    setInterval(refresh, 5000);

    // Refresh on localStorage change from same tab
    window.addEventListener("storage", function (e) {
      if (e.key === POS_KEY || e.key === STATS_KEY) refresh();
    });
  });
})();
