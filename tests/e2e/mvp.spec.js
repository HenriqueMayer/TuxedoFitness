const { test, expect } = require('@playwright/test');
async function login(page) {
  await page.goto('/accounts/login/');
  await page.locator('#id_username').fill('e2e-owner');
  await page.locator('#id_password').fill(process.env.E2E_PASSWORD);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/dashboard/);
}
async function fits(page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth+1)).toBeTruthy();
}
for (const language of ['en', 'pt-br']) {
  test(`${language} full local journey, themes, menus, profile and immutable prompt`, async ({ page }, testInfo) => {
    const errors=[];page.on('pageerror', error=>errors.push(error.message));
    await login(page);
    await page.locator('[data-language]').selectOption(language);
    await expect(page.locator('html')).toHaveAttribute('lang',language);
    for (const theme of ['light','dark']) {
      if (theme==='dark') await page.locator('[data-theme-toggle]').click();
      for (const route of ['/dashboard/','/dashboard/reports/?panel=effort','/history/','/routines/','/exercises/','/planning/','/planning/generations/','/accounts/settings/','/sync/']) {
        await page.goto(route);await expect(page.locator('h1')).toBeVisible();await fits(page);
        if(route==='/dashboard/') await page.screenshot({path:testInfo.outputPath(`${language}-${theme}.png`)});
      }
    }
    await page.goto('/dashboard/reports/');
    await page.getByText(language==='en'?'Customize panels and favorites':'Personalizar painéis e favoritos',{exact:true}).click();
    await page.locator('#id_position_1').selectOption('effort');
    await page.locator('#id_position_3').selectOption('frequency');
    await page.getByRole('button',{name:language==='en'?'Save preferences':'Salvar preferências',exact:true}).click();
    await page.getByText(language==='en'?'Customize panels and favorites':'Personalizar painéis e favoritos',{exact:true}).click();
    await expect(page.locator('#id_position_1')).toHaveValue('effort');
    await page.goto('/planning/');
    await page.locator('#id_comments').fill('Synthetic request: keep familiar exercises.');
    await page.locator('#id_period_mode').selectOption('workouts');
    await expect(page.locator('#id_count')).toBeVisible();
    await expect(page.locator('#id_start')).toBeHidden();
    await page.locator('#id_count').fill('5');
    await page.getByRole('button',{name:language==='en'?'Preview complete prompt':'Conferir prompt completo'}).click();
    await expect(page.locator('textarea[readonly]')).toContainText('synthetic-workout');
    await page.getByRole('button',{name:language==='en'?'Save this generation':'Salvar esta geração'}).click();
    await expect(page).toHaveURL(/generations\/[-a-f0-9]+\//);
    await expect(page.locator('textarea')).toContainText('{{HEVY_API_KEY}}');
    await fits(page);
    const menu=page.locator('#menu-btn');
    if (await menu.isVisible()) {
      await menu.click();await expect(page.locator('#mobile-menu')).toHaveAttribute('aria-hidden','false');
      await page.keyboard.press('Escape');await expect(menu).toBeFocused();
    }
    expect(errors).toEqual([]);
  });
}
test('same-path filters preserve focus and scroll, SVG has keyboard data table', async ({page})=>{
  await login(page);
  await page.goto('/history/');
  await page.locator('#history-query').fill('Strength');
  await page.locator('button').filter({hasText:'Apply filters'}).focus();
  const before=await page.evaluate(()=>window.scrollY);
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/q=Strength/);
  await expect(page.getByRole('button',{name:'Apply filters',exact:true})).toBeFocused();
  expect(Math.abs(await page.evaluate(()=>window.scrollY)-before)).toBeLessThan(5);
  await page.goto('/dashboard/reports/?panel=effort');
  await expect(page.locator('svg [tabindex="0"]').first()).toBeAttached();
  await page.locator('svg [tabindex="0"]').first().focus();
  await expect(page.locator('svg [tabindex="0"]').first()).toBeFocused();
  await page.getByText('Data table and definition',{exact:true}).first().click();
  await expect(page.locator('table').first()).toBeVisible();
});
test('no JavaScript: login, filters, prompt, native language form and connection fallback', async ({browser,baseURL},testInfo)=>{
  const context=await browser.newContext({javaScriptEnabled:false,baseURL,viewport:testInfo.project.use.viewport});
  const page=await context.newPage();await login(page);
  await page.goto('/history/?set_type=normal');await expect(page.locator('h1')).toContainText('Training history');
  if (testInfo.project.name !== 'desktop') { await page.locator('noscript nav').getByRole('link',{name:'Generate prompt',exact:true}).click(); } else { await page.goto('/planning/'); }
  await page.locator('#id_period_mode').selectOption('last_7_days');
  await page.getByRole('button',{name:'Preview complete prompt'}).click();
  await expect(page.locator('textarea[readonly]')).toContainText('synthetic-workout');
  await page.locator('[data-language]').selectOption('pt-br');
  await page.getByRole('button',{name:'Apply',exact:true}).click();
  await expect(page.locator('html')).toHaveAttribute('lang','pt-br');
  await context.close();
});
