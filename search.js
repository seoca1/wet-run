/* dashboard/search.js — client-side full-text search over the search index. */

(function () {
  "use strict";

  const INDEX_PATH = (window.SEARCH_INDEX_PATH || "data/search_index.json");

  let index = [];
  let activeFilter = "all";

  function escReg(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function escHtml(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[c]);
  }

  function highlight(text, query) {
    if (!query) return escHtml(text);
    const pattern = new RegExp("(" + escReg(query) + ")", "gi");
    return escHtml(text).replace(pattern, "<mark>$1</mark>");
  }

  function matches(item, query) {
    if (!query) return true;
    const q = query.toLowerCase();
    const fields = [
      item.title || "",
      item.subtitle || "",
      item.character || "",
      item.id || "",
      item.body_preview || "",
      (item.missions || []).join(" "),
    ];
    return fields.some((f) => f.toLowerCase().includes(q));
  }

  function derivePreview(item, query) {
    if (!query) return item.body_preview || "";
    const text = item.body_preview || "";
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx < 0) return text.substring(0, 200);
    const start = Math.max(0, idx - 50);
    const end = Math.min(text.length, idx + 150);
    return (start > 0 ? "..." : "") + text.substring(start, end) + (end < text.length ? "..." : "");
  }

  function renderResults() {
    const query = (document.getElementById("search-input").value || "").trim();
    const container = document.getElementById("results");
    const meta = document.getElementById("results-meta");

    let filtered = index.filter((it) => (activeFilter === "all" || it.lang === activeFilter));
    filtered = filtered.filter((it) => matches(it, query));
    filtered = filtered.slice(0, 60);

    meta.textContent = `${filtered.length} result(s)`;
    if (filtered.length === 0) {
      container.innerHTML = '<div class="empty">No results. Try a different query.</div>';
      return;
    }

    container.innerHTML = filtered
      .map((it) => {
        const titleHl = highlight(it.title, query);
        const preview = highlight(derivePreview(it, query), query);
        const langBadge = `<span style="background:${it.lang === "en" ? "#ffaa5522" : "#00ccff22"};padding:1px 6px;border-radius:2px;color:${it.lang === "en" ? "#ffaa55" : "#00ccff"}">${it.lang.toUpperCase()}</span>`;
        const chars = it.character ? `<span>${escHtml(it.character)}</span>` : "";
        const missions = (it.missions || [])
          .map((m) => `<span>${escHtml(m)}</span>`)
          .join("");
        return `
          <div class="result-card">
            <div class="title"><a href="${escHtml(it.url)}">${titleHl}</a> ${langBadge}</div>
            <div class="subtitle">${escHtml(it.subtitle || "")}</div>
            <div class="meta">${chars}${missions}<span>${escHtml(it.id)}</span></div>
            <div class="preview">${preview}</div>
          </div>
        `;
      })
      .join("");
  }

  function attachUI() {
    const input = document.getElementById("search-input");
    input.addEventListener("input", renderResults);
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeFilter = btn.dataset.filter;
        renderResults();
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    fetch(INDEX_PATH, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        index = d.stories || [];
        attachUI();
        renderResults();
      });
  });
})();
