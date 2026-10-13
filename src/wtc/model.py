"""Evidence-bounded WTC tower study. Run with Blender: blender -b -P build.py."""
import bpy
import math
from mathutils import Vector
from wtc.context import wtc7_massing, program_metadata
from wtc.completion import build_completion

FT = 0.3048
SIDE = (208 + 10/12) * FT  # outside column cover to outside column cover
CHAMFER = (6 + 11/12) * FT
COLUMN_PITCH = 40 / 12 * FT
COLUMN_SECTION = 14 / 12 * FT
SPANDREL_DEPTH = 52 / 12 * FT
TREE_TO_REGULAR = (418 + 11.5/12 - 310) * FT  # NIST drawing elevations, Concourse = El.310
TOP_TRANSITION_DEPTH = 3 * 12 * FT  # display estimate; exact level heights unresolved
ROOFS = {"WTC1": 1368 * FT, "WTC2": 1362 * FT}
MATERIALS = {}
MESH_CACHE = {}


def material(name, color, metallic=0, roughness=.42):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    noise=m.node_tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=42
    bump=m.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.045 if metallic else .12
    bump.inputs['Distance'].default_value=.025
    m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    m.node_tree.links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    return m


def cube(name, location, scale, collection, mat):
    key=(*scale,mat.name)
    mesh=MESH_CACHE.get(key)
    if mesh is None:
        a,b,c=(v/2 for v in scale)
        mesh=bpy.data.meshes.new(name+'_prototype_mesh')
        mesh.from_pydata([(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),
                         (-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)],[],
                        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
        mesh.materials.append(mat); MESH_CACHE[key]=mesh
    ob=bpy.data.objects.new(name,mesh); collection.objects.link(ob)
    ob.location=location
    return ob


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def wide_flange_mesh(name,height,mat):
    # Rolled-member type proxy. Exact upper-wall rolled section is unresolved.
    w=d=.32; t=.035; web=.045
    p=[(-w/2,-d/2),(w/2,-d/2),(w/2,-d/2+t),(web/2,-d/2+t),
       (web/2,d/2-t),(w/2,d/2-t),(w/2,d/2),(-w/2,d/2),
       (-w/2,d/2-t),(-web/2,d/2-t),(-web/2,-d/2+t),(-w/2,-d/2+t)]
    n=len(p); mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(a,b,z) for z in (-height/2,height/2) for a,b in p],[],
                     [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+
                     [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    mesh.materials.append(mat)
    return mesh


def tower(name, xy, roof, cladding, glass):
    root = collection(name)
    shell = bpy.data.collections.new("01_envelope_verified")
    columns = bpy.data.collections.new("02_perimeter_rhythm_schematic")
    core = bpy.data.collections.new("03_core_extent_approximate")
    floors = bpy.data.collections.new("04_floor_datum_schematic")
    prototype = bpy.data.collections.new("05_three_story_facade_prototype")
    panes = bpy.data.collections.new('06_glazing_panels_STUDY')
    for c in (shell, columns, core, floors, prototype,panes): root.children.link(c)
    x, y = xy
    h = SIDE / 2
    c = CHAMFER
    pts = [(-h+c,-h),(h-c,-h),(h,-h+c),(h,h-c),(h-c,h),(-h+c,h),(-h,h-c),(-h,-h+c)]
    # The glazing study sits inside the documented outer-cover dimension.
    glazing_inset = .48
    pts = [(a*(h-glazing_inset)/h,b*(h-glazing_inset)/h) for a,b in pts]
    base_transition=TREE_TO_REGULAR
    verts = [(a,b,z) for z in (base_transition,roof-7.9) for a,b in pts]
    faces = [tuple(range(7,-1,-1)), tuple(range(8,16))] + [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    mesh = bpy.data.meshes.new(name+"_envelope")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(glass)
    ob = bpy.data.objects.new(name+"_envelope_208ft10in", mesh)
    ob.location=(x,y,0)
    shell.objects.link(ob)
    ob["source"] = "NIST NCSTAR 1-5A vol 1 sec 4.2.1"
    ob["accuracy"] = "outer-cover envelope; internal geometry not claimed"
    # Leave the mechanical louver zone open, with a separate upper glazed band.
    topverts=[(a,b,z) for z in (roof-2.0,roof) for a,b in pts]
    topmesh=bpy.data.meshes.new(name+'_top_glazing_band_mesh')
    topmesh.from_pydata(topverts,[],[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)])
    topmesh.materials.append(glass)
    topglass=bpy.data.objects.new(name+'_top_glazing_band_STUDY',topmesh)
    shell.objects.link(topglass); topglass.location=(x,y,0)
    topglass['confidence']='upper glazing band height estimated; mechanical opening elevation estimated'
    pane_mats=[material(name+f'_glazing_tone_{k}_STUDY',
               (.095*(.85+.075*k),.19*(.85+.075*k),.23*(.85+.075*k)),.20,.20)
               for k in range(5)]
    upper_rolled=wide_flange_mesh(name+'_upper_rolled_type_mesh',TOP_TRANSITION_DEPTH,cladding)
    # NIST NCSTAR 1-3 provides 59 columns/side, 40 in centers, 14 in section.
    # The trident and 107-110 wall are built as distinct modules.
    for side in range(4):
        for i in range(59):
            p = (i-29)*COLUMN_PITCH
            q = h-COLUMN_SECTION/2
            top_start=roof-TOP_TRANSITION_DEPTH
            mid=(top_start+base_transition)/2
            rise=top_start-base_transition
            if side == 0: loc=(x+p,y-q,mid); dims=(COLUMN_SECTION,COLUMN_SECTION,rise)
            elif side == 1: loc=(x+q,y+p,mid); dims=(COLUMN_SECTION,COLUMN_SECTION,rise)
            elif side == 2: loc=(x-p,y+q,mid); dims=(COLUMN_SECTION,COLUMN_SECTION,rise)
            else: loc=(x-q,y-p,mid); dims=(COLUMN_SECTION,COLUMN_SECTION,rise)
            ob = cube(f"{name}_face{side+1}_column{i+1:02d}",loc,dims,columns,cladding)
            ob["source"]="NIST NCSTAR 1-3 sec 2.3.1: 59/side, 40 in pitch, approx 14 in steel section"
            ob["confidence"]="pitch/steel section sourced; full-height extent and visible cover are schematic"
            # 107–110 changes to rolled/box members (NIST 1-3 §2.3.4).
            # The exact rolled-shape schedule is not transcribed here.
            top_width=7/12*FT if i%2==0 else .32
            top_depth=5/12*FT if i%2==0 else .32
            top_loc=(loc[0],loc[1],(top_start+roof)/2)
            top_dims=(top_width,top_depth,TOP_TRANSITION_DEPTH) if side%2==0 else (top_depth,top_width,TOP_TRANSITION_DEPTH)
            cap=cube(f"{name}_upper_wall_face{side+1}_member{i+1:02d}_STUDY",top_loc,top_dims,columns,cladding)
            if i%2:
                cap.data=upper_rolled
                cap.rotation_euler[2]=side*math.pi/2
            cap['source']='NIST NCSTAR 1-3 §2.3.4 and NCSTAR 1-2A §3.2.7'
            cap['confidence']='7x5 inch tube section sourced; alternate rolled-member section/spacing are display estimates'
        # Top wall has deeper horizontal members, separated from the typical facade.
        for tier,offset in enumerate((TOP_TRANSITION_DEPTH*.42, TOP_TRANSITION_DEPTH*.83)):
            z=roof-TOP_TRANSITION_DEPTH+offset
            q=h-COLUMN_SECTION/2
            if side==0: loc=(x,y-q,z); dims=(58*COLUMN_PITCH+COLUMN_SECTION,.4,1.2)
            elif side==1: loc=(x+q,y,z); dims=(.4,58*COLUMN_PITCH+COLUMN_SECTION,1.2)
            elif side==2: loc=(x,y+q,z); dims=(58*COLUMN_PITCH+COLUMN_SECTION,.4,1.2)
            else: loc=(x-q,y,z); dims=(.4,58*COLUMN_PITCH+COLUMN_SECTION,1.2)
            top_sp=cube(f"{name}_upper_wall_face{side+1}_spandrel{tier+1}_STUDY",loc,dims,columns,cladding)
            top_sp['source']='NIST NCSTAR 1-2A §3.2.7: upper-story spandrel variation'
            top_sp['confidence']='position and depth estimated for CG, not fabrication geometry'
        # Full facade rhythm, with level interpolation expressly recorded.
        for level in range(98):
            z=base_transition+(level+.5)*(top_start-base_transition)/98
            q=h-.68  # steel spandrel is behind the glazing display plane
            if side==0: loc=(x,y-q,z); dims=(58*COLUMN_PITCH+COLUMN_SECTION,.18,SPANDREL_DEPTH)
            elif side==1: loc=(x+q,y,z); dims=(.18,58*COLUMN_PITCH+COLUMN_SECTION,SPANDREL_DEPTH)
            elif side==2: loc=(x,y+q,z); dims=(58*COLUMN_PITCH+COLUMN_SECTION,.18,SPANDREL_DEPTH)
            else: loc=(x-q,y,z); dims=(.18,58*COLUMN_PITCH+COLUMN_SECTION,SPANDREL_DEPTH)
            bar=cube(f'{name}_face{side}_floor_band_{level+9:03d}_STUDY',loc,dims,columns,cladding)
            bar['source']='NIST NCSTAR 1-3: typical 52 inch spandrel'
            bar['confidence']='uniform floor interpolation; floor-specific elevations unresolved'
        # Actual individual pane faces; deterministic tone variation is lighting
        # art direction, not a claim about tenancy or historical window tints.
        verts=[]; faces=[]; tones=[]
        floor_pitch=(top_start-base_transition)/98
        for level in range(98):
            z=base_transition+(level+.5)*floor_pitch
            pane_height=floor_pitch-SPANDREL_DEPTH
            for win in range(58):
                p=(win-28.5)*COLUMN_PITCH
                width=COLUMN_PITCH-COLUMN_SECTION
                q=h-.47
                coords=[(p-width/2,z-pane_height/2),(p+width/2,z-pane_height/2),
                        (p+width/2,z+pane_height/2),(p-width/2,z+pane_height/2)]
                start=len(verts)
                for t,zz in coords:
                    if side==0: v=(t,-q,zz)
                    elif side==1: v=(q,t,zz)
                    elif side==2: v=(-t,q,zz)
                    else: v=(-q,-t,zz)
                    verts.append(v)
                faces.append(tuple(range(start,start+4)))
                tones.append((level*17+win*13+side*7)%5)
        mesh=bpy.data.meshes.new(f'{name}_face{side}_individual_panes_mesh')
        mesh.from_pydata(verts,[],faces)
        for m in pane_mats: mesh.materials.append(m)
        for poly,tone in zip(mesh.polygons,tones): poly.material_index=tone
        window=bpy.data.objects.new(f'{name}_face{side}_glazing_panes_STUDY',mesh)
        panes.objects.link(window); window.location=(x,y,0)
        window['source']='derived from NIST 40 inch pitch, 14 inch column and typical 52 inch structural spandrel'
        window['confidence']='planar display glass; cover/inset and floor heights estimated; tone variation is art direction'
    # An isolated 3-story sample, centered at arbitrary display elevation.
    # NIST cites 36 ft prefabricated 3-story panels and 52 in typical spandrels.
    # These bars are only a facade-detail study, not claimed as actual floor elevations.
    sample_z = roof*.55
    for j in range(4):
        z = sample_z + (j-1.5)*12*FT
        ob = cube(f"{name}_sample_spandrel_{j+1}",
                  (x,y-h+.02,z),
                  (58*COLUMN_PITCH+COLUMN_SECTION,.16,SPANDREL_DEPTH),
                  prototype,cladding)
        ob["source"]="NIST NCSTAR 1-3 sec 2.3.1: typical 52 in spandrel; 36 ft/3-story panel"
        ob["confidence"]="section depth sourced; absolute elevation arbitrary, sample only"
        ob.hide_render=True
        ob.hide_viewport=True
    # NIST approximate 87 x 137 ft. Flat translucent-free block keeps it visible
    # in top views and deliberately omits unsourced shafts/stairs.
    core_xy=(137*FT,87*FT) if name=='WTC1' else (87*FT,137*FT)
    ob = cube(name+"_core_extent_approx",(x,y,roof/2),(*core_xy,roof),core,material("core_study",(.22,.28,.32)))
    ob.hide_render = True
    ob.hide_viewport = True
    ob["source"]="NIST NCSTAR 1-3A sec 2.1, approximately 87 x 137 ft; NIST NCSTAR 1-5A: WTC1 E-W, WTC2 N-S"
    # Floor datum only: equal interpolation is expressly NOT actual story elevations.
    ob = cube(name+"_roof_datum",(x,y,roof+.20),(SIDE*.98,SIDE*.98,.4),floors,cladding)
    ob["source"]="NIST NCSTAR 1-5A vol 1 sec 4.2.1 roof height"
    root["status"]="detailed CG study: sourced envelope/pitch/program; tree, top wall and interiors carry confidence tags"
    return root


def build():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        if col.name != bpy.context.scene.collection.name and col.users == 0: bpy.data.collections.remove(col)
    stone=material("silver_cladding_color_study",(.72,.76,.78),.72,.28)
    glass=material("blue_gray_glazing_color_study",(.095,.19,.23),.28,.18)
    site=collection("SITE_study_datum_only")
    slab=cube("site_datum_NOT_surveyed",(0,55,-1),(380,490,2),site,material("site_neutral",(.14,.17,.18)))
    slab["confidence"]="arbitrary visualization ground; not site geometry"
    # Relative site positions are visual staging, not georeferenced coordinates.
    tower("WTC1",(-55,55),ROOFS["WTC1"],stone,glass)
    tower("WTC2",(55,-55),ROOFS["WTC2"],stone,glass)
    wtc7_massing(center=(-20,230))
    program_metadata()
    tile_count=build_completion(ROOFS,stone,glass)
    bpy.context.scene['individual_plaza_tile_meshes']=tile_count
    world=bpy.context.scene.world
    world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.55,.62,.70,1)
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.7
    bpy.ops.object.camera_add(location=(700,-850,640))
    cam=bpy.context.object
    cam.rotation_euler=(Vector((0,55,205))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'; cam.data.ortho_scale=1120
    cam.data.clip_end=10000
    bpy.context.scene.camera=cam
    bpy.ops.object.light_add(type='SUN', location=(0,0,500))
    bpy.context.object.data.energy=3.0
    bpy.context.object.rotation_euler=(math.radians(25),math.radians(-25),math.radians(-30))
    bpy.ops.object.light_add(type='SUN',location=(0,0,500))
    bpy.context.object.name='soft_review_fill'
    bpy.context.object.data.energy=.85
    bpy.context.object.data.use_shadow=False
    bpy.context.object.rotation_euler=(math.radians(-50),math.radians(20),math.radians(130))
    bpy.context.scene.render.engine='BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x=1000
    bpy.context.scene.render.resolution_y=1000
    bpy.context.scene.render.resolution_percentage=100
    bpy.context.scene.render.image_settings.file_format='PNG'
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.view_settings.view_transform='AgX'

