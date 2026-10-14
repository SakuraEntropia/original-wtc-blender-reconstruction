"""Rebuild, render review cameras, restore exterior state, save editable scene."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT))
from wtc.model import build
from wtc.completion import PLAZA_Z
from wtc.facade_detail import upgrade_facades,steel_mesh,cover_mesh,material,object_mesh,typical_panel_sample
from wtc.lowrise_detail import enrich_context
from wtc.crown_site_detail import enhance
from wtc.latest_revision import apply as latest_revision
import bpy
import bmesh
from mathutils import Vector

build()
upgrade_facades()
enrich_context()
enhance()
latest_revision()
panel_sample=typical_panel_sample()
section=bpy.data.collections.new('SECTION_REVIEW_steel_and_aluminum')
bpy.context.scene.collection.children.link(section)
steelmat=bpy.data.materials['structural_steel_unclad_STUDY']
object_mesh('SECTION_14in_steel_box',steel_mesh(.6,steelmat,connections=False),(245,-140,.65),section,hidden=True)
object_mesh('SECTION_18in_recessed_aluminum_cover',cover_mesh(.6,bpy.data.materials['silver_cladding_color_study']),
            (245.8,-140,.65),section,hidden=True)
for mesh in bpy.data.meshes:
    if not mesh.users: continue
    bm=bmesh.new(); bm.from_mesh(mesh)
    if bm.edges and all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)<0:
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(mesh)
    bm.free()
scene=bpy.context.scene
scene.eevee.shadow_pool_size='2048'
if scene.camera:
    bpy.data.objects.remove(scene.camera,do_unlink=True)
scene.render.resolution_x=1280
scene.render.resolution_y=1280
scene.render.resolution_percentage=100
(ROOT/'renders').mkdir(exist_ok=True)
cameras=bpy.data.collections.new('REVIEW_CAMERAS')
scene.collection.children.link(cameras)

def camera(name,location,target,scale):
    data=bpy.data.cameras.new(name); data.type='ORTHO'; data.ortho_scale=scale
    data.clip_start=.05; data.clip_end=10000
    ob=bpy.data.objects.new(name,data); cameras.objects.link(ob); ob.location=location
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob

views={
 'overview':camera('CAM_overview',(680,-900,620),(0,40,215),950),
 'site_plan':camera('CAM_site_plan',(0,65,1000),(0,65,0),560),
 'trident':camera('CAM_trident',(55,-151,35),(55,-86.5,20),48),
 'lobby':camera('CAM_lobby_inside',(76,-76,11),(52,-53,10),44),
 'globe':camera('CAM_plaza_globe',(18,-28,19),(0,0,PLAZA_Z+4.0),26),
 'roof1':camera('CAM_roof_WTC1',(24,-56,470),(-55,55,419),110),
 'roof2':camera('CAM_roof_WTC2',(140,-148,470),(55,-55,419),115),
 'antenna':camera('CAM_antenna',(70,-80,494),(-55,55,472),160),
 'mep':camera('CAM_MEP_cutaway',(-5,-5,446),(-55,55,410),83),
 'hat_truss':camera('CAM_hat_truss',(-5,-5,447),(-55,55,411),90),
 'core':camera('CAM_core_cutaway',(245,-280,260),(55,-55,210),450),
 'steel_panels':camera('CAM_segmented_steel',(253,-154,10),(245,-140,5.3),14.5),
 'section':camera('CAM_steel_cover_section',(247.1,-142.8,3.4),(245.4,-140,.95),2.4),
 'wtc7':camera('CAM_WTC7',(190,65,160),(-20,230,93),260),
 'lowrise':camera('CAM_WTC3_6',(310,-310,220),(30,-20,50),440),
 'roof_plan':camera('CAM_roof_plan',(55,-55,560),(55,-55,415),78),
}
views['lobby'].data.type='PERSP'
views['lobby'].data.lens=20
views['lobby'].location=(73,-73,PLAZA_Z+1.7)
views['lobby'].rotation_euler=(Vector((52,-50,PLAZA_Z+4))-views['lobby'].location).to_track_quat('-Z','Y').to_euler()

from review import create_detail_cameras,render_reviews
create_detail_cameras()
render_reviews()
scene['coordinate_datum']='Concourse El.310 ft = z0; Plaza El.332 ft = z6.7056m'
scene['quality_status']='detailed procedural CG study with photo-interpreted crown/roof/plaza; unmeasured dimensions tagged'
for col in scene.collection.children:
    if col.name.startswith(('WTC','PLAZA')) and any(o.type=='MESH' for o in col.all_objects):
        col.asset_mark()
        col.asset_data.description=col.get('confidence','WTC procedural study. Read collection source tags.')
        if col.name.startswith('WTC1'): col.instance_offset=(-55,55,416.9664 if 'antenna' in col.name else 0)
        elif col.name.startswith('WTC2'): col.instance_offset=(55,-55,0)
        elif col.name.startswith('WTC7'): col.instance_offset=(-20,230,0)
for col in bpy.data.collections:
    if any(s in col.name for s in ('_CROWN_photo','_CORNER_aluminum','_ROOF_detail','_CORE_roof_connections','PLAZA_furniture')):
        col.asset_mark();col.asset_data.description=col.get('confidence','CG study')
        if col.name.startswith('WTC1'): col.instance_offset=(-55,55,0)
        elif col.name.startswith('WTC2'): col.instance_offset=(55,-55,0)
scene.render.filepath='//renders/preview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wtc_detailed_cg.blend'),compress=True)
(ROOT/'assets').mkdir(exist_ok=True)
from asset_export import export_assets
export_assets()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wtc_detailed_cg.blend'),compress=True)
