"""Closed, reusable fabrication meshes; component boundaries retained in metadata."""
import math
import bpy
from mathutils import Vector,Matrix


class Batch:
    def __init__(self,name,mat):self.name=name;self.mat=mat;self.v=[];self.f=[];self.count=0
    def add(self,verts,faces,matrix=None):
        n=len(self.v);self.v.extend(tuple(matrix@Vector(p)) if matrix else p for p in verts)
        self.f.extend(tuple(n+i for i in face) for face in faces);self.count+=1
    def box(self,p,size):
        x,y,z=p;a,b,c=(s/2 for s in size)
        self.add([(x+u*a,y+v*b,z+w*c) for u,v,w in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    def bar(self,a,b,section):
        if sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(section,section[1:]+section[:1]))<0:section=section[::-1]
        a,b=Vector(a),Vector(b);d=(b-a).normalized();up=Vector((0,0,1)) if abs(d.z)<.99 else Vector((0,1,0));side=up.cross(d).normalized();up=d.cross(side)
        mat=Matrix((side,up,d)).transposed().to_4x4();mat.translation=a
        n=len(section);length=(b-a).length
        self.add([(x,y,z) for z in (0,length) for x,y in section],[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)
    def tube(self,a,b,r,n=10):self.bar(a,b,[(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n)) for i in range(n)])
    def mesh(self,col,module):
        if not self.v:return None
        m=bpy.data.meshes.new(self.name);m.from_pydata(self.v,[],self.f);m.materials.append(self.mat)
        o=bpy.data.objects.new(self.name,m);col.objects.link(o);o['module']=module;o['component_count']=self.count
        o['source']=col.get('source','');o['confidence']=col.get('confidence','');return o


def i_section(h=.46,w=.19,web=.011,flange=.018):
    return [(-w/2,-h/2),(w/2,-h/2),(w/2,-h/2+flange),(web/2,-h/2+flange),(web/2,h/2-flange),(w/2,h/2-flange),(w/2,h/2),(-w/2,h/2),(-w/2,h/2-flange),(-web/2,h/2-flange),(-web/2,-h/2+flange),(-w/2,-h/2+flange)]


def orient_framing_solids():
    """Correct each disconnected steel solid, including mirrored angle pairs."""
    import bmesh
    for mesh in bpy.data.meshes:
        if not mesh.users or not mesh.name.startswith('SHELL_'):continue
        bm=bmesh.new();bm.from_mesh(mesh)
        if bm.faces and all(e.is_manifold for e in bm.edges):
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh)
        bm.free()
