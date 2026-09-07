const {test,expect}=require('@playwright/test');
const path=require('path');
test('capture every synthetic surface before publishing the static tour',async({page})=>{
  await page.goto('/accounts/login/');
  await page.locator('#id_username').fill('e2e-owner');
  await page.locator('#id_password').fill(process.env.E2E_PASSWORD);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  for(const lang of ['en','pt-br']){
    await page.locator('[data-language]').selectOption(lang);
    await expect(page.locator('html')).toHaveAttribute('lang',lang);
    for(const [name,route] of [['overview','/dashboard/'],['analysis','/dashboard/reports/?panel=effort'],['history','/history/'],['routines','/routines/'],['exercises','/exercises/'],['prompt','/planning/']]){
      await page.goto(route);await expect(page.locator('h1')).toBeVisible();
      await page.evaluate(()=>document.fonts.ready);
      await page.screenshot({path:path.join(process.env.FITNESS_CAPTURE_DIR,`${lang}-${name}.png`),fullPage:true});
    }
  }
});
