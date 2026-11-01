"""Protect old save IDs and trainer identities while appending village content."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build-tools'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import patch_cave_village as village

class VillageCompatibilityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.inputs=json.loads((Path(__file__).parent/'fixtures/village_inputs.json').read_text())
  for name,value in self.inputs.items():
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
   p.write_bytes(bytes(value)) if isinstance(value,list) else p.write_text(value)
 def apply(self):
  # Pixel/ROM geometry is covered by the compiled validator, not this source fixture.
  with patch.object(village,'village_art',return_value={}):return village.apply(self.root)
 def test_every_existing_event_id_is_preserved(self):
  def ids(src):
   value=0;out={}
   for line in src.splitlines():
    parts=line.split(';')[0].split()
    if not parts:continue
    if parts[0]=='const_next':value=int(parts[1],0)
    elif parts[0]=='const_skip':value+=int(parts[1],0) if len(parts)>1 else 1
    elif parts[0]=='const':out[parts[1]]=value;value+=1
   return out
  old=ids(self.inputs['constants/event_flags.asm']);self.apply();new=ids((self.root/'constants/event_flags.asm').read_text())
  self.assertEqual({k:new[k] for k in old},old)
  self.assertEqual([new[f] for f in village.FLAGS],[185,186,187,188])
 def test_every_old_map_and_trainer_id_is_preserved(self):
  def maps(src):
   group=0;index=0;out={}
   for line in src.splitlines():
    parts=line.split(';')[0].split()
    if not parts:continue
    if parts[0]=='newgroup':group+=1;index=0
    elif parts[0]=='map_const':index+=1;out[parts[1].rstrip(',')]=(group,index)
   return out
  def trainers(src):
   cls='';index=0;out={}
   for line in src.splitlines():
    parts=line.split(';')[0].split()
    if not parts:continue
    if parts[0]=='trainerclass':cls=parts[1];index=0
    elif parts[0]=='const' and cls:index+=1;out[parts[1]]=(cls,index)
   return out
  oldmaps=maps(self.inputs['constants/map_constants.asm']);oldtrainers=trainers(self.inputs['constants/trainer_constants.asm'])
  oldteams=self.inputs['data/trainers/parties.asm'].split('SchoolboyGroup:')[0]
  self.apply()
  newmaps=maps((self.root/'constants/map_constants.asm').read_text());newtrainers=trainers((self.root/'constants/trainer_constants.asm').read_text())
  self.assertEqual({k:newmaps[k] for k in oldmaps},oldmaps)
  self.assertEqual((newmaps['CAVE_LODGE'],newmaps['CAVE_TRAINING_HALL']),((24,16),(24,17)))
  self.assertEqual({k:newtrainers[k] for k in oldtrainers},oldtrainers)
  self.assertEqual(newtrainers['CAVE_COACH_ROOKIE'],('YOUNGSTER',13))
  self.assertEqual(newtrainers['CAVE_COACH_EXPERT'],('YOUNGSTER',15))
  self.assertTrue((self.root/'data/trainers/parties.asm').read_text().startswith(oldteams))
 def test_reapply_and_bad_inputs_do_not_partially_write(self):
  self.apply();before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  with self.assertRaises(ValueError):self.apply()
  self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

if __name__=='__main__':unittest.main()
