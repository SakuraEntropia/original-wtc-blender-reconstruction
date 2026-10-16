"""Core rolled-beam headers respect actual fitted shaft openings."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from .mesh_batch import Batch,i_section
from .shell_floor_revision import SOURCE,LIMIT,H,K,Q
from .facade_detail import outline
from .lobby_plan_revision import slab_mesh
from .planar import clip

VERSION='2026-10-16-core-headers-perimeter-closures-v1'


def apply():
    bpy.context.view_layer.update()
    for tower in ('WTC1','WTC2'):
        owner=bpy.data.collections[tower+'_OWNER_public_halls_and_bare_core']
        floors={o['floor']:o for o in owner.objects if o.get('module')=='owner_core_floor'}
        for ob in owner.objects:
            if ob.get('module')=='owner_core_beams':ob.matrix_world=floors[ob['floor']].matrix_world.copy()
    hall=bpy.data.collections['OWNER_LOCAL6_elevator_hall_TEMPLATE']
    if not any(o.type=='LIGHT' for o in hall.objects):
        from .interior_parts import Parts
        p=Parts('OWNER_HALL',hall)
        for y in (-3.2,3.2):p.area('ambient_'+str(y),(0,y,2.78),90,1.1,(1,.84,.66))
    if bpy.context.scene.get('core_framing_revision')==VERSION:return
    mat=bpy.data.materials['SHELL_steel_fireproof_surface'];cache={}
    for tower in ('WTC1','WTC2'):
        c=bpy.data.collections[tower+'_OWNER_public_halls_and_bare_core']
        for floor in list(c.objects):
            if floor.get('module')!='owner_core_floor':continue
            mesh=floor.data
            if mesh.name not in cache:
                batch=Batch(mesh.name+'_rolled_beams',mat)
                # Every vertical slab side yields a perimeter or shaft header.
                for face in mesh.polygons:
                    pts=[mesh.vertices[i].co for i in face.vertices]
                    xy=sorted({(round(p.x,6),round(p.y,6)) for p in pts})
                    if len(xy)==2 and max(p.z for p in pts)-min(p.z for p in pts)>.05:
                        batch.bar((*xy[0],-.34),(*xy[1],-.34),i_section(.42,.17,.010,.017))
                bvh=BVHTree.FromPolygons([v.co for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons])
                xs=sorted({round(v.co.x,6) for v in mesh.vertices})
                for y in (-10.5,-6.2,-4.65,-1.55,1.55,4.65,6.2,10.5):
                    for a,b in zip(xs,xs[1:]):
                        if b-a<.05:continue
                        if all(bvh.ray_cast(Vector(((a+b)/2,y+d,1)),Vector((0,0,-1)),2)[0] is not None for d in (-.10,0,.10)):
                            batch.bar((a,y,-.34),(b,y,-.34),i_section(.42,.17,.010,.017))
                tmp=bpy.data.collections.new('CORE_beams_temporary');ob=batch.mesh(tmp,'owner_core_beams');cache[mesh.name]=ob.data;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.collections.remove(tmp)
            ob=bpy.data.objects.new(floor.name+'_steel_headers',cache[mesh.name]);c.objects.link(ob);ob.matrix_world=floor.matrix_world.copy()
            for key in ('floor','site_registered','site_world_annotations_synced'):
                if key in floor:ob[key]=floor[key]
            ob['module']='owner_core_beams';ob['source']=SOURCE;ob['confidence']=LIMIT
    # Narrow perimeter closing sheets stop at the chamfered plan boundary.
    c=bpy.data.collections['SHELL_edge_and_core_collector_TEMPLATE']
    for side in (-1,1):
        x0,x1=((-Q+.15,-Q+2.2) if side<0 else (Q-2.2,Q-.15))
        for sy in (-1,1):
            y0,y1=((-Q+.15,-K) if sy<0 else (K,Q-.15));poly=outline(Q-.15)
            rect=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
            for a,b in zip(rect,rect[1:]+rect[:1]):poly=clip(poly,a,b)
            if not poly:continue
            mesh=slab_mesh(f'SHELL_corner_closure_{side}_{sy}',poly,[],.001,mat)
            ob=bpy.data.objects.new(mesh.name,mesh);c.objects.link(ob);ob.location.z=-.14
            ob['module']='shell_perimeter_closing_sheet';ob['source']=SOURCE;ob['confidence']='Fitted perimeter closure strip, cut to chamfer; sheet rib/fastener schedule unverified'
    bpy.context.scene['core_framing_revision']=VERSION
    from .mesh_batch import orient_framing_solids
    orient_framing_solids()
