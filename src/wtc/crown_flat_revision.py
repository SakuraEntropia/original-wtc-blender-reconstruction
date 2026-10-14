"""Flat, connected two-bay crown finish; remove superseded viewport glass.

Sourced widths/heights retained. Curvature and25mm finish depth are CG fits.
CDT unions seven planar regions before extrusion: no detached arms or doubled
front faces. This decorative finish does not replace the separate steel assets.
"""
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from .facade_revision import IN, PITCH, OUTER_HALF, _mesh, _box_mesh, _prism_profile, _face_object

VERSION='2026-10-14-flat-connected-crown-v2'
DEPTH=.025
STRIP=7*IN
SOURCE='NIST1-5Av1 Fig4-8; original A-AB-321/323; user flat-section correction'


def _ccw(poly):
    area=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))
    return poly if area>0 else poly[::-1]


def _joined_mesh(lower,middle,upper,total,metal):
    even=[12*IN,17*IN,17*IN,12*IN];odd=[7*IN,7*IN,7*IN,12*IN]
    heights=[0,lower,middle,total]
    left=[(0,0)]+[(w/2,z) for w,z in zip(even,heights)]+[(0,total)]
    right=[(2*PITCH-x,z) for x,z in left]
    center=[(PITCH+w/2,z) for w,z in zip(odd,heights)]
    center += [(PITCH-w/2,z) for w,z in reversed(list(zip(odd,heights)))]
    polygons=[_ccw(left),_ccw(center),_ccw(right)]
    join=.010  # internal overlap removed by planar union, never double surfaces
    for sign in (-1,1):
        # Entire ribbon end lies inside the receiving stem. Finishing on its
        # outside edge leaves a square ledge even though the mesh is connected.
        start=PITCH
        wide=PITCH+sign*(PITCH-8.5*IN+STRIP/2+join)
        close=PITCH
        for x0,x1,z0,h in ((start,wide,0,lower),(wide,close,middle,upper)):
            path=[]
            for i in range(25):
                t=i/24;x=x0+(x1-x0)*(3*t*t-2*t*t*t)
                path.append((x,z0+h*t))
            poly=[(x+STRIP/2,z) for x,z in path]
            poly += [(x-STRIP/2,z) for x,z in path[::-1]]
            polygons.append(_ccw(poly))
    coords=[];regions=[]
    for poly in polygons:
        regions.append(list(range(len(coords),len(coords)+len(poly))))
        coords.extend(Vector(v) for v in poly)
    verts,edges,faces,origv,orige,origf=delaunay_2d_cdt(coords,[],regions,0,1e-7,True)
    face2=[face for face,ids in zip(faces,origf) if ids]
    used=sorted({i for face in face2 for i in face});remap={old:new for new,old in enumerate(used)}
    points=[verts[i] for i in used];face2=[[remap[i] for i in f] for f in face2]
    n=len(points);v=[(p.x,y,p.y) for y in (0,DEPTH) for p in points]
    front=[tuple(f) for f in face2];back=[tuple(n+i for i in f[::-1]) for f in face2]
    counts={};directed={}
    for f in face2:
        for a,b in zip(f,f[1:]+f[:1]):
            k=tuple(sorted((a,b)));counts[k]=counts.get(k,0)+1;directed[k]=(a,b)
    walls=[]
    for k,count in counts.items():
        if count==1:
            a,b=directed[k];walls.append((b,a,a+n,b+n))
    m=_mesh(('flat_union',lower,middle,upper,total),v,front+back+walls,metal)
    for p in m.polygons:p.use_smooth=False
    m['flat_connected_crown']=VERSION;m['front_plane_local_y_m']=0
    return m


def apply():
    scene=bpy.context.scene
    if scene.get('flat_connected_crown_revision')==VERSION:return
    bpy.context.view_layer.update()
    metal=bpy.data.materials['silver_cladding_color_study']
    for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):
        col=bpy.data.collections[tower+'_crown_curved_cladding']
        a=col['z_transition_lower_estimated_m'];b=col['z_transition_middle_estimated_m']
        d=col['z_transition_upper_estimated_m'];top=col['z_fascia_bottom_inferred_m']
        proto=_joined_mesh(b-a,d-a,top-d,top-a,metal)
        remove=[o for o in col.objects if o.get('module') in ('crown_curved_transition','crown_alternating_cover','crown_flat_joined_unit','crown_flat_end_cover')]
        if remove:bpy.data.batch_remove(ids=remove)
        for side in range(4):
            for cell in range(29):
                ob=_face_object(f'{tower}_crown_flat_S{side+1}_two_bay{cell:02d}',proto,xy,side,OUTER_HALF,a,col,(-29+2*cell)*PITCH)
                for k,v in dict(module='crown_flat_joined_unit',source=SOURCE,face=side+1,
                    cell_index=cell,branch_count=4,flat_depth_m=DEPTH,branch_width_m=STRIP,
                    lower_transition_height_m=b-a,upper_transition_height_m=top-d,
                    profile_samples=24,structural=False,confidence='Source widths/heights; flat25mm depth and smoothstep curvature CG estimates; planar union physically connects all arms/stems').items():ob[k]=v
            # Outermost halves close the59-axis rhythm without overlapping cells.
            heights=[0,b-a,d-a,top-a];widths=[12*IN,17*IN,17*IN,12*IN]
            for sign in (-1,1):
                profile=[(0,0)]+[(sign*w/2,z) for w,z in zip(widths,heights)]+[(0,top-a)]
                profile=_ccw(profile);v=[];f=[];_prism_profile(v,f,profile,DEPTH,DEPTH/2)
                m=_mesh(('flat_end',sign,b-a,d-a,top-a),v,f,metal)
                for p in m.polygons:p.use_smooth=False
                ob=_face_object(f'{tower}_crown_flat_S{side+1}_end{sign:+d}',m,xy,side,OUTER_HALF,a,col,sign*29*PITCH)
                ob['module']='crown_flat_end_cover';ob['source']=SOURCE;ob['flat_depth_m']=DEPTH
        roof=bpy.data.objects[tower+'_roof_datum']
        roof_bottom=min((roof.matrix_world@v.co).z for v in roof.data.vertices)
        for ob in col.objects:
            if ob.get('module')=='crown_107_cover':
                if 'taper' in ob.name:
                    h=(7+1/12)*.3048
                    profile=[(-18.75*IN/2,0),(18.75*IN/2,0),(6*IN,h),(-6*IN,h)]
                else:
                    h=(11+7/12)*.3048
                    profile=[(-6*IN,-h/2),(6*IN,-h/2),(6*IN,h/2),(-6*IN,h/2)]
                v=[];f=[];_prism_profile(v,f,profile,DEPTH,DEPTH/2)
                ob.data=_mesh(('flat_107', 'taper' in ob.name,h),v,f,metal)
                ob['flat_depth_m']=DEPTH;ob['confidence']='Source width/height;25mm flat finish depth estimated'
            elif ob.get('module')=='crown_mechanical_backing':
                height=roof_bottom-.008-a
                ob.data=_box_mesh((58*PITCH+12*IN,.08,height),ob.data.materials[0]);ob.location.z=a+height/2
                ob['roof_clearance_m']=.008;ob['confidence']='Service wall clipped below current estimated maintenance roof, not extended through roof slab'
        for suffix in ('_top_lower_glass_STUDY','_top_upper_glass_STUDY','_crown_glazing_to_cap_STUDY'):
            ob=bpy.data.objects.get(tower+suffix)
            if ob:ob.hide_render=True;ob.hide_viewport=True;ob['superseded_by']=VERSION
        legacy=bpy.data.collections.get(tower+'_CROWN_photo_interpretation')
        if legacy:legacy.hide_render=True;legacy.hide_viewport=True
        col['confidence']='Flat joined two-bay crown finish; source widths/heights retained. Curvature/depth/absolute datums estimated.'
        col['flat_connected_revision']=VERSION
        if col.asset_data:col.asset_data.description=col['confidence']
    scene['flat_connected_crown_revision']=VERSION
