/**
 * Tier 5 — Web Expansion
 * Status state machine, Volume slider, SFX expansion, Save compression
 * Pure ES module, no build step required.
 */

(function(global) {
  'use strict';

  /* =====================================================================
     LZ-string — minimal implementation for save compression
     ===================================================================== */
  const LZString = (function() {
    const f = String.fromCharCode;
    const keyStrBase64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    const keyStrUriSafe = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-$';

    function _compress(uncompressed) {
      if (!uncompressed) return '';
      const dict = {}, c = {}, data = uncompressed.split('');
      let dictSize = 256, res = [], w = '', wc;
      for (let i = 0; i < data.length; i++) {
        c = data[i];
        wc = w + c;
        if (Object.prototype.hasOwnProperty.call(dict, wc)) w = wc;
        else {
          res.push(w.charCodeAt(0) < 256 ? w.charCodeAt(0) : dict[w]);
          dict[wc] = dictSize++;
          w = c;
        }
      }
      if (w) res.push(w.charCodeAt(0) < 256 ? w.charCodeAt(0) : dict[w]);
      return _encodeToBase64(res);
    }

    function _decompress(compressed) {
      if (!compressed) return '';
      const data = _decodeFromBase64(compressed);
      const dict = {}, w = f(data[0]), res = [w];
      let dictSize = 256, entry;
      for (let i = 1; i < data.length; i++) {
        const k = data[i];
        if (Object.prototype.hasOwnProperty.call(dict, k)) entry = dict[k];
        else if (k === dictSize) entry = w + w[0];
        else return null;
        res.push(entry);
        dict[dictSize++] = w + entry[0];
        w = entry;
      }
      return res.join('');
    }

    function _encodeToBase64(input) {
      let output = '', chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0;
      while (i < input.length) {
        chr1 = input[i++];
        chr2 = input[i++];
        chr3 = input[i++];
        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;
        if (isNaN(chr2)) enc3 = enc4 = 64;
        else if (isNaN(chr3)) enc4 = 64;
        output += keyStrBase64[enc1] + keyStrBase64[enc2] + keyStrBase64[enc3] + keyStrBase64[enc4];
      }
      return output;
    }

    function _decodeFromBase64(input) {
      let output = [], chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0;
      input = input.replace(/[^A-Za-z0-9+/=]/g, '');
      while (i < input.length) {
        enc1 = keyStrBase64.indexOf(input[i++]);
        enc2 = keyStrBase64.indexOf(input[i++]);
        enc3 = keyStrBase64.indexOf(input[i++]);
        enc4 = keyStrBase64.indexOf(input[i++]);
        chr1 = (enc1 << 2) | (enc2 >> 4);
        chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
        chr3 = ((enc3 & 3) << 6) | enc4;
        output.push(chr1);
        if (enc3 !== 64) output.push(chr2);
        if (enc4 !== 64) output.push(chr3);
      }
      return output;
    }

    return { compress: _compress, decompress: _decompress };
  })();

  /* =====================================================================
     Audio Manager — Volume slider + SFX expansion
     ===================================================================== */
  class AudioManager {
    constructor() {
      this.masterVolume = 0.5;
      this.musicVolume = 0.5;
      this.sfxVolume = 0.7;
      this.sounds = new Map();
      this.music = null;
      this.currentMusicKey = null;
      this.muted = false;
      this._initVolumeFromStorage();
    }

    _initVolumeFromStorage() {
      try {
        const saved = localStorage.getItem('wetrun_audio');
        if (saved) {
          const v = JSON.parse(saved);
          this.masterVolume = v.master ?? 0.5;
          this.musicVolume = v.music ?? 0.5;
          this.sfxVolume = v.sfx ?? 0.7;
          this.muted = v.muted ?? false;
        }
      } catch (e) { /* ignore */ }
    }

    _saveVolume() {
      try {
        localStorage.setItem('wetrun_audio', JSON.stringify({
          master: this.masterVolume,
          music: this.musicVolume,
          sfx: this.sfxVolume,
          muted: this.muted
        }));
      } catch (e) { /* ignore */ }
    }

    setMasterVolume(v) {
      this.masterVolume = Math.max(0, Math.min(1, v));
      this._saveVolume();
      if (this.music) this.music.volume = this.masterVolume * this.musicVolume;
    }

    setMusicVolume(v) {
      this.musicVolume = Math.max(0, Math.min(1, v));
      this._saveVolume();
      if (this.music) this.music.volume = this.masterVolume * this.musicVolume;
    }

    setSfxVolume(v) {
      this.sfxVolume = Math.max(0, Math.min(1, v));
      this._saveVolume();
    }

    toggleMute() {
      this.muted = !this.muted;
      this._saveVolume();
      if (this.music) this.music.muted = this.muted;
    }

    getEffectiveVolume(type) {
      if (this.muted) return 0;
      switch (type) {
        case 'music': return this.masterVolume * this.musicVolume;
        case 'sfx': return this.masterVolume * this.sfxVolume;
        default: return this.masterVolume;
      }
    }

    // SFX registry
    registerSfx(key, url) {
      const audio = new Audio();
      audio.src = url;
      audio.preload = 'auto';
      this.sounds.set(key, audio);
    }

    playSfx(key) {
      const audio = this.sounds.get(key);
      if (!audio) return;
      const clone = audio.cloneNode();
      clone.volume = this.getEffectiveVolume('sfx');
      clone.play().catch(() => { /* ignore autoplay restrictions */ });
    }

    // Music management
    playMusic(key, url) {
      if (this.currentMusicKey === key && this.music && !this.music.paused) return;
      if (this.music) {
        this.music.pause();
        this.music.currentTime = 0;
      }
      this.music = new Audio();
      this.music.src = url;
      this.music.loop = true;
      this.music.volume = this.getEffectiveVolume('music');
      this.music.muted = this.muted;
      this.currentMusicKey = key;
      this.music.play().catch(() => { /* ignore autoplay restrictions */ });
    }

    stopMusic() {
      if (this.music) {
        this.music.pause();
        this.music.currentTime = 0;
        this.music = null;
        this.currentMusicKey = null;
      }
    }

    // Create volume slider UI
    createVolumeControls(container) {
      const wrap = document.createElement('div');
      wrap.className = 'volume-controls';
      wrap.innerHTML = `
        <style>
          .volume-controls {
            background: #050810; border: 1px solid #2a3540; border-radius: 4px;
            padding: 12px; margin: 12px 0; font-size: 12px; color: #6a7888;
            display: grid; gap: 8px;
          }
          .volume-row { display: flex; align-items: center; gap: 8px; }
          .volume-row label { min-width: 80px; color: #66ffcc; font-size: 11px; text-transform: uppercase; }
          .volume-row input[type=range] { flex: 1; accent-color: #66ffcc; }
          .volume-row .value { min-width: 40px; text-align: right; color: #ffaa55; font-family: monospace; }
          .volume-row button { padding: 4px 10px; font-size: 11px; }
        </style>
        <div class="volume-row">
          <label>Master</label>
          <input type="range" id="vol-master" min="0" max="1" step="0.05" value="${this.masterVolume}">
          <span class="value" id="vol-master-val">${Math.round(this.masterVolume * 100)}%</span>
          <button id="btn-mute" class="button ghost">${this.muted ? 'UNMUTE' : 'MUTE'}</button>
        </div>
        <div class="volume-row">
          <label>Music</label>
          <input type="range" id="vol-music" min="0" max="1" step="0.05" value="${this.musicVolume}">
          <span class="value" id="vol-music-val">${Math.round(this.musicVolume * 100)}%</span>
        </div>
        <div class="volume-row">
          <label>SFX</label>
          <input type="range" id="vol-sfx" min="0" max="1" step="0.05" value="${this.sfxVolume}">
          <span class="value" id="vol-sfx-val">${Math.round(this.sfxVolume * 100)}%</span>
        </div>
      `;
      container.appendChild(wrap);

      // Bind events
      const bind = (id, setter, displayId) => {
        const el = document.getElementById(id);
        const disp = document.getElementById(displayId);
        el.addEventListener('input', (e) => {
          const v = parseFloat(e.target.value);
          setter(v);
          disp.textContent = Math.round(v * 100) + '%';
        });
      };
      bind('vol-master', (v) => this.setMasterVolume(v), 'vol-master-val');
      bind('vol-music', (v) => this.setMusicVolume(v), 'vol-music-val');
      bind('vol-sfx', (v) => this.setSfxVolume(v), 'vol-sfx-val');

      document.getElementById('btn-mute').addEventListener('click', () => {
        this.toggleMute();
        document.getElementById('btn-mute').textContent = this.muted ? 'UNMUTE' : 'MUTE';
      });

      // Apply initial volumes
      if (this.music) this.music.volume = this.getEffectiveVolume('music');
    }
  }

  /* =====================================================================
     Save Manager — Compression + IndexedDB integration
     ===================================================================== */
  class SaveManager {
    constructor() {
      this.dbName = 'WetRunSaves';
      this.dbVersion = 1;
      this.db = null;
      this.useIDB = typeof indexedDB !== 'undefined';
    }

    async init() {
      if (!this.useIDB) return;
      return new Promise((resolve, reject) => {
        const req = indexedDB.open(this.dbName, this.dbVersion);
        req.onupgradeneeded = (e) => {
          const db = e.target.result;
          if (!db.objectStoreNames.contains('saves')) {
            db.createObjectStore('saves', { keyPath: 'id' });
          }
          if (!db.objectStoreNames.contains('meta')) {
            db.createObjectStore('meta', { keyPath: 'key' });
          }
        };
        req.onsuccess = (e) => { this.db = e.target.result; resolve(); };
        req.onerror = () => reject(req.error);
      });
    }

    _compress(data) {
      try {
        const json = JSON.stringify(data);
        return LZString.compress(json);
      } catch (e) {
        return null;
      }
    }

    _decompress(compressed) {
      try {
        const json = LZString.decompress(compressed);
        return json ? JSON.parse(json) : null;
      } catch (e) {
        return null;
      }
    }

    async save(id, data) {
      const compressed = this._compress(data);
      if (!compressed) throw new Error('Compression failed');
      const record = { id, data: compressed, timestamp: Date.now(), size: compressed.length };

      if (this.useIDB && this.db) {
        return new Promise((resolve, reject) => {
          const tx = this.db.transaction('saves', 'readwrite');
          const store = tx.objectStore('saves');
          store.put(record);
          tx.oncomplete = () => resolve();
          tx.onerror = () => reject(tx.error);
        });
      } else {
        // Fallback to localStorage
        localStorage.setItem('wetrun_save_' + id, compressed);
        return Promise.resolve();
      }
    }

    async load(id) {
      if (this.useIDB && this.db) {
        return new Promise((resolve, reject) => {
          const tx = this.db.transaction('saves', 'readonly');
          const store = tx.objectStore('saves');
          const req = store.get(id);
          req.onsuccess = () => {
            if (req.result) {
              const data = this._decompress(req.result.data);
              resolve(data);
            } else {
              resolve(null);
            }
          };
          req.onerror = () => reject(req.error);
        });
      } else {
        const compressed = localStorage.getItem('wetrun_save_' + id);
        return Promise.resolve(compressed ? this._decompress(compressed) : null);
      }
    }

    async list() {
      if (this.useIDB && this.db) {
        return new Promise((resolve, reject) => {
          const tx = this.db.transaction('saves', 'readonly');
          const store = tx.objectStore('saves');
          const req = store.getAll();
          req.onsuccess = () => resolve(req.result.map(r => ({
            id: r.id,
            timestamp: r.timestamp,
            size: r.size
          })));
          req.onerror = () => reject(req.error);
        });
      } else {
        const saves = [];
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith('wetrun_save_')) {
            const id = key.slice('wetrun_save_'.length);
            const compressed = localStorage.getItem(key);
            saves.push({ id, timestamp: 0, size: compressed.length });
          }
        }
        return Promise.resolve(saves);
      }
    }

    async delete(id) {
      if (this.useIDB && this.db) {
        return new Promise((resolve, reject) => {
          const tx = this.db.transaction('saves', 'readwrite');
          const store = tx.objectStore('saves');
          store.delete(id);
          tx.oncomplete = () => resolve();
          tx.onerror = () => reject(tx.error);
        });
      } else {
        localStorage.removeItem('wetrun_save_' + id);
        return Promise.resolve();
      }
    }
  }

  /* =====================================================================
     State Machine — Enhanced game state management
     ===================================================================== */
  const GameState = {
    BOOT: 'boot',
    CHAR_SELECT: 'char_select',
    CHAPTER_SELECT: 'chapter_select',
    CHAPTER: 'chapter',
    MISSION_CHOICE: 'mission_choice',
    MISSION_RESOLVE: 'mission_resolve',
    ENDING_CHOICE: 'ending_choice',
    ENDING: 'ending',
    SETTINGS: 'settings',
    PAUSED: 'paused'
  };

  const StateTransitions = {
    [GameState.BOOT]: [GameState.CHAR_SELECT],
    [GameState.CHAR_SELECT]: [GameState.CHAPTER_SELECT, GameState.ENDING_CHOICE],
    [GameState.CHAPTER_SELECT]: [GameState.CHAPTER, GameState.CHAR_SELECT, GameState.ENDING_CHOICE],
    [GameState.CHAPTER]: [GameState.MISSION_CHOICE, GameState.CHAPTER_SELECT],
    [GameState.MISSION_CHOICE]: [GameState.MISSION_RESOLVE, GameState.CHAPTER],
    [GameState.MISSION_RESOLVE]: [GameState.CHAPTER_SELECT, GameState.ENDING_CHOICE, GameState.CHAPTER],
    [GameState.ENDING_CHOICE]: [GameState.ENDING, GameState.CHAPTER_SELECT],
    [GameState.ENDING]: [GameState.CHAR_SELECT, GameState.CHAPTER_SELECT],
    [GameState.SETTINGS]: [GameState.CHAR_SELECT, GameState.CHAPTER_SELECT, GameState.CHAPTER, GameState.MISSION_CHOICE],
    [GameState.PAUSED]: [GameState.CHAR_SELECT, GameState.CHAPTER_SELECT, GameState.CHAPTER, GameState.MISSION_CHOICE]
  };

  class StateMachine {
    constructor(initialState = GameState.BOOT) {
      this.currentState = initialState;
      this.previousState = null;
      this.history = [initialState];
      this.listeners = new Set();
    }

    getState() { return this.currentState; }
    getPreviousState() { return this.previousState; }
    getHistory() { return [...this.history]; }

    canTransition(toState) {
      const allowed = StateTransitions[this.currentState] || [];
      return allowed.includes(toState);
    }

    transition(toState) {
      if (!this.canTransition(toState)) {
        console.warn(`Invalid transition: ${this.currentState} → ${toState}`);
        return false;
      }
      this.previousState = this.currentState;
      this.currentState = toState;
      this.history.push(toState);
      this._notify();
      return true;
    }

    onChange(fn) { this.listeners.add(fn); }
    offChange(fn) { this.listeners.delete(fn); }

    _notify() {
      this.listeners.forEach(fn => fn(this.currentState, this.previousState));
    }

    // Persist state
    serialize() {
      return {
        currentState: this.currentState,
        previousState: this.previousState,
        history: this.history
      };
    }

    static deserialize(data) {
      const sm = new StateMachine(data.currentState);
      sm.previousState = data.previousState;
      sm.history = data.history;
      return sm;
    }
  }

  /* =====================================================================
     Tier 5 Integration — Auto-initialization for play.html
     ===================================================================== */
  class Tier5 {
    constructor() {
      this.audio = new AudioManager();
      this.saveManager = new SaveManager();
      this.stateMachine = new StateMachine();
      this.initialized = false;
    }

    async init() {
      if (this.initialized) return;
      await this.saveManager.init();
      this._registerDefaultSfx();
      this.initialized = true;
    }

    _registerDefaultSfx() {
      const base = 'sounds/v2/';
      const sfx = [
        'click', 'select', 'error', 'success', 'flatline',
        'jack_in', 'jack_out', 'scan', 'probe', 'hammer', 'wardrone'
      ];
      for (const name of sfx) {
        this.audio.registerSfx(name, base + name + '.wav');
      }
    }

    // Inject volume controls into page
    injectVolumeControls(selector = '#status') {
      const container = document.querySelector(selector);
      if (container) {
        container.insertAdjacentElement('afterend', this._createVolumePanel());
      }
    }

    _createVolumePanel() {
      const panel = document.createElement('div');
      panel.id = 'tier5-volume-panel';
      panel.style.display = 'none';
      this.audio.createVolumeControls(panel);
      return panel;
    }

    // Toggle volume panel
    toggleVolumePanel() {
      const panel = document.getElementById('tier5-volume-panel');
      if (panel) panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }

    // Save game state with compression
    async saveGame(id, gameData) {
      return this.saveManager.save(id, gameData);
    }

    async loadGame(id) {
      return this.saveManager.load(id);
    }

    async listSaves() {
      return this.saveManager.list();
    }
  }

  // Export
  global.Tier5 = {
    AudioManager,
    SaveManager,
    StateMachine,
    GameState,
    Tier5,
    LZString
  };
})(window);

// Auto-init when DOM ready
document.addEventListener('DOMContentLoaded', async () => {
  window._tier5 = new window.Tier5.Tier5();
  await window._tier5.init();
});