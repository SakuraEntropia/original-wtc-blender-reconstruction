"""South roof: photo-fitted observation ring, access and communications.

Original historical aerial is reference only, never an embedded texture. The
8.4x7.6m central pad is a photographic fit; the mirror's 55x50ft caption is
not adopted without the original dimensioned page. No equipment model or
installation date is asserted. Absolute roof registration remains unresolved.
"""
import math
import bpy
from mathutils import Vector
from .facade_revision import _box_mesh

VERSION='2026-10-15-south-roof-photo-v2'
SOURCE='https://www.airfields-freeman.com/NY/Airfields_NY_NY_Brooklyn_htm_29933882.jpg'
X,Y=55,-55
ROOF=1362*.3048
DECK=ROOF+.60
MAINT=ROOF-4.572+.445
CACHE={}


def material(name,color,metal=0,rough=.5):
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    return m


def object_mesh(name,mesh,col,xyz=(0,0,0)):
    o=bpy.data.objects.new('WTC2_SR_'+name,mesh);col.objects.link(o)
    o.location=(X+xyz[0],Y+xyz[1],xyz[2])
    o['source']=SOURCE;o['confidence']='Historical aerial topology; component dimensions/positions photo-fitted, not fabrication drawings'
    o['south_roof_revision']=VERSION
    return o


def box(name,xyz,size,col,mat):return object_mesh(name,_box_mesh(size,mat),col,xyz)


def beam(name,a,b,width,col,mat):
    a,b=Vector(a),Vector(b)
    ob=box(name,(a+b)/2,(width,width,(b-a).length),col,mat)
    ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return ob


def octagon(q,c):return [(-q+c,-q),(q-c,-q),(q,-q+c),(q,q-c),(q-c,q),(-q+c,q),(-q,q-c),(-q,-q+c)]


def ring_mesh(outer,inner,thickness,mat):
    verts=[(x,y,z) for z in (-thickness,0) for loop in (outer,inner) for x,y in loop]
    faces=[]
    for i in range(8):
        j=(i+1)%8
        faces.extend([(16+i,16+j,24+j,24+i),(i,8+i,8+j,j),
                      (i,j,16+j,16+i),(8+j,8+i,24+i,24+j)])
    m=bpy.data.meshes.new('SOUTH_ROOF_octagonal_ring_shared');m.from_pydata(verts,[],faces);m.materials.append(mat)
    return m


def guardrail(name,path,z,height,col,mat,spacing=1.2,picket=False):
    for edge,(a,b) in enumerate(zip(path,path[1:]+path[:1])):
        a,b=Vector(a),Vector(b);length=(b-a).length;n=max(1,math.ceil(length/spacing))
        for j in range(n):
            p=a+(b-a)*j/n
            if name=='inner_public_guardrail' and edge in (0,4) and abs(p.x)<1.35:continue
            box(f'{name}_e{edge}_post{j}',(p.x,p.y,z+height/2),(.035,.035,height),col,mat)
        for lift in ((.15,height) if picket else (.12,.58,height)):
            if name=='inner_public_guardrail' and edge in (0,4):
                for suffix,u0,u1 in (('L',-abs(a.x),-1.35),('R',1.35,abs(a.x))):
                    beam(f'{name}_e{edge}_rail{lift}_{suffix}',(u0,a.y,z+lift),(u1,a.y,z+lift),.045,col,mat)
            else:beam(f'{name}_e{edge}_rail{lift}',(*a,z+lift),(*b,z+lift),.045,col,mat)


def dish(name,xyz,radius,col,white,steel):
    # Closed thin paraboloid, local +Z boresight; a separate feed tripod.
    key=(radius,white.name)
    if key not in CACHE:
        verts=[];faces=[];rings=8;segments=32
        # Tiny central ring avoids coincident pole vertices.
        for back in (False,True):
            for ring in range(rings+1):
                r=radius*(.015+.985*ring/rings)
                z=.31*(r/radius)**2-(.025 if back else 0)
                verts.extend((r*math.cos(k*math.tau/segments),r*math.sin(k*math.tau/segments),z) for k in range(segments))
        n=(rings+1)*segments
        for layer in (0,1):
            for j in range(rings):
                for k in range(segments):
                    a=layer*n+j*segments+k;b=layer*n+j*segments+(k+1)%segments
                    f=(a,b,b+segments,a+segments);faces.append(f if not layer else f[::-1])
        for j in (0,rings):
            for k in range(segments):
                a=j*segments+k;b=j*segments+(k+1)%segments
                f=(a,a+n,b+n,b);faces.append(f if j==rings else f[::-1])
        m=bpy.data.meshes.new('SOUTH_ROOF_paraboloid_shared');m.from_pydata(verts,[],faces);m.materials.append(white)
        for p in m.polygons:p.use_smooth=True
        CACHE[key]=m
    ob=object_mesh(name,CACHE[key],col,xyz)
    normal=Vector((.2,-1,.22)).normalized();ob.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
    rot=ob.rotation_euler.to_matrix();center=Vector(xyz);tip=center+rot@Vector((0,0,.9))
    for k in range(3):
        p=center+rot@Vector((radius*.8*math.cos(k*math.tau/3),radius*.8*math.sin(k*math.tau/3),.2))
        beam(name+f'_feed_strut{k}',p,tip,.025,col,steel)
    box(name+'_feed',tip,(.14,.14,.18),col,steel)
    return ob


def mast(name,xy,height,col,steel,white):
    x,y=xy;z=MAINT+.1;w=.72
    for sx in (-1,1):
        for sy in (-1,1):
            beam(name+f'_leg{sx}{sy}',(x+sx*w,y+sy*w,z),(x+sx*w*.6,y+sy*w*.6,z+height),.085,col,steel)
            box(name+f'_base{sx}{sy}',(x+sx*w,y+sy*w,z),(.34,.34,.075),col,steel)
    n=math.ceil(height/1.5)
    for j in range(n):
        z1=z+j*height/n;z2=z+(j+1)*height/n
        for side in range(4):
            a=side*math.pi/2
            def p(u,v,h):return (x+u*math.cos(a)-v*math.sin(a),y+u*math.sin(a)+v*math.cos(a),h)
            beam(name+f'_cross{j}_{side}',p(-w,-w,z1),p(w,-w,z2),.045,col,steel)
            beam(name+f'_girt{j}_{side}',p(-w,-w,z1),p(w,-w,z1),.055,col,steel)
    dish(name+'_dish',(x,y-1.05,z+height*.65),1.08,col,white,steel)
    beam(name+'_dish_bracket',(x,y,z+height*.65),(x,y-1.2,z+height*.65),.11,col,steel)
    box(name+'_junction_box',(x+.85,y,z+.7),(.48,.35,.6),col,white)
    for j in range(9):
        box(name+f'_ladder{j}',(x+.9,y,z+.45+j*.45),(.4,.035,.025),col,steel)
    beam(name+'_cable_riser',(x+.87,y+.15,z),(x+.87,y+.15,z+height*.65),.035,col,steel)
    for k in range(3):
        beam(name+f'_whip{k}',(x+(k-1)*.35,y,z+height),(x+(k-1)*.35,y,z+height+1.1),.022,col,steel)


def access(name,sy,col,steel,wall):
    # Two opposite gabled access bulkheads, as visible in the aerial.
    x,y=0,sy*18.7;bottom=MAINT;top=DECK+1.7
    box(name+'_body',(x,y,(bottom+top)/2),(4.7,6.2,top-bottom),col,wall)
    for sign in (-1,1):
        a=Vector((sign*2.55,0,-.65));b=Vector((0,0,.65))
        ob=box(name+f'_gable_roof{sign}',(x+sign*1.275,y,top+.65),((b-a).length,6.65,.09),col,steel)
        ob.rotation_euler.y=-sign*math.atan2(1.3,2.55)
    # Doors face the observation walkway; framed leaves, hinges and handles.
    yy=y+sy*3.135
    for side in (-1,1):
        box(name+f'_door{side}',(side*.54,yy,DECK+1.03),(1.03,.055,2.06),col,steel)
        box(name+f'_handle{side}',(side*.18,yy+sy*.05,DECK+1.05),(.04,.045,.35),col,wall)
    for dx in (-1.14,1.14):box(name+f'_jamb{dx}',(dx,yy,DECK+1.08),(.075,.12,2.16),col,wall)
    box(name+'_header',(0,yy,DECK+2.15),(2.35,.12,.08),col,wall)
    bridge_center=(abs(yy)+23.3)/2
    box(name+'_walkway_bridge',(0,sy*bridge_center,DECK-.10),(2.7,23.3-abs(yy),.20),col,steel)
    for dx in (-1.3,1.3):
        beam(name+f'_bridge_rail{dx}',(dx,yy,DECK+1.15),(dx,sy*23.3,DECK+1.15),.045,col,steel)
        box(name+f'_bridge_post{dx}',(dx,yy,DECK+.575),(.045,.045,1.15),col,steel)
    # Service stairs descend into the central maintenance well.
    n=25;run=.26;rise=(DECK-MAINT)/n;yy=y-sy*3.2
    for j in range(n):
        box(name+f'_service_step{j}',(0,yy-sy*(j+.5)*run,DECK-(j+.5)*rise),(1.4,.28,.10),col,steel)
    for dx in (-.78,.78):
        beam(name+f'_stringer{dx}',(dx,yy,DECK-.15),(dx,yy-sy*n*run,MAINT-.15),.12,col,steel)
        beam(name+f'_stair_rail{dx}',(dx,yy,DECK+.95),(dx,yy-sy*n*run,MAINT+.95),.04,col,steel)


def apply():
    scene=bpy.context.scene
    if scene.get('south_roof_revision')==VERSION:return
    root=bpy.data.collections['WTC2_COMPLETION_study']
    old=next(c for c in root.children if c.name.startswith('roof_observation'))
    old.hide_render=True;old.hide_viewport=True;old['superseded_by']=VERSION
    previous=bpy.data.collections.get('WTC2_ROOF_observation_and_communications_STUDY')
    if previous:bpy.data.batch_remove(ids=list(previous.objects)+[previous])
    col=bpy.data.collections.new('WTC2_ROOF_observation_and_communications_STUDY');root.children.link(col)
    col['source']=SOURCE;col['confidence']='Aerial-fitted ring walkway, central well, two access houses and communications; dimensions and datum registration estimated.'
    col['deck_z_estimated_m']=DECK;col['maintenance_z_estimated_m']=MAINT
    col['central_pad_size_estimated_m']=[8.4,7.6];col['south_roof_revision']=VERSION
    col.asset_mark();col.asset_data.description=col['confidence'];col.instance_offset=(X,Y,0)
    steel=material('SR_galvanized_steel',(.43,.46,.47),.75,.35)
    white=material('SR_aged_white_finish',(.77,.79,.76),.25,.42)
    blue=material('SR_observation_blue_floor',(.16,.36,.51),.05,.64)
    dark=material('SR_dark_access_cladding',(.25,.27,.28),.25,.62)
    yellow=material('SR_pad_yellow_border',(.85,.57,.025),.1,.56)
    red=material('SR_pad_red_marking',(.65,.025,.018),0,.55)
    membrane=material('SR_weathered_tan_membrane',(.40,.32,.23),0,.83)
    for ob in bpy.data.objects:
        if ob.type=='MESH' and ob.name.startswith('WTC2') and ('roof_membrane' in ob.name or ob.name=='WTC2_roof_datum'):
            if ob.data.users>1:ob.data=ob.data.copy()
            ob.data.materials.clear();ob.data.materials.append(membrane)
            ob['finish_confidence']='Muted tan roof tone photo-fitted; membrane product/weathering not known'
    outside=octagon(26,3.2);inside=octagon(23.3,2.7)
    floor=object_mesh('blue_ring_floor',ring_mesh(outside,inside,.20,blue),col,(0,0,DECK))
    floor['module']='observation_ring_floor';floor['walkway_width_estimated_m']=2.7
    guardrail('outer_public_guardrail',outside,DECK,1.15,col,white)
    guardrail('inner_public_guardrail',inside,DECK,1.15,col,white)
    guardrail('maintenance_security_fence',octagon(28.7,3.2),MAINT,2.0,col,steel,.18,True)
    # Eight edge girders and repeated support bays leave the central well open.
    for edge,(a,b) in enumerate(zip(outside,outside[1:]+outside[:1])):
        a,b=Vector(a),Vector(b);n=max(1,math.ceil((b-a).length/3.0))
        beam(f'outer_edge_girder{edge}',(*a,DECK-.30),(*b,DECK-.30),.20,col,steel)
        c,d=Vector(inside[edge]),Vector(inside[(edge+1)%8])
        beam(f'inner_edge_girder{edge}',(*c,DECK-.30),(*d,DECK-.30),.20,col,steel)
        for j in range(n):
            p=a+(b-a)*(j+.5)/n;q=c+(d-c)*(j+.5)/n
            beam(f'transverse_joist{edge}_{j}',(*p,DECK-.23),(*q,DECK-.23),.12,col,steel)
            for k,pt in enumerate((p,q)):
                box(f'walk_support{edge}_{j}_{k}',(pt.x,pt.y,(MAINT+DECK-.4)/2),(.12,.12,DECK-.4-MAINT),col,steel)
                box(f'walk_baseplate{edge}_{j}_{k}',(pt.x,pt.y,MAINT+.045),(.33,.33,.09),col,steel)
            # Thin joints split the walking surface without coplanar duplicate faces.
            beam(f'deck_expansion_joint{edge}_{j}',(*p,DECK+.002),(*q,DECK+.002),.008,col,dark)
    access('north_access',1,col,steel,dark);access('south_access',-1,col,steel,dark)
    # Historic small central pad and horizontal safety net perimeter.
    pad=DECK+.55;box('historic_pad_deck',(0,0,pad-.12),(8.4,7.6,.24),col,steel)
    box('pad_yellow',(0,0,pad+.006),(6.1,5.6,.012),col,yellow)
    box('pad_white',(0,0,pad+.018),(5.7,5.2,.012),col,white)
    for sx in (-1,1):
        for sy in (-1,1):
            box(f'pad_leg{sx}{sy}',(sx*2.5,sy*2.2,(MAINT+pad-.3)/2),(.22,.22,pad-.3-MAINT),col,steel)
            beam(f'pad_brace{sx}{sy}',(sx*2.5,sy*2.2,MAINT+.15),(-sx*2.5,sy*2.2,pad-.3),.085,col,steel)
    # Red circle uses geometry; no downloaded logos, photographs or fonts.
    verts=[];faces=[]
    for rr in (1.58,1.28):verts.extend((rr*math.cos(k*math.tau/64),rr*math.sin(k*math.tau/64),0) for k in range(64))
    for k in range(64):faces.append((k,(k+1)%64,(k+1)%64+64,k+64))
    m=bpy.data.meshes.new('SR_pad_circle_marking');m.from_pydata(verts,[],faces);m.materials.append(red)
    object_mesh('pad_circle_paint',m,col,(0,0,pad+.027))
    text=bpy.data.curves.new('SR_historic_pad_15','FONT');text.body='15';text.align_x='CENTER';text.align_y='CENTER';text.size=1.55;text.extrude=.001;text.materials.append(red)
    ob=bpy.data.objects.new('WTC2_SR_historic_pad_number15',text);col.objects.link(ob);ob.location=(X,Y,pad+.030)
    for side in range(4):
        angle=side*math.pi/2
        for j in range(18):
            u=-4.8+j*9.6/17
            a=Vector((u,-3.85,pad));b=Vector((u,-4.75,pad+.26))
            rot=lambda p:(p.x*math.cos(angle)-p.y*math.sin(angle),p.x*math.sin(angle)+p.y*math.cos(angle),p.z)
            beam(f'pad_safety_net_radial{side}_{j}',rot(a),rot(b),.013,col,steel)
        for k in range(4):
            d=3.85+k*.3;h=pad+(d-3.85)*.26/.9
            beam(f'pad_safety_net_long{side}_{k}',rot(Vector((-4.8,-d,h))),rot(Vector((4.8,-d,h))),.013,col,steel)
    # Three visually distinct lattice masts, dishes and antenna arrays.
    for name,xy,height in (('west_comm',(-12,-11),9.8),('east_comm',(11,-10),7.8),('north_comm',(-9,13),9.2)):
        mast(name,xy,height,col,steel,white)
    beam('west_top_array_spine',(-15,-11,MAINT+11),(-9,-11,MAINT+11),.08,col,steel)
    for j in range(9):
        u=-15+j*.75;beam(f'west_top_array_element{j}',(u,-12,MAINT+11),(u,-10,MAINT+11),.025,col,steel)
    # Low roof stand-offs and conduit runs visible in the well; schedules unknown.
    for i in range(9):
        for j in range(9):
            x,y=-19+i*4.7,-19+j*4.7
            if abs(x)<5 and abs(y)<7:continue
            if abs(x)<3 and abs(y)>12:continue
            box(f'well_pedestal_base{i}_{j}',(x,y,MAINT+.025),(.30,.30,.05),col,steel)
            box(f'well_pedestal{i}_{j}',(x,y,MAINT+.17),(.065,.065,.30),col,white)
    for x in (-15,15):
        beam(f'well_conduit{x}',(x,-16,MAINT+.09),(x,16,MAINT+.09),.055,col,steel)
        for y in (-14,0,14):box(f'conduit_box{x}_{y}',(x,y,MAINT+.19),(.4,.3,.25),col,dark)
    scene['south_roof_revision']=VERSION
