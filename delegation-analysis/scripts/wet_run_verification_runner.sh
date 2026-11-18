#!/usr/bin/env bash
# wet_run_verification_runner.sh
# Orchestrates wet_run test/verification suite with Aside browser and SSH distribution

set -euo pipefail

# Configuration
CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../config" && pwd)"
WORKING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_REPO="/Users/emilio/projects/opencodework/Game/wet_run"
TARGET_DIR="web"
REPORT_DIR="${WORKING_DIR}/reports"
LOG_DIR="${WORKING_DIR}/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_ID="wet_run_verify_${TIMESTAMP}"

# Logging
LOG_FILE="${LOG_DIR}/${RUN_ID}.log"
mkdir -p "${LOG_DIR}" "${REPORT_DIR}"

exec > >(tee -a "${LOG_FILE}") 2>&1

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ✗${NC} $*"
}

# Parse arguments
RUN_E2E=false
RUN_BALANCE=false
DISTRIBUTED=false
SHARD_PATTERN=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --e2e) RUN_E2E=true; shift ;;
        --balance) RUN_BALANCE=true; shift ;;
        --distributed) DISTRIBUTED=true; shift ;;
        --shard) SHARD_PATTERN="$2"; shift 2 ;;
        --verbose) VERBOSE=true; shift ;;
        --help)
            cat <<EOF
Usage: $0 [options]

Options:
  --e2e           Run Playwright E2E tests (requires browser)
  --balance       Run balance harness simulation
  --distributed   Use SSH hosts for distributed execution
  --shard PATTERN Run only tests matching pattern (e.g., "tests/combat*.test.ts")
  --verbose       Verbose output
  --help          Show this help

Examples:
  $0                          # Unit tests + typecheck + lint
  $0 --e2e                    # Full suite including E2E
  $0 --distributed --shard "tests/combat*.test.ts"  # Distributed combat tests
  $0 --balance                # Balance harness only
EOF
            exit 0
            ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# Verify environment
verify_environment() {
    log "Verifying environment..."
    
    # Check source repo
    if [[ ! -d "${SOURCE_REPO}/${TARGET_DIR}" ]]; then
        log_error "Source repo not found: ${SOURCE_REPO}/${TARGET_DIR}"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm not found in PATH"
        exit 1
    fi
    
    # Check Aside MCP if needed
    if [[ "${RUN_E2E}" == "true" ]] || [[ "${DISTRIBUTED}" == "true" ]]; then
        if ! command -v aside &> /dev/null; then
            log_warn "Aside CLI not found, E2E may fail"
        fi
    fi
    
    log_success "Environment verified"
}

# Sync source to working directory
sync_source() {
    log "Syncing source from ${SOURCE_REPO}..."
    rsync -avz --delete \
        --exclude="node_modules/" \
        --exclude="dist/" \
        --exclude=".vite/" \
        --exclude="*.log" \
        --exclude="playwright-report/" \
        --exclude="test-results/" \
        "${SOURCE_REPO}/${TARGET_DIR}/" \
        "${WORKING_DIR}/${TARGET_DIR}/"
    log_success "Source synced"
}

# Install dependencies
install_deps() {
    log "Installing dependencies..."
    cd "${WORKING_DIR}/${TARGET_DIR}"
    if [[ ! -d "node_modules" ]] || [[ ! -f "package-lock.json" ]]; then
        npm ci
    else
        npm ci --prefer-offline
    fi
    log_success "Dependencies installed"
}

# Run unit tests
run_unit_tests() {
    local test_files=()
    if [[ -n "${SHARD_PATTERN}" ]]; then
        # Expand glob pattern to actual test files
        # Check if pattern already includes tests/ prefix
        local pattern="${SHARD_PATTERN}"
        if [[ "${pattern}" != tests/* ]]; then
            pattern="tests/${pattern}"
        fi
        test_files=(${pattern})
        if [[ ${#test_files[@]} -eq 0 ]] || [[ ! -e ${test_files[0]} ]]; then
            log_error "No test files match pattern: ${pattern}"
            return 1
        fi
    fi
    
    log "Running unit tests${SHARD_PATTERN:+ (shard: ${SHARD_PATTERN})}..."
    cd "${WORKING_DIR}/${TARGET_DIR}"
    
    if [[ ${#test_files[@]} -gt 0 ]]; then
        # Pass test files as individual arguments to vitest
        if npm test -- "${test_files[@]}"; then
            log_success "Unit tests passed"
            return 0
        else
            log_error "Unit tests failed"
            return 1
        fi
    else
        if npm test; then
            log_success "Unit tests passed"
            return 0
        else
            log_error "Unit tests failed"
            return 1
        fi
    fi
}

# Run typecheck
run_typecheck() {
    log "Running TypeScript typecheck..."
    cd "${WORKING_DIR}/${TARGET_DIR}"
    
    if npm run typecheck; then
        log_success "Typecheck passed (0 errors)"
        return 0
    else
        log_error "Typecheck failed"
        return 1
    fi
}

# Run lint
run_lint() {
    log "Running ESLint..."
    cd "${WORKING_DIR}/${TARGET_DIR}"
    
    if npm run lint; then
        log_success "Lint passed"
        return 0
    else
        log_error "Lint failed"
        return 1
    fi
}

# Run format check
run_format() {
    log "Checking format with Prettier..."
    cd "${WORKING_DIR}/${TARGET_DIR}"
    
    if npm run format -- --check; then
        log_success "Format check passed"
        return 0
    else
        log_warn "Format issues found (run 'npm run format' to fix)"
        return 1
    fi
}

# Run E2E tests via Aside
run_e2e() {
    log "Running Playwright E2E tests via Aside..."
    cd "${WORKING_DIR}/${TARGET_DIR}"
    
    # Set base URL for local testing
    export PLAYWRIGHT_BASE_URL="http://localhost:5173"
    
    # Start dev server in background
    log "Starting Vite dev server..."
    npm run dev > "${LOG_DIR}/vite_${RUN_ID}.log" 2>&1 &
    VITE_PID=$!
    
    # Wait for server
    sleep 5
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Run E2E tests
    local e2e_result=0
    if npm run e2e; then
        log_success "E2E tests passed"
    else
        log_error "E2E tests failed"
        e2e_result=1
    fi
    
    # Kill dev server
    kill $VITE_PID 2>/dev/null || true
    
    return $e2e_result
}

# Run balance harness
run_balance() {
    log "Running balance harness..."
    cd "${WORKING_DIR}/${TARGET_DIR}"
    
    if npm run balance -- --runs 100; then
        log_success "Balance harness completed"
        return 0
    else
        log_error "Balance harness failed"
        return 1
    fi
}

# Distributed execution via SSH
run_distributed() {
    log "Running distributed tests via SSH..."
    
    local hosts_file="${WORKING_DIR}/ssh-hosts/hosts.yaml"
    
    if [[ ! -f "${hosts_file}" ]]; then
        log_error "Hosts file not found: ${hosts_file}"
        return 1
    fi
    
    # Check if yq is available for YAML parsing
    if ! command -v yq &> /dev/null; then
        log_warn "yq not found, falling back to local execution"
        log "Install yq for YAML parsing: brew install yq (macOS) or apt-get install yq (Linux)"
        run_unit_tests
        return $?
    fi
    
    # Parse hosts from YAML
    local host_names=()
    local host_ips=()
    local host_users=()
    local host_keys=()
    local host_dirs=()
    
    local count=$(yq '.hosts | length' "${hosts_file}")
    for ((i=0; i<count; i++)); do
        host_names+=("$(yq ".hosts[$i].name" "${hosts_file}")")
        host_ips+=("$(yq ".hosts[$i].host" "${hosts_file}")")
        host_users+=("$(yq ".hosts[$i].user" "${hosts_file}")")
        host_keys+=("$(yq ".hosts[$i].key_path // \"~/.ssh/id_ed25519\"" "${hosts_file}")")
        host_dirs+=("$(yq ".hosts[$i].work_dir // \"~/projects/claudework/wet_run_delegation\"" "${hosts_file}")")
    done
    
    # Get test patterns
    local patterns=()
    local pattern_count=$(yq '.distribution.patterns | length' "${hosts_file}")
    for ((i=0; i<pattern_count; i++)); do
        patterns+=("$(yq ".distribution.patterns[$i]" "${hosts_file}")")
    done
    
    if [[ ${#patterns[@]} -eq 0 ]]; then
        log_error "No test patterns defined in hosts.yaml"
        return 1
    fi
    
    # Distribute patterns across hosts
    local results=()
    local overall=0
    
    for ((idx=0; idx<${#patterns[@]}; idx++)); do
        local pattern="${patterns[idx]}"
        local host_idx=$((idx % ${#host_names[@]}))
        local host_name="${host_names[host_idx]}"
        local host_ip="${host_ips[host_idx]}"
        local host_user="${host_users[host_idx]}"
        local host_key="${host_keys[host_idx]}"
        local host_dir="${host_dirs[host_idx]}"
        
        log "Distributing pattern '${pattern}' to ${host_name} (${host_ip})"
        
        if [[ "${host_ip}" == "localhost" ]] || [[ "${host_ip}" == "127.0.0.1" ]]; then
            # Run locally
            log "Running locally: ${pattern}"
            SHARD_PATTERN="${pattern}" run_unit_tests
            local result=$?
        else
            # Run via SSH (source nvm.sh for npm in PATH)
            log "Running via SSH on ${host_name}"
            ssh -i "${host_key}" -o ConnectTimeout=10 -o ServerAliveInterval=30 \
                "${host_user}@${host_ip}" \
                "source ~/.nvm/nvm.sh && cd ${host_dir} && SHARD_PATTERN=\"${pattern}\" ./scripts/wet_run_verification_runner.sh 2>&1"
            local result=$?
        fi
        
        if [[ $result -eq 0 ]]; then
            log_success "Pattern '${pattern}' on ${host_name}: PASSED"
            results+=("${host_name}:${pattern}|PASS")
        else
            log_error "Pattern '${pattern}' on ${host_name}: FAILED"
            results+=("${host_name}:${pattern}|FAIL")
            overall=1
        fi
    done
    
    # Aggregate results for reporting
    for r in "${results[@]}"; do
        IFS='|' read -r name status <<< "$r"
        DIST_RESULTS+=("${name}|${status}")
    done
    
    return $overall
}

# Generate report
generate_report() {
    local results=("$@")
    local report_file="${REPORT_DIR}/${RUN_ID}_report.md"
    
    cat > "${report_file}" <<EOF
# wet_run Verification Report

**Run ID**: ${RUN_ID}
**Timestamp**: $(date)
**Source**: ${SOURCE_REPO}
**Target**: ${WORKING_DIR}/${TARGET_DIR}

## Configuration
- E2E Tests: ${RUN_E2E}
- Balance Harness: ${RUN_BALANCE}
- Distributed: ${DISTRIBUTED}
- Shard Pattern: ${SHARD_PATTERN:-"none"}

## Results
EOF
    
    local all_passed=true
    for result in "${results[@]}"; do
        IFS='|' read -r name status <<< "$result"
        if [[ "$status" == "PASS" ]]; then
            echo "- ✅ **${name}**: PASSED" >> "${report_file}"
        else
            echo "- ❌ **${name}**: FAILED" >> "${report_file}"
            all_passed=false
        fi
    done
    
    echo "" >> "${report_file}"
    if [[ "$all_passed" == "true" ]]; then
        echo "**OVERALL: ALL CHECKS PASSED** ✅" >> "${report_file}"
    else
        echo "**OVERALL: SOME CHECKS FAILED** ❌" >> "${report_file}"
    fi
    
    echo "" >> "${report_file}"
    echo "## Logs" >> "${report_file}"
    echo "- Full log: \`${LOG_FILE}\`" >> "${report_file}"
    echo "- Vite log: \`${LOG_DIR}/vite_${RUN_ID}.log\`" >> "${report_file}"
    
    log "Report generated: ${report_file}"
    cat "${report_file}"
}

# Main execution
main() {
    log "Starting wet_run verification: ${RUN_ID}"
    
    verify_environment
    sync_source
    install_deps
    
    local results=()
    local overall=0
    
    # Core verification (always run)
    if run_unit_tests; then
        results+=("Unit Tests|PASS")
    else
        results+=("Unit Tests|FAIL")
        overall=1
    fi
    
    if run_typecheck; then
        results+=("TypeCheck|PASS")
    else
        results+=("TypeCheck|FAIL")
        overall=1
    fi
    
    if run_lint; then
        results+=("Lint|PASS")
    else
        results+=("Lint|FAIL")
        overall=1
    fi
    
    if run_format; then
        results+=("Format|PASS")
    else
        results+=("Format|FAIL")
        # Format is warning, not failure
    fi
    
    # Optional: E2E
    if [[ "${RUN_E2E}" == "true" ]]; then
        if run_e2e; then
            results+=("E2E Tests|PASS")
        else
            results+=("E2E Tests|FAIL")
            overall=1
        fi
    fi
    
    # Optional: Balance
    if [[ "${RUN_BALANCE}" == "true" ]]; then
        if run_balance; then
            results+=("Balance Harness|PASS")
        else
            results+=("Balance Harness|FAIL")
            overall=1
        fi
    fi
    
    # Optional: Distributed
    if [[ "${DISTRIBUTED}" == "true" ]]; then
        if run_distributed; then
            results+=("Distributed|PASS")
        else
            results+=("Distributed|FAIL")
            overall=1
        fi
    fi
    
    generate_report "${results[@]}"
    
    if [[ $overall -eq 0 ]]; then
        log_success "All verification checks passed!"
    else
        log_error "Some verification checks failed"
    fi
    
    exit $overall
}

main "$@"