"""User-photo lower facade: three folded crests, nested frames and grooved transoms.

Visible aluminum finishes / glazing frames are distinguished from the hidden
structural steel study. Profile dimensions are fitted, not fabrication sizes.
User photographs remain outside the project and are not redistributed.
"""
import math,re
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from .completion import PLAZA_Z,FORK_START,FORK_END,TREE_TOP,TREE_SPLICE
from .facade_revision import _mesh,_box_mesh,_face_object,_prism_profile
from .south_roof_revision import material
from .lobby_plan_revision import well,Builder

VERSION='2026-10-15-independent-crests-thicker-lintel-v4'
SOURCE='User reference Image1 OIP.NQM18ZsIccvaLpnLSnItdwHaNH.webp; Image2 23c07deae31fd011a078f00472a7652e3493122703100439.jpg'
RIDGE=.035;CENTER_RIDGE=.016;STEM_RIB_OFFSET=.18;RIB_HALF_WIDTH=.08;CREST_HALF_WIDTH=.0127


def branch(z):
    t=max(0,min(1,(z-FORK_START)/(FORK_END-FORK_START)))
    smooth=t*t*(3-2*t)
    return 1.016*smooth,.4+(.2286-.4)*smooth


def _ccw(loop):
    return loop if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(loop,loop[1:]+loop[:1]))>0 else loop[::-1]


def body_mesh(metal):
    heights=[PLAZA_Z,FORK_START]+[FORK_START+(FORK_END-FORK_START)*i/24 for i in range(1,25)]+[TREE_TOP]
    coords=[];regions=[];edges=[]
    for sign in (-1,0,1):
        path=[(sign*branch(z)[0],z) for z in heights]
        outline=[(u+branch(z)[1],z) for u,z in path]+[(u-branch(z)[1],z) for u,z in path[::-1]]
        outline=_ccw(outline);regions.append(list(range(len(coords),len(coords)+len(outline))));coords.extend(Vector(p) for p in outline)
    points,_,faces,_,_,orig=delaunay_2d_cdt(coords,edges,regions,0,1e-7,True)
    faces=[list(f) for f,ids in zip(faces,orig) if ids]
    used=sorted({i for f in faces for i in f});mapping={old:new for new,old in enumerate(used)}
    points=[points[i] for i in used];faces=[[mapping[i] for i in f] for f in faces]
    n=len(points);v=[(p.x,-.25,p.y-PLAZA_Z) for p in points]+[(p.x,.25,p.y-PLAZA_Z) for p in points]
    polys=[tuple(f) for f in faces]+[tuple(n+i for i in f[::-1]) for f in faces]
    counts={};dirs={}
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            key=tuple(sorted((a,b)));counts[key]=counts.get(key,0)+1;dirs[key]=(a,b)
    for key,count in counts.items():
        if count==1:
            a,b=dirs[key];polys.append((b,a,a+n,b+n))
    m=bpy.data.meshes.new('BASE_trident_body_without_crests');m.from_pydata(v,[],polys);m.materials.append(metal)
    m['source']=SOURCE;m['confidence']='Trident body; three raised crests are separate closed parts. Silhouette and0.50m body depth are CG fits.'
    return m


def crest_mesh(sign,metal):
    heights=[PLAZA_Z,FORK_START]+[FORK_START+(FORK_END-FORK_START)*i/24 for i in range(1,25)]+[TREE_TOP]
    height=CENTER_RIDGE if sign==0 else RIDGE
    section=((-RIB_HALF_WIDTH,0),(-CREST_HALF_WIDTH,height),(0,height),(CREST_HALF_WIDTH,height),(RIB_HALF_WIDTH,0))
    v=[];f=[];n=len(section)
    for z in heights:
        t=max(0,min(1,(z-FORK_START)/(FORK_END-FORK_START)));e=t*t*(3-2*t)
        u=sign*(STEM_RIB_OFFSET+(1.016-STEM_RIB_OFFSET)*e)
        v.extend((u+x,-.25-relief,z-PLAZA_Z) for x,relief in section)
    for j in range(len(heights)-1):
        for k in range(n):f.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
    f.extend((tuple(range(n-1,-1,-1)),tuple((len(heights)-1)*n+k for k in range(n))))
    m=bpy.data.meshes.new(f'BASE_crest_profile_{sign}');m.from_pydata(v,[],f);m.materials.append(metal)
    m['source']=SOURCE;m['confidence']='Independent closed positive folded crest, not a cut groove;outer35mm/middle16mm CG fits'
    return m


def frame_path(sign,start):
    zs=[start,FORK_START]+[FORK_START+(FORK_END-FORK_START)*i/24 for i in range(1,25)]+[TREE_TOP]
    zs=sorted(set(z for z in zs if z>=start))
    return [(sign*(1.524-branch(z)[0]-branch(z)[1]-.025),z) for z in zs]


def secondary_mesh(sign,start,metal):
    path=frame_path(sign,start);w=.0254
    polygon=[(u+w/2,z) for u,z in path]+[(u-w/2,z) for u,z in path[::-1]]
    v=[];f=[];_prism_profile(v,f,_ccw(polygon),.045)
    return _mesh(('base_secondary_curve',sign,start),v,f,metal)


def channel_mesh(length,height,metal,dark):
    # Separate lips with a recessed web: the horizontal slot is an actual void
    # ahead of the web, not a painted stripe or bump-only surrogate.
    from .facade_detail import append_box
    v=[];f=[];gap=.018
    for s in (-1,1):append_box(v,f,(0,-.020,s*(gap/2+(height-gap)/4)),(length,.035,(height-gap)/2))
    front_faces=len(f)
    append_box(v,f,(0,.01475,0),(length,.0345,height))
    m=_mesh(('base_horizontal_channel',round(length,6),height),v,f,metal)
    if len(m.materials)==1:m.materials.append(dark)
    for p in list(m.polygons)[front_faces:]:p.material_index=1
    m['physical_horizontal_slot_m']=gap;m['slot_depth_estimated_m']=.0345
    return m


def waisted_lintel_mesh(metal):
    """First-floor head beam: paired bowed edges, thicker at each pier.

    This is the visible facing, not an assertion about the hidden steel section.
    The user's facade photo establishes the waist; dimensions are CG fits.
    """
    half=1.524-.4-.025
    xs=[-half+2*half*i/48 for i in range(49)]
    def h(x):return .12+.22*(x/half)**2
    outline=[(x,h(x)) for x in xs]+[(x,-h(x)) for x in xs[::-1]]
    v=[];f=[];_prism_profile(v,f,_ccw(outline),.18)
    m=_mesh('first_floor_thicker_paired_curve_waisted_lintel',v,f,metal)
    m['source']=SOURCE;m['confidence']='Paired bowed edges visible in user exterior photo;user-requested thicker profile0.24m middle/0.68m ends,0.18m depth;all CG fits'
    return m


def first_floor_lintels(tower,xy,col,metal):
    # Replace the previously misidentified straight door-height transoms.
    retired=[o for o in col.objects if re.fullmatch(tower+r'_BASE_S\d_B\d+_transom1',o.name) or o.get('module') in ('first_floor_waisted_lintel','entry_glazing_headrail')]
    if retired:bpy.data.batch_remove(ids=retired)
    mesh=waisted_lintel_mesh(metal)
    for side in range(4):
        for bay in range(18):
            p=(bay-8.5)*3.048
            data=mesh.copy();data.name=f'{tower}_BASE_S{side}_B{bay}_lintel_mesh'
            ob=_face_object(f'{tower}_BASE_S{side}_B{bay}_first_floor_waisted_lintel',data,xy,side,31.69,PLAZA_Z+3.03,col,p)
            ob['module']='first_floor_waisted_lintel';ob['hierarchy_level']=2
            ob['source']=SOURCE;ob['confidence']=mesh['confidence'];ob['base_frame_revision']=VERSION
    # Door leaf head rails remain straight below the bowed beam. Retire the
    # old continuous rectangular header, which would conceal the waist.
    old=bpy.data.objects.get(tower+'_LP_entry_header')
    if old:old.hide_render=True;old.hide_viewport=True;old['superseded_by']=VERSION
    side=1 if tower=='WTC1' else 2
    for bay in (7,8,9,10):
        ob=_face_object(f'{tower}_BASE_entry_headrail_{bay}',_box_mesh((2.56,.09,.06),metal),xy,side,31.5662,PLAZA_Z+2.62,col,(bay-8.5)*3.048)
        ob['module']='entry_glazing_headrail';ob['source']=SOURCE;ob['confidence']='Straight door-frame head below curved lintel;60mm CG fit'


def nested_frames(tower,xy,col,metal,dark):
    for side in range(4):
        for bay in range(18):
            p=(bay-8.5)*3.048
            entry=(side==(1 if tower=='WTC1' else 2) and bay in (7,8,9,10))
            start=PLAZA_Z+2.65 if entry else .24
            for sign in (-1,1):
                ob=_face_object(f'{tower}_BASE_S{side}_B{bay}_secondary_arch{sign}',secondary_mesh(sign,start,metal),xy,side,31.70,0,col,p)
                ob['module']='secondary_lower_arch_frame';ob['hierarchy_level']=2;ob['bay']=bay;ob['face']=side
            half=1.524-.4-.025
            for level,z in enumerate((PLAZA_Z,PLAZA_Z+2.65,TREE_SPLICE)):
                if level==1:continue
                if entry and level<2:continue
                ob=_face_object(f'{tower}_BASE_S{side}_B{bay}_transom{level}',channel_mesh(half*2,.16,metal,dark),xy,side,31.69,z,col,p)
                ob['module']='grooved_horizontal_transom';ob['hierarchy_level']=2;ob['slot_height_estimated_m']=.018;ob['slot_depth_estimated_m']=.0345
            top=TREE_SPLICE-.08
            if top>start:
                ob=_face_object(f'{tower}_BASE_S{side}_B{bay}_inner_mullion',_box_mesh((.025,.025,top-start),metal),xy,side,31.645,(top+start)/2,col,p)
                ob['module']='tertiary_glazing_mullion';ob['hierarchy_level']=3
            # Beads nest inside each half-pane below the tree fork.
            for layer,(a,b) in enumerate(zip((start,PLAZA_Z,PLAZA_Z+2.65),(PLAZA_Z,PLAZA_Z+2.65,TREE_SPLICE))):
                if b<=a+.1 or (entry and a<start):continue
                for halfsign in (-1,1):
                    center=p+halfsign*half/2;pw=half-.08;ph=b-a-.15
                    for edge in (-1,1):
                        ob=_face_object(f'{tower}_BASE_S{side}_B{bay}_inner_bead{layer}_{halfsign}_{edge}',_box_mesh((pw,.012,.012),metal),xy,side,31.625,(a+b)/2+edge*ph/2,col,center)
                        ob['module']='tertiary_glazing_bead';ob['hierarchy_level']=3
    for ob in col.objects:
        ob['source']=SOURCE;ob['confidence']='Photographic nested-frame hierarchy; small dimensions and transom placement estimated; visible finish/frame, not structural fabrication';ob['base_frame_revision']=VERSION


def balcony_fascia(tower,xy,metal,dark):
    col=bpy.data.collections[tower+'_LOBBY_curved_mezzanine_and_entrances_STUDY'];angle=0 if tower=='WTC1' else math.pi/2
    b=Builder(tower,xy,angle,col);stone=bpy.data.materials[tower+'_warm_pale_stone_STUDY']
    for sign in (-1,1):
        path=well(sign)
        for j,(a,c) in enumerate(zip(path,path[1:])):
            a,c=Vector(a),Vector(c);d=c-a;normal=sign*Vector((d.y,-d.x)).normalized()
            # Face into the well. Four closed facing bands leave three physical
            # shallow horizontal reveals over a recessed backing web.
            center=(a+c)/2-normal*.025
            ob=b.box(f'curved_edge_beam_{sign}_{j}',(*center,PLAZA_Z-.26),(d.length+.002,.035,.52),dark);ob.rotation_euler.z=angle+math.atan2(d.y,d.x)
            ob['module']='balcony_edge_beam';ob['source']=SOURCE;ob['confidence']='User interior photo deep curved fascia;520mm CG depth, not a measured structural section'
            band=(.52-3*.006)/4
            for strip in range(4):
                q=center+normal*.030
                zz=PLAZA_Z-.52+(strip+.5)*band+strip*.006
                ob=b.box(f'fascia_facing_band_{sign}_{j}_{strip}',(*q,zz),(d.length+.002,.025,band),stone);ob.rotation_euler.z=angle+math.atan2(d.y,d.x)
                ob['module']='balcony_fascia_grooved_facing';ob['source']=SOURCE;ob['physical_slot_height_estimated_m']=.006



def apply():
    scene=bpy.context.scene
    if scene.get('base_frame_revision')==VERSION:return
    metal=bpy.data.materials['silver_cladding_color_study']
    frame=material('BASE_brushed_frame_aluminum',(.55,.58,.57),.82,.3)
    dark=material('BASE_recessed_track_shadow',(.12,.14,.14),.55,.5)
    prototype=body_mesh(metal)
    crests={sign:crest_mesh(sign,metal) for sign in (-1,0,1)}
    for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):
        col=bpy.data.collections.get(tower+'_BASE_nested_frames_and_transoms_STUDY')
        if col is None:
            col=bpy.data.collections.new(tower+'_BASE_nested_frames_and_transoms_STUDY');bpy.data.collections[tower].children.link(col)
            col.asset_mark();col.asset_data.description='User-photo nested lower frames, mullions, true grooved transoms; fitted profiles';col.instance_offset=(*xy,0)
            col['source']=SOURCE;col['confidence']='Photo-fitted secondary/tertiary finish framing; unknown fabrication sizes'
            nested_frames(tower,xy,col,frame,dark)
            balcony_fascia(tower,xy,frame,dark)
        retired=[o for o in col.objects if o.get('module')=='base_positive_crest']
        if retired:bpy.data.batch_remove(ids=retired)
        trees=[o for o in bpy.data.objects if re.fullmatch(tower+r'_tree_s\d_\d+',o.name)]
        for ob in trees:
            ob.data=prototype.copy();ob.data.name=ob.name+'_body_mesh';ob.modifiers.clear()
            ob['separate_three_crests']=True;ob['source_profile']=SOURCE
            for key in ('integral_recessed_track','integral_three_crests'):
                if key in ob:del ob[key]
            ob['profile_confidence']='Independent body and three unique crest meshes;outer35mm/middle16mm, each follows one branch;CG fitted sizes'
            for sign,label in ((-1,'left'),(0,'middle'),(1,'right')):
                data=crests[sign].copy();data.name=ob.name+'_crest_'+label+'_mesh'
                part=bpy.data.objects.new(ob.name+'_crest_'+label,data);col.objects.link(part);part.matrix_world=ob.matrix_world.copy()
                part['module']='base_positive_crest';part['base_column']=ob.name;part['branch_index']=sign
                part['source']=SOURCE;part['confidence']=data['confidence'];part['base_frame_revision']=VERSION
        first_floor_lintels(tower,xy,col,frame)
        col['base_frame_revision']=VERSION
    scene['base_frame_revision']=VERSION
