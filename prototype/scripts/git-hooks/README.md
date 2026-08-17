# Git Hooks

Pre-commit hooks for wet_run repository.

## pre-commit (cross-project link validation)

Validates that staged changes don't break the Fiction ↔ wet_run
cross-project links (mission.story.source, Fiction game_mission_id, GN
scene mission_id). Runs `verify_story_links.py` on every commit.

### Install

```bash
cp prototype/scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Behavior

- **WARNINGS only**: Does not block commit. Orphan references are
  informational (e.g., Bridge/Blue Ant out-of-scope missions).
- **Fast**: Only runs the JSON output of verify_story_links.py.
- **Bypass**: `git commit --no-verify`

### Example output

```
WARN: cross-project orphans: 0 Fiction→mission orphans, 0 mission→Fiction blocking
```

This means the cross-project integration is clean. The warning is silent
when no orphans exist.

### Related

- `prototype/scripts/verify_story_links.py` (CLI validator)
- `prototype/docs/cross-project/orphan_source_stems.json` (historical record)
- `.github/workflows/cross-project-integrity.yml` (CI enforcement)