"""Shared closed mesh parts; no downloaded geometry or bitmap textures."""
import math
import bpy
from mathutils import Vector,Matrix
from .facade_revision import _box_mesh,_mesh
from .south_roof_revision import material


def collection(name,parent,source,limits,origin=(0,0)):
    c=bpy.data.collections.new(name);parent.children.link(c)
    c['source']=source;c['confidence']=limits;c.asset_mark();c.asset_data.description=limits;c.instance_offset=(*origin,0)
    return c


def finish(name,color,metal=0,rough=.5,grain=0):
    m=material(name,color,metal,rough)
    if grain and not m.get('microdetail'):
        n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=grain;noise.inputs['Detail'].default_value=2
        bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.00045;bump.inputs['Strength'].default_value=.3
        l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);m['microdetail']=True
    return m


def profile(points,length,mat):
    n=len(points);v=[(x,y,z) for z in (0,length) for x,y in points]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return _mesh(('IP_profile',tuple(points),round(length,6)),v,f,mat)


def cylinder(radius,length,mat,n=20):
    return profile([(radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n)) for i in range(n)],length,mat)


class Parts:
    def __init__(self,prefix,col,xy=(0,0),angle=0):self.prefix=prefix;self.col=col;self.xy=xy;self.angle=angle
    def point(self,p):
        x,y,z=p;c=math.cos(self.angle);s=math.sin(self.angle)
        return Vector((self.xy[0]+c*x-s*y,self.xy[1]+s*x+c*y,z))
    def mesh(self,name,data,p=(0,0,0),angle=0,kind='interior_detail'):
        ob=bpy.data.objects.new(self.prefix+'_'+name,data);self.col.objects.link(ob)
        ob.location=self.point(p);ob.rotation_euler.z=self.angle+angle
        ob['module']=kind;ob['source']=self.col['source'];ob['confidence']=self.col['confidence']
        return ob
    def box(self,name,p,size,mat,angle=0,kind='interior_detail'):return self.mesh(name,_box_mesh(size,mat),p,angle,kind)
    def bar(self,name,a,b,section,mat,kind='steel_detail'):
        a,b=self.point(a),self.point(b);ob=self.mesh(name,profile(section,(b-a).length,mat),kind=kind)
        d=(b-a).normalized();up=Vector((0,0,1)) if abs(d.z)<.99 else Vector((0,1,0))
        side=up.cross(d).normalized();up=d.cross(side)
        ob.location=a;ob.rotation_euler=Matrix((side,up,d)).transposed().to_euler();return ob
    def tube(self,name,a,b,r,mat,kind='interior_detail'):
        a,b=self.point(a),self.point(b);ob=self.mesh(name,cylinder(r,(b-a).length,mat),kind=kind)
        ob.location=a;ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return ob
    def disk(self,name,p,r,h,mat,kind='interior_detail'):return self.mesh(name,cylinder(r,h,mat),p,kind=kind)
    def area(self,name,p,power,size,color=(1,.73,.45)):
        d=bpy.data.lights.new(self.prefix+'_'+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
        ob=bpy.data.objects.new(d.name,d);self.col.objects.link(ob);ob.location=self.point(p)
        ob['source']=self.col['source'];ob['confidence']='Lamp photometry/color/position CG estimate';return ob


def lift(p,name,center,z,top,metal,glass,stone,open_door=False,buttons=12):
    """Editable cab, split doors, door operator, guides, weight and traction type."""
    x,y=center
    def box(n,loc,size,mat=metal):return p.box(name+'_'+n,(x+loc[0],y+loc[1],z+loc[2]),size,mat,kind='elevator_component')
    def tube(n,a,b,r=.012):return p.tube(name+'_'+n,(x+a[0],y+a[1],z+a[2]),(x+b[0],y+b[1],z+b[2]),r,metal,'elevator_component')
    box('floor',(0,0,.05),(2.15,2.05,.10),stone)
    for side in (-1,1):
        box('sidewall'+str(side),(side*1.085,0,1.3),(.045,2.1,2.5),metal)
        tube('handrail'+str(side),(side*1.04,-.7,.95),(side*1.04,.7,.95),.022)
        box('guide'+str(side),(side*1.25,0,(top-z)/2),(.06,.07,top-z))
        for h in (.15,2.5):box(f'guide_shoe_{side}_{h:.2f}',(side*1.18,0,h),(.17,.18,.12))
        box('jamb'+str(side),(side*.79,-1.075,1.25),(.13,.15,2.5))
        box('landing_door'+str(side),(side*(.31+(.58 if open_door else 0)),-1.06,1.18),(.61,.035,2.28),metal)
        for k in range(4):box(f'sill_slot{side}_{k}',(side*.38,-1.11+k*.018,.115),(.72,.006,.012))
    box('rearwall',(0,1.06,1.3),(2.15,.045,2.5),metal)
    box('rear_mirror',(0,1.025,1.55),(1.7,.009,1.1),glass)
    box('ceiling',(0,0,2.575),(2.2,2.15,.08))
    diffuser=finish('IP_lift_diffuser',(.93,.86,.68),0,.25)
    bs=diffuser.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.83,.58,1);bs.inputs['Emission Strength'].default_value=2
    box('light_diffuser',(0,0,2.526),(1.5,1.4,.012),diffuser)
    box('button_panel',(.93,-.66,1.25),(.018,.32,.90))
    for i in range(buttons):
        yy=-.73+(i%2)*.14;zz=.95+(i//2)*.08
        tube(f'button{i}',(.912,yy,zz),(.901,yy,zz),.017)
    box('door_header',(0,-1.08,2.5),(1.8,.18,.13));tube('operator_track',(-.9,-1.07,2.68),(.9,-1.07,2.68),.025)
    for side in (-1,1):
        tube('door_hanger'+str(side),(side*.32,-1.07,2.37),(side*.32,-1.07,2.67),.015)
        tube('hanger_roller'+str(side),(side*.32,-1.10,2.65),(side*.32,-1.04,2.65),.047)
    box('door_operator_motor',(.6,-.88,2.7),(.23,.28,.16))
    # Counterweight sits near the top while the inspection car is at the lobby.
    for j in range(8):box('counterweight'+str(j),(0,1.43,top-z-2+j*.13),(.85,.17,.105))
    for k in range(6):
        xx=(k-2.5)*.045;tube('rope_car'+str(k),(xx,0,2.7),(xx,0,top-z-.1),.006)
        tube('rope_weight'+str(k),(xx,1.4,top-z-1),(xx,1.4,top-z-.1),.006)
    tube('traction_sheave',(0,.5,top-z-.35),(0,.85,top-z-.35),.27)
    box('traction_bed',(0,.65,top-z-.7),(1.4,1.2,.16));box('traction_motor',(.6,.65,top-z-.35),(.45,.65,.4))
