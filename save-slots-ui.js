"use strict";
globalThis.JohtoSlotGallery=class {
 constructor({grid,message,releaseSpeed}){
  this.grid=grid;this.message=message;this.releaseSpeed=releaseSpeed;this.selected=1;
  this.model=null;this.error=null;this.urls=[];this.render();
 }
 render(){
  this.urls.forEach(url=>URL.revokeObjectURL(url));this.urls=[];
  this.grid.replaceChildren();
  for(let slot=1;slot<=9;slot++){
   const record=this.model?.records.get(slot),ready=!!this.model?.ready&&!this.error;
   const card=document.createElement("article");card.className="state-slot"+(slot===this.selected?" selected":"");
   const select=document.createElement("button");select.type="button";select.className="slot-select";
   select.disabled=!ready;select.setAttribute("aria-pressed",String(slot===this.selected));
   select.setAttribute("aria-label","Select save-state slot "+slot);
   const title=document.createElement("strong");title.textContent="Slot "+slot+(slot===this.selected?" · selected":"");
   const preview=document.createElement("span");preview.className="state-preview";
   if(record){
    const img=document.createElement("img"),url=URL.createObjectURL(record.image);this.urls.push(url);
    img.src=url;img.alt="Screenshot of save-state slot "+slot;preview.append(img);
   }else{
    preview.textContent=this.error?"save states unavailable":!this.model?"start a game":!ready?"loading save states…":"empty save state";
   }
   select.append(title,preview);select.addEventListener("click",()=>this.select(slot));card.append(select);
   const timestamp=document.createElement("small");
   timestamp.textContent=record?new Date(record.savedAt).toLocaleString():"\u00a0";card.append(timestamp);
   const actions=document.createElement("div");actions.className="slot-actions";
   for(const action of ["save","load"]){
    const button=document.createElement("button");button.type="button";button.textContent=action==="save"?"Save":"Load";
    button.setAttribute("aria-label",(action==="save"?"Save to":"Load")+" slot "+slot);
    button.disabled=!ready||this.model.busy||(action==="load"&&!record);
    button.addEventListener("click",()=>{void this.perform(action,slot);});actions.append(button);
   }
   card.append(actions);this.grid.append(card);
  }
 }
 select(slot){this.emulator?.changeSettingOption("save-state-slot",String(slot));}
 async perform(action,value){
  try{
   const slot=JohtoStateSlots.validSlot(value);
   if(!this.model?.ready)throw Error("Start the game and wait for save states to load");
   this.releaseSpeed();this.select(slot);
   this.message.textContent=(action==="save"?"Saving":"Loading")+" slot "+slot+"…";
   await this.model[action](slot);
   this.message.textContent=action==="save"?"Slot "+slot+" and its screenshot saved in this browser.":"Loaded slot "+slot+".";
   this.emulator.displayMessage(this.message.textContent);
   return true;
  }catch(error){this.message.textContent=error.message;return false;}
 }
 async start(game,emulator){
  this.emulator=emulator;this.error=null;
  const manager=emulator.gameManager;
  this.model=new JohtoStateSlots.StateSlots({game,manager,onChange:()=>this.render()});
  const change=emulator.changeSettingOption.bind(emulator);
  emulator.changeSettingOption=(name,value,...rest)=>{
   const result=change(name,value,...rest);
   if(name==="save-state-slot"){
    this.selected=JohtoStateSlots.validSlot(value);this.render();
    try{emulator.saveSettings();}catch{}
   }
   return result;
  };
  try{this.selected=JohtoStateSlots.validSlot(emulator.getSettingValue("save-state-slot")||1);}catch{this.selected=1;}
  // Route both native quick-save menu actions and hotkeys through the same slots.
  manager.quickSave=(slot=1)=>{
   if(!this.model.ready||this.model.busy)return false;
   void this.perform("save",slot);return true;
  };
  manager.quickLoad=(slot=1)=>{void this.perform("load",slot);};
  const nativeInput=manager.simulateInput.bind(manager);
  manager.simulateInput=(player,index,value)=>{
   if(index===24||index===25){
    if(value===1)void this.perform(index===24?"save":"load",this.selected);
    return;
   }
   return nativeInput(player,index,value);
  };
  this.message.textContent="Loading this game's save states…";this.render();
  try{
   await this.model.init();
   this.message.textContent="Select a slot, then Save or Load. Keyboard defaults: 1 saves, 2 loads, 3 changes slot.";
  }catch(error){this.error=error;this.render();this.message.textContent="Save states unavailable: "+error.message;}
 }
};
