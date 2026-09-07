const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { pathToFileURL } = require('url');
const root = path.resolve(__dirname, '../../preview');
let server, baseURL;
test.beforeAll(async () => {
  server = http.createServer((req, res) => {
    const file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname);
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404); res.end(); return;
    }
    const types = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.png':'image/png', '.woff2':'font/woff2'};
    res.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  baseURL = `http://127.0.0.1:${server.address().port}`;
});
test.afterAll(async () => { await new Promise(resolve => server.close(resolve)); });
for (const mode of ['file', 'http']) {
  for (const language of ['en', 'pt-br']) {
    test(`${mode}: explicit filenames and synthetic tour ${language}`, async ({ browser }) => {
      const context = await browser.newContext({javaScriptEnabled:false, viewport:{width:390,height:844}});
      const page = await context.newPage();
      const filename = language === 'en' ? 'index.html' : 'pt-br/index.html';
      await page.goto(mode === 'file' ? pathToFileURL(path.join(root, filename)).href : `${baseURL}/${filename}`);
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('img')).toHaveCount(6);
      for (const image of await page.locator('img').all()) {
        await image.scrollIntoViewIfNeeded();
        expect(await image.evaluate(img => img.complete && img.naturalWidth > 0)).toBeTruthy();
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      await page.getByRole('link', {name:language === 'en' ? 'Português (Brasil)' : 'English',exact:true}).click();
      await expect(page).toHaveURL(/index\.html$/);
      await expect(page.locator('html')).toHaveAttribute('lang', language === 'en' ? 'pt-br' : 'en');
      await context.close();
    });
  }
}
