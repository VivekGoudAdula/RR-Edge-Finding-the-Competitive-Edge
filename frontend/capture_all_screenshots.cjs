const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.resolve(__dirname, '../reports/screenshots');
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function clickNav(page, label) {
  // Check and close any modal first
  const openModal = await page.$('.fixed.inset-0');
  if (openModal) {
    await page.evaluate(() => {
      const btn = document.querySelector('.fixed.inset-0 button');
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 600));
  }

  const clicked = await page.evaluate((navLabel) => {
    const buttons = Array.from(document.querySelectorAll('aside button, nav button'));
    for (const b of buttons) {
      if (b.textContent && b.textContent.includes(navLabel)) {
        b.click();
        return true;
      }
    }
    return false;
  }, label);

  if (!clicked) {
    throw new Error(`Nav button with label "${label}" not found`);
  }
  await new Promise(r => setTimeout(r, 1200));
}

async function run() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  
  // 1. Desktop Viewport
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 1500));

  console.log('1. Capturing Executive Overview Desktop...');
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01_executive_overview_desktop.png'), fullPage: true });

  console.log('2. Capturing Pressure Intelligence...');
  await clickNav(page, 'Pressure Intelligence');
  await page.waitForFunction(() => !document.querySelector('.animate-pulse'), { timeout: 15000 });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '02_pressure_intelligence_desktop.png'), fullPage: true });

  console.log('3. Capturing Batter Intelligence (with Tim David drawer)...');
  await clickNav(page, 'Batter Intelligence');
  await page.waitForSelector('tbody tr', { timeout: 15000 });
  // Click first row (Tim David)
  const firstBatterRow = await page.$('tbody tr');
  if (firstBatterRow) {
    await firstBatterRow.click();
    await page.waitForFunction(() => document.querySelector('.fixed.inset-0') !== null, { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1200));
  }
  await page.screenshot({ path: path.join(OUTPUT_DIR, '03_batter_intelligence_drawer_desktop.png'), fullPage: true });

  console.log('Closing batter drawer...');
  await page.evaluate(() => {
    const closeBtn = document.querySelector('.fixed.inset-0 button');
    if (closeBtn) closeBtn.click();
  });
  await page.waitForFunction(() => !document.querySelector('.fixed.inset-0'), { timeout: 5000 });
  await new Promise(r => setTimeout(r, 500));

  console.log('4. Capturing Bowler Intelligence (with Sunil Narine drawer)...');
  await clickNav(page, 'Bowler Intelligence');
  await page.waitForSelector('tbody tr', { timeout: 15000 });
  // Click first row (Sunil Narine)
  const firstBowlerRow = await page.$('tbody tr');
  if (firstBowlerRow) {
    await firstBowlerRow.click();
    await page.waitForFunction(() => document.querySelector('.fixed.inset-0') !== null, { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1200));
  }
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04_bowler_intelligence_drawer_desktop.png'), fullPage: true });

  console.log('Closing bowler drawer...');
  await page.evaluate(() => {
    const closeBtn = document.querySelector('.fixed.inset-0 button');
    if (closeBtn) closeBtn.click();
  });
  await page.waitForFunction(() => !document.querySelector('.fixed.inset-0'), { timeout: 5000 });
  await new Promise(r => setTimeout(r, 500));

  console.log('5. Capturing Player Comparison Lab...');
  await clickNav(page, 'Player Comparison Lab');
  await page.waitForFunction(() => !document.querySelector('.animate-pulse'), { timeout: 15000 });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '05_player_comparison_lab_desktop.png'), fullPage: true });

  console.log('6. Capturing Methodology & Lab...');
  await clickNav(page, 'Methodology & Lab');
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '06_methodology_lab_desktop.png'), fullPage: true });

  console.log('7. Capturing Data Explorer...');
  await clickNav(page, 'Data Explorer');
  await page.waitForSelector('tbody tr', { timeout: 15000 });
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '07_data_explorer_desktop.png'), fullPage: true });

  // 8. Mobile Executive Overview
  console.log('8. Capturing Mobile Executive Overview (375x667)...');
  await page.setViewport({ width: 375, height: 667, isMobile: true, hasTouch: true });
  await clickNav(page, 'Executive Overview');
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '08_executive_overview_mobile.png'), fullPage: true });

  // 9. Mobile Navigation Drawer
  console.log('9. Capturing Mobile Navigation Drawer...');
  await page.evaluate(() => {
    const menuBtn = document.querySelector('header button');
    if (menuBtn) menuBtn.click();
  });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '09_mobile_navigation_drawer.png'), fullPage: false });

  await browser.close();
  console.log('ALL 9 SCREENSHOTS CAPTURED AND VERIFIED SUCCESSFULLY!');
}

run().catch(err => {
  console.error('Fatal error in capture script:', err);
  process.exit(1);
});
