"""Saved geometry checks for requested interior, frame and floor additions."""
import bpy,bmesh,json
from pathlib import Path
from wtc.facade_revision import _story_schedule,FT


def inspect(check):
    n={r['level']:r for r in _story_schedule(1368*FT)};s={r['level']:r for r in _story_schedule(1362*FT)}
    check('North43_14ft_North67_16ft_South_both12ft',abs(n[43]['pitch']-14*FT)<1e-6 and abs(n[67]['pitch']-16*FT)<1e-6 and abs(s[43]['pitch']-12*FT)<1e-6 and abs(s[67]['pitch']-12*FT)<1e-6,
          {'N43':n[43]['pitch'],'N67':n[67]['pitch'],'S43':s[43]['pitch'],'S67':s[67]['pitch']})
    check('six_foot_difference_allocated_once',abs(n[44]['z']-s[44]['z']-2*FT)<1e-5 and abs(n[68]['z']-s[68]['z']-6*FT)<1e-5,
          {'F44_difference_m':n[44]['z']-s[44]['z'],'F68_difference_m':n[68]['z']-s[68]['z']})
    for tower,rows in (('WTC1',n),('WTC2',s)):
        check(tower+'_slabs_follow_revised_facade_datums',all(abs(bpy.data.objects[tower+f'_F{k:03d}_SLAB_STUDY'].location.z-r['z'])<3e-5 for k,r in rows.items()),len(rows))
        col=bpy.data.collections[tower+'_FLOOR_composite_truss_panel_DETAIL']
        seats=[o for o in col.objects if o.get('module')=='slotted_connection_seat']
        # Slots are real holes through closed plates, with bolts as separate solids.
        hole=seats[0].ray_cast((.105,0,1),(0,0,-1))[0]
        solid=seats[0].ray_cast((0,.08,1),(0,0,-1))[0]
        check(tower+'_end_seat_slots_are_geometry',len(seats)==12 and not hole and solid,{'seats':len(seats),'slot_open':not hole,'solid_web':solid})
        deck=next(o for o in col.objects if o.get('module')=='corrugated_metal_deck')
        check(tower+'_six_physical_connection_hosts',sum(o.get('module')=='connection_host_column_TYPE' for o in col.objects)==6,len(col.objects))
        check(tower+'_profiled_deck_bridging_rods_and_concrete',len(deck.data.vertices)>100 and sum(o.get('module')=='bridging_truss' for o in col.objects)>30 and any(o.get('module')=='shear_knuckle' for o in col.objects),len(col.objects))
        frame=bpy.data.collections[tower+'_BASE_nested_frames_and_transoms_STUDY']
        check(tower+'_lower_corner_terminal_projections_present',all(o.hide_render and o.hide_viewport for o in frame.objects if o.get('module')=='base_end_corner_projection') and len(bpy.data.collections[tower+'_BASE_tapered_corner_borders'].objects)==24,{'retired_tabs':32,'tapered_parts':24})
        rugs=bpy.data.collections[tower+'_LOBBY_stone_carpet_lamps_DETAIL']
        check(tower+'_carpets_jointed_stone_and_actual_lights',sum(o.get('module')=='carpet_zone' for o in rugs.objects)>=12 and sum(o.type=='LIGHT' for o in rugs.objects)==12 and any(o.get('module')=='jointed_stone_fascia' for o in rugs.objects),len(rugs.objects))
        c=bpy.data.collections[tower+'_ELEVATOR_cab_and_mechanism_TYPE']
        check(tower+'_lift_portal_backing_opened',bpy.data.objects[tower+'_LR_core_s0_opaque_inner_wall_STUDY'].hide_render and c.objects.get(tower+'_LIFT_core_backing_head') is not None,'Replaced closed backing with three separate wall parts')
        check(tower+'_editable_lift_doors_guides_weight_ropes_operator',all(any(s in o.name for o in c.objects) for s in ('landing_door','guide','counterweight','rope_car','door_operator_motor','traction_sheave')),len(c.objects))
    c=bpy.data.collections['WTC7_INTERIOR_NIST_core_and_public_lobbies']
    cars=[o for o in c.objects if 'elevator_number' in o]
    check('WTC7_31_elevators_per_NIST_primary_source',{o['elevator_number'] for o in cars}==set(range(1,32)),len(cars))
    check('WTC7_lobbies_stairs_escalators_and_floor4_atrium',all(any(s in o.name for o in c.objects) for s in ('stair0','stair1','escalator0','escalator1','fire_command_desk','floor04')),len(c.objects))
    c=bpy.data.collections['WTC1_WINDOWS_1977_Platner_STUDY']
    check('Windows_original_period_and_functional_components',c.get('period')=='1976/1977' and all(any(s in o.name for o in c.objects) for s in ('table','chair','gallery_arch','bar_counter','ivory_half_column','banquet_partition')),{'period':c.get('period'),'parts':len(c.objects)})
    cols=[c for c in bpy.data.collections if any(s in c.name for s in ('_LOBBY_stone_carpet','_ELEVATOR_cab','WINDOWS_1977','_INTERIOR_NIST','_FLOOR_composite'))]
    bad=[]
    for m in {o.data for c in cols for o in c.objects if o.type=='MESH'}:
        bm=bmesh.new();bm.from_mesh(m)
        if not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(m.name)
        bm.free()
    check('new_interior_and_floor_parts_closed_positive',len(cols)==8 and not bad,{'modules':len(cols),'failed':bad})
    rt=json.loads((Path(__file__).parent/'reports/render_runtime.json').read_text())
    keys=('wtc7_interior','wtc7_core','floor_structure','floor_end','elevator','restaurant','stone','north_heights','overview','lobby','lobby_ceiling','balcony','revolving','base_frame')
    versions=('floor_schedule_revision','public_interiors_revision','wtc7_interior_revision','floor_structure_revision')
    valid=[k for k in keys if all(rt['views'].get(k,{}).get(v)==bpy.context.scene.get(v) for v in versions)]
    check('latest14_views_rendered_for_current_detail_revisions',len(valid)==14,valid)
    proof=rt.get('interior_execution_evidence',{});lines=proof.get('cycles_debug_path_tracing_device_lines',[])
    check('current_interior_batch_actual_Metal_path_tracing',set(keys)<=set(proof.get('completed_views',[])) and proof.get('gpu_path_records',0)>=14 and bool(lines) and all('(Metal)' in line for line in lines),proof)
