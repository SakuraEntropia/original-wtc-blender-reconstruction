"""Apply the latest modular detail revision to the previous saved scene."""
from pathlib import Path
import sys,bpy,bmesh
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT))
from wtc.facade_detail import typical_panel_sample
from wtc.crown_site_detail import enhance
from wtc.latest_revision import apply as latest_revision
from review import create_detail_cameras,render_reviews
for mesh in bpy.data.meshes:
    if mesh.name.startswith('steel_box_segment_type') and len(mesh.vertices)>=104 and not mesh.get('splices_cross_joint'):
        for v in list(mesh.vertices)[24:]:v.co.z+=.16
        mesh['splices_cross_joint']=True;mesh.update()
typical_panel_sample();enhance();latest_revision();create_detail_cameras()
for mesh in bpy.data.meshes:
    if not mesh.users:continue
    bm=bmesh.new();bm.from_mesh(mesh)
    if bm.edges and all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)<0:
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh)
    bm.free()
render_reviews()
scene=bpy.context.scene
scene['quality_status']='modular CG study: NIST facade / photo lobby / traced WTC7 roof / conforming paving / mitered crown junctions; fabrication gaps explicit'
for c in bpy.data.collections:
    if any(s in c.name for s in ('_CROWN_photo','_CORNER_aluminum','_ROOF_detail','_CORE_roof_connections','PLAZA_furniture')):
        c.asset_mark();c.asset_data.description=c.get('confidence','CG study; inspect source tags')
        if c.name.startswith('WTC1'):c.instance_offset=(-55,55,0)
        elif c.name.startswith('WTC2'):c.instance_offset=(55,-55,0)
scene.render.filepath='//renders/preview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wtc_detailed_cg.blend'),compress=True)
from asset_export import export_assets
export_assets()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wtc_detailed_cg.blend'),compress=True)
