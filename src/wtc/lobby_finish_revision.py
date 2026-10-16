"""A-AB-258/265 and user photo: coved ceiling, crystal rods, marble details."""
import math,re
import bpy
from .interior_parts import Parts,collection,finish
from .mesh_batch import Batch,i_section
from .lobby_plan_revision import slab_mesh
from .facade_revision import _face_object,_prism_profile
from .completion import PLAZA_Z,TREE_TOP,FORK_START,FORK_END
from . import base_frame_revision as base

VERSION='2026-10-16-marble-crystal-smooth-crests-v1'
SOURCE='Original A-AB-258 reflected ceiling/A-AB-265 stone and grille sections; user OIP.iThPKo5TULV9TtG316EPgAHaEK.jpeg; RR-3985 museum archive'
LIMIT='Source visible topology/material system; dimensions, panel subdivisions, chandelier rod count, curvature and lower tapered-frame section fitted; not an as-built shop drawing'
CANOPY='https://images15.fotki.com/v1675/photos/6/61/129797/IMG_1809or-vi.jpg'


def marble():
    m=finish('LOBBY_fine_white_marble',(.70,.68,.62),0,.29,1200)
    if m.get('vein_system'):return m
    nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
    tex=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(2.1,.65,4.4)
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.8;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.74
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.39;ramp.color_ramp.elements[0].color=(.39,.37,.31,1);ramp.color_ramp.elements[1].position=.47;ramp.color_ramp.elements[1].color=(.76,.73,.66,1)
    links.new(tex.outputs['Object'],mapping.inputs[0]);links.new(mapping.outputs[0],noise.inputs['Vector']);links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],bs.inputs['Base Color']);m['vein_system']=True
    return m


def smooth_crests():
    profiles={}
    for sign in (-1,0,1):
        heights=[PLAZA_Z,FORK_START]+[FORK_START+(FORK_END-FORK_START)*i/64 for i in range(1,65)]+[TREE_TOP]
        h=base.CENTER_RIDGE if sign==0 else base.RIDGE
        section=[(base.RIB_HALF_WIDTH*math.sin(-math.pi/2+k*math.pi/20),h*math.cos(-math.pi/2+k*math.pi/20)) for k in range(21)]
        v=[];f=[];N=len(section)
        for z in heights:
            t=max(0,min(1,(z-FORK_START)/(FORK_END-FORK_START)));u=sign*(base.STEM_RIB_OFFSET+(1.016-base.STEM_RIB_OFFSET)*t*t*(3-2*t))
            v.extend((u+x,-.25-relief,z-PLAZA_Z) for x,relief in section)
        for j in range(len(heights)-1):
            for k in range(N):f.append((j*N+k,j*N+(k+1)%N,(j+1)*N+(k+1)%N,(j+1)*N+k))
        f.extend((tuple(range(N-1,-1,-1)),tuple((len(heights)-1)*N+k for k in range(N))))
        m=bpy.data.meshes.new('smooth_crest_profile_'+str(sign));m.from_pydata(v,[],f)
        for face in list(m.polygons)[:-2]:face.use_smooth=face.index%N!=N-1
        profiles[sign]=m
    for o in bpy.data.objects:
        match=re.search(r'_crest_(left|middle|right)$',o.name)
        if not match:continue
        sign={'left':-1,'middle':0,'right':1}[match.group(1)];m=profiles[sign].copy();m.name=o.name+'_smooth_independent_mesh'
        for mat in o.data.materials:m.materials.append(mat)
        o.data=m;o['surface']='Smooth elliptical positive crest; separate single-user closed mesh';o['source']=SOURCE;o['confidence']=LIMIT
    for m in profiles.values():bpy.data.meshes.remove(m)


def fixture():
    c=bpy.data.collections.new('LOBBY_crystal_cylinder_chandelier_TEMPLATE');c['source']=SOURCE;c['confidence']=LIMIT
    gold=finish('LOBBY_lamp_champagne_frame',(.49,.36,.17),.82,.25)
    glass=finish('LOBBY_crystal_glass',(.91,.84,.63),.02,.13)
    bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=.82;bs.inputs['IOR'].default_value=1.46
    light=finish('LOBBY_chandelier_luminous_core',(.96,.78,.41),0,.3)
    bs=light.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.76,.38,1);bs.inputs['Emission Strength'].default_value=5
    p=Parts('CRYSTAL',c);p.box('ceiling_plate',(0,0,.10),(.78,.78,.045),gold)
    for sx in (-1,1):
        for sy in (-1,1):p.tube(f'suspension{sx}_{sy}',(sx*.29,sy*.29,.08),(sx*.29,sy*.29,-.30),.008,gold)
    for z in (-.28,-.68):
        for s in (-1,1):
            p.box(f'frameX{z}_{s}',(0,s*.40,z),(.85,.020,.022),gold)
            p.box(f'frameY{z}_{s}',(s*.40,0,z),(.020,.85,.022),gold)
    rods=Batch('CRYSTAL_120_individual_cylinders',glass)
    # Several depths, with rods on the outside and in the central volume.
    for i in range(10):
        for j in range(10):
            if 2<i<7 and 2<j<7:continue
            x,y=(i-4.5)*.078,(j-4.5)*.078;bottom=-.65+.055*((i+j)%3)
            rods.tube((x,y,bottom),(x,y,-.30),.021,16)
    for side in (-1,1):
        for i in range(18):
            x=(i-8.5)*.037;rods.tube((x,side*.30,-.81),(x,side*.30,-.57),.013,12)
    ob=rods.mesh(c,'chandelier_glass_cylinders');ob['glass_cylinders']=rods.count
    for x in (-.2,.2):p.box('light_core'+str(x),(x,0,-.46),(.11,.43,.16),light)
    return c


def coved_panel(width,depth,mat):
    v=[];f=[];N=5
    for back in (0,.065):
        for i in range(N):
            t=i/(N-1);u=t*t*(3-2*t);w=width/2*(1-u)+.40*u;d=depth/2*(1-u)+.40*u;z=.78*math.sin(t*math.pi/2)+back
            v.extend((x*w,y*d,z) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1)))
    size=N*4
    for k in range(N-1):
        for j in range(4):
            a=k*4+j;b=k*4+(j+1)%4;cc=(k+1)*4+(j+1)%4;d=(k+1)*4+j
            f.extend(((a,b,cc,d),(size+d,size+cc,size+b,size+a)))
    for k in (0,N-1):
        for j in range(4):
            a=k*4+j;b=k*4+(j+1)%4;f.append((a,size+a,size+b,b))
    m=bpy.data.meshes.new('LOBBY_coved_plaster_panel');m.from_pydata(v,[],f);m.materials.append(mat)
    for face in list(m.polygons)[:(N-1)*8]:face.use_smooth=True
    return m


def lobby(tower,xy,lamp):
    parent=bpy.data.collections[tower+'_LOBBY_photo_interpretation_STUDY'];c=collection(tower+'_LOBBY_marble_crystal_and_reveals',parent,SOURCE,LIMIT,xy)
    p=Parts(tower+'_REFINED',c,xy);stone=marble();metal=finish('LOBBY_trim_satin_metal',(.43,.40,.33),.87,.25,500)
    dark=finish('LOBBY_small_shadow_gaps',(.035,.033,.028),.15,.64);plaster=finish('LOBBY_coved_cream_plaster',(.74,.72,.64),0,.76)
    hx,hy=((137*.3048/2,87*.3048/2) if tower=='WTC1' else (87*.3048/2,137*.3048/2))
    for o in parent.objects:
        if any(s in o.name for s in ('coffer_','pendant_','ceiling_shadow_backing')):o.hide_render=True;o.hide_viewport=True
    old=bpy.data.collections.get(tower+'_LOBBY_stone_carpet_lamps_DETAIL')
    for o in old.objects:
        if 'lamp_' in o.name:o.hide_render=True;o.hide_viewport=True
    coffer=coved_panel(61.4/12-.025,61.4/7-.025,plaster)
    for i in range(12):
        for j in range(7):
            if 2<=i<=9 and 2<=j<=4:continue
            u=(i-5.5)*61.4/12;v=(j-3)*61.4/7
            x,y=(u,v) if tower=='WTC1' else (-v,u)
            o=p.mesh(f'coffer_{i}_{j}',coffer,(x,y,20.84),kind='source_coved_ceiling')
            if tower=='WTC2':o.rotation_euler.z=math.pi/2
            ob=bpy.data.objects.new(tower+f'_CYLINDER_CHANDELIER_{i}_{j}',None);c.objects.link(ob);ob.instance_type='COLLECTION';ob.instance_collection=lamp;ob.location=p.point((x,y,21.52));ob['module']='cylinder_chandelier';ob['source']=SOURCE;ob['confidence']=LIMIT
            if (i+j)%3==0:p.area(f'chandelier_light_{i}_{j}',(x,y,20.66),85,1.2)
    # Individual courses, returns, seams and kerf-anchor type details.
    for side in range(4):
        along=hx if side%2==0 else hy;normal=hy if side%2==0 else hx;count=max(6,round(along*2/3.05));pitch=along*2/count
        for axis in range(count+1):
            u=-along+axis*pitch
            for row in range(18):
                z=.25+(21.02-.25)*(row+.5)/18;h=(21.02-.25)/18-.007
                m=bpy.data.meshes.get('LOBBY_marble_course_mesh')
                if not m:
                    from .facade_revision import _box_mesh
                    m=_box_mesh((.63,.038,h),stone);m.name='LOBBY_marble_course_mesh'
                ob=_face_object(f'{tower}_MARBLE_S{side}_P{axis}_C{row}',m,xy,side,normal+.121,z,c,u);ob['module']='lobby_jointed_marble_course';ob['source']=SOURCE;ob['confidence']=LIMIT
                for s in (-1,1):
                    from .facade_revision import _box_mesh
                    _face_object(f'{tower}_MARBLE_RETURN_{side}_{axis}_{row}_{s}',_box_mesh((.025,.18,h),stone),xy,side,normal+.045,z,c,u+s*.316)
            # Details from active/inactive grille sections, rather than a mirror slab.
            for row,z in enumerate((.68,4.0,10.7)):
                for blade in range(6):
                    from .facade_revision import _box_mesh
                    ob=_face_object(f'{tower}_MARBLE_GRILLE_{side}_{axis}_{row}_{blade}',_box_mesh((.052,.020,.24),metal),xy,side,normal+.148,z,c,u+(blade-2.5)*.076);ob['module']='core_metal_grille_blade'
        for bank in range(count):
            u=-along+(bank+.5)*pitch;w=pitch-.66
            for level,z in (('concourse',.24),('plaza',PLAZA_Z)):
                # Keep actual independently open inspection cab; recess closed leaves.
                for leaf in ('leafL','leafR'):
                    ob=bpy.data.objects.get(f'{tower}_LR_core_s{side}_{level}_{leaf}_{bank}_STUDY')
                    if ob and not ob.hide_render:
                        ob.location.x-=.13*math.sin(side*math.pi/2);ob.location.y+=.13*math.cos(side*math.pi/2)
                for s in (-1,1):
                    from .facade_revision import _box_mesh
                    ob=_face_object(f'{tower}_PORTAL_{side}_{level}_{bank}_{s}',_box_mesh((.075,.25,3.44),metal),xy,side,normal-.012,z+1.72,c,u+s*(w/2-.03));ob['module']='lobby_recessed_portal_jamb'
                for k in range(4):_face_object(f'{tower}_THRESHOLD_SLOT_{side}_{level}_{bank}_{k}',_box_mesh((w,.006,.009),metal),xy,side,normal+.02+k*.018,z+.03,c,u)
                # Triple-piece door head and narrow mirrored return.
                for k in range(3):_face_object(f'{tower}_PORTAL_HEAD_{side}_{level}_{bank}_{k}',_box_mesh((w/3-.005,.22,.085),metal),xy,side,normal-.012,z+3.45,c,u+(k-1)*w/3)
    c['chandelier_count']=60;c['stone_system']='Panel courses, joint reveals, marble returns and metal grille inserts; small anchor gauges fitted'


def cab_finish(tower):
    c=bpy.data.collections[tower+'_ELEVATOR_cab_and_mechanism_TYPE'];xy=(-55,55) if tower=='WTC1' else (55,-55);p=Parts(tower+'_CAB1993',c,xy)
    floor=c.objects[tower+'_LIFT_inspection_car_floor'];x=floor.location.x-xy[0];y=floor.location.y-xy[1];z=.24
    enamel=finish('CAB1993_porcelain_enamel',(.60,.54,.41),.10,.30);stone=marble();trim=finish('CAB1993_aluminium_dividers',(.53,.54,.51),.85,.27,800);mirror=finish('CAB1993_mirror_light_cove',(.68,.70,.67),.96,.075)
    for o in c.objects:
        if 'rear_mirror' in o.name or 'light_diffuser' in o.name:o.hide_render=True;o.hide_viewport=True
        if any(s in o.name for s in ('operator_track','hanger_roller','door_hanger','door_operator_motor')):o.hide_render=True;o.hide_viewport=True;o['inspection_only']=True
    for side in (-1,1):
        for j in range(3):
            yy=y+(j-1)*.67
            p.box(f'upper_panel{side}_{j}',(x+side*1.05,yy,z+1.77),(.025,.653,1.19),enamel,kind='cab_removable_enamel_panel')
            p.box(f'lower_panel{side}_{j}',(x+side*1.05,yy,z+.51),(.025,.653,.80),enamel)
            p.box(f'panel_divider{side}_{j}',(x+side*1.032,yy+.33,z+1.35),(.018,.016,2.25),trim)
        p.box('marble_chair_rail'+str(side),(x+side*1.025,y,z+1.05),(.055,2.02,.18),stone)
        p.tube('round_handrail'+str(side),(x+side*.98,y-.88,z+1.08),(x+side*.98,y+.88,z+1.08),.027,trim)
    for j in range(3):p.box('rear_enamel'+str(j),(x+(j-1)*.69,y+1.027,z+1.72),(.674,.024,1.27),enamel)
    p.box('rear_marble_rail',(x,y+1.005,z+1.04),(2.08,.05,.18),stone)
    p.tube('rear_handrail',(x-.9,y+.95,z+1.08),(x+.9,y+.95,z+1.08),.027,trim)
    for side in (-1,1):
        p.box('light_cove_side'+str(side),(x+side*.96,y,z+2.46),(.13,2.04,.17),mirror)
        p.box('light_cove_rear'+str(side),(x,y+side*.93,z+2.46),(1.81,.14,.17),mirror)
    for j in range(5):p.box('ceiling_panel'+str(j),(x+(j-2)*.36,y,z+2.50),(.35,1.70,.025),trim)
    opal=finish('CAB1993_cove_diffuser',(.93,.87,.73),0,.27);bs=opal.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.86,.67,1);bs.inputs['Emission Strength'].default_value=3
    for side in (-1,1):p.box('cove_strip'+str(side),(x+side*.89,y,z+2.43),(.055,1.77,.012),opal)
    for k in range(8):
        for j in range(2):
            xx=x+.899;yy=y-.73+j*.14;zz=z+.94+k*.078
            for dot in range(3):p.tube(f'button_braille_{k}_{j}_{dot}',(xx-.015,yy-.032+dot*.022,zz-.028),(xx-.020,yy-.032+dot*.022,zz-.028),.004,trim)
    c['cab_finish_source']='RR-3985/1993 museum archive: enamel panels/divider strips/marble rails/aluminium ceiling/mirrored light cove; unreadable dimensions retained as fits'


def lower_borders(tower,xy):
    parent=bpy.data.collections[tower+'_COMPLETION_study'];c=collection(tower+'_BASE_tapered_corner_borders',parent,SOURCE,LIMIT,xy)
    metal=bpy.data.materials['silver_cladding_color_study'];length=TREE_TOP-PLAZA_Z+.14;w=.127
    # Independent proud face and folded side returns, narrowing at the top.
    for side in range(4):
        for sign in (-1,1):
            for part,shift,width,depth,q in (('face',0,w,.012,31.82),('left',-.061,.006,.1778,31.738),('right',.061,.006,.1778,31.738)):
                tip=.003 if part!='face' else .014
                tipcenter=0 if part=='face' else math.copysign(.007,shift)
                profile=[(shift-width/2,0),(shift+width/2,0),(shift+width/2,length-2.25),(tipcenter+tip/2,length),(tipcenter-tip/2,length),(shift-width/2,length-2.25)]
                v=[];f=[];_prism_profile(v,f,profile,depth);m=bpy.data.meshes.new('tapered_lower_border_'+part);m.from_pydata(v,[],f);m.materials.append(metal)
                ob=_face_object(f'{tower}_BASE_TAPER_{side}_{sign}_{part}',m,xy,side,q,PLAZA_Z,c,sign*29*1.016);ob['module']='lower_corner_tapered_border';ob['source']=SOURCE;ob['confidence']=LIMIT
    old=bpy.data.collections[tower+'_BASE_nested_frames_and_transoms_STUDY']
    for ob in old.objects:
        if ob.get('module')=='base_end_corner_projection':ob.hide_render=True;ob.hide_viewport=True;ob['superseded_by']=c.name


def canopy():
    c=collection('WTC1_WEST_glass_pyramid_canopy',bpy.data.collections['WTC1_COMPLETION_study'],CANOPY,'Original West Street canopy photo: metal fascia, pyramidal skylights and supports;30.48x8.5m/5.4m high CG image fits',(-55,55))
    p=Parts('WTC1_CANOPY',c,(-55,55));metal=finish('CANOPY_painted_aluminium',(.58,.60,.57),.68,.32);glass=finish('CANOPY_laminated_glass',(.19,.29,.29),.12,.12)
    bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=.68;bs.inputs['IOR'].default_value=1.48
    x=-31.5722-4.25;z=5.4;holes=[]
    for i in range(2):
        for j in range(5):
            cx=x+(i-.5)*3.8;cy=(j-2)*5.75;hx,hy=1.60,2.52
            holes.append([(cx-hx,cy-hy),(cx+hx,cy-hy),(cx+hx,cy+hy),(cx-hx,cy+hy)])
            ring=[(cx-hx,cy-hy,z),(cx+hx,cy-hy,z),(cx+hx,cy+hy,z),(cx-hx,cy+hy,z)];peak=(cx,cy,z+.95)
            for k in range(4):
                a,b=ring[k],ring[(k+1)%4];v=[a,b,peak]+[(u,v,w-.012) for u,v,w in (a,b,peak)];faces=[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
                m=bpy.data.meshes.new(f'CANOPY_glass_{i}_{j}_{k}');m.from_pydata(v,[],faces);m.materials.append(glass)
                ob=p.mesh(f'glass_{i}_{j}_{k}',m,kind='canopy_pyramidal_glazing')
                p.tube(f'hip_{i}_{j}_{k}',a,peak,.035,metal)
    p.mesh('roof_apron',slab_mesh('CANOPY_roof_apron',[(x-4.25,-15.24),(x+4.25,-15.24),(x+4.25,15.24),(x-4.25,15.24)],holes,.10,metal),(0,0,z),kind='canopy_roof_apron')
    for s in (-1,1):
        p.box('fasciaY'+str(s),(x,s*15.24,z-.29),(8.65,.09,.66),metal)
        p.box('fasciaX'+str(s),(x+s*4.25,0,z-.29),(.09,30.55,.66),metal)
    for j in range(6):
        y=-14.6+j*5.84;p.bar('cantilever'+str(j),(-31.57,y,z-.30),(x-4.3,y,z-.30),i_section(.38,.18,.012,.02),metal)
    for j in range(4):
        y=(j-1.5)*9.1;p.tube('post'+str(j),(x-3.95,y,.1),(x-3.95,y,z-.30),.12,metal)
        p.tube('drain'+str(j),(x-3.83,y,.2),(x-3.83,y,z-.12),.025,metal)


def apply():
    scene=bpy.context.scene
    if scene.get('lobby_finish_revision')==VERSION:return
    smooth_crests();lamp=fixture()
    for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):lobby(tower,xy,lamp);cab_finish(tower);lower_borders(tower,xy)
    canopy();scene['lobby_finish_revision']=VERSION
