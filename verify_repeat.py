"""Run against saved scene: repeated migrations must not duplicate geometry."""
import sys,json,bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from wtc.latest_revision import apply

def counts():
    return {'objects':len(bpy.data.objects),'meshes':len(bpy.data.meshes),
            'collections':len(bpy.data.collections),'materials':len(bpy.data.materials)}
before=counts();apply();once=counts();apply();twice=counts()
report={'passed':before==once==twice,'before':before,'once':once,'twice':twice}
(ROOT/'reports/repeat_qa.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
if not report['passed']:raise RuntimeError('Scene migration duplicated data')
