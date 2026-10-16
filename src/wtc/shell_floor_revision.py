"""Whole tower floors: NIST G-1 taxonomy, long/short/two-way framing zones."""
import math
import bpy
from .mesh_batch import Batch,i_section
from .interior_parts import collection,finish
from .lobby_plan_revision import slab_mesh
from .facade_detail import outline,REFERENCE_HALF
from .floor_structure_revision import angle,IN,FT

VERSION='2026-10-16-whole-floor-shell-v1'
SOURCE='https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2a.pdf; final TableG-1/FigsG-1..4,Fig1-4,1-7..10; NIST1-2v1 p31'
LIMIT='Source construction family, spacing, chord type and composite layers; region registration/member schedules/shaft coordinates are fitted CG, not an engineering analysis or exact fabrication model'
H=137*FT/2;K=87*FT/2;Q=REFERENCE_HALF


def floor_type(tower,n):
    if n in (7,9,41,43,75,77,107,108,110):return 12
    if n in (8,42,76,109):return 13
    if n==1:return 14
    if n==2:return 15
    if n in (25,59,92):return 2
    if 46<=n<=49:return 3
    if n==44:return 4
    if n==45:return 5
    if tower=='WTC1' and n==67:return 6
    if n==78:return 7
    if n==79:return 8
    if 80<=n<=83:return 9
    if tower=='WTC1' and n==106:return 10
    if tower=='WTC2' and 10<=n<=13:return 11
    return 1


def region(name,x0,x1,y0,y1,direction,beam=False,heavy=False):
    c=bpy.data.collections.new(name);c['source']=SOURCE;c['confidence']=LIMIT
    steel=finish('SHELL_steel_fireproof_surface',(.37,.38,.36),.28,.86,1300)
    boltmat=finish('SHELL_connection_metal',(.20,.23,.23),.8,.43)
    roles={s:Batch(name+'_'+s,boltmat if s in ('seats','bolts') else steel) for s in ('top_chords','bottom_chords','web_rods','knuckles','bridging','seats','bolts','deck')}
    if direction=='Y':a0,a1=x0,x1;b0,b1=y0,y1
    else:a0,a1=y0,y1;b0,b1=x0,x1
    def p(a,b,z):return (a,b,z) if direction=='Y' else (b,a,z)
    top=-5.5*IN;depth=29*IN
    # The column grid establishes the paired truss axes; no stretched samples.
    axes=[k*2.032 for k in range(-16,17) if a0+.10<k*2.032<a1-.10]
    if not axes:axes=[(a0+a1)/2]
    for a in axes:
        if beam:
            roles['top_chords'].bar(p(a,b0,top-.28),p(a,b1,top-.28),i_section(.56,.22,.012,.022))
        else:
            for pair in (-1,1):
                aa=a+pair*7.125*IN/2
                for side in (-1,1):
                    roles['top_chords'].bar(p(aa,b0,top),p(aa,b1,top),angle(1.5*IN,2*IN,.25*IN,side))
                    roles['bottom_chords'].bar(p(aa,b0,top-depth+3*IN),p(aa,b1,top-depth+3*IN),angle(2*IN,3*IN,.37*IN,side))
                cells=max(1,round((b1-b0)/(40*IN)))
                for j in range(cells):
                    b=b0+(b1-b0)*j/cells;e=b0+(b1-b0)*(j+1)/cells;mid=(b+e)/2
                    roles['web_rods'].tube(p(aa,b,top-.018),p(aa,mid,top-depth+.04),1.09*IN/2)
                    roles['web_rods'].tube(p(aa,mid,top-depth+.04),p(aa,e,top-.018),1.09*IN/2)
                for j in range(cells+1):
                    b=b0+(b1-b0)*j/cells
                    for k in range(6):
                        u=k*math.pi/6;v=(k+1)*math.pi/6
                        roles['knuckles'].tube(p(aa,b+.038*math.cos(u),top+.025+.038*math.sin(u)),p(aa,b+.038*math.cos(v),top+.025+.038*math.sin(v)),1.09*IN/2,8)
        for end,b in enumerate((b0+.18,b1-.18)):
            roles['seats'].box(p(a,b,top-.07),(.42,.32,.375*IN) if direction=='Y' else (.32,.42,.375*IN))
            for s in (-1,1):
                roles['bolts'].tube(p(a+s*.10,b,top-.08),p(a+s*.10,b,top-.025),.625*IN/2,8)
            roles['seats'].box(p(a,b,top-depth-.025),(.40,.22,.09))
    # True transverse bridge trusses, heavy in the two-way corner zones.
    count=max(1,round((b1-b0)/(13+4/12)/FT))
    for j in range(1,count+1):
        b=b0+(b1-b0)*j/(count+1);r=.014 if heavy else .009
        for zz in (top-.16,top-.55):roles['bridging'].bar(p(a0+.06,b,zz),p(a1-.06,b,zz),[(-.020,-.022),(.020,-.022),(.020,.022),(-.020,.022)])
        for k in range(max(1,round((a1-a0)/1.016))):
            a=a0+(a1-a0)*k/max(1,round((a1-a0)/1.016));e=min(a1,a+1.016)
            roles['bridging'].tube(p(a,b,top-.16),p((a+e)/2,b,top-.55),r)
            roles['bridging'].tube(p((a+e)/2,b,top-.55),p(e,b,top-.16),r)
    # Closed one-millimetre fluted sheet, perpendicular to main spans.
    section=[];steps=max(1,math.ceil((a1-a0)/.1524));pitch=(a1-a0)/steps
    for k in range(steps):
        a=a0+k*pitch
        section.extend(((a,0),(a+.29*pitch,0),(a+.47*pitch,-1.5*IN),(a+.82*pitch,-1.5*IN),(a+pitch,0)))
    section=[p for i,p in enumerate(section) if not i or math.dist(p,section[i-1])>1e-8]
    section += [(x,z-.001) for x,z in section[::-1]]
    roles['deck'].bar(p(0,b0,-4*IN),p(0,b1,-4*IN),[(-x,z) for x,z in section[::-1]] if direction=='Y' else section)
    for key,batch in roles.items():batch.mesh(c,'shell_'+key)
    c['main_axes']=len(axes);c['framing_family']='beam' if beam else 'paired_truss';c['two_way']=heavy
    return c


def templates():
    regions=[]
    for side in (-1,1):
        y0,y1=((-Q+.20,-K) if side<0 else (K,Q-.20))
        for j,(a,b) in enumerate(((-Q+2.2,-K),(-K,K),(K,Q-2.2))):regions.append((f'long{side}_{j}',a,b,y0,y1,'Y',j!=1))
        x0,x1=((-Q+.20,-H) if side<0 else (H,Q-.20))
        for j,(a,b) in enumerate(((-K,-9),(-9,9),(9,K))):regions.append((f'short{side}_{j}',x0,x1,a,b,'X',j!=1))
    variants={}
    for label,x0,x1,y0,y1,d,heavy in regions:
        for beam in (False,True):variants[label,beam]=region('SHELL_ZONE_'+label+('_BEAM' if beam else '_TRUSS'),x0,x1,y0,y1,d,beam,heavy)
    result={}
    edgecol=bpy.data.collections.new('SHELL_edge_and_core_collector_TEMPLATE');edgecol['source']=SOURCE;edgecol['confidence']=LIMIT
    edge=Batch('SHELL_perimeter_and_core_collectors',bpy.data.materials['SHELL_steel_fireproof_surface'])
    for ring in (outline(Q-.12),[(-H,-K),(H,-K),(H,K),(-H,K)]):
        for a,b in zip(ring,ring[1:]+ring[:1]):edge.bar((*a,-.35),(*b,-.35),i_section(.42,.20,.012,.022))
    edge.mesh(edgecol,'shell_edge_girders')
    for typ in range(1,14):
        root=bpy.data.collections.new('SHELL_FLOOR_NIST_TYPE'+str(typ));root['source']=SOURCE;root['confidence']=LIMIT
        for label,*_ in regions:
            beam=typ>=12 or (typ in (3,9) and label.startswith('short') and label[-1]!='1') or (typ in (2,4,5,6,7,8) and label.startswith('long') and label[-1]=='1')
            zone=variants[label,beam];ob=bpy.data.objects.new('TYPE'+str(typ)+'_'+label,None);ob.instance_type='COLLECTION';ob.instance_collection=zone;root.objects.link(ob)
        ob=bpy.data.objects.new('TYPE'+str(typ)+'_edge_collectors',None);ob.instance_type='COLLECTION';ob.instance_collection=edgecol;root.objects.link(ob)
        result[typ]=root
    return result


def apply():
    scene=bpy.context.scene
    if scene.get('shell_floor_revision')==VERSION:return
    types=templates();concrete=finish('SHELL_bare_concrete',(.48,.47,.43),0,.91,1000)
    outline_core=[(-H,-K),(H,-K),(H,K),(-H,K)]
    ring=slab_mesh('SHELL_typical_4in_composite_ring',outline(Q-.03),[outline_core],4*IN,concrete)
    beamring=slab_mesh('SHELL_beam_floor_6in_ring',outline(Q-.03),[outline_core],6*IN,concrete)
    for mesh in (ring,beamring):
        for v in mesh.vertices:v.co.z+=.10
    for tower,xy,rotation in (('WTC1',(-55,55),0),('WTC2',(55,-55),math.pi/2)):
        c=collection(tower+'_WHOLE_FLOOR_shell_structure',bpy.data.collections[tower+'_COMPLETION_study'],SOURCE,LIMIT,xy)
        c['state']='Owner shell before tenant partitions, desks, office carpet and suspended ceilings'
        for n in range(7,111):
            z=bpy.data.objects[tower+f'_F{n:03d}_SLAB_STUDY'].location.z+.1;typ=floor_type(tower,n)
            ob=bpy.data.objects.new(tower+f'_F{n:03d}_STRUCTURE_NIST_TYPE{typ}',None);ob.instance_type='COLLECTION';ob.instance_collection=types[typ];ob.location=(*xy,z);ob.rotation_euler.z=rotation;c.objects.link(ob)
            ob['module']='whole_floor_structure';ob['floor']=n;ob['source_floor_type']=typ;ob['source']=SOURCE;ob['confidence']=LIMIT
            old=bpy.data.objects[tower+f'_F{n:03d}_SLAB_STUDY'];old.data=beamring if typ>=12 else ring;old.rotation_euler.z=rotation;old['construction_type']=typ;old['slab_layer']='Physical4in/6in composite slab with core void; original proxy replaced'
            # top-anchored slab follows the former top face, keeping all datums.
            old.location.z=z-.10
        # Separate roof sample remains usable as an asset, without duplicating F9.
        oldpanel=bpy.data.collections[tower+'_FLOOR_composite_truss_panel_DETAIL'];oldpanel.hide_render=True;oldpanel.hide_viewport=True;oldpanel['superseded_in_main_scene_by']=c.name
        c['floor_instances']=104
    scene['shell_floor_revision']=VERSION
