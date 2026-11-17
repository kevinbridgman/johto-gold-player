const {test}=require('node:test'),assert=require('node:assert/strict');
const {inspectRom,gameIdentity}=require('../rom-system.js');
function gba(size=32768){
 const bytes=new Uint8Array(size);bytes[0xb2]=0x96;bytes[0xbd]=(-0x96-0x19)&255;return bytes;
}
const gold='d8b8a3600a465308c9953dfa04f0081c05bdcb94',a='a'.repeat(40),b='b'.repeat(40);
test('detects native GB/GBC and GBA, including GBA without an extension',()=>{
 for(const name of ['gold.gb','gold.GBC'])assert.equal(inspectRom(new Uint8Array(32768),name).core,'gb');
 for(const name of ['game.gba','game.GBA','game.bin','game'])assert.equal(inspectRom(gba(),name).core,'gba');
 assert.equal(inspectRom(gba().slice(0,0x150),'game.gba',32*1024*1024).system,'gba');
});
test('rejects archives, unsupported consoles, malformed GBA headers and oversize files',()=>{
 for(const name of ['game.zip','game.7z','game.rar'])assert.throws(()=>inspectRom(gba(),name),/Extract/);
 const zip=gba();zip[0]=0x50;zip[1]=0x4b;assert.throws(()=>inspectRom(zip,'game.gba'),/Extract/);
 assert.throws(()=>inspectRom(gba(),'game.nds'),/Game Boy/);
 assert.throws(()=>inspectRom(new Uint8Array(32768),'bad.gba'),/GBA header/);
 const broken=gba();broken[0xbd]^=1;assert.throws(()=>inspectRom(broken,'bad.gba'),/GBA header/);
 assert.throws(()=>inspectRom(gba(),'huge.gba',32*1024*1024+1),/32 MB/);
 assert.throws(()=>inspectRom(new Uint8Array(32769),'game.gbc'),/GB\/GBC ROM size/);
});
test('retains Gold cartridge saves and exact old GB state keys across every patch',()=>{
 const profile=inspectRom(new Uint8Array(32768),'Gold.gbc');
 for(const active of [gold,a,b]){
  const id=gameIdentity(profile,gold,active,gold);
  assert.equal(id.gameName,'Johto Gold Mod');assert.equal(id.stateKey,'gb-gambatte-legacy:'+active);
 }
});
test('isolates GBA saves/states per ROM, from GB and from Gold, without using filenames',()=>{
 const gb=inspectRom(new Uint8Array(32768),'game.gbc'),advance=inspectRom(gba(),'game.gba');
 const one=gameIdentity(advance,a,a,gold),two=gameIdentity(advance,b,b,gold),other=gameIdentity(gb,a,a,gold);
 assert.notEqual(one.gameName,two.gameName);assert.notEqual(one.stateKey,two.stateKey);
 assert.notEqual(one.gameName,other.gameName);assert.notEqual(one.stateKey,other.stateKey);
 assert.notEqual(one.gameName,'Johto Gold Mod');assert.equal(one.stateKey,'gba-mgba-legacy:'+a);
 assert.deepEqual(gameIdentity(inspectRom(gba(),'renamed.GBA'),a,a,gold),one);
});
