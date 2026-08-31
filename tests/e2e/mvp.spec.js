const { test, expect } = require('@playwright/test');
const pageErrors = new WeakMap();

async function login(page) {
  await page.goto('/conta/entrar/');
  await page.getByLabel('Usuário').fill('e2e-owner');
  await page.getByLabel('Senha').fill('Synthetic-e2e-password-274');
  await page.getByRole('button', { name: 'Entrar' }).click();
  await expect(page.getByRole('heading', { name: /Olá, e2e-owner/ })).toBeVisible();
}

async function expectNoOverflow(page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow).toBe(false);
}

test.describe('public surfaces', () => {
  test('landing page explains the local product without personal data', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Seu histórico de treino/ })).toBeVisible();
    await expect(page.getByLabel('Prévia sintética do painel')).toBeVisible();
    await expect(page.getByText('nenhum dado pessoal', { exact: false })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Entrar' }).first()).toBeVisible();
    await expectNoOverflow(page);
  });

  test('login and closed signup screens are explicit', async ({ page }) => {
    await page.goto('/conta/entrar/');
    await expect(page.getByRole('heading', { name: 'Entrar.' })).toBeVisible();
    await page.goto('/conta/cadastro/');
    await expect(page.getByRole('heading', { name: 'Novos cadastros estão desativados.' })).toBeVisible();
    await expect(page.locator('#main-content').getByRole('link', { name: 'Entrar' })).toBeVisible();
    await expectNoOverflow(page);
  });
});

test.describe('authenticated surfaces', () => {
  test.beforeEach(async ({ page }) => {
    const errors = [];
    pageErrors.set(page, errors);
    page.on('console', message => {
      if (message.type() === 'error') errors.push(message.text());
    });
    page.on('pageerror', error => errors.push(error.message));
    await login(page);
  });

  test.afterEach(async ({ page }) => {
    expect(pageErrors.get(page)).toEqual([]);
  });

  test('overview is responsive, local, and accessible', async ({ page }) => {
    await expect(page.getByRole('region', { name: 'Indicadores principais' })).toBeVisible();
    await expect(page.getByRole('img', { name: /Treinos por semana/ })).toBeVisible();
    await expect(page.getByText('tabela equivalente', { exact: false }).first()).toBeAttached();
    await expect(page.getByText('Atualizando indicadores…')).toHaveAttribute('aria-hidden', 'true');
    await expectNoOverflow(page);
  });

  test('boosted primary navigation preserves the document and has no overflow', async ({ page }, testInfo) => {
    const routes = [
      ['Histórico', 'Histórico'],
      ['Exercícios', 'Exercícios'],
      ['Rotinas', 'Rotinas'],
      ['Sincronização', 'Sincronização'],
      ['Configurações', 'Configurações'],
    ];
    await page.evaluate(() => { window.__tuxedoNavigationMarker = 'preserved'; });
    for (const [link, heading] of routes) {
      if (testInfo.project.name === 'desktop') {
        await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('link', { name: link, exact: true }).click();
      } else {
        await page.getByRole('button', { name: 'Abrir menu' }).click();
        await page.getByRole('dialog', { name: 'Menu de navegação' }).getByRole('link', { name: link, exact: true }).click();
      }
      await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
      await expect.poll(() => page.evaluate(() => window.__tuxedoNavigationMarker)).toBe('preserved');
      await expectNoOverflow(page);
    }
  });

  test('theme and mobile menu keep keyboard behavior', async ({ page }, testInfo) => {
    if (testInfo.project.name !== 'desktop') {
      const trigger = page.getByRole('button', { name: 'Abrir menu' });
      await trigger.click();
      const dialog = page.getByRole('dialog', { name: 'Menu de navegação' });
      await expect(dialog).toHaveAttribute('aria-hidden', 'false');
      await expect(page.getByRole('button', { name: 'Fechar menu' })).toBeFocused();
      await dialog.getByRole('button', { name: 'Alternar tema de cores' }).click();
      await expect(page.locator('html')).toHaveClass(/dark/);
      await page.keyboard.press('Escape');
      await expect(trigger).toBeFocused();
    } else {
      await page.getByRole('navigation').getByRole('button', { name: 'Alternar tema de cores' }).click();
      await expect(page.locator('html')).toHaveClass(/dark/);
    }
  });

  test('empty states and GET filters remain explicit', async ({ page }) => {
    await page.getByLabel('Início').fill('2030-01-01');
    await page.getByLabel('Fim').fill('2030-01-28');
    await page.getByRole('button', { name: 'Aplicar período' }).click();
    await expect(page).toHaveURL(/inicio=2030-01-01/);
    await expect(page.getByText('Atualizando indicadores…')).toHaveAttribute('aria-hidden', 'true');
    await expect(page.getByText('O gráfico será exibido quando houver treinos confirmados neste período.').first()).toBeVisible();
    await expect(page.getByRole('table', { name: /tabela equivalente/ })).toBeVisible();
    await expect(page.getByRole('row', { name: /31\/12 0/ })).toBeVisible();
  });

  test('filters submit without JavaScript', async ({ browser, baseURL }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(`${baseURL}/conta/entrar/`);
    await page.getByLabel('Usuário').fill('e2e-owner');
    await page.getByLabel('Senha').fill('Synthetic-e2e-password-274');
    await page.getByRole('button', { name: 'Entrar' }).click();
    await page.getByLabel('Início').fill('2030-02-01');
    await page.getByLabel('Fim').fill('2030-02-28');
    await page.getByRole('button', { name: 'Aplicar período' }).click();
    await expect(page).toHaveURL(/inicio=2030-02-01/);
    await expect(page.getByRole('table', { name: /tabela equivalente/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Olá, e2e-owner/ })).toBeVisible();
    await context.close();
  });
});
