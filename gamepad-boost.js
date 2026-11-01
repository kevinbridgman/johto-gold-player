/* A browser-visible controller button can hold the player's existing boost. */
(function(root){
 'use strict';
 const KEY='johto-gold-controller-boost';
 function validBinding(value){
  return value&&value.version===1&&typeof value.id==='string'&&value.id.length>0&&value.id.length<=1024&&
   typeof value.mapping==='string'&&Number.isInteger(value.button)&&value.button>=0&&value.button<256;
 }
 function pressed(button){return typeof button==='number'?button>0.5:!!(button&&(button.pressed||button.value>0.5));}
 class ControllerBoost {
  constructor({readPads,canPlay,onHold,onChange=()=>{},storage,now=()=>Date.now()}){
   Object.assign(this,{readPads,canPlay,onHold,onChange,storage,now});
   this.binding=null;this.listening=false;this.captureArmed=false;this.held=false;this.blocked=true;
   this.note='';this.lastView='';this.handlers=new WeakSet();
   try{const value=JSON.parse(storage?.getItem(KEY)||'null');if(validBinding(value))this.binding=value;}catch{}
  }
  pads(){return Array.from(this.readPads()||[]).filter(p=>p&&p.connected!==false);}
  matches(pad){return !!this.binding&&pad?.id===this.binding.id&&(pad.mapping||'')===this.binding.mapping;}
  setHeld(value){if(value===this.held)return;this.held=value;this.onHold(value);}
  suspend(cancelCapture=false){
   this.blocked=true;this.setHeld(false);
   if(cancelCapture&&this.listening){this.listening=false;this.note='Assignment canceled.';this.publish();}
  }
  save(){
   try{if(this.binding)this.storage?.setItem(KEY,JSON.stringify(this.binding));else this.storage?.removeItem(KEY);}
   catch{this.note=this.binding?'Assigned for this visit; browser could not remember the setting.':'Cleared for this visit; browser could not forget the saved setting.';}
  }
  beginCapture(){
   this.suspend();this.listening=true;this.captureArmed=false;this.deadline=this.now()+20000;
   this.note='Release all controller buttons, then press the paddle/button you want to use.';this.publish();
  }
  cancelCapture(){this.suspend(true);}
  clear(){this.suspend();this.binding=null;this.listening=false;this.note='Controller boost is not assigned.';this.save();this.publish();}
  publish(pads=[]){
   const view={binding:this.binding,listening:this.listening,held:this.held,note:this.note,
    connected:pads.some(p=>this.matches(p))};
   const key=JSON.stringify(view);if(key===this.lastView)return;this.lastView=key;this.onChange(view);
  }
  tick(){
   let pads;
   try{pads=this.pads();}catch{this.suspend(true);this.note='Controller access is unavailable in this browser.';this.publish();return;}
   if(this.listening){
    if(this.now()>=this.deadline){this.listening=false;this.note='No button detected. Try again; for a mirrored paddle, assign an unused button in the 8BitDo app first.';}
    else{
     const down=[];
     for(const pad of pads)Array.from(pad.buttons||[]).forEach((button,index)=>{if(pressed(button))down.push({pad,index});});
     if(!down.length){this.captureArmed=true;this.note='Press one paddle/button now…';}
     else if(this.captureArmed){
      this.captureArmed=false;
      if(down.length===1){
       const {pad,index}=down[0];
       this.binding={version:1,id:pad.id,mapping:pad.mapping||'',button:index};
       this.listening=false;this.blocked=true;
       this.note='Assigned. Release the button, then hold it to boost.';this.save();
      }else this.note='Several buttons detected. Release them, then press just one.';
     }
    }
    this.publish(pads);return;
   }
   if(this.binding&&!pads.some(p=>this.matches(p))){this.suspend();this.publish(pads);return;}
   const down=pads.some(p=>this.matches(p)&&pressed(p.buttons?.[this.binding.button]));
   if(!this.canPlay())this.suspend();
   else if(!down){
    this.blocked=false;this.setHeld(false);
    if(this.note==='Assigned. Release the button, then hold it to boost.')this.note='';
   }
   else if(!this.blocked)this.setHeld(true);
   this.publish(pads);
  }
  // Reserve this physical input before EmulatorJS dispatches its game actions.
  // Its stable GamepadHandler dispatches through this method dynamically.
  attach(emulator){
   const handler=emulator?.gamepad;
   if(!handler||typeof handler.dispatchEvent!=='function'||this.handlers.has(handler))return;
   this.handlers.add(handler);
   const dispatch=handler.dispatchEvent.bind(handler);
   handler.dispatchEvent=(type,event)=>{
    if(type==='buttondown'||type==='buttonup'){
     let pad;try{pad=this.pads().find(p=>p.index===event.gamepadIndex);}catch{}
     const reserved=pad&&this.matches(pad)&&event.index===this.binding.button;
     // Unbound releases still reach the core: a button could have been held
     // before assignment began, and its earlier press must not get stuck.
     if(reserved||(this.listening&&this.captureArmed&&type==='buttondown'))return;
    }
    return dispatch(type,event);
   };
  }
 }
 const api={ControllerBoost,validBinding,pressed,KEY};
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.JohtoControllerBoost=api;
})(typeof window==='object'?window:globalThis);
