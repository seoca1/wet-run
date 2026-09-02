/* dashboard/reader-controls.js — Tier 4 polish utilities
 *
 * - per-card notes (localStorage)
 * - dyslexia-friendly and serif/sans toggles
 * - keyboard shortcuts (j/k navigation)
 */

(function () {
  "use strict";

  const NOTES_KEY = "sprawl-card-notes";
  const PREFS_KEY = "sprawl-reader-prefs";

  function escHtml(s) {
    return String(s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[c]);
  }

  function pageKey() {
    return location.pathname.replace(/\/$/, "");
  }

  function loadNotes() {
    try { return JSON.parse(localStorage.getItem(NOTES_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function saveNotes(n) {
    try { localStorage.setItem(NOTES_KEY, JSON.stringify(n)); } catch (e) {}
  }

  function loadPrefs() {
    try { return JSON.parse(localStorage.getItem(PREFS_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function savePrefs(p) {
    try { localStorage.setItem(PREFS_KEY, JSON.stringify(p)); } catch (e) {}
  }

  function applyPrefs(prefs) {
    const root = document.documentElement;
    if (prefs.font === "dyslexia") {
      root.style.fontFamily = '"Atkinson Hyperlegible", "Comic Sans MS", "OpenDyslexic", sans-serif';
      root.style.fontSize = "1.15rem";
      root.style.lineHeight = "2";
    } else if (prefs.font === "serif") {
      root.style.fontFamily = '"Crimson Pro", Georgia, serif';
    } else {
      root.style.fontFamily = "";
      root.style.fontSize = "";
      root.style.lineHeight = "";
    }
  }

  function buildNotesWidget() {
    const w = document.createElement("div");
    w.className = "notes-widget";
    w.innerHTML = `
      <button class="notes-toggle" title="My notes (n)">📝</button>
      <div class="notes-panel">
        <textarea placeholder="Notes for this card... (saved locally)"></textarea>
        <div class="notes-status"></div>
      </div>
    `;
    document.body.appendChild(w);

    const key = pageKey();
    const all = loadNotes();
    const ta = w.querySelector("textarea");
    const status = w.querySelector(".notes-status");
    ta.value = all[key] || "";

    let saveTimer;
    function save() {
      const v = ta.value;
      const cur = loadNotes();
      if (v.trim()) cur[key] = v;
      else delete cur[key];
      saveNotes(cur);
      status.textContent = "saved · " + new Date().toLocaleTimeString();
      setTimeout(() => status.textContent = "", 1200);
    }
    ta.addEventListener("input", () => {
      clearTimeout(saveTimer);
      saveTimer = setTimeout(save, 300);
    });

    w.querySelector(".notes-toggle").addEventListener("click", () => {
      w.classList.toggle("open");
    });
  }

  function buildPrefsPanel() {
    const toolbar = document.createElement("div");
    toolbar.className = "prefs-toolbar";
    toolbar.innerHTML = `
      <button data-font="default" title="Default serif font">Aa</button>
      <button data-font="dyslexia" title="Dyslexia-friendly font">A⌐</button>
    `;
    document.body.appendChild(toolbar);

    const prefs = loadPrefs();
    toolbar.querySelectorAll("button[data-font]").forEach((btn) => {
      btn.addEventListener("click", () => {
        prefs.font = btn.dataset.font;
        savePrefs(prefs);
        applyPrefs(prefs);
        if (window.SprawlStats) window.SprawlStats.increment("controls.font_change");
      });
    });
    applyPrefs(prefs);
  }

  function installKeyboardShortcuts() {
    document.addEventListener("keydown", (e) => {
      if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "j" || e.key === "ArrowRight" || e.key === " ") {
        scrollBy(0.8);
        e.preventDefault();
      } else if (e.key === "k" || e.key === "ArrowLeft") {
        scrollBy(-0.8);
        e.preventDefault();
      } else if (e.key === "n") {
        const widget = document.querySelector(".notes-widget");
        if (widget) widget.classList.toggle("open");
        e.preventDefault();
      } else if (e.key === "?") {
        showHelp();
        e.preventDefault();
      }
    });
  }

  function scrollBy(frac) {
    const max = document.body.scrollHeight - window.innerHeight;
    window.scrollTo({ top: Math.max(0, Math.min(max, window.scrollY + max * frac)), behavior: "smooth" });
  }

  function showHelp() {
    const panel = document.createElement("div");
    panel.className = "help-panel";
    panel.innerHTML = `
      <button class="close">×</button>
      <h3>Keyboard Shortcuts</h3>
      <ul style="list-style:none;line-height:2">
        <li><kbd>j</kbd> / <kbd>→</kbd> / <kbd>space</kbd> — scroll down 80%</li>
        <li><kbd>k</kbd> / <kbd>←</kbd> — scroll up 80%</li>
        <li><kbd>n</kbd> — toggle notes panel</li>
        <li><kbd>?</kbd> — show this help</li>
      </ul>
      <p style="margin-top:8px;font-size:11px;color:#6a7888">Reading position auto-saves. Use buttons in the toolbar to switch font.</p>
    `;
    document.body.appendChild(panel);
    panel.querySelector(".close").addEventListener("click", () => panel.remove());
    setTimeout(() => panel.addEventListener("click", (e) => {
      if (e.target === panel) panel.remove();
    }), 0);
  }

  document.addEventListener("DOMContentLoaded", () => {
    buildNotesWidget();
    buildPrefsPanel();
    installKeyboardShortcuts();
  });
})();
