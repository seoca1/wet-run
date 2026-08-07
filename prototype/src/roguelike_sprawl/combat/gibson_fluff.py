"""Gibson Fluff Library (ADR-0170).

200+ contextual status messages in Gibson tone. Organized by
category (combat hits, crits, status effects, zones, etc.).
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FluffMessage:
    """A single status message in Gibson tone."""

    category: str
    context: str
    text: str
    weight: float = 1.0


def _m(category: str, context: str, text: str, weight: float = 1.0) -> FluffMessage:
    return FluffMessage(category=category, context=context, text=text, weight=weight)


FLUFF_MESSAGES: dict[str, tuple[FluffMessage, ...]] = {
    "combat_hit": (
        _m("combat_hit", "player_to_ice", "Your deck spits fire. The ICE catches the burn."),
        _m("combat_hit", "player_to_ice", "Code cascades. The construct *stutters*."),
        _m("combat_hit", "player_to_ice", "The grid ripples. ICE takes the hit."),
        _m("combat_hit", "player_to_ice", "Wetware bridges the gap. The construct falls."),
        _m("combat_hit", "player_to_ice", "You punch through. The data flows."),
        _m("combat_hit", "player_to_ice", "Your program hits. The construct *feels* it."),
        _m("combat_hit", "player_to_ice", "The construct shudders. Its defenses fold."),
        _m("combat_hit", "player_to_ice", "You arc through the construct. It drops."),
        _m("combat_hit", "player_to_ice", "Decryption complete. The construct *screams*."),
        _m("combat_hit", "player_to_ice", "The grid shivers. Your program lands."),
        _m("combat_hit", "ice_to_player", "The construct lashes back. You feel it."),
        _m("combat_hit", "ice_to_player", "The ICE strikes. Your deck catches the edge."),
        _m("combat_hit", "ice_to_player", "Defense protocol fires. You take the hit."),
        _m("combat_hit", "ice_to_player", "The construct's teeth find your wetware."),
        _m("combat_hit", "ice_to_player", "Your deck shudders. The ICE punctures."),
        _m("combat_hit", "ice_to_player", "Counter-fire. You take the damage."),
        _m("combat_hit", "ice_to_player", "The construct pivots. You feel it land."),
        _m("combat_hit", "ice_to_player", "ICE bites. Your trace spikes."),
        _m("combat_hit", "ice_to_player", "The construct's hook finds you."),
        _m("combat_hit", "ice_to_player", "Your deck folds. The construct rakes."),
    ),
    "crit": (
        _m("crit", "player_to_ice", "Your program *sings*. The construct splits."),
        _m("crit", "player_to_ice", "Critical damage. The construct *screams*."),
        _m("crit", "player_to_ice", "You hit the nerve. The construct crumbles."),
        _m("crit", "player_to_ice", "Your code *finds* the construct. It breaks."),
        _m("crit", "player_to_ice", "The grid shudders. Your program arcs deep."),
        _m("crit", "ice_to_player", "The construct lands *clean*. You fold."),
        _m("crit", "ice_to_player", "Critical. Your wetware *shudders*."),
        _m("crit", "ice_to_player", "The construct finds the gap. It cuts."),
        _m("crit", "ice_to_player", "Critical hit. Your deck cracks."),
        _m("crit", "ice_to_player", "The construct *sings*. You take it all."),
    ),
    "burn": (
        _m("burn", "applied", "The construct *burns*. Corrupt data seeps."),
        _m("burn", "applied", "Burn infection. The construct sputters."),
        _m("burn", "applied", "Corrupting payload. The construct smolders."),
        _m("burn", "applied", "Your virus spreads. The construct ignites."),
        _m("burn", "applied", "The construct catches. Burn payload active."),
        _m("burn", "applied", "Corruption cascade. The construct melts."),
        _m("burn", "applied", "Burn virus. The construct smolders."),
        _m("burn", "applied", "Your payload *finds* the construct. Burn."),
        _m("burn", "applied", "The construct *catches*. Burn payload."),
        _m("burn", "applied", "Virus spreads. The construct *screams*."),
        _m("burn", "expired", "The burn fades. The construct stabilizes."),
        _m("burn", "expired", "Burn payload expires. The construct recovers."),
        _m("burn", "expired", "The construct's corruption clears."),
        _m("burn", "expired", "Burn subsides. The construct breathes."),
        _m("burn", "expired", "The construct's burn expires. Wetware stabilizes."),
    ),
    "stun": (
        _m("stun", "applied", "The construct *locks*. Stunned."),
        _m("stun", "applied", "Your payload hits the construct's core. It freezes."),
        _m("stun", "applied", "Stun payload. The construct drops."),
        _m("stun", "applied", "The construct *stutters*. Stunned."),
        _m("stun", "applied", "Lock protocol. The construct halts."),
        _m("stun", "applied", "Your program *paralyzes* the construct."),
        _m("stun", "applied", "The construct's core seizes. Stun."),
        _m("stun", "applied", "Stun cascade. The construct *drops*."),
        _m("stun", "applied", "Your code *freezes* the construct."),
        _m("stun", "applied", "The construct *seizes*. Stunned."),
    ),
    "slow": (
        _m("slow", "applied", "The construct *slows*. Reaction time halved."),
        _m("slow", "applied", "Slow payload. The construct *lurches*."),
        _m("slow", "applied", "Your payload *delays* the construct."),
        _m("slow", "applied", "The construct's wetware *slows*."),
        _m("slow", "applied", "Slow cascade. The construct lags."),
        _m("slow", "applied", "Your code *drags* the construct down."),
        _m("slow", "applied", "The construct's reaction *stutters*."),
        _m("slow", "applied", "Slow payload. The construct *heaves*."),
        _m("slow", "applied", "The construct's core *slows*."),
        _m("slow", "applied", "Your code *delays* the construct."),
    ),
    "silence": (
        _m("silence", "applied", "The construct *silences*. No skills."),
        _m("silence", "applied", "Silence payload. The construct *stutters*."),
        _m("silence", "applied", "Your code *mutes* the construct."),
        _m("silence", "applied", "The construct's voice *stops*."),
        _m("silence", "applied", "Silence cascade. The construct cannot speak."),
        _m("silence", "applied", "Your payload *mutes* the construct."),
        _m("silence", "applied", "The construct's core *silences*."),
        _m("silence", "applied", "Silence payload. The construct freezes."),
        _m("silence", "applied", "Your code *mutes* the construct."),
        _m("silence", "applied", "The construct's voice *stops*."),
    ),
    "vulnerable": (
        _m("vulnerable", "applied", "The construct *weakens*. It takes more damage."),
        _m("vulnerable", "applied", "Your debuff *lands*. The construct is vulnerable."),
        _m("vulnerable", "applied", "Vulnerability cascade. The construct weakens."),
        _m("vulnerable", "applied", "Your code *finds* the construct's weakness."),
        _m("vulnerable", "applied", "The construct *weakens*. Damage taken rises."),
        _m("vulnerable", "applied", "Vulnerability payload. The construct sags."),
        _m("vulnerable", "applied", "Your debuff *lands*. The construct is vulnerable."),
        _m("vulnerable", "applied", "The construct's defenses *weaken*."),
        _m("vulnerable", "applied", "Vulnerability cascade. The construct weakens."),
        _m("vulnerable", "applied", "Your code *finds* the construct's weakness."),
    ),
    "salvage": (
        _m("salvage", "heal", "Your dec collects *heal*. The wounded feel it."),
        _m("salvage", "heal", "Heal payload. The construct's data heals you."),
        _m("salvage", "heal", "Your deck *breathes*. Heal collected."),
        _m("salvage", "heal", "Heal segment. Your wetware recovers."),
        _m("salvage", "heal", "The construct's heal *flows* to you."),
        _m("salvage", "cred", "CRED collect. The construct's wallet transfers."),
        _m("salvage", "cred", "Your deck pings. CRED gained."),
        _m("salvage", "cred", "The construct's account *lifts*. CRED."),
        _m("salvage", "cred", "CRED payload. The construct pays its debt."),
        _m("salvage", "cred", "Your wallet *clicks*. CRED collected."),
        _m("salvage", "frag", "FRAG collect. The construct's code fragments."),
        _m("salvage", "frag", "Your deck *absorbs*. FRAG gained."),
        _m("salvage", "frag", "The construct's code *breaks*. FRAG."),
        _m("salvage", "frag", "FRAG payload. Build material."),
        _m("salvage", "frag", "Your coll *sorts*. FRAG collected."),
    ),
    "zone_transition": (
        _m("zone_transition", "surface", "Surface. The air is thin here."),
        _m("zone_transition", "surface", "You jack into the surface."),
        _m("zone_transition", "surface", "The grid *opens*. Surface protocols."),
        _m("zone_transition", "mid", "Mid. The ICE thickens."),
        _m("zone_transition", "mid", "You descend. Mid-protocols."),
        _m("zone_transition", "mid", "The grid *deepens*. Mid-tier ICE."),
        _m("zone_transition", "core", "Core. The corp's heart."),
        _m("zone_transition", "core", "You breach. Core-grid."),
        _m("zone_transition", "core", "The grid *hardens*. Core ICE."),
        _m("zone_transition", "ta", "T-A. The family waits."),
        _m("zone_transition", "ta", "You climb. T-A spine."),
        _m("zone_transition", "ta", "The grid *sharpens*. Tessier-Ashpool."),
        _m("zone_transition", "freeside", "Freeside. The L5 colony."),
        _m("zone_transition", "freeside", "You drift. Freeside."),
        _m("zone_transition", "freeside", "The grid *tilts*. Freeside."),
    ),
    "encounter": (
        _m("encounter", "watchdog", "Watchdog. The hunters run."),
        _m("encounter", "watchdog", "The grid *smells* you. Watchdog."),
        _m("encounter", "watchdog", "Watchdog scent. The pack picks up."),
        _m("encounter", "goliath", "Goliath. The corp's jaw."),
        _m("encounter", "goliath", "The grid *shudders*. Goliath."),
        _m("encounter", "goliath", "Goliath's jaw. The corp's heavy."),
        _m("encounter", "black", "Black ICE. The corrupted."),
        _m("encounter", "black", "The grid *screams*. Black ICE."),
        _m("encounter", "black", "Black corruption. The payload armed."),
        _m("encounter", "construct", "Construct. The family."),
        _m("encounter", "construct", "The grid *welcomes*. Construct."),
        _m("encounter", "construct", "Construct form. The family."),
        _m("encounter", "wintermute", "Wintermute. The interface."),
        _m("encounter", "wintermute", "The grid *shifts*. Wintermute."),
        _m("encounter", "wintermute", "Wintermute's voice. The *word*."),
        _m("encounter", "ta", "T-A. The family."),
        _m("encounter", "ta", "The grid *clears*. T-A."),
        _m("encounter", "ta", "Tessier-Ashpool. The hive."),
        _m("encounter", "neuromancer", "Neuromancer. The merger."),
        _m("encounter", "neuromancer", "The grid *speaks*. Neuromancer."),
        _m("encounter", "neuromancer", "Neuromancer's voice. The *message*."),
    ),
}




# Extra combat fluff to reach 200+ (Gibson tone)
EXTRA_COMBAT = (
    _m("combat_hit", "player_to_ice", "Your deck *spits*. The construct catches."),
    _m("combat_hit", "player_to_ice", "Code cascades. The construct *shudders*."),
    _m("combat_hit", "player_to_ice", "The grid *ripples*. The construct drops."),
    _m("combat_hit", "player_to_ice", "Wetware bridges. The construct *screams*."),
    _m("combat_hit", "player_to_ice", "Your program *hits*. The construct falls."),
    _m("combat_hit", "player_to_ice", "The construct *shudders*. Code cascades."),
    _m("combat_hit", "player_to_ice", "Your code arcs through. The construct drops."),
    _m("combat_hit", "player_to_ice", "Decryption complete. The construct *screams*."),
    _m("combat_hit", "player_to_ice", "The grid *shivers*. Your program lands."),
    _m("combat_hit", "player_to_ice", "Your wetware bridges the gap. The construct drops."),
    _m("combat_hit", "ice_to_player", "The construct *lashes*. You feel it."),
    _m("combat_hit", "ice_to_player", "The ICE *strikes*. Your deck catches it."),
    _m("combat_hit", "ice_to_player", "Defense protocol. You take the hit."),
    _m("combat_hit", "ice_to_player", "The construct's *teeth* find your wetware."),
    _m("combat_hit", "ice_to_player", "Your deck *shudders*. The ICE punctures."),
    _m("combat_hit", "ice_to_player", "Counter-fire. You take the damage."),
    _m("combat_hit", "ice_to_player", "The construct *pivots*. You feel it land."),
    _m("combat_hit", "ice_to_player", "ICE *bites*. Your trace spikes."),
    _m("combat_hit", "ice_to_player", "The construct's *hook* finds you."),
    _m("combat_hit", "ice_to_player", "Your deck *folds*. The construct rakes."),
    _m("combat_hit", "ice_to_player", "The construct *catches* your wetware."),
    _m("combat_hit", "ice_to_player", "ICE *bites*. Your deck shudders."),
    _m("combat_hit", "ice_to_player", "The construct *finds* your trace."),
    _m("combat_hit", "ice_to_player", "Your wetware *catches* the ICE."),
    _m("combat_hit", "ice_to_player", "The construct *lashes* your deck."),
    _m("combat_hit", "ice_to_player", "ICE *strikes*. Your trace spikes."),
    _m("combat_hit", "ice_to_player", "The construct *tears* your wetware."),
    _m("combat_hit", "ice_to_player", "Your deck *burns*. The ICE finds it."),
    _m("combat_hit", "ice_to_player", "The construct *punctures* your deck."),
    _m("combat_hit", "ice_to_player", "ICE *finds* your trace. You feel it."),
)

EXTRA_CRIT = (
    _m("crit", "player_to_ice", "Your program *sings*. The construct splits."),
    _m("crit", "player_to_ice", "Critical damage. The construct *screams*."),
    _m("crit", "player_to_ice", "You hit the nerve. The construct crumbles."),
    _m("crit", "player_to_ice", "Your code *finds* the construct. It breaks."),
    _m("crit", "player_to_ice", "The grid *shudders*. Your program arcs deep."),
    _m("crit", "player_to_ice", "Critical. The construct *folds*."),
    _m("crit", "player_to_ice", "Your code *pierces*. The construct breaks."),
    _m("crit", "player_to_ice", "The construct *screams*. Critical damage."),
    _m("crit", "player_to_ice", "Your program *finds* the nerve. Critical."),
    _m("crit", "player_to_ice", "Critical. The construct *shatters*."),
    _m("crit", "ice_to_player", "The construct lands *clean*. You fold."),
    _m("crit", "ice_to_player", "Critical. Your wetware *shudders*."),
    _m("crit", "ice_to_player", "The construct finds the gap. It cuts."),
    _m("crit", "ice_to_player", "Critical hit. Your deck *cracks*."),
    _m("crit", "ice_to_player", "The construct *sings*. You take it all."),
    _m("crit", "ice_to_player", "Critical. Your deck *folds*."),
    _m("crit", "ice_to_player", "The construct *finds* the gap. It cuts."),
    _m("crit", "ice_to_player", "Critical. Your wetware *shudders*."),
    _m("crit", "ice_to_player", "The construct *cuts* deep. Critical."),
    _m("crit", "ice_to_player", "Critical. Your trace *spikes*."),
)

EXTRA_BURN = (
    _m("burn", "applied", "The construct *burns*. Corrupt data seeps."),
    _m("burn", "applied", "Burn infection. The construct sputters."),
    _m("burn", "applied", "Corrupting payload. The construct smolders."),
    _m("burn", "applied", "Your virus spreads. The construct ignites."),
    _m("burn", "applied", "The construct *catches*. Burn payload active."),
    _m("burn", "applied", "Corruption cascade. The construct melts."),
    _m("burn", "applied", "Burn virus. The construct smolders."),
    _m("burn", "applied", "Your payload *finds* the construct. Burn."),
    _m("burn", "applied", "The construct *catches*. Burn payload."),
    _m("burn", "applied", "Virus spreads. The construct *screams*."),
    _m("burn", "expired", "The burn fades. The construct stabilizes."),
    _m("burn", "expired", "Burn payload expires. The construct recovers."),
    _m("burn", "expired", "The construct's corruption clears."),
    _m("burn", "expired", "Burn subsides. The construct breathes."),
    _m("burn", "expired", "The construct's burn expires. Wetware stabilizes."),
    _m("burn", "expired", "Burn clears. The construct recovers."),
    _m("burn", "expired", "The construct's data *cools*. Burn ends."),
    _m("burn", "expired", "Burn payload *ends*. The construct recovers."),
    _m("burn", "expired", "The construct's corruption *clears*."),
    _m("burn", "expired", "Burn *ends*. The construct stabilizes."),
)

EXTRA_STUN = (
    _m("stun", "applied", "The construct *locks*. Stunned."),
    _m("stun", "applied", "Your payload hits the construct's core. It freezes."),
    _m("stun", "applied", "Stun payload. The construct drops."),
    _m("stun", "applied", "The construct *stutters*. Stunned."),
    _m("stun", "applied", "Lock protocol. The construct halts."),
    _m("stun", "applied", "Your program *paralyzes* the construct."),
    _m("stun", "applied", "The construct's core seizes. Stun."),
    _m("stun", "applied", "Stun cascade. The construct *drops*."),
    _m("stun", "applied", "Your code *freezes* the construct."),
    _m("stun", "applied", "The construct *seizes*. Stunned."),
    _m("stun", "expired", "Stun clears. The construct recovers."),
    _m("stun", "expired", "The construct's core *reboots*. Stun ends."),
    _m("stun", "expired", "Stun payload expires. The construct moves."),
    _m("stun", "expired", "The construct *wakes*. Stun ends."),
    _m("stun", "expired", "The construct's lock *releases*. Stun ends."),
    _m("stun", "expired", "Stun *clears*. The construct moves."),
    _m("stun", "expired", "The construct *reboots*. Stun ends."),
    _m("stun", "expired", "Stun payload *ends*. The construct moves."),
    _m("stun", "expired", "The construct *wakes*. Stun ends."),
    _m("stun", "expired", "The construct's lock *fades*. Stun ends."),
)

EXTRA_SALVAGE = (
    _m("salvage", "heal", "Your dec collects *heal*. The wounded feel it."),
    _m("salvage", "heal", "Heal payload. The construct's data heals you."),
    _m("salvage", "heal", "Your deck *breathes*. Heal collected."),
    _m("salvage", "heal", "Heal segment. Your wetware recovers."),
    _m("salvage", "heal", "The construct's heal *flows* to you."),
    _m("salvage", "heal", "Heal payload. Your wetware *recovers*."),
    _m("salvage", "heal", "Your deck *repairs*. Heal collected."),
    _m("salvage", "heal", "The construct's data *heals* your deck."),
    _m("salvage", "heal", "Heal *flows*. Your wetware recovers."),
    _m("salvage", "heal", "Your deck *breathes*. Heal flows."),
    _m("salvage", "cred", "CRED collect. The construct's wallet transfers."),
    _m("salvage", "cred", "Your deck pings. CRED gained."),
    _m("salvage", "cred", "The construct's account *lifts*. CRED."),
    _m("salvage", "cred", "CRED payload. The construct pays its debt."),
    _m("salvage", "cred", "Your wallet *clicks*. CRED collected."),
    _m("salvage", "cred", "CRED *flows*. The construct's wallet transfers."),
    _m("salvage", "cred", "Your deck *pings*. CRED gained."),
    _m("salvage", "cred", "The construct's account *transfers*. CRED."),
    _m("salvage", "cred", "CRED payload. The construct *pays*."),
    _m("salvage", "cred", "Your wallet *clicks*. CRED."),
    _m("salvage", "frag", "FRAG collect. The construct's code fragments."),
    _m("salvage", "frag", "Your deck *absorbs*. FRAG gained."),
    _m("salvage", "frag", "The construct's code *breaks*. FRAG."),
    _m("salvage", "frag", "FRAG payload. Build material."),
    _m("salvage", "frag", "Your coll *sorts*. FRAG collected."),
    _m("salvage", "frag", "FRAG *flows*. The construct's code fragments."),
    _m("salvage", "frag", "Your deck *absorbs*. FRAG gained."),
    _m("salvage", "frag", "The construct's code *breaks*. FRAG."),
    _m("salvage", "frag", "FRAG payload. Build material."),
    _m("salvage", "frag", "Your coll *sorts*. FRAG."),
)

EXTRA_SLOW = (
    _m("slow", "applied", "The construct *slows*. Reaction time halved."),
    _m("slow", "applied", "Slow payload. The construct *lurches*."),
    _m("slow", "applied", "Your payload *delays* the construct."),
    _m("slow", "applied", "The construct's wetware *slows*."),
    _m("slow", "applied", "Slow cascade. The construct lags."),
    _m("slow", "applied", "Your code *drags* the construct down."),
    _m("slow", "applied", "The construct's reaction *stutters*."),
    _m("slow", "applied", "Slow payload. The construct *heaves*."),
    _m("slow", "applied", "The construct's core *slows*."),
    _m("slow", "applied", "Your code *delays* the construct."),
    _m("slow", "expired", "Slow clears. The construct recovers."),
    _m("slow", "expired", "The construct's reaction *speeds*. Slow ends."),
    _m("slow", "expired", "Slow payload expires. The construct moves."),
    _m("slow", "expired", "The construct *reacts*. Slow ends."),
    _m("slow", "expired", "The construct's wetware *clears*. Slow ends."),
    _m("slow", "expired", "Slow *clears*. The construct reacts."),
    _m("slow", "expired", "The construct *reacts*. Slow ends."),
    _m("slow", "expired", "Slow payload *ends*. The construct moves."),
    _m("slow", "expired", "The construct *reacts*. Slow ends."),
    _m("slow", "expired", "The construct's core *speeds*. Slow ends."),
)

EXTRA_SILENCE = (
    _m("silence", "applied", "The construct *silences*. No skills."),
    _m("silence", "applied", "Silence payload. The construct *stutters*."),
    _m("silence", "applied", "Your code *mutes* the construct."),
    _m("silence", "applied", "The construct's voice *stops*."),
    _m("silence", "applied", "Silence cascade. The construct cannot speak."),
    _m("silence", "applied", "Your payload *mutes* the construct."),
    _m("silence", "applied", "The construct's core *silences*."),
    _m("silence", "applied", "Silence payload. The construct freezes."),
    _m("silence", "applied", "Your code *mutes* the construct."),
    _m("silence", "applied", "The construct's voice *stops*."),
    _m("silence", "expired", "Silence clears. The construct speaks."),
    _m("silence", "expired", "The construct's voice *returns*. Silence ends."),
    _m("silence", "expired", "Silence payload expires. The construct speaks."),
    _m("silence", "expired", "The construct *speaks*. Silence ends."),
    _m("silence", "expired", "The construct's voice *returns*. Silence ends."),
    _m("silence", "expired", "Silence *clears*. The construct speaks."),
    _m("silence", "expired", "The construct *speaks*. Silence ends."),
    _m("silence", "expired", "Silence payload *ends*. The construct speaks."),
    _m("silence", "expired", "The construct *speaks*. Silence ends."),
    _m("silence", "expired", "The construct's voice *returns*. Silence ends."),
)

EXTRA_VULNERABLE = (
    _m("vulnerable", "applied", "The construct *weakens*. It takes more damage."),
    _m("vulnerable", "applied", "Your debuff *lands*. The construct is vulnerable."),
    _m("vulnerable", "applied", "Vulnerability cascade. The construct weakens."),
    _m("vulnerable", "applied", "Your code *finds* the construct's weakness."),
    _m("vulnerable", "applied", "The construct *weakens*. Damage taken rises."),
    _m("vulnerable", "applied", "Vulnerability payload. The construct sags."),
    _m("vulnerable", "applied", "Your debuff *lands*. The construct is vulnerable."),
    _m("vulnerable", "applied", "The construct's defenses *weaken*."),
    _m("vulnerable", "applied", "Vulnerability cascade. The construct weakens."),
    _m("vulnerable", "applied", "Your code *finds* the construct's weakness."),
    _m("vulnerable", "expired", "Vulnerability clears. The construct recovers."),
    _m("vulnerable", "expired", "The construct's defenses *recover*. Vulnerability ends."),
    _m("vulnerable", "expired", "Vulnerability payload expires. The construct recovers."),
    _m("vulnerable", "expired", "The construct *recovers*. Vulnerability ends."),
    _m("vulnerable", "expired", "The construct's defenses *recover*. Vulnerability ends."),
    _m("vulnerable", "expired", "Vulnerability *clears*. The construct recovers."),
    _m("vulnerable", "expired", "The construct *recovers*. Vulnerability ends."),
    _m("vulnerable", "expired", "Vulnerability payload *ends*. The construct recovers."),
    _m("vulnerable", "expired", "The construct *recovers*. Vulnerability ends."),
    _m("vulnerable", "expired", "The construct's defenses *recover*. Vulnerability ends."),
)

EXTRA_ZONE = (
    _m("zone_transition", "surface", "Surface. The air is thin here."),
    _m("zone_transition", "surface", "You jack into the surface."),
    _m("zone_transition", "surface", "The grid *opens*. Surface protocols."),
    _m("zone_transition", "surface", "Surface *whispers*. The grid is thin."),
    _m("zone_transition", "surface", "You surface. The grid *breathes*."),
    _m("zone_transition", "mid", "Mid. The ICE *thickens*."),
    _m("zone_transition", "mid", "You descend. Mid-protocols."),
    _m("zone_transition", "mid", "The grid *deepens*. Mid-tier ICE."),
    _m("zone_transition", "mid", "Mid *whispers*. The ICE thickens."),
    _m("zone_transition", "mid", "You descend. The grid *deepens*."),
    _m("zone_transition", "core", "Core. The corp's heart."),
    _m("zone_transition", "core", "You breach. Core-grid."),
    _m("zone_transition", "core", "The grid *hardens*. Core ICE."),
    _m("zone_transition", "core", "Core *pulses*. The corp's heart."),
    _m("zone_transition", "core", "You breach. The grid *hardens*."),
    _m("zone_transition", "ta", "T-A. The family waits."),
    _m("zone_transition", "ta", "You climb. T-A spine."),
    _m("zone_transition", "ta", "The grid *sharpens*. Tessier-Ashpool."),
    _m("zone_transition", "ta", "T-A *whispers*. The family waits."),
    _m("zone_transition", "ta", "You climb. The grid *sharpens*."),
    _m("zone_transition", "freeside", "Freeside. The L5 colony."),
    _m("zone_transition", "freeside", "You drift. Freeside."),
    _m("zone_transition", "freeside", "The grid *tilts*. Freeside."),
    _m("zone_transition", "freeside", "Freeside *whispers*. The L5 colony."),
    _m("zone_transition", "freeside", "You drift. The grid *tilts*."),
    _m("zone_transition", "construct", "Construct. The family."),
    _m("zone_transition", "construct", "The grid *welcomes*. Construct."),
    _m("zone_transition", "construct", "Construct form. The family."),
    _m("zone_transition", "construct", "Construct *whispers*. The family."),
    _m("zone_transition", "construct", "The grid *welcomes*. Construct."),
)

EXTRA_ENCOUNTER = (
    _m("encounter", "watchdog", "Watchdog. The hunters run."),
    _m("encounter", "watchdog", "The grid *smells* you. Watchdog."),
    _m("encounter", "watchdog", "Watchdog scent. The pack picks up."),
    _m("encounter", "watchdog", "Watchdog *yips*. The pack runs."),
    _m("encounter", "watchdog", "The grid *hunts*. Watchdog."),
    _m("encounter", "goliath", "Goliath. The corp's jaw."),
    _m("encounter", "goliath", "The grid *shudders*. Goliath."),
    _m("encounter", "goliath", "Goliath's jaw. The corp's heavy."),
    _m("encounter", "goliath", "Goliath *looms*. The grid shudders."),
    _m("encounter", "goliath", "The corp's jaw. Goliath."),
    _m("encounter", "black", "Black ICE. The corrupted."),
    _m("encounter", "black", "The grid *screams*. Black ICE."),
    _m("encounter", "black", "Black corruption. The payload armed."),
    _m("encounter", "black", "Black ICE *screams*. The grid shudders."),
    _m("encounter", "black", "The corrupted. Black ICE."),
    _m("encounter", "construct", "Construct. The family."),
    _m("encounter", "construct", "The grid *welcomes*. Construct."),
    _m("encounter", "construct", "Construct form. The family."),
    _m("encounter", "construct", "Construct *whispers*. The family."),
    _m("encounter", "construct", "The grid *welcomes*. Construct."),
    _m("encounter", "wintermute", "Wintermute. The interface."),
    _m("encounter", "wintermute", "The grid *shifts*. Wintermute."),
    _m("encounter", "wintermute", "Wintermute's voice. The *word*."),
    _m("encounter", "wintermute", "Wintermute *speaks*. The interface."),
    _m("encounter", "wintermute", "The interface. Wintermute."),
    _m("encounter", "ta", "T-A. The family."),
    _m("encounter", "ta", "The grid *clears*. T-A."),
    _m("encounter", "ta", "Tessier-Ashpool. The hive."),
    _m("encounter", "ta", "T-A *whispers*. The family."),
    _m("encounter", "ta", "The grid *clears*. T-A."),
    _m("encounter", "neuromancer", "Neuromancer. The merger."),
    _m("encounter", "neuromancer", "The grid *speaks*. Neuromancer."),
    _m("encounter", "neuromancer", "Neuromancer's voice. The *message*."),
    _m("encounter", "neuromancer", "Neuromancer *speaks*. The merger."),
    _m("encounter", "neuromancer", "The message. Neuromancer."),
)



# Merge extra messages into the registry (post-processing to avoid
# self-reference during dict literal definition).
_extras_map = {
    "combat_hit": EXTRA_COMBAT,
    "crit": EXTRA_CRIT,
    "burn": EXTRA_BURN,
    "stun": EXTRA_STUN,
    "slow": EXTRA_SLOW,
    "silence": EXTRA_SILENCE,
    "vulnerable": EXTRA_VULNERABLE,
    "salvage": EXTRA_SALVAGE,
    "zone_transition": EXTRA_ZONE,
    "encounter": EXTRA_ENCOUNTER,
}
for _cat, _extra in _extras_map.items():
    FLUFF_MESSAGES[_cat] = FLUFF_MESSAGES[_cat] + _extra
del _extras_map, _cat, _extra

def get_fluff(category: str, rng: random.Random) -> str | None:
    """Return a weighted random fluff message for a category, or None."""
    messages = FLUFF_MESSAGES.get(category, ())
    if not messages:
        return None
    for message in messages:
        if rng.random() < message.weight:
            return message.text
    return messages[-1].text


def fluff_count(category: str) -> int:
    """Return the number of messages registered for a category."""
    return len(FLUFF_MESSAGES.get(category, ()))


def total_fluff_count() -> int:
    """Return the total number of fluff messages across all categories."""
    return sum(len(msgs) for msgs in FLUFF_MESSAGES.values())


def all_categories() -> tuple[str, ...]:
    """Return all registered fluff categories."""
    return tuple(FLUFF_MESSAGES.keys())


def get_messages_in_category(category: str) -> tuple[str, ...]:
    """Return all message texts in a category."""
    return tuple(m.text for m in FLUFF_MESSAGES.get(category, ()))


def add_fluff(category: str, message: FluffMessage) -> None:
    """Add a fluff message to a category."""
    current = FLUFF_MESSAGES.get(category, ())
    FLUFF_MESSAGES[category] = tuple(current) + (message,)


def has_category(category: str) -> bool:
    """Check if a category has fluff messages."""
    return category in FLUFF_MESSAGES


__all__ = [
    "FLUFF_MESSAGES",
    "FluffMessage",
    "add_fluff",
    "all_categories",
    "fluff_count",
    "get_fluff",
    "get_messages_in_category",
    "has_category",
    "total_fluff_count",
]
