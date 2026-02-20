const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'], headless: true });
  const page = await browser.newPage();
  try {
    await page.goto('http://localhost:5173/', { waitUntil: 'networkidle2', timeout: 15000 });

    // Wait for city input
    await page.waitForSelector('input[placeholder="Digite o nome da cidade"]', { timeout: 8000 });
    await page.type('input[placeholder="Digite o nome da cidade"]', 'Salvador', { delay: 100 });

    // Wait for suggestion item containing 'Salvador'
    await page.waitForFunction(() => {
      const nodes = Array.from(document.querySelectorAll('div'));
      return nodes.some(n => n.textContent && n.textContent.includes('Salvador'));
    }, { timeout: 8000 });

    // Click the first suggestion that includes 'Salvador'
    await page.evaluate(() => {
      const nodes = Array.from(document.querySelectorAll('div'));
      const target = nodes.find(n => n.textContent && n.textContent.includes('Salvador'));
      if (target) target.click();
    });

    // Wait for formatted address to appear in the page text
    const found = await page.waitForFunction(() => document.body.innerText.includes('Salvador - BA, Brasil'), { timeout: 8000 }).catch(() => null);

    if (found) {
      console.log('FRONTEND TEST: PASS - selection produced formatted address');
    } else {
      console.error('FRONTEND TEST: FAIL - formatted address not found after selection');
      console.log('BODY SNIPPET:\n', await page.evaluate(() => document.body.innerText.slice(0, 2000)));
      process.exitCode = 2;
    }
  } catch (err) {
    console.error('FRONTEND TEST: ERROR', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
