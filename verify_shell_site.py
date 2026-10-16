"""Independent saved-scene acceptance for the current source/shell batch."""
import bpy,bmesh,math
from mathutils import Vector
from pathlib import Path
import json


def inspect(check):
    from wtc.site_registration_revision import NEW,FOUNTAIN
    for t in ('WTC1','WTC2'):
        c=bpy.data.collections[t+'_WHOLE_FLOOR_shell_structure'];floors=[o for o in c.objects if o.get('module')=='whole_floor_structure']
        check(t+'_104_actual_floor_structures',len(floors)==104 and {o['floor'] for o in floors}==set(range(7,111)),len(floors))
        placement=all((o.location-Vector((*NEW[t],bpy.data.objects[t+f"_F{o['floor']:03d}_SLAB_STUDY"].location.z+.1))).length<1e-4 and abs(o.rotation_euler.z-(0 if t=='WTC1' else math.pi/2))<1e-5 for o in floors)
        check(t+'_actual_floor_instances_at_registered_storey_positions',placement,{'center':NEW[t],'sample':list(floors[0].location)})
        expected={9:12,43:12,67:6 if t=='WTC1' else 1,83:9,106:10 if t=='WTC1' else 1,109:13}
        actual={o['floor']:o['source_floor_type'] for o in floors}
        check(t+'_G1_floor_taxonomy_instantiated',all(actual[n]==v for n,v in expected.items()),{'TableG1_expected':expected,'actual':{n:actual[n] for n in expected}})
        ring=bpy.data.objects[t+'_F020_SLAB_STUDY'];hit=ring.ray_cast((0,0,1),(0,0,-1))[0]
        check(t+'_original_floor_proxy_replaced_with_open_core_ring',not hit and 'composite' in ring.data.name,{'core_void':not hit,'mesh':ring.data.name})
        halls=bpy.data.collections[t+'_OWNER_public_halls_and_bare_core'];core=[o for o in halls.objects if o.get('module')=='owner_core_floor'];headers=[o for o in halls.objects if o.get('module')=='owner_core_beams']
        check(t+'_every_floor_has_owner_hall_core_and_headers',len(core)==104 and len(headers)==104 and {o['floor'] for o in halls.objects if o.get('module')=='owner_floor_hall'}==set(range(7,111)),{'core_floors':len(core),'header_grids':len(headers)})
        floor_by_id={o['floor']:o for o in core}
        check(t+'_core_headers_match_floor_world_transforms',all((o.matrix_world.translation-floor_by_id[o['floor']].matrix_world.translation).length<1e-4 and abs(o.rotation_euler.z-floor_by_id[o['floor']].rotation_euler.z)<1e-5 for o in headers),len(headers))
        a=next(o for o in core if o['floor']==10);b=next(o for o in core if o['floor']==19)
        open10=not a.ray_cast((-17.7,-3.1,1),(0,0,-1))[0];closed19=b.ray_cast((-17.7,-3.1,1),(0,0,-1))[0]
        check(t+'_exhausted_bankA_shafts_reclaimed_above18',open10 and closed19,{'F10_void':open10,'F19_slab':closed19})
        frame=bpy.data.collections[t+'_BASE_nested_frames_and_transoms_STUDY'];crests=[o for o in frame.objects if o.get('module')=='base_positive_crest']
        check(t+'_228_independent_smooth_positive_crests',len(crests)==228 and len({o.data for o in crests})==228 and all(any(p.use_smooth for p in o.data.polygons) and o.data.users==1 for o in crests),len(crests))
        finish=bpy.data.collections[t+'_LOBBY_marble_crystal_and_reveals'];lamps=[o for o in finish.objects if o.get('module')=='cylinder_chandelier']
        check(t+'_60_coved_panels_and_cylinder_chandeliers',len(lamps)==60 and sum(o.get('module')=='source_coved_ceiling' for o in finish.objects)==60,{'chandeliers':len(lamps),'panels':sum(o.get('module')=='source_coved_ceiling' for o in finish.objects)})
        check(t+'_actual_chandelier_transforms_above_lobby',bool(lamps) and all(abs(o.location.z-21.52)<1e-4 and math.dist(o.location[:2],NEW[t])<45 for o in lamps),list(lamps[0].location))
        check(t+'_marble_courses_recessed_jambs_and_grilles',sum(o.get('module')=='lobby_jointed_marble_course' for o in finish.objects)>500 and sum(o.get('module')=='lobby_recessed_portal_jamb' for o in finish.objects)>20 and any(o.get('module')=='core_metal_grille_blade' for o in finish.objects),len(finish.objects))
        border=bpy.data.collections[t+'_BASE_tapered_corner_borders'];check(t+'_24_separate_tapered_lower_border_parts',len(border.objects)==24 and all(not o.hide_render and o.type=='MESH' for o in border.objects),24)
        unit=next(o for o in bpy.data.collections[t+'_crown_curved_cladding'].objects if o.get('module')=='crown_flat_joined_unit')
        # Measure a curved-arm slice between stems, so overall two-bay width
        # cannot mask a wrongly rotated thin rectangular section.
        mesh=unit.data;depth=max(v.co.y for v in mesh.vertices)-min(v.co.y for v in mesh.vertices)
        z=unit['lower_transition_height_m']*.473;cuts=[]
        for face in mesh.polygons:
            points=[mesh.vertices[i].co for i in face.vertices];front=[p for p in points if abs(p.y)<1e-7]
            if len(front)==2 and abs(front[0].z-front[1].z)>1e-7 and min(p.z for p in front)<z<max(p.z for p in front):
                a,b=front;cuts.append(a.x+(b.x-a.x)*(z-a.z)/(b.z-a.z))
        cuts=sorted(set(round(x,7) for x in cuts));widths=[b-a for a,b in zip(cuts[::2],cuts[1::2])]
        check(t+'_actual_curved_ribbon_face_slice_6mm',any(abs(w-.006)<2e-5 for w in widths),{'z':z,'solid_widths':widths})
        check(t+'_crown_ribbons_thin_face_broad_normal_full_span',abs(depth-.0635)<1e-6 and abs(unit['branch_width_m']-.006)<1e-7 and max(v.co.x for v in mesh.vertices)-min(v.co.x for v in mesh.vertices)>2.03 and unit['lower_transition_height_m']+unit['upper_transition_height_m']<11.176,{'normal_depth':depth,'face_ribbon_width':unit['branch_width_m']})
    hall=bpy.data.collections['OWNER_LOCAL6_elevator_hall_TEMPLATE'];check('six_car_hall_twelve_recessed_leaves',sum(o.get('module')=='owner_landing_door_leaf' for o in hall.objects)==12,12)
    rods=next(o for o in bpy.data.collections['LOBBY_crystal_cylinder_chandelier_TEMPLATE'].objects if o.get('module')=='chandelier_glass_cylinders')
    bm=bmesh.new();bm.from_mesh(rods.data);remaining=set(bm.verts);components=0
    while remaining:
        components+=1;stack=[remaining.pop()]
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in remaining:remaining.remove(other);stack.append(other)
    bm.free()
    check('chandeliers_have120_physical_glass_rods',components==120,{'connected_cylinders':components,'vertices':len(rods.data.vertices)})
    canopy=bpy.data.collections['WTC1_WEST_glass_pyramid_canopy'];check('north_canopy_40_separate_pyramid_glass_facets',sum(o.get('module')=='canopy_pyramidal_glazing' for o in canopy.objects)==40,40)
    south=bpy.data.objects['WTC2_F020_SLAB_STUDY'];check('south_tower_source_plan_relative_registration',(south.location-Vector((*NEW['WTC2'],south.location.z))).length<1e-5,list(south.location))
    terrace=bpy.data.collections['PLAZA_SOURCE_aligned_terraces'];check('plaza_has48_short_steps_eight_curved_beds',sum(o.get('module')=='plaza_short_terrace_stair' for o in terrace.objects)==48 and sum('PLAZA_curved_planter_' in o.name for o in terrace.objects)==8,len(terrace.objects))
    for t in ('WTC3','WTC4','WTC5','WTC6'):
        c=bpy.data.collections[t+'_SOURCE_outline_architecture'];coords=list(c['base_outline_world_m']);check(t+'_source_nonrectangular_podium_and_roof_details',len(coords)>=12 and any(o.get('module')=='podium_roof_equipment_TYPE' for o in c.objects) and not c.hide_render,{'outline_vertices':len(coords)//2,'objects':len(c.objects)})
    c=bpy.data.collections['SITE_parking_structure_CG_TYPE'];check('parking_two_levels_columns_beams_ramp_and_bays',sum(o.get('module')=='parking_slab' for o in c.objects)==3 and sum(o.get('module')=='parking_column' for o in c.objects)>200 and any(o.get('module')=='parking_ramp' for o in c.objects) and sum(o.get('module')=='parking_bay_line' for o in c.objects)>500 and c['minimum_under_beam_clearance_m']>=2.3,{'ramp_grade':c['ramp_grade_CG'],'headroom':c['minimum_under_beam_clearance_m'],'historical_as_built':c['historical_as_built']})
    roots=[c for c in bpy.data.collections if c.name.startswith(('SHELL_','OWNER_','LOBBY_crystal','WTC3_SOURCE','WTC4_SOURCE','WTC5_SOURCE','WTC6_SOURCE','SITE_parking')) or any(s in c.name for s in ('_OWNER_public','_LOBBY_marble','_BASE_tapered','WEST_glass'))]
    meshes={o.data for c in roots for o in c.objects if o.type=='MESH'};bad=[]
    for m in meshes:
        bm=bmesh.new();bm.from_mesh(m)
        if not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(m.name)
        bm.free()
    check('current_batch_closed_outward_meshes',bool(meshes) and not bad,{'meshes':len(meshes),'bad':bad})
    rt=json.loads((Path(__file__).parent/'reports/render_runtime.json').read_text());keys=('shell_floor','owner_hall','chandelier','lower_border','canopy','plaza_registered','parking','podium_plan')
    versions=('shell_floor_revision','owner_lobby_revision','lobby_finish_revision','site_registration_revision','podium_parking_revision','core_framing_revision')
    check('eight_new_views_current_revision_actual_gpu_renders',all(k in rt['views'] and all(rt['views'][k].get(v)==bpy.context.scene.get(v) for v in versions) and rt['views'][k].get('compute_device_type')=='METAL' for k in keys),list(keys))
    proof=rt.get('shell_site_execution_evidence',{});lines=proof.get('cycles_debug_path_tracing_device_lines',[])
    check('current15_view_batch_actual_Metal_path_tracing',proof.get('unique_completed_view_count')==15 and proof.get('gpu_path_records',0)>=15 and bool(lines) and all('(Metal)' in line for line in lines),{'completed_views':proof.get('unique_completed_view_count'),'gpu_path_records':proof.get('gpu_path_records'),'devices':lines})
