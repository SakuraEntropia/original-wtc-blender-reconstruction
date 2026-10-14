"""Photo-informed, modular lobby fit-out; no as-built fit-out dimensions claimed.

Call apply() after completion.tower_completion(). Existing camera is preserved.
Source and uncertainty register: docs/LOBBY_SPHERE_EVIDENCE.md.
"""
import math
import bpy
from mathutils import Vector
from .completion import FT, PLAZA_Z

REVISION = "2026-10-14-lobby-r1"
PREFIX = "LR_"
PHOTO = "https://www.taipingcarpets.com/projects/twin-towers-at-world-trade-center-ny"
CONFIDENCE = "Photo-informed CG fit-out; all panel, fixture, opening sizes and bay counts estimated"


def _material(name, color, metal=0, rough=.45, emission=0, stone=False):
    name = PREFIX + name
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = rough
    out = nodes.new('ShaderNodeOutputMaterial')
    links.new(shader.outputs['BSDF'], out.inputs['Surface'])
    if emission:
        shader.inputs['Emission Color'].default_value = (*color, 1)
        shader.inputs['Emission Strength'].default_value = emission
    if stone:
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 3.5
        tex.inputs['Detail'].default_value = 3
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .31
        ramp.color_ramp.elements[0].color = (color[0]*.72, color[1]*.73, color[2]*.75, 1)
        ramp.color_ramp.elements[1].position = .65
        ramp.color_ramp.elements[1].color = (*color, 1)
        links.new(tex.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
    mat['confidence'] = 'Procedural color/roughness study; not sampled historic finish'
    return mat


def _collection(name, parent):
    col = bpy.data.collections.new(name)
    parent.children.link(col)
    col['source'] = PHOTO
    col['confidence'] = CONFIDENCE
    return col


def _clear_revision(name):
    old = bpy.data.collections.get(name)
    if not old:
        return
    # Walk collection ownership once; no per-object users_collection scans.
    def remove(col):
        for child in list(col.children):
            remove(child)
        for obj in list(col.objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
        bpy.data.collections.remove(col)
    remove(old)


class Builder:
    """Shared low-polygon prototypes, separately editable modular objects."""
    def __init__(self, name):
        self.name = name
        self.meshes = {}

    def box(self, name, xyz, size, col, material):
        key = material.name
        if key not in self.meshes:
            mesh = bpy.data.meshes.new(self.name + '_' + key + '_unit_box')
            mesh.from_pydata([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),
                              (-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)], [],
                             [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
            mesh.materials.append(material)
            self.meshes[key] = mesh
        obj = bpy.data.objects.new(self.name + '_' + name + '_STUDY', self.meshes[key])
        col.objects.link(obj)
        obj.location, obj.scale = xyz, size
        obj['confidence'] = CONFIDENCE
        return obj

    def disk(self, name, xyz, radius, depth, col, material):
        key = 'disk_' + material.name
        if key not in self.meshes:
            n = 20
            verts = [(math.cos(i*2*math.pi/n), math.sin(i*2*math.pi/n), z)
                     for z in (-.5,.5) for i in range(n)]
            faces = [tuple(range(n-1,-1,-1)), tuple(range(n,2*n))]
            faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
            mesh = bpy.data.meshes.new(self.name + '_' + key)
            mesh.from_pydata(verts, [], faces)
            mesh.materials.append(material)
            self.meshes[key] = mesh
        obj = bpy.data.objects.new(self.name + '_' + name + '_STUDY', self.meshes[key])
        col.objects.link(obj)
        obj.location, obj.scale = xyz, (radius,radius,depth)
        return obj


def _coffers(b, xy, halfcore, ceiling, col, mats):
    x,y = xy
    # Recessed pans, sloping reveals, visible joints: one closed shared mesh.
    pitch = 59/18
    a, inner = (pitch-.045)/2, (pitch-.045)*.36
    verts = [(u,v,z) for edge,z in ((a,-.28),(inner,.24),(a,.38))
             for u,v in ((-edge,-edge),(edge,-edge),(edge,edge),(-edge,edge))]
    faces = [(4,7,6,5),(8,9,10,11)]
    for i in range(4):
        j = (i+1)%4
        faces += [(i,i+4,j+4,j),(i,j,j+8,i+8)]
    mesh = bpy.data.meshes.new(b.name + '_coffer_pan_closed_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mats['ceiling'])
    # Raised backing makes dark narrow seams read without open mesh boundaries.
    b.box('ceiling_shadow_backing',(x,y,ceiling+.48),(59,59,.16),col,mats['joint'])
    for i in range(18):
        dx = -29.5+(i+.5)*pitch
        for j in range(18):
            dy = -29.5+(j+.5)*pitch
            if abs(dx)<halfcore[0]-.25 and abs(dy)<halfcore[1]-.25:
                continue
            obj = bpy.data.objects.new(f'{b.name}_coffer_{i:02d}_{j:02d}_STUDY',mesh)
            col.objects.link(obj)
            obj.location = (x+dx,y+dy,ceiling)
            obj['confidence'] = 'Square recessed ceiling modules inferred from archive photo reflection; pitch and depth estimated'
            if i%3 == 1 and j%3 == 1:
                b.box(f'pendant_stem_{i}_{j}',(x+dx,y+dy,ceiling-.20),(.04,.04,.58),col,mats['metal'])
                b.box(f'pendant_square_case_{i}_{j}',(x+dx,y+dy,ceiling-.67),(.48,.48,.42),col,mats['metal'])
                b.box(f'pendant_diffuser_{i}_{j}',(x+dx,y+dy,ceiling-.89),(.38,.38,.026),col,mats['lamp'])


def _core(b, xy, halfcore, ceiling, col, mats):
    x,y = xy
    top = ceiling-.55
    # Core envelope is sourced; divisions and finish geometry are interpretations.
    for side in range(4):
        along = halfcore[0] if side%2==0 else halfcore[1]
        normal = halfcore[1] if side%2==0 else halfcore[0]
        count = max(6,round(along*2/3.05))
        pitch = along*2/count
        angle = side*math.pi/2
        # side0 south, side1 east, side2 north, side3 west
        def pos(t,d,z):
            return (x+t*math.cos(angle)+d*math.sin(angle),
                    y+t*math.sin(angle)-d*math.cos(angle),z)
        def panel(label,t,z,w,h,material,d=normal,depth=.18):
            ob=b.box(f'core_s{side}_{label}',pos(t,d,z),(w,depth,h),col,material)
            ob.rotation_euler.z=angle
            return ob
        panel('opaque_inner_wall',0,top/2,along*2,top,mats['joint'],normal-.17,.12)
        for k in range(count+1):
            t = -along+k*pitch
            for course in range(6):
                z0 = .24+course*(top-.24)/6
                h = (top-.24)/6-.014
                panel(f'pier_{k}_course_{course}',t,z0+h/2,.64,h,mats['stone'])
        for k in range(count):
            t=-along+(k+.5)*pitch
            w=pitch-.66
            # Concourse and plaza portals are separated by a stone spandrel.
            for level,base in (('concourse',.24),('plaza',PLAZA_Z)):
                h=3.45
                panel(f'{level}_portal_{k}',t,base+h/2,w,h,mats['metal'],normal+.015,.12)
                panel(f'{level}_leafL_{k}',t-w*.245,base+h/2,w*.47,h-.12,mats['door'],normal+.09,.075)
                panel(f'{level}_leafR_{k}',t+w*.245,base+h/2,w*.47,h-.12,mats['door'],normal+.09,.075)
                panel(f'{level}_threshold_{k}',t,base+.035,w,.055,mats['metal'],normal+.15,.42)
                panel(f'{level}_lintel_{k}',t,base+h+.16,w,.25,mats['metal'],normal+.04,.17)
                panel(f'{level}_callplate_{k}',t+w/2+.13,base+1.32,.11,.24,mats['metal'],normal+.115,.03)
                panel(f'{level}_callbutton_{k}',t+w/2+.13,base+1.32,.04,.055,mats['lamp'],normal+.137,.012)
            # Lower spandrel and tall mirror/glazing rhythm visible in archive photos.
            panel(f'lower_spandrel_{k}',t,(3.88+PLAZA_Z)/2,w,PLAZA_Z-3.88,mats['stone'])
            sill=PLAZA_Z+4.15
            panel(f'plaza_spandrel_{k}',t,PLAZA_Z+3.86,w,.55,mats['stone'])
            panel(f'upper_reflective_panel_{k}',t,(sill+top)/2,w-.12,top-sill,mats['reflective'],normal+.045,.06)
            for edge in (-1,1):
                panel(f'window_jamb_{k}_{edge}',t+edge*(w-.09)/2,(sill+top)/2,.055,top-sill,mats['metal'],normal+.10,.10)
            panel(f'window_sill_{k}',t,sill,w,.075,mats['metal'],normal+.10,.14)
        panel('stone_cornice',0,top-.18,along*2,.34,mats['stone'],normal+.025,.28)
        panel('stone_skirt',0,.34,along*2,.19,mats['stone'],normal+.04,.25)


def _soffits_and_floor(b, xy, halfcore, col, mats):
    x,y=xy
    # Narrow core-side galleries connect to the existing plaza rim. The atrium
    # remainder stays open; these gallery footprints are explicitly a study.
    for side in range(4):
        angle=side*math.pi/2
        along=halfcore[0] if side%2==0 else halfcore[1]
        normal=halfcore[1] if side%2==0 else halfcore[0]
        width=max(2.4,18.25-normal)
        dist=normal+width/2
        def position(t,d,z):
            return (x+t*math.cos(angle)+d*math.sin(angle),y+t*math.sin(angle)-d*math.cos(angle),z)
        deck=b.box(f'core_gallery_deck_s{side}',position(0,dist,PLAZA_Z-.16),(along*2,width,.32),col,mats['stone'])
        deck.rotation_euler.z=angle
        for k in range(max(4,round(along*2/2.8))):
            t=-along+(k+.5)*along*2/max(4,round(along*2/2.8))
            b.disk(f'gallery_downlight_trim_s{side}_{k}',position(t,dist,PLAZA_Z-.336),.16,.032,col,mats['metal'])
            b.disk(f'gallery_downlight_lens_s{side}_{k}',position(t,dist,PLAZA_Z-.355),.117,.018,col,mats['lamp'])
        # Independent carpet fields and terrazzo borders use the documented
        # material strategy; placement/size and tower-specific color are inferred.
        fields=max(2,round(along*2/6.1))
        for k in range(fields):
            t=-along+(k+.5)*along*2/fields
            carpet=b.box(f'carpet_field_s{side}_{k}',position(t,dist,PLAZA_Z+.017),(along*2/fields-.16,width-.26,.024),col,mats['carpet'])
            carpet.rotation_euler.z=angle


def _lighting(b, xy, halfcore, ceiling, col):
    x,y=xy
    for side in range(4):
        angle=side*math.pi/2
        normal=halfcore[1] if side%2==0 else halfcore[0]
        dist=(normal+29.5)/2
        data=bpy.data.lights.new(f'{b.name}_lobby_fill_{side}','AREA')
        data.energy=1600
        data.shape='DISK'
        data.size=8
        data.color=(1,.88,.69)
        ob=bpy.data.objects.new(data.name,data)
        col.objects.link(ob)
        ob.location=(x+dist*math.sin(angle),y-dist*math.cos(angle),ceiling-1.6)


def apply():
    """Idempotently replace lobby placeholders with source-labelled modules."""
    roots=[bpy.data.collections.get(n+'_LOBBY_photo_interpretation_STUDY') for n in ('WTC1','WTC2')]
    if all(c and c.get('revision')==REVISION for c in roots):return roots
    created=[]
    mats={
        'stone':_material('pale_core_stone',(.69,.67,.60),rough=.3,stone=True),
        'ceiling':_material('offwhite_coffer',(.76,.75,.69),rough=.73),
        'joint':_material('deep_reveal',(.065,.058,.046),rough=.8),
        'metal':_material('dark_bronze_trim',(.16,.125,.074),metal=.75,rough=.26),
        'door':_material('brushed_bronze_door',(.36,.30,.20),metal=.83,rough=.31),
        'reflective':_material('smoky_core_reflection',(.20,.225,.205),metal=.88,rough=.17),
        'lamp':_material('warm_lens',(.99,.84,.61),rough=.24,emission=3.5),
        'carpet':_material('muted_green_carpet',(.115,.16,.12),rough=.94),
    }
    for name,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):
        parent=bpy.data.collections.get(name+'_COMPLETION_study')
        if not parent:
            raise RuntimeError('Run tower_completion before lobby_revision.apply: '+name)
        rootname=name+'_LOBBY_photo_interpretation_STUDY'
        _clear_revision(rootname)
        root=_collection(rootname,parent)
        root['revision']=REVISION
        root['core_envelope_source']='NIST NCSTAR 1-3A section 2.1, approximately 87 x 137 ft; orientation NCSTAR 1-5A'
        root['floor_use_source']='NIST NCSTAR 1 Table 1-1 and Fig 1-9: 44 and 78 are express/local transfer sky lobbies'
        root.asset_mark()
        root.asset_data.description='Modular lobby core finish, coffer pans, luminaires, carpet fields. Photo-informed; inferred dimensions.'
        root.instance_offset=(*xy,0)
        legacy=next((c for c in parent.children if c.name.startswith('six_story_lobby')),None)
        if legacy:
            for obj in legacy.objects:
                if any(s in obj.name for s in ('_lobby_ceiling','_lobby_elevator_bank','_elevator_door','_lobby_area_')):
                    obj.hide_render=True
                    obj.hide_set(True)
                    obj['superseded_by']=rootname
        halfcore=((137*FT/2,87*FT/2) if name=='WTC1' else (87*FT/2,137*FT/2))
        ceiling=6*12*FT  # existing display datum retained, not a measured ceiling level
        b=Builder(name+'_LR')
        coffercol=_collection(name+'_LOBBY_modular_coffers',root)
        corecol=_collection(name+'_LOBBY_core_finish_panels',root)
        gallerycol=_collection(name+'_LOBBY_gallery_soffit_and_carpet',root)
        lightcol=_collection(name+'_LOBBY_lighting',root)
        _coffers(b,xy,halfcore,ceiling,coffercol,mats)
        _core(b,xy,halfcore,ceiling,corecol,mats)
        _soffits_and_floor(b,xy,halfcore,gallerycol,mats)
        _lighting(b,xy,halfcore,ceiling,lightcol)
        # Facts belong in metadata, not speculative public-facing historic signs.
        for level in (44,78):
            slab=bpy.data.objects.get(f'{name}_F{level}_SKY_LOBBY_STUDY')
            if slab:
                slab['transfer_function']='Express elevator to this sky lobby; transfer to local bank'
                slab['transfer_source']='NIST NCSTAR 1 Fig 1-9; NCSTAR 1-7 section 2.2.3'
                slab['fitout_confidence']='Transfer floor documented; existing room geometry and elevation remain schematic'
        created.append(root)
    return created
