const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function runAudit() {
  const screenshotDir = path.resolve(__dirname, '..', 'reports', 'screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const consoleLogs = [];
  const failedRequests = [];

  console.log('--- Starting Comprehensive Puppeteer Browser Interaction Audit ---');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  page.on('console', (msg) => {
    const text = msg.text();
    const type = msg.type();
    consoleLogs.push({ type, text });
    if (type === 'error' && !text.includes('favicon')) {
      console.error(`[Browser Console Error]: ${text}`);
    }
  });

  page.on('requestfailed', (req) => {
    const url = req.url();
    const failure = req.failure();
    failedRequests.push({ url, errorText: failure ? failure.errorText : 'Unknown' });
    console.error(`[Browser Network Failed]: ${url} - ${failure ? failure.errorText : ''}`);
  });

  try {
    // 1. Load Application
    console.log('Navigating to http://127.0.0.1:8000 ...');
    await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle0', timeout: 30000 });
    console.log('Loaded: ', await page.title());

    // 2. Scenario Lab Audit
    console.log('Clicking Scenario Lab in sidebar...');
    await page.evaluate(() => {
      const navBtns = Array.from(document.querySelectorAll('nav button'));
      const btn = navBtns.find((b) => b.textContent.includes('Scenario Lab'));
      if (btn) btn.click();
    });

    await page.waitForFunction(
      () => document.querySelector('h1') && document.querySelector('h1').textContent.includes('Scenario Lab'),
      { timeout: 10000 }
    );
    await new Promise((r) => setTimeout(r, 2000));

    const scenarioLabShot = path.join(screenshotDir, '01_scenario_lab_desktop.png');
    await page.screenshot({ path: scenarioLabShot, fullPage: false });
    console.log(`Saved screenshot: ${scenarioLabShot}`);

    // Switch scenario discipline to Batting Scenarios
    console.log('Switching to Batting Scenarios...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const batBtn = buttons.find((b) => b.textContent.includes('Batting Scenarios'));
      if (batBtn) batBtn.click();
    });
    await new Promise((r) => setTimeout(r, 2000));

    // Select two players for comparison
    console.log('Selecting 2 players for head-to-head comparison...');
    const selectedCount = await page.evaluate(() => {
      const checkboxes = Array.from(document.querySelectorAll('table tbody input[type="checkbox"]'));
      if (checkboxes.length >= 2) {
        checkboxes[0].click();
        checkboxes[1].click();
        return 2;
      }
      return 0;
    });

    if (selectedCount === 2) {
      await new Promise((r) => setTimeout(r, 500));
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const compBtn = buttons.find((b) => b.textContent.includes('Compare Selected'));
        if (compBtn) compBtn.click();
      });

      await new Promise((r) => setTimeout(r, 2500)); // Wait for comparison modal
      const compareShot = path.join(screenshotDir, '02_scenario_compare_modal.png');
      await page.screenshot({ path: compareShot, fullPage: false });
      console.log(`Saved screenshot: ${compareShot}`);

      // Close comparison modal
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const closeBtn = buttons.find((b) => b.textContent === '✕' || b.textContent.includes('Close Comparison'));
        if (closeBtn) closeBtn.click();
      });
      await new Promise((r) => setTimeout(r, 500));
    }

    // 3. Custom Scenario Builder
    console.log('Opening Custom Scenario Builder...');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const customBtn = buttons.find((b) => b.textContent.includes('Custom Scenario Builder'));
      if (customBtn) customBtn.click();
    });
    await new Promise((r) => setTimeout(r, 1000));
    const customShot = path.join(screenshotDir, '03_scenario_custom_builder.png');
    await page.screenshot({ path: customShot, fullPage: false });
    console.log(`Saved screenshot: ${customShot}`);

    // Close custom modal
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const closeBtn = buttons.find((b) => b.textContent === '✕' || b.textContent.includes('Cancel'));
      if (closeBtn) closeBtn.click();
    });
    await new Promise((r) => setTimeout(r, 500));

    // 4. Player Gallery Audit
    console.log('Navigating to Player Gallery...');
    await page.evaluate(() => {
      const navBtns = Array.from(document.querySelectorAll('nav button'));
      const btn = navBtns.find((b) => b.textContent.includes('Player Gallery'));
      if (btn) btn.click();
    });

    await page.waitForFunction(
      () => document.querySelector('h1') && document.querySelector('h1').textContent.includes('Player Intelligence Gallery'),
      { timeout: 10000 }
    );
    await new Promise((r) => setTimeout(r, 2000));

    // Search for Jasprit Bumrah
    console.log('Searching for Jasprit Bumrah in Player Gallery...');
    await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input'));
      const searchInput = inputs.find((i) => i.placeholder && i.placeholder.includes('Search player'));
      if (searchInput) {
        searchInput.value = 'Jasprit Bumrah';
        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await new Promise((r) => setTimeout(r, 1500));

    const galleryShot = path.join(screenshotDir, '04_player_gallery_desktop.png');
    await page.screenshot({ path: galleryShot, fullPage: false });
    console.log(`Saved screenshot: ${galleryShot}`);

    // Click on Jasprit Bumrah card to open complete 12-section dossier
    console.log('Opening player dossier modal for Jasprit Bumrah...');
    await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('div.cursor-pointer'));
      if (cards.length > 0) {
        cards[0].click();
      }
    });
    await new Promise((r) => setTimeout(r, 3000)); // Allow complete dossier sections to populate

    const dossierShot = path.join(screenshotDir, '05_player_dossier_modal.png');
    await page.screenshot({ path: dossierShot, fullPage: false });
    console.log(`Saved screenshot: ${dossierShot}`);

    // Close dossier modal
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const closeBtn = buttons.find((b) => b.textContent === '✕');
      if (closeBtn) closeBtn.click();
    });
    await new Promise((r) => setTimeout(r, 500));

    // 5. Behavioral Intelligence (Dynamics) Audit
    console.log('Navigating to Behavioral Dynamics...');
    await page.evaluate(() => {
      const navBtns = Array.from(document.querySelectorAll('nav button'));
      const btn = navBtns.find((b) => b.textContent.includes('Behavioral Dynamics'));
      if (btn) btn.click();
    });
    await new Promise((r) => setTimeout(r, 2000));
    const behShot = path.join(screenshotDir, '06_behavioral_intelligence_desktop.png');
    await page.screenshot({ path: behShot, fullPage: false });
    console.log(`Saved screenshot: ${behShot}`);

    // 6. Mobile Viewport Audit (390x844 iPhone 14)
    console.log('Configuring Mobile Viewport (390x844)...');
    await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    await new Promise((r) => setTimeout(r, 1000));

    // In mobile view, navigate to Scenario Lab
    console.log('Opening mobile navigation drawer...');
    await page.evaluate(() => {
      const headerBtns = Array.from(document.querySelectorAll('header button'));
      if (headerBtns.length > 0) headerBtns[0].click(); // Hamburger button
    });
    await new Promise((r) => setTimeout(r, 800));

    await page.evaluate(() => {
      const navBtns = Array.from(document.querySelectorAll('aside nav button'));
      const btn = navBtns.find((b) => b.textContent.includes('Scenario Lab'));
      if (btn) btn.click();
    });
    await new Promise((r) => setTimeout(r, 2000));

    const mobileScenarioShot = path.join(screenshotDir, '07_scenario_lab_mobile.png');
    await page.screenshot({ path: mobileScenarioShot, fullPage: false });
    console.log(`Saved screenshot: ${mobileScenarioShot}`);

    // Navigate to Player Gallery on mobile
    await page.evaluate(() => {
      const headerBtns = Array.from(document.querySelectorAll('header button'));
      if (headerBtns.length > 0) headerBtns[0].click(); // Hamburger
    });
    await new Promise((r) => setTimeout(r, 800));

    await page.evaluate(() => {
      const navBtns = Array.from(document.querySelectorAll('aside nav button'));
      const btn = navBtns.find((b) => b.textContent.includes('Player Gallery'));
      if (btn) btn.click();
    });
    await new Promise((r) => setTimeout(r, 2000));

    const mobileGalleryShot = path.join(screenshotDir, '08_player_gallery_mobile.png');
    await page.screenshot({ path: mobileGalleryShot, fullPage: false });
    console.log(`Saved screenshot: ${mobileGalleryShot}`);

    console.log('--- Browser Interaction Audit Complete ---');
    console.log(`Total Console Messages Logged: ${consoleLogs.length}`);
    console.log(`Total Failed Network Requests: ${failedRequests.length}`);

    const criticalErrors = consoleLogs.filter((c) => c.type === 'error' && !c.text.includes('favicon'));
    console.log(`Critical Console Errors: ${criticalErrors.length}`);
    if (criticalErrors.length > 0) {
      console.log('Console Errors:', JSON.stringify(criticalErrors, null, 2));
    }
    if (failedRequests.length > 0) {
      console.log('Failed Requests:', JSON.stringify(failedRequests, null, 2));
    }
  } catch (err) {
    console.error('Audit encountered an exception:', err);
  } finally {
    await browser.close();
  }
}

runAudit();
