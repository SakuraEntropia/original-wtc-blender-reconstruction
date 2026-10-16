"""Load every generated asset library and verify actual mesh/material dependencies."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parent
results=[]
for path in sorted((ROOT/'assets').glob('*.blend')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(path),link=True) as (source,target):
        target.collections=source.collections
    roots=[c for c in target.collections if c and c.asset_data]
    objects=set();seen=set()
    def visit(c):
        if c in seen:return
        seen.add(c)
        for ob in c.all_objects:
            objects.add(ob)
            if ob.instance_type=='COLLECTION' and ob.instance_collection:visit(ob.instance_collection)
    for c in roots:visit(c)
    meshes=[o for o in objects if o.type=='MESH']
    external=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath]
    passed=bool(roots) and bool(meshes) and all(o.data.vertices and o.data.materials for o in meshes) and not external
    results.append({'file':path.name,'passed':passed,'root_assets':[c.name for c in roots],
                    'mesh_objects':len(meshes),'external_images':external,'bytes':path.stat().st_size,
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
report={'passed':all(r['passed'] for r in results),'mode':'isolated read-only linked library loading; no per-ID localization','libraries':results}
(ROOT/'reports'/'assets_qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'libraries':len(results),'failed':[r['file'] for r in results if not r['passed']]}))
if not report['passed']: raise RuntimeError('Asset dependency check failed')
