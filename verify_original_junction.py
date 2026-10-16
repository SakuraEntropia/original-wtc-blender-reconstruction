"""Read-only geometry gates for the original drawing based crown junction.

Import inspect(check) from the saved-scene verifier. Dimensions below are
independent source readings; mesh coordinates must corroborate object tags.
"""
import math

import bpy
from mathutils import Vector

FT = .3048
PITCH = 40 * .0254
WIDTH = .127
PROJECTION = .1778
SS_THICKNESS = .0015
PANEL_WIDTHS = (.587375, 1.016, .587375)
PANEL_JOINT = .006
EDGES = (1, 3, 5, 7)
TOWERS = {'WTC1': (-55., 55.), 'WTC2': (55., -55.)}
FRAME_MODULES = {'original_edge_al_return', 'original_edge_ss_face',
                 'original_edge_track'}
ROOF_MODULES = {'original_corner_roof_triangle', 'original_roof_field_panel',
                'original_roof_raked_joint'}


def _number(ob, key):
    try:
        return float(ob.get(key))
    except (TypeError, ValueError):
        return math.nan


def _vector(ob, key):
    try:
        value = ob.get(key)
        if len(value) != 3 or not all(math.isfinite(float(x)) for x in value):
            return None
        return Vector(value)
    except (TypeError, ValueError):
        return None


def _close(a, b, tolerance=.001):
    return math.isfinite(a) and abs(a-b) <= tolerance


def _objects(collection_name, modules):
    collection = bpy.data.collections.get(collection_name)
    objects = list(collection.all_objects) if collection else []
    return collection, [ob for ob in objects if ob.get('module') in modules]


def _points(ob):
    return [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]


def _range(points, direction):
    values = [point.dot(direction) for point in points]
    return min(values), max(values)


def _bounds(points):
    return {'min_m': [min(p[i] for p in points) for i in range(3)],
            'max_m': [max(p[i] for p in points) for i in range(3)]}


def _tangent(edge):
    return Vector({1: (1, 1, 0), 3: (-1, 1, 0),
                   5: (-1, -1, 0), 7: (1, -1, 0)}[edge]).normalized()


def _sample_frames(tower, objects, points, check):
    groups = {}
    for ob in objects:
        key = (ob.get('face'), ob.get('axis_index'), ob.get('piece_index'))
        groups.setdefault(key, []).append(ob)
    bad_pairs = []
    for key, group in groups.items():
        valid_key = key[0] in range(1, 5) and key[1] in (0, 58) and key[2] is not None
        halves = [{ob.get('frame_half') for ob in group if ob.get('module') == module}
                  for module in ('original_edge_al_return', 'original_edge_ss_face')]
        has_track = any(ob.get('module') == 'original_edge_track' for ob in group)
        if not valid_key or halves != [{-1, 1}, {-1, 1}] or not has_track:
            bad_pairs.append(key)
    coverage = {(key[0], key[1]) for key in groups}
    expected = {(face, axis) for face in range(1, 5) for axis in (0, 58)}
    check(tower+'_original_frame_pairs_and_tracks',
          bool(groups) and not bad_pairs and coverage == expected,
          {'groups': len(groups), 'bad_groups': bad_pairs[:12],
           'face_axis_coverage': sorted(coverage, key=str)})
    check(tower+'_original_frame_dimension_tags', bool(objects) and all(
        _close(_number(ob, 'frame_width_m'), WIDTH, 1e-6) and
        _close(_number(ob, 'projection_m'), PROJECTION, 1e-6) for ob in objects),
        {'width_m': WIDTH, 'projection_m': PROJECTION})

    samples = []
    for face, axis in sorted(expected):
        candidates = [(key, group) for key, group in groups.items()
                      if key[:2] == (face, axis) and all(ob.name in points for ob in group)]
        if not candidates:
            continue
        key, group = min(candidates, key=lambda item: str(item[0][2]))
        angle = (face-1)*math.pi/2
        tangent = Vector((math.cos(angle), math.sin(angle), 0))
        outward = Vector((math.sin(angle), -math.cos(angle), 0))
        combined = [point for ob in group for point in points[ob.name]]
        u0, u1 = _range(combined, tangent)
        q0, q1 = _range(combined, outward)
        origin = Vector((*TOWERS[tower], 0))
        axis_u = origin.dot(tangent)+(axis-29)*PITCH
        valid = (_close(u1-u0, WIDTH) and
                 _close(q1-q0, PROJECTION+SS_THICKNESS) and
                 _close((u0+u1)/2, axis_u))
        samples.append({'face': face, 'axis': axis, 'piece': key[2],
                        'width_m': u1-u0, 'depth_m': q1-q0,
                        'axis_error_m': (u0+u1)/2-axis_u,
                        'bounds': _bounds(combined), 'passed': valid})
    check(tower+'_original_frame_actual_width_projection_and_axis',
          len(samples) == 8 and all(sample['passed'] for sample in samples), samples)


def _corner_panels(tower, objects, points, check):
    groups = {}
    bad = []
    for ob in objects:
        edge, index = ob.get('edge'), ob.get('panel_index')
        groups.setdefault((edge, ob.get('story_index')), []).append(ob)
        if edge not in EDGES or index not in (1, 2, 3) or ob.name not in points:
            bad.append(ob.name)
            continue
        nominal = PANEL_WIDTHS[index-1]
        low, high = _range(points[ob.name], _tangent(edge))
        if not (_close(_number(ob, 'nominal_width_m'), nominal, 1e-6) and
                _close(high-low, nominal-PANEL_JOINT)):
            bad.append(ob.name)
    bad_groups = []
    for key, group in groups.items():
        if (key[0] not in EDGES or key[1] is None or len(group) != 3 or
                {ob.get('panel_index') for ob in group} != {1, 2, 3} or
                any(ob.name not in points for ob in group)):
            bad_groups.append(key)
            continue
        ranges = sorted(_range(points[ob.name], _tangent(key[0])) for ob in group)
        gaps = [ranges[i+1][0]-ranges[i][1] for i in (0, 1)]
        if not (_close(ranges[-1][1]-ranges[0][0], sum(PANEL_WIDTHS)-PANEL_JOINT)
                and all(_close(gap, PANEL_JOINT) for gap in gaps)):
            bad_groups.append(key)
    check(tower+'_original_corner_panels_actual_unequal_widths',
          bool(objects) and not bad, {'nominal_m': PANEL_WIDTHS,
                                     'joint_m': PANEL_JOINT, 'bad': bad[:12]})
    check(tower+'_original_corner_three_panels_and_seams',
          bool(groups) and {key[0] for key in groups} == set(EDGES) and not bad_groups,
          {'story_groups': len(groups), 'bad_groups': bad_groups[:12]})


def _roof(tower, objects, points, check):
    triangles = [ob for ob in objects if ob.get('module') == 'original_corner_roof_triangle']
    fields = [ob for ob in objects if ob.get('module') == 'original_roof_field_panel']
    joints = [ob for ob in objects if ob.get('module') == 'original_roof_raked_joint']
    groups = {}
    bad_shape, bad_datums = [], []
    anchors = {}
    for ob in triangles:
        edge, index = ob.get('edge'), ob.get('panel_index')
        groups.setdefault(edge, []).append(ob)
        a, b, apex = (_vector(ob, key) for key in ('low_a_world', 'low_b_world', 'apex_world'))
        valid = (edge in EDGES and index in (1, 2, 3) and a is not None and
                 b is not None and apex is not None and ob.name in points)
        if valid:
            nominal = PANEL_WIDTHS[index-1]
            actual = points[ob.name]
            valid = (_close(_number(ob, 'lower_width_m'), nominal, 1e-6) and
                     _close((b-a).length, nominal) and
                     (b-a).cross(apex-a).length > 1e-6 and
                     all(min((point-anchor).length for point in actual) < .001
                         for anchor in (a, b, apex)))
            if valid:
                anchors[ob.name] = (a, b, apex)
        if not valid:
            bad_shape.append(ob.name)
        finished = _number(ob, 'finished110_z')
        parapet = _number(ob, 'parapet_z')
        top = _number(ob, 'paneltop_z')
        valid_datums = (_close(parapet-finished, 6*FT) and
                        _close(top-parapet, 9*FT) and
                        bool(ob.get('datum_mapping_estimated')) and
                        bool(ob.get('source_geometry_inference')) and
                        a is not None and b is not None and apex is not None and
                        _close(a.z, parapet) and _close(b.z, parapet) and _close(apex.z, top))
        if not valid_datums:
            bad_datums.append(ob.name)
    check(tower+'_original_roof_triangles_mesh_matches_source_anchors',
          bool(triangles) and not bad_shape,
          {'triangles': len(triangles), 'bad': bad_shape[:12]})
    check(tower+'_original_roof_6ft_parapet_9ft_rise_estimated_mapping',
          bool(triangles) and not bad_datums,
          {'parapet_rise_m': 6*FT, 'roof_rise_m': 9*FT, 'bad': bad_datums[:12]})

    shared = {}
    bad_shared = []
    for edge, group in groups.items():
        if (edge not in EDGES or len(group) != 3 or
                {ob.get('panel_index') for ob in group} != {1, 2, 3} or
                any(ob.name not in anchors for ob in group)):
            bad_shared.append(edge)
            continue
        ordered = sorted(group, key=lambda ob: ob['panel_index'])
        values = [anchors[ob.name] for ob in ordered]
        apex = values[0][2]
        if (any((value[2]-apex).length > .001 for value in values) or
                any((values[i][1]-values[i+1][0]).length > .001 for i in (0, 1))):
            bad_shared.append(edge)
            continue
        # The two main miters meet the adjacent flat roof fields. They run
        # from the outer corners of the complete triangle, not its panel seams.
        shared[edge] = (apex, [values[0][0], values[-1][1]])
    check(tower+'_original_roof_corner_three_shared_apex_triangles',
          set(shared) == set(EDGES) and not bad_shared,
          {'corner_edges': sorted(shared), 'bad_edges': bad_shared})

    joint_groups = {}
    bad_joints = []
    actual_joint_anchors = {}
    for ob in joints:
        edge = ob.get('edge')
        joint_groups.setdefault(edge, []).append(ob)
        a, b = _vector(ob, 'a_world'), _vector(ob, 'b_world')
        if (edge not in shared or a is None or b is None or
                ob.name not in points or (b-a).length < .01):
            bad_joints.append(ob.name)
            continue
        apex, seams = shared[edge]
        low, high = (a, b) if a.z < b.z else (b, a)
        direction, length = (b-a).normalized(), (b-a).length
        along = [(point-a).dot(direction) for point in points[ob.name]]
        cross = [((point-a)-direction*(point-a).dot(direction)).length
                 for point in points[ob.name]]
        if (min(abs(value) for value in along) > .03 or
                abs(max(along)-length) > .03 or min(along) < -.03 or
                max(along) > length+.03 or max(cross) > .04 or
                (high-apex).length > .001 or
                min((low-seam).length for seam in seams) > .001):
            bad_joints.append(ob.name)
        else:
            actual_joint_anchors.setdefault(edge, []).append(low)
    valid_joints = set(joint_groups) == set(EDGES) and not bad_joints
    for edge, group in joint_groups.items():
        lows = actual_joint_anchors.get(edge, [])
        if len(group) != 2 or len(lows) != 2 or (lows[0]-lows[1]).length < .01:
            valid_joints = False
    check(tower+'_original_roof_two_actual_raked_seams_per_corner', valid_joints,
          {'joints_per_edge': {str(edge): len(group) for edge, group in joint_groups.items()},
           'bad': bad_joints[:12]})
    folded=[]
    for ob in joints:
        vertices=points.get(ob.name,[])
        if len(vertices)!=16:
            folded.append(ob.name);continue
        n0=(vertices[1]-vertices[0]).cross(vertices[3]-vertices[0]).normalized()
        n1=(vertices[9]-vertices[8]).cross(vertices[11]-vertices[8]).normalized()
        # A flat cover overlaps one of the two roof planes at a dihedral seam.
        if abs(n0.dot(n1))>.98:folded.append(ob.name)
    check(tower+'_raked_seam_has_two_actual_folded_planes',len(joints)==8 and not folded,
          {'joints':len(joints),'failed':folded})
    bad_fields = []
    for ob in fields:
        if ob.name not in points:
            bad_fields.append(ob.name)
            continue
        z0, z1 = _range(points[ob.name], Vector((0, 0, 1)))
        if not (_close(z0, _number(ob, 'parapet_z'), .004) and
                _close(z1, _number(ob, 'paneltop_z'), .004) and
                z1-z0 > 1 and bool(ob.get('datum_mapping_estimated'))):
            bad_fields.append(ob.name)
    check(tower+'_original_roof_field_panels_actual_datum_span',
          bool(fields) and {ob.get('edge') for ob in fields} == {0, 2, 4, 6}
          and not bad_fields, {'panels': len(fields), 'bad': bad_fields[:12]})


def inspect(check):
    """Emit check(name, passed, evidence); never mutate or save Blender data."""
    from wtc.site_registration_revision import center
    TOWERS.update({t:center(t) for t in TOWERS})
    for tower in TOWERS:
        collections = []
        frame_col, frames = _objects(tower+'_FACADE_corner_transition_frames', FRAME_MODULES)
        corner_col, panels = _objects(tower+'_corner_three_panels', {'original_corner_panel'})
        roof_col, roofs = _objects(tower+'_CROWN_CAP_mitered_panels', ROOF_MODULES)
        collections.extend((frame_col, corner_col, roof_col))
        check(tower+'_original_junction_collections_visible',
              all(collection is not None and not collection.hide_render for collection in collections),
              [collection.name if collection else None for collection in collections])
        points = {}
        bad_mesh = []
        for ob in frames+panels+roofs:
            if ob.type != 'MESH' or not ob.data.vertices or not ob.data.polygons or ob.hide_render:
                bad_mesh.append(ob.name)
                continue
            actual = _points(ob)
            if not all(math.isfinite(value) for point in actual for value in point):
                bad_mesh.append(ob.name)
                continue
            points[ob.name] = actual
        check(tower+'_original_junction_actual_visible_finite_meshes',
              bool(points) and not bad_mesh, {'meshes': len(points), 'bad': bad_mesh[:12]})
        _sample_frames(tower, frames, points, check)
        _corner_panels(tower, panels, points, check)
        _roof(tower, roofs, points, check)


if __name__ == '__main__':
    import json
    checks = []
    inspect(lambda name, passed, evidence: checks.append(
        {'name': name, 'passed': bool(passed), 'evidence': evidence}))
    print(json.dumps({'passed': all(item['passed'] for item in checks),
                      'checks': checks}, ensure_ascii=False))
