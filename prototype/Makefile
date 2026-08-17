.PHONY: help install sync run test lint format typecheck docstring-check build clean download-font all verify-missions verify-3way verify-facts verify-all-checks fiction-verify fiction-motif fiction-cards story-review story-review-llm story-review-motif

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

sync: ## Install/sync dependencies with uv
	uv sync --all-extras

install: sync ## Alias for sync

download-font: ## Download the libtcod font (one-time)
	uv run python scripts/download_font.py

run: ## Run the game (hello-world)
	uv run roguelike-sprawl

prologue: ## Play the prologue cinematic
	uv run python scripts/prologue.py

prologue-fast: ## Play the prologue (fast typing)
	uv run python scripts/prologue.py --speed fast

briefing: ## Play the Finn briefing scene
	uv run python scripts/prologue.py --scene briefing

demo: ## Full game demo with Korean subtitles (Prologue → Briefing → Matrix → Combat)
	uv run python scripts/full_demo.py

demo-en: ## English-only demo (no Korean)
	uv run python scripts/full_demo.py --no-korean

demo-fast: ## Full game demo (fast typing)
	uv run python scripts/full_demo.py --fast

demo-skip: ## Skip prologue and start at briefing
	uv run python scripts/full_demo.py --skip-prologue

play: ## Interactive playthrough with Korean subtitles
	uv run python scripts/full_demo.py --interactive

play-en: ## Interactive playthrough, English-only
	uv run python scripts/full_demo.py --interactive --no-korean

text-demo: ## Text-only demo (no graphics, for verification)
	uv run python scripts/text_demo.py --fast

# --- Graphic Novel (GUI window) ---
# Requires display/window environment. Launches actual game window.
gn: ## Graphic Novel — GUI window (case/novice)
	uv run python scripts/play.py --gn-mode novice

gn-veteran: ## Graphic Novel — GUI window (sil/veteran)
	uv run python scripts/play.py --gn-mode veteran

gn-heretic: ## Graphic Novel — GUI window (kas/heretic)
	uv run python scripts/play.py --gn-mode heretic

gn-all: ## Graphic Novel — GUI window (all 12 scenes shuffled)
	uv run python scripts/play.py --gn-mode prologue

# --- Graphic Novel (text/headless) ---
# No window required. Terminal output only.
gn-text: ## Graphic Novel — text mode (case/novice)
	uv run python scripts/graphic_novel.py --mode novice --speed 50

gn-text-veteran: ## Graphic Novel — text mode (sil/veteran)
	uv run python scripts/graphic_novel.py --mode veteran --speed 50

gn-text-heretic: ## Graphic Novel — text mode (kas/heretic)
	uv run python scripts/graphic_novel.py --mode heretic --speed 50

gn-text-all: ## Graphic Novel — text mode (all 12 scenes)
	uv run python scripts/graphic_novel.py --mode prologue --seed 42 --speed 50

test-tcod: ## Test tcod font rendering
	uv run python scripts/test_tcod.py

test: ## Run tests with pytest
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov

lint: ## Run ruff linter
	uv run ruff check .

format: ## Format code with ruff
	uv run ruff format .

typecheck: ## Run mypy type checker
	uv run mypy src/

docstring-check: ## Measure docstring coverage (ADR-0120)
	uv run interrogate -vv src/wet_run

build: ## Build the package
	uv build

clean: ## Clean build artifacts and caches
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

all: format lint typecheck docstring-check test ## Run all checks (format, lint, typecheck, docstring-check, test)

# --- Sound system ---
.PHONY: sound-test sound-manager sound-demo sound-demo-full sound-clean

sound-test: ## Test which audio backends are available
	uv run python scripts/test_sound_libraries.py

sound-manager: ## Run SoundManager unit tests
	uv run python -m pytest tests/unit/test_sound_manager.py -v

sound-demo: ## Play all 27 default sounds in sequence
	uv run python scripts/demo_sounds.py

sound-demo-full: ## Full game demo with sound integration
	uv run python scripts/full_demo_sound.py

sound-clean: ## Remove generated sound files
	rm -rf data/sounds_test/

# --- Avatar ---
.PHONY: demo-avatar

demo-avatar: ## Show Jockey Avatar visual demo (ADR-0016)
	uv run python scripts/demo_avatar.py

# --- Full demo (GUI + sound) ---
.PHONY: demo-sound-full demo-sound-headless

demo-sound-full: ## Full game demo with sound (requires GUI/display)
	uv run python scripts/full_demo_sound.py

demo-sound-headless: ## Headless sound demo (audio + text, no GUI required)
	uv run python scripts/headless_sound_demo.py

# --- Cinematic art ---
.PHONY: demo-art

demo-art: ## Show cinematic ASCII art demo
	uv run python scripts/demo_cinematic_art.py

# --- Prologue verification ---
.PHONY: verify-prologue

verify-prologue: ## Headless verification of prologue + briefing scenes
	uv run python scripts/verify_prologue.py

# --- Dashboard ---
.PHONY: dashboard dashboard-validate

dashboard: ## Open project dashboard in browser
	@echo "Opening http://localhost:8765/dashboard/index.html"
	@echo "(Run 'make dashboard-server' in another terminal if not already running)"
	open http://localhost:8765/dashboard/index.html 2>/dev/null || \
	  xdg-open http://localhost:8765/dashboard/index.html 2>/dev/null || \
	  echo "Open manually: http://localhost:8765/dashboard/index.html"

dashboard-server: ## Start local HTTP server for dashboard (port 8765)
	uv run python -m http.server 8765

dashboard-validate: ## Validate prologue_data.json structure
	uv run python scripts/validate_prologue_data.py

# --- Event dialogues validation ---
.PHONY: validate-event-dialogues

validate-event-dialogues: ## Validate event_dialogues.json structure
	uv run python scripts/validate_event_dialogues.py

# --- Stage structure validation ---
.PHONY: validate-stage-structure

validate-stage-structure: ## Validate stage_structure.json
	uv run python scripts/validate_stage_structure.py

# --- Top hub (cross-project) ---
.PHONY: hub

hub: ## Open cross-project dashboard hub (Game/dashboard/index.html)
	@echo "Cross-project hub: http://localhost:8765/dashboard/index.html"
	open http://localhost:8765/dashboard/index.html 2>/dev/null || \
	  xdg-open http://localhost:8765/dashboard/index.html 2>/dev/null || \
	  echo "Open manually: http://localhost:8765/dashboard/index.html"

# --- Cross-project integrity (ADR-0006 / P3) ---
.PHONY: verify-missions verify-3way verify-facts verify-all-checks

verify-missions: ## Validate missions.json ↔ EN stories sync
	uv run python scripts/verify_story_links.py

verify-3way: ## Validate 3-way consistency (Fiction side)
	python3 ../../../Fiction/tools/verify_3way_consistency.py --all

verify-facts: ## Regenerate game_facts.json from missions + chapters + tests
	uv run python $(CURDIR)/../scripts/sync_dashboard_facts.py

verify-all-checks: ## Run cross-project integrity suite (mission + 3-way + facts + tests)
	uv run python scripts/verify_story_links.py && \
	python3 ../../../Fiction/tools/verify_3way_consistency.py --all && \
	make verify-facts && \
	uv run pytest --tb=line -q

# Fix double-defined dashboard-server (was duplicate target)
.PHONY: dashboard-server-cross
dashboard-server-cross: ## Start HTTP server at Game/ level (port 8765) - serves both Game and Fiction
	cd $(CURDIR)/../.. && $(CURDIR)/.venv/bin/python -m http.server 8765

# --- Fiction cross-project checks (Fiction repo entry points) ---
.PHONY: fiction-verify fiction-motif fiction-cards

fiction-verify: ## Fiction: frontmatter + structure verify (110/110)
	python3 ../../../Fiction/tools/verify_derivative.py --all --quiet

fiction-motif: ## Fiction: motif consistency check (55 stories)
	python3 ../../../Fiction/tools/story_check.py --motif-check --all

fiction-cards: ## Fiction: regenerate 110 dashboard cards (.html / .ko.html)
	python3 ../../_publish/scripts/sync_dashboard_cards.py --all

# --- Comprehensive review pipeline (L2+ Sonnet) ---
.PHONY: story-review story-review-llm story-review-motif

story-review: ## Comprehensive story review (motif check + optional LLM)
	python3 ../../../Fiction/tools/story_check.py --motif-check --all

story-review-llm: ## LLM plot+prose review on single story (costs ~$0.03, OpenRouter)
	python3 ../../../Fiction/tools/story_review.py --provider openrouter --mode full --review-runs 3

story-review-motif: ## Comprehensive: motif check + LLM plot check (combined)
	make story-review && python3 ../../../Fiction/tools/story_review.py --mode plot --review-runs 3 \
	  Fiction/derivative/sprawl-trilogy/short-stories/en/2026-06-29_dixies_choice.md

# --- Master review pipeline (ADR-0006 + P3 + LLM) ---
.PHONY: all-review

all-review: ## Master review: every cross-project check (verify + fiction + story)
	make verify-all-checks
	@echo ""
	@echo "=== Fiction integrity ==="
	make fiction-verify
	make fiction-motif
	@echo ""
	@echo "=== Game integrity ==="
	make lint
	make test
	@echo ""
	@echo "=== Summary ==="
	@echo "Cross-project integrity: ✓ all checks passed"
	@echo "Fiction: 110/110 verify, 55/55 motif consistent"
	@echo "Game: 3003 pytest passed, ruff clean"

# LLM-assisted review (Sonnet 4.5 via OpenRouter, ~$0.03/story)
.PHONY: story-review-batch

story-review-batch: ## LLM review on all v2.0+ stories (~$0.50 for 20 stories)
	cd $(CURDIR)/../../../.. && \
	for f in Fiction/derivative/sprawl-trilogy/short-stories/en/2026-07-*.md; do \
		if [ ! -f "$${f%.md}.review.json" ] || [ "$${f}" -nt "$${f%.md}.review.json" ]; then \
			python3 Fiction/tools/story_review.py --provider openrouter --mode plot --save "$$f"; \
		fi; \
	done
	@echo "Batch review complete. Check *.review.json for grades."
