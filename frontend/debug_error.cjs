const puppeteer = require('puppeteer');

async function testPages() {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('CONSOLE ERROR:', msg.text());
    }
  });

  page.on('pageerror', err => {
    console.log('PAGE ERROR STACK:', err.stack);
  });

  console.log('Testing each navigation target...');
  await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
  console.log('1. Executive Overview loaded.');

  const clickNav = async (label) => {
    console.log(`Clicking ${label}...`);
    await page.evaluate((l) => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes(l));
      if (btn) btn.click();
    }, label);
    await new Promise(r => setTimeout(r, 800));
  };

  await clickNav('Pressure Intelligence');
  await clickNav('Batter Intelligence');
  await clickNav('Bowler Intelligence');
  await clickNav('Player Comparison Lab');
  await clickNav('Methodology & Lab');
  await clickNav('Data Explorer');

  console.log('Done testing all pages.');
  await browser.close();
}

testPages().catch(console.error);

