/* dashboard/glossary.js — Gibson Sprawl glossary hover/click integration
 *
 * Auto-detects wiki terms in card body text and wraps them with a <a>
 * that opens the corresponding Fiction wiki page in a new tab.
 *
 * Companion CSS: dashboard/glossary.css
 * Glossary dictionary: dashboard/glossary.json
 *
 * Designed to be loaded by every story card. No jQuery, no build step.
 */

(function () {
  "use strict";

  const DIC_PATH = (window.GLOSSARY_DICT_PATH || "glossary.json");
  const WIKI_BASE = (window.GLOSSARY_WIKI_BASE ||
    "../../../Fiction/wiki/");

  function escapeReg(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function loadDictionary() {
    return fetch(DIC_PATH, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : {}))
      .catch(() => ({}));
  }

  function walkTextNodes(root, fn) {
    const SKIP = new Set(["SCRIPT", "STYLE", "A", "CODE", "PRE"]);
    function visit(node) {
      if (!node) return;
      if (SKIP.has(node.nodeName)) return;
      if (node.nodeType === Node.TEXT_NODE) {
        fn(node);
        return;
      }
      const children = node.childNodes;
      for (let i = 0; i < children.length; i++) {
        visit(children[i]);
      }
    }
    visit(root);
  }

  function applyTerms(dictionary) {
    if (!dictionary || !dictionary.terms || dictionary.terms.length === 0) return 0;
    const sorted = [...dictionary.terms].sort((a, b) => b.length - a.length);
    const pattern = new RegExp(
      "\\b(" + sorted.map((t) => escapeReg(t)).join("|") + ")\\b",
      "g"
    );
    let replacements = 0;

    function processArticle(article) {
      const replacementsByTextNode = new Map();
      walkTextNodes(article, (textNode) => {
        const original = textNode.nodeValue;
        if (!original || original.length < 3) return;
        if (!pattern.test(original)) return;
        pattern.lastIndex = 0;
        const segments = [];
        let last = 0;
        let m;
        while ((m = pattern.exec(original)) !== null) {
          const matched = m[1];
          const dict = dictionary.map[matched.toLowerCase()];
          if (!dict) continue;
          if (m.index > last) {
            segments.push({ text: original.slice(last, m.index), link: null });
          }
          segments.push({ text: matched, link: dict });
          last = m.index + matched.length;
        }
        if (segments.length === 0) return;
        if (last < original.length) {
          segments.push({ text: original.slice(last), link: null });
        }
        replacementsByTextNode.set(textNode, segments);
      });

      replacementsByTextNode.forEach((segments, textNode) => {
        const fragment = document.createDocumentFragment();
        segments.forEach((seg) => {
          if (!seg.link) {
            fragment.appendChild(document.createTextNode(seg.text));
            return;
          }
          const a = document.createElement("a");
          a.className = "glossary-term";
          a.href = WIKI_BASE + seg.link.page + (seg.link.anchor ? "#" + seg.link.anchor : "");
          a.target = "_blank";
          a.rel = "noopener";
          a.title = seg.link.title || seg.link.text || seg.text;
          const tooltip = seg.link.tooltip || "";
          if (tooltip) {
            a.dataset.tooltip = tooltip;
          }
          a.textContent = seg.text;
          fragment.appendChild(a);
        });
        textNode.replaceWith(fragment);
        replacements++;
      });
    }

    const articles = document.querySelectorAll("article.story-body, .story-body, article");
    articles.forEach(processArticle);
    return replacements;
  }

  function showTooltip(target) {
  if (window.SprawlStats) window.SprawlStats.increment("glossary.hover");
    const tt = document.querySelector("#glossary-tooltip");
    if (!tt) return;
    const tip = target.dataset.tooltip || target.title || target.textContent;
    if (!tip) return;
    tt.textContent = tip;
    const rect = target.getBoundingClientRect();
    const top = rect.bottom + window.scrollY + 8;
    const left = rect.left + window.scrollX;
    tt.style.top = top + "px";
    tt.style.left = left + "px";
    tt.style.display = "block";
  }

  function hideTooltip() {
    const tt = document.querySelector("#glossary-tooltip");
    if (tt) tt.style.display = "none";
  }

  function installTooltip() {
    if (document.querySelector("#glossary-tooltip")) return;
    const tt = document.createElement("div");
    tt.id = "glossary-tooltip";
    tt.className = "glossary-tooltip";
    document.body.appendChild(tt);
    document.addEventListener("mousemove", (e) => {
      const t = e.target.closest(".glossary-term");
      if (!t) return;
      const rect = t.getBoundingClientRect();
      tt.style.top = rect.bottom + window.scrollY + 8 + "px";
      tt.style.left = Math.min(rect.left + window.scrollX, window.innerWidth - 360) + "px";
    });
    document.addEventListener("mouseover", (e) => {
      const t = e.target.closest(".glossary-term");
      if (t) showTooltip(t);
    });
    document.addEventListener("mouseout", (e) => {
      const t = e.target.closest(".glossary-term");
      if (t) hideTooltip();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    installTooltip();
    loadDictionary().then(applyTerms);
  });
})();
