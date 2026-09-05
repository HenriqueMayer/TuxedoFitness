const {defineConfig}=require('@playwright/test');
module.exports=defineConfig({testDir:'../../tests/preview',workers:1,reporter:'line',use:{channel:'chrome'}});
