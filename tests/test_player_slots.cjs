const {test}=require('node:test'),assert=require('node:assert/strict');
const {StateSlots,validSlot}=require('../save-slots.js');
function fixture(){
 const disk=new Map(),loads=[];let bytes=new Uint8Array([1,2,3]),fail=false;
 const store={list:async game=>[...disk.values()].filter(x=>x.game===game),
 put:async record=>{if(fail)throw Error('Quota exceeded');disk.set(record.game+':'+record.slot,structuredClone(record));}};
 const manager={getState:()=>bytes,loadState:data=>loads.push([...data])};
 const capture=async()=>new Blob([Uint8Array.from(bytes)],{type:'image/png'});
 return {disk,store,manager,loads,capture,setBytes:b=>bytes=Uint8Array.from(b),setFail:b=>fail=b,
 make:game=>new StateSlots({game,manager,store,capture})};
}
test('all nine slots start empty, and initialization never saves',async()=>{
 const t=fixture(),model=await t.make('game-a').init();
 assert.equal(model.records.size,0);assert.equal(t.disk.size,0);
 for(let slot=1;slot<=9;slot++){await model.save(slot);assert(model.records.has(slot));}
 assert.equal(t.disk.size,9);
});
test('saved state and image survive a new model and remain isolated by ROM/patch key',async()=>{
 const t=fixture(),first=await t.make('rom-a-patch-a').init();await first.save(3);
 const reopened=await t.make('rom-a-patch-a').init();
 assert.equal(reopened.records.size,1);await reopened.load(3);
 assert.deepEqual(t.loads,[[1,2,3]]);assert.equal(reopened.records.get(3).image.size,3);
 const different=await t.make('rom-a-patch-b').init();assert.equal(different.records.size,0);
 await assert.rejects(different.load(3),/empty save state/);assert.equal(t.loads.length,1);
});
test('overwrite replaces only the requested slot and commits state and image together',async()=>{
 const t=fixture(),m=await t.make('a').init();await m.save(1);await m.save(2);
 t.setBytes([7,8]);await m.save(1);
 assert.deepEqual([...new Uint8Array(m.records.get(1).state)],[7,8]);
 assert.deepEqual([...new Uint8Array(m.records.get(2).state)],[1,2,3]);
 assert.deepEqual([...new Uint8Array(await m.records.get(1).image.arrayBuffer())],[7,8]);
});
test('failed database write retains previous state and thumbnail',async()=>{
 const t=fixture(),m=await t.make('a').init();const old=await m.save(1);
 t.setBytes([9]);t.setFail(true);await assert.rejects(m.save(1),/Quota/);
 assert.equal(m.records.get(1),old);assert.equal(m.busy,false);
 await m.load(1);assert.deepEqual(t.loads,[[1,2,3]]);
});
test('failed screenshot does not create a phantom save or replace an existing one',async()=>{
 const t=fixture(),m=await t.make('a').init();const old=await m.save(1);
 m.capture=async()=>{throw Error('capture failed')};
 await assert.rejects(m.save(1),/capture failed/);assert.equal(m.records.get(1),old);
 await assert.rejects(m.save(2),/capture failed/);assert.equal(m.records.has(2),false);
});
test('state bytes are frozen before asynchronous screenshot capture and concurrent operations are rejected',async()=>{
 const t=fixture();let finish;
 const m=new StateSlots({game:'a',manager:t.manager,store:t.store,capture:()=>new Promise(r=>finish=r)});
 await m.init();const pending=m.save(1);
 t.setBytes([9]);await assert.rejects(m.save(2),/Wait/);
 finish(new Blob(['picture'],{type:'image/png'}));await pending;await m.load(1);
 assert.deepEqual(t.loads,[[1,2,3]]);
});
test('invalid slot numbers and corrupt records are rejected',async()=>{
 for(const n of [0,10,1.5,'x',null])assert.throws(()=>validSlot(n));
 const t=fixture();t.disk.set('a:1',{game:'a',slot:1,state:new ArrayBuffer(0),image:new Blob(['png'])});
 await assert.rejects(t.make('a').init(),/unreadable/);
});
