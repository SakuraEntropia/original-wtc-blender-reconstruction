"""Procedural CG detail. Inferred profiles remain explicitly tagged STUDY."""
import bpy
import math
from mathutils import Vector

FT=.3048
PLAZA_Z=22*FT  # NIST NCSTAR 1-1 Fig 2-3: Plaza El.332, Concourse El.310
TREE_SPLICE=(363-310)*FT
TREE_TOP=(418+11.5/12-310)*FT
FORK_START=TREE_SPLICE+(9+4/12)*FT
FORK_END=FORK_START+(11+4/12)*FT
FORK_CROTCH=FORK_START+6*FT  # original 2-AB2-2, NIST 1-2A Fig 3-6


def group(name):
    c=bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def mat(name,color,metal=0,rough=.45):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal
    p.inputs['Roughness'].default_value=rough
    noise=m.node_tree.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=28
    bump=m.node_tree.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.07
    bump.inputs['Distance'].default_value=.018
    m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m


def box(name,loc,size,col,material):
    a,b,c=(v/2 for v in size)
    verts=[(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),
           (-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]
    mesh=bpy.data.meshes.new(name+'_mesh')
    mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    mesh.materials.append(material)
    obj=bpy.data.objects.new(name,mesh); col.objects.link(obj)
    obj.location=loc
    return obj


def strut(name,p1,p2,width,col,material):
    mid=(Vector(p1)+Vector(p2))/2
    direction=Vector(p2)-Vector(p1)
    ob=box(name,mid,(width,width,direction.length),col,material)
    ob.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    return ob


def cylinder(name,location,radius,depth,col,material,vertices=16):
    verts=[(radius*math.cos(2*math.pi*k/vertices),radius*math.sin(2*math.pi*k/vertices),z)
           for z in (-depth/2,depth/2) for k in range(vertices)]
    faces=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,2*vertices))]
    faces += [(k,(k+1)%vertices,(k+1)%vertices+vertices,k+vertices) for k in range(vertices)]
    mesh=bpy.data.meshes.new(name+'_mesh'); mesh.from_pydata(verts,[],faces)
    mesh.materials.append(material)
    ob=bpy.data.objects.new(name,mesh); col.objects.link(ob); ob.location=location
    return ob


def tube(name,p1,p2,radius,col,material):
    a,b=Vector(p1),Vector(p2)
    ob=cylinder(name,(a+b)/2,radius,(b-a).length,col,material,12)
    ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return ob


def tree_plate(name,center,tangent,col,material):
    """One watertight, concave plate-prism per three-to-one tree column.

    This is a visual loft between *sourced* pitch/splice datums. Section contour
    is conjectural until Drawing Book 2 section plates are manually traced.
    """
    # Ordered silhouette: outer left, two V notches, outer right, stem.
    profile=[(-.40,PLAZA_Z),(-.40,FORK_START),(-.65,FORK_CROTCH),(-1.2446,FORK_END),
             (-1.2446,TREE_TOP),(-.7874,TREE_TOP),(-.7874,FORK_END),(-.56,FORK_CROTCH+.6),
             (-.25,FORK_CROTCH),(-.2286,FORK_END),(-.2286,TREE_TOP),(.2286,TREE_TOP),
             (.2286,FORK_END),(.25,FORK_CROTCH),(.56,FORK_CROTCH+.6),(.7874,FORK_END),
             (.7874,TREE_TOP),(1.2446,TREE_TOP),(1.2446,FORK_END),
             (.65,FORK_CROTCH),(.40,FORK_START),(.40,PLAZA_Z)]
    n=len(profile); nx,ny=-tangent[1],tangent[0]; depth=.50
    verts=[]
    for normal in (-depth/2,depth/2):
        for t,z in profile:
            verts.append((tangent[0]*t+nx*normal,
                          tangent[1]*t+ny*normal,z-PLAZA_Z))
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name+'_mesh'); mesh.from_pydata(verts,[],faces)
    mesh.materials.append(material); mesh.update()
    ob=bpy.data.objects.new(name,mesh); col.objects.link(ob)
    ob.location=(*center,PLAZA_Z)
    bevel=ob.modifiers.new('soft_cladding_edges','BEVEL'); bevel.width=.035; bevel.segments=2
    ob.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
    ob['source']='NIST NCSTAR 1-2A Fig 3-6: three-to-one trident; El.363 and El.418ft11.5in splice'
    ob['confidence']='pitch, splice, 9ft4in stem and 11ft4in fork height from Fig3-6; plate width/depth and curve interpolation estimated'
    return ob


def ahu(name,xyz,size,col,body,trim):
    """Generic AHU assembly; dimensions are a CG type study, not WTC schedule."""
    x,y,z=xyz; sx,sy,sz=size
    ob=box(name+'_case_STUDY',(x,y,z),(sx,sy,sz),col,body)
    ob['confidence']='type reference from NIST 1-4D Fig 4-6; size/placement estimated'
    for side in (-1,1):
        box(name+f'_service_panel_{side}_STUDY',
            (x+side*(sx/2+.015),y,z),(.03,sy*.72,sz*.72),col,trim)
    for k in (-1,1):
        fan=cylinder(name+f'_fan_{k}_STUDY',
                     (x+sx*.20*k,y-sy/2-.06,z),sz*.19,.12,col,trim,16)
        fan.rotation_euler=(math.pi/2,0,0)
        r=sz*.19
        verts=[]; faces=[]
        for blade in range(6):
            angle=blade*math.pi/3
            profile=[(r*.18*math.cos(angle),r*.18*math.sin(angle)),
                     (r*.88*math.cos(angle+.22),r*.88*math.sin(angle+.22)),
                     (r*.85*math.cos(angle+.60),r*.85*math.sin(angle+.60)),
                     (r*.18*math.cos(angle+.40),r*.18*math.sin(angle+.40))]
            n=len(verts)
            verts += [(a,b,d) for d in (-.018,.018) for a,b in profile]
            faces += [tuple(n+j for j in f) for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))]
        mesh=bpy.data.meshes.new(name+f'_impeller_{k}_mesh'); mesh.from_pydata(verts,[],faces)
        mesh.materials.append(body)
        rotor=bpy.data.objects.new(name+f'_six_blade_impeller_{k}_STUDY',mesh); col.objects.link(rotor)
        rotor.location=(x+sx*.20*k,y-sy/2-.15,z); rotor.rotation_euler=(math.pi/2,0,0)
        for grid in (-1,0,1):
            box(name+f'_fan_guard_{k}_{grid}_STUDY',
                (x+sx*.20*k+r*.43*grid,y-sy/2-.20,z),(.022,.035,r*1.6),col,trim)
    for k in range(3):
        box(name+f'_filter_slit_{k}_STUDY',
            (x-sx*.32+k*sx*.32,y+sy/2+.02,z),(.08,.04,sz*.53),col,trim)
    return ob


def mechanical_modules(name,xy,roof,root,roofcol,dark,clad):
    x,y=xy
    plant=bpy.data.collections.new('MEP_108_109_type_reference_cutaway')
    root.children.link(plant)
    plant['source']='NIST 1-4C p85: typical MER 12 AHUs; 1-4D Figs4-5..4-8: 75/76 system types; NCSTAR1 Table1-1: 108/109 mechanical use'
    plant['confidence']='108/109 arrangement, equipment size and pipe routing unknown; design-type reference only'
    copper=mat(name+'_MEP_copper_STUDY',(.45,.25,.11),.7,.32)
    ductmat=mat(name+'_MEP_galvanized_STUDY',(.32,.37,.39),.5,.43)
    z=roof-7.3
    slab=box(name+'_MER_cutaway_floor_STUDY',(x,y,z-1.225),(59,59,.20),plant,dark)
    slab['confidence']='CG support datum for equipment; elevation estimated'
    for row in (-1,1):
        for k in range(6):
            dx=-19+k*7.6; dy=row*12
            unit=ahu(f'{name}_MER_type_AHU_{row}_{k}',(x+dx,y+dy,z),(4.8,2.9,2.25),plant,dark,ductmat)
            unit['type_position']='interior/perimeter/core schematic distribution'
            # Local square ducts lead toward the central spine; segmentation is visible.
            strut(f'{name}_MER_supply_duct_{row}_{k}_STUDY',
                  (x+dx,y+dy-row*1.5,z+.3),(x+dx,y+row*3.0,z+.3),.56,plant,ductmat)
    for side in (-1,1):
        for k in range(5):
            px=x-21+k*10.5
            tube(f'{name}_MER_high_pressure_pipe_{side}_{k}_STUDY',
                 (px,y+side*18,z-.8),(px,y+side*7,z-.8),.09,plant,copper)
            for flange in (9,16):
                ob=cylinder(f'{name}_MER_pipe_flange_{side}_{k}_{flange}_STUDY',
                    (px,y+side*flange,z-.8),.15,.07,plant,ductmat,12)
                ob.rotation_euler=(math.pi/2,0,0)
        box(f'{name}_MER_return_plenum_{side}_STUDY',
            (x,y+side*22,z+.5),(47,2.5,1.3),plant,ductmat)
    # Visible top-floor ventilation line: 4 ft setback is sourced; slat layout is not.
    louvers=bpy.data.collections.new('MEP_108_109_recessed_louvers')
    root.children.link(louvers)
    louvers['source']='NIST NCSTAR 1-5A v2 Appendix A, Figs A-1..A-8: 108/109 grilles 4 ft behind outer wall'
    louvers['confidence']='strip count and extents schematic; consult elevation sheets for exact schedule'
    q=63.6524/2-4*FT
    for side in range(4):
        for panel in range(8):
            p=-23+panel*6.6
            for s in range(5):
                zz=roof-7.6+s*.56
                if side==0: loc=(x+p,y-q,zz); dim=(5.5,.08,.09)
                elif side==1: loc=(x+q,y+p,zz); dim=(.08,5.5,.09)
                elif side==2: loc=(x-p,y+q,zz); dim=(5.5,.08,.09)
                else: loc=(x-q,y-p,zz); dim=(.08,5.5,.09)
                ob=box(f'{name}_recessed_louver_{side}_{panel}_{s}_STUDY',loc,dim,louvers,dark)
                ob['recess_m']=4*FT
    # Hat truss is a separate inspectable structural asset. Equipment reference
    # and structure are not presented as a coordinated as-built MEP solution.
    hat=bpy.data.collections.new('hat_truss_structure_STUDY')
    root.children.link(hat)
    hat['source']='NIST NCSTAR 1-2A §3.2.8, Figs 3-10,3-11'
    hat['confidence']='four planes each axis sourced; node positions and profiles estimated'
    core_x,core_y=((137*FT,87*FT) if name=='WTC1' else (87*FT,137*FT))
    for axis in (0,1):
        for k in range(4):
            along=core_x if axis==0 else core_y
            across=core_y if axis==0 else core_x
            off=(-.5,-1/6,1/6,.5)[k]*across
            nodes=(-along/2,-along/6,along/6,along/2)
            def point(t,z):
                return (x+t,y+off,z) if axis==0 else (x+off,y+t,z)
            elevations=(roof-10,roof-7,roof-4,roof-1)
            for z in elevations:
                strut(f'{name}_hat_chord_{axis}_{k}_{z:.1f}_STUDY',
                      point(-along/2,z),point(along/2,z),.38,hat,dark)
            for j,t in enumerate(nodes):
                strut(f'{name}_hat_vertical_{axis}_{k}_{j}_STUDY',
                      point(t,roof-10),point(t,roof-1),.28,hat,dark)
            for story in range(3):
                for j in range(3):
                    a,b=elevations[story:story+2]
                    if (j+story)%2: a,b=b,a
                    strut(f'{name}_hat_diagonal_{axis}_{k}_{story}_{j}_STUDY',
                          point(nodes[j],a),point(nodes[j+1],b),.30,hat,dark)
            # Triangular outriggers transfer core forces to the perimeter.
            for side in (-1,1):
                outer=point(side*29,roof-4)
                for label,z in (('low',roof-10),('high',roof-1),('tie',roof-4)):
                    strut(f'{name}_hat_outrigger_{axis}_{k}_{side}_{label}_STUDY',
                          point(side*along/2,z),outer,.38,hat,dark)
    plant.hide_render=True
    hat.hide_render=True
    return plant


def rooftop_detail(name,xy,roof,root,col,dark,clad):
    x,y=xy
    col['source']='NIST NCSTAR 1 Table 1-1 roof use; 1-4D system types'
    col['confidence']='rooftop unit footprints, sizes, ducts and railing geometry estimated'
    galvanized=mat(name+'_roof_galvanized_STUDY',(.35,.39,.40),.55,.37)
    red=mat(name+'_roof_safety_red_STUDY',(.46,.09,.07),.3,.4)
    # Four perimeter caps and corner drain markers.
    for side in (-1,1):
        box(f'{name}_roof_parapet_EW_{side}_STUDY',(x,y+side*30.8,roof+.65),
            (61.5,.35,1.3),col,clad)
        box(f'{name}_roof_parapet_NS_{side}_STUDY',(x+side*30.8,y,roof+.65),
            (.35,61.5,1.3),col,clad)
    # Service enclosures and exposed duct tree. WTC2 central roof kept open for visitors.
    clusters=[(-17,-13),(-17,12),(16,-12),(17,12)] if name=='WTC1' else [(-15,-9),(-15,9),(15,-9),(15,9)]
    for i,(dx,dy) in enumerate(clusters):
        u=ahu(f'{name}_roof_service_unit_{i}',(x+dx,y+dy,roof+1.4),
              (6.1,3.5,2.8),col,dark,galvanized)
        u['confidence']='rooftop equipment class inferred; historical position not verified'
        for k in (-1,1):
            cx=x+dx+k*1.5; cy=y+dy+3.8
            stack=cylinder(f'{name}_roof_vent_stack_{i}_{k}_STUDY',
                           (cx,cy,roof+1.2),.34,2.4,col,galvanized)
            stack['confidence']='generic roof outlet; not as-built'
            cylinder(f'{name}_roof_vent_cap_{i}_{k}_STUDY',
                     (cx,cy,roof+2.45),.53,.15,col,red)
        strut(f'{name}_roof_main_duct_{i}_STUDY',
              (x+dx,y+dy-2.0,roof+.8),(x+dx,y+dy-6.0,roof+.8),.72,col,galvanized)
    for side in (-1,1):
        # Long service access grating, with distinct mesh from roof plate.
        box(f'{name}_roof_service_walk_{side}_STUDY',
            (x+side*25,y,roof+.08),(1.2,48,.12),col,galvanized)
        for j in range(8):
            cylinder(f'{name}_roof_drain_{side}_{j}_STUDY',
                (x+side*28,y-24+j*7,roof+.02),.16,.05,col,dark)


def lobby_detail(name,xy,col,stone,dark,brass,clad):
    x,y=xy
    col['source']='NIST NCSTAR 1 Table 1-1: Concourse-6 lobby; Fig 2-3: Plaza 22 ft above Concourse'
    col['confidence']='fit-out, balcony, entrances, doors and stair sizes are schematic'
    # Plaza-level atrium rim with an open center, rather than one solid floor.
    for side in (-1,1):
        box(f'{name}_plaza_lobby_rim_NS_{side}_STUDY',
            (x+side*24,y,PLAZA_Z-.18),(12,60,.36),col,stone)
        box(f'{name}_plaza_lobby_rim_EW_{side}_STUDY',
            (x,y+side*24,PLAZA_Z-.18),(36,12,.36),col,stone)
        # Open railing admits a lobby interior view.
        for k in range(16):
            yy=y-18+k*2.4
            box(f'{name}_atrium_rail_post_{side}_{k}_STUDY',
                (x+side*18,yy,PLAZA_Z+.55),(.06,.06,1.1),col,brass)
        box(f'{name}_atrium_rail_top_{side}_STUDY',
            (x+side*18,y,PLAZA_Z+1.1),(.08,38,.07),col,brass)
    # Two visible concourse/plaza stairs.
    steps=28; rise=PLAZA_Z/steps
    for side in (-1,1):
        for s in range(steps):
            box(f'{name}_lobby_stair_{side}_{s}_STUDY',
                (x+side*23,y-12+s*.32,(s+.5)*rise),
                (2.8,.34,rise),col,stone)
        strut(f'{name}_lobby_stair_rail_{side}_STUDY',
              (x+side*24.2,y-12,1),(x+side*24.2,y-12+steps*.32,PLAZA_Z+1),.06,col,brass)
    # Entrance frames and door panels sit at plaza level.
    for side in range(4):
        for door in range(5):
            t=-6+door*3
            if side==0: loc=(x+t,y-30,PLAZA_Z+2); dim=(2.3,.08,4)
            elif side==1: loc=(x+30,y+t,PLAZA_Z+2); dim=(.08,2.3,4)
            elif side==2: loc=(x-t,y+30,PLAZA_Z+2); dim=(2.3,.08,4)
            else: loc=(x-30,y-t,PLAZA_Z+2); dim=(.08,2.3,4)
            panel=box(f'{name}_plaza_entrance_panel_{side}_{door}_STUDY',loc,dim,col,dark)
            panel['confidence']='door grid for presentation only'
            # Bronze transom of each opening.
            head=tuple((v+2.03 if i==2 else v) for i,v in enumerate(loc))
            d=(dim[0],max(.10,dim[1]),.08) if side%2==0 else (.10,dim[1],.08)
            box(f'{name}_plaza_entrance_transom_{side}_{door}_STUDY',head,d,col,brass)
    # Ceiling / warm linear luminaires, physically modeled emissive panels.
    ceiling_z=6*12*FT
    box(name+'_lobby_ceiling_STUDY',(x,y,ceiling_z),(59,59,.25),col,clad)
    warm=mat(name+'_lobby_warm_lights',(1,.72,.4),0,.2)
    p=warm.node_tree.nodes.get('Principled BSDF')
    p.inputs['Emission Color'].default_value=(1,.72,.4,1); p.inputs['Emission Strength'].default_value=2
    for side in (-1,1):
        for k in range(7):
            box(f'{name}_lobby_ceiling_light_{side}_{k}_STUDY',
                (x+side*23,y-21+k*7,ceiling_z-.17),(1.0,3.0,.08),col,warm)
    for dx,dy in ((-15,-15),(15,-15),(-15,15),(15,15)):
        light=bpy.data.lights.new(name+f'_lobby_area_{dx}_{dy}','AREA')
        light.energy=1800; light.shape='DISK'; light.size=10
        ob=bpy.data.objects.new(light.name,light); col.objects.link(ob)
        ob.location=(x+dx,y+dy,ceiling_z-1)


def tower_completion(name,xy,roof,clad,glass):
    x,y=xy; half=63.6524/2
    root=group(name+'_COMPLETION_study')
    trident=bpy.data.collections.new('base_tridents_NIST_count_geometry_study')
    lobby=bpy.data.collections.new('six_story_lobby_material_study')
    core=bpy.data.collections.new('47_core_columns_layout_study')
    landings=bpy.data.collections.new('skylobby_and_MEP_floor_datums')
    roofcol=bpy.data.collections.new('roof_mechanical_and_hat_truss_study')
    for c in (trident,lobby,core,landings,roofcol): root.children.link(c)
    stone=mat(name+'_warm_pale_stone_STUDY',(.62,.59,.53),.02)
    dark=mat(name+'_dark_metal_STUDY',(.12,.14,.16),.55)
    brass=mat(name+'_brass_STUDY',(.47,.38,.23),.65)
    # NIST: 57 inner lines merge three-to-one, 19 base axes at 10 ft.
    # Two face-end lines are separate straight columns, not extra trees.
    for side in range(4):
        for j in range(19):
            mid_i=2+j*3
            p=(mid_i-29)*40/12*FT
            q=(207+2/12)*FT/2
            if side==0:
                rootp=(x+p,y-q); tangent=(1,0)
            elif side==1:
                rootp=(x+q,y+p); tangent=(0,1)
            elif side==2:
                rootp=(x-p,y+q); tangent=(-1,0)
            else:
                rootp=(x-q,y-p); tangent=(0,-1)
            ob=tree_plate(f'{name}_tree_s{side}_{j}',rootp,tangent,trident,clad)
            ob['base_axis_spacing_m']=10*FT
            ob['upper_axis_spacing_m']=(40/12)*FT
            support=box(f'{name}_concourse_tree_stem_s{side}_{j}_STUDY',
                        (*rootp,PLAZA_Z/2),(.55,.55,PLAZA_Z),trident,dark)
            support['source']='NIST lower exterior column axes below Plaza'
            support['confidence']='lower steel section guessed; same 10 ft axis spacing'
        for idx in (0,58):
            p=(idx-29)*(40/12)*FT; q=(207+2/12)*FT/2
            if side==0: edge=(x+p,y-q)
            elif side==1: edge=(x+q,y+p)
            elif side==2: edge=(x-p,y+q)
            else: edge=(x-q,y-p)
            ob=box(f'{name}_face{side}_end_column_{idx}_STUDY',
                   (*edge,(PLAZA_Z+TREE_TOP)/2),(.36,.36,TREE_TOP-PLAZA_Z),trident,clad)
            ob['source']='NIST NCSTAR 1-1 Fig 2-3: 59 upper lines; corner drawings 2-AB2-17..22 still unresolved'
            ob['confidence']='temporary corner-return proxy; 59/19 count does not establish straight-column geometry'
    # Interior has physical but intentionally simplified volumes. Exact elevator bays unknown.
    floor=box(name+'_lobby_floor_STUDY',(x,y,.12),(61,61,.24),lobby,stone)
    floor['basis']='six-story lobby exists; finish, dimensions and layout are unverified'
    lobby_h=6*12*FT
    for s in (-1,1):
        box(name+f'_lobby_elevator_bank_{s}_STUDY',(x+s*9,y,1.8),(1,23,3.6),lobby,dark)
        for k in range(6):
            door=box(name+f'_elevator_door_{s}_{k}_STUDY',
                     (x+s*9.6,y-9+k*3.6,2.0),(0.1,2.1,3.6),lobby,brass)
            door['basis']='symbolic elevator bay; count/location not verified'
    lobby_detail(name,xy,lobby,stone,dark,brass,clad)
    # 47-column count documented; 6-row distribution schematic, 8+8+8+7+8+8.
    cx,cy=((137*FT,87*FT) if name=='WTC1' else (87*FT,137*FT))
    for row,n in enumerate((8,8,8,7,8,8)):
        for k in range(n):
            px=x-cx/2+(k+.5)*cx/n
            py=y-cy/2+(row+.5)*cy/6
            ob=box(f'{name}_core_{row}_{k}_STUDY',(px,py,roof/2),(.5,.5,roof),core,dark)
            ob.hide_render=True
            ob['basis']='47 core columns sourced; x/y grid and sizes not surveyed'
    for stair,(dx,dy) in enumerate(((-cx*.27,0),(0,0),(cx*.27,0))):
        ob=box(f'{name}_stairwell_{stair+1}_STUDY',
               (x+dx,y+dy,roof/2),(4.0,5.5,roof),core,stone)
        ob.hide_render=True
        ob['basis']='NIST NCSTAR 1-1 confirms three stairs; exact placement/shaft size schematic'
    # A few floor datums allow inspection after hiding shell; no claim to real elevations.
    floors={7:'MEP',8:'MEP',41:'MEP',42:'MEP',44:'SKY_LOBBY',75:'MEP',76:'MEP',78:'SKY_LOBBY',107:'PUBLIC_TOP',108:'MEP',109:'MEP'}
    for level,use in floors.items():
        z=roof*(level-1)/110
        ob=box(f'{name}_F{level}_{use}_STUDY',(x,y,z),(59,59,.32),landings,stone if use=='SKY_LOBBY' else dark)
        ob.hide_render=True
        ob['floor_use_source']='NIST NCSTAR 1 Table 1-1'
        ob['elevation_confidence']='ratio estimate, NOT design elevation'
    # Additional story datums complete the editable interior stack.  The same
    # prototype slab is reused; these are uniformly interpolated study levels.
    allfloors=bpy.data.collections.new('all_110_floor_slabs_interpolated_STUDY')
    root.children.link(allfloors)
    proto=box(name+'_F001_SLAB_STUDY',(x,y,0),(59,59,.20),allfloors,stone)
    proto.hide_render=True
    for level in range(2,111):
        zz=PLAZA_Z+(level-2)*(TREE_TOP-PLAZA_Z)/7 if level<=9 else TREE_TOP+(level-9)*(roof-TREE_TOP)/102
        if level==3:
            ob=box(f'{name}_F{level:03d}_SLAB_STUDY',(x,y,zz),(cx,cy,.20),allfloors,stone)
            core_slab_mesh=ob.data
        else:
            mesh=core_slab_mesh if level in (4,5,6) else proto.data
            ob=bpy.data.objects.new(f'{name}_F{level:03d}_SLAB_STUDY',mesh)
            allfloors.objects.link(ob); ob.location=(x,y,zz)
        ob.hide_render=True
        ob['confidence']='piecewise interpolation; slab section/shafts unknown; floors 3-6 core only per NIST 1-2A pp2-3'
    # Fit-out modules for the two sky lobbies, plus public top floor.
    special=bpy.data.collections.new('sky_lobby_and_public_top_interiors_STUDY')
    root.children.link(special)
    special['source']='NIST NCSTAR 1 Table 1-1: floors 44,78 sky lobby; WTC2 107 observation; WTC1 107 restaurant'
    special['confidence']='room layout, fit-out, lighting and finish unverified'
    for level in (44,78,107):
        z=roof*(level-1)/110
        for s in (-1,1):
            box(f'{name}_F{level}_lift_bank_{s}_STUDY',(x+s*8,y,z+1.6),
                (.4,22,3.2),special,dark)
            for k in range(6):
                box(f'{name}_F{level}_lift_door_{s}_{k}_STUDY',
                    (x+s*8.25,y-9+k*3.6,z+1.2),(.05,2.2,2.4),special,brass)
        if level==107:
            for k in range(12):
                px=x-24+(k%6)*9.6; py=y+(-21 if k<6 else 21)
                cylinder(f'{name}_public_top_table_{k}_STUDY',
                    (px,py,z+.8),.8,.12,special,stone,16)
                cylinder(f'{name}_public_top_table_leg_{k}_STUDY',
                    (px,py,z+.38),.07,.76,special,dark,8)
    for ob in special.objects: ob.hide_render=True
    mechanical_modules(name,xy,roof,root,roofcol,dark,clad)
    rooftop_detail(name,xy,roof,root,roofcol,dark,clad)
    if name=='WTC2':
        obs=bpy.data.collections.new('roof_observation_deck_STUDY')
        root.children.link(obs)
        # Outdoor observation deck is sourced; railing path and height estimated.
        for side in (-1,1):
            for zoff in (.6,1.2):
                box(f'{name}_observation_rail_X{side}_{zoff}',
                    (x+side*28,y,roof+zoff),(.06,56,.06),obs,clad)
                box(f'{name}_observation_rail_Y{side}_{zoff}',
                    (x,y+side*28,roof+zoff),(56,.06,.06),obs,clad)
            for k in range(29):
                p=-28+2*k
                box(f'{name}_observation_post_X{side}_{k}',
                    (x+side*28,y+p,roof+.6),(.06,.06,1.2),obs,clad)
                box(f'{name}_observation_post_Y{side}_{k}',
                    (x+p,y+side*28,roof+.6),(.06,.06,1.2),obs,clad)
        box(name+'_roof_observation_access_STUDY',(x,y,roof+1.5),(8,7,3),obs,dark)
        obs['basis']='NIST NCSTAR 1 Table 1-1 rooftop observation; railing geometry assumed'


def lowrise_context():
    """Storey counts sourced; footprint/heights/locations deliberately tagged estimates."""
    # WTC5 L envelope: FEMA403 ch4 330x420ft, approx120000sqft/floor.
    # Equal-sided notch inferred from approximate area, not a survey dimension.
    five_x,five_y=330*FT,420*FT
    notch=math.sqrt(five_x*five_y-120000*FT*FT)
    specs=[('WTC3_Marriott',(-112,-67),22,[(0,0,28,105),(25,-25,42,28)]),
           ('WTC4',(128,-95),9,[(0,0,42,78)]),
           ('WTC5',(129,72),9,[(0,notch/2,five_x,five_y-notch),
                              (notch/2,-(five_y-notch)/2,five_x-notch,notch)]),
           ('WTC6',(-82,150),8,[(0,0,82,39)])]
    wall=mat('lowrise_limestone_color_STUDY',(.48,.53,.52),.1)
    glazing=mat('lowrise_band_glass_STUDY',(.07,.15,.18),.35,.25)
    for name,(x,y),stories,segments in specs:
        col=group(name+'_massing_STUDY')
        height=242*FT if name=='WTC3_Marriott' else stories*3.65
        base_z=0 if name=='WTC3_Marriott' else PLAZA_Z
        col['verified']='building identity and story count: NIST NCSTAR 1-1 sec 2.1'
        col['estimated']='footprint, segment count, location, all floor heights and materials'
        if name=='WTC3_Marriott':
            col['height_source']='Council on Vertical Urbanism/Skyscraper Center building 19942: 242 ft, 22 floors; entrance datum modeled as Concourse proxy'
        if name=='WTC5':
            col['footprint_source']='FEMA403 ch4 §4.1.1: L-shaped,330x420ft,about120000sqft/floor'
            col['footprint_confidence']='envelope sourced; equal-sided notch inferred from approximate floor area; orientation/location unverified'
        for i,(dx,dy,sx,sy) in enumerate(segments):
            if base_z:
                box(f'{name}_podium_support_{i}_STUDY',(x+dx,y+dy,base_z/2),(sx,sy,base_z),col,wall)
            box(f'{name}_volume_{i}_STUDY',(x+dx,y+dy,base_z+height/2),(sx,sy,height),col,wall)
            for level in range(1,stories):
                z=base_z+level*height/stories
                # Continuous dark bands give visual floor rhythm, not surveyed windows.
                box(f'{name}_facade_band_{i}_{level}_STUDY',
                    (x+dx,y+dy-sy/2-.08,z),(sx,.16,1.3),col,glazing)
                box(f'{name}_facade_north_band_{i}_{level}_STUDY',
                    (x+dx,y+dy+sy/2+.08,z),(sx,.16,1.3),col,glazing)
                for side in (-1,1):
                    box(f'{name}_facade_side_band_{i}_{level}_{side}_STUDY',
                        (x+dx+side*(sx/2+.08),y+dy,z),(.16,sy,1.3),col,glazing)
            # Roof parapet, service walk and equipment, all massing studies.
            roof=base_z+height
            for side in (-1,1):
                box(f'{name}_roof_parapet_EW_{i}_{side}_STUDY',
                    (x+dx,y+dy+side*sy/2,roof+.38),(sx,.25,.76),col,wall)
                box(f'{name}_roof_parapet_NS_{i}_{side}_STUDY',
                    (x+dx+side*sx/2,y+dy,roof+.38),(.25,sy,.76),col,wall)
            for u in (-1,1):
                ob=box(f'{name}_roof_plant_{i}_{u}_STUDY',
                    (x+dx+u*sx*.18,y+dy,roof+.85),(2.5,3.4,1.7),col,glazing)
                ob['confidence']='unsurveyed generic service enclosure'


def plaza_tiles():
    """Every paver is its own Blender object and its own mesh datablock."""
    col=group('PLAZA_individual_tile_meshes_STUDY')
    col['source']='NIST NCSTAR 1-1 sec 2.1 confirms five-acre plaza; paver size/material/layout unverified'
    tilemat=mat('plaza_light_paver_STUDY',(.63,.64,.61),0,.72)
    grout=mat('plaza_joint_STUDY',(.22,.24,.23),0,.95)
    tile_size=3.0; count=0
    support_verts=[]; support_faces=[]
    footprints=[(-55,55,33.6,33.6),(55,-55,33.6,33.6)]
    for volume in bpy.data.objects:
        if any(volume.name.startswith(n+'_volume_') for n in ('WTC3_Marriott','WTC4','WTC5','WTC6')):
            footprints.append((volume.location.x,volume.location.y,
                               volume.dimensions.x/2+1.7,volume.dimensions.y/2+1.7))
    for i in range(60):
        x=(i-29.5)*tile_size
        for j in range(50):
            y=(j-24.5)*tile_size
            if any(abs(x-bx)<bw and abs(y-by)<bh for bx,by,bw,bh in footprints): continue
            # Clear the central fountain footprint.
            if x*x+y*y < 8.5*8.5: continue
            ob=box(f'plaza_tile_{i:02d}_{j:02d}',(x,y,PLAZA_Z+.015),(2.94,2.94,.03),col,tilemat)
            ob['mesh_unique']=True
            n=len(support_verts); a=tile_size/2
            support_verts += [(x+dx,y+dy,z) for z in (0,PLAZA_Z-.03)
                              for dx,dy in ((-a,-a),(a,-a),(a,a),(-a,a))]
            support_faces += [tuple(n+k for k in face) for face in
                ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))]
            count+=1
    support_mesh=bpy.data.meshes.new('plaza_podium_with_tower_voids_mesh')
    support_mesh.from_pydata(support_verts,[],support_faces); support_mesh.materials.append(grout)
    support=bpy.data.objects.new('plaza_podium_with_tower_voids_STUDY',support_mesh)
    col.objects.link(support)
    support['confidence']='grid support proxy; excludes tower footprints to preserve concourse/lobby interior'
    col['actual_tile_mesh_count']=count
    col['status']='separate unique meshes; 3 m square demonstration grid, not surveyed historic pavers'
    return count


def plaza_globe_proxy():
    """Scale marker for Koenig's Sphere; deliberately generic, not a replica."""
    col=group('PLAZA_globe_and_fountain_SCALE_PROXY')
    col['source']='Smithsonian Art Inventories 302674; 9/11 Memorial collection 20476'
    col['rights']='Original Koenig sculpture copyright not cleared; generic sphere only'
    bronze=mat('bronze_globe_proxy_STUDY',(.46,.28,.12),.72,.27)
    granite=mat('fountain_black_granite_STUDY',(.025,.03,.034),.18,.17)
    water=mat('fountain_water_STUDY',(.07,.18,.22),.4,.12)
    # Source: sculpture about 25 ft high, 15 ft diameter; pedestal split unverified.
    sphere_r=7.5*FT
    plinth_h=25*FT-2*sphere_r
    paving=bpy.data.materials.get('plaza_light_paver_STUDY') or granite
    cylinder('fountain_podium_support_STUDY',(0,0,PLAZA_Z/2),10.5,PLAZA_Z,col,paving,64)
    cylinder('round_fountain_basin_STUDY',(0,0,PLAZA_Z+.18),7.0,.36,col,granite,64)
    cylinder('water_surface_STUDY',(0,0,PLAZA_Z+.39),6.45,.035,col,water,64)
    cylinder('globe_plinth_STUDY',(0,0,PLAZA_Z+plinth_h/2),1.0,plinth_h,col,granite,32)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=sphere_r,
                                          location=(0,0,PLAZA_Z+plinth_h+sphere_r))
    ob=bpy.context.object; ob.name='generic_15ft_globe_mass_proxy_NOT_Koenig_replica'
    for old in tuple(ob.users_collection): old.objects.unlink(ob)
    col.objects.link(ob); ob.data.materials.append(bronze)
    for face in ob.data.polygons: face.use_smooth=True
    ob['sourced_bounds']='approx 25 ft overall height; 15 ft diameter, Smithsonian Art Inventories'
    ob['geometry']='generic icosphere, deliberately distinct from original artwork'
    for angle in (0,math.pi/3,2*math.pi/3):
        bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=6,
            location=(0,0,PLAZA_Z+plinth_h+sphere_r),
            major_radius=sphere_r*1.004,minor_radius=.035)
        ring=bpy.context.object; ring.name=f'generic_globe_orbit_{angle:.2f}_STUDY'
        for old in tuple(ring.users_collection): old.objects.unlink(ring)
        col.objects.link(ring); ring.rotation_euler=(math.pi/2,0,angle)
        ring.data.materials.append(bronze)
    return col


def antenna_detail(tower_xy,roof):
    x,y=tower_xy
    col=group('WTC1_antenna_lattice_STUDY')
    col['source']='NIST NCSTAR 1 says approx 360 ft mast; all other geometry estimated'
    steel=mat('antenna_steel_STUDY',(.46,.49,.51),.55,.4)
    red=mat('aviation_marking_STUDY',(.62,.08,.06),.25,.3)
    h=360*FT
    col['confidence']='mast height sourced; taper, tier count, member sizes, transmitters and marks inferred'
    box('antenna_foundation_STUDY',(x,y,roof+.75),(6.0,6.0,1.5),col,steel)
    tiers=14
    for k in range(tiers):
        z0=roof+k*h/tiers; z1=roof+(k+1)*h/tiers
        r0=2.25-1.9*k/tiers; r1=2.25-1.9*(k+1)/tiers
        for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1)):
            strut(f'antenna_leg_{k}_{sx}_{sy}_STUDY',
                  (x+sx*r0,y+sy*r0,z0),(x+sx*r1,y+sy*r1,z1),.13,col,steel)
        corners=[(-1,-1),(1,-1),(1,1),(-1,1)]
        for edge in range(4):
            a,b=corners[edge],corners[(edge+1)%4]
            strut(f'antenna_crossbar_{k}_{edge}_STUDY',
                  (x+a[0]*r0,y+a[1]*r0,z0),(x+b[0]*r0,y+b[1]*r0,z0),.10,col,red if k%4==0 else steel)
            strut(f'antenna_diagonal_{k}_{edge}_STUDY',
                  (x+a[0]*r0,y+a[1]*r0,z0),(x+b[0]*r1,y+b[1]*r1,z1),.075,col,steel)
    # Self-contained central transmission mast and simple service platform.
    cylinder('antenna_central_mast_STUDY',(x,y,roof+h/2),.20,h,col,steel,12)
    cylinder('antenna_tip_beacon_STUDY',(x,y,roof+h-.18),.25,.36,col,red,12)
    for k in (3,7,11):
        z=roof+k*h/tiers
        cylinder(f'antenna_transmitter_radome_{k}_STUDY',(x,y,z),.65,1.8,col,steel,16)


def build_completion(roofs,clad,glass):
    tower_completion('WTC1',(-55,55),roofs['WTC1'],clad,glass)
    tower_completion('WTC2',(55,-55),roofs['WTC2'],clad,glass)
    lowrise_context()
    count=plaza_tiles()
    plaza_globe_proxy()
    antenna_detail((-55,55),roofs['WTC1'])
    return count
