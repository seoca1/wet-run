#!/usr/bin/env tsx
/**
 * Balance Regression Detector
 * 목적: 현재 브랜치와 baseline 비교하여 승률 regression 감지
 */

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const BASELINE_BRANCH = process.argv[2] || 'main';
const THRESHOLD = 5; // 5%p 이상 차이면 regression
const RESULTS_DIR = path.join(process.cwd(), 'test-results');

interface DeckResults {
  [deck: string]: {
    [grade: string]: number;
  };
}

function runBalance(label: string): DeckResults {
  console.log(`\n[${label}] Running balance tests...`);

  const results: DeckResults = {};
  const decks = ['opening', 'veteran', 'heretic'];

  for (const deck of decks) {
    try {
      const output = execSync(`npm run balance -- --deck ${deck}`, {
        encoding: 'utf8',
        stdio: 'pipe'
      });

      // Parse output for win rates
      const gradePattern = /Grade (\d+): ([\d.]+)%/g;
      let match;
      results[deck] = {};

      while ((match = gradePattern.exec(output)) !== null) {
        const grade = `grade${match[1]}`;
        const winRate = parseFloat(match[2]);
        results[deck][grade] = winRate;
      }

      console.log(`  ✓ ${deck}: ${Object.keys(results[deck]).length} grades`);
    } catch (error) {
      console.error(`  ✗ ${deck}: failed`);
      results[deck] = {};
    }
  }

  return results;
}

function compareResults(current: DeckResults, baseline: DeckResults): {
  hasRegression: boolean;
  report: string[];
} {
  let hasRegression = false;
  const report: string[] = [];

  report.push('# Balance Comparison Report');
  report.push('');
  report.push(`Baseline: ${BASELINE_BRANCH}`);
  report.push(`Threshold: ±${THRESHOLD}%p`);
  report.push('');

  for (const deck of Object.keys(current)) {
    if (!baseline[deck]) {
      report.push(`## ${deck} (NEW DECK)`);
      continue;
    }

    report.push(`## ${deck.toUpperCase()}`);
    report.push('');
    report.push('| Grade | Baseline | Current | Diff | Status |');
    report.push('|-------|----------|---------|------|--------|');

    for (const grade of Object.keys(current[deck])) {
      const curr = current[deck][grade];
      const base = baseline[deck]?.[grade] ?? 0;
      const diff = curr - base;

      let status = '✅ OK';
      if (diff < -THRESHOLD) {
        hasRegression = true;
        status = '❌ REGRESSION';
      } else if (diff > THRESHOLD) {
        status = '⚠️  IMPROVEMENT';
      }

      report.push(
        `| ${grade} | ${base.toFixed(1)}% | ${curr.toFixed(1)}% | ${diff > 0 ? '+' : ''}${diff.toFixed(1)}%p | ${status} |`
      );
    }

    report.push('');
  }

  return { hasRegression, report };
}

async function main() {
  console.log('🎮 Balance Regression Detector');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  // Create results directory
  if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
  }

  // Run tests on current branch
  console.log('\n[1/3] Testing current branch...');
  const currentResults = runBalance('current');

  // Stash changes if any
  console.log('\n[2/3] Switching to baseline...');
  try {
    execSync('git stash', { stdio: 'pipe' });
  } catch {
    // No changes to stash
  }

  // Switch to baseline branch
  const originalBranch = execSync('git branch --show-current', {
    encoding: 'utf8'
  }).trim();

  execSync(`git checkout ${BASELINE_BRANCH}`, { stdio: 'pipe' });

  // Run tests on baseline
  const baselineResults = runBalance('baseline');

  // Restore original branch
  console.log('\n[3/3] Restoring original branch...');
  execSync(`git checkout ${originalBranch}`, { stdio: 'pipe' });
  try {
    execSync('git stash pop', { stdio: 'pipe' });
  } catch {
    // No stash to pop
  }

  // Compare results
  console.log('\n📊 Comparing results...');
  const { hasRegression, report } = compareResults(currentResults, baselineResults);

  // Write report
  const reportText = report.join('\n');
  const summaryPath = path.join(RESULTS_DIR, 'balance-summary.txt');
  fs.writeFileSync(summaryPath, reportText);

  console.log('\n' + reportText);

  // Exit with status
  if (hasRegression) {
    console.error('\n❌ Balance regression detected!');
    process.exit(1);
  } else {
    console.log('\n✅ No regression detected');
    process.exit(0);
  }
}

main().catch((error) => {
  console.error('Error running balance comparison:', error);
  process.exit(1);
});
