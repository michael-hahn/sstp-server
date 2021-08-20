const puppeteer = require("puppeteer");

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: [
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
          //"--no-sandbox",
        ]
    });

    const page = await browser.newPage();
    // Note: SSL not set up so do not use https!
    await page.goto("http://172.18.0.5");  // 172.18.0.5 is the flask application's IP
    // await page.screenshot({path: "screenshot.png"});

    await page.close();
    await browser.close();
})();
