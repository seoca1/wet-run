/* dashboard/sync-scroll.js — paired-reading EN/KO sync helper.
 *
 * When a card is opened with ?align_to=EN and a `pct` parameter,
 * the page loads, waits for layout, then scrolls to the same % of the
 * paired article. Also exposes a small floating toggle button so the
 * reader can switch languages at the same point in the text.
 */

(function () {
  "use strict";

  function pctFromScroll() {
    const max = Math.max(1, document.body.scrollHeight - window.innerHeight);
    return Math.min(100, Math.max(0, (window.scrollY / max) * 100));
  }

  function scrollToPct(pct) {
    const max = Math.max(1, document.body.scrollHeight - window.innerHeight);
    window.scrollTo({ top: (max * pct) / 100, behavior: "instant" });
  }

  function buildViewer() {
    const params = new URLSearchParams(location.search);
    if (params.get("viewer") !== "paired") return;

    const enPath = params.get("en");
    const koPath = params.get("ko");
    if (!enPath || !koPath) return;

    const wrap = document.createElement("div");
    wrap.className = "paired-viewer";

    const iframe = (path, label) => {
      const url = new URL(path, location.href);
      return `<div class="paired-pane">
        <div class="paired-label">${label}</div>
        <iframe src="${url.href}" loading="lazy"></iframe>
      </div>`;
    };
    wrap.innerHTML = iframe(enPath, "EN") + iframe(koPath, "KO");
    document.body.replaceWith(wrap);
  }

  function buildSwitcher() {
    const currentPath = location.pathname.replace(/\/$/, "");
    const altMatch = currentPath.match(/^(.*?)\/(2026-\d{2}-\d{2}_[a-z0-9_-]+?)_(en|ko)\.html$/);
    if (!altMatch) return;
    const [, prefix, stem, cur] = altMatch;
    const other = cur === "en" ? "ko" : "en";
    const altPath = `${prefix}/${stem}_${other}.html`;

    const link = document.createElement("a");
    link.href = altPath + "?pct=" + encodeURIComponent(pctFromScroll().toFixed(1));
    link.className = "lang-switcher";
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent =
      cur === "en" ? "→ KO (현재 % 위치 유지)" : "→ EN (keep current %)";

    const existing = document.querySelector(".lang-switcher");
    if (existing) existing.remove();
    document.body.appendChild(link);
  }

  function applyAlignedScroll() {
    const params = new URLSearchParams(location.search);
    const pct = parseFloat(params.get("pct"));
    if (!isFinite(pct) || pct < 0 || pct > 100) return;
    setTimeout(() => scrollToPct(pct), 50);
  }

  document.addEventListener("DOMContentLoaded", () => {
    buildViewer();
    applyAlignedScroll();
    buildSwitcher();
  });
})();
