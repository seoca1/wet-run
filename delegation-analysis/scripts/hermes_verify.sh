#!/usr/bin/env bash
# hermes_verify.sh - Run verification using Hermes with cost optimization
# Uses cheaper models for repetitive tasks

set -euo pipefail

WORKING_DIR="/Users/emilio/projects/claudework/wet_run_delegation"
TARGET_DIR="web"
CONFIG_FILE="$HOME/.config/hermes/config.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"; }
log_success() { echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $*"; }
log_warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠${NC} $*"; }
log_error() { echo -e "${RED}[$(date +'%H:%M:%S')] ✗${NC} $*"; }

# Read config
CHEAP_MODEL=$(jq -r '.models.cheap' "$CONFIG_FILE" 2>/dev/null || echo "openai/gpt-4o-mini")
EXPENSIVE_MODEL=$(jq -r '.models.expensive' "$CONFIG_FILE" 2>/dev/null || echo "anthropic/claude-3.5-sonnet")

# Parse arguments
USE_CHEAP=false
RUN_NUMBER=1

while [[ $# -gt 0 ]]; do
    case $1 in
        --cheap) USE_CHEAP=true; shift ;;
        --run) RUN_NUMBER="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Determine which model to use
if [[ "$USE_CHEAP" == "true" ]] || [[ "$RUN_NUMBER" -ge 3 ]]; then
    SELECTED_MODEL="$CHEAP_MODEL"
    log "Using CHEAP model: $SELECTED_MODEL (run #$RUN_NUMBER)"
else
    SELECTED_MODEL="$EXPENSIVE_MODEL"
    log "Using EXPENSIVE model: $SELECTED_MODEL (run #$RUN_NUMBER)"
fi

# Run verification with selected model
cd "$WORKING_DIR"

log "Starting verification with model: $SELECTED_MODEL"

# Set model via environment (if supported) or pass via command
export HERMES_MODEL="$SELECTED_MODEL"

# Run the standard verification
./scripts/wet_run_verification_runner.sh "$@"

RESULT=$?

if [[ $RESULT -eq 0 ]]; then
    log_success "Verification passed with model: $SELECTED_MODEL"
else
    log_error "Verification failed with model: $SELECTED_MODEL"
fi

exit $RESULT