"""Original WTC 7 roof, traced from NIST 1-9 Fig. 2-14 / Figs. 5-8, 5-9.

The plan is a proportional reading, not a fabrication drawing. Heights and
equipment sections are exposed CG estimates; see docs/WTC7_ROOF_EVIDENCE.md.
Call apply() after lowrise_detail / crown_site_detail. No bpy operators are used.
"""
import math
import bpy
from .lowrise_detail import cube, material

FT = 0.3048
SOURCE = 'https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-9.pdf'
ROOT = 'WTC7_ROOF_NIST_plan_interpretation'
VERSION = '2026-10-14.1'
LIMITS = ('Footprints proportionally traced from NIST Fig2-14; heights, sections, '
          'fin spacing, fan blades, pipework and colors are CG estimates, not measured equipment.')
_meshes = {}


def _object(name, mesh, col, location=(0, 0, 0), confidence=LIMITS):
    ob = bpy.data.objects.new('WTC7_' + name, mesh)
    col.objects.link(ob)
    ob.location = location
    ob['source'] = SOURCE
    ob['confidence'] = confidence
    ob['module'] = 'wtc7_rooftop_plant'
    return ob


def _box(name, position, size, col, mat, angle=0):
    ob = cube('WTC7_' + name, size, position, angle, col, mat)
    ob['source'] = SOURCE
    ob['confidence'] = LIMITS
    ob['module'] = 'wtc7_rooftop_plant'
    return ob


def _mesh(key, verts, faces, mat):
    cache_key = (key, mat.name)
    mesh = _meshes.get(cache_key)
    if mesh is None or mesh.name not in bpy.data.meshes:
        mesh = bpy.data.meshes.new('WTC7_roof_prototype_' + str(len(_meshes)))
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(mat)
        mesh.update()
        _meshes[cache_key] = mesh
    return mesh


def _prism(name, ring, lo, hi, col, mat):
    n = len(ring)
    # Top faces point up regardless of the clockwise source-plan trace.
    if sum(ring[i][0]*ring[(i+1)%n][1]-ring[(i+1)%n][0]*ring[i][1]
           for i in range(n)) < 0:
        ring = list(reversed(ring))
    verts = [(x, y, z) for z in (lo, hi) for x, y in ring]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return _object(name, _mesh((name, tuple(ring), lo, hi), verts, faces, mat), col)


def _edge(name, a, b, z, width, height, col, mat):
    return _box(name, ((a[0]+b[0])/2, (a[1]+b[1])/2, z),
                (math.dist(a, b), width, height), col, mat,
                math.atan2(b[1]-a[1], b[0]-a[0]))


def _round(name, position, radius, depth, col, mat, inner=0):
    """Shared closed cylinder or annular shroud; all objects have real-size meshes."""
    n = 40
    radii = (inner, radius) if inner else (radius,)
    verts = [(r*math.cos(i*math.tau/n), r*math.sin(i*math.tau/n), z)
             for z in (-depth/2, depth/2) for r in radii for i in range(n)]
    faces = []
    if inner:
        for i in range(n):
            j = (i+1) % n
            faces += [(i, 2*n+i, 2*n+j, j), (n+i, n+j, 3*n+j, 3*n+i),
                      (i, j, n+j, n+i), (2*n+i, 3*n+i, 3*n+j, 2*n+j)]
    else:
        faces = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
        faces += [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)]
    return _object(name, _mesh(('round', radius, inner, depth), verts, faces, mat), col, position)


def _fan(name, xy, z, radius, col, metal, dark):
    """Photo-interpreted fan silhouette. Blade count/pitch are not historical data."""
    x, y = xy
    _round(name+'_dark_throat_STUDY', (x, y, z-.26), radius, .10, col, dark)
    _round(name+'_fan_shroud_STUDY', (x, y, z), radius, .55, col, metal, radius-.10)
    _round(name+'_fan_hub_TYPE', (x, y, z+.02), radius*.16, .18, col, metal)
    for k in range(8):
        a = k*math.tau/8
        blade = _box(name+f'_blade{k}_TYPE',
                     (x+math.cos(a)*radius*.51, y+math.sin(a)*radius*.51, z),
                     (radius*.67, radius*.18, .045), col, metal, a+.16)
        blade.rotation_euler.x = .16
    for a in (0, math.pi/2):
        _box(name+'_guard_cross_'+str(a)+'_TYPE', (x, y, z+.29),
             (radius*1.91, .06, .06), col, metal, a)


def _louver(name, a, b, z, height, col, metal, dark, pitch=.24):
    """Vertical blades, as explicitly described for the north mechanical intake."""
    length = math.dist(a, b)
    _edge(name+'_recess_STUDY', a, b, z, .08, height, col, dark)
    count = max(2, round(length/pitch))
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    nx, ny = math.sin(angle), -math.cos(angle)
    for i in range(count):
        t = (i+.5)/count
        _box(name+f'_vertical_blade{i:03d}_TYPE',
             (a[0]+(b[0]-a[0])*t+nx*.08, a[1]+(b[1]-a[1])*t+ny*.08, z),
             (.075, .20, height), col, metal, angle)
    for dz in (-height/2, height/2):
        _edge(name+'_frame_'+str(dz)+'_TYPE', a, b, z+dz, .18, .10, col, metal)


def _suppress_legacy():
    old = bpy.data.collections.get('WTC7_ROOF_detail_components')
    if old:
        old.hide_render = True
        old.hide_viewport = True
        old['superseded_by'] = ROOT
    facades = bpy.data.collections.get('WTC7_panelized_facades')
    if facades:
        for ob in facades.objects:
            if ob.name.startswith('WTC7_NORTH_F46_47_COOLING_INTAKE'):
                ob.hide_render = True
                ob.hide_viewport = True


def apply():
    """Create once; a repeated call returns the same completed collection."""
    parent = bpy.data.collections.get('WTC7__NIST_massing_position_schematic')
    shell = bpy.data.objects.get('WTC7_47_story_envelope')
    if parent is None or shell is None:
        return None
    _suppress_legacy()
    old = bpy.data.collections.get(ROOT)
    if old and old.get('revision') == VERSION:
        return old
    if old:
        # Only this module's flat collection is cleared after an interrupted build.
        for ob in list(old.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(ROOT)
    parent.children.link(col)
    col['source'] = SOURCE
    col['source_figures'] = 'Fig2-14 p22; Figs5-8/9 p99; north intake text p101'
    col['confidence'] = LIMITS
    col['verified_inventory'] = '2 enclosed penthouses; 2 parallel screenwalls; 5 north cooling towers'
    col['unresolved'] = 'Model/serial numbers; fabrication dimensions; below-roof tower internals; yard equipment inventory'
    vertices = [shell.matrix_world @ v.co for v in shell.data.vertices]
    roof = max(v.z for v in vertices)
    nw, ne, se, sw = vertices[:4]
    width = math.dist(nw.xy, ne.xy)
    depth = abs(nw.y-sw.y)
    # Coordinates normalized to the bounding box of Fig2-14's trapezoid.
    # These are traced ratios, deliberately not presented as original dimensions.
    def p(u, v):
        return (nw.x+u*width, nw.y-v*depth)
    top = max((poly for poly in shell.data.polygons
               if all(abs(vertices[i].z-roof)<.001 for i in poly.vertices)),
              key=lambda poly: len(poly.vertices))
    roof_ring = [(vertices[i].x, vertices[i].y) for i in top.vertices]
    warm = material('WTC7_roof_weathered_light_membrane_STUDY', (.48,.47,.42), 0, .83)
    red = material('WTC7_penthouse_brown_enclosure_STUDY', (.20,.11,.082), .08, .51)
    metal = material('WTC7_roof_gray_metal_STUDY', (.43,.46,.43), .65, .38)
    pale = material('WTC7_penthouse_pale_roof_STUDY', (.67,.68,.62), .15, .62)
    dark = material('WTC7_roof_equipment_recess_STUDY', (.035,.048,.043), .12, .65)
    _prism('roof_membrane_plan_STUDY', roof_ring, roof+.025, roof+.06, col, warm)
    for i, a in enumerate(roof_ring):
        b = roof_ring[(i+1) % len(roof_ring)]
        ob = _edge(f'roof_parapet{i}_4ft', a, b, roof+2*FT, .28, 4*FT, col, red)
        ob['confidence'] = 'NIST p99 parapet approximately 4ft; wall thickness and roof datum interpretation estimated'
        _edge(f'roof_parapet{i}_coping_TYPE', a, b, roof+4*FT+.03, .35, .09, col, pale)

    west = [p(.215,.375), p(.378,.375), p(.378,.620), p(.215,.620)]
    east = [p(.665,.049), p(.932,.049), p(.960,.147), p(.914,.674), p(.665,.674)]
    for name, ring, height in (('west', west, 5.4), ('east', east, 7.2)):
        _prism(name+'_penthouse_enclosure_PLAN_STUDY', ring, roof+.06, roof+height, col, red)
        _prism(name+'_penthouse_roof_PLAN_STUDY', ring, roof+height, roof+height+.18, col, pale)
        for i, a in enumerate(ring):
            _edge(name+f'_penthouse_roof_edge{i}_TYPE', a, ring[(i+1)%len(ring)],
                  roof+height+.22, .19, .25, col, metal)
    # The big east penthouse has a chamfered northeast corner, not a cuboid.
    _louver('east_penthouse_south_louver_STUDY', p(.720,.677), p(.870,.677),
            roof+4.1, 2.4, col, metal, dark)
    _louver('west_penthouse_south_louver_STUDY', p(.264,.623), p(.350,.623),
            roof+2.8, 1.7, col, metal, dark)
    # Open yard, bounded only on north and south; never cap this with a roof.
    for v in (.375, .620):
        a, b = p(.378,v), p(.665,v)
        _edge('yard_screenwall_'+str(v)+'_PLAN_STUDY', a, b, roof+2.75, .15, 5.4, col, metal)
        for j in range(34):
            u = .378+(.665-.378)*(j+.5)/34
            _box('yard_screen_rib_'+str(v)+f'_{j}_TYPE', (*p(u,v), roof+2.75),
                 (.065,.24,5.4), col, metal)
        _edge('yard_screen_cap_'+str(v)+'_TYPE', a, b, roof+5.5, .28, .10, col, pale)

    # Five projecting fan outlets. Their cooling tower bodies are below this roof.
    # A dark recess represents the visible opening; the existing shell is not cut.
    a, b = p(.296,.046), p(.639,.330)
    _box('north_cooling_bank_visual_recess_STUDY', ((a[0]+b[0])/2,(a[1]+b[1])/2,roof+.08),
         (b[0]-a[0],a[1]-b[1],.04), col, dark)
    bank_length = b[0]-a[0]
    radius = bank_length/5*.40
    for i in range(5):
        x, y = a[0]+bank_length*(i+.5)/5, (a[1]+b[1])/2
        _fan(f'north_cooling_tower{i+1}', (x,y), roof+.95, radius, col, metal, dark)
        for s in (-1,1):
            _box(f'north_tower{i+1}_grating_beam{s}_TYPE',
                 (x+s*bank_length/10,y,roof+.39),( .12,a[1]-b[1],.22), col, metal)
    for j in range(11):
        y = b[1]+(a[1]-b[1])*j/10
        _box(f'north_cooling_bank_grating{j}_TYPE', ((a[0]+b[0])/2,y,roof+.29),
             (bank_length,.055,.075),col,metal)
    for y in (a[1],b[1]):
        _box('north_bank_perimeter_beam_'+str(y)+'_TYPE',
             ((a[0]+b[0])/2,y,roof+.39),(bank_length,.16,.24),col,metal)

    # Visible yard machinery: three interpreted fan/deck modules, not a schedule.
    for i in range(3):
        x, y = p(.420+i*.091,.495)
        _box(f'yard_plant{i}_louvered_plenum_STUDY',(x,y,roof+2.35),(6.8,7.4,4.0),col,dark)
        _fan(f'yard_plant{i}', (x,y), roof+4.45, 2.55, col, metal, dark)
        for side in (-1,1):
            a, b = (x-3.35,y+side*3.73), (x+3.35,y+side*3.73)
            if side > 0:
                a, b = b, a
            _louver(f'yard_plant{i}_coil{side}_TYPE',a,b,roof+2.4,3.6,col,metal,dark,.37)
        for side in (-1,1):
            _box(f'yard_plant{i}_service_rail{side}_TYPE',(x+side*3.48,y,roof+.25),(.10,8.0,.30),col,metal)
    # A small number of roof vents is visible; shapes/positions below are estimates.
    for name, uv, h in (('west_a',(.252,.456),5.4),('west_b',(.328,.562),5.4),
                        ('east_a',(.724,.192),7.2),('east_b',(.840,.164),7.2),
                        ('east_c',(.842,.513),7.2),('east_d',(.725,.550),7.2)):
        x,y = p(*uv)
        _box(name+'_roof_vent_curb_STUDY',(x,y,roof+h+.38),(.70,.70,.36),col,metal)
        _round(name+'_roof_vent_neck_STUDY',(x,y,roof+h+.82),.22,.64,col,metal)
        _round(name+'_roof_vent_cowl_STUDY',(x,y,roof+h+1.18),.38,.13,col,pale)
    # NIST p101 explicitly describes vertical louvers at Floors46/47.
    window_pitch = 4*FT+7*FT/12
    start = (width-63*window_pitch)/2+17*window_pitch
    a = (nw.x+start,nw.y+.25)
    b = (a[0]+28*window_pitch,a[1])
    _louver('north_F46_47_intake',b,a,roof-14*FT,28*FT-.70,col,metal,dark,.28)
    col['revision'] = VERSION
    col['generated_object_count'] = len(col.objects)
    col['estimated_penthouse_heights_m'] = 'west5.4 / east7.2 / screen5.4'
    col.asset_mark()
    col.asset_data.description = 'Original procedural WTC7 roof; NIST traced arrangement, with explicit geometry estimates.'
    bpy.context.scene['wtc7_roof_revision'] = VERSION
    return col
