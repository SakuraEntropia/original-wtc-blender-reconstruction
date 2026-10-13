"""Photo-grounded crown/site revisions, with unmeasured dimensions tagged.

No source photograph is embedded. All meshes/materials are generated here.
Rose/Fausty 1981 and JWSmythe 2001 document forms, not fabrication dimensions.
"""
import math
import bpy
from mathutils import Vector
from .facade_detail import outline, material, object_mesh, cover_mesh, REFERENCE_HALF, OUTER_HALF
from .completion import FT, PLAZA_Z, box, cylinder, tube, strut
from .lowrise_detail import cube, subgroup

PHOTO='https://www.brianrose.com/blog/2015/10/new-yorkthe-walk/'
ANTENNA_PHOTO='https://commons.wikimedia.org/wiki/File:2WTC_roof_to_1WTC_roof.jpeg'
PLAZA_PHOTO='https://www.loc.gov/item/2021636621/'
CROWN_DEPTH=17.0

def collection(parent,name,source,confidence):
    return subgroup(parent,name,source,confidence)

def part(name,loc,size,col,mat,angle=0):
    return cube(name,size,loc,angle,col,mat)

def section_extrude(name,profile,z0,z1,col,mat,xy=(0,0)):
    n=len(profile);m=bpy.data.meshes.new(name+'_mesh')
    m.from_pydata([(x,y,z) for z in (z0,z1) for x,y in profile],[],
        [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+
        [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)])
    m.materials.append(mat);return object_mesh(name,m,(*xy,0),col)

def annulus(name,r0,r1,z0,z1,col,mat,xy=(0,0),a0=0,a1=math.tau,n=48):
    # Closed individual wedge/paver or complete annular assembly.
    closed=abs(a1-a0-math.tau)<1e-7
    q=n if closed else n+1
    v=[(xy[0]+r*math.cos(a0+(a1-a0)*i/n),xy[1]+r*math.sin(a0+(a1-a0)*i/n),z)
       for z in (z0,z1) for r in (r0,r1) for i in range(q)]
    f=[]
    for i in range(n):
        j=(i+1)%q
        f.extend(((i,i+2*q,j+2*q,j),(q+i,q+j,q+j+2*q,q+i+2*q),
                  (i,j,q+j,q+i),(i+2*q,q+i+2*q,q+j+2*q,j+2*q)))
    if not closed:f.extend(((0,q,3*q,2*q),(n,n+2*q,n+3*q,n+q)))
    m=bpy.data.meshes.new(name+'_mesh');m.from_pydata(v,[],f);m.materials.append(mat)
    ob=object_mesh(name,m,(0,0,0),col);return ob

def rail(name,a,b,col,mat,width=.11,depth=.12):
    dx,dy=b[0]-a[0],b[1]-a[1]
    return part(name,((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2),
                (math.hypot(dx,dy),width,depth),col,mat,math.atan2(dy,dx))

def crown(name,xy,roof):
    root=bpy.data.collections[name]
    c=collection(root,name+'_CROWN_photo_interpretation',PHOTO,
        'Pointed upper arches, lower diamond transitions and inward sloping cap observed; 17m crown depth, slopes, profiles and plate seams unmeasured CG estimates.')
    metal=bpy.data.materials['silver_cladding_color_study']
    dark=bpy.data.materials['structural_steel_unclad_STUDY']
    frame=next(g for g in root.children if g.name.startswith('02_perimeter'))
    structural=collection(frame,name+'_107_110_structural_types',
        'NIST1-2A §3.2.7 p41: rolled shapes, including7x5in tubes; drawings4-AB3-4/5.2/6/9',
        'Original straight structural type samples retained for inspection, hidden behind photo interpretation; actual fabrication schedule unresolved.')
    structural.hide_render=True
    for ob in list(frame.objects):
        if '_upper_wall_' in ob.name:
            structural.objects.link(ob);frame.objects.unlink(ob)
    covers=next(g for g in frame.children if 'separate_grooved' in g.name)
    cutoff=roof-CROWN_DEPTH
    # Remove ordinary column covers from the special crown and trim crossing parts.
    for ob in list(covers.objects):
        z=ob.location.z;h=max(v.co.z for v in ob.data.vertices)
        if z>=cutoff:bpy.data.objects.remove(ob,do_unlink=True)
        elif z+h>cutoff:
            ob.data=cover_mesh(cutoff-z,metal)
    envelope=next(g for g in root.children if g.name.startswith('01_envelope'))
    for suffix in ('top_lower_glass_STUDY','top_upper_glass_STUDY'):
        ob=bpy.data.objects.get(name+'_'+suffix)
        if ob:ob.hide_render=True
    body=bpy.data.objects[name+'_envelope_208ft10in']
    old_top=max(v.co.z for v in body.data.vertices)
    for v in body.data.vertices:
        if abs(v.co.z-old_top)<.0001:v.co.z=cutoff
    glass=bpy.data.materials['blue_gray_glazing_color_study']
    from .facade_detail import glazing_ring
    glazing_ring(name+'_crown_glazing_to_cap_STUDY',cutoff,roof-2.4,c,glass,xy)
    for side in range(4):
        def point(p,z):
            x,y=xy;q=REFERENCE_HALF+.24
            return ((x+p,y-q,z),(x+q,y+p,z),(x-p,y+q,z),(x-q,y-p,z))[side]
        for i in range(59):
            p=(i-29)*1.016
            railob=strut(f'{name}_crown_S{side}_axis{i}_vertical_STUDY',
                point(p,roof-14.2),point(p,roof-2.47),.19,c,metal)
            railob['module']='crown_vertical';railob['axis_index']=i;railob['face']=side+1
            # Lower diamond transition from the broad ordinary aluminum cover.
            for sign in (-1,1):
                wing=point(p+sign*.29,roof-15.55)
                strut(f'{name}_crown_S{side}_{i}_diamond_low{sign}_STUDY',point(p,cutoff),wing,.12,c,metal)
                strut(f'{name}_crown_S{side}_{i}_diamond_high{sign}_STUDY',wing,point(p,roof-14.2),.12,c,metal)
            if i<58:
                peak=point(p+.508,roof-2.47)
                for endpoint in (p,p+1.016):
                    strut(f'{name}_crown_S{side}_arch{i}_{endpoint:.3f}_STUDY',
                          point(endpoint,roof-4.2),peak,.105,c,metal)
        for level in (roof-14.2,roof-2.44):
            rail(f'{name}_crown_S{side}_horizontal_{level:.2f}_STUDY',point(-29.8,level),point(29.8,level),c,metal,.10,.14)
    # Individual sloped cap panels, including all four 45-degree corner returns.
    outer=outline(OUTER_HALF);inner=outline(OUTER_HALF-1.8,-1.8)
    for e in range(8):
        a,b=outer[e],outer[(e+1)%8];u,w=inner[e],inner[(e+1)%8]
        count=max(1,round(math.dist(a,b)/1.016))
        for j in range(count):
            t0=(j+.012)/count;t1=(j+.988)/count
            A=Vector(a).lerp(Vector(b),t0);B=Vector(a).lerp(Vector(b),t1)
            U=Vector(u).lerp(Vector(w),t0);W=Vector(u).lerp(Vector(w),t1)
            v=[(p.x+xy[0],p.y+xy[1],z) for p,z in ((A,roof-2.4),(B,roof-2.4),(W,roof+.14),(U,roof+.14))]
            v+= [(x,y,z-.045) for x,y,z in v]
            m=bpy.data.meshes.new('crown_sloped_panel_mesh');m.from_pydata(v,[],
                [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])
            m.materials.append(metal)
            ob=object_mesh(f'{name}_crown_cap_edge{e}_panel{j:02d}_STUDY',m,(0,0,0),c)
            ob['module']='sloping_cap_panel';ob['edge']=e
        for ring,z,label in ((outer,roof-2.4,'drip'),(inner,roof+.16,'inner_coping')):
            aa,bb=ring[e],ring[(e+1)%8]
            rail(f'{name}_crown_edge{e}_{label}_STUDY',(*Vector(aa)+Vector(xy),z),(*Vector(bb)+Vector(xy),z),c,metal,.13,.14)
    completion=bpy.data.collections[name+'_COMPLETION_study']
    roofcol=next(g for g in completion.children if g.name.startswith('roof_mechanical'))
    for ob in list(roofcol.objects):
        if '_roof_parapet_' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
    return c

def pipe_details(name,x,y,z,col,metal):
    # Independently selectable type components: flanges, bolts, supports and valve.
    for k in range(3):
        px=x+k*.38
        tube(name+f'_pipe{k}_TYPE',(px,y,z+.30),(px,y+4,z+.30),.065,col,metal)
        for yy in (y+.4,y+3.6):
            flange=cylinder(name+f'_flange{k}_{yy:.1f}_TYPE',(px,yy,z+.3),.115,.055,col,metal,16)
            flange.rotation_euler.x=math.pi/2
            for j in range(6):
                a=j*math.tau/6
                part(name+f'_bolt{k}_{yy:.1f}_{j}_TYPE',(px+.09*math.cos(a),yy-.04,z+.3+.09*math.sin(a)),(.022,.033,.022),col,metal)
        for yy in (y+.8,y+3.1):
            part(name+f'_support{k}_{yy:.1f}_TYPE',(px,yy,z+.14),(.24,.22,.28),col,metal)
        cylinder(name+f'_valve_stem{k}_TYPE',(px,y+2,z+.48),.027,.20,col,metal,12)
        annulus(name+f'_valve_wheel{k}_TYPE',.11,.14,z+.59,z+.62,col,metal,(px,y+2),n=16)

def industrial_detail():
    """Maintainable service-panel and support type geometry for the AHU studies."""
    if bpy.context.scene.get('industrial_component_revision'):return
    trim=material('industrial_service_fixings_TYPE',(.30,.34,.35),.78,.35)
    black=material('industrial_gasket_TYPE',(.024,.03,.032),0,.8)
    indicator=material('industrial_service_indicator_TYPE',(.09,.19,.11),.1,.5)
    cases=[o for o in bpy.data.objects if o.name.endswith('_case_STUDY')]
    for case in cases:
        name=case.name[:-11]
        parent=case.users_collection[0]
        for ob in list(parent.all_objects):
            if ob.name.startswith(name+'_'):ob.location.z+=.42
        x,y,z=case.location
        sx,sy,sz=[max(v.co[a] for v in case.data.vertices)-min(v.co[a] for v in case.data.vertices) for a in range(3)]
        bevel=case.modifiers.new('service_case_edge_radius_TYPE','BEVEL');bevel.width=.025;bevel.segments=2
        c=collection(parent,name+'_service_components_TYPE','Original industrial type geometry; NIST1-4D system-class reference',
            'Self-modeled service access components. Device model and all service/fastener dimensions generic; not original WTC equipment schedule.')
        for i in range(3):
            px=x+sx*(i-1)/3
            part(name+f'_door_gasket{i}_TYPE',(px,y-sy/2-.025,z),(sx/3-.10,.018,sz*.84),c,black)
            part(name+f'_access_door{i}_TYPE',(px,y-sy/2-.040,z),(sx/3-.14,.018,sz*.80),c,trim)
            for k in (-1,1):
                part(name+f'_door_hinge{i}_{k}_TYPE',(px-sx/6+.13,y-sy/2-.067,z+k*sz*.26),(.06,.05,.15),c,trim)
                part(name+f'_cam_latch{i}_{k}_TYPE',(px+sx/6-.16,y-sy/2-.080,z+k*sz*.22),(.12,.04,.035),c,black)
        for k in (-1,1):
            part(name+f'_base_skid{k}_TYPE',(x,y+k*sy*.32,z-sz/2-.18),(sx+.34,.18,.28),c,trim)
            for i in (-1,1):
                part(name+f'_mount_foot{k}_{i}_TYPE',(x+i*sx*.36,y+k*sy*.32,z-sz/2-.36),(.46,.38,.10),c,trim)
                cylinder(name+f'_mount_bolt{k}_{i}_TYPE',(x+i*sx*.36,y+k*sy*.32,z-sz/2-.28),.025,.06,c,trim,8)
        px=x+sx/2+.07
        part(name+'_control_enclosure_TYPE',(px,y,z+.07),(.18,.56,.74),c,trim)
        part(name+'_control_display_TYPE',(px+.10,y,z+.24),(.018,.27,.18),c,black)
        for k in (-1,1):
            part(name+f'_control_switch{k}_TYPE',(px+.12,y+k*.12,z-.08),(.045,.06,.06),c,indicator)
        for i in range(10):
            part(name+f'_control_vent{i}_TYPE',(px+.10,y-.19+i*.042,z-.22),(.015,.017,.10),c,black)
        # Short inlet collar and four flange strips are separate from the unit case.
        for k in (-1,1):
            part(name+f'_duct_collar_side{k}_TYPE',(x+k*.52,y+sy/2+.24,z+.16),(.035,.46,.85),c,trim)
            part(name+f'_duct_collar_horizontal{k}_TYPE',(x,y+sy/2+.24,z+.16+k*.42),(1.07,.46,.035),c,trim)
            part(name+f'_duct_flange_side{k}_TYPE',(x+k*.56,y+sy/2+.48,z+.16),(.08,.04,.95),c,trim)
            part(name+f'_duct_flange_horizontal{k}_TYPE',(x,y+sy/2+.48,z+.16+k*.47),(1.19,.04,.08),c,trim)
    bpy.context.scene['industrial_component_revision']='generic access doors/skids/control boxes/collars; not historical equipment models'

def refine_existing():
    """Idempotent migration for the first saved photo interpretation revision."""
    if bpy.context.scene.get('crown_photo_geometry_refined'):return
    import bmesh
    for ob in bpy.data.objects:
        if '_crown_S' in ob.name and '_vertical_STUDY' in ob.name:
            old=max(v.co.z for v in ob.data.vertices)-min(v.co.z for v in ob.data.vertices)
            if abs(old-10)<.001:
                for v in ob.data.vertices:v.co.z*=11.73/10
                ob.location.z+=.865
        fullring=any(t in ob.name for t in ('plaza_round_planter','antenna_service_platform','antenna_platform_rail','_track_corner_turntable','_valve_wheel'))
        if fullring and ob.type=='MESH':
            m=ob.data;n=len(m.vertices)//4-1
            if len(m.vertices)==4*(n+1) and len(m.polygons)==4*n+2:
                bm=bmesh.new();bm.from_mesh(m);bm.faces.ensure_lookup_table()
                bmesh.ops.delete(bm,geom=list(bm.faces)[-2:],context='FACES_ONLY')
                bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
    bpy.context.scene['crown_photo_geometry_refined']='three-prong center stems reach cap; periodic annulus seams welded'

def special_crown_structure():
    if bpy.context.scene.get('special_crown_structure_revision'):return
    from .facade_detail import steel_mesh,TREE_TOP
    steel=bpy.data.materials['structural_steel_unclad_STUDY']
    aluminum=bpy.data.materials['silver_cladding_color_study']
    for name,xy,roof in (('WTC1',(-55,55),1368*FT),('WTC2',(55,-55),1362*FT)):
        cutoff=roof-CROWN_DEPTH
        for ob in list(bpy.data.objects):
            if ob.name.startswith(name+'_') and ob.get('module')=='steel_column':
                a=ob.location.z;b=a+max(v.co.z for v in list(ob.data.vertices)[:16])
                if a>=cutoff:bpy.data.objects.remove(ob,do_unlink=True)
                elif b>cutoff:ob.data=steel_mesh(cutoff-a,steel)
            elif ob.name.startswith(name+'_upper_wall_') and '_member' in ob.name:
                height=max(v.co.z for v in ob.data.vertices)-min(v.co.z for v in ob.data.vertices)
                # Each old type mesh is uniquely used, except the shared WF profile.
                ob.data=ob.data.copy()
                for v in ob.data.vertices:v.co.z*=CROWN_DEPTH/height
                ob.location.z=roof-CROWN_DEPTH/2
                from .facade_detail import face_xy
                side=int(ob.name.split('_face')[1][0])-1
                axis=int(ob.name.split('_member')[1][:2])-1
                px,py=face_xy(xy,side,(axis-29)*1.016);ob.location.x=px;ob.location.y=py
                ob.data.materials.clear();ob.data.materials.append(steel)
                ob['confidence']='7x5in tube / rolled-profile type; 17m vertical zone estimated from photos, not design elevation'
        root=bpy.data.collections[name]
        c=collection(root,name+'_CORNER_aluminum_photo_interpretation',PHOTO+'; '+PLAZA_PHOTO,
            'Opaque chamfered corner cladding observed. Outline follows sourced column-reference chamfer/cover offset; sheet thickness and 3.65m panel joint spacing estimated. Lobby corner steel/trees remain unresolved.')
        pts=outline(OUTER_HALF)
        for edge in (1,3,5,7):
            a,b=Vector(pts[edge]),Vector(pts[(edge+1)%8]);t=(b-a).normalized();n=Vector((t.y,-t.x))
            midpoint=(a+b)/2+Vector(xy)+n*.015
            z=TREE_TOP;j=0
            while z<roof-2.4:
                upper=min(roof-2.4,z+3.65)
                ob=part(f'{name}_corner_edge{edge}_panel{j:03d}_STUDY',(*midpoint,(z+upper)/2),
                    ((b-a).length,.06,upper-z-.008),c,aluminum,math.atan2(t.y,t.x))
                ob['module']='corner_cover_panel';ob['edge']=edge
                z=upper;j+=1
    bpy.context.scene['special_crown_structure_revision']='normal steel stops at special crown; rolled type zone extended; opaque corner cover panels photo-interpreted'

def landscape_type():
    if bpy.context.scene.get('plaza_landscape_revision'):return
    import bmesh,random
    rng=random.Random(1976)
    c=bpy.data.collections.new('PLAZA_vegetation_TYPE');bpy.context.scene.collection.children.link(c)
    c['source']=PLAZA_PHOTO
    c['confidence']='Perimeter trees and planted pots observed; species, branching, foliage, planter sizes and staged coordinates are CG types, not surveyed planting plan.'
    leaves=material('plaza_foliage_procedural_TYPE',(.095,.15,.045),0,.88)
    bark=material('plaza_tree_bark_TYPE',(.17,.11,.065),0,.86)
    def foliage(name,count,radius):
        bm=bmesh.new()
        for k in range(count):
            a=k*math.tau/count
            geom=bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1)
            p=Vector((radius*.55*math.cos(a),radius*.55*math.sin(a),radius*(.65+rng.random()*.42)))
            scale=Vector((radius*.6,radius*.55,radius*.65))
            for v in geom['verts']:v.co=Vector((v.co.x*scale.x,v.co.y*scale.y,v.co.z*scale.z))+p
        m=bpy.data.meshes.new(name);bm.to_mesh(m);bm.free();m.materials.append(leaves)
        for p in m.polygons:p.use_smooth=True
        return m
    small=foliage('round_planter_leaf_cluster_TYPE',8,.30)
    for ob in bpy.data.objects:
        if ob.name.startswith('plaza_planter_low_planting'):
            ob.data=small;ob['confidence']='original procedural plant type; species not identified'
    crown=foliage('perimeter_tree_leaf_cluster_TYPE',12,1.8)
    coords=[(82,y) for y in (-10,5,20,35)]+[(-88,y) for y in (-5,10)]+[(x,-69) for x in (-52,-36,-20,-4,12)]
    for j,(x,y) in enumerate(coords):
        annulus(f'plaza_tree_planter{j}_TYPE',.95,1.10,PLAZA_Z,PLAZA_Z+.32,c,bark,(x,y),n=24)
        cylinder(f'plaza_tree_trunk{j}_TYPE',(x,y,PLAZA_Z+2),.13,4,c,bark,12)
        for k in range(4):
            a=k*math.pi/2+j*.3
            strut(f'plaza_tree_branch{j}_{k}_TYPE',(x,y,PLAZA_Z+2.6),(x+math.cos(a),y+math.sin(a),PLAZA_Z+4.5),.085,c,bark)
        ob=object_mesh(f'plaza_tree_foliage{j}_TYPE',crown,(x,y,PLAZA_Z+3.5),c)
        ob.rotation_euler.z=j*1.3
    paving=bpy.data.materials['plaza_pale_stone_variation_TYPE']
    ramp=next(n for n in paving.node_tree.nodes if n.type=='VALTORGB')
    ramp.color_ramp.elements[0].color=(.59,.58,.54,1);ramp.color_ramp.elements[1].color=(.72,.69,.62,1)
    c.asset_mark();c.asset_data.description=c['confidence']
    bpy.context.scene['plaza_landscape_revision']='original plant/tree types; subtle paver palette variation'

def roof_detail(name,xy,roof,parent,half_x=31.8,half_y=31.8,tower=True):
    c=collection(parent,name+'_ROOF_detail_components',PHOTO if tower else 'NIST1-9 ch5 / LOC2021636621 roof photographs',
        'Tracks/roof components separated; coordinates, gauges, circuit routing and device inventory are unmeasured CG interpretations, not as-built equipment plans.')
    steel=material('roof_galvanized_metal_TYPE',(.38,.40,.39),.72,.32)
    rubber=material('roof_membrane_TYPE',(.25,.26,.24),0,.84)
    dark=material('roof_track_dark_TYPE',(.10,.13,.14),.66,.4)
    x,y=xy
    if tower:
        from .facade_detail import prism
        prism(name+'_roof_membrane_STUDY',outline(OUTER_HALF-1.83,-1.83),roof+.405,roof+.445,c,rubber,xy)
        # Unverified large rooftop AHUs become optional type studies, not roof reconstruction.
        old=next(g for g in parent.children if g.name.startswith('roof_mechanical'))
        optional=collection(old,name+'_unsurveyed_rooftop_AHU_types',
            'NIST1-4D Figs4-5..8 system types, not roof schedule','Optional generic AHU type samples; historical rooftop presence/placement not established.')
        optional.hide_render=True
        for ob in list(old.objects):
            if any(token in ob.name for token in ('_roof_service_unit','_roof_vent_','_roof_main_duct','_roof_service_walk')):
                optional.objects.link(ob);old.objects.unlink(ob)
    # Double rails on a support beam with physically separated posts and clamps.
    hx=max(4,half_x-4.6);hy=max(4,half_y-4.6)
    path=[(-hx,-hy),(hx,-hy),(hx,hy),(-hx,hy)]
    for e in range(4):
        a=Vector(path[e]);b=Vector(path[(e+1)%4]);t=(b-a).normalized();normal=Vector((-t.y,t.x))
        A=a+Vector(xy);B=b+Vector(xy)
        rail(name+f'_track_support_beam{e}_STUDY',(*A,roof+.85),(*B,roof+.85),c,steel,.28,.22)
        for side in (-1,1):
            aa=A+normal*.30*side;bb=B+normal*.30*side
            rail(name+f'_window_wash_rail{e}_{side}_STUDY',(*aa,roof+1.04),(*bb,roof+1.04),c,steel,.075,.09)
        for j in range(max(2,int((B-A).length/2.5)+1)):
            p=A.lerp(B,j/max(1,int((B-A).length/2.5)))
            part(name+f'_track_post{e}_{j}_STUDY',(*p,roof+.6),(.18,.18,.36),c,steel)
            part(name+f'_track_baseplate{e}_{j}_STUDY',(*p,roof+.445),(.42,.42,.06),c,steel)
            part(name+f'_track_crosshead{e}_{j}_STUDY',(*p,roof+.87),(.78,.12,.10),c,steel,math.atan2(normal.y,normal.x))
        p=(A+B)/2
        for j in range(7):
            q=A.lerp(B,(j+.5)/7)
            part(name+f'_flashing_joint{e}_{j}_STUDY',(*q,roof+.46),(.04,.60,.02),c,dark,math.atan2(t.y,t.x))
    for e,(px,py) in enumerate(path):
        annulus(name+f'_track_corner_turntable{e}_STUDY',.65,.86,roof+.86,roof+.95,c,steel,(x+px,y+py),n=32)
        for axis in (0,math.pi/2):
            dx,dy=.85*math.cos(axis),.85*math.sin(axis)
            rail(name+f'_turntable_bridge{e}_{axis}_STUDY',(x+px-dx,y+py-dy,roof+.98),(x+px+dx,y+py+dy,roof+.98),c,steel,.10,.1)
    # Inspectable window-washing trolley with wheels, motor and maintenance boom.
    tx,ty=x+hx,y-hy/2
    part(name+'_wash_trolley_frame_STUDY',(tx,ty,roof+1.23),(.85,1.9,.22),c,dark)
    for j in (-1,1):
        for k in (-1,1):
            wheel=cylinder(name+f'_trolley_wheel{j}_{k}_STUDY',(tx+j*.31,ty+k*.67,roof+1.11),.14,.11,c,steel,16)
            wheel.rotation_euler.y=math.pi/2
    part(name+'_wash_motor_TYPE',(tx,ty-.35,roof+1.53),(.48,.64,.35),c,steel)
    strut(name+'_wash_boom_STUDY',(tx,ty,roof+1.5),(tx+3.4,ty,roof+3.4),.16,c,steel)
    tube(name+'_wash_boom_tension_cable_STUDY',(tx,ty,roof+2.8),(tx+3.4,ty,roof+3.4),.014,c,dark)
    tube(name+'_wash_cable_drop_STUDY',(tx+3.4,ty,roof+3.4),(tx+3.4,ty,roof-2),.014,c,dark)
    for j in range(2):
        px=x-4+j*8;py=y+half_y*.35
        part(name+f'_access_hatch_curb{j}_TYPE',(px,py,roof+.62),(1.2,1.8,.35),c,dark)
        lid=part(name+f'_hatch_lid{j}_TYPE',(px,py,roof+.82),(1.26,1.86,.065),c,steel)
        for k in (-1,1):part(name+f'_hatch_hinge{j}_{k}_TYPE',(px+k*.38,py+.91,roof+.85),(.13,.11,.07),c,dark)
        part(name+f'_hatch_handle{j}_TYPE',(px,py-.5,roof+.89),(.25,.04,.055),c,dark)
    pipe_details(name+'_roof_pipe',x-2,y+half_y*.45,roof+.44,c,steel)
    for side in (-1,1):
        bx=x+side*min(12,half_x*.35);by=y+min(12,half_y*.35)
        for j in range(12):
            part(name+f'_cable_tray_rung{side}_{j}_TYPE',(bx,by-j*.55,roof+.73),(1.0,.045,.045),c,steel)
        for k in (-1,1):
            part(name+f'_cable_tray_side{side}_{k}_TYPE',(bx+k*.51,by-3.05,roof+.75),(.045,6.6,.16),c,steel)
        for j in range(3):tube(name+f'_tray_cable{side}_{j}_TYPE',(bx-.3+j*.30,by,roof+.77),(bx-.3+j*.3,by-6.2,roof+.77),.022,c,dark)
    return c

def mast():
    c=bpy.data.collections['WTC1_antenna_lattice_STUDY']
    c.name='WTC1_antenna_photo_interpretation_STUDY'
    for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
    c['source']='NIST NCSTAR1 360ft antenna height; '+ANTENNA_PHOTO+'; '+PHOTO
    c['confidence']='White segmented cylindrical mast and attached transmitter forms observed in photographs; radii, equipment sections, fixings and placements inferred. Mast height is sourced.'
    x,y=-55,55;z=1368*FT;h=360*FT
    white=material('antenna_white_paint_TYPE',(.78,.79,.75),.30,.28)
    steel=material('antenna_galvanized_fixings_TYPE',(.37,.40,.41),.8,.32)
    dark=material('antenna_coax_black_TYPE',(.035,.039,.035),.15,.6)
    def taper(name,a,b,r0,r1):
        n=32;v=[(r*math.cos(k*math.tau/n),r*math.sin(k*math.tau/n),zz) for zz,r in ((a,r0),(b,r1)) for k in range(n)]
        f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
        m=bpy.data.meshes.new(name+'_mesh');m.from_pydata(v,[],f);m.materials.append(white)
        for p in m.polygons:
            if len(p.vertices)==4:p.use_smooth=True
        return object_mesh(name,m,(x,y,z),c)
    joints=[(0,1.05),(8,.84),(33,.66),(54,.59),(78,.48),(102,.36),(h,.08)]
    for i,((a,r0),(b,r1)) in enumerate(zip(joints,joints[1:])):
        taper(f'antenna_cylindrical_section{i}_STUDY',a,b,r0,r1)
        cylinder(f'antenna_joint_flange{i}_STUDY',(x,y,z+a),r0+.12,.15,c,steel,32)
        for j in range(12):
            ang=j*math.tau/12
            cylinder(f'antenna_joint_bolt{i}_{j}_TYPE',(x+(r0+.07)*math.cos(ang),y+(r0+.07)*math.sin(ang),z+a+.09),.023,.06,c,steel,8)
    for level in (3.5,8,30,53,77):
        r=3.1 if level<9 else 1.65
        annulus(f'antenna_service_platform_{level}_STUDY',.92 if level<9 else .65,r,z+level,z+level+.09,c,steel,(x,y),n=32)
        annulus(f'antenna_platform_rail_{level}_STUDY',r-.025,r+.025,z+level+1.05,z+level+1.10,c,steel,(x,y),n=32)
        for j in range(12):
            a=j*math.tau/12
            tube(f'antenna_rail_post{level}_{j}_TYPE',(x+r*math.cos(a),y+r*math.sin(a),z+level),(x+r*math.cos(a),y+r*math.sin(a),z+level+1.1),.025,c,steel)
    for j in range(8):
        a=j*math.tau/8;A=(x+3.7*math.cos(a),y+3.7*math.sin(a),z+.5);B=(x+.8*math.cos(a),y+.8*math.sin(a),z+9)
        strut(f'antenna_base_support{j}_STUDY',A,B,.18,c,steel)
        part(f'antenna_base_footplate{j}_TYPE',A,(.65,.65,.08),c,steel)
    for i,(a,b) in enumerate(((10,30),(56,78),(84,99))):
        for j in range(8):
            theta=j*math.tau/8;r=1.05 if i==0 else .72
            px,py=x+r*math.cos(theta),y+r*math.sin(theta)
            part(f'antenna_transmitter_panel{i}_{j}_STUDY',(px,py,z+(a+b)/2),(.23,.30,b-a),c,steel,theta)
            for zz in range(a,b,3):part(f'antenna_transmitter_clip{i}_{j}_{zz}_TYPE',(px,py,z+zz),(.30,.37,.06),c,white,theta)
    for j in range(20):
        zz=z+1+j*.36
        tube(f'antenna_ladder_rung{j}_TYPE',(x-.32,y-1.13,zz),(x+.32,y-1.13,zz),.024,c,steel)
    for k in (-1,1):tube(f'antenna_ladder_side{k}_TYPE',(x+k*.34,y-1.13,z+.5),(x+k*.34,y-1.13,z+8),.028,c,steel)
    for k in range(4):tube(f'antenna_coax_riser{k}_TYPE',(x-.5+k*.32,y+.95,z+.3),(x-.5+k*.32,y+.95,z+30),.055,c,dark)
    # Smaller roof masts/whips visible around the main transmitter in source photographs.
    roof=bpy.data.collections['WTC1_COMPLETION_study']
    rc=collection(roof,'WTC1_ROOF_auxiliary_antenna_interpretation',ANTENNA_PHOTO,
        'Dense roof antenna array observed; count/locations/frequencies and mount details not surveyed.')
    for j in range(32):
        a=j*math.tau/32;px=x+23*math.cos(a);py=y+23*math.sin(a);height=2.0+(j%5)*.65
        part(f'roof_aux_mount{j}_STUDY',(px,py,z+.62),(.34,.34,.34),rc,steel)
        cylinder(f'roof_aux_whip{j}_STUDY',(px,py,z+.8+height/2),.025,height,rc,white,8)
    for j,(dx,dy,height) in enumerate(((-13,-11,18),(15,-10,12),(16,15,15))):
        px,py=x+dx,y+dy
        cylinder(f'roof_aux_mast{j}_STUDY',(px,py,z+height/2),.09,height,rc,steel,12)
        for k in range(3):
            cylinder(f'roof_aux_panel{j}_{k}_STUDY',(px+.18,py,z+height*(.5+.12*k)),.18,1.0,rc,white,12)
        for ox,oy in ((2,0),(-1.5,1.5),(-1.5,-1.5)):
            tube(f'roof_aux_guy{j}_{ox}_{oy}_STUDY',(px,py,z+height*.65),(px+ox,py+oy,z+.5),.012,rc,steel)

def core_head(name,xy,roof):
    parent=bpy.data.collections[name+'_COMPLETION_study']
    c=collection(parent,name+'_CORE_roof_connections_STUDY',
        'NIST1-2A §3.2.8 Figs3-10/11; core columns connect through107-roof hat truss',
        'Continuous core endpoint at roof; roof beam sections, column node plates and shaft enclosure sections are CG type interpretations. Original47-axis plan remains schematic.')
    c.hide_render=True
    steel=bpy.data.materials['structural_steel_unclad_STUDY'];x,y=xy
    cx,cy=((137*FT,87*FT) if name=='WTC1' else (87*FT,137*FT))
    for axis in (0,1):
        along=cx if axis==0 else cy;across=cy if axis==0 else cx
        for k in range(6):
            p=-across/2+(k+.5)*across/6
            a=(x-along/2,y+p,roof-.42) if axis==0 else (x+p,y-along/2,roof-.42)
            b=(x+along/2,y+p,roof-.42) if axis==0 else (x+p,y+along/2,roof-.42)
            rail(f'{name}_core_roof_beam{axis}_{k}_STUDY',a,b,c,steel,.24,.56)
    cols=[ob for ob in bpy.data.objects if ob.name.startswith(name+'_core_axis') and ob.get('module')=='core_steel_column']
    for i in range(47):
        segments=[o for o in cols if o.get('axis_index')==i]
        top=max(segments,key=lambda o:o.location.z)
        px,py=top.location.x,top.location.y
        part(f'{name}_core_roof_node{i}_capplate_TYPE',(px,py,roof-.04),(.65,.65,.08),c,steel)
        for dx in (-.23,.23):
            for dy in (-.23,.23):cylinder(f'{name}_core_roof_node{i}_bolt{dx}_{dy}_TYPE',(px+dx,py+dy,roof+.025),.023,.05,c,steel,8)
    # Three independent shaft modules continue to the roof instead of ending in lobby.
    wall=material('core_shaft_wall_TYPE',(.43,.43,.39),0,.78)
    shafts=collection(c,name+'_CORE_shaft_wall_types','NIST1-1 three stairs; study shaft proportions','Shaft sizes/positions estimated; open-sided inspection modules, not surveyed enclosures.')
    shafts.hide_render=True
    for j,dx in enumerate((-cx*.27,0,cx*.27)):
        for s in range(math.ceil(roof/10.9728)):
            lo=s*10.9728;hi=min(roof,lo+10.9728)
            section_extrude(f'{name}_shaft{j}_wall_segment{s}_STUDY',
                [(-2,-2.75),(2,-2.75),(2,2.75),(1.8,2.75),(1.8,-2.55),(-1.8,-2.55),(-1.8,2.75),(-2,2.75)],lo,hi,shafts,wall,(x+dx,y))
    return c

def plaza():
    c=bpy.data.collections['PLAZA_individual_tile_meshes_STUDY']
    oldtiles=[o for o in c.objects if o.get('mesh_unique')]
    for ob in oldtiles:bpy.data.objects.remove(ob,do_unlink=True)
    paving=material('plaza_pale_stone_variation_TYPE',(.60,.58,.53),0,.65)
    p=paving.node_tree.nodes.get('Principled BSDF')
    info=paving.node_tree.nodes.new('ShaderNodeObjectInfo');ramp=paving.node_tree.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(.47,.46,.42,1);ramp.color_ramp.elements[1].color=(.72,.69,.61,1)
    paving.node_tree.links.new(info.outputs['Random'],ramp.inputs[0]);paving.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
    noise=paving.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=90
    bump=paving.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.005;bump.inputs['Strength'].default_value=.10
    paving.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);paving.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
    c['source']=PLAZA_PHOTO
    c['confidence']='Photograph establishes stone paving and fountain-centered radial layout. 1.5m grid, 12.5m basin radius and radial details estimated; site alignment unverified.'
    footprints=[(-55,55,33.6,33.6),(55,-55,33.6,33.6)]
    for volume in bpy.data.objects:
        if any(volume.name.startswith(n+'_volume_') for n in ('WTC3_Marriott','WTC4','WTC5','WTC6')):
            footprints.append((volume.location.x,volume.location.y,volume.dimensions.x/2+1.7,volume.dimensions.y/2+1.7))
    tile_proto=None
    for i in range(120):
        x=(i-59.5)*1.5
        for j in range(100):
            y=(j-49.5)*1.5
            if any(abs(x-bx)<bw and abs(y-by)<bh for bx,by,bw,bh in footprints) or math.hypot(x,y)<18.0:continue
            if tile_proto is None:
                ob=box(f'plaza_tile_{i:03d}_{j:03d}',(x,y,PLAZA_Z+.015),(1.482,1.482,.03),c,paving);tile_proto=ob.data
            else:
                ob=object_mesh(f'plaza_tile_{i:03d}_{j:03d}',tile_proto.copy(),(x,y,PLAZA_Z+.015),c)
            ob['mesh_unique']=True;ob['module']='plaza_paver'
    for ring in range(5):
        r0=12.75+ring*1.02;r1=r0+1.003
        for j in range(96):
            ob=annulus(f'plaza_radial_paver_{ring}_{j:02d}_STUDY',r0,r1,PLAZA_Z,PLAZA_Z+.03,c,paving,
                a0=(j+.01)*math.tau/96,a1=(j+.99)*math.tau/96,n=2)
            ob['mesh_unique']=True;ob['module']='plaza_radial_paver'
    c['actual_tile_mesh_count']=sum(bool(o.get('mesh_unique')) for o in c.objects)
    detail=bpy.data.collections.new('PLAZA_furniture_and_landscape_interpretation');bpy.context.scene.collection.children.link(detail)
    detail['source']=PLAZA_PHOTO
    detail['confidence']='Segmented ring benches, round planters and lamp poles observed in1976 photo. Sizes, positions, counts and planting CG estimates, not later2001 survey.'
    bronze=material('plaza_bench_warm_brown_TYPE',(.27,.18,.09),.2,.45)
    steel=material('plaza_furniture_dark_TYPE',(.095,.10,.095),.7,.45)
    soil=material('planter_soil_TYPE',(.05,.04,.02),0,.95)
    green=material('plant_low_foliage_TYPE',(.13,.19,.05),0,.9)
    for j in range(8):
        a=j*math.tau/8
        for k in range(9):
            b=a-.30+k*.064
            px,py=16.1*math.cos(b),16.1*math.sin(b)
            part(f'plaza_bench{j}_seat_segment{k}_STUDY',(px,py,PLAZA_Z+.48),(.9,.57,.09),detail,bronze,b+math.pi/2)
            part(f'plaza_bench{j}_back_segment{k}_STUDY',(16.4*math.cos(b),16.4*math.sin(b),PLAZA_Z+.82),(.9,.08,.55),detail,bronze,b+math.pi/2)
            if k%2==0:part(f'plaza_bench{j}_support{k}_STUDY',(px,py,PLAZA_Z+.23),(.10,.40,.46),detail,steel,b+math.pi/2)
        for k in range(3):
            b=a+.39+(k-1)*.12;radius=19.8+(1 if k==1 else 0);px,py=radius*math.cos(b),radius*math.sin(b)
            annulus(f'plaza_round_planter{j}_{k}_STUDY',.53,.66,PLAZA_Z,PLAZA_Z+.52,detail,paving,(px,py),n=24)
            cylinder(f'plaza_planter_soil{j}_{k}_TYPE',(px,py,PLAZA_Z+.42),.53,.08,detail,soil,24)
            cylinder(f'plaza_planter_low_planting{j}_{k}_TYPE',(px,py,PLAZA_Z+.53),.40,.14,detail,green,16)
        px,py=22.5*math.cos(a+.39),22.5*math.sin(a+.39)
        cylinder(f'plaza_lamp_base{j}_STUDY',(px,py,PLAZA_Z+.15),.17,.30,detail,steel,16)
        cylinder(f'plaza_lamp_pole{j}_STUDY',(px,py,PLAZA_Z+3.5),.045,7,detail,steel,12)
        part(f'plaza_lamp_head{j}_STUDY',(px,py,PLAZA_Z+7.05),(.24,.24,.70),detail,steel)
    # Resize the basin/support only; retain clearly named generic sculpture proxy.
    fountain=bpy.data.collections['PLAZA_globe_and_fountain_SCALE_PROXY']
    for name in ('fountain_podium_support_STUDY','round_fountain_basin_STUDY','water_surface_STUDY'):
        ob=bpy.data.objects[name];factor=(18.05 if name.startswith('fountain_podium') else 12.5 if name.startswith('round') else 12.20)/(10.5 if name.startswith('fountain_podium') else 7 if name.startswith('round') else 6.45)
        for v in ob.data.vertices:v.co.x*=factor;v.co.y*=factor
    for j in range(96):
        annulus(f'fountain_coping_segment{j}_STUDY',12.22,12.60,PLAZA_Z+.33,PLAZA_Z+.43,fountain,paving,
                a0=(j+.01)*math.tau/96,a1=(j+.99)*math.tau/96,n=2)
    water=bpy.data.materials['fountain_water_STUDY'];p=water.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.16
    noise=water.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5
    bump=water.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.015;bump.inputs['Strength'].default_value=.3
    water.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);water.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])

def enhance():
    if bpy.context.scene.get('crown_site_revision'):
        legacy=bpy.data.collections.get('WTC1_antenna_lattice_STUDY')
        if legacy:legacy.name='WTC1_antenna_photo_interpretation_STUDY'
        industrial_detail()
        refine_existing()
        special_crown_structure()
        landscape_type()
        return
    for name,xy,roof in (('WTC1',(-55,55),1368*FT),('WTC2',(55,-55),1362*FT)):
        print('DETAIL_MODULE_START '+name,flush=True)
        crown(name,xy,roof)
        parent=bpy.data.collections[name+'_COMPLETION_study']
        roof_detail(name,xy,roof,parent)
        core_head(name,xy,roof)
        print('DETAIL_MODULE_DONE '+name,flush=True)
    mast();print('DETAIL_MAST_DONE',flush=True)
    plaza();print('DETAIL_PLAZA_DONE',flush=True)
    industrial_detail()
    for name in ('WTC3_Marriott','WTC4','WTC5','WTC6'):
        parent=bpy.data.collections.get(name+'_massing_STUDY')
        for ob in list(parent.objects):
            if '_volume_' in ob.name:
                x,y,z=ob.location;sx,sy,sz=ob.dimensions
                roof_detail(ob.name,(x,y),z+sz/2,parent,sx/2,sy/2,False)
    parent=bpy.data.collections.get('WTC7__NIST_massing_position_schematic')
    if parent:roof_detail('WTC7',(-20,230),610*FT,parent,50,22,False)
    refine_existing()
    special_crown_structure()
    landscape_type()
    bpy.context.scene['crown_site_revision']='2026-10-13 photo interpretation; see DETAIL_REVISION_PLAN and source tags'
