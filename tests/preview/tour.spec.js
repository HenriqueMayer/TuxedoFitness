const {test,expect}=require('@playwright/test');
const path=require('path');
const {pathToFileURL}=require('url');
for(const language of ['en','pt-br'])test(`explicit local filenames and synthetic tour ${language}`,async({browser})=>{
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const page=await context.newPage();
  const target=path.resolve(__dirname,'../../preview',language==='en'?'index.html':'pt-br/index.html');
  await page.goto(pathToFileURL(target).href);
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('img')).toHaveCount(6);
  for(const image of await page.locator('img').all()){
    await image.scrollIntoViewIfNeeded();
    expect(await image.evaluate(img=>img.complete&&img.naturalWidth>0)).toBeTruthy();
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await page.getByRole('link',{name:language==='en'?'Português (Brasil)':'English',exact:true}).click();
  await expect(page).toHaveURL(/index\.html$/);
  await expect(page.locator('html')).toHaveAttribute('lang',language==='en'?'pt-br':'en');
  await context.close();
});
