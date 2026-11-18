
// Visual verification script for wet_run
const { test, expect } = require('@playwright/test');

test.describe('wet_run Visual Verification', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5173');
        await page.waitForLoadState('networkidle');
    });

    test('Main menu loads correctly', async ({ page }) => {
        await expect(page.locator('canvas')).toBeVisible();
        const screenshot = await page.screenshot({ 
            path: '/Users/emilio/projects/claudework/wet_run_delegation/reports/main_menu_wet_run_aside_2026-09-25T15-42-27-987Z.png',
            fullPage: true 
        });
        console.log('Main menu screenshot saved');
    });

    test('Graphic novel mode accessible', async ({ page }) => {
        // Navigate to graphic novel mode (menu option 2)
        await page.keyboard.press('2');
        await page.waitForTimeout(1000);
        const screenshot = await page.screenshot({ 
            path: '/Users/emilio/projects/claudework/wet_run_delegation/reports/graphic_novel_wet_run_aside_2026-09-25T15-42-27-987Z.png',
            fullPage: true 
        });
        console.log('Graphic novel screenshot saved');
    });

    test('Combat screen renders', async ({ page }) => {
        // Start new run and enter combat
        await page.keyboard.press('1'); // NEW RUN
        await page.waitForTimeout(500);
        await page.keyboard.press('Enter'); // Confirm jack
        await page.waitForTimeout(2000);
        
        const screenshot = await page.screenshot({ 
            path: '/Users/emilio/projects/claudework/wet_run_delegation/reports/combat_wet_run_aside_2026-09-25T15-42-27-987Z.png',
            fullPage: true 
        });
        console.log('Combat screenshot saved');
    });

    test('Responsive layout - mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);
        const screenshot = await page.screenshot({ 
            path: '/Users/emilio/projects/claudework/wet_run_delegation/reports/mobile_wet_run_aside_2026-09-25T15-42-27-987Z.png',
            fullPage: true 
        });
        console.log('Mobile screenshot saved');
    });
});
