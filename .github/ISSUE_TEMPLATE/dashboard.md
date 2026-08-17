---
name: Dashboard request
about: Request a new dashboard or change to existing dashboard
title: '[DASH] '
labels: dashboard, enhancement
assignees: ''
---

## 📊 Dashboard Type
- [ ] New dashboard
- [ ] Update existing dashboard
- [ ] Bug fix on dashboard

## 📍 Target
- [ ] Top hub (`Game/dashboard/index.html`)
- [ ] Roguelike submenu (`wet_run/dashboard/`)
- [ ] New sub-dashboard (e.g. Sound, Combat, Cyberspace, Equipment)
- [ ] Other: ___

## 💡 Purpose
What is the dashboard for? What data does it show?

## 📈 Data Source
Which JSON/data file does it read?
- [ ] `prologue_data.json`
- [ ] `event_dialogues.json`
- [ ] `stage_structure.json`
- [ ] New data file
- [ ] Other: ___

## 🎨 Design Notes
- Color scheme: ___
- Layout: [grid / list / table / diagram]
- Interactivity: [filters / tabs / etc.]

## ✅ Acceptance Criteria
- [ ] HTML + CSS + JS implemented
- [ ] JSON data validated by `validate_*.py`
- [ ] Tests added in `tests/unit/test_*.py`
- [ ] Static — no server-side code
- [ ] Bilingual (ko + en) where applicable
