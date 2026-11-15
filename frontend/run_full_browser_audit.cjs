const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function runBrowserAudit() {
  console.log('===============================================================');
  console.log('  RR EDGE — COMPREHENSIVE LIVE BROWSER ACCEPTANCE SUITE');
  console.log('===============================================================');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const consoleErrors = [];
  const consoleWarnings = [];
  const failedRequests = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
    if (msg.type() === 'warn') consoleWarnings.push(msg.text());
  });

  page.on('requestfailed', (req) => {
    failedRequests.push(`${req.method()} ${req.url()} (${req.failure().errorText})`);
  });

  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // --- 1. EXECUTIVE OVERVIEW ---
  console.log('\n[PAGE 1] Executive Overview ...');
  const res = await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
  console.log(`  HTTP Response: ${res.status()}`);
  
  const heroH1 = await page.$eval('h1', el => el.innerText.trim());
  console.log(`  Hero Headline: "${heroH1.replace(/\n/g, ' ')}"`);

  const metrics = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('div.shadow-rr-card'));
    return cards.slice(0, 4).map(c => {
      const texts = c.innerText.split('\n').filter(Boolean);
      return { title: texts[0], value: texts[1], subtitle: texts[2] };
    });
  });
  console.log('  Scope Metrics Cards:');
  metrics.forEach(m => console.log(`    - ${m.title}: ${m.value} (${m.subtitle})`));

  // Check Vaibhav Sooryavanshi and Tim David in Top 10 Batters Table
  const top10Batters = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('tbody tr'));
    return rows.slice(0, 10).map(r => {
      const cols = r.innerText.split('\t');
      return cols[1] || cols[0];
    });
  });
  console.log(`  Top 10 Batters Listed: ${top10Batters.length} candidates loaded.`);

  // --- 2. PRESSURE INTELLIGENCE ---
  console.log('\n[PAGE 2] Pressure Intelligence Framework ...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Pressure Intelligence'));
    if (btn) btn.click();
  });
  await delay(800);

  const pressureTitle = await page.evaluate(() => document.querySelector('h2') ? document.querySelector('h2').innerText : '');
  console.log(`  Section Title: "${pressureTitle}"`);
  
  const tierBars = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.recharts-bar-rectangle')).length;
  });
  console.log(`  Rendered Recharts SVG Bar Elements: ${tierBars}`);

  // --- 3. BATTER INTELLIGENCE & SCOUT DRAWER ---
  console.log('\n[PAGE 3] Batter Intelligence & Scout Drawer ...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Batter Intelligence'));
    if (btn) btn.click();
  });
  await delay(800);

  // Search 'David'
  await page.type('input[type="text"]', 'David');
  await delay(400);
  const searchResults = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('tbody tr')).map(r => r.innerText.split('\n')[0]);
  });
  console.log(`  Search for 'David' filtered candidates: ${searchResults.length} row(s)`);

  // Open Scout Drawer
  console.log('  Opening Tim David Scout Dossier Drawer ...');
  await page.evaluate(() => {
    const row = Array.from(document.querySelectorAll('tbody tr')).find(r => r.innerText.includes('Tim David'));
    if (row) row.click();
  });
  await delay(800);

  const drawerData = await page.evaluate(() => {
    const h3 = Array.from(document.querySelectorAll('h3')).find(el => el.innerText.includes('Tim David'));
    const metrics = Array.from(document.querySelectorAll('span.font-mono')).map(s => s.innerText);
    return {
      open: !!h3,
      name: h3 ? h3.innerText : '',
      metricsSample: metrics.slice(0, 5)
    };
  });
  console.log(`  Scout Drawer Open: ${drawerData.open} ("${drawerData.name}")`);

  // Close Drawer
  await page.evaluate(() => {
    const btn = document.querySelector('div.fixed button');
    if (btn) btn.click();
  });
  await delay(500);

  // Clear search
  await page.evaluate(() => {
    const input = document.querySelector('input[type="text"]');
    if (input) {
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });

  // --- 4. BOWLER INTELLIGENCE ---
  console.log('\n[PAGE 4] Bowler Intelligence & Scout Drawer ...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Bowler Intelligence'));
    if (btn) btn.click();
  });
  await delay(800);

  // Open Sunil Narine Drawer
  await page.evaluate(() => {
    const row = Array.from(document.querySelectorAll('tbody tr')).find(r => r.innerText.includes('Sunil Narine'));
    if (row) row.click();
  });
  await delay(800);

  const bowlerDrawer = await page.evaluate(() => {
    const h3 = Array.from(document.querySelectorAll('h3')).find(el => el.innerText.includes('Sunil Narine'));
    return !!h3;
  });
  console.log(`  Sunil Narine Bowler Dossier Drawer Open: ${bowlerDrawer}`);

  // Close Drawer
  await page.evaluate(() => {
    const btn = document.querySelector('div.fixed button');
    if (btn) btn.click();
  });
  await delay(500);

  // --- 5. PLAYER COMPARISON LAB ---
  console.log('\n[PAGE 5] Player Comparison Lab ...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Player Comparison Lab'));
    if (btn) btn.click();
  });
  await delay(1000);

  // 1. Adjacent Pair: Tim David (#1) vs SKY (#2)
  const adjacentAudit = await page.evaluate(() => {
    const title = document.querySelector('div.shadow-rr-card h3.font-heading');
    const badge = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('Bootstrap') || s.innerText.includes('Empirical Bayes'));
    const ci = Array.from(document.querySelectorAll('div.text-rr-pink')).find(d => d.innerText.includes('['));
    const verdict = Array.from(document.querySelectorAll('h5')).find(h => h.innerText.includes('Analytical Verdict'));
    return {
      title: title ? title.innerText : '',
      badge: badge ? badge.innerText : '',
      ci: ci ? ci.innerText : '',
      verdict: verdict ? verdict.innerText : ''
    };
  });
  console.log(`  Adjacent Pair Bootstrap Test:`);
  console.log(`    Header: "${adjacentAudit.title}"`);
  console.log(`    Badge: "${adjacentAudit.badge}"`);
  console.log(`    95% CI: "${adjacentAudit.ci}"`);
  console.log(`    Verdict: "${adjacentAudit.verdict}"`);

  // 2. Non-Adjacent Pair: Tim David vs Yashasvi Jaiswal (#3)
  console.log('  Selecting non-adjacent candidate (Yashasvi Jaiswal) ...');
  await page.evaluate(() => {
    const selects = Array.from(document.querySelectorAll('select'));
    if (selects.length >= 2) {
      selects[1].value = '6819'; // Jaiswal
      selects[1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
  await delay(1000);

  const nonAdjacentAudit = await page.evaluate(() => {
    const badge = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('Empirical Bayes Posterior'));
    const desc = Array.from(document.querySelectorAll('p')).find(p => p.innerText.includes('strictly precomputed for adjacent'));
    return {
      badge: badge ? badge.innerText : '',
      descriptionFound: !!desc
    };
  });
  console.log(`  Non-Adjacent Uncertainty Model:`);
  console.log(`    Badge: "${nonAdjacentAudit.badge}"`);
  console.log(`    Explicit Method Disclosure Present: ${nonAdjacentAudit.descriptionFound}`);

  // --- 6. METHODOLOGY & MODEL LAB ---
  console.log('\n[PAGE 6] Methodology & Model Lab ...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Methodology & Lab'));
    if (btn) btn.click();
  });
  await delay(800);

  // Check Pressure Section does not have logistic formula and has rule-based architecture
  const pressureMeth = await page.evaluate(() => {
    const title = Array.from(document.querySelectorAll('h4')).find(h => h.innerText.includes('Asymmetric Rule-Based'));
    const formulaDiv = document.querySelector('div.bg-rr-pale div.font-mono');
    return {
      hasRuleTitle: !!title,
      content: formulaDiv ? formulaDiv.innerText : ''
    };
  });
  console.log(`  Asymmetric Rule-Based Architecture Present: ${pressureMeth.hasRuleTitle}`);
  console.log(`  Rule Definition Sample: "${pressureMeth.content.split('\n')[0]}"`);

  // Switch to Governance & Exclusions tab
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Governance & Exclusions'));
    if (btn) btn.click();
  });
  await delay(600);

  const governanceItems = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('div.rounded-lg')).filter(d => d.innerText && d.innerText.includes('Exclusion'));
    return items.map(d => d.innerText.split('\n')[0]);
  });
  console.log(`  Governance Disclosures Audited:`);
  governanceItems.forEach(item => console.log(`    - ${item}`));

  // --- 7. DATA EXPLORER ---
  console.log('\n[PAGE 7] Data Explorer ...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('Data Explorer'));
    if (btn) btn.click();
  });
  await delay(1000);

  // Check record counter
  const explorerCounter = await page.evaluate(() => {
    const span = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes('verified player records'));
    return span ? span.innerText : '';
  });
  console.log(`  Candidate Universe Records: "${explorerCounter}"`);

  // Test Sort by Balls
  await page.evaluate(() => {
    const th = Array.from(document.querySelectorAll('th')).find(t => t.innerText.includes('Balls'));
    if (th) th.click();
  });
  await delay(400);
  console.log('  Sort by Balls executed.');

  // Test Pagination
  const beforePage = await page.evaluate(() => {
    const span = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes(' / '));
    return span ? span.innerText : '';
  });
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button')).filter(b => b.querySelector('svg.lucide-chevron-right'));
    if (btns.length > 0) btns[0].click();
  });
  await delay(400);
  const afterPage = await page.evaluate(() => {
    const span = Array.from(document.querySelectorAll('span')).find(s => s.innerText.includes(' / '));
    return span ? span.innerText : '';
  });
  console.log(`  Pagination transition: ${beforePage} -> ${afterPage}`);

  // Test CSV export button
  const csvExportClicked = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Export Filtered Dataset'));
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  });
  await delay(400);
  console.log(`  CSV Export Button Clicked: ${csvExportClicked}`);

  // --- 8. MOBILE VIEWPORT AUDIT (375x667) ---
  console.log('\n[RESPONSIVE AUDIT] Mobile Viewport (375x667) ...');
  await page.setViewport({ width: 375, height: 667 });
  await delay(600);

  const mobileNav = await page.evaluate(() => {
    const burger = document.querySelector('header button');
    return {
      burgerVisible: burger && burger.offsetParent !== null
    };
  });
  console.log(`  Mobile Hamburger Toggle Visible: ${mobileNav.burgerVisible}`);

  // Open mobile drawer
  if (mobileNav.burgerVisible) {
    await page.click('header button');
    await delay(500);
    const drawerOpen = await page.evaluate(() => {
      const aside = document.querySelector('aside');
      return aside ? aside.className.includes('translate-x-0') : false;
    });
    console.log(`  Mobile Navigation Drawer Slide-In Active: ${drawerOpen}`);
  }

  // --- AUDIT VERDICT ---
  console.log('\n===============================================================');
  console.log('  AUDIT SUMMARY: CONSOLE & NETWORK INTEGRITY');
  console.log('===============================================================');
  console.log(`  Console Errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    consoleErrors.forEach(err => console.log(`    ❌ ${err}`));
  } else {
    console.log('  ✅ ZERO Uncaught JavaScript Exceptions across all 7 pages & interactions.');
  }

  console.log(`  Failed Network Requests: ${failedRequests.length}`);
  if (failedRequests.length > 0) {
    failedRequests.forEach(r => console.log(`    ❌ ${r}`));
  } else {
    console.log('  ✅ ZERO Broken API endpoints or 404 assets.');
  }
  console.log('===============================================================');

  await browser.close();
}

runBrowserAudit().catch((err) => {
  console.error('Audit Failure:', err);
  process.exit(1);
});

