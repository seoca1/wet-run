/* dashboard/stories-browse.js — Data-driven story browser
 *
 * Loads all 78 stories from data/search_index.json, applies
 * character / language / read-state filters and a quick text filter.
 * Tracks read state by listening to the existing localStorage key
 * `sprawl-reading-pos` from reading-position.js.
 */

(function () {
  "use strict";

  const INDEX_PATH = "data/search_index.json";

  const filters = {
    trilogy: "all",
    char: "all",
    lang: "all",
    state: "all",
    gibson: "all",
    literary: "all",
    advanced: "all",
    text: "",
  };

  const POS_KEY = "sprawl-reading-pos";

  function readReadState() {
    try { return JSON.parse(localStorage.getItem(POS_KEY) || "{}"); }
    catch (e) { return {}; }
  }

  function fmtDate(stem) {
    const m = stem.match(/^(\d{4}-\d{2}-\d{2})_/);
    return m ? m[1] : "—";
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

  function highlight(s, query) {
    if (!query) return escHtml(s);
    const safe = escHtml(s);
    const parts = safe.split(new RegExp("(" + query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"));
    return parts.map((p, i) => i % 2 === 1
      ? `<mark style="background:#66ffcc44;color:#fff">${p}</mark>`
      : p).join("");
  }

  function storyHasText(story, query) {
    if (!query) return true;
    const q = query.toLowerCase();
    return [
      story.title || "",
      story.subtitle || "",
      story.character || "",
      story.id || "",
      story.body_preview || "",
      (story.missions || []).join(" "),
    ].some((f) => f.toLowerCase().includes(q));
  }

  function render(stories) {
    const readState = readReadState();

    const filtered = stories.filter((s) => {
      if (filters.trilogy !== "all") {
        const t = s.trilogy || "sprawl";
        if (t !== filters.trilogy) return false;
      }
      if (filters.char !== "all") {
        const char = (s.character || "").split(" ")[0];
        if (char !== filters.char) return false;
      }
      if (filters.lang !== "all" && s.lang !== filters.lang) return false;
      if (filters.state !== "all") {
        const isRead = readState[s.url] && readState[s.url].y > 50;
        if (filters.state === "read" && !isRead) return false;
        if (filters.state === "unread" && isRead) return false;
      }
      if (filters.gibson !== "all") {
        const gibsonOverall = (s.gibson_style || {}).overall || "partial";
        if (gibsonOverall !== filters.gibson) return false;
      }
      if (filters.literary !== "all") {
        const litGrade = (s.literary || {}).grade || "unknown";
        if (litGrade !== filters.literary) return false;
      }
      if (filters.advanced !== "all") {
        const advGrade = (s.advanced_literary || {}).grade || "unknown";
        if (advGrade !== filters.advanced) return false;
      }
      if (!storyHasText(s, filters.text)) return false;
      return true;
    });

    const meta = document.getElementById("meta");
    const totalRead = stories.filter((s) =>
      readState[s.url] && readState[s.url].y > 50
    ).length;
    const totalGibsonPass = stories.filter((s) => (s.gibson_style || {}).overall === "pass").length;
    const totalGibsonPartial = stories.filter((s) => (s.gibson_style || {}).overall === "partial").length;
    const totalGibsonFail = stories.filter((s) => (s.gibson_style || {}).overall === "fail").length;
    const totalLiterary = stories.filter((s) => (s.literary || {}).grade).length;
    const totalAdvanced = stories.filter((s) => (s.advanced_literary || {}).grade).length;
    meta.innerHTML = `
      <span>Total: <strong style="color:#66ffcc">${stories.length}</strong></span>
      <span>Filtered: <strong style="color:#ffaa55">${filtered.length}</strong></span>
      <span>Read: <strong style="color:#88dd44">${totalRead}</strong></span>
      <span>Gibson: <strong style="color:#88dd44">${totalGibsonPass}</strong> / <strong style="color:#ffaa55">${totalGibsonPartial}</strong> / <strong style="color:#ff4444">${totalGibsonFail}</strong></span>
      <span>Literary (S5): <strong style="color:#88dd44">${totalLiterary}</strong> scored</span>
      <span>Advanced (S6): <strong style="color:#88dd44">${totalAdvanced}</strong> scored</span>
    `;

    const grid = document.getElementById("grid");
    grid.innerHTML = filtered.map((s) => {
      const isRead = readState[s.url] && readState[s.url].y > 50;
      const pct = isRead
        ? Math.min(100, Math.round((readState[s.url].y / Math.max(1, document.body.scrollHeight)) * 100))
        : 0;
      const langBadge = s.lang === "en" ? "EN" : "KO";
      const trilogyBadge = s.trilogy || "sprawl";
      const trilogyColors = { sprawl: "#ff8844", bridge: "#88dd44", "blue-ant": "#66ffcc" };
      const trilogyColor = trilogyColors[trilogyBadge] || "#66ffcc";
      
      
      const gibson = s.gibson_style;
      const gibsonColors = { pass: "#88dd44", partial: "#ffaa55", fail: "#ff4444" };
      const gibsonBadge = gibson
        ? `<span style="background:${gibsonColors[gibson.overall]}22;border:1px solid ${gibsonColors[gibson.overall]};color:${gibsonColors[gibson.overall]};padding:1px 5px;border-radius:2px;font-size:9px;text-transform:uppercase;">${gibson.overall} (${gibson.passed}/${gibson.passed + gibson.partial + gibson.failed})</span>`
        : "";

      const lit = s.literary;
      const adv = s.advanced_literary;
      const gradeColors = { S: "#ff44ff", A: "#66ffcc", B: "#88dd44", C: "#ffaa55", D: "#ff4444" };
      const litBadge = lit && lit.grade
        ? `<span style="background:${gradeColors[lit.grade] || '#666'}22;border:1px solid ${gradeColors[lit.grade] || '#666'};color:${gradeColors[lit.grade] || '#666'};padding:1px 5px;border-radius:2px;font-size:9px;">S5:${lit.grade}</span>`
        : "";
      const advBadge = adv && adv.grade
        ? `<span style="background:${gradeColors[adv.grade] || '#666'}22;border:1px solid ${gradeColors[adv.grade] || '#666'};color:${gradeColors[adv.grade] || '#666'};padding:1px 5px;border-radius:2px;font-size:9px;">S6:${adv.grade}</span>`
        : "";
      
      return `<div class="story-card ${isRead ? "read" : ""}">
        ${isRead ? '<span class="read-badge">✓ READ</span>' : ""}
        <div class="lang" style="display:flex;justify-content:space-between;align-items:center;">
          <span>[${langBadge}] ${fmtDate(s.id)}</span>
          <span style="display:flex;gap:4px;">
            <span style="background:${trilogyColor}22;border:1px solid ${trilogyColor};color:${trilogyColor};padding:1px 5px;border-radius:2px;font-size:9px;text-transform:uppercase;">${trilogyBadge}</span>
            ${litBadge}
            ${advBadge}
            ${gibsonBadge}
          </span>
        </div>
        <div class="title"><a href="${escHtml(s.url)}">${highlight(s.title || s.id, filters.text)}</a></div>
        <div class="meta">${highlight(s.character || "—", filters.text)} · ${escHtml(s.word_count || "")}</div>
        <div class="meta">${highlight(s.id, filters.text)}</div>
        ${(s.missions || []).length
          ? `<div class="missions">${(s.missions || []).map((m) =>
              `<span class="mission-pill">${escHtml(m)}</span>`).join("")}</div>`
          : ""}
        ${isRead ? `<div class="progress"><div class="progress-fill" style="width:${pct}%"></div></div>` : ""}
      </div>`;
    }).join("");
  }

  function attachUI() {
    document.querySelectorAll("[data-trilogy]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.trilogy = btn.dataset.trilogy;
        document.querySelectorAll("[data-trilogy]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        rerender();
      });
    });
    document.querySelectorAll("[data-char]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.char = btn.dataset.char;
        document.querySelectorAll("[data-char]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        rerender();
      });
    });
    document.querySelectorAll("[data-lang]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.lang = btn.dataset.lang;
        document.querySelectorAll("[data-lang]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        rerender();
      });
    });
    document.querySelectorAll("[data-state]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.state = btn.dataset.state;
        document.querySelectorAll("[data-state]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        rerender();
      });
    });
    document.querySelectorAll("[data-gibson]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.gibson = btn.dataset.gibson;
        document.querySelectorAll("[data-gibson]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        rerender();
      });
    });
    document.querySelectorAll("[data-literary]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.literary = btn.dataset.literary;
        document.querySelectorAll("[data-literary]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        rerender();
      });
    });
    document.querySelectorAll("[data-advanced]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filters.advanced = btn.dataset.advanced;
        document.querySelectorAll("[data-advanced]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        rerender();
      });
    });
    document.getElementById("search-input").addEventListener("input", (e) => {
      filters.text = e.target.value.trim();
      rerender();
    });
  }

  let storiesData = null;

  function rerender() {
    if (storiesData) render(storiesData);
  }

  document.addEventListener("DOMContentLoaded", () => {
    fetch(INDEX_PATH, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        storiesData = (d.stories || []).slice().sort((a, b) => {
          if (a.lang !== b.lang) return a.lang < b.lang ? -1 : 1;
          return (a.id || "").localeCompare(b.id || "");
        });
        attachUI();
        // Apply ?lang=ko or ?lang=en URL query param pre-filter
        const params = new URLSearchParams(window.location.search);
        const urlLang = params.get("lang");
        if (urlLang === "ko" || urlLang === "en") {
          filters.lang = urlLang;
          document.querySelectorAll("[data-lang]").forEach((b) => {
            b.classList.toggle("active", b.dataset.lang === urlLang);
          });
        }
        render(storiesData);
      });
  });
})();
