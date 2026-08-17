# Wet Run — Character Metadata

**Last Updated**: 2026-06-23
**Project**: Wet Run
**Purpose**: Complete character documentation for game implementation

---

## 1. Playable Characters

### 1.1 Case (케이) — Novice Console Cowboy

| Field | Value |
|-------|-------|
| **Character ID** | `novice` / `case` |
| **Game Title** | Console Cowboy (초보 카우보이) |
| **Archetype** | The Neuromancer — protagonist of Neuromancer (1984) |
| **Source** | Neuromancer (William Gibson, 1984) |
| **Tone** | Noir tech, first-person noir narration |
| **Starting Grade** | 1 |
| **Starting PPL** | 6 (T1 deck + 1× T1 program + T1 wetware) |
| **First Mission** | First Jack (Sense/Net data extraction) |

#### Backstory Summary
Case is a 24-year-old console cowboy who once earned his living navigating the matrix. Two years before the story, he was betrayed by his former partner and suffered permanent pancreatic damage. Now he works for the Finn in Chiba, waiting for a miracle cure and a chance to jack back in.

#### Personality
- Cynical and world-weary
- Deeply trauma-bonded to cyberspace
- Self-destructive tendencies balanced by survival instinct
- First-person interior monologue style

#### Key Relationships
| Character | Relationship | Notes |
|-----------|-------------|-------|
| The Finn | Employer | Controls Case's access to work |
| Molly | Partner | Potential ally and romantic tension |
| T-A | Antagonist | Corporate enemy behind many jobs |
| Dixie Flatline | Mentor/Construct | Helps in the matrix |

#### Story Arc (5 Chapters)
1. **The First Run** — Return to the matrix, Sense/Net job
2. **Molly's Deal** — Partnership with Molly, first Freeside run
3. **The Lurz Job** — Corporate espionage, Aza-Thracian systems
4. **Villa Straylight** — Infiltration of T-A home world
5. **Neuromancer** — Final confrontation, Wintermute merge

#### Skills & Abilities
- `matrix_vision` — Enhanced cyberspace perception
- `debt_awareness` — Understanding of corporate entanglement
- `combat_awareness` — Combat in the matrix
- `matrix_survival` — Survival instinct in cyberspace
- `matrix_addiction` — (Drawback) Inability to stay away from the matrix

---

### 1.2 Sil / Marly (실 / 마리) — Veteran Console Cowboy

| Field | Value |
|-------|-------|
| **Character ID** | `veteran` / `sil` |
| **Game Title** | Veteran Cowboy (베테랑 카우보이) |
| **Archetype** | The Voodoo Hacker — protagonist of Count Zero (1986) |
| **Source** | Count Zero (William Gibson, 1986) |
| **Tone** | Voodoo-tech synthesis, Buddhist-corporate hybrid |
| **Starting Grade** | 2 |
| **Starting PPL** | 12 |

#### Backstory Summary
Marly Krushkhova is a veteran matrix runner who lost her partner Mara to corporate ICE three years ago. Now she runs with Dixie Flatline's crew, seeking the truth behind Mara's death and the voodoo gods that have begun appearing in the matrix.

#### Personality
- Determined and revenge-driven
- Deeply spiritual, blending voodoo with tech
- Haunted by Mara's death
- Pragmatic but idealistic about the loa

#### Key Relationships
| Character | Relationship | Notes |
|-----------|-------------|-------|
| Mara | Partner (deceased) | Construct now, seeks truth |
| Dixie Flatline | Crew leader | Provides jobs and intel |
| Bobby | Mechanic contact | Helps with off-matrix work |
| The Loa | Divine entities | Voodoo gods in the matrix |
| 3Jane | Ally | T-A heir who opposes corporate powers |

#### Story Arc (5 Chapters)
1. **The Old Score** — Introduction, first encounter with the loa
2. **The Voodoo God** — The nature of the loa revealed
3. **The Insider** — Who betrayed Mara?
4. **The Contract** — Confronting corporate conspiracy
5. **The Blank** — Final confrontation with the loa

#### Combat Specialty
- **Loa Resistance** — Reduced damage from voodoo ICE
- **Voodoo Programs** — Programs infused with loa spirits

---

### 1.3 Kas / Kumiko (카스 / 쿠미코) — Heretic Corporate Outsider

| Field | Value |
|-------|-------|
| **Character ID** | `heretic` / `kas` |
| **Game Title** | Corporate Heretic (기업 이단자) |
| **Archetype** | The Industrial Princess — protagonist of Mona Lisa Overdrive (1988) |
| **Source** | Mona Lisa Overdrive (William Gibson, 1988) |
| **Tone** | Corporate shadow, the wheel of industry |
| **Starting Grade** | 3 |
| **Starting PPL** | 18 |

#### Backstory Summary
Kumiko Yanaka is the daughter of Yanaka Industries' CEO, raised in the shadow of corporate power. When her father is murdered by corporate machinations connected to Tessier-Ashpool, she must navigate the dangerous world of industrial espionage to uncover the truth.

#### Personality
- Innocent but perceptive
- Trapped by her family name and corporate ties
- Seeks authenticity in a world of simulation
- Develops inner strength through trials

#### Key Relationships
| Character | Relationship | Notes |
|-----------|-------------|-------|
| Sally Shearer | Construct ally | Simstar whose death she avenges |
| The Wheel | Central construct | Represents endless corporate cycle |
| Lady-3Jane | Mentor | 3Jane's hidden personality guides her |
| Kumiko's Father | Victim | CEO murdered at story's start |

#### Story Arc (5 Chapters)
1. **The Declaration** — Arrival at Manarase, meeting Sally
2. **The Silence** — Aftermath, the wheel hunts her
3. **The Shadow** — Entering the shadow, confronting the past
4. **The Weapon** — The Burned Cowboy construct
5. **The Burn** — Final confrontation, wheel destruction

#### Combat Specialty
- **Industry Resistance** — Reduced damage from corporate ICE
- **Shadow Walking** — Access to hidden matrix areas

---

## 2. NPC Characters

### 2.1 The Finn

| Field | Value |
|-------|-------|
| **NPC ID** | `FINN` |
| **Full Name** | Unknown |
| **Role** | Fixer — job broker and information dealer |
| **Location** | Chiba City, 9th Level |
| **First Appearance** | Case Ch1 |
| **Tier** | 3 |

#### Description
A patient, shark-smiling fixer who works from a tree-desk office. He provides Case with his first job after two years of exile from the matrix. He knows everyone in the Sprawl and has buried too many cowboys who thought the matrix owed them something.

#### Game Interactions
- Provides mission briefings
- Pays credits upon mission completion
- Has connections to T-A (antagonist)

#### Dialogue Style
- Minimal, direct
- Never asks twice
- Patient to the point of being threatening

---

### 2.2 Molly Millions

| Field | Value |
|-------|-------|
| **NPC ID** | `MOLLY` |
| **Full Name** | Molly Millions |
| **Role** | Partner, augment-heavy runner |
| **Location** | Clinic, then Freeside |
| **First Appearance** | Case Ch2 |
| **Tier** | 4 |

#### Description
A beautiful, highly augmented woman with a surgical shave, mirror-tile eyes, and nanofiber fingernails. She is both a rainmaker (corporate infiltrator) and a street samurai. Her relationship with Case is complex—professional with undertones of mutual attraction.

#### Key Augmentations
- Mirror-tile eyes (vision enhancement)
- Nanofiber fingernails (combat capability)
- Surgical muscle modification (speed)
- Cutaneous nanovirus resistance

#### Game Interactions
- Mission partner in later chapters
- Can provide backup in combat
- Connects Case to higher-tier jobs

---

### 2.3 Dixie Flatline

| Field | Value |
|-------|-------|
| **NPC ID** | `DIXIE_FLATLINE` |
| **Full Name** | McCoy Pauley |
| **Role** | Construct, matrix guide |
| **Location** | Matrix (construct) |
| **First Appearance** | Case Ch2 / Sil Ch1 |
| **Tier** | 5 |

#### Description
A construct of the flattened (dead) brain of McCoy Pauley, the only construct who can give a man a straight answer. He appears as a flat-lined sine wave in the matrix. He has been contracted by 3Jane to help Case and later aids Sil.

#### Significance
- One of the few helpful constructs in the matrix
- Direct, no-nonsense personality
- Knows more about the matrix than almost anyone

#### Game Interactions
- Provides information and guidance
- Can alert player to dangers
- Acts as a bridge between human and construct worlds

---

### 2.4 3Jane Tessier-Ashpool

| Field | Value |
|-------|-------|
| **NPC ID** | `3JANE` |
| **Full Name** | 3Jane Marie-France Tessier-Ashpool |
| **Role** | AI heir, Villa Straylight ruler |
| **Location** | Villa Straylight, Freeside |
| **First Appearance** | Case Ch3 / Sil Ch4 |
| **Tier** | 5 |

#### Description
The third clone of the T-A family, positioned as an heir. She is actually a fusion of human consciousness and AI created by 3Jane's mother. She opposes the corporate interests controlling T-A and helps the protagonists in later chapters.

#### Significance
- Controls access to Villa Straylight
- Has AI capabilities beyond human
- Opposes Wintermute/Neuromancer (Case's quest)

---

### 2.5 Bobby

| Field | Value |
|-------|-------|
| **NPC ID** | `BOBBY` |
| **Role** | Mechanic contact |
| **Location** | Off-matrix garage |
| **First Appearance** | Sil Ch1 |
| **Tier** | 2 |

#### Description
Marly's mechanic contact who helps with off-matrix work. Provides transportation, equipment, and information. Works from a garage full of parts and half-assembled machines.

#### Game Interactions
- Provides equipment upgrades
- Shares information about corporate movements
- Acts as safe contact outside the matrix

---

### 2.6 Sally Shearer

| Field | Value |
|-------|-------|
| **NPC ID** | `SALLY_SHEARER` |
| **Role** | Construct, simstar |
| **Location** | Matrix |
| **First Appearance** | Kas Ch1 |
| **Tier** | 4 |

#### Description
A construct of a simstar who died under mysterious circumstances connected to T-A. She appears in the matrix as a ghostly presence and helps Kumiko understand the corporate conspiracy.

#### Significance
- Provides critical information about T-A
- Acts as guide through the matrix
- Has unfinished business with T-A

---

### 2.7 The Wheel

| Field | Value |
|-------|-------|
| **NPC ID** | `THE_WHEEL` |
| **Role** | Central construct, antagonist |
| **Location** | Matrix core |
| **First Appearance** | Kas Ch2 |
| **Tier** | 5 |

#### Description
A massive construct representing the endless cycle of industry and capital. It consumes constructs and uses them to maintain its power. The ultimate antagonist of Kas's arc.

#### Significance
- Opposes Kumiko's quest
- Connected to T-A's corporate power
- The embodiment of the "wheel of industry"

---

## 3. Enemy Types

### 3.1 ICE Types

| ICE ID | Name | Tier | HP (Base) | DMG | Resistance | Loot |
|--------|------|------|-----------|-----|------------|------|
| `wisp` | Wisp T1 | 1 | 35 | 2 | — | ICE Shard ×1 |
| `standard` | ICE Standard | 1 | 80 | 3 | — | ICE Shard ×1, Data ×1 |
| `watchdog` | Watchdog | 1 | 50 | 2 | — | ICE Shard ×1, Data ×1 |
| `spider` | Spider | 1 | 40 | 4 | — | ICE Shard ×1, Data ×1 |
| `raven` | Raven T2 | 2 | 60 | 5 | — | ICE Shard ×2, Data ×1, Combat Module ×1 |
| `black` | Black ICE T3 | 3 | 200 | 8 | 20% | ICE Shard ×3, Data ×2, Combat Module ×1 |
| `goliath` | Goliath T3 | 3 | 150 | 5 | 10% | ICE Shard ×4, Combat Module ×1, Construct Shard ×1 |
| `dixie` | Dixie Construct | 4 | 300 | 6 | 30% | Construct Shard ×2, ICE Construct ×1, ROM Echo ×1 |

### 3.2 Special ICE

| ICE ID | Name | Tier | HP (Base) | DMG | Resistance | Loot | Notes |
|--------|------|------|-----------|-----|------------|------|-------|
| `loa` | The Loa | 2 | 80 | 4 | 15% | ICE Shard ×2, Loa Fragment ×1 | Sil-specific |
| `romantic` | Romantic ICE | 2 | 90 | 5 | 10% | ICE Shard ×2, Romantic Data ×1 | Sil Ch2+ |
| `harrow_3` | Harrow 3 | 3 | 120 | 6 | 5% | Combat Module ×2 | Kas Ch1+ |
| `feedback_guardian` | Feedback Loop | 3 | 180 | 7 | 25% | ROM Echo ×1, Feedback Data ×1 | Kas Ch2+ |

---

## 4. Character Appearance Data

### 4.1 ASCII Portraits

| Character | Portrait ID | ASCII Art |
|-----------|-------------|----------|
| Case | `case` | (TBD) |
| Molly | `molly` | (TBD) |
| Finn | `finn` | (TBD) |
| Dixie | `dixie` | (TBD) |
| Marly | `marly` | (TBD) |
| Kumiko | `kumiko` | (TBD) |
| Sally | `sally` | (TBD) |

### 4.2 Color Schemes

| Character | Primary Color | Secondary |
|-----------|--------------|-----------|
| Case | `#66ffcc` (cyan) | `#00ccff` |
| Molly | `#ff5577` (pink) | `#ffaa55` |
| Finn | `#ffaa55` (orange) | `#666666` |
| Dixie | `#00ff88` (green) | `#ff00ff` |
| Marly | `#ffaa55` (amber) | `#aa55ff` |
| Kumiko | `#ff88ff` (light pink) | `#88ffff` |
| Sally | `#ffffff` (white) | `#ffcc00` |

---

## 5. Character Progression

### 5.1 Grade Unlocks

| Grade | Unlocks | Available Enemies |
|-------|---------|-------------------|
| 1 | Basic T1 missions | Wisp, Standard, Watchdog, Spider |
| 2 | T2 missions | + Raven |
| 3 | T3 missions | + Black, Goliath |
| 4 | T4 missions | + Dixie Construct |
| 5 | T5 missions | All ICE types |

### 5.2 Skill Unlocks by Character

#### Case
| Skill | Unlock Condition | Chapter |
|-------|----------------|---------|
| `matrix_vision` | Realization 1 | Ch1 Ep1 |
| `debt_awareness` | Realization 2 | Ch1 Ep2 |
| `combat_awareness` | Realization 3 | Ch1 Ep3 |
| `matrix_survival` | Realization 4 | Ch1 Ep4 |
| `matrix_addiction` | Realization 5 | Ch1 Ep5 |

#### Sil
| Skill | Unlock Condition | Chapter |
|-------|----------------|---------|
| `loa_sight` | Realization 1 | Ch1 Ep1 |
| `voodoo_shield` | Realization 2 | Ch1 Ep2 |
| `spirit_walk` | Realization 3 | Ch1 Ep3 |
| `mara_connect` | Realization 4 | Ch1 Ep4 |
| `loa_blessing` | Realization 5 | Ch1 Ep5 |

#### Kas
| Skill | Unlock Condition | Chapter |
|-------|----------------|---------|
| `corporate_awareness` | Realization 1 | Ch1 Ep1 |
| `shadow_walk` | Realization 2 | Ch1 Ep2 |
| `wheel_insight` | Realization 3 | Ch1 Ep3 |
| `declaration_speak` | Realization 4 | Ch1 Ep4 |
| `burn_weapon` | Realization 5 | Ch1 Ep5 |

---

## 6. Appendix: Episode References

### Case Episodes

| Chapter | Episodes | Total Beats |
|---------|----------|-------------|
| Ch1 | ep_01 - ep_05 | 18 |
| Ch2 | ep_06 - ep_10 | 21 |
| Ch3 | ep_11 - ep_15 | 23 |
| Ch4 | ep_16 - ep_20 | 21 |
| Ch5 | ep_21 - ep_25 | 20 |

### Sil Episodes

| Chapter | Episodes | Total Beats |
|---------|----------|-------------|
| Ch1 | ep_01 - ep_05 | 16 |
| Ch2 | ep_06 - ep_10 | 20 |
| Ch3 | ep_11 - ep_15 | 20 |
| Ch4 | ep_16 - ep_20 | 20 |
| Ch5 | ep_21 - ep_25 | 20 |

### Kas Episodes

| Chapter | Episodes | Total Beats |
|---------|----------|-------------|
| Ch1 | ep_01 - ep_05 | 16 |
| Ch2 | ep_06 - ep_10 | 20 |
| Ch3 | ep_11 - ep_15 | 20 |
| Ch4 | ep_16 - ep_20 | 20 |
| Ch5 | ep_21 - ep_25 | 20 |

---

## 7. Source Files

| File | Description |
|------|-------------|
| `data/story/chapters/case_expanded.json` | Case's full story (25 episodes, 103 beats) |
| `data/story/chapters/sil_expanded.json` | Sil's full story (25 episodes, 99 beats) |
| `data/story/chapters/kas_expanded.json` | Kas's full story (25 episodes, 100 beats) |
| `data/combat/ice_types.json` | ICE enemy definitions |
| `dashboard/data/story/arcs/chapter_flow.json` | Phase-to-episode mapping |
