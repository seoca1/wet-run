/* dashboard/reading-position.js — localStorage scroll position
 *
 * Saves and restores vertical scroll position per card.
 * Survives navigation between EN and KO versions of the same story.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "sprawl-reading-pos";
  const RESUME_BUTTON_ID = "resume-reading-link";

  function pageKey() {
    return location.pathname.replace(/\/$/, "");
  }

  function capture() {
    const data = readAll();
    const pct = Math.round((window.scrollY / Math.max(1, document.body.scrollHeight - window.innerHeight)) * 1000) / 10;
    data[pageKey()] = {
      y: window.scrollY,
      pct: pct,
      saved: Date.now(),
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {}
  }

  function readAll() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch (e) {
      return {};
    }
  }

  function showResumeButton(savedY) {
    if (savedY < 50) return;
    let btn = document.getElementById(RESUME_BUTTON_ID);
    if (!btn) {
      btn = document.createElement("button");
      btn.id = RESUME_BUTTON_ID;
      btn.className = "resume-reading-btn";
      btn.textContent = "Resume reading from " + Math.round(savedY / 100) * 100 + "px";
        if (window.SprawlStats) window.SprawlStats.increment("reading.resume");
      btn.addEventListener("click", () => {
        const saved = readAll()[pageKey()];
        if (saved) {
          window.scrollTo({ top: saved.y, behavior: "smooth" });
          btn.style.display = "none";
        }
      });
      document.body.appendChild(btn);
    } else {
      btn.style.display = "block";
    }
  }

  function restore() {
    const data = readAll();
    const saved = data[pageKey()];
    if (!saved || !saved.y || saved.y < 50) return;
    setTimeout(() => showResumeButton(saved.y), 100);
  }

  document.addEventListener("DOMContentLoaded", () => {
    restore();
    let lastCapture = 0;
    const throttled = function () {
      const now = Date.now();
      if (now - lastCapture < 500) return;
      lastCapture = now;
      capture();
    };
    window.addEventListener("scroll", throttled, { passive: true });
    window.addEventListener("beforeunload", capture);
  });
})();
