"use strict";
(() => {
 const validSlot=value=>{const slot=Number(value);if(!Number.isInteger(slot)||slot<1||slot>9)throw Error("Invalid save-state slot");return slot;};
 class SlotDatabase {
  constructor(indexedDB=globalThis.indexedDB){this.indexedDB=indexedDB;this.connection=null;}
  open(){
   if(this.connection)return this.connection;
   this.connection=new Promise((resolve,reject)=>{
    if(!this.indexedDB){reject(Error("Browser save-state storage is unavailable"));return;}
    const request=this.indexedDB.open("johto-player-save-states",1);
    request.onupgradeneeded=()=>{
     const store=request.result.createObjectStore("slots",{keyPath:["game","slot"]});
     store.createIndex("game","game");
    };
    request.onerror=()=>reject(request.error);
    request.onblocked=()=>reject(Error("Close other player tabs to open save-state storage"));
    request.onsuccess=()=>{const db=request.result;db.onversionchange=()=>db.close();resolve(db);};
   });
   return this.connection;
  }
  async list(game){
   const db=await this.open();
   return new Promise((resolve,reject)=>{
    const tx=db.transaction("slots","readonly"),request=tx.objectStore("slots").index("game").getAll(game);
    tx.oncomplete=()=>resolve(request.result);
    tx.onerror=tx.onabort=()=>reject(tx.error||Error("Could not read save states"));
   });
  }
  async put(record){
   const db=await this.open();
   return new Promise((resolve,reject)=>{
    const tx=db.transaction("slots","readwrite");
    // State bytes and screenshot are committed together, never independently.
    tx.objectStore("slots").put(record);
    tx.oncomplete=()=>resolve();
    tx.onerror=tx.onabort=()=>reject(tx.error||Error("Could not store save state"));
   });
  }
 }
 async function captureScreenshot(manager){
  const file="/screenshot.png";
  if(manager.FS.analyzePath(file).exists)manager.FS.unlink(file);
  manager.functions.screenshot();
  const deadline=Date.now()+5000;
  while(Date.now()<deadline){
   if(manager.FS.analyzePath(file).exists){
    const bytes=manager.FS.readFile(file);
    if(bytes.length<8||bytes[0]!==137||bytes[1]!==80||bytes[2]!==78||bytes[3]!==71)throw Error("Screenshot could not be captured");
    return new Blob([Uint8Array.from(bytes)],{type:"image/png"});
   }
   await new Promise(resolve=>setTimeout(resolve,25));
  }
  throw Error("Screenshot capture timed out; previous save state was kept");
 }
 class StateSlots {
  constructor({game,manager,store=new SlotDatabase(),capture=()=>captureScreenshot(manager),onChange=()=>{}}){
   this.game=game;this.manager=manager;this.store=store;this.capture=capture;this.onChange=onChange;
   this.records=new Map();this.busy=false;this.ready=false;
  }
  async init(){
   const records=await this.store.list(this.game);
   for(const record of records){
    const slot=validSlot(record.slot);
    if(record.game!==this.game||!(record.state instanceof ArrayBuffer)||!record.state.byteLength||!(record.image instanceof Blob)||!record.image.size)throw Error("A stored save state is unreadable");
    this.records.set(slot,record);
   }
   this.ready=true;this.onChange();return this;
  }
  async run(operation){
   if(!this.ready)throw Error("Save states are still loading");
   if(this.busy)throw Error("Wait for the current save-state operation to finish");
   this.busy=true;this.onChange();
   try{return await operation();}finally{this.busy=false;this.onChange();}
  }
  save(value){
   const slot=validSlot(value);
   return this.run(async()=>{
    const state=Uint8Array.from(this.manager.getState());
    if(!state.length)throw Error("The emulator did not provide a save state");
    const image=await this.capture();
    if(!(image instanceof Blob)||!image.size)throw Error("Screenshot could not be captured; previous save state was kept");
    const record={game:this.game,slot,state:state.buffer,image,savedAt:new Date().toISOString()};
    await this.store.put(record);
    this.records.set(slot,record);return record;
   });
  }
  load(value){
   const slot=validSlot(value);
   return this.run(async()=>{
    const record=this.records.get(slot);
    if(!record)throw Error("empty save state");
    this.manager.loadState(new Uint8Array(record.state));return record;
   });
  }
 }
 const api={StateSlots,SlotDatabase,captureScreenshot,validSlot};
 if(typeof module!=="undefined"&&module.exports)module.exports=api;
 else globalThis.JohtoStateSlots=api;
})();
