#!/usr/bin/env node
// aside_e2e_runner.js
// Runs wet_run E2E tests and visual verification via Aside browser MCP

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKING_DIR = '/Users/emilio/projects/claudework/wet_run_delegation';
const WET_RUN_WEB = '/Users/emilio/projects/opencodework/Game/wet_run/web';
const REPORT_DIR = path.join(WORKING_DIR, 'reports');
const LOG_DIR = path.join(WORKING_DIR, 'logs');
const ASIDE_SESSIONS_ROOT = '/Users/emilio/.aside/u/0/sessions';

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-');
const RUN_ID = `wet_run_aside_${TIMESTAMP}`;

function runAsideRepl(script) {
    return new Promise((resolve, reject) => {
        const proc = spawn('aside', ['repl', script], {
            cwd: WET_RUN_WEB,
            env: { ...process.env }
        });
        
        let stdout = '';
        let stderr = '';
        
        proc.stdout.on('data', (data) => { stdout += data.toString(); });
        proc.stderr.on('data', (data) => { stderr += data.toString(); });
        
        proc.on('close', (code) => {
            resolve({ code, stdout, stderr });
        });
        
        proc.on('error', reject);
    });
}

function findLatestAsideSession() {
    try {
        const sessions = fs.readdirSync(ASIDE_SESSIONS_ROOT)
            .map(name => path.join(ASIDE_SESSIONS_ROOT, name))
            .filter(p => fs.statSync(p).isDirectory())
            .sort((a, b) => fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime());
        return sessions[0] || null;
    } catch {
        return null;
    }
}

function findScreenshotInSession(sessionDir, name) {
    try {
        // First check sessionDir directly
        let files = fs.readdirSync(sessionDir);
        for (const file of files) {
            if (file.includes(name) && file.endsWith('.png')) {
                return path.join(sessionDir, file);
            }
        }
        
        // Then check tmp subdirectory if it exists
        const tmpDir = path.join(sessionDir, 'tmp');
        if (fs.existsSync(tmpDir)) {
            files = fs.readdirSync(tmpDir);
            for (const file of files) {
                if (file.includes(name) && file.endsWith('.png')) {
                    return path.join(tmpDir, file);
                }
            }
        }
    } catch {}
    return null;
}

function startDevServer() {
    console.log('Starting Vite dev server...');
    return new Promise((resolve, reject) => {
        const proc = spawn('npm', ['run', 'dev'], {
            cwd: WET_RUN_WEB,
            detached: true,
            stdio: ['ignore', 'pipe', 'pipe']
        });
        
        proc.stdout.on('data', (data) => {
            const output = data.toString();
            if (output.includes('Local:') || output.includes('ready')) {
                console.log('Dev server ready');
                resolve(proc.pid);
            }
        });
        
        proc.stderr.on('data', (data) => {
            console.error('Dev server:', data.toString());
        });
        
        setTimeout(() => reject(new Error('Dev server timeout')), 30000);
    });
}

async function runVisualVerification() {
    console.log('Running visual verification via Aside...');
    
    // Start dev server
    const serverPid = await startDevServer();
    
    try {
        // Wait for server to be fully ready
        await new Promise(r => setTimeout(r, 3000));
        
        // Run ALL tests in ONE aside repl call to keep same session
        console.log('Running all visual tests in single session...');
        const script = `
// Test 1: Main menu
const page1 = await openTab('http://localhost:5173');
await page1.waitForLoadState('networkidle');
await page1.screenshot({path: 'main_menu_${RUN_ID}.png', fullPage: true});
console.log('Main menu done');

// Test 2: Graphic novel page (navigate directly)
const page2 = await openTab('http://localhost:5173/?mode=graphic_novel');
await page2.waitForLoadState('networkidle');
await page2.screenshot({path: 'graphic_novel_${RUN_ID}.png', fullPage: true});
console.log('Graphic novel done');

// Test 3: Combat page (navigate directly)
const page3 = await openTab('http://localhost:5173/?mode=combat');
await page3.waitForLoadState('networkidle');
await page3.screenshot({path: 'combat_${RUN_ID}.png', fullPage: true});
console.log('Combat done');

// Test 4: Mobile viewport (using query param)
const page4 = await openTab('http://localhost:5173?mobile=1');
await page4.waitForLoadState('networkidle');
await page4.screenshot({path: 'mobile_${RUN_ID}.png', fullPage: true});
console.log('Mobile done');

// Test 5: GitHub Pages
const page5 = await openTab('https://seoca1.github.io/wet-run/wetrun-web/');
await page5.waitForLoadState('networkidle');
await page5.screenshot({path: 'github_pages_${RUN_ID}.png', fullPage: true});
console.log('GitHub Pages done');
`;

        console.log('Running all visual tests in single session...');
        let result = await runAsideRepl(script);
        console.log(result.stdout);
        
        if (result.code !== 0) {
            console.error('Visual tests failed:', result.stderr);
            return { mainMenu: false, graphicNovel: false, combat: false, mobile: false, githubPages: false };
        }
        
        // Find the latest session and copy screenshots
        console.log('Finding screenshots in latest Aside session...');
        await new Promise(r => setTimeout(r, 3000)); // Wait for file writes
        
        const sessionDir = findLatestAsideSession();
        if (!sessionDir) {
            console.error('Could not find Aside session directory');
            return { mainMenu: false, graphicNovel: false, combat: false, mobile: false, githubPages: false };
        }
        
        console.log(`Found session: ${sessionDir}`);
        
        const screenshots = [
            'main_menu',
            'graphic_novel',
            'combat',
            'mobile',
            'github_pages'
        ];
        
        const screenshotResults = {};
        
        for (const name of screenshots) {
            const src = findScreenshotInSession(sessionDir, name);
            const dst = path.join(REPORT_DIR, `${name}_${RUN_ID}.png`);
            
            if (src && fs.existsSync(src)) {
                fs.copyFileSync(src, dst);
                console.log(`Copied ${name} from ${path.basename(src)}`);
                screenshotResults[name] = true;
            } else {
                console.log(`Missing: ${name}`);
                screenshotResults[name] = false;
            }
        }
        
        return screenshotResults;
    } finally {
        // Kill dev server
        try { process.kill(-serverPid, 'SIGTERM'); } catch {}
    }
}

function runAsideRepl(script) {
    return new Promise((resolve, reject) => {
        const proc = spawn('aside', ['repl', script], {
            cwd: WET_RUN_WEB,
            env: { ...process.env }
        });
        
        let stdout = '';
        let stderr = '';
        
        proc.stdout.on('data', (data) => { stdout += data.toString(); });
        proc.stderr.on('data', (data) => { stderr += data.toString(); });
        
        proc.on('close', (code) => {
            resolve({ code, stdout, stderr });
        });
        
        proc.on('error', reject);
    });
}

function findLatestAsideSession() {
    try {
        const sessions = fs.readdirSync(ASIDE_SESSIONS_ROOT)
            .map(name => path.join(ASIDE_SESSIONS_ROOT, name))
            .filter(p => fs.statSync(p).isDirectory())
            .sort((a, b) => fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime());
        return sessions[0] || null;
    } catch {
        return null;
    }
}

function findScreenshotInSession(sessionDir, name) {
    try {
        // First check sessionDir directly
        let files = fs.readdirSync(sessionDir);
        for (const file of files) {
            if (file.includes(name) && file.endsWith('.png')) {
                return path.join(sessionDir, file);
            }
        }
        
        // Then check tmp subdirectory if it exists
        const tmpDir = path.join(sessionDir, 'tmp');
        if (fs.existsSync(tmpDir)) {
            files = fs.readdirSync(tmpDir);
            for (const file of files) {
                if (file.includes(name) && file.endsWith('.png')) {
                    return path.join(tmpDir, file);
                }
            }
        }
    } catch {}
    return null;
}

function startDevServer() {
    console.log('Starting Vite dev server...');
    return new Promise((resolve, reject) => {
        const proc = spawn('npm', ['run', 'dev'], {
            cwd: WET_RUN_WEB,
            detached: true,
            stdio: ['ignore', 'pipe', 'pipe']
        });
        
        proc.stdout.on('data', (data) => {
            const output = data.toString();
            if (output.includes('Local:') || output.includes('ready')) {
                console.log('Dev server ready');
                resolve(proc.pid);
            }
        });
        
        proc.stderr.on('data', (data) => {
            console.error('Dev server:', data.toString());
        });
        
        setTimeout(() => reject(new Error('Dev server timeout')), 30000);
    });
}

async function main() {
    const args = process.argv.slice(2);
    const mode = args[0] || 'visual';
    
    console.log(`=== wet_run Aside E2E Runner: ${RUN_ID} ===`);
    console.log(`Mode: ${mode}`);
    console.log(`Working dir: ${WET_RUN_WEB}`);
    console.log(`Reports: ${REPORT_DIR}`);
    
    fs.mkdirSync(REPORT_DIR, { recursive: true });
    fs.mkdirSync(LOG_DIR, { recursive: true });
    
    let success = true;
    let results = {};
    
    if (mode === 'visual' || mode === 'all') {
        results = await runVisualVerification();
        success = Object.values(results).every(v => v);
    }
    
    // Generate summary report
    const reportPath = path.join(REPORT_DIR, `${RUN_ID}_aside_summary.md`);
    const summary = `# Aside E2E Verification Summary

**Run ID**: ${RUN_ID}
**Timestamp**: ${new Date().toISOString()}
**Mode**: ${mode}

## Results
- Visual Verification: ${success ? '✅ PASSED' : '❌ FAILED'}

## Screenshots
${Object.entries(results).map(([k, v]) => `- ${k}: ${v ? '✅' : '❌'} \`${k}_${RUN_ID}.png\``).join('\n')}

## Aside Session
- Session dir: (auto-detected latest)
`;

    fs.writeFileSync(reportPath, summary);
    console.log(`\nReport: ${reportPath}`);
    console.log(summary);
    
    process.exit(success ? 0 : 1);
}

main().catch(console.error);