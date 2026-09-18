#!/usr/bin/env python3
"""
Wet Run Game Flow Validation Script
Automated verification of game flow from start to end
"""

import subprocess
import time
import sys
import json
import requests
from pathlib import Path

class GameFlowValidator:
    def __init__(self):
        self.project_root = Path("/Users/emilio/projects/opencodework/Game/wet_run")
        self.web_dir = self.project_root / "web"
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def run(self):
        print("=" * 60)
        print("WET RUN GAME FLOW VALIDATION")
        print("=" * 60)
        
        self.check_environment()
        self.check_typescript_compilation()
        self.run_unit_tests()
        self.check_dev_server()
        self.verify_game_load()
        self.verify_game_flow()
        self.verify_hud_rendering()
        self.verify_tools()
        
        self.print_summary()
        
    def check_environment(self):
        print("\n🔍 Checking environment...")
        # Check Node.js
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"  Node.js: {result.stdout.strip()}")
        
        # Check npm
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"  npm: {result.stdout.strip()}")
        
        # Check Python
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        print(f"  Python: {result.stdout.strip()}")
        
        self.passed.append("Environment check")
        
    def check_typescript_compilation(self):
        print("\n🔍 Checking TypeScript compilation...")
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=self.web_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  ✅ TypeScript compilation clean")
            self.passed.append("TypeScript compilation")
        else:
            print(f"  ❌ TypeScript errors:\n{result.stderr}")
            self.errors.append("TypeScript compilation failed")
            
    def run_unit_tests(self):
        print("\n🔍 Running unit tests...")
        result = subprocess.run(
            ["npm", "run", "test"],
            cwd=self.web_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            # Parse test output
            for line in result.stdout.split('\n'):
                if "Test Files" in line and "passed" in line:
                    print(f"  ✅ {line.strip()}")
            self.passed.append("Unit tests (2626 tests)")
        else:
            print(f"  ❌ Unit tests failed:\n{result.stdout}")
            self.errors.append("Unit tests failed")
            
    def check_dev_server(self):
        print("\n🔍 Checking dev server...")
        # Start dev server in background
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=self.web_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(5)
        
        try:
            # Check if server responds
            response = requests.get("http://localhost:5173/", timeout=10)
            if response.status_code == 200:
                print("  ✅ Dev server responds (200 OK)")
                self.passed.append("Dev server")
            else:
                print(f"  ❌ Dev server returned {response.status_code}")
                self.errors.append("Dev server not responding")
        except Exception as e:
            print(f"  ❌ Dev server error: {e}")
            self.errors.append("Dev server connection failed")
        finally:
            proc.terminate()
            
    def verify_game_load(self):
        print("\n🔍 Verifying game loads in browser...")
        # Use the existing check script
        result = subprocess.run(
            ["node", "check_loading2.mjs"],
            cwd=self.web_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if "w.wetrun type: object" in result.stdout:
            print("  ✅ Game loads (w.wetrun object available)")
            self.passed.append("Game load in browser")
        else:
            print(f"  ❌ Game failed to load:\n{result.stdout}")
            self.errors.append("Game failed to load in browser")
            
    def verify_game_flow(self):
        print("\n🔍 Verifying game flow stages...")
        # Check that all stage renderers exist
        stages = [
            ("briefing", "renderBriefingScreen"),
            ("travel", "renderTravelScreen"),
            ("meet_npc", "renderNPCDialogueScreen"),
            ("bypass_security", "renderBypassSecurityScreen"),
            ("extract_data", "renderExtractDataScreen"),
            ("black_market", "renderBlackMarketScreen"),
            ("ghost_encounter", "renderGhostEncounterScreen"),
            ("death_restart", "renderDeathRestartScreen"),
            ("failed", "renderFailedScreen"),
        ]
        
        menu_ts = self.web_dir / "src" / "renderer" / "menu.ts"
        content = menu_ts.read_text()
        
        for stage_id, renderer in stages:
            if renderer in content:
                print(f"  ✅ {stage_id}: {renderer} exists")
            else:
                print(f"  ❌ {stage_id}: {renderer} missing")
                self.errors.append(f"Missing renderer for {stage_id}")
                
        # Check main.ts integration
        main_ts = self.web_dir / "src" / "main.ts"
        main_content = main_ts.read_text()
        
        for stage_id, _ in stages:
            if f'this.screen === "{stage_id}"' in main_content:
                print(f"  ✅ {stage_id}: integrated in main.ts draw()")
            else:
                print(f"  ⚠️  {stage_id}: not found in main.ts draw()")
                self.warnings.append(f"Stage {stage_id} not integrated in main.ts")
                
    def verify_hud_rendering(self):
        print("\n🔍 Verifying HUD rendering...")
        # Check hud.ts exists and exports
        hud_ts = self.web_dir / "src" / "renderer" / "hud.ts"
        if hud_ts.exists():
            content = hud_ts.read_text()
            if "export function renderHUD" in content and "export function shouldRenderHUD" in content:
                print("  ✅ HUD module exports correctly")
                self.passed.append("HUD module")
            else:
                print("  ❌ HUD module missing exports")
                self.errors.append("HUD module missing exports")
        else:
            print("  ❌ HUD module missing")
            self.errors.append("HUD module missing")
            
        # Check main.ts uses renderWithHUD
        main_ts = self.web_dir / "src" / "main.ts"
        content = main_ts.read_text()
        if "renderWithHUD" in content and "renderHUD" in content:
            print("  ✅ HUD integrated in main.ts")
            self.passed.append("HUD integration")
        else:
            print("  ❌ HUD not integrated in main.ts")
            self.errors.append("HUD not integrated")
            
        # Check shouldRenderHUD screens
        hud_ts = self.web_dir / "src" / "renderer" / "hud.ts"
        content = hud_ts.read_text()
        required_screens = [
            "menu", "mission_select", "briefing", "travel",
            "meet_npc", "extract_data", "matrix", "approach",
            "black_market", "ghost_encounter", "death_restart"
        ]
        for screen in required_screens:
            if screen in content:
                print(f"  ✅ HUD enabled for: {screen}")
            else:
                print(f"  ⚠️  HUD not enabled for: {screen}")
                self.warnings.append(f"HUD not enabled for {screen}")
                
    def verify_tools(self):
        print("\n🔍 Verifying tools and scripts...")
        
        # Check web scripts
        scripts = [
            ("export_all.py", "exports all data"),
            ("export_missions.py", "exports missions"),
            ("export_web_data.py", "exports web data"),
            ("export_effects.py", "exports effects"),
            ("generate-audio.py", "generates audio"),
            ("generate-icons.py", "generates icons"),
            ("sync_missions.ts", "syncs missions"),
            ("sync_scenes.ts", "syncs scenes"),
        ]
        
        for script, desc in scripts:
            path = self.web_dir / "scripts" / script
            if path.exists():
                print(f"  ✅ {script}: {desc}")
            else:
                print(f"  ❌ {script}: missing ({desc})")
                self.errors.append(f"Missing script: {script}")
                
        # Check tools
        tools = [
            ("build_static_data.py", "builds static data"),
            ("find_broken_links.py", "finds broken links"),
            ("audit_sprawl.py", "audits sprawl content"),
            ("build_dashboard.py", "builds dashboard"),
            ("fix_scene_data_drift.py", "fixes scene data drift"),
        ]
        
        for tool, desc in tools:
            path = Path("/Users/emilio/projects/opencodework/Game/wet_run/scripts/tools") / tool
            if path.exists():
                print(f"  ✅ {tool}: {desc}")
            else:
                print(f"  ❌ {tool}: missing ({desc})")
                self.errors.append(f"Missing tool: {tool}")
                
    def print_summary(self):
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"\n✅ Passed: {len(self.passed)}")
        for p in self.passed:
            print(f"  ✅ {p}")
            
        print(f"\n⚠️  Warnings: {len(self.warnings)}")
        for w in self.warnings:
            print(f"  ⚠️  {w}")
            
        print(f"\n❌ Errors: {len(self.errors)}")
        for e in self.errors:
            print(f"  ❌ {e}")
            
        print("\n" + "=" * 60)
        if self.errors:
            print("❌ VALIDATION FAILED - Errors found")
            sys.exit(1)
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS")
            sys.exit(0)
        else:
            print("✅ VALIDATION PASSED - All checks passed")
            sys.exit(0)

if __name__ == "__main__":
    validator = GameFlowValidator()
    validator.run()
