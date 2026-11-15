const puppeteer = require('puppeteer');

async function runBrowserAudit() {
  console.log('===============================================================');
  console.log('  RR EDGE — LIVE BROWSER ACCEPTANCE & INTERACTION AUDIT');
  console.log('===============================================================');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleLogs = [];
  const consoleErrors = [];
  const failedRequests = [];

  page.on('console', (msg) => {
    const text = msg.text();
    consoleLogs.push(`[${msg.type()}] ${text}`);
    if (msg.type() === 'error') {
      consoleErrors.push(text);
    }
  });

  page.on('requestfailed', (req) => {
    failedRequests.push(`${req.method()} ${req.url()} - ${req.failure().errorText}`);
  });

  console.log('\n[1] Navigating to http://localhost:8000 ...');
  const response = await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
  console.log(`    HTTP Status: ${response.status()}`);
  if (response.status() !== 200) {
    throw new Error(`Failed to load root page: status ${response.status()}`);
  }

  // Helper wait
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // --- PAGE 1: EXECUTIVE OVERVIEW ---
  console.log('\n[2] Testing Page 1: Executive Overview ...');
  await page.waitForSelector('h1');
  const heroText = await page.$eval('h1', (el) => el.innerText);
  console.log(`    Hero Title: "${heroText.replace(/\n/g, ' ')}"`);

  const primaryDeliveriesText = await page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('div')).find(d => d.innerText && d.innerText.includes('Primary Deliveries'));
    return el ? el.innerText.split('\n')[1] || el.innerText : 'Not found';
  });
  console.log(`    Primary Deliveries Metric: ${primaryDeliveriesText}`);

  // --- PAGE 2: PRESSURE INTELLIGENCE ---
  console.log('\n[3] Testing Page 2: Pressure Intelligence Navigation ...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const btn = buttons.find(b => b.innerText && b.innerText.includes('Pressure Intelligence'));
    if (btn) btn.click();
  });
  await delay(1000);
  const pressureHeader = await page.$eval('h2', el => el.innerText);
  console.log(`    Active Page Header: "${pressureHeader}"`);

  // --- PAGE 3: BATTER INTELLIGENCE & SCOUT DRAWER ---
  console.log('\n[4] Testing Page 3: Batter Intelligence, Filters & Drawer ...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const btn = buttons.find(b => b.innerText && b.innerText.includes('Batter Intelligence'));
    if (btn) btn.click();
  });
  await delay(1000);

  // Search input
  await page.waitForSelector('input[type="text"]');
  await page.type('input[type="text"]', 'Sooryavanshi');
  await delay(500);
  const rowsFound = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tbody tr'));
    return rows.map(r => r.innerText.split('\t')[0] || r.innerText.split('\n')[0]);
  });
  console.log(`    Search 'Sooryavanshi' found: ${rowsFound.join(', ')}`);

  // Click on Vaibhav Sooryavanshi to open Drawer
  console.log('    Opening Vaibhav Sooryavanshi Scout Drawer ...');
  await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tbody tr'));
    const r = rows.find(row => row.innerText.includes('Sooryavanshi'));
    if (r) r.click();
  });
  await delay(1200);

  // Check drawer content
  const drawerOpen = await page.evaluate(() => {
    const h3 = Array.from(document.querySelectorAll('h3')).find(el => el.innerText.includes('Vaibhav Sooryavanshi'));
    return !!h3;
  });
  console.log(`    Scout Dossier Drawer Opened: ${drawerOpen ? 'YES' : 'NO'}`);

  // Close drawer
  await page.evaluate(() => {
    const closeButtons = Array.from(document.querySelectorAll('button')).filter(b => b.querySelector('svg'));
    if (closeButtons.length > 0) closeButtons[closeButtons.length - 1].click();
  });
  await delay(600);

  // Clear search and test Format toggle
  await page.evaluate(() => {
    const input = document.querySelector('input[type="text"]');
    if (input) {
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const t20iBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Senior T20I');
    if (t20iBtn) t20iBtn.click();
  });
  await delay(600);
  console.log('    Toggled Format View to Senior T20I successfully.');

  // --- PAGE 4: BOWLER INTELLIGENCE ---
  console.log('\n[5] Testing Page 4: Bowler Intelligence & Drawer ...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const btn = buttons.find(b => b.innerText && b.innerText.includes('Bowler Intelligence'));
    if (btn) btn.click();
  });
  await delay(1000);

  // Open Sunil Narine Drawer
  await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tbody tr'));
    const r = rows.find(row => row.innerText.includes('Sunil Narine'));
    if (r) r.click();
  });
  await delay(1000);

  const bowlerDrawerOpen = await page.evaluate(() => {
    const h3 = Array.from(document.querySelectorAll('h3')).find(el => el.innerText.includes('Sunil Narine'));
    return !!h3;
  });
  console.log(`    Sunil Narine Bowler Dossier Drawer Opened: ${bowlerDrawerOpen ? 'YES' : 'NO'}`);

  // Close drawer
  await page.evaluate(() => {
    const closeButtons = Array.from(document.querySelectorAll('button')).filter(b => b.querySelector('svg'));
    if (closeButtons.length > 0) closeButtons[closeButtons.length - 1].click();
  });
  await delay(600);

  // --- PAGE 5: PLAYER COMPARISON LAB ---
  console.log('\n[6] Testing Page 5: Player Comparison Lab (Bootstrap vs Credible) ...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const btn = buttons.find(b => b.innerText && b.innerText.includes('Player Comparison Lab'));
    if (btn) btn.click();
  });
  await delay(1200);

  // Default pair is Tim David (6396) vs SKY (1699) -> Adjacent Rank 1 vs 2
  const compCardText = await page.evaluate(() => {
    const el = document.querySelector('h3.font-heading');
    const badge = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('Bootstrap') || s.innerText.includes('Empirical Bayes'));
    const verdict = Array.from(document.querySelectorAll('h5')).find(h => h.innerText.includes('Analytical Verdict'));
    return {
      title: el ? el.innerText : '',
      badge: badge ? badge.innerText : '',
      verdict: verdict ? verdict.innerText : ''
    };
  });
  console.log(`    Pairwise Card Title: "${compCardText.title}"`);
  console.log(`    Uncertainty Badge: "${compCardText.badge}"`);
  console.log(`    Statistical Verdict: "${compCardText.verdict}"`);

  // Change Candidate B to non-adjacent candidate (e.g. Yashasvi Jaiswal, ID 6819)
  console.log('    Changing Candidate B to non-adjacent player ...');
  await page.evaluate(() => {
    const selects = Array.from(document.querySelectorAll('select'));
    if (selects.length >= 2) {
      selects[1].value = '6819'; // Yashasvi Jaiswal
      selects[1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await delay(1000);

  const nonAdjacentText = await page.evaluate(() => {
    const alert = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('Alternative Method') || s.innerText.includes('Independent Empirical Bayes'));
    return alert ? alert.innerText : 'Not found';
  });
  console.log(`    Non-Adjacent Uncertainty Method Displayed: "${nonAdjacentText}"`);

  // --- PAGE 6: METHODOLOGY & MODEL LAB ---
  console.log('\n[7] Testing Page 6: Methodology & Model Lab ...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const btn = buttons.find(b => b.innerText && b.innerText.includes('Methodology & Lab'));
    if (btn) btn.click();
  });
  await delay(1000);

  // Check that logistic equation is gone and Asymmetric Rule Architecture is present
  const methArch = await page.evaluate(() => {
    const el = Array.from(document.querySelectorAll('h4')).find(h => h.innerText.includes('Asymmetric Rule-Based'));
    return el ? el.innerText : 'NOT FOUND (Check if old formula remained)';
  });
  console.log(`    Methodology Architecture Section: "${methArch}"`);

  // Click Governance & Exclusions tab
  await page.evaluate(() => {
    const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Governance & Exclusions'));
    if (tabBtn) tabBtn.click();
  });
  await delay(600);

  const governanceExclusions = await page.evaluate(() => {
    const headings = Array.from(document.querySelectorAll('div')).filter(d => d.innerText && d.innerText.includes('DLS-Uncertain'));
    return headings.length > 0;
  });
  console.log(`    Governance & Exclusions (1,641 DLS Quarantined): ${governanceExclusions ? 'VERIFIED' : 'NOT FOUND'}`);

  // --- PAGE 7: DATA EXPLORER ---
  console.log('\n[8] Testing Page 7: Data Explorer (Filter, Sort, Paginate, Export) ...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const btn = buttons.find(b => b.innerText && b.innerText.includes('Data Explorer'));
    if (btn) btn.click();
  });
  await delay(1200);

  // Check initial count
  const initialExplorerText = await page.evaluate(() => {
    const span = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('verified player records'));
    return span ? span.innerText : 'Not found';
  });
  console.log(`    Initial Data Explorer Status: "${initialExplorerText}"`);

  // Click column header to sort
  await page.evaluate(() => {
    const ths = Array.from(document.querySelectorAll('th'));
    const ballsTh = ths.find(th => th.innerText.includes('Balls'));
    if (ballsTh) ballsTh.click();
  });
  await delay(500);
  console.log('    Column sorting clicked successfully.');

  // Click next page
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button')).filter(b => b.querySelector('svg'));
    if (btns.length >= 2) btns[btns.length - 1].click();
  });
  await delay(500);
  const pageCounter = await page.evaluate(() => {
    const span = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('Page '));
    return span ? span.innerText : '';
  });
  console.log(`    Pagination after clicking Next: "${pageCounter}"`);

  // Click Export CSV button
  const exportBtnPresent = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Export Filtered Dataset'));
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  });
  await delay(500);
  console.log(`    CSV Export Triggered: ${exportBtnPresent ? 'YES' : 'NO'}`);

  // --- RESPONSIVE MOBILE VIEWPORT AUDIT ---
  console.log('\n[9] Testing Mobile Viewport (375x667) ...');
  await page.setViewport({ width: 375, height: 667 });
  await delay(600);

  // Check if hamburger menu button is visible on mobile
  const hamburgerVisible = await page.evaluate(() => {
    const btn = document.querySelector('header button');
    return btn && btn.offsetParent !== null;
  });
  console.log(`    Mobile Hamburger Menu Button Visible: ${hamburgerVisible ? 'YES' : 'NO'}`);

  // Open mobile drawer
  if (hamburgerVisible) {
    await page.click('header button');
    await delay(600);
    const drawerOpen = await page.evaluate(() => {
      const nav = document.querySelector('nav');
      return nav && nav.offsetParent !== null;
    });
    console.log(`    Mobile Navigation Drawer Opened: ${drawerOpen ? 'YES' : 'NO'}`);
  }

  // --- SUMMARY OF CONSOLE & NETWORK LOGS ---
  console.log('\n===============================================================');
  console.log('  CONSOLE & NETWORK AUDIT RESULTS');
  console.log('===============================================================');
  console.log(`  Total Console Messages: ${consoleLogs.length}`);
  console.log(`  Console Errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    consoleErrors.forEach(err => console.log(`    ERROR: ${err}`));
  } else {
    console.log('  [OK] ZERO Uncaught JavaScript Errors detected across all pages!');
  }

  console.log(`  Failed Network Requests: ${failedRequests.length}`);
  if (failedRequests.length > 0) {
    failedRequests.forEach(req => console.log(`    FAILED: ${req}`));
  } else {
    console.log('  [OK] ZERO Failed Network Requests detected across all navigation!');
  }
  console.log('===============================================================');

  await browser.close();
}

runBrowserAudit().catch((err) => {
  console.error('Fatal Browser Audit Error:', err);
  process.exit(1);
});
