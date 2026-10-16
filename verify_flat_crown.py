"""Saved-file regression gates for the three reported crown defects."""
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _points(ob):return [ob.matrix_world@v.co for v in ob.data.vertices]


def _bvh(objects):
    vertices=[];faces=[]
    for ob in objects:
        n=len(vertices);vertices.extend(_points(ob))
        faces.extend(tuple(n+i for i in p.vertices) for p in ob.data.polygons)
    return BVHTree.FromPolygons(vertices,faces,all_triangles=False,epsilon=0)


def inspect(check):
    bpy.context.view_layer.update()
    for tower in ('WTC1','WTC2'):
        col=bpy.data.collections[tower+'_crown_curved_cladding'];units=[o for o in col.objects if o.get('module')=='crown_flat_joined_unit']
        bad=[]
        for mesh in {o.data for o in units}:
            bm=bmesh.new();bm.from_mesh(mesh);remaining=set(bm.verts);components=0
            while remaining:
                components+=1;stack=[remaining.pop()]
                while stack:
                    v=stack.pop()
                    for e in v.link_edges:
                        n=e.other_vert(v)
                        if n in remaining:remaining.remove(n);stack.append(n)
            if components!=1 or not all(e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(mesh.name)
            bm.free()
        check(tower+'_crown_arms_and_stems_one_connected_solid',len(units)==116 and not bad,{'units':len(units),'bad_meshes':bad})
        flat=all(not p.use_smooth for o in units for p in o.data.polygons)
        depth=all(abs(max(v.co.y for v in o.data.vertices)-min(v.co.y for v in o.data.vertices)-.0635)<1e-6 for o in units)
        check(tower+'_crown_edge_on_ribbons_unsmoothed_section',bool(units) and flat and depth,{'flat_normals':flat,'normal_depth_m':.0635,'face_ribbon_width_m':.006})
        a=col['z_transition_lower_estimated_m'];top=col['z_fascia_bottom_inferred_m']
        continuous=all(abs(min(p.z for p in _points(o))-a)<.0001 and abs(max(p.z for p in _points(o))-top)<.0001 for o in units)
        check(tower+'_joined_finish_reaches_lower_and_upper_seats',bool(units) and continuous,{'lower_z':a,'upper_z':top})
        legacy=[bpy.data.objects.get(tower+s) for s in ('_top_lower_glass_STUDY','_top_upper_glass_STUDY','_crown_glazing_to_cap_STUDY')]
        check(tower+'_superseded_top_glass_hidden_in_viewport_and_render',all(o and o.hide_render and o.hide_viewport for o in legacy),[o.name for o in legacy if o])
        roof=bpy.data.objects[tower+'_roof_datum'];rz=min(p.z for p in _points(roof))
        backing=[o for o in col.objects if o.get('module')=='crown_mechanical_backing']
        clearance=rz-max(p.z for o in backing for p in _points(o))
        check(tower+'_service_backing_stops_below_maintenance_roof',clearance>.007,{'clearance_m':clearance})
        # Actual triangle overlap, not bounding-box overlap: source107 glass is
        # recessed behind all finish pieces and must not intersect them.
        glass=[o for o in col.objects if o.get('module')=='crown_107_glazing']
        finish=[o for o in col.objects if o.get('module') in ('crown_flat_joined_unit','crown_flat_end_cover','crown_107_cover')]
        overlap=_bvh(glass).overlap(_bvh(finish))
        check(tower+'_active_top_glass_clear_of_cladding_triangles',not overlap,{'intersecting_triangle_pairs':len(overlap)})
