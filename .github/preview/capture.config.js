const { defineConfig } = require('@playwright/test');
if (!process.env.E2E_BASE_URL || !process.env.FITNESS_CAPTURE_DIR) throw new Error('Use npm run preview:capture.');
module.exports=defineConfig({testDir:__dirname,outputDir:'../../test-results/capture',testMatch:'capture.spec.js',timeout:120000,workers:1,reporter:'line',use:{baseURL:process.env.E2E_BASE_URL,channel:'chrome',viewport:{width:1440,height:1000}}});
