"""Composite panel and end seats from supplied Fig2-6/1-6 and NIST1-2 p31."""
import math
import bpy
from .interior_parts import Parts,collection,finish
from .lobby_plan_revision import slab_mesh
from .facade_revision import _prism_profile,_mesh,_face_object
from .completion import PLAZA_Z

VERSION='2026-10-16-composite-floor-and-end-projections-v1'
SOURCE='User supplied Fig2-6 truss end connections and Fig1-6 composite floor; https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2v1.pdf p31'
LIMIT='Reference C32T1-type composite panel:29in depth,60ft span,double angles and7.125in pair gap sourced. Seats/bolts per supplied diagram; unsized gauges/welds/bridging sections fitted. Representative F9 panel, not a complete fabrication schedule.'
IN=.0254;FT=.3048


def capsule(x,y,length,width):
    r=width/2;straight=(length-width)/2
    return [(x+s*straight+r*math.cos(a),y+r*math.sin(a)) for s,start in ((1,-math.pi/2),(-1,math.pi/2)) for a in [start+i*math.pi/10 for i in range(11)]]


def angle(w,h,t,sign):
    a=[(.003,0),(.003+w,0),(.003+w,-t),(.003+t,-t),(.003+t,-h),(.003,-h)]
    return a if sign>0 else [(-x,y) for x,y in a[::-1]]


def bolt(p,name,x,y,z,dia,metal):
    p.tube(name+'_shaft',(x,y,z-.018),(x,y,z+.032),dia/2,metal,'connection_bolt')
    hexagon=[(.85*dia*math.cos(i*math.tau/6),.85*dia*math.sin(i*math.tau/6)) for i in range(6)]
    p.bar(name+'_nut',(x,y,z+.009),(x,y,z+.028),hexagon,metal,'connection_nut')
    p.disk(name+'_washer',(x,y,z+.005),dia, .004,metal,'connection_washer')


def panel(tower,xy,angle_z,origin):
    col=collection(tower+'_FLOOR_composite_truss_panel_DETAIL',bpy.data.collections[tower+'_COMPLETION_study'],SOURCE,LIMIT,xy)
    p=Parts(tower+'_FLOOR_PANEL',col,origin,angle_z)
    steel=finish('FLOOR_galvanized_steel',(.34,.38,.38),.85,.38,250)
    dark=finish('FLOOR_connection_steel',(.14,.16,.16),.8,.42,400)
    concrete=finish('FLOOR_lightweight_concrete',(.52,.51,.45),0,.9,700)
    slab=bpy.data.objects[tower+'_F009_SLAB_STUDY'];floor_top=slab.location.z+.10
    deck_z=floor_top-4*IN;chord_z=deck_z-1.5*IN;L=60*FT;width=2*(6+8/12)*FT+.32
    for axis in range(3):
        center=(axis-1)*(6+8/12)*FT
        for pair in (-1,1):
            y=center+pair*7.125*IN/2;label=f'T{axis}_{pair}'
            for side in (-1,1):
                p.bar(label+f'_top_angle{side}',(0,y,chord_z),(L,y,chord_z),angle(1.5*IN,2*IN,.25*IN,side),steel,'truss_top_angle')
                p.bar(label+f'_bottom_angle{side}',(0,y,chord_z-29*IN+3*IN),(L,y,chord_z-29*IN+3*IN),angle(2*IN,3*IN,.37*IN,side),steel,'truss_bottom_angle')
            for j in range(18):
                a=j*40*IN;b=a+20*IN;c=a+40*IN
                p.tube(label+f'_web{j}_a',(a,y,chord_z-.018),(b,y,chord_z-29*IN+.04),1.09*IN/2,steel,'truss_diagonal_rod')
                p.tube(label+f'_web{j}_b',(b,y,chord_z-29*IN+.04),(c,y,chord_z-.018),1.09*IN/2,steel,'truss_diagonal_rod')
            for j in range(19):
                x=j*40*IN
                for k in range(6):
                    a=k*math.pi/6;b=(k+1)*math.pi/6
                    p.tube(label+f'_knuckle{j}_{k}',(x+.038*math.cos(a),y,chord_z+.025+.038*math.sin(a)),(x+.038*math.cos(b),y,chord_z+.025+.038*math.sin(b)),1.09*IN/2,steel,'shear_knuckle')
            for end in (0,1):
                x=.22 if not end else L-.22;name=label+f'_end{end}'
                outline=[(-.22,-.12),(.22,-.12),(.22,.12),(-.22,.12)]
                holes=[capsule(s*.105,0,.033,.018) for s in (-1,1)]
                m=slab_mesh(name+'_slotted_seat_mesh',outline,holes,.375*IN,dark)
                o=p.mesh(name+'_slotted_seat',m,(x,y,chord_z-.06),kind='slotted_connection_seat');o['bolt_diameter_m']=.625*IN
                for s in (-1,1):bolt(p,name+f'_bolt{s}',x+s*.105,y,chord_z-.058,.625*IN,steel)
                # Triangular vertical stiffener, closed and individually editable.
                v=[];f=[];_prism_profile(v,f,[(0,0),(.30,0),(0,-.28)],.375*IN)
                p.mesh(name+'_gusset',_mesh(('floor_gusset',end),v,f,dark),(x-.15,y,chord_z-.07),kind='truss_end_gusset')
                p.box(name+'_weld_bead',(x,y,chord_z-.061),(.40,.008,.006),steel,kind='connection_weld_TYPE')
            p.box(label+'_exterior_damper',( .28,y,chord_z-29*IN-.02),(.40,.16,.09),dark,kind='damping_unit_TYPE')
            for s in (-1,1):bolt(p,label+f'_damper_bolt{s}',.28+s*.10,y,chord_z-29*IN+.02,.875*IN,steel)
            p.box(label+'_core_welded_channel',(L+.035,y,chord_z-.20),(.08,.25,.40),dark,kind='core_welded_channel')
            for s in (-1,1):p.tube(label+f'_A490_wall_bolt{s}',(-.09,y+s*.06,chord_z-.18),(.08,y+s*.06,chord_z-.18),IN/2,steel,'exterior_A490_bolt')
    for j,x in enumerate((1.016,6.096,12.192,17.272)):
        for y in (-1.016,1.016):
            for side in (-1,1):p.bar(f'bridge{j}_{y:.3f}_chord{side}',(x,y-1.016,chord_z-.18+(side-1)*.18),(x,y+1.016,chord_z-.18+(side-1)*.18),[(-.022,-.022),(.022,-.022),(.022,.022),(-.022,.022)],steel,'bridging_truss')
            for k in range(4):p.tube(f'bridge{j}_{y:.3f}_web{k}',(x,y-1.016+k*.508,chord_z-.18),(x,y-.762+k*.508,chord_z-.54),.009,steel,'bridging_truss')
    # Actual fluted sheet section, not a flat texture.
    section=[];pitch=.1524;count=math.ceil(width/pitch)
    for k in range(count):
        a=-width/2+k*pitch
        section.extend(((a,0),(a+.045,0),(a+.072,-1.5*IN),(a+.125,-1.5*IN),(a+pitch,0)))
    # Adjacent periods share their last/first vertex; remove exact repeats.
    section=[v for i,v in enumerate(section) if not i or v!=section[i-1]]
    section += [(x,z-.001) for x,z in section[::-1]]
    p.bar('corrugated_metal_deck',(0,0,deck_z),(L,0,deck_z),section,steel,'corrugated_metal_deck')
    full=p.box('concrete_full',(L/2,0,floor_top-2*IN),(L,width,4*IN),concrete,kind='composite_concrete_slab')
    partial=p.box('concrete_cutaway',(L*.65,0,floor_top-2*IN),(L*.70,width,4*IN),concrete,kind='composite_concrete_cutaway')
    partial.hide_render=True;partial.hide_viewport=True
    # Replace only the corresponding area of the old F9 plate; no solid overlap.
    hole=[]
    for a,b in ((0,-width/2),(L,-width/2),(L,width/2),(0,width/2)):
        q=p.point((a,b,0));hole.append((q.x-xy[0],q.y-xy[1]))
    slab.data=slab_mesh(tower+'_F009_panel_opening',[(-29.5,-29.5),(29.5,-29.5),(29.5,29.5),(-29.5,29.5)],[hole],.20,slab.data.materials[0])
    # slab_mesh is top-anchored; keep the existing floor top at z+100mm.
    for v in slab.data.vertices:v.co.z+=.10
    slab['composite_panel_reference']=col.name
    col['nominal_truss_depth_m']=29*IN;col['nominal_span_m']=L;col['panel_floor']=9
    col['source_concrete_thickness_m']=4*IN;col['source_deck_depth_m']=1.5*IN
    return col


def corner_projections(tower,xy):
    col=bpy.data.collections[tower+'_BASE_nested_frames_and_transoms_STUDY']
    p=Parts(tower+'_BASE_END',col,xy)
    metal=finish('BASE_end_folded_metal',(.47,.49,.46),.85,.3)
    for side in range(4):
        for sign in (-1,1):
            for z in (PLAZA_Z+.16,PLAZA_Z+3.03):
                # User requests the projecting terminal/knee; AB323 supplies
                # the5x7in frame envelope. Tab/fastener sizes are CG fits.
                for part,off,size in (('tab',0,(.127,.1778,.12)),('return',sign*.075,(.035,.22,.22))):
                    m=_mesh(('base_end_project',part),[],[],metal) if False else None
                    from .facade_revision import _box_mesh
                    o=_face_object(f'{tower}_BASE_END_S{side}_{sign}_{int(z*1000)}_{part}',_box_mesh(size,metal),xy,side,31.71,z,col,sign*29*1.016+off)
                    o['module']='base_end_corner_projection';o['source']='User requested base terminal/knee projection; AB323 5in x7in frame envelope';o['confidence']='Terminal placement and tab/return gauges CG fitted; not a verified corner fabrication node'


def apply():
    if bpy.context.scene.get('floor_structure_revision')==VERSION:return
    panel('WTC1',(-55,55),math.pi/2,(-55,55-31.5722))
    panel('WTC2',(55,-55),math.pi,(55+31.5722,-55))
    for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):corner_projections(tower,xy)
    bpy.context.scene['floor_structure_revision']=VERSION
