/* dashboard/mission-flow.js — Mission grids by character_ref and arc */

(function () {
  "use strict";

  const MISSIONS_PATH = "data/mission_links.json";
  const SEARCH_PATH = "data/search_index.json";
  const CONTAINER = document.getElementById("flow");

  let activeFilter = "all";
  let activeCast = "all";

  function escHtml(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[c]);
  }

  function gradeFill(min, max) {
    const w = Math.min(100, ((min + max) / 10) * 50);
    return `<div class="grade-fill" style="width:${w}%"></div>`;
  }

  function render(missionsBySource, allStories) {
    const storyByKey = new Map();
    (allStories || []).forEach((it) => {
      const key = it.id.replace(/_en$/, "").replace(/_ko$/, "");
      if (!storyByKey.has(key)) {
        storyByKey.set(key, it);
      }
    });

    const allMissions = [];
    Object.entries(missionsBySource).forEach(([src, ms]) => {
      ms.forEach((m) => {
        allMissions.push({ ...m, source: src });
      });
    });

    allMissions.sort((a, b) => {
      const aArc = a.arc || 0;
      const bArc = b.arc || 0;
      if (aArc !== bArc) return aArc - bArc;
      const aGrade = a.grade_min || 0;
      const bGrade = b.grade_min || 0;
      if (aGrade !== bGrade) return aGrade - bGrade;
      return a.id.localeCompare(b.id);
    });

    const grouped = {};
    allMissions.forEach((m) => {
      const k = m.character_ref || "unknown";
      if (activeFilter !== "all" && activeFilter !== k) return;
      if (activeCast !== "all" && m.cast !== activeCast) return;
      grouped[k] = grouped[k] || [];
      grouped[k].push(m);
    });

    const charNames = {
      novice: "Case — Novice Cowboy",
      veteran: "Sil — Veteran Runner",
      heretic: "Kas — Heretic Console Cowboy",
      suit: "Suit — Suit Player",
    };

    const order = ["novice", "veteran", "heretic", "suit"];
    CONTAINER.innerHTML = order
      .filter((k) => grouped[k])
      .map((k) => {
        const ms = grouped[k];
        const cards = ms.map((m) => {
          const story = storyByKey.get(m.source);
          const storyLink = story
            ? `<a class="story-link" href="stories/short-stories/${m.source}_en.html">→ ${escHtml(story.title || m.source)}</a>`
            : `<a class="story-link" href="library.html">→ library</a>`;
          const cast = m.cast || "";
        return `<div class="mission-card">
            <div class="id">${escHtml(m.id)}</div>
            <div class="title">${escHtml(m.title || m.id)}</div>
            <div class="meta">
              <span class="arc-pill">arc ${m.arc || "?"}</span>
              <span class="cast-pill">cast ${escHtml(cast) || "?"}</span>
              <span>${m.fixer || "?"}</span>
            </div>
            <span class="arc-pill">arc ${m.arc || "?"}</span>
            <span class="pillar-pill">${m.pillar || "?"}</span>
            <div class="grade-bar">${gradeFill(m.grade_min || 0, m.grade_max || 0)}</div>
            <div class="meta" style="margin-top:6px">grade ${m.grade_min || "?"}–${m.grade_max || "?"}</div>
            ${storyLink}
          </div>`;
        }).join("");

        const arcBuckets = {};
        ms.forEach((m) => {
          arcBuckets[m.arc] = arcBuckets[m.arc] || [];
          arcBuckets[m.arc].push(m);
        });
        const arcSections = Object.keys(arcBuckets)
          .sort((a, b) => Number(a) - Number(b))
          .map((arc) => `<h3 style="color:#66ffcc;font-size:12px;margin:14px 0 6px">Arc ${arc} (${arcBuckets[arc].length} missions)</h3>
          <div class="mission-grid">${arcBuckets[arc].map((m) => {
            const story = storyByKey.get(m.source);
            const storyLink = story
              ? `<a class="story-link" href="stories/short-stories/${m.source}_en.html">→ ${escHtml(story.title || m.source)}</a>`
              : `<span class="story-link">→ (no source)</span>`;
            return `<div class="mission-card">
              <div class="id">${escHtml(m.id)}</div>
              <div class="title">${escHtml(m.title || m.id)}</div>
              <span class="arc-pill">${m.pillar || "?"}</span>
              <div class="grade-bar">${gradeFill(m.grade_min || 0, m.grade_max || 0)}</div>
              <div class="meta" style="margin-top:6px">grade ${m.grade_min || "?"}–${m.grade_max || "?"}</div>
              ${storyLink}
            </div>`;
          }).join("")}</div>`).join("");

        return `<div class="character-section character-${k}">
          <div class="character-header">${charNames[k] || k} · ${ms.length} missions</div>
          ${arcSections}
        </div>`;
      })
      .join("");
  }

  
function applyFilter(filter) {
  document.querySelectorAll("[data-filter]").forEach(function (b) {
    b.classList.remove("active");
    if (b.dataset.filter === filter) b.classList.add("active");
  });
  activeFilter = filter;
  Promise.all([
    fetch(MISSIONS_PATH, { cache: "no-store" }).then(function (r) { return r.json(); }),
    fetch(SEARCH_PATH, { cache: "no-store" }).then(function (r) { return r.json(); })
  ]).then(function (m, s) { render(m[0].by_source, s[0].stories); });
}

function applyCast(cast) {
  document.querySelectorAll("[data-cast]").forEach(function (b) {
    b.classList.remove("active");
    if (b.dataset.cast === cast) b.classList.add("active");
  });
  activeCast = cast;
  Promise.all([
    fetch(MISSIONS_PATH, { cache: "no-store" }).then(function (r) { return r.json(); }),
    fetch(SEARCH_PATH, { cache: "no-store" }).then(function (r) { return r.json(); })
  ]).then(function (m, s) { render(m[0].by_source, s[0].stories); });
}

function attachUI() {
    document.querySelectorAll("[data-filter]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("[data-filter]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeFilter = btn.dataset.filter;
        Promise.all([
          fetch(MISSIONS_PATH, { cache: "no-store" }).then((r) => r.json()),
          fetch(SEARCH_PATH, { cache: "no-store" }).then((r) => r.json()),
        ]).then(([m, s]) => render(m.by_source, s.stories));
      });
    });
    document.querySelectorAll("[data-cast]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("[data-cast]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeCast = btn.dataset.cast;
        Promise.all([
          fetch(MISSIONS_PATH, { cache: "no-store" }).then((r) => r.json()),
          fetch(SEARCH_PATH, { cache: "no-store" }).then((r) => r.json()),
        ]).then(([m, s]) => render(m.by_source, s.stories));
      });
    });
  }

  Promise.all([
    fetch(MISSIONS_PATH, { cache: "no-store" }).then((r) => r.json()),
    fetch(SEARCH_PATH, { cache: "no-store" }).then((r) => r.json()),
  ])
    .then(([m, s]) => {
      var urlFilter = new URLSearchParams(location.search).get("filter");
      if (urlFilter) {
        var fb = document.querySelector('[data-filter="' + urlFilter + '"]');
        if (fb) {
          activeFilter = urlFilter;
          document.querySelectorAll("[data-filter]").forEach(function (b) { b.classList.remove("active"); });
          fb.classList.add("active");
        }
      }
      var urlCast = new URLSearchParams(location.search).get("cast");
      if (urlCast) {
        var cb = document.querySelector('[data-cast="' + urlCast + '"]');
        if (cb) {
          activeCast = urlCast;
          document.querySelectorAll("[data-cast]").forEach(function (b) { b.classList.remove("active"); });
          cb.classList.add("active");
        }
      }
      render(m.by_source, s.stories);
      attachUI();
    });
})();
