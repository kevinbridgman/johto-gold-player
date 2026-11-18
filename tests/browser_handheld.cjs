const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),evidence='/tmp/handheld-evidence',cache='/tmp/handheld-cdn';fs.mkdirSync(evidence,{recursive:true});
(async()=>{
 const context=await chromium.launchPersistentContext('/tmp/handheld-profile',{executablePath:process.env.CHROME_BIN||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--disable-dev-shm-usage'],viewport:{width:420,height:900},hasTouch:true,isMobile:true});
 const errors=[];
 const page=await context.newPage();
 // Exercise the published GBA patch route with a self-authored ROM only.
 // The patch changes an unused byte; no commercial game bytes enter CI.
 const original=fs.readFileSync('/tmp/player-selftest.gba');
 const patch=Buffer.from([80,65,84,67,72,0,6,0,0,1,42,69,79,70]);
 const modified=Buffer.from(original);modified[0x600]=42;
 const patch2=Buffer.from(patch);patch2[10]=43;
 const modified2=Buffer.from(modified);modified2[0x600]=43;
 const digest=(algorithm,data)=>crypto.createHash(algorithm).update(data).digest('hex');
 const catalog=JSON.parse(fs.readFileSync(path.join(root,'patches/catalog.json'),'utf8'));
 catalog.patches.push({id:'selftest-patch',name:'Original GBA test patch',version:'1.0',system:'gba',
  file:'patches/handheld-test.ips',baseSha1:digest('sha1',original),sha256:digest('sha256',patch),modifiedSha1:digest('sha1',modified)});
 await page.route('http://127.0.0.1:8766/**',async route=>{
  const url=new URL(route.request().url());
  if(url.pathname==='/patches/catalog.json'){await route.fulfill({contentType:'application/json',body:JSON.stringify(catalog)});return;}
  if(url.pathname==='/patches/handheld-test2.ips'){await route.fulfill({body:patch2});return;}
  if(url.pathname==='/patches/handheld-test.ips'){await route.fulfill({body:patch});return;}
  const p=path.join(root,url.pathname==='/'?'index.html':url.pathname);
  if(!fs.existsSync(p)||fs.statSync(p).isDirectory()){await route.fulfill({status:404,body:''});return;}
  await route.fulfill({contentType:p.endsWith('.html')?'text/html':p.endsWith('.js')?'application/javascript':'application/octet-stream',body:fs.readFileSync(p)});
 });
 await page.route('https://cdn.emulatorjs.org/**',async route=>{
  const name=route.request().url().split('/stable/data/')[1]?.split('?')[0],dest=name&&path.join(cache,name);
  if(!dest){await route.abort();return;}
  if(!fs.existsSync(dest)){
   fs.mkdirSync(path.dirname(dest),{recursive:true});
   try{await require('node:util').promisify(require('node:child_process').execFile)('curl',['-fLsS','--retry','2','--max-time','45',route.request().url(),'-o',dest]);}
   catch(error){errors.push('CDN fetch failed '+name+': '+error.message);await route.abort();return;}
  }
  await route.fulfill({body:fs.readFileSync(dest),headers:{'content-type':name.endsWith('.js')?'application/javascript':name.endsWith('.css')?'text/css':name.endsWith('.json')?'application/json':'application/octet-stream','access-control-allow-origin':'*'}});
 });
 page.on('pageerror',e=>{errors.push(e.message);console.log('PAGE ERROR',e.message)});
 await page.goto('http://127.0.0.1:8766');
 await page.setInputFiles('#rom','/tmp/player-selftest.gba');
 await page.waitForFunction(()=>document.querySelector('#rom-system').textContent.includes('Advance'));
 assert.equal(await page.inputValue('#patch-select'),'selftest-patch');
 assert.deepEqual(await page.locator('#patch-select option').evaluateAll(options=>options.map(o=>o.value)),['selftest-patch','none','manual']);
 await page.click('#start');
 console.log('Loading GBA core...');
 await page.waitForFunction(()=>window.EJS_emulator?.started,{timeout:120000});
 await page.waitForTimeout(2500);
 const initial=await page.evaluate(()=>({core:EJS_core,name:EJS_gameName,actualCore:EJS_emulator.getCore(),savePath:EJS_emulator.gameManager.getSaveFilePath(),touch:document.querySelector('#game').dataset.touchControls,buttons:[...document.querySelectorAll('.ejs_virtualGamepad_button')].map(x=>x.textContent)}));
 console.log('GBA started',JSON.stringify(initial));assert.equal(initial.name,'Handheld-gba-'+digest('sha1',modified));assert.equal(initial.core,'gba');assert.equal(initial.actualCore,'mgba');assert.equal(initial.touch,'on');
 assert(initial.buttons.includes('L'));assert(initial.buttons.includes('R'));
 await page.screenshot({path:evidence+'/gba-started.png'});
 await page.evaluate(()=>EJS_emulator.gameManager.simulateInput(0,10,1));await page.waitForTimeout(180);
 await page.evaluate(()=>EJS_emulator.gameManager.simulateInput(0,10,0));await page.waitForTimeout(1000);
 await page.screenshot({path:evidence+'/gba-after-L.png'});
 const save=await page.evaluate(async()=>{await flushBatterySave(true);return {bytes:[...EJS_emulator.gameManager.getSaveFile(false).slice(0,8)],status:document.querySelector('#save-status').textContent};});
 console.log('Saved',JSON.stringify(save));
 assert.equal(save.bytes[0],0x4c,'L must write the expected SRAM byte');
 // Publish a compatible second revision and prove the prior battery save
 // is discovered automatically even though the patched ROM hash changes.
 catalog.patches.unshift({id:'selftest-patch2',name:'Original GBA test patch 2',version:'2.0',system:'gba',
  file:'patches/handheld-test2.ips',baseSha1:digest('sha1',original),sha256:digest('sha256',patch2),
  modifiedSha1:digest('sha1',modified2),saveIdentitySha1:digest('sha1',modified)});
 await page.reload();await page.setInputFiles('#rom','/tmp/player-selftest.gba');await page.waitForFunction(()=>document.querySelector('#rom-system').textContent.includes('Advance'));await page.click('#start');await page.waitForFunction(()=>window.EJS_emulator?.started,{timeout:120000});await page.waitForTimeout(1500);
 assert.equal(await page.inputValue('#patch-select'),'selftest-patch2');
 assert.equal(await page.evaluate(()=>EJS_gameName),initial.name);
 const restored=await page.evaluate(()=>[...EJS_emulator.gameManager.getSaveFile(false).slice(0,8)]);
 assert.equal(restored[0],0x4c,'GBA save must restore on reload');
 await page.screenshot({path:evidence+'/gba-restored.png'});
 await page.evaluate(()=>EJS_emulator.gameManager.simulateInput(0,11,1));await page.waitForTimeout(180);await page.evaluate(()=>EJS_emulator.gameManager.simulateInput(0,11,0));await page.waitForTimeout(1000);
 const afterR=await page.evaluate(()=>{EJS_emulator.gameManager.saveSaveFiles();return [...EJS_emulator.gameManager.getSaveFile(false).slice(0,8)]});assert.equal(afterR[0],0x52);
 await page.click('#speed-toggle');await page.waitForTimeout(400);assert.equal(await page.getAttribute('#speed-toggle','aria-pressed'),'true');await page.click('#speed-toggle');
 assert.equal(errors.length,0,errors.join('\n'));
 fs.writeFileSync(evidence+'/browser-result.json',JSON.stringify({initial,save,restored,afterR,errors},null,2));
 await context.close();console.log('GBA boot, L/R input, battery reload and boost toggle passed');
})().catch(e=>{console.error(e);process.exit(1)});
