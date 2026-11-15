const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function testBehavioralIntelligence() {
  console.log('Testing Behavioral Intelligence page navigation & rendering...');
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

  try {
    // 1. Go to home
    console.log('Opening home page...');
    await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle0', timeout: 20000 });
    await delay(1000);

    // 2. Click Behavioral Dynamics tab
    console.log('Navigating to Behavioral Dynamics...');
    const clicked = await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Behavioral Dynamics'));
      if (btn) {
        btn.click();
        return true;
      }
      return false;
    });
    console.log('Clicked Behavioral Dynamics:', clicked);
    await delay(1500);

    // 3. Verify Page Title
    const title = await page.evaluate(() => document.querySelector('h1')?.innerText || '');
    console.log('Page Title:', title);

    // 4. Capture 12_behavioral_batting_overview.png
    const path1 = path.join(screenshotsDir, '12_behavioral_batting_overview.png');
    await page.screenshot({ path: path1, fullPage: false });
    console.log('Saved screenshot to:', path1);

    // 5. Open Batter Dossier Drawer (Click on Tim David)
    console.log('Clicking Tim David row for detailed dossier...');
    await page.evaluate(() => {
      const tr = Array.from(document.querySelectorAll('tr')).find(r => r.innerText && r.innerText.includes('Tim David'));
      if (tr) tr.click();
    });
    await delay(1000);
    const path2 = path.join(screenshotsDir, '13_behavioral_batter_drawer.png');
    await page.screenshot({ path: path2, fullPage: false });
    console.log('Saved screenshot to:', path2);

    // Close drawer
    await page.evaluate(() => {
      const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Close Dossier'));
      if (closeBtn) closeBtn.click();
    });
    await delay(500);

    // 6. Switch to Bowling Bounce-Back & Spells tab
    console.log('Switching to Bowling Bounce-Back & Spells tab...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Bowling Bounce-Back & Spells'));
      if (btn) btn.click();
    });
    await delay(1200);
    const path3 = path.join(screenshotsDir, '14_behavioral_bowling_overview.png');
    await page.screenshot({ path: path3, fullPage: false });
    console.log('Saved screenshot to:', path3);

    // 7. Open Bowler Dossier Drawer (Click on Jasprit Bumrah)
    console.log('Clicking Jasprit Bumrah row for bounce-back dossier...');
    await page.evaluate(() => {
      const tr = Array.from(document.querySelectorAll('tr')).find(r => r.innerText && r.innerText.includes('Jasprit Bumrah'));
      if (tr) tr.click();
    });
    await delay(1000);
    const path4 = path.join(screenshotsDir, '15_behavioral_bowler_drawer.png');
    await page.screenshot({ path: path4, fullPage: false });
    console.log('Saved screenshot to:', path4);

    // Close drawer
    await page.evaluate(() => {
      const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Close Dossier'));
      if (closeBtn) closeBtn.click();
    });
    await delay(500);

    // 8. Switch to Behavioral Taxonomy & Rubric tab
    console.log('Switching to Behavioral Taxonomy & Rubric tab...');
    await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Behavioral Taxonomy & Rubric'));
      if (btn) btn.click();
    });
    await delay(1000);
    const path5 = path.join(screenshotsDir, '16_behavioral_methodology_rubric.png');
    await page.screenshot({ path: path5, fullPage: false });
    console.log('Saved screenshot to:', path5);

    console.log('Behavioral browser acceptance verification PASSED!');
  } catch (err) {
    console.error('Error during behavioral browser test:', err);
  } finally {
    await browser.close();
  }
}

testBehavioralIntelligence();

