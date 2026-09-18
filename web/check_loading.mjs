import { chromium } from 'playwright';

async function check() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  
  page.on('pageerror', (err) => { 
    errors.push('PAGE ERROR: ' + err.message); 
    console.log('PAGE ERROR:', err.message); 
  });
  page.on('console', (msg) => { 
    if (msg.type() === 'error') { 
      errors.push('CONSOLE ERROR: ' + msg.text()); 
      console.log('CONSOLE ERROR:', msg.text()); 
    } else {
      console.log('CONSOLE [' + msg.type() + ']:', msg.text());
    }
  });
  
  await page.goto('http://localhost:5173/');
  await page.waitForLoadState('networkidle');
  console.log('--- Page loaded ---');
  
  const canvas = await page.locator('canvas#game-canvas').count();
  console.log('Canvas elements found:', canvas);
  
  if (canvas === 0) {
    const body = await page.content();
    console.log('Body preview:', body.substring(0, 3000));
  }
  
  console.log('Errors collected:', errors);
  await browser.close();
}

check().catch(console.error);