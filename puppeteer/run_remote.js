const puppeteer = require("puppeteer");
const fs = require('fs');
const path = require('path');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: [
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--no-sandbox",
        ]
    });

    const dir = "/home/pptruser/Downloads/";
    const logpath = dir.concat(2, '.json')
    const times = 10;
    for (let i = 0; i < times; i++) {
      const page = await browser.newPage({ context: "user-" + i });
      // Configure the navigation timeout
      await page.setDefaultNavigationTimeout(0);
      await page.setCacheEnabled(false);
      // We will wait until the page is fully loaded.
      const response = await page.goto("http://stackoverflow.com");//, {waitUtil: 'domcontentloaded'});
      const timing = await page.evaluate(() => {
        const result = {};
        for (const key of Object.keys(window.performance.timing.__proto__))
          result[key] = window.performance.timing[key];
        return result;
      });
      fs.appendFileSync(logpath, JSON.stringify(timing, null, "  "));
      
      // await page.screenshot({path: '/home/pptruser/Downloads/screenshot_' + i + '.png'});
      await page.close();
    }
    await browser.close();
})();

