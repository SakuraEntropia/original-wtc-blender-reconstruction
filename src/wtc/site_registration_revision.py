"""Bounded SKA55 image registration; never presented as georeferenced survey."""
import math,re
import bpy
from mathutils import Matrix,Vector
from .interior_parts import collection,finish,Parts
from .lobby_plan_revision import slab_mesh
from .crown_site_detail import annulus
from .completion import PLAZA_Z
from .planar import clip,subtract_convex,regular_polygon,extrude_union

VERSION='2026-10-16-SKA55-plaza-registration-v1'
SOURCE='Original SKA55/84 plaza plan: https://www.wtcexplained.com/complex/assets/main-plaza-source-overlay.jpg; LOC2021636621 lower fountain terrace photograph'
LIMIT='Manual plan/image registration using tower width; not georeferenced or independently surveyed. Stair rise, paving pitch, planter profile, planting and most small dimensions fitted; later1995/2001 changes unresolved.'
OLD={'WTC1':(-55,55),'WTC2':(55,-55),'WTC3':(-112,-67),'WTC4':(128,-95),'WTC5':(129,72),'WTC6':(-82,150),'WTC7':(-20,230)}
NEW={'WTC1':(-55,55),'WTC2':(10,-45),'WTC3':(-59,-30),'WTC4':(100,-35),'WTC5':(82,108),'WTC6':(-66,130),'WTC7':(-27,204)}
SCALE={'WTC5':(420/330,330/420),'WTC6':(1.33,1.80)}
FOUNTAIN=(38,52);LOWER=PLAZA_Z-.90


def matrix(tower):
    x,y=OLD[tower];a,b=NEW[tower];sx,sy=SCALE.get(tower,(1,1))
    return Matrix.Translation((a,b,0))@Matrix.Diagonal((sx,sy,1,1))@Matrix.Translation((-x,-y,0))


def center(tower):return NEW[tower] if bpy.context.scene.get('site_registration_revision')==VERSION else OLD[tower]


def register():
    # Location/rotation assignments on new datablocks do not refresh
    # matrix_world until the dependency graph updates. Read real transforms.
    bpy.context.view_layer.update()
    for ob in list(bpy.context.scene.objects):
        key=next((t for t in OLD if ob.name.startswith(t)),None)
        if key and not ob.get('site_registered'):
            ob.matrix_world=matrix(key)@ob.matrix_world;ob['site_registered']=VERSION;ob['site_registration_source']=SOURCE
    for c in bpy.data.collections:
        key=next((t for t in NEW if c.name.startswith(t)),None)
        if key and c.asset_data:c.instance_offset=(*NEW[key],0)


def sync_world_annotations():
    for ob in bpy.context.scene.objects:
        if not ob.get('site_registered') or ob.get('site_world_annotations_synced'):continue
        keys=[key for key in ob.keys() if key.endswith('_world')]
        if not keys:continue
        tower=next((t for t in NEW if ob.name.startswith(t)),None)
        if tower:
            transform=matrix(tower)
            for key in keys:
                value=ob.get(key)
                if key.endswith('_world') and hasattr(value,'__len__') and len(value)==3:
                    ob['site_canonical_'+key]=list(value);ob[key]=list(transform@Vector(value))
        ob['site_world_annotations_synced']=True


def tile(col,name,parts,mat,z):
    # Material append scans every object in this large scene. Copy one empty
    # material-bearing seed; every tile still receives its own unique mesh.
    seed=bpy.data.meshes.get('zz_PLAZA_empty_material_seed')
    if seed is None:
        seed=bpy.data.meshes.new('zz_PLAZA_empty_material_seed');seed.materials.append(mat)
    v,f=extrude_union(parts,z,z+.03);m=seed.copy();m.name='zz_'+name+'_unique_mesh';m.from_pydata(v,[],f)
    o=bpy.data.objects.new('zz_'+name,m);col.objects.link(o);o['mesh_unique']=True;o['module']='plaza_paver';o['finished_z_m']=z+.03;o['source']=SOURCE;o['confidence']=LIMIT
    from .planar import area
    o['clipped_boundary']=sum(area(p) for p in parts)<1.21**2-1e-6
    return o


def plaza():
    col=bpy.data.collections['PLAZA_individual_tile_meshes_STUDY']
    parents=[c for c in (bpy.context.scene.collection,*bpy.data.collections) if col in c.children[:]]
    for parent in parents:parent.children.unlink(col)
    old=[o for o in col.objects if o.get('mesh_unique')]
    if old:bpy.data.batch_remove(ids=old)
    col['source']=SOURCE;col['confidence']=LIMIT;col.instance_offset=(*FOUNTAIN,0)
    for name in ('PLAZA_furniture_and_landscape_interpretation','PLAZA_vegetation_TYPE'):
        c=bpy.data.collections.get(name)
        if c:c.hide_render=True;c.hide_viewport=True;c['superseded_by']='PLAZA_SOURCE_aligned_terraces'
    c=bpy.data.collections.get('PLAZA_SOURCE_aligned_terraces')
    if c:bpy.data.batch_remove(ids=list(c.objects))
    else:c=collection('PLAZA_SOURCE_aligned_terraces',bpy.context.scene.collection,SOURCE,LIMIT,FOUNTAIN)
    p=Parts('PLAZA_REGISTERED',c)
    stone=finish('PLAZA_registered_granite',(.57,.55,.49),0,.65,950)
    dark=finish('PLAZA_paving_inlay',(.25,.25,.22),.10,.65)
    soil=finish('PLAZA_curved_bed_soil',(.055,.041,.025),0,.99,500)
    green=finish('PLAZA_bed_planting_TYPE',(.14,.20,.075),0,.93,190)
    fx,fy=FOUNTAIN
    main=[(-23.4278,-13.4278),(86,-13.4278),(86,94),(-23.4278,94)]
    circle=regular_polygon(fx,fy,22.05,128)
    # Architectural rectangle follows the tower door thresholds, not an arbitrary square.
    platform=slab_mesh('PLAZA_source_platform_with_terrace_opening',main,[circle],.25,stone)
    p.mesh('platform',platform,(0,0,PLAZA_Z-.015),kind='source_plaza_platform')
    footprints=[]
    from .podium_parking_revision import FOOTPRINTS
    for spec in FOOTPRINTS.values():
        poly=spec['base']
        # Convex decomposition preserves re-entrant podium corners in paving cuts.
        from mathutils.geometry import tessellate_polygon
        verts=[Vector((x,y,0)) for x,y in poly]
        for tri in tessellate_polygon([verts]):
            pts=[verts[v] if isinstance(v,int) else v for v in tri]
            triangle=[(v.x,v.y) for v in pts]
            if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(triangle,triangle[1:]+triangle[:1]))<0:triangle.reverse()
            footprints.append(triangle)
    for ob in bpy.context.scene.objects:
        if not FOOTPRINTS and re.fullmatch(r'WTC(?:3_Marriott|4|5|6)_volume_\d+_STUDY',ob.name):
            pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];x0=min(v.x for v in pts);x1=max(v.x for v in pts);y0=min(v.y for v in pts);y1=max(v.y for v in pts)
            footprints.append([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
    print('REGISTERED_PLAZA_BUILDING_FOOTPRINTS '+str(len(footprints)),flush=True)
    # Each slab is a separate mesh, including exact curved boundary cuts.
    pitch=1.22;gap=.010;count=0
    for ix in range(math.floor(main[0][0]/pitch),math.ceil(main[1][0]/pitch)):
        for iy in range(math.floor(main[0][1]/pitch),math.ceil(main[2][1]/pitch)):
            x,y=(ix+.5)*pitch,(iy+.5)*pitch;h=(pitch-gap)/2
            if math.hypot(x-fx,y-fy)<22.05-h*1.42:continue
            poly=[(x-h,y-h),(x+h,y-h),(x+h,y+h),(x-h,y+h)]
            for a,b in zip(main,main[1:]+main[:1]):poly=clip(poly,a,b)
            if not poly:continue
            parts=[poly]
            for cutter in [circle]+footprints:
                if max(v[0] for v in cutter)<x-h or min(v[0] for v in cutter)>x+h or max(v[1] for v in cutter)<y-h or min(v[1] for v in cutter)>y+h:continue
                parts=[q for part in parts for q in subtract_convex(part,cutter)]
            if parts:tile(col,f'plaza_tile_SOURCE_{ix}_{iy}',parts,stone,PLAZA_Z);count+=1
    # Five circular courses on the lower terrace meet the eight short stairs.
    for ring in range(5):
        r0=12.65+ring*(18.60-12.65)/5;r1=12.65+(ring+1)*(18.60-12.65)/5
        for j in range(96):
            o=annulus(f'plaza_radial_paver_SOURCE_{ring}_{j}',r0+.005,r1-.005,LOWER,LOWER+.03,col,stone,FOUNTAIN,j*math.tau/96+.0003,(j+1)*math.tau/96-.0003,3)
            o['mesh_unique']=True;o['module']='plaza_radial_paver';o['finished_z_m']=LOWER+.03;o['source']=SOURCE;o['confidence']=LIMIT
    # Curved planters with stairs in the gaps replace24 arbitrary circular pots.
    for sector in range(8):
        a=sector*math.tau/8
        annulus(f'PLAZA_curved_planter_{sector}',18.8,21.95,LOWER,PLAZA_Z+.45,c,stone,FOUNTAIN,a+.105,a+math.tau/8-.105,20)
        annulus(f'PLAZA_curved_soil_{sector}',19.1,21.65,PLAZA_Z+.445,PLAZA_Z+.46,c,soil,FOUNTAIN,a+.12,a+math.tau/8-.12,20)
        annulus(f'PLAZA_curved_low_planting_{sector}',19.2,21.55,PLAZA_Z+.46,PLAZA_Z+.64,c,green,FOUNTAIN,a+.13,a+math.tau/8-.13,28)
        for j in range(6):
            r0=18.6+j*3.45/6;r1=18.6+(j+1)*3.45/6
            ob=annulus(f'PLAZA_terrace_stair_{sector}_{j}',r0,r1,LOWER-.04,LOWER+(j+1)*.9/6,c,stone,FOUNTAIN,a-.098,a+.098,5);ob['module']='plaza_short_terrace_stair'
        annulus(f'PLAZA_curved_bench_{sector}',18.48,18.78,LOWER+.43,LOWER+.50,c,stone,FOUNTAIN,a+.14,a+math.tau/8-.14,24)
    # Drawn offset paving arcs, bounded to the main open plaza.
    for band,r in enumerate((27,35,44,53)):
        cx,cy=fx-band*.7,fy-band*.4
        for j in range(128):
            a=j*math.tau/128;b=(j+1)*math.tau/128
            poly=[(cx+(r+d)*math.cos(t),cy+(r+d)*math.sin(t)) for d,t in ((-.025,a),(.025,a),(.025,b),(-.025,b))]
            for A,B in zip(main,main[1:]+main[:1]):poly=clip(poly,A,B)
            if poly:
                m=slab_mesh(f'PLAZA_arc_{band}_{j}',poly,[],.003,dark);p.mesh(f'arc_{band}_{j}',m,(0,0,PLAZA_Z+.034),kind='plaza_source_paving_arc')
    # Move existing self-made scale sculpture/pool; no copyrighted mesh is imported.
    old=bpy.data.collections['PLAZA_globe_and_fountain_SCALE_PROXY']
    for ob in old.objects:
        if not bpy.context.scene.get('site_registration_revision'):ob.location+=Vector((fx,fy,-.90))
        if ob.name=='fountain_podium_support_STUDY':ob.hide_render=True;ob.hide_viewport=True
    old.instance_offset=(*FOUNTAIN,0)
    col['actual_tile_mesh_count']=sum(bool(o.get('mesh_unique')) for o in col.objects)
    col['boundary_cut_tile_count']=sum(len(o.data.vertices)>8 for o in col.objects if o.type=='MESH')
    col['pitch_m_CG_fit']=pitch;c['terrace_drop_m_CG_fit']=.90;c['fountain_xy_CG_registered']=list(FOUNTAIN)
    c['building_footprints']=len(footprints)
    bpy.context.scene['individual_plaza_tile_meshes']=col['actual_tile_mesh_count']
    for parent in parents:parent.children.link(col)


def apply():
    scene=bpy.context.scene
    if scene.get('site_registration_revision')==VERSION:
        register()
        sync_world_annotations()
        if not scene.get('plaza_podium_outline_cuts_v2'):
            plaza();scene['plaza_exact_massing_filter']=True
            scene['plaza_podium_outline_cuts_v2']=True
        return
    register();sync_world_annotations();plaza();scene['site_registration_revision']=VERSION
    scene['site_registration_scope']=LIMIT
    scene['plaza_exact_massing_filter']=True
    scene['plaza_podium_outline_cuts_v2']=True


SOUTH_CAMERAS={'CAM_trident','CAM_lobby_inside','CAM_roof_WTC2','CAM_core_cutaway','CAM_roof_plan','CAM_crown_detail','CAM_core_roof_connection','CAM_facade_corner','CAM_sky_lobby_band','CAM_lobby_ceiling','CAM_cap_structure','CAM_crown_miter','CAM_edge_profile','CAM_edge_top','CAM_base_nested_frame','CAM_base_track_ridge','CAM_lobby_mezzanine_plan','CAM_revolving_entrance','CAM_crown_unit_flat','CAM_composite_floor','CAM_composite_end','CAM_elevator_cab','CAM_lobby_stone','CAM_owner_hall','CAM_shell_floor','CAM_chandelier','CAM_lower_border'}


def reset_cameras():
    for o in bpy.data.objects:
        if o.type=='CAMERA' and o.get('camera_site_delta'):
            o.location-=Vector(o['camera_site_delta']);del o['camera_site_delta']


def register_cameras():
    if bpy.context.scene.get('site_registration_revision')!=VERSION:return
    from .render_config import perspective
    for o in bpy.data.objects:
        if o.type!='CAMERA' or o.get('camera_site_delta'):continue
        delta=None
        if o.name in SOUTH_CAMERAS:delta=Vector((*NEW['WTC2'],0))-Vector((*OLD['WTC2'],0))
        elif o.name in ('CAM_WTC7','CAM_WTC7_roof','CAM_WTC7_inside','CAM_WTC7_inside_core'):delta=Vector((*NEW['WTC7'],0))-Vector((*OLD['WTC7'],0))
        elif o.name in ('CAM_plaza_furniture','CAM_plaza_globe','CAM_site_plan','CAM_paving_seam','CAM_plaza_registered'):delta=Vector((*FOUNTAIN,0))
        if delta is not None:
            target=Vector(o.get('review_target_m',(0,0,0)))+delta;o.location+=delta;perspective(o,target,lens=o.data.lens);o['camera_site_delta']=list(delta)
