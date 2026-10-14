"""Cut individual pavers to the fountain and planter boundaries; no photo textures."""
import math
import bpy
from .planar import area, subtract_convex, regular_polygon, extrude_union
from .completion import PLAZA_Z
from .facade_detail import object_mesh
from .crown_site_detail import annulus, PLAZA_PHOTO

VERSION='2026-10-14-conforming-pavers-v1'
RADIUS=18.05
GAP=.018


def apply():
    scene=bpy.context.scene
    if scene.get('paving_boundary_revision')==VERSION:return
    col=bpy.data.collections['PLAZA_individual_tile_meshes_STUDY']
    mat=bpy.data.materials['plaza_pale_stone_variation_TYPE']
    prototypes=[o for o in col.objects if o.name.startswith('plaza_tile_') and o.get('mesh_unique')]
    prototype=prototypes[0].data.copy()
    obsolete=[o for o in col.objects if o.get('mesh_unique') and
              ('radial' in o.name or math.hypot(o.location.x,o.location.y)<25)]
    bpy.data.batch_remove(ids=obsolete)
    planters=[]
    for j in range(8):
        for k in range(3):
            a=j*math.tau/8+.39+(k-1)*.12;r=19.8+(1 if k==1 else 0)
            planters.append((r*math.cos(a),r*math.sin(a),.66+GAP/2,24))
    cutters=[(0,0,RADIUS+GAP/2,192)]+planters
    cuts=[(x,y,r,regular_polygon(x,y,r,n)) for x,y,r,n in cutters]
    count=0;cut_count=0
    for i in range(120):
        x=(i-59.5)*1.5
        for j in range(100):
            y=(j-49.5)*1.5
            if math.hypot(x,y)>=25:continue
            half=(1.5-GAP)/2
            square=[(x-half,y-half),(x+half,y-half),(x+half,y+half),(x-half,y+half)]
            parts=[square];modified=False
            for cx,cy,r,cutter in cuts:
                dx=max(abs(cx-x)-half,0);dy=max(abs(cy-y)-half,0)
                if math.hypot(dx,dy)>r:continue
                modified=True
                next_parts=[]
                for p in parts:next_parts.extend(subtract_convex(p,cutter))
                parts=next_parts
                if not parts:break
            if not parts:continue
            name=f'plaza_tile_{i:03d}_{j:03d}'
            if not modified:
                ob=object_mesh(name,prototype.copy(),(x,y,PLAZA_Z+.015),col)
            else:
                verts,faces=extrude_union(parts,PLAZA_Z,PLAZA_Z+.03)
                mesh=bpy.data.meshes.new(name+'_boundary_cut_mesh');mesh.from_pydata(verts,[],faces)
                mesh.materials.append(mat);ob=object_mesh(name,mesh,(0,0,0),col)
                ob['clipped_boundary']=True;ob['tile_grid_xy']=(x,y)
                ob['plan_area_m2']=sum(area(p) for p in parts);cut_count+=1
            ob['mesh_unique']=True;ob['module']='plaza_paver';count+=1
    bpy.data.meshes.remove(prototype)
    width=(RADIUS-12.60)/5
    for ring in range(5):
        r0=12.60+ring*width+GAP/2;r1=12.60+(ring+1)*width-GAP/2
        for j in range(96):
            # Shared radial boundary and consistent physical joint width.
            da=GAP/(2*((r0+r1)/2))
            ob=annulus(f'plaza_radial_paver_{ring}_{j:02d}_STUDY',r0,r1,PLAZA_Z,PLAZA_Z+.03,col,mat,
                       a0=j*math.tau/96+da,a1=(j+1)*math.tau/96-da,n=2)
            ob['mesh_unique']=True;ob['module']='plaza_radial_paver'
    # Replace coarse 64-gon support edge with the paving boundary; same elevation.
    support=bpy.data.objects['fountain_podium_support_STUDY']
    pts=regular_polygon(0,0,RADIUS,192)
    verts,faces=extrude_union([pts],0,PLAZA_Z)
    mesh=bpy.data.meshes.new('fountain_support_conforming_mesh');mesh.from_pydata(verts,[],faces)
    mesh.materials.append(mat);support.data=mesh;support.location=(0,0,0)
    col['actual_tile_mesh_count']=sum(bool(o.get('mesh_unique')) for o in col.objects)
    col['source']=PLAZA_PHOTO
    col['confidence']='Photographic radial paving interpretation. Grid1.5m/radius18.05m are CG estimates. Tiles clipped at fountain/24 planter contours;18mm joints, not an original shop drawing.'
    col['boundary_cut_tile_count']=cut_count
    col['status']='Every paver separate unique mesh; continuous finished z datum; no center-based deletion at curved edges.'
    scene['paving_boundary_revision']=VERSION
    print(f'PAVING_REVISION replacement_grid={count} clipped={cut_count}',flush=True)
