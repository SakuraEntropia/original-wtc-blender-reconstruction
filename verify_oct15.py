"""Saved-file acceptance for the reported viewport/lobby/roof/GPU defects."""
import bpy,bmesh,json,re
from pathlib import Path


def inspect(check):
    scene=bpy.context.scene
    for tower in ('WTC1','WTC2'):
        hidden=[c for c in bpy.data.collections if c.name.startswith(tower) and c.hide_render]
        check(tower+'_render_hidden_study_collections_also_viewport_hidden',bool(hidden) and all(c.hide_viewport for c in hidden),[c.name for c in hidden])
        retired=[o for o in bpy.data.objects if o.name.startswith(tower) and any(s in o.name for s in ('plaza_lobby_rim','atrium_rail','core_gallery_deck'))]
        check(tower+'_unsupported_atrium_ring_retired',bool(retired) and all(o.hide_render and o.hide_viewport for o in retired),len(retired))
        floor=bpy.data.objects.get(tower+'_continuous_plaza_lobby_floor_STUDY')
        bm=bmesh.new();bm.from_mesh(floor.data)
        valid=all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0;bm.free()
        top=max(v.co.z for v in floor.data.vertices)+floor.location.z
        check(tower+'_retired_continuous_floor_archived',valid and floor.hide_viewport and floor.hide_render,{'top_m':top,'polygons':len(floor.data.polygons)})
        trees=[o for o in bpy.data.objects if re.fullmatch(tower+r'_tree_s\d_\d+',o.name)]
        correct=all(abs(min(v.co.y for v in o.data.vertices)+.25)<1e-5 and not o.modifiers and o.get('separate_three_crests') for o in trees)
        check(tower+'_76_folded_trident_ridges_no_round_modifiers',len(trees)==76 and correct,len(trees))
    for tower in ('WTC1','WTC2'):
        col=bpy.data.collections[tower+'_crown_curved_cladding']
        bottom=col['z_transition_lower_estimated_m'];top=col['z_fascia_bottom_inferred_m']
        check(tower+'_whole_crown_extended_to_AB302_floor_chain',abs(top-bottom-11.176)<1e-4 and col.get('crown_full_height_revision'),
              {'motif_height_m':top-bottom,'FIN107':col['source_FIN107_z_m'],'FIN108':col['source_FIN108_z_m'],'FIN109':col['source_FIN109_z_m'],'FIN110':col['source_FIN110_z_m']})
    col=bpy.data.collections['WTC2_ROOF_observation_and_communications_STUDY']
    floor=next(o for o in col.objects if o.get('module')=='observation_ring_floor')
    # The top is eight annular quads; a full slab would have a central face.
    check('south_observation_ring_has_open_central_well',len(floor.data.vertices)==32 and len(floor.data.polygons)==32,
          {'vertices':len(floor.data.vertices),'faces':len(floor.data.polygons)})
    closed_bad=[];meshes={o.data for o in col.objects if o.type=='MESH' and 'circle_paint' not in o.name}
    for m in meshes:
        bm=bmesh.new();bm.from_mesh(m)
        if not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:closed_bad.append(m.name)
        bm.free()
    check('south_roof_generated_solids_closed_positive',not closed_bad,closed_bad)
    check('south_roof_access_masts_dishes_and_deck_supports',all(any(s in o.name for o in col.objects) for s in
          ('north_access_door','south_access_door','west_comm_dish','east_comm_dish','north_comm_dish','walk_support','maintenance_security_fence','pad_safety_net')),len(col.objects))
    cameras=[o for o in bpy.data.objects if o.type=='CAMERA']
    check('all_review_cameras_perspective',len(cameras)==50 and all(o.data.type=='PERSP' for o in cameras),len(cameras))
    check('saved_cycles_gpu_configuration',scene.render.engine=='CYCLES' and scene.cycles.device=='GPU',scene.get('render_configuration',''))
    path=Path(__file__).parent/'reports/render_runtime.json'
    runtime=json.loads(path.read_text()) if path.exists() else {'views':{}}
    views=runtime['views'];valid=[k for k,v in views.items() if v.get('revision')==scene.get('south_roof_revision') and
        v.get('base_frame_revision')==scene.get('base_frame_revision') and v.get('lobby_revision')==scene.get('source_lobby_plan_revision') and v.get('engine')=='CYCLES' and v.get('cycles_device')=='GPU' and v.get('compute_device_type')=='METAL' and
        v.get('enabled_devices') and v.get('camera_type')=='PERSP' and v.get('seconds',0)>0]
    check('all50_stored_views_have_individually_versioned_GPU_evidence',len(valid)==50,{'rendered_views':len(valid),'devices':scene.get('render_device_names',[])[:],'note':'Per-view revisions distinguish incremental updates from prior images.'})
    evidence=runtime.get('execution_evidence',{})
    lines=evidence.get('cycles_debug_path_tracing_device_lines',[])
    check('cycles_debug_confirms_actual_metal_path_tracing',evidence.get('gpu_path_records')==34 and bool(lines) and all('(Metal)' in line for line in lines),evidence)
    for tower in ('WTC1','WTC2'):
        col=bpy.data.collections[tower+'_LOBBY_curved_mezzanine_and_entrances_STUDY']
        floor=next(o for o in col.objects if o.get('module')=='source_mezzanine_floor')
        miss=not floor.ray_cast((0,87*.3048/2+6,10),(0,0,-1))[0]
        miss2=not floor.ray_cast((0,-87*.3048/2-6,10),(0,0,-1))[0]
        hit=floor.ray_cast((29,0,10),(0,0,-1))[0]
        check(tower+'_actual_two_open_wells_and_outer_balcony',miss and miss2 and hit,{'north_well_open':miss,'south_well_open':miss2,'outer_gallery_present':hit})
        pivots=[o for o in col.objects if 'revolving' in o.name and o.name.endswith('_pivot')]
        wings=[o for o in col.objects if '_glass_wing' in o.name]
        check(tower+'_two_four_wing_revolving_doors',len(pivots)==2 and len(wings)==8,{'pivots':len(pivots),'glass_wings':len(wings)})
        shell=bpy.data.objects[tower+'_concourse_to_tree_glass_STUDY'];openings=[]
        for u in (-4.572,-1.524,1.524,4.572):
            origin=(33.5662,u,8.0) if tower=='WTC1' else (-u,33.5662,8.0)
            direction=(-1,0,0) if tower=='WTC1' else (0,-1,0)
            openings.append(not shell.ray_cast(origin,direction,distance=3)[0])
        check(tower+'_entrance_has_four_real_glass_openings',all(openings),openings)
        bad=[]
        for m in {o.data for o in col.objects if o.type=='MESH'}:
            bm=bmesh.new();bm.from_mesh(m)
            if not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(m.name)
            bm.free()
        check(tower+'_new_lobby_parts_closed_positive',not bad,bad)

    for tower in ('WTC1','WTC2'):
        tree=bpy.data.objects[tower+'_tree_s0_9']
        parts=[bpy.data.objects[tree.name+'_crest_'+label] for label in ('left','middle','right')]
        # Sample the actual stem and branch meshes. All three project forward;
        # outer crests are19mm higher than the middle, with no recessed mouth.
        samples=[]
        for z,positions in (((363-310)*.3048+(9+4/12)*.3048-6.7056,(-.18,0,.18)),
                            ((418+11.5/12-310)*.3048-6.7056,(-1.016,0,1.016))):
            front=[]
            for x in positions:
                candidates=[v.co.y for part in parts for v in part.data.vertices if abs(v.co.z-z)<1e-4 and abs(v.co.x-x)<1e-4 and v.co.y<0]
                front.append(min(candidates) if candidates else 1)
            samples.append(front)
        correct=all(abs(a+.285)<1e-4 and abs(b+.266)<1e-4 and abs(c+.285)<1e-4 for a,b,c in samples)
        check(tower+'_three_positive_crests_middle_lower_each_takes_one_fork',correct,{'stem_and_branch_front_y':samples})
        col=bpy.data.collections[tower+'_BASE_nested_frames_and_transoms_STUDY']
        arches=[o for o in col.objects if o.get('module')=='secondary_lower_arch_frame']
        transoms=[o for o in col.objects if o.get('module')=='grooved_horizontal_transom']
        thirds=[o for o in col.objects if o.get('hierarchy_level')==3]
        check(tower+'_secondary_arches_and_tertiary_pane_frames',len(arches)==144 and bool(thirds),{'arches':len(arches),'third_level_parts':len(thirds)})
        sample=transoms[0]
        slot=sample.ray_cast((0,-1,0),(0,1,0));lip=sample.ray_cast((0,-1,.05),(0,1,0))
        depth=slot[1].y-lip[1].y if slot[0] and lip[0] else -1
        check(tower+'_physical_grooved_transom_meshes',len(transoms)==140 and .0335<depth<.0365,
              {'transoms':len(transoms),'ray_measured_slot_depth_m':depth})
        lintels=[o for o in col.objects if o.get('module')=='first_floor_waisted_lintel']
        m=lintels[0].data if lintels else None
        zs=lambda x:[v.co.z for v in m.vertices if abs(abs(v.co.x)-x)<1e-5]
        middle=zs(0) if m else [];ends=zs(1.099) if m else []
        heights=[max(a)-min(a) if a else -1 for a in (middle,ends)]
        check(tower+'_first_floor_beams_bowed_edges_narrow_in_middle',len(lintels)==72 and abs(heights[0]-.24)<1e-5 and abs(heights[1]-.68)<1e-5,
              {'beams':len(lintels),'actual_middle_end_heights_m':heights,'placement':'plaza +3.03m estimated centre'})
        crests=[o for o in col.objects if o.get('module')=='base_positive_crest']
        bodies=[o for o in bpy.data.objects if re.fullmatch(tower+r'_tree_s\d_\d+',o.name)]
        independent=crests+lintels+bodies
        check(tower+'_body_beam_crests_independent_single_user_meshes',len(crests)==228 and len({o.data.as_pointer() for o in independent})==len(independent) and all(o.data.users==1 for o in independent),
              {'bodies':len(bodies),'waisted_beams':len(lintels),'separate_crests':len(crests),'unique_meshes':len({o.data.as_pointer() for o in independent})})
        bad=[]
        for m in {o.data for o in col.objects}:
            bm=bmesh.new();bm.from_mesh(m)
            if not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(m.name)
            bm.free()
        check(tower+'_nested_frame_solids_closed_positive',not bad,bad)
