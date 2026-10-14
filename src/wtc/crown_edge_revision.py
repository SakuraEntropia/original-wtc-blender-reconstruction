"""Mitered crown hood, folded corner jambs and inspectable support type parts.

Historical fabrication sizes of these junctions are unavailable. The same
documented octagonal perimeter is used at all seams; cosmetic curve breadth,
sheet gauge, support sections and connections are explicitly estimates.
"""
import math
import bpy
from mathutils import Vector
from .completion import FT, PLAZA_Z
from .facade_detail import outline, OUTER_HALF, REFERENCE_HALF, object_mesh, append_box
from .facade_revision import _curve_ribbon, _face_object, IN, PITCH, NIST, PHOTO
from .lowrise_detail import cube, subgroup

VERSION='2026-10-14-crown-junction-v1'
CACHE={}
LIMITS='Photo-informed CG junction; sheet gauge/curve breadth/frame profiles/support sections/bolt pattern are estimates, not fabrication dimensions.'


def mesh(key,verts,faces,mat):
    key=(key,mat.name)
    if key not in CACHE:
        m=bpy.data.meshes.new('crown_junction_prototype_'+str(len(CACHE)))
        m.from_pydata(verts,[],faces);m.materials.append(mat);CACHE[key]=m
    return CACHE[key]


def tag(ob,module):
    ob['module']=module;ob['source']=NIST+'; '+PHOTO;ob['confidence']=LIMITS
    return ob


def prism(name,pts,lo,hi,col,mat):
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))<0:pts=pts[::-1]
    n=len(pts)
    v=[(x,y,z) for z in (lo,hi) for x,y in pts]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return object_mesh(name,mesh((name,tuple(pts),lo,hi),v,f,mat),(0,0,0),col)


def beam(name,a,b,col,mat,width=.12,depth=.18):
    """Closed real I-section; independently selectable from plates and sheets."""
    direction=Vector(b)-Vector(a);h=direction.length;t=.008;web=.006
    p=[(-width/2,-depth/2),(width/2,-depth/2),(width/2,-depth/2+t),(web/2,-depth/2+t),
       (web/2,depth/2-t),(width/2,depth/2-t),(width/2,depth/2),(-width/2,depth/2),
       (-width/2,depth/2-t),(-web/2,depth/2-t),(-web/2,-depth/2+t),(-width/2,-depth/2+t)]
    n=len(p);v=[(x,y,z) for z in (-h/2,h/2) for x,y in p]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ob=object_mesh(name,mesh(('I',round(h,6),width,depth),v,f,mat),(Vector(a)+Vector(b))/2,col)
    ob.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    return tag(ob,'cap_steel_support_type')


def connection(name,loc,angle,col,mat):
    # End plate and four hex bolt heads in one reusable, closed component mesh.
    v=[];f=[];append_box(v,f,(0,0,0),(.25,.22,.012))
    for x in (-.078,.078):
        for y in (-.065,.065):
            n=len(v);v.extend((x+.014*math.cos(i*math.tau/6),y+.014*math.sin(i*math.tau/6),z)
                             for z in (.006,.021) for i in range(6))
            f.extend((tuple(n+i for i in range(5,-1,-1)),tuple(n+6+i for i in range(6))))
            f.extend((n+i,n+(i+1)%6,n+(i+1)%6+6,n+i+6) for i in range(6))
    ob=object_mesh(name,mesh('four_bolt_plate',v,f,mat),loc,col,angle)
    return tag(ob,'cap_connection_plate_type')


def curves(tower,col,metal):
    strip=7*IN
    for ob in col.objects:
        if ob.get('module')!='crown_curved_transition':continue
        sign=1 if '_+1' in ob.name else -1
        start=sign*(3.5*IN+strip/2);end=sign*(PITCH-6*IN-strip/2)
        lo,hi=(start,end) if ob.get('transition')=='open' else (end,start)
        ob.data=_curve_ribbon(lo,hi,ob['transition_height_m'],strip,.075,metal)
        ob['ribbon_width_m']=strip;ob['ribbon_depth_m']=.075
        ob['confidence']='Curve heights/pitch sourced;7in breadth fitted to adjacent source7in narrow stem and user correction;75mm depth estimated. Cosmetic aluminum, not a surveyed steel branch.'


def corner_frames(tower,xy,roof,root,metal):
    col=subgroup(root,tower+'_FACADE_corner_transition_frames',NIST+'; '+PHOTO,LIMITS)
    w=.16;t=.006;back=11.5*IN;front=-.065
    profile=[(-w/2,front),(w/2,front),(w/2,back),(w/2-t,back),
             (w/2-t,front+t),(-w/2+t,front+t),(-w/2+t,back),(-w/2,back)]
    corner=bpy.data.collections[tower+'_corner_three_panels']
    levels={PLAZA_Z,roof-2.4}
    for ob in corner.objects:
        levels.update((ob.location.z-ob.dimensions.z/2-.004,ob.location.z+ob.dimensions.z/2+.004))
    raw=sorted(z for z in levels if PLAZA_Z<=z<=roof-2.4)
    levels=[]
    for z in raw:
        if not levels or z-levels[-1]>.001:levels.append(z)
    if levels[1]-levels[0]>4.5:
        levels=sorted(set(levels+[PLAZA_Z+i*3.6576 for i in range(1,8) if PLAZA_Z+i*3.6576<levels[1]]))
    end=outline(OUTER_HALF,OUTER_HALF-REFERENCE_HALF)[1][0]
    for j,(a,b) in enumerate(zip(levels,levels[1:])):
        if b-a<=.01:continue
        h=b-a-.008;n=len(profile)
        verts=[(x,y,z) for z in (0,h) for x,y in profile]
        faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        proto=mesh(('folded_jamb',round(h,7)),verts,faces,metal)
        for side in range(4):
            for sign in (-1,1):
                ob=_face_object(f'{tower}_corner_frame_S{side+1}_{sign:+d}_piece{j:03d}',proto,
                                xy,side,OUTER_HALF,a+.004,col,sign*(end-.035))
                tag(ob,'corner_transition_frame');ob['projection_m']=.065
    col.asset_mark();col.asset_data.description=LIMITS;col.instance_offset=(*xy,0)
    return col


def cap(tower,xy,roof,root,metal,steel):
    old=bpy.data.collections[tower+'_CROWN_photo_interpretation']
    remove=[o for o in old.objects if o.get('module')=='sloping_cap_panel' or
            (o.name.startswith(tower+'_crown_edge') and any(v in o.name for v in ('drip','inner_coping')))]
    bpy.data.batch_remove(ids=remove)
    col=subgroup(root,tower+'_CROWN_CAP_mitered_panels',PHOTO,LIMITS)
    support=subgroup(root,tower+'_CROWN_CAP_steel_support_TYPE',PHOTO+'; NIST1-2A§3.2.7',LIMITS)
    offset=OUTER_HALF-REFERENCE_HALF
    outer=[Vector((x+xy[0],y+xy[1])) for x,y in outline(OUTER_HALF,offset)]
    inner=[Vector((x+xy[0],y+xy[1])) for x,y in outline(OUTER_HALF-1.8,offset-1.8)]
    inside=[Vector((x+xy[0],y+xy[1])) for x,y in outline(OUTER_HALF-1.98,offset-1.98)]
    lip_inside=[Vector((x+xy[0],y+xy[1])) for x,y in outline(OUTER_HALF-.012,offset-.012)]
    for edge in range(8):
        a,b=outer[edge],outer[(edge+1)%8];u,w=inner[edge],inner[(edge+1)%8]
        count=3 if edge%2 else max(1,round((b-a).length/PITCH))
        for j in range(count):
            gap=.003/(b-a).length;t0=j/count+gap;t1=(j+1)/count-gap
            A=a.lerp(b,t0);B=a.lerp(b,t1);U=u.lerp(w,t0);W=u.lerp(w,t1)
            face=[Vector((p.x,p.y,z)) for p,z in ((A,roof-2.4),(B,roof-2.4),(W,roof+.60),(U,roof+.60))]
            normal=(face[1]-face[0]).cross(face[3]-face[0]).normalized()
            v=[tuple(p) for p in face]+[tuple(p-normal*.006) for p in face]
            f=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
            ob=object_mesh(f'{tower}_crown_cap_edge{edge}_panel{j:02d}_MITER_STUDY',mesh(('sheet',tower,edge,j),v,f,metal),(0,0,0),col)
            tag(ob,'sloping_cap_panel');ob['edge']=edge;ob['sheet_thickness_m']=.006
        pts=[tuple(inner[edge]),tuple(inner[(edge+1)%8]),tuple(inside[(edge+1)%8]),tuple(inside[edge])]
        tag(prism(f'{tower}_cap_inner_coping_edge{edge}_MITER',pts,roof+.586,roof+.612,col,metal),'cap_mitered_coping')
        pts=[tuple(outer[edge]),tuple(outer[(edge+1)%8]),tuple(lip_inside[(edge+1)%8]),tuple(lip_inside[edge])]
        tag(prism(f'{tower}_cap_outer_drip_edge{edge}_MITER',pts,roof-2.50,roof-2.40,col,metal),'cap_mitered_drip')
        # Continuous lower header and inward rakers; corner members follow45deg.
        d0=(u-a).normalized();d1=(w-b).normalized()
        lowa=a+d0*.13;lowb=b+d1*.13
        beam(f'{tower}_cap_header_E{edge}',(*lowa,roof-2.55),(*lowb,roof-2.55),support,steel,.18,.22)
        for j in range(count+1):
            t=j/count;out=a.lerp(b,t);inn=u.lerp(w,t);delta=(inn-out).normalized()
            start=out+delta*.13
            beam(f'{tower}_cap_raker_E{edge}_{j:02d}',(*start,roof-2.54),(*inn,roof+.50),support,steel)
            if j%3==0 or edge%2:
                connection(f'{tower}_cap_anchor_E{edge}_{j:02d}',(*inn,roof+.457),math.atan2((b-a).y,(b-a).x),support,steel)
                # Short vertical knee, folded gusset type and cross-bay brace.
                knee=out+delta*.26
                beam(f'{tower}_cap_knee_E{edge}_{j:02d}',(*knee,roof-2.55),(*knee,roof-2.08),support,steel,.09,.14)
                if j<count:
                    next_in=u.lerp(w,(j+1)/count)
                    beam(f'{tower}_cap_diagonal_E{edge}_{j:02d}',(*start,roof-2.54),(*next_in,roof+.50),support,steel,.08,.12)
    for c in (col,support):
        c.asset_mark();c.asset_data.description=LIMITS;c.instance_offset=(*xy,0)
    return col,support


def apply():
    if bpy.context.scene.get('crown_junction_revision')==VERSION:
        # Earlier saved input could contain submillimetre duplicated datums
        # from float32 bounds. Clean only degenerate short jamb pieces.
        tiny=[]
        for tower in ('WTC1','WTC2'):
            col=bpy.data.collections.get(tower+'_FACADE_corner_transition_frames')
            if col:tiny.extend(o for o in col.objects if o.dimensions.z<.01)
        if tiny:bpy.data.batch_remove(ids=tiny)
        return
    metal=bpy.data.materials['silver_cladding_color_study'];steel=bpy.data.materials['structural_steel_unclad_STUDY']
    for tower,xy,roof in (('WTC1',(-55,55),1368*FT),('WTC2',(55,-55),1362*FT)):
        root=bpy.data.collections[tower+'_FACADE_REVISION']
        curves(tower,bpy.data.collections[tower+'_crown_curved_cladding'],metal)
        corner_frames(tower,xy,roof,root,metal)
        cap(tower,xy,roof,bpy.data.collections[tower],metal,steel)
    bpy.context.scene['crown_junction_revision']=VERSION
