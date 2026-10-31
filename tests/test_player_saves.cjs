const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
function fixture(){
 const status={textContent:''},events={},pending=[];
 let data=new Uint8Array([1,2,3]),copies=0;
 const manager={saveSaveFiles(){copies++},getSaveFile(){return data},FS:{syncfs(populate,callback){
  assert.equal(populate,false);pending.push(callback);
 }}};
 const context={gameStarted:true,window:{EJS_emulator:{gameManager:manager},addEventListener:(name,fn)=>events[name]=fn},
 document:{hidden:false,querySelector:()=>status,addEventListener:(name,fn)=>events[name]=fn},
 console:{error(){}},setInterval:(fn,ms)=>{events.timer=fn;assert.equal(ms,1000);return 1},clearInterval(){}};
 vm.createContext(context);
 vm.runInContext(script.slice(script.indexOf('// Flush cartridge SRAM'),script.indexOf('function hex(')),context);
 return {context,status,events,pending,setData:value=>data=value,get copies(){return copies},
 flush:force=>context.flushBatterySave(force)};
}
test('confirmation waits for browser commit and changed SRAM persists',async()=>{
 const t=fixture(),p=t.flush();
 assert.match(t.status.textContent,/Storing/);
 assert.equal(t.pending.length,1);
 t.pending.shift()(null);assert.equal(await p,true);
 assert.match(t.status.textContent,/stored in this browser/);
 await t.flush();assert.equal(t.pending.length,0);
 t.setData(new Uint8Array([1,2,4]));
 const next=t.flush();assert.equal(t.pending.length,1);t.pending.shift()(null);await next;
});
test('storage errors are visible and retried without certifying the failed write',async()=>{
 const t=fixture(),p=t.flush();t.pending.shift()(new Error('quota'));assert.equal(await p,false);
 assert.match(t.status.textContent,/Browser save failed/);
 const retry=t.flush();assert.equal(t.pending.length,1);t.pending.shift()(null);assert.equal(await retry,true);
});
test('forced final save waits for pending write then captures the latest SRAM',async()=>{
 const t=fixture(),first=t.flush();
 t.setData(new Uint8Array([4,5,6]));
 const final=t.flush(true);
 assert.equal(t.pending.length,1);t.pending.shift()(null);await first;
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(t.pending.length,1);t.pending.shift()(null);assert.equal(await final,true);
 await t.flush();assert.equal(t.pending.length,0);
});
test('hidden tabs and periodic timer trigger flushes',async()=>{
 const t=fixture();t.context.startBatterySavePersistence();
 t.pending.shift()(null);await new Promise(resolve=>setImmediate(resolve));
 t.setData(new Uint8Array([3]));t.events.timer();
 t.pending.shift()(null);await new Promise(resolve=>setImmediate(resolve));
 t.context.document.hidden=true;t.events.visibilitychange();
 assert.equal(t.pending.length,1);t.pending.shift()(null);
});
test('missing SRAM and a game that has not started do not report a saved game',async()=>{
 const t=fixture();t.context.gameStarted=false;
 assert.equal(await t.flush(),true);assert.equal(t.copies,0);
 t.context.gameStarted=true;t.setData(null);
 assert.equal(await t.flush(),true);assert.equal(t.pending.length,0);assert.equal(t.status.textContent,'');
});
