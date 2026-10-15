"""A-AB-252 / A-B-22 curved mezzanine wells and four-bay entrance groups.

Source topology is traced; the unrectified trace has no surveyed tolerance.
Small door/rail profiles and escalator machinery remain explicit CG types.
"""
import math
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from .completion import PLAZA_Z
from .facade_revision import _box_mesh,_face_object
from .south_roof_revision import material

VERSION='2026-10-15-traced-mezzanine-revolving-v2'
SOURCE='Original A-AB-252 plaza floor/balcony detail; A-B-22 South plaza plan; NIST1-7 Figs2-4/2-5'
H=137*.3048/2;K=87*.3048/2


def well(sign):
    # Shared plan: core long axis u; wells lie on the two short-axis sides.
    segments=[((-H,K),(-H,K+5.7),(-H,K+9.5),(-H+4,K+10.5)),
              ((-H+4,K+10.5),(-8,K+12.8),(8,K+12.8),(H-4,K+10.5)),
              ((H-4,K+10.5),(H,K+9.5),(H,K+5.7),(H,K))]
    path=[]
    for controls in segments:
        for j in range(17):
            if path and j==0:continue
            t=j/16;s=1-t
            p=Vector(controls[0])*s**3+Vector(controls[1])*3*s*s*t+Vector(controls[2])*3*s*t*t+Vector(controls[3])*t**3
            path.append((p.x,sign*p.y))
    return path


def slab_mesh(name,outline,holes,depth,mat):
    coords=[];regions=[]
    for loop in [outline]+holes:
        if sum(a[0]*c[1]-c[0]*a[1] for a,c in zip(loop,loop[1:]+loop[:1]))<0:loop=loop[::-1]
        regions.append(list(range(len(coords),len(coords)+len(loop))));coords.extend(Vector(p) for p in loop)
    vertices,_,faces,_,_,orig=delaunay_2d_cdt(coords,[],regions,0,1e-7,True)
    faces=[list(f) for f,ids in zip(faces,orig) if 0 in ids and not any(i>0 for i in ids)]
    used=sorted({i for f in faces for i in f});remap={i:j for j,i in enumerate(used)}
    vertices=[vertices[i] for i in used];faces=[[remap[i] for i in f] for f in faces];n=len(vertices)
    v=[(p.x,p.y,z) for z in (0,-depth) for p in vertices]
    polys=[tuple(f) for f in faces]+[tuple(n+i for i in f[::-1]) for f in faces]
    counts={};directions={}
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            key=tuple(sorted((a,b)));counts[key]=counts.get(key,0)+1;directions[key]=(a,b)
    for key,count in counts.items():
        if count==1:
            a,b=directions[key];polys.append((a,a+n,b+n,b))
    m=bpy.data.meshes.new(name);m.from_pydata(v,[],polys);m.materials.append(mat);m.update()
    return m


class Builder:
    def __init__(self,tower,xy,angle,col):self.tower=tower;self.xy=xy;self.angle=angle;self.col=col
    def point(self,p):
        x,y,z=p;c,s=math.cos(self.angle),math.sin(self.angle)
        return Vector((self.xy[0]+c*x-s*y,self.xy[1]+s*x+c*y,z))
    def obj(self,name,mesh,p=(0,0,0)):
        ob=bpy.data.objects.new(self.tower+'_LP_'+name,mesh);self.col.objects.link(ob)
        ob.location=self.point(p);ob.rotation_euler.z=self.angle
        ob['source']=SOURCE;ob['confidence']='Source plan topology; manual curve trace and small profiles estimated, no surveyed tolerance';ob['lobby_plan_revision']=VERSION
        return ob
    def box(self,name,p,size,mat):return self.obj(name,_box_mesh(size,mat),p)
    def beam(self,name,a,b,width,mat):
        a,b=self.point(a),self.point(b);ob=self.obj(name,_box_mesh((width,width,(b-a).length),mat))
        ob.location=(a+b)/2;ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return ob


def balcony(b,stone,steel,glass,carpet):
    q=31.38;c=1.45
    outer=[(-q+c,-q),(q-c,-q),(q,-q+c),(q,q-c),(q-c,q),(-q+c,q),(-q,q-c),(-q,-q+c)]
    paths=[well(s) for s in (-1,1)]
    escalator_slot=[(22.0,3.5),(25.8,3.5),(25.8,18.0),(22.0,18.0)]
    floor=b.obj('curved_mezzanine_floor',slab_mesh(b.tower+'_plaza_floor_two_wells',outer,paths+[escalator_slot],.32,stone),(0,0,PLAZA_Z))
    floor['module']='source_mezzanine_floor';floor['curved_well_count']=2;floor['escalator_slot_count']=1
    for side,path in enumerate(paths):
        for j,(a,c) in enumerate(zip(path,path[1:])):
            a,c=Vector(a),Vector(c);d=c-a;length=d.length;angle=math.atan2(d.y,d.x)
            for suffix,z,sz,wide,mat in (('shoe',.07,.14,.11,steel),('glass',.60,1.0,.012,glass),('cap',1.12,.045,.055,steel)):
                ob=b.box(f'well{side}_{suffix}{j}',(*(a+c)/2,PLAZA_Z+z),(length+.001,wide,sz),mat)
                ob.rotation_euler.z=b.angle+angle
    for side in (-1,1):
        b.box(f'outer_carpet_long{side}',(0,side*28.2,PLAZA_Z+.008),(50,2.2,.016),carpet)
        b.box(f'outer_carpet_short{side}',(side*28.2,0,PLAZA_Z+.008),(2.2,50,.016),carpet)
    # Paired escalators occupy a real opening and join the lower lobby datum.
    rise=PLAZA_Z-.24;run=rise/math.tan(math.radians(30));n=44
    for bank,u in enumerate((22.85,24.65)):
        for j in range(n):
            v=4+(j+.5)*run/n;z=PLAZA_Z-(j+.5)*rise/n
            b.box(f'escalator{bank}_tread{j}',(u,v,z),(1.0,run/n+.005,.075),steel)
            for groove in (-.28,0,.28):b.box(f'escalator{bank}_cleat{j}_{groove}',(u+groove,v,z+.041),(.015,run/n,.009),steel)
        for s in (-1,1):
            b.beam(f'escalator{bank}_stringer{s}',(u+s*.57,4,PLAZA_Z-.25),(u+s*.57,4+run,.24-.25),.16,steel)
            b.beam(f'escalator{bank}_handrail{s}',(u+s*.59,4,PLAZA_Z+.9),(u+s*.59,4+run,.24+.9),.065,steel)
        b.box(f'escalator{bank}_bottom_landing',(u,4+run+.6,.25),(1.25,1.2,.10),steel)


def entrance(tower,xy,col,steel,glass):
    side=1 if tower=='WTC1' else 2;q=(207+2/12)*.3048/2-.006
    def box(name,u,depth,z,size,mat):
        ob=_face_object(tower+'_LP_'+name,_box_mesh(size,mat),xy,side,depth,z,col,u)
        ob['source']='Original four-bay entrance elevation and WTC2 plaza door plan';ob['confidence']='Two revolving drums flanking two double-leaf bays;10ft tree-bay pitch; drum/gauge/door height estimated';return ob
    centers=(-4.572,-1.524,1.524,4.572);height=2.65;r=1.2
    box('entry_header',0,q,PLAZA_Z+height+.16,(12.55,.24,.32),steel)
    for k,u in enumerate(centers):
        for s in (-1,1):box(f'entry_jamb{k}_{s}',u+s*1.28,q,PLAZA_Z+height/2,(.075,.2,height),steel)
        if k in (0,3):
            center=q-.82
            box(f'revolving{k}_pivot',u,center,PLAZA_Z+height/2,(.065,.065,height),steel)
            for wing in range(4):
                a=math.pi/4+wing*math.pi/2
                # A wing is a framed radial leaf; the four leaves share the hub.
                du,dv=math.cos(a),math.sin(a)
                ob=box(f'revolving{k}_glass_wing{wing}',u+du*r/2,center-dv*r/2,PLAZA_Z+height/2,(r-.07,.012,height-.13),glass)
                ob.rotation_euler.z=side*math.pi/2+a
                for offset in (-height/2+.05,height/2-.05):
                    ob=box(f'revolving{k}_wingrail{wing}_{offset:.3f}',u+du*r/2,center-dv*r/2,PLAZA_Z+height/2+offset,(r-.04,.045,.045),steel)
                    ob.rotation_euler.z=side*math.pi/2+a
                box(f'revolving{k}_stile{wing}',u+du*(r-.04),center-dv*(r-.04),PLAZA_Z+height/2,(.045,.045,height),steel)
            # Fixed curved side screens leave generous opposing entrances.
            for arc,start in enumerate((-math.pi/4,3*math.pi/4)):
                for j in range(16):
                    a=start+j*math.pi/2/16;b=a+math.pi/2/16;mid=(a+b)/2
                    chord=2*r*math.sin((b-a)/2)
                    for suffix,z,h,w,mat in (('screen',height/2,height-.08,.012,glass),('head',height-.02,.07,.06,steel),('base',.035,.07,.06,steel)):
                        ob=box(f'revolving{k}_{suffix}{arc}_{j}',u+r*math.cos(mid),center-r*math.sin(mid),PLAZA_Z+z,(chord+.002,w,h),mat)
                        ob.rotation_euler.z=side*math.pi/2+mid+math.pi/2
            box(f'revolving{k}_overhead_operator',u,center,PLAZA_Z+height+.08,(.45,.45,.16),steel)
        else:
            for leaf,s in enumerate((-1,1)):
                v=u+s*.61
                box(f'swing{k}_glass{leaf}',v,q,PLAZA_Z+height/2,(1.16,.012,height-.12),glass)
                for edge in (-1,1):box(f'swing{k}_stile{leaf}_{edge}',v+edge*.59,q,PLAZA_Z+height/2,(.04,.05,height),steel)
                for z in (.035,height-.035):box(f'swing{k}_rail{leaf}_{z:.3f}',v,q,PLAZA_Z+z,(1.22,.05,.07),steel)
                box(f'swing{k}_pushbar{leaf}',v,q+.06,PLAZA_Z+1.05,(.8,.035,.035),steel)
    # Cut the original continuous glass shell, rather than laying doors over it.
    box('entry_plaza_apron',0,34.39,PLAZA_Z-.16,(12.8,6.02,.32),bpy.data.materials[tower+'_warm_pale_stone_STUDY'])
    ob=bpy.data.objects[tower+'_concourse_to_tree_glass_STUDY']
    if ob.get('entry_openings')==4:return
    cutters=bpy.data.collections.new(tower+'_entrance_boolean_TEMP');bpy.context.scene.collection.children.link(cutters)
    for k,u in enumerate(centers):
        _face_object(tower+f'_doorcut{k}',_box_mesh((2.5,1.5,height+.03),steel),xy,side,q,PLAZA_Z+height/2,cutters,u)
    print(tower+'_LP_BOOLEAN_START',flush=True)
    mod=ob.modifiers.new('real_entry_openings','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.operand_type='COLLECTION';mod.collection=cutters
    bpy.context.view_layer.update();ob.data=bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    print(tower+'_LP_BOOLEAN_DONE',flush=True)
    ob.modifiers.remove(mod);ob['entry_openings']=4;ob['source_entry_plan']=SOURCE
    bpy.data.batch_remove(ids=list(cutters.objects)+[cutters])


def apply():
    scene=bpy.context.scene
    if scene.get('source_lobby_plan_revision')==VERSION:return
    steel=material('LP_brushed_stainless',(.46,.48,.47),.8,.28)
    glass=material('LP_clear_glass',(.66,.77,.76),0,.12)
    bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=1.45
    carpet=material('LP_muted_green_carpet',(.17,.20,.15),0,.92)
    for tower,xy,angle in (('WTC1',(-55,55),0),('WTC2',(55,-55),math.pi/2)):
        old=bpy.data.objects[tower+'_continuous_plaza_lobby_floor_STUDY'];old.hide_render=True;old.hide_viewport=True;old['superseded_by']=VERSION
        for ob in bpy.data.objects:
            if ob.name.startswith(tower+'_plaza_entrance_'):ob.hide_render=True;ob.hide_viewport=True;ob['superseded_by']=VERSION
        parent=bpy.data.collections[tower+'_LOBBY_photo_interpretation_STUDY']
        previous=bpy.data.collections.get(tower+'_LOBBY_curved_mezzanine_and_entrances_STUDY')
        if previous:bpy.data.batch_remove(ids=list(previous.objects)+[previous])
        col=bpy.data.collections.new(tower+'_LOBBY_curved_mezzanine_and_entrances_STUDY');parent.children.link(col)
        col['source']=SOURCE;col['confidence']='Original plan topology; approximate manual curves, 22ft level difference; fit-out and machinery simplified'
        col.asset_mark();col.asset_data.description=col['confidence'];col.instance_offset=(*xy,0)
        b=Builder(tower,xy,angle,col)
        print(tower+'_LP_BALCONY_START',flush=True)
        balcony(b,bpy.data.materials[tower+'_warm_pale_stone_STUDY'],steel,glass,carpet)
        print(tower+'_LP_ENTRANCE_START',flush=True)
        entrance(tower,xy,col,steel,glass)
    scene['source_lobby_plan_revision']=VERSION
