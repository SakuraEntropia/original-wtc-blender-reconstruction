"""Additional saved-file geometry gates for the seven-item corrective batch."""
import bpy,bmesh,math


def inspect(check):
    for tower in ('WTC1','WTC2'):
        curves=[o for o in bpy.data.collections[tower+'_crown_curved_cladding'].objects if o.get('module')=='crown_flat_joined_unit']
        check(tower+'_crown_curves_thin_flat',len(curves)==116 and all(abs(o.get('branch_width_m',0)-.006)<1e-5 for o in curves),len(curves))
        support=bpy.data.collections.get(tower+'_CROWN_CAP_steel_support_TYPE')
        check(tower+'_cap_independent_support',support and len(support.objects)>300,len(support.objects) if support else 0)
        edge_frames=bpy.data.collections.get(tower+'_FACADE_corner_transition_frames')
        check(tower+'_glass_corner_transition_frames',edge_frames and len(edge_frames.objects)>700,len(edge_frames.objects) if edge_frames else 0)
        cap=bpy.data.collections.get(tower+'_CROWN_CAP_mitered_panels')
        check(tower+'_mitered_coping8_edges',cap and sum(o.get('module')=='cap_mitered_coping' for o in cap.objects)==8,len(cap.objects) if cap else 0)
        facade=bpy.data.collections.get(tower+'_FACADE_REVISION')
        facade_objects=list(facade.all_objects) if facade else []
        frames=[o for o in facade_objects if o.get('module')=='raised_window_frame']
        check(tower+'_raised_window_frames_sourced',len(frames)>=376 and all(abs(o.get('frame_width_m',.0254)-.0254)<1e-6 for o in frames),len(frames))
        corner=[o for o in facade_objects if o.get('module')=='original_corner_panel']
        groups={}
        for o in corner:groups.setdefault((o.get('edge'),o.get('story_index')),set()).add(o.get('panel_index'))
        check(tower+'_corner_three_panels_per_story',bool(groups) and all(v=={1,2,3} for v in groups.values()),len(groups))
        sky=[o for o in facade_objects if o.get('module')=='sky_lobby_window']
        check(tower+'_sky_lobby44_78_eight_panels',len(sky)==8 and {o.get('floor') for o in sky}=={44,78} and all(abs(o.get('opening_height_m')-8.4166666667*.3048)<1e-6 for o in sky),len(sky))
        mech=[o for o in facade_objects if o.get('module')=='mechanical_cover_fins']
        check(tower+'_MER_fins_7inch_projection',len(mech)==8 and all(abs(o.get('fin_projection_m')-.1778)<1e-6 for o in mech),len(mech))
        root=bpy.data.collections.get(tower+'_LOBBY_photo_interpretation_STUDY')
        objs=list(root.all_objects) if root else []
        check(tower+'_modular_lobby_ceiling',any('_coffer_' in o.name for o in objs),len(objs))
        check(tower+'_lobby_core_finish',sum('upper_reflective_panel' in o.name for o in objs)>20,
              sum('upper_reflective_panel' in o.name for o in objs))
        check(tower+'_lobby_operative_lights',sum(o.type=='LIGHT' and o.data.energy>0 for o in objs)>=4,
              sum(o.type=='LIGHT' for o in objs))
    col=bpy.data.collections.get('WTC7_ROOF_NIST_plan_interpretation')
    objs=list(col.objects) if col else []
    check('WTC7_two_penthouses',sum('_penthouse_enclosure_PLAN' in o.name for o in objs)==2,
          [o.name for o in objs if '_penthouse_enclosure_PLAN' in o.name])
    check('WTC7_five_north_cooling_outlets',sum('north_cooling_tower' in o.name and '_fan_shroud' in o.name for o in objs)==5,
          [o.name for o in objs if 'north_cooling_tower' in o.name and '_fan_shroud' in o.name])
    check('WTC7_open_equipment_court',sum('yard_screenwall_' in o.name for o in objs)==2,
          [o.name for o in objs if 'yard_screenwall_' in o.name])
    check('WTC7_vertical_intake_louvers',sum('north_F46_47_intake_vertical_blade' in o.name for o in objs)>100,
          sum('north_F46_47_intake_vertical_blade' in o.name for o in objs))
    old=bpy.data.collections.get('WTC7_ROOF_detail_components')
    check('WTC7_old_generic_plant_suppressed',old and old.hide_render,old.name if old else None)
    tiles=[o for o in bpy.data.objects if o.get('clipped_boundary')]
    bad=[]
    for o in tiles:
        bm=bmesh.new();bm.from_mesh(o.data)
        if not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(o.name)
        bm.free()
    check('conforming_paver_boundary_closed',len(tiles)>100 and not bad,{'tiles':len(tiles),'bad':bad})
    check('paving_revision_saved',bool(bpy.context.scene.get('paving_boundary_revision')),bpy.context.scene.get('paving_boundary_revision'))
    # Each clipped square lies outside the fountain's polygonal outer edge.
    from wtc.site_registration_revision import FOUNTAIN
    threshold=22.05*math.cos(math.pi/128)-1e-4
    near=[]
    for o in tiles:
        for v in o.data.vertices:
            p=o.matrix_world@v.co
            if math.hypot(p.x-FOUNTAIN[0],p.y-FOUNTAIN[1])<threshold:near.append(o.name);break
    check('cut_pavers_clear_fountain',not near,near)
