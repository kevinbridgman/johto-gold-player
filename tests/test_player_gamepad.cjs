const {test}=require('node:test'),assert=require('node:assert/strict');
const {ControllerBoost,KEY}=require('../gamepad-boost.js');
function pad(id='8BitDo test',index=0){return {id,index,mapping:'standard',connected:true,buttons:Array.from({length:20},()=>({pressed:false,value:0})),axes:[0,0,0,0]};}
function fixture(saved=null){
 let pads=[],allowed=true,time=0;const holds=[],views=[],data=new Map();if(saved)data.set(KEY,JSON.stringify(saved));
 const storage={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
 const model=new ControllerBoost({readPads:()=>pads,canPlay:()=>allowed,onHold:v=>holds.push(v),onChange:v=>views.push(v),storage,now:()=>time});
 const button=(p,index,down)=>p.buttons[index]={pressed:down,value:down?1:0};
 return {model,holds,views,data,storage,button,setPads:p=>pads=p,allow:v=>allowed=v,advance:ms=>time+=ms};
}
function assign(t,p,index=18){t.setPads([p]);t.model.beginCapture();t.model.tick();t.button(p,index,true);t.model.tick();}
test('capture waits for existing presses to release and requires one new button',()=>{
 const t=fixture(),p=pad();t.setPads([p]);t.button(p,0,true);t.model.beginCapture();t.model.tick();
 assert.equal(t.model.binding,null);
 t.button(p,0,false);t.model.tick();t.button(p,18,true);t.model.tick();
 assert.equal(t.model.binding.button,18);assert.deepEqual(t.holds,[]);
 t.button(p,18,false);t.model.tick();t.button(p,18,true);t.model.tick();t.model.tick();
 assert.deepEqual(t.holds,[true]);t.button(p,18,false);t.model.tick();assert.deepEqual(t.holds,[true,false]);
});
test('simultaneous presses cannot silently pick the wrong button',()=>{
 const t=fixture(),p=pad();t.setPads([p]);t.model.beginCapture();t.model.tick();
 t.button(p,0,true);t.button(p,1,true);t.model.tick();assert.equal(t.model.binding,null);
 t.button(p,1,false);t.model.tick();assert.equal(t.model.binding,null);
 t.button(p,0,false);t.model.tick();t.button(p,18,true);t.model.tick();assert.equal(t.model.binding.button,18);
});
test('assignment survives reopening and controller index changes but not a different device',()=>{
 const t=fixture(),p=pad();assign(t,p);
 const restored=fixture(JSON.parse(t.data.get(KEY))),other=pad('another device');restored.setPads([other]);restored.model.tick();
 restored.button(other,18,true);restored.model.tick();assert.deepEqual(restored.holds,[]);
 const reconnected=pad('8BitDo test',3);restored.setPads([null,null,null,reconnected]);restored.model.tick();
 restored.button(reconnected,18,true);restored.model.tick();assert.deepEqual(restored.holds,[true]);
});
test('lost focus, hidden/paused/form states and disconnect require release before rearming',()=>{
 for(const cause of ['gated','disconnect','manual']){
  const t=fixture(),p=pad();assign(t,p);t.button(p,18,false);t.model.tick();t.button(p,18,true);t.model.tick();
  if(cause==='gated')t.allow(false);else if(cause==='disconnect')t.setPads([]);else t.model.suspend();
  t.model.tick();assert.deepEqual(t.holds,[true,false]);
  t.allow(true);t.setPads([p]);t.model.tick();assert.deepEqual(t.holds,[true,false]);
  t.button(p,18,false);t.model.tick();t.button(p,18,true);t.model.tick();assert.deepEqual(t.holds,[true,false,true]);
 }
});
test('native dispatch reserves only the assigned button and preserves all other controller inputs',()=>{
 const t=fixture(),p=pad();assign(t,p);const events=[];
 const handler={dispatchEvent:(type,e)=>events.push([type,e])};t.model.attach({gamepad:handler});t.model.attach({gamepad:handler});
 handler.dispatchEvent('buttondown',{gamepadIndex:0,index:18});handler.dispatchEvent('buttonup',{gamepadIndex:0,index:18});
 assert.deepEqual(events,[]);
 handler.dispatchEvent('buttondown',{gamepadIndex:0,index:0});handler.dispatchEvent('axischanged',{gamepadIndex:0,index:18});
 handler.dispatchEvent('connected',{gamepadIndex:0});assert.equal(events.length,3);
 t.button(p,18,false);t.model.beginCapture();t.model.tick();
 handler.dispatchEvent('buttondown',{gamepadIndex:0,index:1});assert.equal(events.length,3);
 handler.dispatchEvent('buttonup',{gamepadIndex:0,index:1});assert.equal(events.length,4);
});
test('cancel, timeout, clear and invalid storage preserve or remove the intended binding',()=>{
 const t=fixture(),p=pad();assign(t,p);const old=t.model.binding;
 t.model.beginCapture();t.model.cancelCapture();assert.deepEqual(t.model.binding,old);
 t.model.beginCapture();t.advance(20001);t.model.tick();assert.equal(t.model.listening,false);assert.deepEqual(t.model.binding,old);
 t.model.clear();assert.equal(t.model.binding,null);assert(!t.data.has(KEY));assert.equal(t.model.held,false);
 for(const button of [-1,256,1.5,'18'])assert.equal(fixture({...old,button}).model.binding,null);
});
test('inaccessible storage and gamepad API fail without breaking controls',()=>{
 const t=fixture(),p=pad();t.model.storage={getItem(){throw Error('blocked')},setItem(){throw Error('blocked')}};
 assign(t,p);assert.equal(t.model.binding.button,18);assert.match(t.model.note,/this visit/);
 t.button(p,18,false);t.model.tick();t.button(p,18,true);t.model.tick();
 t.model.readPads=()=>{throw Error('denied')};t.model.tick();assert.equal(t.model.held,false);assert.deepEqual(t.holds,[true,false]);
});
