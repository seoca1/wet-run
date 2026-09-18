# Wet Run Game Flow Validation Scenario

## Test Scenario: Complete Game Flow from Start to Ending

### Phase 0: Pre-Game Setup
- [ ] Dev server starts without errors
- [ ] Game loads in browser (canvas renders, w.wetrun available)
- [ ] No console errors on load
- [ ] Audio context unlock works on first interaction

### Phase 1: Main Menu
- [ ] Main menu renders with 9 options
- [ ] Navigation (↑↓) works
- [ ] ENTER on NEW RUN → mission_select
- [ ] ESC → stays on menu
- [ ] HUD visible on menu (shows default state)

### Phase 2: Mission Select
- [ ] 30 missions listed
- [ ] Navigation (↑↓) works
- [ ] ENTER on mission → briefing screen
- [ ] ESC → back to menu
- [ ] HUD visible

### Phase 3: Briefing Screen
- [ ] Finn's office ASCII art displays
- [ ] Mission title shown
- [ ] Fixer dialogue displays correctly
- [ ] ENTER → travel animation
- [ ] ESC → back to mission select
- [ ] HUD visible

### Phase 4: Travel Animation
- [ ] "JACKING IN..." title
- [ ] 3-step animation (Chiba sector → Street level → Jack-in point)
- [ ] Auto-advances every 3 seconds
- [ ] Any key advances immediately
- [ ] ESC → back to briefing
- [ ] HUD visible
- [ ] Auto-advance to meet_npc after 3 steps

### Phase 5: Meet NPC (Dixie Flatline)
- [ ] Construct ASCII portrait displays
- [ ] 7 dialogue lines
- [ ] ENTER advances dialogue line by line
- [ ] ESC skips dialogue
- [ ] After last line → extract_data screen
- [ ] HUD visible

### Phase 6: Extract Data
- [ ] Data extraction screen with progress bar (5 segments)
- [ ] Auto-advances or ENTER advances progress
- [ ] At 5/5 → ENTER confirms
- [ ] ESC aborts → back to meet_npc
- [ ] HUD visible

### Phase 7: Combat (Approach → Combat)
- [ ] After extract_data → approach phase
- [ ] ENTER → combat screen
- [ ] Combat UI renders (player HP, ICE HP, programs, alarm, combo)
- [ ] Programs selectable (1-9 keys)
- [ ] Program use → damage, ICE HP decreases
- [ ] ICE attacks → player HP decreases
- [ ] Victory → loot screen
- [ ] Defeat → death screen
- [ ] HUD visible during combat

### Phase 8: Loot & Mission Complete
- [ ] Loot screen shows rewards
- [ ] ENTER → mission complete
- [ ] Mission complete screen
- [ ] ENTER → back to hub/menu

### Phase 9: Death & Restart
- [ ] Combat defeat → flatline screen
- [ ] DEATH RESTART screen options
- [ ] ENTER → restart (new jockey)
- [ ] ESC → quit to menu
- [ ] Death summary recorded in Hall of Dead

### Phase 10: Ending
- [ ] Final mission (final_choice) completion
- [ ] Ending screen with choice (A/B/C)
- [ ] Ending screen displays
- [ ] Return to menu

### Phase 11: Side Content
- [ ] Hall of Dead accessible from menu
- [ ] Graphic Novel mode accessible
- [ ] Settings screen accessible
- [ ] Black Market accessible
- [ ] Tutorial overlay on first run

## Verification Checklist

- [ ] All 2626 unit tests pass
- [ ] TypeScript compilation clean
- [ ] Dev server starts cleanly
- [ ] Game loads in browser without errors
- [ ] HUD renders correctly on all applicable screens
- [ ] No console errors during normal gameplay
- [ ] Save/load works (autosave + manual)
- [ ] Audio unlock works on first interaction
- [ ] Mobile viewport works (responsive)
- [ ] Touch controls work on mobile
- [ ] Gamepad support works
