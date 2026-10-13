"""Independent, evidence-scoped context assets for the 2001 WTC study."""
import math
import bpy

FT = 0.3048


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def wtc7_massing(center=(-20, 175)):
    """NIST NCSTAR 1A trapezoid dimensions; placement is unsurveyed staging."""
    north, south, west, east = (329*FT, 247*FT, 153*FT, 149*FT)
    a = ((north-south)**2 + west**2 - east**2)/(2*(north-south))
    b = north-south-a
    depth = math.sqrt(west**2-a**2)
    x, y = center
    xy = [(x-north/2,y+depth/2), (x+north/2,y+depth/2),
          (x+north/2-b,y-depth/2), (x-north/2+a,y-depth/2)]
    roof=610*FT
    verts=[(px,py,z) for z in (0,roof) for px,py in xy]
    faces=[(3,2,1,0),(4,5,6,7)] + [(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
    mesh=bpy.data.meshes.new('WTC7_NIST_trapezoid_mesh')
    mesh.from_pydata(verts,[],faces)
    mat=bpy.data.materials.new('WTC7_neutral_massing_material')
    mat.diffuse_color=(.32,.23,.20,1)
    mat.use_nodes=True
    mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.32,.23,.20,1)
    mesh.materials.append(mat)
    col=collection('WTC7__NIST_massing_position_schematic')
    ob=bpy.data.objects.new('WTC7_47_story_envelope',mesh)
    col.objects.link(ob)
    glass=bpy.data.materials.new('WTC7_glazing_color_STUDY'); glass.use_nodes=True
    glass.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.08,.14,.17,1)
    glass.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.3
    glass.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.22
    for face in range(4):
        a,b=xy[face],xy[(face+1)%4]
        vx,vy=b[0]-a[0],b[1]-a[1]; length=math.hypot(vx,vy)
        nx,ny=-vy/length,vx/length
        verts=[]; faces=[]
        for level in range(1,47):
            z=level*roof/47; n=len(verts)
            verts += [(a[0]+nx*.04,a[1]+ny*.04,z-.8),(b[0]+nx*.04,b[1]+ny*.04,z-.8),
                      (b[0]+nx*.04,b[1]+ny*.04,z+.8),(a[0]+nx*.04,a[1]+ny*.04,z+.8)]
            faces.append(tuple(range(n,n+4)))
        m=bpy.data.meshes.new(f'WTC7_face{face}_glazing_bands_mesh')
        m.from_pydata(verts,[],faces); m.materials.append(glass)
        o=bpy.data.objects.new(f'WTC7_face{face}_glazing_bands_STUDY',m); col.objects.link(o)
        o['confidence']='facade bands and material estimated; 47 stories and overall envelope sourced'
    col['source']='NIST NCSTAR 1A sec 1.2.3: north 329 ft, south 247 ft, width about 144 ft, height 610 ft'
    col['limits']='shape dimensions sourced; map position, exact face offsets, glazing, podium and roof details not surveyed'
    return col


def antenna_height_datum(tower_xy, roof):
    """A conspicuously plain measured-height proxy, not antenna fabrication geometry."""
    col=collection('WTC1_ANTENNA__height_datum_only')
    x,y=tower_xy
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.45, depth=360*FT,
                                         location=(x,y,roof+180*FT))
    ob=bpy.context.object
    ob.name='WTC1_antenna_360ft_height_proxy'
    for c in tuple(ob.users_collection): c.objects.unlink(ob)
    col.objects.link(ob)
    mat=bpy.data.materials.new('measurement_proxy_orange')
    mat.diffuse_color=(.76,.34,.12,1)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(.76,.34,.12,1)
    bsdf.inputs['Emission Color'].default_value=(.76,.20,.04,1)
    bsdf.inputs['Emission Strength'].default_value=.4
    ob.data.materials.append(mat)
    ob['source']='NIST NCSTAR 1-5A vol 1 sec 4.2.1, approximately 360 ft tall'
    ob['limits']='radius and shape invented solely to display height; NOT a reconstructed mast'
    return col


def program_metadata():
    """Inventory documented uses without inventing room or MEP geometry."""
    programs={
      'LOBBY_1_2': 'Concourse through 6: six-story lobby (NIST NCSTAR 1 Table 1-1)',
      'SKY_LOBBY_44_78': '44 and 78: sky lobbies in both towers (NIST NCSTAR 1 Table 1-1)',
      'MEP_7_8_41_42_75_76_108_109': 'paired mechanical levels (NIST NCSTAR 1 Table 1-1)',
      'WTC1_107_RESTAURANT': 'Windows on the World restaurant (NIST NCSTAR 1 Table 1-1)',
      'WTC2_107_ROOF_OBSERVATION': 'indoor 107 and roof outdoor observation decks (NIST NCSTAR 1 Table 1-1)',
      'CONCOURSE_PATH': 'concourse and PATH are documented; floor plans require separate geometry tracing',
    }
    for name,source in programs.items():
        col=collection(name+'__program_reference')
        col['program_source']=source
        col['status']='program reference; inspect detailed CG modules and their confidence tags'
