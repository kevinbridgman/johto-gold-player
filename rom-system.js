(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.HandheldROM=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const MAX_GBA_BYTES=32*1024*1024;
 function inspectRom(data,filename='',size=data.byteLength){
  const bytes=data instanceof Uint8Array?data:new Uint8Array(data);
  if(/\.(zip|7z|rar)$/i.test(filename)||(bytes[0]===0x50&&bytes[1]===0x4b))
   throw Error('Extract the ROM first, then choose its .gb, .gbc, or .gba file.');
  const extension=(filename.match(/\.([^.]+)$/)||[])[1]?.toLowerCase();
  if(extension&&!['gb','gbc','gba','bin'].includes(extension))
   throw Error('Choose a Game Boy (.gb/.gbc) or Game Boy Advance (.gba) ROM.');
  let checksum=0x19;
  for(let i=0xa0;i<=0xbc&&i<bytes.length;i++)checksum+=bytes[i];
  const gbaHeader=bytes.length>=0xc0&&bytes[0xb2]===0x96&&((-checksum)&255)===bytes[0xbd];
  if(extension==='gba'||gbaHeader){
   if(!gbaHeader)throw Error('Invalid GBA header. Choose an uncompressed .gba ROM.');
   if(size<0xc0||size>MAX_GBA_BYTES)throw Error('Invalid GBA ROM size (maximum 32 MB).');
   return {system:'gba',core:'gba',label:'Game Boy Advance',statePrefix:'gba-mgba-legacy:',aspectRatio:'3 / 2'};
  }
  if(size<0x150||size%0x4000!==0)throw Error('Invalid GB/GBC ROM size. Choose an uncompressed .gb or .gbc file.');
  return {system:'gb',core:'gb',label:'Game Boy / Game Boy Color',statePrefix:'gb-gambatte-legacy:',aspectRatio:'10 / 9'};
 }
 function compatiblePatches(patches,profile,sourceSha,goldSha){
  const signature=(sourceSha||(!profile?goldSha:'')||'').toLowerCase();
  return patches.filter(p=>p.baseSha1.toLowerCase()===signature&&
   (!profile||!p.system||p.system===profile.system));
 }
 function gameIdentity(profile,sourceSha,activeSha,goldSha){
  // Retain Gold's existing cartridge-save directory across all published patches.
  const gameName=profile.system==='gb'&&sourceSha.toLowerCase()===goldSha.toLowerCase()
   ?'Johto Gold Mod':'Handheld-'+profile.system+'-'+activeSha.toLowerCase();
  return {gameName,stateKey:profile.statePrefix+activeSha.toLowerCase()};
 }
 return {inspectRom,gameIdentity,compatiblePatches};
});
