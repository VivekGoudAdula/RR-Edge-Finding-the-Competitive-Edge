const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function testMLLab() {
  console.log('Testing ML Lab page navigation & rendering...');
  const screenshotsDir = path.resolve(__dirname, '../reports/screenshots');
  if (!fs.existsSync(screenshotsDir)) fs.mkdirSync(screenshotsDir, { recursive: true });

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  const delay = ms => new Promise(r => setTimeout(r, ms));

  // 1. Go to home
  console.log('Opening home page...');
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle0', timeout: 20000 });
  await delay(1000);

  // 2. Click Machine Learning Lab tab
  console.log('Navigating to Machine Learning Lab...');
  const clicked = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Machine Learning Lab'));
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  });
  console.log('Clicked Machine Learning Lab:', clicked);
  await delay(1500);

  // 3. Verify ML Lab Header
  const title = await page.evaluate(() => document.querySelector('h1')?.innerText || '');
  console.log('Page Title:', title);

  // 4. Capture screenshot
  const screenshotPath = path.join(screenshotsDir, '10_ml_lab_overview.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });
  console.log('Saved screenshot to:', screenshotPath);

  // 5. Test Live Simulator click
  console.log('Switching to Simulator tab...');
  await page.evaluate(() => {
    const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Live Delivery Inference Simulator'));
    if (tabBtn) tabBtn.click();
  });
  await delay(1000);

  console.log('Clicking Run Live ML Prediction...');
  await page.evaluate(() => {
    const simBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Run Live ML Prediction'));
    if (simBtn) simBtn.click();
  });
  await delay(1500);

  const simResult = await page.evaluate(() => {
    const text = document.body.innerText;
    return text.includes('Batter Expected Runs') && text.includes('Bowler Expected Concession');
  });
  console.log('Live inference rendered results:', simResult);

  const simScreenshotPath = path.join(screenshotsDir, '11_ml_lab_simulator.png');
  await page.screenshot({ path: simScreenshotPath, fullPage: false });
  console.log('Saved simulator screenshot to:', simScreenshotPath);

  await browser.close();
  console.log('Console errors:', consoleErrors.length);
  if (consoleErrors.length > 0) {
    console.error('Errors:', consoleErrors);
    process.exit(1);
  }
  console.log('Browser test finished successfully.');
}

testMLLab().catch(err => {
  console.error('Error during browser test:', err);
  process.exit(1);
});

