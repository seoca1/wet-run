import { chromium } from 'playwright';

async function check() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  page.on('pageerror', (err) => { 
    console.log('PAGE ERROR:', err.message); 
  });
  page.on('console', (msg) => { 
    if (msg.type() === 'error') { 
      console.log('CONSOLE ERROR:', msg.text()); 
    } else {
      console.log('CONSOLE [' + msg.type() + ']:', msg.text());
    }
  });
  
  await page.goto('http://localhost:5173/');
  await page.waitForLoadState('networkidle');
  console.log('--- Page loaded ---');
  
  // Wait a bit for game to initialize
  await page.waitForTimeout(3000);
  
  const canvas = await page.locator('canvas#game-canvas').count();
  console.log('Canvas elements found:', canvas);
  
  const loading = await page.locator('#loading').count();
  console.log('Loading elements found:', loading);
  
  if (loading > 0) {
    const loadingText = await page.locator('#loading').textContent();
    console.log('Loading text:', loadingText);
  }
  
  const wetrun = await page.evaluate(() => {
    const w = window;
    return typeof w.wetrun;
  });
  console.log('w.wetrun type:', wetrun);
  
  await browser.close();
}

check().catch(console.error);