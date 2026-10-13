"""Segmented steel, separate grooved covers, continuous glazing and mitered roofs.

NCSTAR 1 Fig5-6 supplies 18-inch aluminum cover and a rectangular center recess.
Slot, wall and fastener dimensions below remain editable CG assumptions.
"""
import bpy, math
from mathutils import Vector
FT=.3048
REFERENCE_HALF=(207+2/12)*FT/2
OUTER_HALF=(208+10/12)*FT/2
CHAMFER=(6+11/12)*FT
COVER_WIDTH=18/12*FT
STEEL_WIDTH=14/12*FT
TREE_TOP=(418+11.5/12-310)*FT
TOP_DEPTH=36*FT
CACHE={}

def child(root,name):
    c=bpy.data.collections.new(name);root.children.link(c);return c

def material(name,color,metal=.7,rough=.3):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    return m

def object_mesh(name,mesh,loc,col,rotation=0,hidden=False):
    ob=bpy.data.objects.new(name,mesh);col.objects.link(ob);ob.location=loc;ob.rotation_euler.z=rotation
    if hidden:ob.hide_render=True
    return ob

def append_box(v,f,center,size):
    n=len(v);a,b,c=(s/2 for s in size);x,y,z=center
    v.extend([(x+dx,y+dy,z+dz) for dx,dy,dz in
              ((-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c))])
    f.extend([tuple(n+i for i in q) for q in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))])

def steel_mesh(height,material,width=STEEL_WIDTH,connections=True):
    key=('steel',round(height,6),width,connections)
    if key in CACHE:return CACHE[key]
    t=.0254;h=width/2;i=h-t
    outer=[(-h,-h),(h,-h),(h,h),(-h,h)];inner=[(-i,-i),(i,-i),(i,i),(-i,i)]
    v=[(x,y,z) for z in (0,height) for x,y in outer+inner];f=[]
    for k in range(4):
        j=(k+1)%4
        f.extend(((k,j,j+8,k+8),(k+4,k+12,j+12,j+4),
                  (k,k+4,j+4,j),(k+8,j+8,j+12,k+12)))
    if connections:
        # Sourced end-plate range 1.375–3in; minimum used as a type proxy.
        plate=1.375*.0254
        append_box(v,f,(0,0,height-plate/2),(width,width,plate))
        for side in (-1,1):
            append_box(v,f,(side*(h+.008),0,height),(.016,width*.78,.32))
            for yy in (-width*.22,width*.22):
                for zz in (height-.09,height+.09):
                    append_box(v,f,(side*(h+.021),yy,zz),(.025,.033,.033))
    m=bpy.data.meshes.new('steel_box_segment_type');m.from_pydata(v,[],f);m.materials.append(material)
    m['splices_cross_joint']=connections;CACHE[key]=m
    return m

def typical_panel_sample():
    existing=bpy.data.collections.get('WTC_TYPICAL_STEEL_PANEL_STUDY')
    if existing:return existing
    col=bpy.data.collections.new('WTC_TYPICAL_STEEL_PANEL_STUDY')
    bpy.context.scene.collection.children.link(col);col.hide_render=True
    col['source']='NIST1-1 Fig2-9: 10ft x36ft, 3 columns x3 stories,52in spandrels'
    col['confidence']='dimensioned type sample; wall/bolt gauges and within-panel elevations inferred'
    metal=bpy.data.materials['structural_steel_unclad_STUDY']
    for axis in (-1,0,1):
        object_mesh(f'TYPE_PANEL_steel_column_{axis}',steel_mesh(36*FT,metal),(245+axis*40/12*FT,-140,0),col)
    v=[];f=[];append_box(v,f,(0,0,0),(10*FT,.0254,52/12*FT))
    m=bpy.data.meshes.new('TYPE_PANEL_spandrel_mesh');m.from_pydata(v,[],f);m.materials.append(metal)
    for level in range(3):object_mesh(f'TYPE_PANEL_spandrel_{level}',m,(245,-140,(level+.5)*12*FT),col)
    col.asset_mark();col.asset_data.description=col['confidence'];col.instance_offset=(245,-140,0)
    return col

def cover_mesh(height,material):
    key=('cover',round(height,6))
    if key in CACHE:return CACHE[key]
    w=COVER_WIDTH/2;front=OUTER_HALF-REFERENCE_HALF;back=-.205
    slot=.04;depth=.03;t=.003  # drawn feature, dimensions not supplied by NIST
    p=[(-w,back),(-w,front),(-slot/2,front),(-slot/2,front-depth),
       (slot/2,front-depth),(slot/2,front),(w,front),(w,back),
       (w-t,back),(w-t,front-t),(slot/2+t,front-t),(slot/2+t,front-depth-t),
       (-slot/2-t,front-depth-t),(-slot/2-t,front-t),(-w+t,front-t),(-w+t,back)]
    n=len(p);v=[(x,-y,z) for z in (0,height) for x,y in p]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
    m=bpy.data.meshes.new('18in_grooved_aluminum_cover_segment');m.from_pydata(v,[],f);m.materials.append(material);CACHE[key]=m
    return m

def outline(half,offset=0):
    c=CHAMFER+offset*(2-math.sqrt(2))
    h=half
    return [(-h+c,-h),(h-c,-h),(h,-h+c),(h,h-c),(h-c,h),(-h+c,h),(-h,h-c),(-h,-h+c)]

def prism(name,pts,z0,z1,col,mat,xy=(0,0)):
    n=len(pts);m=bpy.data.meshes.new(name+'_mesh')
    m.from_pydata([(x,y,z) for z in (z0,z1) for x,y in pts],[],
                 [tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+
                 [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)])
    m.materials.append(mat);return object_mesh(name,m,(*xy,0),col)

def glazing_ring(name,z0,z1,col,mat,xy):
    outer=outline(REFERENCE_HALF-.006,-.006);inner=outline(REFERENCE_HALF-.026,-.026)
    v=[(x,y,z) for z in (z0,z1) for ring in (outer,inner) for x,y in ring];f=[]
    for k in range(8):
        j=(k+1)%8
        f.extend(((k,j,j+16,k+16),(k+8,k+24,j+24,j+8),
                  (k,k+8,j+8,j),(k+16,j+16,j+24,k+24)))
    m=bpy.data.meshes.new(name+'_mesh');m.from_pydata(v,[],f);m.materials.append(mat)
    ob=object_mesh(name,m,(*xy,0),col)
    ob['confidence']='continuous 8-sided glazed closure; glass thickness and top opening elevations are CG estimates'
    ob['source']='NIST NCSTAR1 Fig5-6 glass/steel/cover relationship; 1-1 Fig2-3 footprint'
    return ob

def face_xy(xy,side,p):
    x,y=xy;q=REFERENCE_HALF
    return ((x+p,y-q),(x+q,y+p),(x-p,y+q),(x-q,y-p))[side]

def segmented_tower(name,xy,roof):
    root=bpy.data.collections[name]
    col=next(c for c in root.children if c.name.startswith('02_perimeter'))
    steel=child(col,name+'_segmented_structural_steel');covers=child(col,name+'_separate_grooved_aluminum_covers')
    steel.hide_render=True
    steel['source']='NIST NCSTAR1-1 Figs2-9/2-10: 3-column/3-story panels, staggered joints; butt and double splice plates'
    steel['confidence']='floor/splice datums interpolated; steel wall, bolts and plate schedules unverified'
    covers['source']='NIST NCSTAR1 p72 Fig5-6: 18in aluminum cover, rectangular middle recess'
    covers['confidence']='recess width/depth and aluminum gauge estimated; section feature is sourced'
    metal=material('structural_steel_unclad_STUDY',(.16,.18,.19),.65,.4)
    aluminum=bpy.data.materials['silver_cladding_color_study']
    top=roof-TOP_DEPTH;pitch=(top-TREE_TOP)/98
    for ob in list(col.objects):
        if ('_column' in ob.name and '_face' in ob.name) or '_floor_band_' in ob.name:
            bpy.data.objects.remove(ob,do_unlink=True)
    for side in range(4):
        for axis in range(59):
            p=(axis-29)*40/12*FT;loc=face_xy(xy,side,p)
            phase=((axis//3)%3)*pitch
            joints={TREE_TOP,top}
            for k in range(-1,36):
                z=TREE_TOP+phase+k*3*pitch
                if TREE_TOP<z<top:joints.add(z)
            for level in (41,42,75,76):joints.add(TREE_TOP+(level-9)*pitch)
            edges=sorted(joints)
            for s,(a,b) in enumerate(zip(edges,edges[1:])):
                length=b-a
                ob=object_mesh(f'{name}_face{side+1}_axis{axis:02d}_seg{s:03d}_steel',
                    steel_mesh(length,metal),(*loc,a),steel,side*math.pi/2)
                ob['module']='steel_column';ob['zone']='regular';ob['face']=side+1;ob['axis_index']=axis;ob['segment_index']=s
                ob['panel_group']=axis//3;ob['source']='NIST1-1 Fig2-9/2-10';ob['confidence']='3-story panel logic; actual story heights and joints inferred'
                cover=object_mesh(ob.name.replace('_steel','_aluminum_cover'),cover_mesh(max(.01,length-.008),aluminum),
                                  (*loc,a+.004),covers,side*math.pi/2)
                cover['module']='aluminum_cover';cover['axis_index']=axis;cover['face']=side+1
                cover['source']='NIST NCSTAR1 Fig5-6';cover['confidence']='18in width sourced; recess .04x.03m and 3mm gauge estimated'
        # Separate panel-width spandrels instead of one whole-building bar.
        for level in range(98):
            z=TREE_TOP+(level+.5)*pitch
            for group in range(20):
                low=max(-29*40/12*FT,(group*3-29-.5)*40/12*FT)
                high=min(29*40/12*FT,(group*3-29+2.5)*40/12*FT)
                if high<=low:continue
                loc=face_xy(xy,side,(low+high)/2)
                v=[];f=[];append_box(v,f,(0,0,0),(high-low,.0254,52/12*FT))
                key=('spandrel',round(high-low,6))
                if key not in CACHE:
                    m=bpy.data.meshes.new('panel_spandrel_plate_mesh');m.from_pydata(v,[],f);m.materials.append(metal);CACHE[key]=m
                ob=object_mesh(f'{name}_face{side+1}_panel{group:02d}_F{level+9}_spandrel_STUDY',CACHE[key],
                               (*loc,z),steel,side*math.pi/2)
                ob['source']='NIST1-1: 10ft panel width, 52in spandrel';ob['confidence']='plate gauge, corner fit and elevations inferred'
    # Split the 47 existing core axes as independent steel segments too.
    completion=bpy.data.collections[name+'_COMPLETION_study']
    core=next(c for c in completion.children if c.name.startswith('47_core_columns'))
    core.hide_render=True
    originals=[o for o in list(core.objects) if o.name.startswith(name+'_core_')]
    for axis,old in enumerate(originals):
        loc=old.location.copy();width=old.dimensions.x
        bpy.data.objects.remove(old,do_unlink=True)
        count=math.ceil(roof/(36*FT))
        for s in range(count):
            a=s*36*FT;b=min(roof,a+36*FT)
            ob=object_mesh(f'{name}_core_axis{axis:02d}_seg{s:03d}_steel_STUDY',steel_mesh(b-a,metal,width),
                           (loc.x,loc.y,a),core)
            ob['module']='core_steel_column';ob['axis_index']=axis;ob['confidence']='47 axes preserved; location/section and nominal 36ft splice schedule schematic'
    # Correct glass reference plane and pane width to clear the 18-inch cover.
    shell=next(c for c in root.children if c.name.startswith('01_envelope'))
    for o in list(shell.objects):bpy.data.objects.remove(o,do_unlink=True)
    normal=bpy.data.materials['blue_gray_glazing_color_study']
    body=glazing_ring(name+'_envelope_208ft10in',TREE_TOP,roof-TOP_DEPTH,shell,normal,xy)
    body['source']='NIST1-1 207ft2in reference lines; glazing plane inferred from NCSTAR1 Fig5-6'
    lobby=material(name+'_lobby_glass_translucent_STUDY',(.16,.23,.26),.05,.12)
    p=lobby.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=.34
    if hasattr(lobby,'surface_render_method'):
        try:lobby.surface_render_method='BLENDED'
        except (TypeError,ValueError):lobby.surface_render_method='DITHERED'
    glazing_ring(name+'_concourse_to_tree_glass_STUDY',0,TREE_TOP,shell,lobby,xy)
    glazing_ring(name+'_top_lower_glass_STUDY',roof-TOP_DEPTH,roof-7.7,shell,normal,xy)
    glazing_ring(name+'_top_upper_glass_STUDY',roof-4.7,roof,shell,normal,xy)
    pane_col=next(c for c in root.children if c.name.startswith('06_glazing'))
    for ob in pane_col.objects:
        side=int(ob.name.split('_face')[1][0]);mesh=ob.data
        for face in mesh.polygons:
            points=[mesh.vertices[i] for i in face.vertices]
            axis=0 if side%2==0 else 1
            center=sum(v.co[axis] for v in points)/4
            for v in points:
                v.co[axis]=center+(v.co[axis]-center)*(40/12*FT-COVER_WIDTH)/(40/12*FT-STEEL_WIDTH)
                v.co[1-axis]=(-1 if side in (0,3) else 1)*(REFERENCE_HALF-.004)
    # Roof slab and parapet share the offset chamfered footprint.
    old=bpy.data.objects[name+'_roof_datum'];floor_col=old.users_collection[0]
    bpy.data.objects.remove(old,do_unlink=True)
    pts=outline(OUTER_HALF-.04,OUTER_HALF-.04-REFERENCE_HALF)
    prism(name+'_roof_datum',pts,roof,roof+.4,floor_col,aluminum,xy)
    roofcol=next(c for c in completion.children if c.name.startswith('roof_mechanical'))
    for o in list(roofcol.objects):
        if '_roof_parapet_' in o.name:bpy.data.objects.remove(o,do_unlink=True)
    for edge,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
        dx,dy=b[0]-a[0],b[1]-a[1];v=[];f=[]
        append_box(v,f,(0,0,0),(math.hypot(dx,dy),.25,1.3))
        m=bpy.data.meshes.new(name+f'_parapet{edge}_mesh');m.from_pydata(v,[],f);m.materials.append(aluminum)
        ob=object_mesh(name+f'_roof_parapet_edge{edge}_45deg_STUDY',m,
            (xy[0]+(a[0]+b[0])/2,xy[1]+(a[1]+b[1])/2,roof+.65),roofcol,math.atan2(dy,dx))
        ob['source']='NIST1-1: 6ft11in chamfer; cover offset from 207ft2in to208ft10in';ob['confidence']='parapet section assumed'

def upgrade_facades():
    segmented_tower('WTC1',(-55,55),1368*FT)
    segmented_tower('WTC2',(55,-55),1362*FT)
