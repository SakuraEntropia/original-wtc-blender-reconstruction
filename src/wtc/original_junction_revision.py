"""AB321/323 corner, projection and crown migration. Metres; source tags per part.

Original dimensioned profiles replace the previous generic U jamb and equal
octagonal hood. Roof apex/run and absolute datums remain drawing interpretations,
not an as-built survey. Original scans are references only, never bundled.
"""
import math
import bpy
from mathutils import Vector
from .completion import FT, PLAZA_Z
from .facade_detail import OUTER_HALF, object_mesh, append_box, material
from .facade_revision import (IN, PITCH, COVER, GLASS_Q, _face_object,
                              _mesh, _box_mesh, _prism_profile)
from .crown_edge_revision import mesh, prism, beam

VERSION = '2026-10-14-ab321-ab323-v5'
SOURCE = 'https://www0.ae911truth.org/images/articles/ElectricalDrawings/134_0.png; https://www0.ae911truth.org/images/articles/ElectricalDrawings/135_0.png'
WIDTHS = (.587375, 1.016, .587375)
DIAGONAL = sum(WIDTHS)
LEG = DIAGONAL / math.sqrt(2)
Q = GLASS_Q
END = Q - LEG
AXIS = 29 * PITCH
LIMITS = 'AB321/323 dimensions; thicknesses/fasteners and datum mapping estimated. Apex/run inferred from plan E/F, not verified as built.'


def tag(ob, module, **values):
    ob['module'] = module; ob['source'] = SOURCE
    ob['confidence'] = LIMITS; ob['original_junction_revision'] = VERSION
    for k,v in values.items(): ob[k] = v
    return ob


def clear(col):
    if col.objects: bpy.data.batch_remove(ids=list(col.objects))
    col['source'] = SOURCE; col['confidence'] = LIMITS
    col.hide_render = False; col.hide_viewport = False
    if col.asset_data:col.asset_data.description=LIMITS


def poly_sheet(name, points, normal, col, mat, module, thickness=.003, **tags):
    """Closed independent sheet; geometry lies on the nominal source surface."""
    pts = [Vector(p) for p in points]; normal = Vector(normal).normalized()
    n=len(pts); v=[tuple(p) for p in pts]+[tuple(p-normal*thickness) for p in pts]
    f=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ob=object_mesh(name,mesh(('original_sheet',name),v,f,mat),(0,0,0),col)
    return tag(ob,module,sheet_thickness_m=thickness,**tags)


def profile_mesh(key, pts, height, mat):
    n=len(pts); v=[(x,y,z) for z in (0,height) for x,y in pts]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh((key,round(height,7),tuple(pts)),v,f,mat)


def folded_seam(name, start, end, legs, col, mat, **tags):
    """Two real flanges follow the mating planes; no flat overlapping cover."""
    v=[];f=[]
    for normal,toward in legs:
        cross=(end-start).cross(normal).normalized()
        if cross.dot(toward-(start+end)/2)<0:cross=-cross
        offset=normal*.004;wing=cross*.015
        points=[start+offset,start+offset+wing,end+offset+wing,end+offset]
        if (points[1]-points[0]).cross(points[3]-points[0]).dot(normal)<0:points.reverse()
        n=len(v);v += [tuple(p) for p in points]+[tuple(p-normal*.003) for p in points]
        f += [tuple(n+i for i in face) for face in
              ((0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0))]
    ob=object_mesh(name,mesh(('folded_seam',name),v,f,mat),(0,0,0),col)
    return tag(ob,'original_roof_raked_joint',a_world=tuple(start),b_world=tuple(end),
               seam_cover_width_estimated_m=.030,sheet_thickness_m=.003,folded_flange_count=2,**tags)


def clean_levels(values, lo, hi):
    out=[]
    for z in sorted({lo,hi,*[v for v in values if lo<v<hi]}):
        if not out or z-out[-1]>.001: out.append(z)
    return out


def corners(tower, xy, finish, para, roof, metal):
    col=bpy.data.collections[tower+'_corner_three_panels']
    oldlevels=[]
    for ob in col.objects:
        oldlevels += [ob.location.z-ob.dimensions.z/2-.004,
                      ob.location.z+ob.dimensions.z/2+.004]
    clear(col)
    # H: corner expansion joint is 4ft8in below FIN110. Earlier levels are CG
    # story datums; the source's upper corner panel is a distinct full-height part.
    upper_bottom=finish-(4+8/12)*FT
    lower=clean_levels(oldlevels,PLAZA_Z,upper_bottom)
    levels=lower+[para]
    for side in range(4):
        angle=side*math.pi/2
        def world(p):
            x,y=p;return Vector((xy[0]+x*math.cos(angle)-y*math.sin(angle),
                                 xy[1]+x*math.sin(angle)+y*math.cos(angle)))
        a=world((END,-Q));b=world((Q,-END))
        normal=Vector((math.sin(angle)+math.cos(angle),math.sin(angle)-math.cos(angle),0)).normalized()
        for story,(lo,hi) in enumerate(zip(levels,levels[1:])):
            walked=0
            for panel,w in enumerate(WIDTHS,1):
                t0=(walked+.003)/DIAGONAL;t1=(walked+w-.003)/DIAGONAL
                A=a.lerp(b,t0);B=a.lerp(b,t1);walked+=w
                ob=poly_sheet(f'{tower}_original_corner_E{2*side+1}_story{story:03d}_panel{panel}',
                    [(A.x,A.y,lo+.004),(B.x,B.y,lo+.004),(B.x,B.y,hi-.004),(A.x,A.y,hi-.004)],
                    normal,col,metal,'original_corner_panel',edge=2*side+1,story_index=story,
                    panel_index=panel,nominal_width_m=w,panels_per_story=3,
                    corner_diagonal_m=DIAGONAL,corner_plane_recess_m=11.5*IN)
    col['corner_diagonal_m']=DIAGONAL;col['corner_split_widths_m']=WIDTHS
    return levels


def frames(tower,xy,para,levels,metal,ss,dark):
    col=bpy.data.collections[tower+'_FACADE_corner_transition_frames'];clear(col)
    vals=clean_levels(levels,PLAZA_Z,para)
    # Bottom stories need individually selectable pieces, not one lobby-to-crown bar.
    vals=clean_levels(vals+[PLAZA_Z+i*12*FT for i in range(1,8)],PLAZA_Z,para)
    width=5*IN; projection=7*IN; mouth=.375*IN;gauge=.003
    for j,(lo,hi) in enumerate(zip(vals,vals[1:])):
        h=hi-lo-.008
        if h<.01:continue
        for side in range(4):
            for endsign,axisindex in ((-1,0),(1,58)):
                p=endsign*AXIS
                shared=dict(face=side+1,axis_index=axisindex,piece_index=j,
                            frame_width_m=width,projection_m=projection)
                for half in (-1,1):
                    pts=[(mouth/2,-projection),(width/2,-projection),
                         (width/2,0),(width/2-gauge,0),
                         (width/2-gauge,-projection+gauge),(mouth/2,-projection+gauge)]
                    if half<0:pts=[(-x,y) for x,y in pts][::-1]
                    ob=_face_object(f'{tower}_original_frame_S{side+1}_A{axisindex}_P{j:03d}_AL{half:+d}',
                        profile_mesh(('al_return',half),pts,h,metal),xy,side,OUTER_HALF,lo+.004,col,p)
                    tag(ob,'original_edge_al_return',frame_half=half,**shared)
                    sw=(width-mouth)/2
                    ob=_face_object(f'{tower}_original_frame_S{side+1}_A{axisindex}_P{j:03d}_SS{half:+d}',
                        _box_mesh((sw,.0015,h),ss),xy,side,OUTER_HALF+projection+.00075,
                        (lo+hi)/2,col,p+half*(mouth/2+sw/2))
                    tag(ob,'original_edge_ss_face',frame_half=half,**shared)
                ob=_face_object(f'{tower}_original_frame_S{side+1}_A{axisindex}_P{j:03d}_track',
                    _box_mesh((1.5*IN,.003,h),dark),xy,side,OUTER_HALF+projection-.030,
                    (lo+hi)/2,col,p)
                tag(ob,'original_edge_track',mouth_width_m=mouth,track_depth_estimated_m=.030,**shared)
                # The terminal broad cover returns diagonally toward the inset
                # corner panel, instead of the previous straight generic U jamb.
                e=END-AXIS; r=11.5*IN
                pts=[(COVER/2,0),(e,r),(e-gauge,r),(COVER/2-gauge,gauge)]
                if endsign<0:pts=[(-x,y) for x,y in pts][::-1]
                ob=_face_object(f'{tower}_original_frame_S{side+1}_A{axisindex}_P{j:03d}_corner_fold',
                    profile_mesh(('corner_fold',endsign),pts,h,metal),xy,side,OUTER_HALF,
                    lo+.004,col,p)
                tag(ob,'original_edge_corner_fold',nominal_fold_degrees=45,
                    absolute_plane_placement_estimated=True,**shared)
    col['frame_width_m']=width;col['projection_m']=projection
    col['absolute_plane_residual_m']=.0124


def crown_curves(tower,finish,metal):
    col=bpy.data.collections[tower+'_crown_curved_cladding']
    top=finish+(4+2/12)*FT
    a=col['z_transition_lower_estimated_m'];b=col['z_transition_middle_estimated_m']
    upper=col['upper_transition_height_m'];d=top-upper
    assert d>b
    for ob in col.objects:
        module=ob.get('module')
        if module=='crown_curved_transition' and ob['transition']=='close':
            ob.location.z=d
        elif module=='crown_alternating_cover':
            odd=ob['axis_index']%2==1
            widths=[7*IN if odd else 12*IN,7*IN if odd else 17*IN,
                    7*IN if odd else 17*IN,12*IN]
            heights=[0,b-a,d-a,top-a]
            profile=[(w/2,h) for w,h in zip(widths,heights)]
            profile += [(-w/2,h) for w,h in reversed(list(zip(widths,heights)))]
            v=[];f=[];_prism_profile(v,f,profile,.065)
            ob.data=_mesh(('ab321_alternating',odd,round(top-a,7)),v,f,metal)
        elif module=='crown_mechanical_backing':
            ob.data=_box_mesh((58*PITCH+12*IN,.08,top-a),ob.data.materials[0]);ob.location.z=(a+top)/2
    col['z_transition_upper_estimated_m']=d;col['z_fascia_bottom_inferred_m']=top
    col['central_open_height_estimated_m']=d-b
    col['upper_datum_source']='AB321 elevation/AB323 H,J node correspondence, FIN110+4ft2 inferred; NIST7ft2 curve height retained'
    return top


def hood(tower,xy,finish,para,roof,fascia_bottom,metal,steel):
    col=bpy.data.collections[tower+'_CROWN_CAP_mitered_panels'];clear(col)
    support=bpy.data.collections[tower+'_CROWN_CAP_steel_support_TYPE'];clear(support)
    common=dict(finished110_z=finish,parapet_z=para,paneltop_z=roof,
                datum_mapping_estimated=True,source_geometry_inference=True)
    points=[]
    for side in range(4):
        angle=side*math.pi/2
        def world(p,q,z):
            return Vector((xy[0]+p*math.cos(angle)+q*math.sin(angle),
                           xy[1]+p*math.sin(angle)-q*math.cos(angle),z))
        fieldnormal=(world(1,Q,para)-world(0,Q,para)).cross(world(0,END,roof)-world(0,Q,para)).normalized()
        for j in range(60):
            pa=max(-END,(j-30)*PITCH);pb=min(END,(j-29)*PITCH)
            if pb-pa<.005:continue
            A=world(pa+.0015,Q,para);B=world(pb-.0015,Q,para)
            C=world(pb-.0015,END,roof);D=world(pa+.0015,END,roof)
            normal=(B-A).cross(D-A).normalized()
            poly_sheet(f'{tower}_original_roof_S{side+1}_panel{j:02d}',[A,B,C,D],normal,col,metal,
                       'original_roof_field_panel',edge=2*side,**common)
            # Straight fascia below roof, with an actual separate folded return.
            F=world(pa,OUTER_HALF,fascia_bottom);G=world(pb,OUTER_HALF,fascia_bottom)
            H=world(pb,OUTER_HALF,para);I=world(pa,OUTER_HALF,para)
            poly_sheet(f'{tower}_original_fascia_S{side+1}_panel{j:02d}',[F,G,H,I],
                       world(0,1,0)-Vector((*xy,0)),col,metal,'original_roof_fascia',**common)
            poly_sheet(f'{tower}_original_fascia_return_S{side+1}_panel{j:02d}',
                       [I,H,world(pb,OUTER_HALF-3.5*IN,para),world(pa,OUTER_HALF-3.5*IN,para)],
                       (0,0,1),col,metal,'original_fascia_fold',return_width_m=3.5*IN,**common)
            poly_sheet(f'{tower}_original_fascia_closure_S{side+1}_panel{j:02d}',
                       [world(pa,OUTER_HALF-3.5*IN,para-.002),world(pb,OUTER_HALF-3.5*IN,para-.002),
                        world(pb,Q,para-.002),world(pa,Q,para-.002)],(0,0,1),col,metal,
                       'original_roof_fascia_closure_TYPE',plane_placement_estimated=True,**common)
        # One corner triangle, with three unequal lower widths and one upper apex.
        A=world(END,Q,para);B=world(Q,END,para);apex=world(END,END,roof)
        normal=(B-A).cross(apex-A).normalized();walked=0
        for panel,w in enumerate(WIDTHS,1):
            L=A.lerp(B,walked/DIAGONAL);R=A.lerp(B,(walked+w)/DIAGONAL);walked+=w
            poly_sheet(f'{tower}_original_roof_corner_E{2*side+1}_triangle{panel}',
                [L,R,apex],normal,col,metal,'original_corner_roof_triangle',
                edge=2*side+1,panel_index=panel,lower_width_m=w,
                apex_world=tuple(apex),low_a_world=tuple(L),low_b_world=tuple(R),**common)
        gasket=material('AB321_roof_panel_joint_TYPE',(.055,.062,.064),.05,.8)
        for j,distance in enumerate((WIDTHS[0],WIDTHS[0]+WIDTHS[1])):
            start=A.lerp(B,distance/DIAGONAL);direction=(apex-start).normalized()
            cross=direction.cross(normal).normalized()*.0015;offset=normal*.001
            poly_sheet(f'{tower}_original_roof_corner_joint_E{2*side+1}_{j}',
                       [start-cross+offset,start+cross+offset,apex+cross+offset,apex-cross+offset],
                       normal,col,gasket,'original_roof_corner_panel_joint_TYPE',width_estimated_m=.003,**common)
        # Cut/folded seam covers on both inclined junctions. Actual mating sheet
        # endpoints are shared, not a merely chamfered flat outline.
        for k,start in enumerate((A,B)):
            adjnormal=fieldnormal if k==0 else Vector((-fieldnormal.y,fieldnormal.x,fieldnormal.z))
            toward=world(0,(Q+END)/2,(para+roof)/2) if k==0 else world((Q+END)/2,0,(para+roof)/2)
            folded_seam(f'{tower}_original_roof_raked_joint_E{2*side+1}_{k}',start,apex,
                        ((normal,(A+B+apex)/3),(adjnormal,toward)),col,metal,edge=2*side+1,**common)
            beam(f'{tower}_original_roof_corner_support_E{2*side+1}_{k}',
                 start-normal*.12,apex-normal*.12,support,steel,.12,.18)
        # Separate curb coping with miters in plan; three corner roof panels
        # start at this diagonal datum. Width is AB323D11 5/8in±.
        points.extend([world(-END,Q,para),world(END,Q,para)])
        headera=world(-END,Q-.15,finish+5*FT);headerb=world(END,Q-.15,finish+5*FT)
        beam(f'{tower}_original_roof_header_S{side+1}',headera,headerb,support,steel,.18,.22)
        for j in range(59):
            p=(j-29)*PITCH
            start=world(p,Q,para)-fieldnormal*.20;end=world(p,END,roof)-fieldnormal*.20
            beam(f'{tower}_original_roof_support_S{side+1}_{j:02d}',start,end,support,steel)
            # AB323D explicitly labels quarter-inch bent steel and stiffener;
            # width/length remain TYPE dimensions.
            v=[];f=[];t=.25*IN
            append_box(v,f,(0,0,0),(.16,.18,t));append_box(v,f,(0,.09-t/2,.065),(.16,t,.13))
            ob=object_mesh(f'{tower}_original_roof_bent_bracket_S{side+1}_{j:02d}',
                mesh('ab323_quarter_inch_bracket',v,f,steel),start,support,angle)
            tag(ob,'original_roof_bent_bracket',plate_gauge_m=t,other_dimensions_estimated=True)
        for j in range(1,4):
            t=j/4; qq=Q-(Q-END)*t;zz=para+(roof-para)*t
            beam(f'{tower}_original_roof_purlin_S{side+1}_{j}',world(-END,qq,zz)-fieldnormal*.20,world(END,qq,zz)-fieldnormal*.20,
                 support,steel,.10,.14)
        # Roof's upper rim is now square: two corner planes terminate at one
        # point. These pieces have ends cut on a diagonal bisector.
        q=END;w=.09
        a=world(-q,q,roof);b=world(q,q,roof);c=world(q-w,q-w,roof);d=world(-q+w,q-w,roof)
        poly_sheet(f'{tower}_original_roof_upper_rim_S{side+1}',[a,b,c,d],(0,0,1),col,metal,
                   'original_upper_rim_miter',rim_width_estimated_m=w,**common)
    def inset(distance):
        result=[]
        for i,p in enumerate(points):
            a=points[i-1];b=points[(i+1)%8]
            e0=(p-a).normalized();e1=(b-p).normalized()
            n0=Vector((-e0.y,e0.x,0));n1=Vector((-e1.y,e1.x,0))
            bisector=n0+n1
            result.append(p+bisector*(distance/bisector.dot(n0)))
        return result
    inside=inset(11.625*IN)
    for i,a in enumerate(points):
        b=points[(i+1)%8];d=inside[i];c=inside[(i+1)%8]
        poly_sheet(f'{tower}_original_parapet_coping_E{i}',[a,b,(c.x,c.y,para),(d.x,d.y,para)],
                   (0,0,1),col,metal,'cap_mitered_coping',coping_width_m=11.625*IN,**common)
    concrete=material('AB323_concrete_parapet',(.39,.37,.32),.0,.86)
    outside=inset(11.625*IN-6*IN);inner=inset(11.625*IN)
    for i,a in enumerate(outside):
        b=outside[(i+1)%8];c=inner[(i+1)%8];d=inner[i]
        ob=prism(f'{tower}_original_concrete_parapet_E{i}',[(v.x,v.y) for v in (a,b,c,d)],
                 finish,finish+5*FT,support,concrete)
        tag(ob,'original_concrete_parapet',thickness_m=6*IN,**common)
    for ob in support.objects:
        if ob.get('module')=='cap_steel_support_type':
            tag(ob,'cap_steel_support_type',section_dimensions_estimated=True,**common)
    for c in (col,support):
        c['finished110_z']=finish;c['parapet_z']=para;c['paneltop_z']=roof
        c['roof_horizontal_run_inferred_m']=LEG;c['inferred_from']='AB321E/F triangular corner plan'
    return col


def roof_datums(tower,xy,finish,roof,metal):
    delta=finish-roof
    roofob=bpy.data.objects[tower+'_roof_datum'];roofob.location.z+=delta
    roofob['datum_mapping_estimated']=True;roofob['source']=SOURCE
    move=[]
    for name in (tower+'_ROOF_detail_components',tower+'_ROOF_auxiliary_antenna_interpretation',
                 'WTC1_antenna_photo_interpretation_STUDY' if tower=='WTC1' else ''):
        c=bpy.data.collections.get(name)
        if c:move.extend(c.all_objects)
    for ob in set(move):
        ob.location.z+=delta;ob['roof_datum_mapping_estimated']=True
    if tower=='WTC2':
        # Public observation platform datum/footprint are not provided by the
        # corner sheets. Preserve existing guard-rail study on a separate deck,
        # clearly labelled estimated, above the newly mapped maintenance roof.
        c=bpy.data.collections.get('WTC2_COMPLETION_study')
        obs=next(c2 for c2 in c.children if c2.name.startswith('roof_observation'))
        ob=object_mesh('WTC2_raised_observation_platform_DATUM_STUDY',
            _box_mesh((56.4,56.4,.30),metal),(*xy,roof+.30),obs)
        tag(ob,'observation_platform_datum_study',dimensions_estimated=True,datum_mapping_estimated=True)
        obs['confidence']='Raised public platform dimensions/level estimated; AB321/323 describe maintenance roof, not visitor deck.'


def apply():
    scene=bpy.context.scene
    if scene.get('original_junction_revision')==VERSION:return
    previous=scene.get('original_junction_revision','')
    if previous=='2026-10-14-ab321-ab323-v4':
        # The two flange solids need independently outward winding. Recalculate
        # disconnected islands even when their summed signed volume was positive.
        import bmesh
        for tower in ('WTC1','WTC2'):
            for ob in bpy.data.collections[tower+'_CROWN_CAP_mitered_panels'].objects:
                if ob.get('module')!='original_roof_raked_joint':continue
                bm=bmesh.new();bm.from_mesh(ob.data)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
                bm.to_mesh(ob.data);bm.free();ob['original_junction_revision']=VERSION
        scene['original_junction_revision']=VERSION
        return
    metal=bpy.data.materials['silver_cladding_color_study']
    steel=bpy.data.materials['structural_steel_unclad_STUDY']
    ss=material('AB323_polished_stainless_projection',(.56,.60,.63),.92,.19)
    dark=material('AB323_washer_track_shadow',(.035,.042,.048),.8,.42)
    for tower,xy,roof in (('WTC1',(-55,55),1368*FT),('WTC2',(55,-55),1362*FT)):
        finish=roof-15*FT;para=finish+6*FT
        if not previous:
            levels=corners(tower,xy,finish,para,roof,metal)
            frames(tower,xy,para,levels,metal,ss,dark)
        fascia=crown_curves(tower,finish,metal)
        hood(tower,xy,finish,para,roof,fascia,metal,steel)
        if not previous:roof_datums(tower,xy,finish,roof,metal)
        for suffix in ('_FACADE_corner_transition_frames','_corner_three_panels','_crown_curved_cladding'):
            c=bpy.data.collections[tower+suffix]
            if c.asset_data:c.asset_data.description=c.get('confidence',LIMITS)
    scene['original_junction_revision']=VERSION
    scene['crown_junction_source']=SOURCE
    scene['quality_status']='AB321/323 dimensional CG junction; roof apex/run and absolute datums inferred; historical production gates remain open'
