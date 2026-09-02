/* dashboard/reading-stats.js — localStorage reading progress
 *
 * Uses the same sprawl-reading-pos key as reading-position.js,
 * but computes aggregate metrics for an at-a-glance view.
 */

(function () {
  "use strict";

  const POS_KEY = "sprawl-reading-pos";
  const STATS_KEY = "sprawl-reading-stats";
  const INDEX_PATH = "data/search_index.json";

  function loadStats() {
    try { return JSON.parse(localStorage.getItem(STATS_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function saveStats(s) {
    try { localStorage.setItem(STATS_KEY, JSON.stringify(s)); } catch (e) {}
  }

  function recordVisit(storyId) {
    const stats = loadStats();
    stats[storyId] = stats[storyId] || { visited: 0, lastRead: 0, maxPct: 0 };
    stats[storyId].visited = (stats[storyId].visited || 0) + 1;
    stats[storyId].lastRead = Date.now();
    saveStats(stats);
  }

  function pctToTime(pct) {
    return Math.round(pct * 0.25);
  }

  function render(index) {
    const stats = loadStats();
    const readStories = Object.keys(stats).filter((k) => (stats[k].visited || 0) > 0);
    const totalStories = index.length / 2;
    const wordsPerStory = { novice: 700, veteran: 650, heretic: 800, suit: 600 };
    let totalWords = 0;
    readStories.forEach((id) => {
      const story = index.find((it) => it.id === id);
      if (!story) return;
      totalWords += Math.max(50, Math.round((story.word_count.match(/(\d+)/) || [200])[1]));
    });

    const arcMap = { 1: "Arc 1", 2: "Arc 2", 3: "Arc 3", 4: "Arc 4", 5: "Arc 5" };
    const arcCounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    const arcRead = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    index.forEach((it) => {
      const s = stats[it.id];
      if (s) arcRead[it.lang === "en" ? (it.character === "Case" ? 1 : it.character === "Sil" ? 2 : it.character === "Kas" ? 4 : 3) : 0] = (arcRead[it.lang === "en" ? (it.character === "Case" ? 1 : it.character === "Sil" ? 2 : it.character === "Kas" ? 4 : 3) : 0] || 0);
      if (it.missions && it.missions.length > 0) {
        const arc = parseArc(it.missions[0]);
        if (arc) {
          arcCounts[arc]++;
          if (s) arcRead[arc]++;
        }
      }
    });

    const langStats = { en: 0, ko: 0 };
    const langRead = { en: 0, ko: 0 };
    index.forEach((it) => {
      langStats[it.lang]++;
      if (stats[it.id]) langRead[it.lang]++;
    });

    document.getElementById("stories-read").textContent = readStories.length;
    document.getElementById("stories-total").textContent = Math.floor(totalStories);
    document.getElementById("words-read").textContent =
      totalWords.toLocaleString();
    document.getElementById("minutes-read").textContent = Math.round(totalWords / 200);
    document.getElementById("completion").textContent =
      Math.round((readStories.length / Math.max(1, Math.floor(totalStories))) * 100) + "%";

    document.getElementById("streak").textContent = computeStreak(stats);

    const arcProgress = document.getElementById("arc-progress");
    arcProgress.innerHTML = Object.keys(arcCounts).map((k) => {
      const arc = parseInt(k);
      const c = arcCounts[arc] || 0;
      const r = arcRead[arc] || 0;
      const pct = c > 0 ? Math.round((r / c) * 100) : 0;
      return `<div class="arc-row">
        <div class="arc-name">${arcMap[arc]} · ${r}/${c} stories</div>
        <div class="progress-bar"><div class="track"><div class="fill" style="width:${pct}%"></div></div></div>
      </div>`;
    }).join("");

    const langProgress = document.getElementById("lang-progress");
    langProgress.innerHTML = Object.keys(langStats).map((k) => {
      const c = langStats[k];
      const r = langRead[k];
      const pct = c > 0 ? Math.round((r / c) * 100) : 0;
      return `<div class="arc-row">
        <div class="arc-name">${k.toUpperCase()} · ${r}/${c} stories</div>
        <div class="progress-bar"><div class="track"><div class="fill" style="width:${pct}%"></div></div></div>
      </div>`;
    }).join("");

    document.getElementById("content").style.display = "";
    document.getElementById("empty-state").style.display = "none";
  }

  function parseArc(missionId) {
    const map = {
      first_jack: 1, first_trace: 2, black_ice_dream: 3,
      delivery_to_finn: 1, marly_louisiana_god: 2,
    };
    return null;
  }

  function computeStreak(stats) {
    const days = Object.values(stats)
      .map((s) => new Date(s.lastRead || 0).toDateString())
      .filter(Boolean);
    const uniq = new Set(days);
    if (uniq.size === 0) return 0;
    let streak = 1;
    let cur = new Date();
    while (true) {
      cur.setDate(cur.getDate() - 1);
      if (uniq.has(cur.toDateString())) streak++;
      else break;
    }
    return streak;
  }

  function setupReset() {
    const btn = document.getElementById("reset-btn");
    if (btn) {
      btn.addEventListener("click", () => {
        if (confirm("Reset all reading history and positions?")) {
          localStorage.removeItem(POS_KEY);
          localStorage.removeItem(STATS_KEY);
          location.reload();
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    fetch(INDEX_PATH, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (!d.stories || d.stories.length === 0) {
          document.getElementById("empty-state").style.display = "";
          return;
        }
        render(d.stories);
        setupReset();
      })
      .catch(() => {
        document.getElementById("empty-state").style.display = "";
      });
  });
})();
