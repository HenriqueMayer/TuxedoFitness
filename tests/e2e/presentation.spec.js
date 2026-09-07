const { test, expect } = require('@playwright/test');
test.use({actionTimeout: 10000});

async function login(page) {
  await page.goto('/accounts/login/');
  await page.locator('#id_username').fill('e2e-owner');
  await page.locator('#id_password').fill(process.env.E2E_PASSWORD);
  await page.getByRole('button', {name:'Sign in', exact:true}).click();
  await expect(page).toHaveURL(/dashboard/);
}
async function landingLayout(page, width) {
  const heading = page.locator('#landing-title');
  await expect(heading).toHaveText('Tuxedo Fitness');
  await expect(heading).toHaveCSS('font-size', width >= 1024 ? '60px' : width >= 640 ? '48px' : '36px');
  const layout = await page.locator('[aria-labelledby="landing-title"]').evaluate(el => {
    const [copy, art] = el.children;
    return {columns: getComputedStyle(el).gridTemplateColumns.split(' ').length, copy:copy.getBoundingClientRect().toJSON(), art:art.getBoundingClientRect().toJSON()};
  });
  expect(layout.columns).toBe(width >= 1024 ? 2 : 1);
  if (width >= 1024) expect(layout.art.x).toBeGreaterThan(layout.copy.right);
  const image = page.locator('main img');
  await expect(image).toHaveCSS('object-fit','contain');
  const bounds = await image.boundingBox();
  expect(bounds.height).toBeLessThan(500);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  if (width >= 640) expect((await page.locator('header').boundingBox()).height).toBe(65);
}
async function chartLayout(page) {
  for (const card of await page.locator('[data-chart]').all()) {
    if (await card.locator('[data-chart-plot]').count() === 0) continue; // Explicit empty state.
    await expect(card.locator('[data-chart-plot]')).toHaveCount(1);
    await expect(card.locator('.chart-mobile, .chart-desktop')).toHaveCount(0);
    const invalid = await card.locator('.chart-hit').evaluateAll(hits => hits.filter(hit => hit.getAttribute('fill') !== 'transparent' || getComputedStyle(hit).fill !== 'rgba(0, 0, 0, 0)').length);
    expect(invalid).toBe(0);
    for (const axis of await card.locator('.chart-axis-x, .chart-axis-y').all()) {
      expect(await axis.evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(12);
    }
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
}

test('anonymous Finance layout and every chart topic in both languages and themes', async ({page}, testInfo) => {
  test.setTimeout(120000);
  await page.goto('/');
  for (const language of ['en','pt-br']) {
    await page.locator('[data-language]').selectOption(language);
    await expect(page.locator('html')).toHaveAttribute('lang', language);
    for (const theme of ['light','dark']) {
      const dark = await page.locator('html').evaluate(el => el.classList.contains('dark'));
      if (dark !== (theme === 'dark')) await page.locator('[data-theme-toggle]').click();
      await landingLayout(page,testInfo.project.use.viewport.width);
      await page.screenshot({path:testInfo.outputPath(`${language}-${theme}-public-home.png`),fullPage:true});
    }
  }
  await page.locator('[data-language]').selectOption('en');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await login(page);
  await page.goto('/exercises/?q=Bench+Press');
  await page.locator('a[href^="/exercises/"]').filter({hasText:'Bench Press (Barbell)'}).first().click();
  const progression = await page.locator('a[href^="/dashboard/reports/?panel=progression"]').getAttribute('href');
  for (const language of ['en','pt-br']) {
    await page.locator('[data-language]').selectOption(language);
    await expect(page.locator('html')).toHaveAttribute('lang', language);
    for (const theme of ['light','dark']) {
      const dark = await page.locator('html').evaluate(el => el.classList.contains('dark'));
      if (dark !== (theme === 'dark')) await page.locator('[data-theme-toggle]').click();
      for (const [name, url] of [['overview','/dashboard/'], ...['frequency','progression','effort','volume','distribution','duration'].map(topic => [topic,topic === 'progression' ? progression : `/dashboard/reports/?panel=${topic}`])]) {
        await page.goto(url);
        await chartLayout(page);
        const first=page.locator('[data-chart]').first();
        const points=first.locator('[data-chart-value]');
        if(await points.count()) {
          await points.first().focus();
          await page.keyboard.press('End');
          await expect(points.last()).toBeFocused();
          await expect(first.locator('[data-chart-readout]')).toHaveText(await points.last().getAttribute('data-chart-value'));
        }
        await page.evaluate(() => { document.activeElement.blur(); window.scrollTo(0, 0); });
        await page.screenshot({path:testInfo.outputPath(`${language}-${theme}-${name}.png`),fullPage:true});
        await first.screenshot({path:testInfo.outputPath(`${language}-${theme}-${name}-chart.png`)});
      }
    }
  }
});

test('a tab holding old styles recovers through ordinary HTMX navigation', async ({page},testInfo) => {
  let oldPage = true;
  await page.route('**/', async route => {
    if (route.request().isNavigationRequest() && oldPage && new URL(route.request().url()).pathname === '/') {
      oldPage = false;
      const response = await route.fetch();
      let html = await response.text();
      html = html.replace(/name="frontend-version" content="[^"]+"/, 'name="frontend-version" content="old-version"')
                 .replace(/\/static\/css\/app\.css\?v=[a-f0-9]+/, '/static/css/app.css?v=020');
      await route.fulfill({response,body:html});
    } else await route.continue();
  });
  await page.route('**/static/css/app.css?v=020', route => route.fulfill({contentType:'text/css',body:'body { margin:0; }'}));
  await page.goto('/');
  await expect(page.locator('#landing-title')).not.toHaveCSS('font-size','60px');
  await page.locator('header a[href="/"]').click();
  await expect(page.locator('meta[name="frontend-version"]')).not.toHaveAttribute('content','old-version');
  await landingLayout(page,testInfo.project.use.viewport.width);
  expect(await page.locator('link[rel="stylesheet"]').getAttribute('href')).toMatch(/v=[a-f0-9]{16}$/);
});

test('missing stylesheet cannot paint chart interaction layers black or duplicate plots', async ({page}) => {
  await login(page);
  await page.route('**/static/css/app.css*', route => route.abort());
  await page.goto('/dashboard/');
  for (const hit of await page.locator('.chart-hit').all()) await expect(hit).toHaveCSS('fill','rgba(0, 0, 0, 0)');
  await expect(page.locator('.chart-mobile, .chart-desktop')).toHaveCount(0);
  for (const card of await page.locator('[data-chart]').all()) expect(await card.locator('[data-chart-plot]').count()).toBeLessThanOrEqual(1);
});

test('RPE categories remain individually labelled at every viewport', async ({page},testInfo) => {
  await login(page);
  await page.goto('/dashboard/reports/?panel=effort');
  const chart=page.locator('[aria-labelledby="effort-distribution-heading"]');
  const labels=await chart.locator('.chart-tick-label').allTextContents();
  expect(labels).toEqual(await chart.locator('tbody th').allTextContents());
  expect(labels).toContain('7.5');
  await chartLayout(page);
  await chart.screenshot({path:testInfo.outputPath('rpe-categories.png')});
});
