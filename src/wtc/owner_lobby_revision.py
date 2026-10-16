"""Reusable owner-delivery elevator hall, separate from empty tenant shells."""
import math
import bpy
from .interior_parts import Parts,collection,finish
from .lobby_plan_revision import slab_mesh
from .shell_floor_revision import H,K,SOURCE as STRUCTURE_SOURCE
from .mesh_batch import Batch

VERSION='2026-10-16-owner-elevator-halls-v1'
SOURCE='https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101046 section2.2.3/Fig2-14;24local lifts in4groups per vertical zone'
LIMIT='Owner-delivery CG finish type, six local cars per served group; bank positions, finish widths, ceiling layout and shaft polygons fitted, not recovered floor-by-floor as-built interiors'


def zone_group(n):
    if n<=40:ends=(16,24,31,40);start=9
    elif n<=74:ends=(50,58,66,74);start=44
    else:ends=(84,92,100,107);start=78
    index=next((i for i,e in enumerate(ends) if n<=e),3)
    return index,ends,start


def hall_template():
    col=bpy.data.collections.new('OWNER_LOCAL6_elevator_hall_TEMPLATE');col['source']=SOURCE;col['confidence']=LIMIT
    p=Parts('OWNER_HALL',col)
    marble=finish('OWNER_hall_marble',(.61,.59,.53),0,.30,400)
    bronze=finish('OWNER_hall_warm_stainless',(.40,.34,.25),.86,.24,450)
    enamel=finish('OWNER_hall_cream_ceiling',(.77,.75,.68),.05,.68)
    door=finish('OWNER_hall_door_brushed',(.29,.30,.28),.91,.28,850)
    black=finish('OWNER_hall_shadow_joint',(.025,.025,.023),0,.75)
    lens=finish('OWNER_hall_diffuser',(.85,.78,.60),0,.34)
    bs=lens.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.84,.64,1);bs.inputs['Emission Strength'].default_value=2
    p.box('floor',(0,0,.025),(2.75,10.7,.05),marble,kind='owner_lobby_floor')
    p.box('ceiling',(0,0,2.91),(2.85,10.7,.10),enamel,kind='owner_lobby_ceiling')
    for s in (-1,1):
        p.box('base'+str(s),(s*1.395,0,.11),(.08,10.7,.22),bronze)
        p.box('ceiling_reveal'+str(s),(s*1.36,0,2.83),(.045,10.7,.05),black)
        for j in range(3):
            y=(j-1)*3.1
            # Open masonry portal; solid wall only between doors, never across them.
            for k in (-1,1):
                p.box(f'pier{s}_{j}_{k}',(s*1.44,y+k*1.18,1.4),(.15,.72,2.8),marble)
                p.box(f'jamb{s}_{j}_{k}',(s*1.395,y+k*.80,1.17),(.23,.09,2.34),bronze)
                p.box(f'leaf{s}_{j}_{k}',(s*1.53,y+k*.376,1.14),(.035,.744,2.24),door,kind='owner_landing_door_leaf')
            p.box(f'head_marble{s}_{j}',(s*1.44,y,2.57),(.15,1.65,.46),marble)
            p.box(f'head_metal{s}_{j}',(s*1.395,y,2.35),(.23,1.69,.10),bronze)
            for k in range(4):p.box(f'sill{s}_{j}_{k}',(s*(1.35+k*.025),y,.055),(.010,1.62,.012),bronze)
            p.box(f'callplate{s}_{j}',(s*1.345,y+1.06,1.30),(.025,.0762,.4826),bronze)
            for k in (-1,1):
                p.tube(f'call_button{s}_{j}_{k}',(s*1.326,y+1.06,1.3+k*.075),(s*1.306,y+1.06,1.3+k*.075),.016,bronze)
            p.box(f'position_indicator{s}_{j}',(s*1.34,y,2.52),(.018,.26,.11),black)
            p.box(f'position_glow{s}_{j}',(s*1.326,y,2.52),(.008,.09,.055),lens)
        for k in range(10):p.box(f'wall_joint{s}_{k}',(s*1.353,-4.8+k*1.07,1.5),(.008,.006,2.6),black)
    for j in range(6):
        y=-4.5+j*1.8;p.box('ceiling_light'+str(j),(0,y,2.84),(.28,1.18,.018),lens)
    for s in (-1,1):
        for j in range(13):p.box(f'transfer_grille{s}_{j}',(j*.12-.72,s*5.29,2.64),(.025,.035,.23),bronze)
    return col


def core_slab(group,ends,n,mat):
    holes=[]
    for i,e in enumerate(ends):
        if n>e+2:continue  # released shaft footprint becomes bare rentable slab
        x=-15+i*10
        for side in (-1,1):
            for j in range(3):
                a=x+side*2.7;b=(j-1)*3.1
                holes.append([(a-1.13,b-1.32),(a+1.13,b-1.32),(a+1.13,b+1.32),(a-1.13,b+1.32)])
    for x,y in ((-15,-9),(0,0),(15,9)):
        holes.append([(x-1.13,y-2.0),(x+1.13,y-2.0),(x+1.13,y+2.0),(x-1.13,y+2.0)])
    return slab_mesh('OWNER_CORE_slab_'+str(group)+'_'+str(sum(n<=e+2 for e in ends)),[(-H,-K),(H,-K),(H,K),(-H,K)],holes,.12,mat)


def apply():
    scene=bpy.context.scene
    if scene.get('owner_lobby_revision')==VERSION:return
    template=hall_template();bare=finish('SHELL_core_bare_slab',(.47,.46,.42),0,.92,1000)
    slab_cache={}
    for tower,xy,a in (('WTC1',(-55,55),0),('WTC2',(55,-55),math.pi/2)):
        root=collection(tower+'_OWNER_public_halls_and_bare_core',bpy.data.collections[tower+'_COMPLETION_study'],SOURCE,LIMIT,xy)
        p=Parts(tower+'_OWNER',root,xy,a)
        for n in range(7,111):
            z=bpy.data.objects[tower+f'_F{n:03d}_SLAB_STUDY'].location.z+.1;group,ends,start=zone_group(n)
            key=(group,tuple(n<=e+2 for e in ends))
            if key not in slab_cache:slab_cache[key]=core_slab(group,ends,n,bare)
            floor=p.mesh(f'F{n:03d}_core_floor',slab_cache[key],(0,0,z),kind='owner_core_floor');floor['floor']=n
            public=n in (44,78);service=n in (7,8,41,42,43,75,76,77,108,109,110)
            groups=range(4) if public else (group,)
            for bank in groups:
                x=-15+bank*10
                ob=bpy.data.objects.new(tower+f'_F{n:03d}_HALL_bank{bank}',None);ob.instance_type='COLLECTION';ob.instance_collection=template
                ob.location=p.point((x,0,z));ob.rotation_euler.z=a;root.objects.link(ob)
                ob['module']='owner_floor_hall';ob['floor']=n;ob['bank']=bank;ob['service_type']='service lobby fit' if service else 'sky transfer lobby' if public else 'six-car local group'
                ob['source']=SOURCE;ob['confidence']=LIMIT
                for side in (-1,1):
                    for j in range(3):
                        # Real shaft-side return walls, clear of the hallway.
                        wall=p.box(f'F{n}_shaft{bank}_{side}_{j}',(x+side*3.8,(j-1)*3.1,z+1.40),(.12,2.7,2.8),bare,kind='owner_shaft_wall');wall['floor']=n
            root['tenant_fitout']='No tenant partition walls, desks, office suspended ceilings or office carpet'
        # Replace obsolete uninterrupted shaft proxies with floor-aware enclosures.
        c=bpy.data.collections.get(tower+'_CORE_shaft_wall_types')
        if c:
            c.hide_render=True;c.hide_viewport=True;c['superseded_by']=root.name
    scene['owner_lobby_revision']=VERSION
