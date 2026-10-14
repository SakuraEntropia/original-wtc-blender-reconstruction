"""NIST/photo facade correction; call apply() after crown_site_detail.upgrade().

Cladding is cosmetic and never substitutes for structural steel. Sourced sizes
are kept in metres without rescaling; absolute story/crown datums remain study
estimates. See docs/FACADE_REVISION_EVIDENCE.md for the evidence boundary.
"""
import math
import bpy

from .facade_detail import (FT, TREE_TOP, REFERENCE_HALF, OUTER_HALF,
                            append_box, material, outline, object_mesh)

VERSION = '2026-10-14-nist-facade-v1'
NIST = 'https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-5av1.pdf'
PHOTO = 'https://www.brianrose.com/blog/2015/10/new-yorkthe-walk/'
IN = FT / 12
PITCH = 40 * IN
COVER = 18.75 * IN
OPENING = 21.25 * IN
FRAME = IN
GLASS_Q = OUTER_HALF - 11.5 * IN
FRAME_PROJECTION = .018  # not dimensioned in NIST; visible relief estimate
CROWN_DEPTH = 17.0       # inherited photographic envelope, NOT a source size
CACHE = {}


def _collection(parent, name, source=NIST, confidence=''):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    c['source'] = source
    c['confidence'] = confidence
    c['facade_revision'] = VERSION
    return c


def _tag(ob, module, confidence, **values):
    ob['module'] = module
    ob['source'] = NIST
    ob['confidence'] = confidence
    ob['facade_revision'] = VERSION
    for key, value in values.items():
        ob[key] = value
    return ob


def _mesh(key, verts, faces, mat):
    key = (key, mat.name)
    if key not in CACHE:
        m = bpy.data.meshes.new('FACADE_REV_' + str(len(CACHE)))
        m.from_pydata(verts, [], faces)
        m.materials.append(mat)
        m.update()
        m['facade_revision'] = VERSION
        CACHE[key] = m
    return CACHE[key]


def _box_mesh(size, mat):
    key = ('box', tuple(round(x, 7) for x in size))
    if (key, mat.name) in CACHE:
        return CACHE[(key, mat.name)]
    v, f = [], []
    append_box(v, f, (0, 0, 0), size)
    return _mesh(key, v, f, mat)


def _face_point(xy, side, p, q, z):
    x, y = xy
    return ((x+p, y-q, z), (x+q, y+p, z),
            (x-p, y+q, z), (x-q, y-p, z))[side]


def _face_object(name, mesh, xy, side, q, z, col, p=0):
    return object_mesh(name, mesh, _face_point(xy, side, p, q, z),
                       col, side * math.pi / 2)


def _prism_profile(v, f, profile, depth, offset=0):
    """Closed extrusion of an ordered x/z silhouette, local front = negative Y."""
    n, start = len(profile), len(v)
    v.extend((x, y, z) for y in (offset-depth/2, offset+depth/2)
             for x, z in profile)
    f.extend([tuple(start+i for i in range(n-1, -1, -1)),
              tuple(start+n+i for i in range(n))])
    f.extend((start+i, start+(i+1) % n, start+(i+1) % n+n, start+i+n)
             for i in range(n))


def _cover_row_mesh(height, mat, width=COVER):
    """59 folded shells with the sourced 1.5in washer track / 3/8in mouth."""
    key = ('cover_row', round(height, 7), round(width, 7))
    if (key, mat.name) in CACHE:
        return CACHE[(key, mat.name)]
    v, f = [], []
    # Each cover is a separate closed mesh island; all stories share prototypes.
    track, mouth, recess, gauge = 1.5*IN, .375*IN, .030, .003
    for axis in range(59):
        x = (axis-29)*PITCH
        # Front strips and return walls leave a physical recessed central track.
        for s in (-1, 1):
            w = (width-mouth)/2
            append_box(v, f, (x+s*(mouth/2+w/2), 0, height/2),
                       (w, gauge, height))
            append_box(v, f, (x+s*(width/2-gauge/2), .145, height/2),
                       (gauge, .29, height))
            append_box(v, f, (x+s*(track/2-gauge/2), recess/2, height/2),
                       (gauge, recess, height))
        append_box(v, f, (x, recess, height/2), (track, gauge, height))
    return _mesh(key, v, f, mat)


def _window_row_mesh(height, mat, frames=False, opening=OPENING):
    key = ('frames' if frames else 'glass', round(height, 7), round(opening, 7))
    if (key, mat.name) in CACHE:
        return CACHE[(key, mat.name)]
    v, f = [], []
    for win in range(58):
        x = (win-28.5)*PITCH
        if frames:
            for s in (-1, 1):
                append_box(v, f, (x+s*(opening-FRAME)/2, 0, height/2),
                           (FRAME, FRAME_PROJECTION, height))
                append_box(v, f, (x, 0, (FRAME/2 if s < 0 else height-FRAME/2)),
                           (opening-2*FRAME, FRAME_PROJECTION, FRAME))
        else:
            append_box(v, f, (x, 0, height/2),
                       (opening-2*FRAME, .25*IN, height-2*FRAME))
    return _mesh(key, v, f, mat)


def _spandrel_row_mesh(height, mat, width=OPENING):
    key = ('spandrel_row', round(height, 7), round(width, 7))
    if (key, mat.name) in CACHE:
        return CACHE[(key, mat.name)]
    v, f = [], []
    for win in range(58):
        append_box(v, f, ((win-28.5)*PITCH, 0, height/2),
                   (width-.002, .025, height))
    return _mesh(key, v, f, mat)


def _story_schedule(roof):
    """Exact ordinary/sky pitch, estimated mechanical pitch closes the envelope.

    TREE_TOP is the existing splice datum, not a newly verified floor elevation.
    This explicitly replaces the old uniform interpolation. MER floor heights
    absorb the unresolved absolute-elevation budget; no sourced window/profile
    dimension is scaled.
    """
    top = roof-CROWN_DEPTH
    mer = (top-TREE_TOP-92*12*FT-2*14*FT)/4
    z, rows = TREE_TOP, []
    for level in range(9, 107):
        mechanical = level in (41, 42, 75, 76)
        pitch = mer if mechanical else (14 if level in (44, 78) else 12)*FT
        opening = (8+5/12)*FT if level in (44, 78) else (7+5/12)*FT
        rows.append(dict(level=level, z=z, pitch=pitch,
                         opening=opening, mechanical=mechanical))
        z += pitch
    assert abs(z-top) < 1e-6
    return rows


def _regular_facade(name, xy, roof, root, metal, glass):
    parent = bpy.data.collections[name]
    frame_root = next(c for c in parent.children if c.name.startswith('02_perimeter'))
    for c in frame_root.children:
        if 'separate_grooved_aluminum' in c.name:
            c.hide_render = True
            c.hide_viewport = True
            c['superseded_by'] = VERSION
    shell = next(c for c in parent.children if c.name.startswith('01_envelope'))
    for ob in shell.objects:
        if ob.name == name+'_envelope_208ft10in':
            ob.hide_render = True
            ob.hide_viewport = True
    for c in parent.children:
        if c.name.startswith('06_glazing'):
            c.hide_render = True
            c.hide_viewport = True

    frames = _collection(root, name+'_window_frames', confidence=
        'NIST1-5Av1 p33: 1in frame and11.5in glass recess. Frame projection18mm estimated; absolute levels estimated.')
    covers = _collection(root, name+'_story_column_covers', confidence=
        '18.75in cover,1.5in washer track,3/8in mouth sourced. Gauge/track depth and8mm expansion joint estimated.')
    panes = _collection(root, name+'_recessed_window_rows', confidence=
        'Ordinary7ft5in opening and21.25in width sourced; bronze glass perNIST p33. Absolute story schedule estimated.')
    bands = _collection(root, name+'_spandrel_covers', confidence=
        'Typical4ft7in cover. Depth placement and gauge estimated.')
    special = _collection(root, name+'_sky_lobby_facade', confidence=
        '78:8ft5in opening,5ft7in upper spandrel,14ft story and additional joints, NIST pp35-36. 44 uses this type by explicit extrapolation.')
    mechanical = _collection(root, name+'_mechanical_facade', confidence=
        '75/76:24.5in covers,5in x7in fins,17ft open gap sourced. 41/42 shares type by extrapolation. Absolute levels/band depths estimated.')
    rows = _story_schedule(roof)
    for row in rows:
        level, z, h = row['level'], row['z'], row['opening']
        if row['mechanical']:
            continue
        sky = level in (44, 78)
        rowcol = special if sky else frames
        window_bottom = z+15*IN
        for side in range(4):
            label = f'{name}_F{level:03d}_S{side+1}'
            fr = _face_object(label+'_raised_frame', _window_row_mesh(h, metal, True),
                              xy, side, GLASS_Q+FRAME_PROJECTION/2, window_bottom, rowcol)
            _tag(fr, 'raised_window_frame', '1in face width sourced;18mm projection estimated',
                 floor=level, face=side+1, frame_width_m=FRAME,
                 projection_m=FRAME_PROJECTION, glass_recess_m=11.5*IN, component_count=58)
            gl = _face_object(label+'_glazing', _window_row_mesh(h, glass),
                              xy, side, GLASS_Q-.25*IN/2, window_bottom, special if sky else panes)
            _tag(gl, 'sky_lobby_window' if sky else 'facade_window_row',
                 'Opening source p33/p35; floor44 profile extrapolated from78; absolute elevation estimated',
                 floor=level, face=side+1, opening_height_m=h, opening_width_m=OPENING)
            # Column cover seams coincide with window tops, not floor slabs.
            top = window_bottom+h
            next_top = top+row['pitch']
            if level < 106:
                following = rows[level-8]
                next_top = following['z']+15*IN+following['opening']
            if level in (9, 43, 77):
                start = TREE_TOP if level == 9 else window_bottom
                first = _face_object(label+'_cover_initial', _cover_row_mesh(top-start-.004, metal),
                                     xy, side, OUTER_HALF, start, covers)
                _tag(first, 'aluminum_cover', 'Lower partial story termination estimated', component_count=59)
            end = min(next_top, roof-CROWN_DEPTH)
            cuts = [top, end]
            if level in (43, 44, 77, 78):
                cuts.append(min(end-.01, top+((5+7/12)*FT if sky else (4+7/12)*FT)))
            cuts = sorted(set(a for a in cuts if top <= a <= end))
            for j, (a, b) in enumerate(zip(cuts, cuts[1:])):
                if b-a <= .01:
                    continue
                co = _face_object(label+f'_column_covers{j}', _cover_row_mesh(b-a-.008, metal),
                                  xy, side, OUTER_HALF, a+.004, special if sky else covers)
                _tag(co, 'aluminum_cover', 'One-story cladding joints;8mm seam estimated',
                     floor=level, face=side+1, component_count=59, cover_width_m=COVER)
            sh = (5+7/12)*FT if sky else (4+7/12)*FT
            sp = _face_object(label+'_upper_spandrel', _spandrel_row_mesh(sh, metal),
                              xy, side, GLASS_Q+.038, top, special if sky else bands)
            _tag(sp, 'sky_lobby_spandrel' if sky else 'spandrel_cover',
                 '4ft7in normal/5ft7in sky upper cover sourced; depth placement estimated',
                 floor=level, face=side+1, height_m=sh)
        if sky:
            # Existing hidden floor/fit-out studies use inconsistent ratio datums.
            # Align their datum only; do not invent transfer beams from facade data.
            slab = bpy.data.objects.get(name+f'_F{level}_SKY_LOBBY_STUDY')
            if slab:
                slab.location.z = z
                slab['elevation_confidence'] = 'Facade revision schedule; absolute level estimated'
            slab = bpy.data.objects.get(name+f'_F{level:03d}_SLAB_STUDY')
            if slab:
                slab.location.z = z
            special[f'F{level}_floor_z_estimated_m'] = z
            special[f'F{level}_story_height_m'] = 14*FT
    _mechanical_bands(name, xy, rows, mechanical, metal)
    return rows


def _mechanical_bands(name, xy, rows, col, metal):
    dark = material('FACADE_REV_recessed_service_shadow', (.024, .027, .027), .15, .7)
    for level in (41, 75):
        row, after = rows[level-9], rows[level+2-9]
        a, b = row['z']-3*FT, after['z']+15*IN
        clear = 17*FT
        transition = (b-a-clear)/2
        v, f = [], []
        wide, finw, projection = 24.5*IN, 5*IN, 7*IN
        for axis in range(59):
            p = (axis-29)*PITCH
            _prism_profile(v, f, [(p-COVER/2, 0), (p+COVER/2, 0),
                (p+wide/2, transition), (p+wide/2, transition+clear),
                (p+COVER/2, b-a), (p-COVER/2, b-a),
                (p-wide/2, transition+clear), (p-wide/2, transition)], .032)
            # The 7in fin projection ramps over the lower and upper transitions.
            n = len(v)
            v.extend((p+x, y, z) for x in (-finw/2, finw/2)
                     for y, z in ((-.016, 0), (-projection, transition),
                                  (-projection, transition+clear), (-.016, b-a),
                                  (.001, b-a), (.001, 0)))
            f.extend([tuple(n+i for i in range(5, -1, -1)), tuple(n+6+i for i in range(6))])
            f.extend((n+i, n+(i+1)%6, n+(i+1)%6+6, n+i+6) for i in range(6))
        mesh = _mesh(('mechanical_cover_fins', round(b-a, 7)), v, f, metal)
        for side in range(4):
            ob = _face_object(f'{name}_F{level}_{level+1}_S{side+1}_cover_and_fins', mesh,
                              xy, side, OUTER_HALF+.003, a, col)
            _tag(ob, 'mechanical_cover_fins',
                 'NIST p35 widths/projection/clear span; transition heights and absolute levels estimated;41/42 type extrapolation',
                 floor=level, face=side+1, cover_width_m=wide, fin_width_m=finw,
                 fin_projection_m=projection, clear_height_m=clear)
            back = _face_object(f'{name}_F{level}_{level+1}_S{side+1}_recessed_inner_wall',
                               _box_mesh((58*PITCH+COVER, .05, b-a), dark),
                               xy, side, OUTER_HALF-4*FT, (a+b)/2, col)
            _tag(back, 'mechanical_recess', '4ft setback sourced p39; no unverified intake schedule rendered')


def _corners(name, xy, roof, rows, root, metal):
    old = bpy.data.collections.get(name+'_CORNER_aluminum_photo_interpretation')
    if old:
        old.hide_render = True
        old.hide_viewport = True
        old['superseded_by'] = VERSION
    c = _collection(root, name+'_corner_three_panels', confidence=
        'NIST1-5Av1 p36 Fig4-6 explicitly gives3 corner sections perstory. Equal widths,6mm joints,3mm gauge estimated.')
    # Window-head seams align with the corrected one-story cover rhythm.
    levels = {TREE_TOP, roof-2.4}
    levels.update(r['z']+15*IN+r['opening'] for r in rows if not r['mechanical'])
    for r in rows:
        if r['level'] in (44, 78):
            levels.update((r['z']+15*IN, r['z']+15*IN+r['opening']+(5+7/12)*FT))
    # Keep the corner's story joint through the two-story mechanical opening.
    levels.update(r['z'] for r in rows if r['mechanical'])
    crown_base = roof-CROWN_DEPTH
    transition_start = crown_base+(7+1/12)*FT+(11+7/12)*FT
    lower_end = transition_start+(6+2/12)*FT
    upper_start = roof-2.4-(7+2/12)*FT
    levels.update((crown_base, crown_base+(7+1/12)*FT, transition_start,
                   lower_end, (lower_end+upper_start)/2, upper_start))
    levels = sorted(z for z in levels if TREE_TOP <= z <= roof-2.4)
    # Correct offset of the sourced chamfer reference outline.
    pts = outline(OUTER_HALF, OUTER_HALF-REFERENCE_HALF)
    for edge in (1, 3, 5, 7):
        a, b = pts[edge], pts[(edge+1)%8]
        dx, dy = b[0]-a[0], b[1]-a[1]
        length, angle = math.hypot(dx, dy), math.atan2(dy, dx)
        nx, ny = dy/length, -dx/length
        for story, (z0, z1) in enumerate(zip(levels, levels[1:])):
            for panel in range(3):
                t = (panel+.5)/3
                ob = object_mesh(f'{name}_corner_E{edge}_story{story:03d}_panel{panel+1}',
                    _box_mesh((length/3-.006, .006, z1-z0-.008), metal),
                    (xy[0]+a[0]+dx*t+nx*.004, xy[1]+a[1]+dy*t+ny*.004, (z0+z1)/2), c, angle)
                _tag(ob, 'corner_three_panel', 'Three sections sourced; equal division, gauge and joint widths estimated',
                     edge=edge, story_index=story, panel_index=panel+1, panels_per_story=3)
    return c


def _curve_ribbon(x0, x1, height, width, depth, mat):
    """Cubic smoothstep path: vertical tangency at both ends, no angular rod joints."""
    key = ('cubic_ribbon', round(x0, 7), round(x1, 7), round(height, 7), width, depth)
    if (key, mat.name) in CACHE:
        return CACHE[(key, mat.name)]
    v, f, samples = [], [], 24
    for k in range(samples+1):
        t = k/samples
        x, z = x0+(x1-x0)*(3*t*t-2*t*t*t), height*t
        dx, dz = (x1-x0)*6*t*(1-t), height
        norm = math.hypot(dx, dz)
        nx, nz = dz/norm*width/2, -dx/norm*width/2
        v.extend(((x-nx, -depth/2, z-nz), (x+nx, -depth/2, z+nz),
                  (x+nx, depth/2, z+nz), (x-nx, depth/2, z-nz)))
    f.append((3, 2, 1, 0))
    for k in range(samples):
        a, b = k*4, (k+1)*4
        f.extend((a+j, a+(j+1)%4, b+(j+1)%4, b+j) for j in range(4))
    f.append(tuple(samples*4+i for i in range(4)))
    m = _mesh(key, v, f, mat)
    for poly in m.polygons:
        if len(poly.vertices) == 4 and poly.index not in (0, len(m.polygons)-1):
            poly.use_smooth = True
    return m


def _crown(name, xy, roof, root, metal, glass):
    old = bpy.data.collections.get(name+'_CROWN_photo_interpretation')
    if old:
        # Leave existing separately built sloped cap/coping available.
        for ob in old.objects:
            if '_crown_S' in ob.name or '_crown_glazing_' in ob.name:
                ob.hide_render = True
                ob.hide_viewport = True
                ob['superseded_by'] = VERSION
    c = _collection(root, name+'_crown_curved_cladding', NIST+'; '+PHOTO,
        'NIST pp37-38 Fig4-8 and Rose/Fausty1981: alternating two-bay curved opening/closing motif. Curvature fit/gauge/absolute17m envelope estimated; cosmetic aluminum only.')
    z0, cap = roof-CROWN_DEPTH, roof-2.4
    base107 = (7+1/12)*FT
    window107 = (11+7/12)*FT
    lower = (6+2/12)*FT
    upper = (7+2/12)*FT
    a, b = z0+base107+window107, z0+base107+window107+lower
    d = cap-upper
    assert d > b, 'Crown envelope cannot fit sourced profile heights'
    c['z_base107_estimated_m'] = z0
    c['z_window107_bottom_estimated_m'] = z0+base107
    c['z_transition_lower_estimated_m'] = a
    c['z_transition_middle_estimated_m'] = b
    c['z_transition_upper_estimated_m'] = d
    c['window107_height_m'] = window107
    c['lower_transition_height_m'] = lower
    c['upper_transition_height_m'] = upper
    c['central_open_height_estimated_m'] = d-b
    c['two_bay_repeat_m'] = 2*PITCH
    backing = material('FACADE_REV_crown_inner_service_wall', (.038, .045, .043), .32, .44)
    for side in range(4):
        # NISTp39: MER facade is an open screen in front of the inner service
        # wall. Keep physical closure behind the decorative crown; the107 glass
        # is separately represented below. No invented full-width vent schedule.
        inner = _face_object(f'{name}_crown_S{side+1}_recessed_service_wall',
            _box_mesh((58*PITCH+12*IN, .08, cap-a), backing),
            xy, side, OUTER_HALF-4*FT, (a+cap)/2, c)
        _tag(inner, 'crown_mechanical_backing',
             'NISTp39:inner service wall behind108/109 open facade,4ft setback; exact wall finish/opening schedule unresolved',
             face=side+1, setback_m=4*FT, glass=False)
        for axis in range(59):
            p = (axis-29)*PITCH
            # Ordinary18.75in cover tapers to12in through the107 base spandrel.
            v, f = [], []
            _prism_profile(v, f, [(-COVER/2, 0), (COVER/2, 0),
                (6*IN, base107), (-6*IN, base107)], .08)
            taper = _face_object(f'{name}_crown_S{side+1}_axis{axis:02d}_107_taper',
                _mesh(('crown_107_taper', base107), v, f, metal), xy, side, OUTER_HALF, z0, c, p)
            _tag(taper, 'crown_107_cover', '18.75to12in width and7ft1in height sourced; depth estimated', axis_index=axis)
            stem = _face_object(f'{name}_crown_S{side+1}_axis{axis:02d}_107_stem',
                _box_mesh((12*IN, .08, window107), metal), xy, side, OUTER_HALF, z0+base107+window107/2, c, p)
            _tag(stem, 'crown_107_cover', '12in cover,11ft7in window sourced; depth estimated', axis_index=axis)
            odd = axis % 2 == 1
            widths = [7*IN if odd else 12*IN, 7*IN if odd else 17*IN,
                      7*IN if odd else 17*IN, 12*IN]
            heights = [0, b-a, d-a, cap-a]
            profile = [(w/2, h) for w, h in zip(widths, heights)]
            profile += [(-w/2, h) for w, h in reversed(list(zip(widths, heights)))]
            v, f = [], []
            _prism_profile(v, f, profile, .065)
            mesh = _mesh(('crown_alternating_cover', odd, round(cap-a, 7)), v, f, metal)
            ob = _face_object(f'{name}_crown_S{side+1}_axis{axis:02d}_alternating_cover', mesh,
                              xy, side, OUTER_HALF, a, c, p)
            _tag(ob, 'crown_alternating_cover', '7/17in middle widths,12in termination sourced; cosmetic cladding',
                 axis_index=axis, face=side+1, structural=False, cover_width_m=widths[1])
            if not odd:
                continue
            # Each narrow central stem has a pair of outward S curves to adjacent
            # wider stems, then an inverted pair. This is the observed 中 motif.
            strip = 2.5*IN  # (17in outer finish -12in base cover)/2
            for sign in (-1, 1):
                start = sign*(3.5*IN+strip/2)
                end = sign*(PITCH-6*IN-strip/2)
                for label, lo, hi, h, z in (('open', start, end, lower, a),
                                           ('close', end, start, upper, d)):
                    ob = _face_object(f'{name}_crown_S{side+1}_axis{axis:02d}_{label}_{sign:+d}',
                        _curve_ribbon(lo, hi, h, strip, .045, metal), xy, side, OUTER_HALF+.033, z, c, p)
                    _tag(ob, 'crown_curved_transition',
                         'Curved2-bay motif directly visible Fig4-8; smoothstep curvature and45mm depth estimated; aluminum trim only',
                         axis_index=axis, face=side+1, transition=label, structural=False,
                         transition_height_m=h, curve_samples=24)
        gl = _face_object(f'{name}_crown_S{side+1}_107_glazing',
            _window_row_mesh(window107, glass, opening=28*IN),
            xy, side, GLASS_Q, z0+base107, c)
        _tag(gl, 'crown_107_glazing', 'NISTp37:28in x11ft7in window; glass plane recess carried from typical type')
        fr = _face_object(f'{name}_crown_S{side+1}_107_frames',
            _window_row_mesh(window107, metal, True, opening=28*IN),
            xy, side, GLASS_Q+FRAME_PROJECTION/2, z0+base107, c)
        _tag(fr, 'raised_window_frame', '1in frame type;107frame section extrapolated')
    return c


def apply():
    """Idempotent scene migration, O(number of relevant collection objects)."""
    scene = bpy.context.scene
    names = ('WTC1', 'WTC2')
    if scene.get('facade_evidence_revision') == VERSION and all(
            bpy.data.collections.get(n+'_FACADE_REVISION') for n in names):
        return {'status': 'already_applied', 'version': VERSION}
    for name in names:
        if not bpy.data.collections.get(name):
            raise RuntimeError('Load the completed WTC tower scene before facade_revision.apply()')
    # A partial prior invocation can be removed without querying users_collection.
    def remove_tree(c):
        for child in list(c.children):
            remove_tree(child)
        objects = list(c.objects)
        if objects:
            bpy.data.batch_remove(ids=objects)
        bpy.data.collections.remove(c)
    for name in names:
        old = bpy.data.collections.get(name+'_FACADE_REVISION')
        if old:
            remove_tree(old)
    CACHE.clear()
    metal = bpy.data.materials['silver_cladding_color_study']
    glass = material('FACADE_REV_bronze_glazing', (.095, .105, .095), .28, .22)
    count = 0
    for name, xy, roof in (('WTC1', (-55, 55), 1368*FT),
                           ('WTC2', (55, -55), 1362*FT)):
        root = _collection(bpy.data.collections[name], name+'_FACADE_REVISION', confidence=
            'Dimensions separately sourced; unknown gauges/curvature/absolute datums remain estimates. See FACADE_REVISION_EVIDENCE.md.')
        rows = _regular_facade(name, xy, roof, root, metal, glass)
        _corners(name, xy, roof, rows, root, metal)
        _crown(name, xy, roof, root, metal, glass)
        root.asset_mark()
        root.asset_data.description = 'NIST1-5Av1 facade correction: raised frames,3-panel corners,curved crown,sky-lobby glazing; estimated absolute datums.'
        root.instance_offset = (*xy, 0)
        count += len(root.all_objects)
    scene['facade_evidence_revision'] = VERSION
    scene['facade_revision_source'] = NIST
    scene['facade_revision_object_count'] = count
    return {'status': 'applied', 'version': VERSION, 'objects': count}
