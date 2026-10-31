const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
function fixture(saved='10'){
 const events={},calls=[],timers=new Map(),status={textContent:''},select={value:'',addEventListener:(name,fn)=>events.change=fn};
 let id=0,time=0,frame=0;
 const manager={toggleSlowMotion:v=>calls.push(['slow',v]),toggleFastForward:v=>calls.push(['fast',v]),
 setFastForwardRatio:v=>calls.push(['ratio',v]),setVSync:v=>calls.push(['vsync',v]),getFrameNum:()=>frame,
 simulateInput:(p,i,v)=>calls.push(['input',i,v])};
 const emulator={gameManager:manager,isFastForward:true,isSlowMotion:true,paused:false,
 changeSettingOption:(k,v)=>calls.push(['setting',k,v]),getSettingValue:()=> 'enabled',
 saveSettings:()=>calls.push(['persist']),isSettingsMenuOpen:()=>false,isPopupOpen:()=>false};
 const game={contains:t=>!!t?.inGame};
 const toggle={disabled:true,textContent:"",attributes:{},setAttribute(k,v){this.attributes[k]=v},addEventListener:(n,fn)=>events.toggle=fn};
 const context={window:{EJS_emulator:emulator,addEventListener:(name,fn)=>events[name]=fn},
 document:{hidden:false,querySelector:s=>s==='#space-speed'?select:s==='#speed-status'?status:s==='#speed-toggle'?toggle:game,addEventListener:(n,fn)=>events[n]=fn},
 localStorage:{getItem:()=>saved,setItem(){}},performance:{now:()=>time},
 setTimeout:(fn,ms)=>{timers.set(++id,{fn,ms});return id},clearTimeout:i=>timers.delete(i),
 setInterval:(fn,ms)=>{timers.set(++id,{fn,ms,interval:true});return id},clearInterval:i=>timers.delete(i)};
 vm.createContext(context);
 vm.runInContext(script.slice(script.indexOf('const spaceSpeedSelect='),script.indexOf('// Flush cartridge SRAM')),context);
 vm.runInContext('gameStarted=true;initializeSpeedControls()',context);
 const key=(code='Space',inGame=true,form=false)=>({code,target:{inGame,closest:()=>form},preventDefault(){},stopImmediatePropagation(){}});
 const tick=()=>{for(const [i,t] of [...timers])if(!t.interval){timers.delete(i);t.fn();}};
 return {events,calls,timers,status,select,toggle,manager,emulator,context,key,tick,
 measure:(ms,frames)=>{time+=ms;frame+=frames;context.sampleSpaceSpeed();}};
}
test('saved toggle modes are reset and native speed inputs cannot conflict',()=>{
 const t=fixture();
 assert.equal(t.emulator.isFastForward,false);assert.equal(t.emulator.isSlowMotion,false);
 assert(t.calls.some(c=>c[0]==='setting'&&c[1]==='slowMotion'&&c[2]==='disabled'));
 const before=t.calls.length;
 t.manager.simulateInput(0,27,1);t.manager.simulateInput(0,29,1);
 assert.equal(t.calls.length,before);
 t.manager.simulateInput(0,8,1);assert.deepEqual(t.calls.at(-1),['input',8,1]);
});
test('all ratios use delayed scheduler correction and return to normal on release',()=>{
 for(let ratio=2;ratio<=10;ratio++){
  const t=fixture(String(ratio));t.calls.length=0;
  t.events.keydown(t.key());t.events.keydown(t.key());
  assert(!t.calls.some(c=>c[0]==='ratio'));
  t.tick();assert.deepEqual(t.calls.slice(-2),[['ratio',ratio],['fast',1]]);
  t.tick();assert.deepEqual(t.calls.at(-1),['vsync',false]);
  t.events.keyup(t.key());assert.deepEqual(t.calls.slice(-3),[['slow',0],['fast',0],['vsync',true]]);
  assert.equal(t.timers.size,0);assert.equal(t.status.textContent,'Normal speed (1×)');
 }
});
test('quick release and focus loss cancel pending speed transitions',()=>{
 for(const exit of ['keyup','blur','visibilitychange','focusout','pointerdown']){
  const t=fixture();t.calls.length=0;t.events.keydown(t.key());
  if(exit==='visibilitychange'){t.context.document.hidden=true;t.events[exit]();}
  else if(exit==='focusout')t.events[exit]({relatedTarget:null});
  else if(exit==='pointerdown')t.events[exit]({target:{inGame:false}});
  else t.events[exit](t.key());
  t.tick();t.tick();
  assert(!t.calls.some(c=>c[0]==='fast'&&c[1]===1),exit);
  assert.equal(t.timers.size,0);
 }
});
test('form focus, external keys, paused game, and settings do not activate speed',()=>{
 const t=fixture();t.calls.length=0;
 t.events.keydown(t.key('Space',false));t.events.keydown(t.key('Space',true,true));t.events.keydown(t.key('KeyA'));
 t.emulator.paused=true;t.events.keydown(t.key());t.emulator.paused=false;
 t.emulator.isSettingsMenuOpen=()=>true;t.events.keydown(t.key());
 assert.equal(t.timers.size,0);assert.equal(t.calls.length,0);
});
test('changing target while held cancels old transitions and uses the new ratio',()=>{
 const t=fixture('2');t.events.keydown(t.key());t.select.value='9';t.events.change();
 t.tick();t.tick();assert(t.calls.some(c=>c[0]==='ratio'&&c[1]===9));
 assert(!t.calls.some(c=>c[0]==='ratio'&&c[1]===2));
});
test('measurement reports achieved rate rather than asserting the target was achieved',()=>{
 const t=fixture('10');t.events.keydown(t.key());t.tick();t.tick();
 t.measure(1000,358);
 assert.match(t.status.textContent,/10× target · 6\.0× measured/);
});
test('stable legacy settings-menu property works without a method',()=>{
 const t=fixture();delete t.emulator.isSettingsMenuOpen;t.emulator.settingsMenu={style:{display:'none'}};
 t.calls.length=0;t.events.keydown(t.key());t.tick();t.tick();
 assert.deepEqual(t.calls.at(-1),['vsync',false]);
 t.events.keyup(t.key());t.emulator.settingsMenu.style.display='';
 t.calls.length=0;t.events.keydown(t.key());assert.equal(t.calls.length,0);
});

test('tap toggles on and off at every selected speed without a keyboard',()=>{
 for(let ratio=2;ratio<=10;ratio++){
  const t=fixture(String(ratio));assert.equal(t.toggle.disabled,false);
  t.events.toggle();assert.equal(t.toggle.attributes['aria-pressed'],'true');
  t.tick();t.tick();assert(t.calls.some(c=>c[0]==='ratio'&&c[1]===ratio));
  assert.deepEqual(t.calls.at(-1),['vsync',false]);
  t.events.toggle();assert.equal(t.toggle.attributes['aria-pressed'],'false');
  assert.equal(t.timers.size,0);assert.deepEqual(t.calls.at(-1),['vsync',true]);
 }
});
test('touch mode stays active while tapping game controls and changing speed',()=>{
 const t=fixture('2');t.events.toggle();t.tick();t.tick();
 t.events.pointerdown({target:{inGame:true}});t.events.focusout({relatedTarget:null});
 assert.equal(t.toggle.attributes['aria-pressed'],'true');
 t.select.value='6';t.events.change();t.tick();t.tick();
 assert.match(t.toggle.textContent,/On \(6×\)/);assert(t.calls.some(c=>c[0]==='ratio'&&c[1]===6));
 t.measure(1000,358);assert.match(t.status.textContent,/Speed boost: 6× target/);
});
test('Space key release does not turn off a latched boost',()=>{
 const t=fixture();t.events.toggle();t.events.keydown(t.key());t.events.keyup(t.key());
 assert.equal(t.toggle.attributes['aria-pressed'],'true');
 t.tick();t.tick();assert.deepEqual(t.calls.at(-1),['vsync',false]);
});
test('hiding or blurring turns a latched boost off and cancels delayed activation',()=>{
 for(const event of ['blur','visibilitychange']){
  const t=fixture();t.calls.length=0;t.events.toggle();
  if(event==='visibilitychange')t.context.document.hidden=true;
  t.events[event]();t.tick();t.tick();
  assert.equal(t.toggle.attributes['aria-pressed'],'false');assert.equal(t.timers.size,0);
  assert(!t.calls.some(c=>c[0]==='fast'&&c[1]===1));
 }
});

test('button reflects keyboard boost and can turn it off without relatching on focus change',()=>{
 const t=fixture();t.events.keydown(t.key());
 assert.equal(t.toggle.attributes['aria-pressed'],'true');
 t.events.pointerdown({target:t.toggle});t.events.focusout({relatedTarget:t.toggle});
 t.events.toggle();t.tick();t.tick();
 assert.equal(t.toggle.attributes['aria-pressed'],'false');assert.equal(t.timers.size,0);
});
