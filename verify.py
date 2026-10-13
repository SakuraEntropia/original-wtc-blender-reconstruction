"""Run against the saved .blend; technical checks do not certify historical accuracy."""
import bpy, bmesh, json, math, re, gzip, shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
FT=.3048
PLAZA_Z=22*FT
TREE_TOP=(418+11.5/12-310)*FT
checks=[]

def check(name,passed,evidence):
    checks.append({'name':name,'passed':bool(passed),'evidence':evidence})

def bounds(ob):
    p=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    return {'min_m':[min(v[i] for v in p) for i in range(3)],
            'max_m':[max(v[i] for v in p) for i in range(3)]}

check('reopened_saved_file',Path(bpy.data.filepath).name=='wtc_detailed_cg.blend',Path(bpy.data.filepath).name)
check('restored_overview_camera',bpy.context.scene.camera.name=='CAM_overview',bpy.context.scene.camera.name)
check('review_cameras_saved',len([o for o in bpy.data.objects if o.name.startswith('CAM_')])==20,
      [o.name for o in bpy.data.objects if o.name.startswith('CAM_')])
for name in ('WTC1','WTC2'):
    trees=[o for o in bpy.data.objects if re.fullmatch(name+r'_tree_s\d_\d+',o.name)]
    check(name+'_76_tree_modules',len(trees)==76,len(trees))
    manifold=True; positive=True; aligned=True
    for ob in trees:
        bm=bmesh.new(); bm.from_mesh(ob.data)
        manifold &= all(e.is_manifold for e in bm.edges)
        positive &= bm.calc_volume(signed=True)>0
        bm.free()
        b=bounds(ob)
        aligned &= abs(b['min_m'][2]-PLAZA_Z)<1e-4 and abs(b['max_m'][2]-TREE_TOP)<1e-4
    check(name+'_tree_closed_outward_meshes',manifold and positive,{'closed':manifold,'positive_volume':positive})
    check(name+'_tree_vertical_datums',aligned,{'plaza_m':PLAZA_Z,'upper_splice_m':TREE_TOP})
    for side in range(1,5):
        cols=[o for o in bpy.data.objects if o.name.startswith(name+'_') and o.get('module')=='steel_column' and o.get('face')==side]
        axes={o.get('axis_index') for o in cols}
        check(name+f'_face{side}_59_segmented_axes',axes==set(range(59)),{'axes':len(axes),'steel_segments':len(cols)})
        check(name+f'_face{side}_no_full_height_steel',all(o.dimensions.z<12 for o in cols),max(o.dimensions.z for o in cols))
    a=bpy.data.objects[name+'_face1_axis00_seg000_steel']; b=bpy.data.objects[name+'_face1_axis01_seg000_steel']
    check(name+'_column_pitch_1_016m',abs((b.location-a.location).length-1.016)<1e-4,(b.location-a.location).length)
    upper=bpy.data.objects[name+'_upper_wall_face1_member01_STUDY']
    check(name+'_upper_tube_7x5in',abs(upper.dimensions.x-7/12*FT)<1e-5 and abs(upper.dimensions.y-5/12*FT)<1e-5,
          list(upper.dimensions))
    core=[o for o in bpy.data.objects if o.name.startswith(name+'_') and o.get('module')=='core_steel_column']
    check(name+'_47_segmented_core_axes',len({o.get('axis_index') for o in core})==47,{'axes':len({o.get('axis_index') for o in core}),'segments':len(core)})
    slabs=[o for o in bpy.data.objects if re.fullmatch(name+r'_F\d{3}_SLAB_STUDY',o.name)]
    check(name+'_110_floor_datums',len(slabs)==110,len(slabs))
    actual=[list(bpy.data.objects[name+f'_F{i:03d}_SLAB_STUDY'].dimensions) for i in (3,4,5,6)]
    check(name+'_F3_F6_core_only',all(max(d[:2])<43 for d in actual),actual)
    check(name+'_envelope_restored_visible',not bpy.data.objects[name+'_envelope_208ft10in'].hide_render,'exterior render state')
    bottom=bounds(bpy.data.objects[name+'_concourse_to_tree_glass_STUDY'])
    check(name+'_bottom_curtain_wall',abs(bottom['min_m'][2])<1e-5 and abs(bottom['max_m'][2]-TREE_TOP)<1e-4,bottom)
    top=bounds(bpy.data.objects[name+'_crown_glazing_to_cap_STUDY'])
    roof=1368*FT if name=='WTC1' else 1362*FT
    check(name+'_crown_curtain_wall_to_opaque_cap',abs(top['max_m'][2]-(roof-2.4))<1e-4 and abs(top['min_m'][2]-(roof-17))<1e-4,top)
    end_heights=[]
    for axis in range(47):
        parts=[o for o in core if o.get('axis_index')==axis]
        last=max(parts,key=lambda o:o.location.z)
        end_heights.append(last.location.z+max(v.co.z for v in list(last.data.vertices)[:16]))
    check(name+'_all_47_core_axes_reach_roof',all(abs(z-roof)<.001 for z in end_heights),{'body_endpoint_min_m':min(end_heights),'body_endpoint_max_m':max(end_heights),'roof_m':roof})
    panels=[o for o in bpy.data.objects if o.name.startswith(name+'_crown_cap_edge') and o.get('module')=='sloping_cap_panel']
    check(name+'_cap_all_8_edges_independent_panels',{o.get('edge') for o in panels}==set(range(8)),len(panels))
    check(name+'_pointed_arch_geometry',sum(o.name.startswith(name+'_crown_S') and '_arch' in o.name for o in bpy.data.objects)==464,'58 pointed arches / face, two prongs per arch; photo interpretation')
    cap=bpy.data.objects[name+'_roof_datum']
    check(name+'_eight_sided_roof',len(cap.data.vertices)==16,len(cap.data.vertices))

tiles=[o for o in bpy.data.objects if o.get('mesh_unique')]
check('each_plaza_tile_unique_mesh',len({o.data.as_pointer() for o in tiles})==len(tiles),len(tiles))
check('plaza_tile_z_datum',all(abs(bounds(o)['min_m'][2]-PLAZA_Z)<1e-4 and abs(bounds(o)['max_m'][2]-(PLAZA_Z+.03))<1e-4 for o in tiles),PLAZA_Z)
check('orange_antenna_proxy_removed',not bpy.data.objects.get('WTC1_antenna_360ft_height_proxy'),'one mast assembly remains')
check('generic_globe_present',bpy.data.objects.get('generic_15ft_globe_mass_proxy_NOT_Koenig_replica') is not None,
      'generic sculpture scale proxy; faithful artwork reproduction excluded')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
ownership={o.name:[] for o in meshes}
for c in bpy.data.collections:
    for o in c.objects:
        if o.name in ownership:ownership[o.name].append(c)
finite=all(all(math.isfinite(v) for row in ob.matrix_world for v in row) and
           all(math.isfinite(v) for vert in ob.data.vertices for v in vert.co) for ob in meshes)
check('finite_geometry_and_transforms',finite,len(meshes))
check('materials_on_all_scene_meshes',all(len(ob.data.materials)>0 for ob in meshes),len(meshes))
external=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath]
check('no_external_texture_dependencies',not external,external)
render_names=('overview','site_plan','trident','lobby','globe','roof1','roof2','antenna','mep','hat_truss','core','steel_panels','section','wtc7','lowrise','roof_plan','crown','core_top','plaza','mep_detail')
check('20_render_files',all((ROOT/'renders'/('detail_'+s+'.png')).is_file() and (ROOT/'renders'/('detail_'+s+'.png')).stat().st_size>10000 for s in render_names),list(render_names))
check('shadow_pool_expanded',bpy.context.scene.eevee.shadow_pool_size=='2048',bpy.context.scene.eevee.shadow_pool_size)
newparts=[o for o in meshes if any(t in c.name for c in ownership[o.name] for t in ('_CROWN_photo','_CORNER_aluminum','_ROOF_detail','_CORE_roof_connections','PLAZA_furniture','PLAZA_vegetation'))]
newmeshes={o.data for o in newparts};bad=[]
for m in newmeshes:
    bm=bmesh.new();bm.from_mesh(m)
    if not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(m.name)
    bm.free()
check('new_detail_parts_closed_outward',not bad,{'unique_meshes':len(newmeshes),'failed':bad})

parents={}
for col in bpy.data.collections:
    for c in col.children: parents[c.name]=col

def context(ob):
    values=[]
    for direct in ownership[ob.name]:
        col=direct
        while col:
            for k in ('source','confidence','estimated','limits','status','program_source','verified','height_source'):
                if col.get(k): values.append(str(col[k]))
            col=parents.get(col.name)
    return list(dict.fromkeys(values))

manifest=[]
for ob in meshes:
    b=bounds(ob)
    manifest.append({'object':ob.name,'collections':[c.name for c in ownership[ob.name]],
                     'bounds':b,'world_axis_extent_m':[b['max_m'][i]-b['min_m'][i] for i in range(3)],
                     'mesh':ob.data.name,'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),
                     'materials':[m.name for m in ob.data.materials if m],
                     'evidence':{k:str(ob[k]) for k in ob.keys() if k!='_RNA_UI'},
                     'inherited_evidence':context(ob),
                     'uncertainty_m':None,
                     'uncertainty_note':'Original source measurement tolerance not supplied; CG-only dimensions remain unquantified, see evidence and source table.'})
(ROOT/'reports').mkdir(exist_ok=True)
(ROOT/'reports'/'geometry_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'reports'/'geometry_manifest.json').open('rb') as src,gzip.open(ROOT/'reports'/'geometry_manifest.json.gz','wb',compresslevel=6) as dst:
    shutil.copyfileobj(src,dst)
report={'technical_checks':checks,'technical_check_count':len(checks),'technical_pass':all(c['passed'] for c in checks),
        'historical_production_ready':False,
        'historical_blockers':['corner tree/return plates not transcribed','full floor elevations and core shafts unverified',
          'lobby/sky lobby/public-floor layouts and finishes schematic','MER equipment reference transferred from 75/76 to top without as-built plan',
          'rooftop and antenna component dimensions/layout estimated','WTC3-7/site footprints and georeference incomplete',
          'Koenig sculpture is only a generic scale proxy','basement/PATH/retail and full MEP distribution absent'],
        'statistics':{'objects':len(bpy.context.scene.objects),'scene_mesh_objects':len(meshes),
                      'unique_scene_meshes':len({o.data.as_pointer() for o in meshes}),
                      'plaza_tile_meshes':len(tiles),'materials':len(bpy.data.materials),
                      'mesh_faces':sum(len(m.polygons) for m in bpy.data.meshes if m.users),
                      'instanced_base_mesh_faces':sum(len(o.data.polygons) for o in meshes),
                      'faces_in_used_mesh_datablocks':sum(len(m.polygons) for m in bpy.data.meshes if m.users)},
        'blender_version':bpy.app.version_string,
        'publication':{'performed_by_this_verification':False,'status_document':'docs/DELIVERY_STATUS.md / reports/publication.json'}}
(ROOT/'reports'/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'technical_pass':report['technical_pass'],'statistics':report['statistics'],
                  'failed':[c for c in checks if not c['passed']]},ensure_ascii=False))
if not report['technical_pass']: raise RuntimeError('Saved-scene technical checks failed')
