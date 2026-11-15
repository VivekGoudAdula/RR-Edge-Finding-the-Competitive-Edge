const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function captureScreenshots() {
  const screenshotsDir = path.resolve(__dirname, '../reports/screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // 1. Overview Page
  console.log('Capturing overview...');
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle0', timeout: 20000 });
  await delay(1000);
  await page.screenshot({ path: path.join(screenshotsDir, 'overview.png'), fullPage: false });

  // 2. Pressure Intelligence
  console.log('Capturing pressure intelligence...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Pressure Intelligence'));
    if (btn) btn.click();
  });
  await delay(1000);
  await page.screenshot({ path: path.join(screenshotsDir, 'pressure_intelligence.png'), fullPage: false });

  // 3. Methodology & Model Lab
  console.log('Capturing methodology lab...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Methodology & Models'));
    if (btn) btn.click();
  });
  await delay(1000);
  await page.screenshot({ path: path.join(screenshotsDir, 'methodology_lab.png'), fullPage: false });

  // 4. Player Comparison Lab: Adjacent (David vs Surya)
  console.log('Capturing comparison adjacent...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Player Comparison'));
    if (btn) btn.click();
  });
  await delay(1000);
  await page.screenshot({ path: path.join(screenshotsDir, 'comparison_adjacent.png'), fullPage: false });

  // 5. Player Comparison Lab: Maxwell vs Vaibhav
  console.log('Capturing comparison Maxwell vs Vaibhav...');
  await page.evaluate(() => {
    const selects = Array.from(document.querySelectorAll('select'));
    if (selects.length >= 2) {
      // Find option for Glenn Maxwell in select 0
      for (const opt of selects[0].options) {
        if (opt.text.includes('Glenn Maxwell')) {
          selects[0].value = opt.value;
          selects[0].dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
      // Find option for Vaibhav in select 1
      for (const opt of selects[1].options) {
        if (opt.text.includes('Vaibhav')) {
          selects[1].value = opt.value;
          selects[1].dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    }
  });
  await delay(1200);
  await page.screenshot({ path: path.join(screenshotsDir, 'comparison_maxwell_vaibhav.png'), fullPage: false });

  // 6. Mobile Viewport Drawer
  console.log('Capturing mobile view...');
  await page.setViewport({ width: 375, height: 667 });
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle0', timeout: 20000 });
  await delay(800);
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="Toggle navigation menu"]');
    if (btn) btn.click();
  });
  await delay(500);
  await page.screenshot({ path: path.join(screenshotsDir, 'mobile_drawer.png'), fullPage: false });

  await browser.close();
  console.log('All screenshots captured successfully.');
}

captureScreenshots().catch(err => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
