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

    const page = await browser.newPage();
    // Configure the navigation timeout
    await page.setDefaultNavigationTimeout(0);
    // Note: SSL not set up so do not use https!
    // We will wait until the page is fully loaded.
    await page.goto("http://cnn.com", {waitUtil: 'networkidle2'});  // remote: cnn.com
    // Get some metrics. Ref: https://github.com/puppeteer/puppeteer/blob/main/docs/api.md#pagemetrics
    // Ref: https://stackoverflow.com/questions/55938315/how-i-can-calculate-page-fully-load-with-pupppeteer
    const metrics = await page.metrics();
    const timing = await page.evaluate(() => {
      const result = {};
      for (const key of Object.keys(window.performance.timing.__proto__))
          result[key] = window.performance.timing[key];
      return result;
    });
    console.log("Logging metrics to %s", metrics.Timestamp);
    const dir = "/home/pptruser/Downloads/";
    // Code to check if a dir exists and writable
    // fs.access(dir, fs.constants.F_OK | fs.constants.W_OK, (err) => {
    //     if (err) {
    //         console.log("%s doesn't exist or not writable", dir);
    //     } else {
    //         console.log('can write to %s', dir);
    //     }
    // });
    // Create a unique pathname to store metrics data
const path = dir.concat(6, '.json')
    // fs.writeFileSync(path, JSON.stringify(metrics, null, "  "));
    fs.writeFileSync(path, JSON.stringify(timing, null, "  "));
    // fs.appendFileSync(path, JSON.stringify(timing, null, "  "));
    // await page.screenshot({path: "/home/pptruser/Downloads/screenshot.png"});
    await page.close();
    await browser.close();
})();
