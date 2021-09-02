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
    // Note: SSL not set up so do not use https!
    await page.goto("http://172.18.0.5");  // 172.18.0.5 is the flask application's IP
    // Get some metrics. Ref: https://github.com/puppeteer/puppeteer/blob/main/docs/api.md#pagemetrics
    const metrics = await page.metrics();
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
    const path = dir.concat("metrics-", metrics.Timestamp.toString(), ".json");
    fs.writeFileSync(path, JSON.stringify(metrics, null, "  "));
    // await page.screenshot({path: "screenshot.png"});

    await page.close();
    await browser.close();
})();
