"""Exterior visibility, continuous lobby floor and folded trident correction.

Retired inferred atrium geometry remains available as a hidden study. Fold
height and the replacement floor footprint are CG fits, not surveyed sizes.
"""
import math
import re
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from .completion import PLAZA_Z, FORK_START, FORK_CROTCH, FORK_END, TREE_TOP

VERSION = '2026-10-15-exterior-lobby-fold-v1'
RIDGE = .035


def _folded_tree(material):
    outline=[(-.40,PLAZA_Z),(-.40,FORK_START),(-.65,FORK_CROTCH),(-1.2446,FORK_END),
        (-1.2446,TREE_TOP),(-.7874,TREE_TOP),(-.7874,FORK_END),(-.56,FORK_CROTCH+.6),
        (-.25,FORK_CROTCH),(-.2286,FORK_END),(-.2286,TREE_TOP),(.2286,TREE_TOP),
        (.2286,FORK_END),(.25,FORK_CROTCH),(.56,FORK_CROTCH+.6),(.7874,FORK_END),
        (.7874,TREE_TOP),(1.2446,TREE_TOP),(1.2446,FORK_END),
        (.65,FORK_CROTCH),(.40,FORK_START),(.40,PLAZA_Z)]
    outline.reverse()
    paths=[[(0,PLAZA_Z),(0,FORK_START),(0,FORK_CROTCH),(0,FORK_END),(0,TREE_TOP)]]
    paths += [[(0,FORK_START),(s*.45,FORK_CROTCH),(s*.715,FORK_CROTCH+.6),
               (s*1.016,FORK_END),(s*1.016,TREE_TOP)] for s in (-1,1)]
    coords=[Vector(p) for p in outline];edges=[]
    for path in paths:
        start=len(coords);coords.extend(Vector(p) for p in path)
        edges.extend((start+i,start+i+1) for i in range(len(path)-1))
    points,_,faces,_,_,regions=delaunay_2d_cdt(coords,edges,[list(range(len(outline)))],0,1e-7,True)
    faces=[list(f) for f,reg in zip(faces,regions) if reg]
    used=sorted({i for f in faces for i in f});remap={o:n for n,o in enumerate(used)}
    points=[points[i] for i in used];faces=[[remap[i] for i in f] for f in faces]
    segments=[(Vector(a),Vector(b)) for path in paths for a,b in zip(path,path[1:])]
    def crease(p):
        for a,b in segments:
            d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared))
            if (p-a-t*d).length<1e-5:return RIDGE
        return 0
    n=len(points)
    verts=[(p.x,-.25-crease(p),p.y-PLAZA_Z) for p in points]
    verts += [(p.x,.25,p.y-PLAZA_Z) for p in points]
    polys=[tuple(f) for f in faces]+[tuple(n+i for i in f[::-1]) for f in faces]
    counts={};directions={}
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            key=tuple(sorted((a,b)));counts[key]=counts.get(key,0)+1;directions[key]=(a,b)
    for key,count in counts.items():
        if count==1:
            a,b=directions[key];polys.append((b,a,a+n,b+n))
    mesh=bpy.data.meshes.new('TRIDENT_folded_shared_profile')
    mesh.from_pydata(verts,[],polys);mesh.materials.append(material);mesh.update()
    mesh['ridge_height_estimated_m']=RIDGE
    return mesh


def _lobby_floor(tower,xy):
    col=bpy.data.collections.new(tower+'_LOBBY_continuous_plaza_floor_STUDY')
    bpy.data.collections[tower+'_LOBBY_photo_interpretation_STUDY'].children.link(col)
    q=31.38;c=1.45
    outline=[(-q+c,-q),(q-c,-q),(q,-q+c),(q,q-c),(q-c,q),(-q+c,q),(-q,q-c),(-q,-q+c)]
    vertices=[(x,y,z) for z in (-.32,0) for x,y in outline]
    faces=[tuple(range(7,-1,-1)),tuple(range(8,16))]
    faces += [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    mesh=bpy.data.meshes.new(tower+'_continuous_lobby_terrazzo_mesh')
    mesh.from_pydata(vertices,[],faces)
    mesh.materials.append(bpy.data.materials[tower+'_warm_pale_stone_STUDY'])
    ob=bpy.data.objects.new(tower+'_continuous_plaza_lobby_floor_STUDY',mesh)
    col.objects.link(ob);ob.location=(*xy,PLAZA_Z)
    ob['module']='continuous_lobby_floor';ob['source']='NIST NCSTAR 1-1 Fig2-3: Plaza El332; floor footprint CG estimate'
    ob['confidence']='Continuous public floor corrects unsupported hollow ring. Footprint, thickness, terrazzo finish inferred; core shaft openings unverified.'
    col['confidence']=ob['confidence'];col['source']=ob['source']


def apply():
    scene=bpy.context.scene
    if scene.get('oct15_exterior_lobby_revision')==VERSION:return
    # Render-disabled research layers were still drawn in the solid viewport.
    # Match visibility without deleting the independent structural assets.
    for c in bpy.data.collections:
        if c.hide_render:c.hide_viewport=True
    for o in bpy.data.objects:
        if o.hide_render:o.hide_viewport=True
    prototype=None
    for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):
        for ob in bpy.data.objects:
            if not ob.name.startswith(tower+'_'):continue
            if any(s in ob.name for s in ('plaza_lobby_rim','atrium_rail','core_gallery_deck',
                'gallery_downlight','carpet_field','lobby_stair_')) or ob.name==tower+'_F002_SLAB_STUDY':
                ob.hide_render=True;ob.hide_viewport=True;ob['superseded_by']=VERSION
            match=re.fullmatch(tower+r'_tree_s(\d)_(\d+)',ob.name)
            if match:
                if prototype is None:prototype=_folded_tree(ob.data.materials[0])
                ob.data=prototype;ob.rotation_euler=(0,0,int(match[1])*math.pi/2)
                ob.modifiers.clear();ob['folded_front_ridge_m']=RIDGE
                ob['confidence']='NIST splice/pitch retained; folded three-branch surface/35mm ridge CG fit; no round bars'
        _lobby_floor(tower,xy)
    scene['oct15_exterior_lobby_revision']=VERSION
