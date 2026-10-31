const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const script=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
function fixture({points=0,coarse=false,mobile=false,saved=null,blocked=false}={}){
 const calls=[],select={value:'',addEventListener:(n,fn)=>calls.push(['listener',n,fn])};
 const game={dataset:{},scrollIntoView:()=>calls.push(['scroll'])};
 const emulator={isMobile:mobile,virtualGamepad:{},touch:false,menu:{close:()=>calls.push(['menu-close'])},
 changeSettingOption:(k,v)=>calls.push(['setting',k,v]),toggleVirtualGamepad:v=>calls.push(['show',v]),
 handleResize:()=>calls.push(['resize']),saveSettings:()=>calls.push(['persist-native'])};
 const context={navigator:{maxTouchPoints:points},gameStarted:false,
 window:{EJS_emulator:emulator,matchMedia:()=>({matches:coarse})},
 document:{querySelector:s=>s==='#touch-controls'?select:game},
 localStorage:{getItem(){if(blocked)throw Error('blocked');return saved},setItem:(k,v)=>calls.push(['persist',v])}};
 vm.createContext(context);
 vm.runInContext(script.slice(script.indexOf('// Touch controller visibility'),script.indexOf('const spaceSpeedSelect=')),context);
 return {context,calls,select,game,emulator};
}
test('Auto shows controls for touch hardware, coarse pointers, and mobile user agents',()=>{
 for(const opts of [{points:5},{coarse:true},{mobile:true}]){
  const t=fixture(opts);t.context.gameStarted=true;t.context.initializeTouchControls();
  assert.equal(t.game.dataset.touchControls,'on');assert.equal(t.game.dataset.gameStarted,'true');
  assert.equal(t.emulator.touch,true);assert(t.calls.some(c=>c[0]==='show'&&c[1]===true));
  assert(t.calls.some(c=>c[0]==='setting'&&c[1]==='virtual-gamepad'&&c[2]==='enabled'));
  assert(t.calls.some(c=>c[0]==='scroll'));assert(t.calls.some(c=>c[0]==='menu-close'));
 }
});
test('Auto keeps desktop controls hidden, while On overrides device detection',()=>{
 const desktop=fixture();desktop.context.initializeTouchControls();
 assert.equal(desktop.game.dataset.touchControls,'off');
 const forced=fixture({saved:'on'});forced.context.initializeTouchControls();
 assert.equal(forced.game.dataset.touchControls,'on');assert.equal(forced.emulator.touch,true);
});
test('explicit Off on a phone is honored and remembered',()=>{
 const t=fixture({points:5,saved:'off'});t.context.gameStarted=true;t.context.initializeTouchControls();
 assert.equal(t.game.dataset.touchControls,'off');assert.equal(t.emulator.touch,false);
 t.select.value='on';t.calls.find(c=>c[0]==='listener')[2]();
 assert.equal(t.game.dataset.touchControls,'on');assert(t.calls.some(c=>c[0]==='persist'&&c[1]==='on'));
});
test('invalid or unavailable preference storage falls back to Auto',()=>{
 for(const opts of [{saved:'invalid',points:2},{blocked:true,points:2}]){
  const t=fixture(opts);assert.equal(t.select.value,'auto');assert.equal(t.context.applyTouchControls(),true);
 }
});
test('ready-time setup works before the emulator settings menu is available',()=>{
 const t=fixture({points:1});delete t.emulator.changeSettingOption;
 assert.equal(t.context.applyTouchControls(),true);assert.equal(t.emulator.touch,true);
 assert(!t.calls.some(c=>c[0]==='resize'||c[0]==='persist-native'));
});
