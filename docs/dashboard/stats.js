/* dashboard/stats.js — lightweight localStorage stat tracking
 *
 * SprawlStats.increment(event) is callable from any dashboard module.
 * Example:
 *     if (window.SprawlStats) window.SprawlStats.increment("glossary.hover");
 *
 * The /reading-stats.html page reads sprawl-stats.json keys to show
 * anonymized per-event counts in an optional debug panel.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "sprawl-stats-v1";
  const MAX_EVENT_KEYS = 256;

  function load() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function save(s) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); } catch (e) {}
  }

  function increment(event) {
    if (!event || typeof event !== "string") return;
    const bucket = (event.split(".")[0] || "other");
    const all = load();
    all[bucket] = all[bucket] || { total: 0, by_event: {}, firstSeen: Date.now() };
    all[bucket].total = (all[bucket].total || 0) + 1;
    all[bucket].by_event[event] = (all[bucket].by_event[event] || 0) + 1;
    all[bucket].lastSeen = Date.now();
    const totalKeys =
      Object.keys(all).reduce(
        (n, k) => n + Object.keys((all[k] || {}).by_event || {}).length,
        0
      );
    if (totalKeys > MAX_EVENT_KEYS) {
      all[bucket].by_event = trimOldest(all[bucket].by_event, MAX_EVENT_KEYS);
    }
    save(all);
  }

  function trimOldest(map, cap) {
    const entries = Object.entries(map)
      .sort((a, b) => (b[1] || 0) - (a[1] || 0));
    const keep = entries.slice(0, cap);
    return Object.fromEntries(keep);
  }

  function reset() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
  }

  function snapshot() {
    return load();
  }

  window.SprawlStats = { increment, reset, snapshot };

  document.addEventListener("DOMContentLoaded", () => {
    window.__SPRAWL_PAGE_PATH__ = location.pathname.replace(/\/$/, "");
    increment("page.view");
  });
})();
