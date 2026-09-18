import { test, expect } from '@playwright/test';

test('debug tutorial state', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  
  // Check tutorial state
  const tutorialState = await page.evaluate(() => {
    return {
      tutorial_completed: localStorage.getItem('wetrun_tutorial_completed'),
      tutorial_step: localStorage.getItem('wetrun_tutorial_step'),
      screen: window.wetrun?.getScreen?.(),
    };
  });
  console.log('Tutorial state:', tutorialState);
  
  // Mark tutorial as completed
  await page.evaluate(() => {
    localStorage.setItem('wetrun_tutorial_completed', 'true');
    localStorage.removeItem('wetrun_tutorial_step');
  });
  
  await page.reload();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  
  const screen = await page.evaluate(() => window.wetrun?.getScreen?.());
  console.log('Screen after reload:', screen);
  
  expect(true).toBe(true);
});
