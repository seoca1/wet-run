# wet_run Delegation Orchestration

This directory contains the orchestration setup for delegating wet_run test/verification to Claude Code with Aside browser and SSH distribution.

## Structure

```
wet_run_delegation/
├── config/
│   └── delegation_config.json      # Main configuration
├── scripts/
│   ├── wet_run_verification_runner.sh   # Main orchestration script
│   └── aside_e2e_runner.js              # Aside browser E2E/visual runner
├── ssh-hosts/
│   └── hosts.yaml                     # SSH host configuration
├── logs/                              # Execution logs
└── reports/                           # Verification reports
```

## Quick Start

### 1. Local Verification (Core Suite)
```bash
cd ~/projects/claudework/wet_run_delegation
./scripts/wet_run_verification_runner.sh
```

### 2. Full Suite with E2E
```bash
./scripts/wet_run_verification_runner.sh --e2e
```

### 3. With Balance Harness
```bash
./scripts/wet_run_verification_runner.sh --balance
```

### 4. Distributed (SSH Hosts)
```bash
# First configure ssh-hosts/hosts.yaml with your hosts
./scripts/wet_run_verification_runner.sh --distributed
```

### 5. Aside Browser E2E/Visual
```bash
# Visual verification only
node scripts/aside_e2e_runner.js visual

# E2E tests via Aside
node scripts/aside_e2e_runner.js e2e

# GitHub Pages check
node scripts/aside_e2e_runner.js github

# All Aside checks
node scripts/aside_e2e_runner.js all
```

## Aside Browser Setup

The Aside browser runs on **mini24** (mac mini M4, 192.168.0.41) via SSH.

### Prerequisites
1. Aside installed on mini24
2. SSH access configured: `ssh-copy-id emilio@192.168.0.41`
3. Aside MCP server running: `aside mcp start` on mini24

### Usage via MCP
```bash
# In opencode, use the aside skill
/aside browse "https://seoca1.github.io/wet-run/wetrun-web/"

# Or via aside_repl for Playwright-style automation
aside repl script.js
```

## SSH Host Configuration

Edit `ssh-hosts/hosts.yaml` to add your distributed execution hosts:

```yaml
hosts:
  - name: "mini24"
    host: "192.168.0.41"
    user: "emilio"
    max_parallel: 4
    tags: ["linux", "ci", "browser"]
    key_path: "~/.ssh/id_ed25519"
```

## Configuration

Edit `config/delegation_config.json` to customize:
- Test patterns and sharding
- Timeout values
- Reporting formats
- Cost optimization settings

## Reports

Reports are generated in `reports/` with timestamped filenames:
- `wet_run_verify_YYYYMMDD_HHMMSS_report.md` - Main verification report
- `wet_run_aside_YYYY-MM-DDTHH-MM-SS_aside_summary.md` - Aside browser summary
- Screenshots: `main_menu_*.png`, `combat_*.png`, etc.

## Integration with opencode

From the main opencode workspace:
```bash
# Run verification from opencodework
cd /Users/emilio/projects/opencodework/Game/wet_run/web
npm test && npm run typecheck && npm run lint

# Or delegate to claudework
/Users/emilio/projects/claudework/wet_run_delegation/scripts/wet_run_verification_runner.sh --e2e
```

## Next Steps

1. **Configure SSH hosts** in `ssh-hosts/hosts.yaml`
2. **Test Aside connection** to mini24
3. **Run baseline verification** locally first
4. **Set up CI integration** for automated runs
5. **Consider Hermes** for cost optimization (future)