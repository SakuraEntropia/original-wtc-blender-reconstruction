"""Source-outline lowrises and a separately labelled fitted parking structure.

Only drawing observations are transcribed; no source bitmap or third-party mesh
is redistributed. Parking is a spatial CG type, not the original basement plan.
"""
import math
import bpy
from .interior_parts import collection,finish,Parts
from .mesh_batch import Batch,i_section
from .lobby_plan_revision import slab_mesh
from .completion import PLAZA_Z

VERSION='2026-10-16-podium-outlines-parking-v1'
SOURCE='Original SKA55/84 plaza-level plan,1986 revision; https://www.wtcexplained.com/complex/assets/main-plaza-source-overlay.jpg'
LIMIT='Manual original-plan outline reading, scaled by63.14m tower width; no surveyed registration. Upper-level setbacks, bay schedules, materials and rooftop equipment are fitted CG types; not certified as-built.'


def trace(points):
    return [(-55+(x-996)*63.1444/176,55-(y-632)*63.1444/176) for x,y in points][::-1]


FOOTPRINTS={
 'WTC3':dict(stories=22,height=73.7,base=trace([(903,735),(1008,735),(1008,833),(1075,833),(1075,1024),(995,1024)]),upper=trace([(914,746),(995,746),(995,847),(1062,847),(1062,1010),(1004,1010)])),
 'WTC4':dict(stories=9,height=36.6,base=trace([(1273,831),(1397,831),(1397,757),(1498,757),(1498,879),(1555,879),(1555,996),(1437,996),(1437,1023),(1273,1023)]),upper=trace([(1398,757),(1498,757),(1498,879),(1555,879),(1555,996),(1437,996),(1437,1023),(1273,1023),(1273,881),(1398,881)])),
 'WTC5':dict(stories=9,height=36.6,base=trace([(1195,357),(1355,357),(1355,389),(1525,389),(1525,489),(1499,489),(1499,624),(1396,624),(1396,519),(1195,519)]),upper=trace([(1195,357),(1355,357),(1355,389),(1525,389),(1525,489),(1499,489),(1499,624),(1396,624),(1396,431),(1195,431)])),
 'WTC6':dict(stories=8,height=28.0,base=trace([(805,341),(973,341),(973,363),(1133,363),(1133,468),(984,468),(984,519),(866,519),(866,450),(805,450)]),upper=trace([(805,341),(973,341),(973,363),(1133,363),(1133,468),(984,468),(984,519),(866,519),(866,450),(805,450)])),
}


def mark_world(col):
    # These objects already use registered site coordinates.
    for o in col.objects:o['site_registered']='world-space-original-plan-trace';o['site_world_annotations_synced']=True


def lowrises():
    wall=finish('PODIUM_dark_anodized_spandrel',(.13,.16,.155),.62,.39,900)
    silver=finish('PODIUM_extruded_aluminum',(.32,.35,.34),.86,.28,700)
    glass=finish('PODIUM_bronze_glazing',(.055,.095,.088),.36,.19)
    bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=.40
    stone=finish('PODIUM_hotel_precast',(.55,.52,.46),.02,.70,750)
    concrete=finish('PODIUM_concrete_slabs',(.40,.41,.38),0,.87,800)
    for tower,spec in FOOTPRINTS.items():
        for c in bpy.data.collections:
            if c.name.startswith(tower) and c.asset_data:
                c.hide_render=True;c.hide_viewport=True;c['superseded_by']=tower+'_SOURCE_outline_architecture';c.asset_clear()
        c=collection(tower+'_SOURCE_outline_architecture',bpy.context.scene.collection,SOURCE,LIMIT)
        c['base_outline_world_m']=[v for p in spec['base'] for v in p];c['upper_outline_world_m']=[v for p in spec['upper'] for v in p]
        p=Parts(tower+'_SOURCE',c);roof=PLAZA_Z+spec['height'];step=spec['height']/spec['stories'];mat=stone if tower=='WTC3' else wall
        for n in range(spec['stories']+1):
            z=PLAZA_Z+n*step;poly=spec['base'] if n<=1 else spec['upper']
            m=slab_mesh(tower+('_podium_slab' if n<=1 else '_upper_slab'),poly,[],.18,concrete)
            ob=p.mesh(f'floor{n:02d}',m,(0,0,z),kind='podium_floor');ob['floor']=n
        # Two-level set-back volumes replace oversized intersecting rectangles.
        for phase,poly,z0,z1 in ((0,spec['base'],PLAZA_Z,PLAZA_Z+step),(1,spec['upper'],PLAZA_Z+step,roof)):
            glazing=Batch(tower+f'_phase{phase}_individual_glazing',glass);frames=Batch(tower+f'_phase{phase}_frames',silver);panels=Batch(tower+f'_phase{phase}_spandrels',mat)
            stories=1 if phase==0 else spec['stories']-1
            for a,b in zip(poly,poly[1:]+poly[:1]):
                length=math.dist(a,b);tx,ty=(b[0]-a[0])/length,(b[1]-a[1])/length;nx,ny=ty,-tx
                count=max(1,round(length/(2.35 if tower=='WTC3' else 1.7)));pitch=length/count
                def point(u,d,z):return (a[0]+tx*u+nx*d,a[1]+ty*u+ny*d,z)
                def bar(batch,u0,u1,z,width,depth=.08):batch.bar(point(u0,0,z),point(u1,0,z),[(-depth/2,-width/2),(depth/2,-width/2),(depth/2,width/2),(-depth/2,width/2)])
                for floor in range(stories):
                    bottom=z0+floor*step;gh=step*(.68 if tower!='WTC3' else .60)
                    bar(panels,0,length,bottom+(step-gh)/2,step-gh,.16)
                    bar(frames,0,length,bottom+step,.075,.16)
                    for j in range(count):
                        lo=j*pitch+.055;hi=(j+1)*pitch-.055
                        bar(glazing,lo,hi,bottom+step-gh/2,gh-.08,.016)
                        frames.bar(point(j*pitch,0,bottom),point(j*pitch,0,bottom+step),[(-.035,-.08),(.035,-.08),(.035,.08),(-.035,.08)])
                        if tower=='WTC3':frames.bar(point(j*pitch,-.10,bottom),point(j*pitch,-.10,bottom+step),[(-.11,-.12),(.11,-.12),(.11,.12),(-.11,.12)])
                bar(frames,0,length,z1+.28,.16,.32)
                bar(panels,0,length,z1+.10,.40,.20)
            for batch,kind in ((glazing,'podium_glazing'),(frames,'podium_frame'),(panels,'podium_spandrel')):batch.mesh(c,kind)
        # Source outline determines positions; equipment specifications remain types.
        x=sum(v[0] for v in spec['upper'])/len(spec['upper']);y=sum(v[1] for v in spec['upper'])/len(spec['upper'])
        p.box('service_bulkhead',(x,y,roof+1.4),(5,6,2.8),mat,kind='podium_roof_bulkhead')
        for k in (-1,1):
            hx=x+k*4.4
            p.box(f'AHU{k}',(hx,y,roof+.85),(2.4,4.0,1.5),silver,kind='podium_roof_equipment_TYPE')
            for j in range(12):p.box(f'AHU{k}_louver{j}',(hx,y-2.025,roof+.3+j*.10),(2.15,.055,.035),wall)
            for j in (-1,1):
                p.disk(f'AHU{k}_fan_ring{j}',(hx,y+j*.9,roof+1.62),.64,.07,wall)
                p.disk(f'AHU{k}_fan_hub{j}',(hx,y+j*.9,roof+1.70),.11,.04,silver)
                for blade in range(8):
                    t=blade*math.tau/8;p.box(f'AHU{k}_fan{j}_{blade}',(hx+.33*math.cos(t),y+j*.9+.33*math.sin(t),roof+1.71),(.52,.095,.025),silver,t+.35)
                for zz in (0,.45):p.tube(f'AHU{k}_pipe{j}_{zz}',(hx+j*.9,y+2,roof+.6+zz),(x+j,y+3.2,roof+.6+zz),.045,silver)
        mark_world(c)


def parking():
    limit='Simplified fitted parking architecture, not recovered WTC basement plan: two decks, reinforced-concrete grid, ramp, bay markings, kerbs and light fixtures. Bounds/columns/services fitted; original PATH, loading docks and utilities not represented.'
    c=collection('SITE_parking_structure_CG_TYPE',bpy.context.scene.collection,'User request; original B1/B2 level datums as architectural references only',limit,(89,10))
    p=Parts('PARKING',c);con=finish('PARKING_trowelled_concrete',(.33,.34,.31),0,.90,950);paint=finish('PARKING_lane_paint',(.82,.75,.49),0,.75)
    steel=finish('PARKING_fixture_metal',(.24,.28,.28),.75,.40);light=finish('PARKING_lamp_diffuser',(.80,.84,.78),0,.30)
    bs=light.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(.85,.91,1,1);bs.inputs['Emission Strength'].default_value=3
    ramp=[(110,-30),(118,-30),(118,65),(110,65)]
    for n,z in enumerate((-7.9248,-4.8768,-1.8288)):
        slab=slab_mesh('PARKING_slab_open_ramp_'+str(n),[(50,-90),(130,-90),(130,150),(50,150)],[ramp] if n else [],.22,con)
        o=p.mesh('deck'+str(n),slab,(0,0,z),kind='parking_slab');o['level']=n;o['finished_z_m']=z
    for level,z in enumerate((-7.9248,-4.8768)):
        beams=Batch('PARKING_level'+str(level)+'_beam_grid',con)
        for ix in range(7):
            x=54+ix*12
            for j in range(20):
                y=-84+j*12
                if 109<x<120 and -35<y<70:continue
                p.box(f'column_{level}_{ix}_{j}',(x,y,z+1.4144),(.55,.55,2.8288),con,kind='parking_column')
                # Cross grid beams stop at the open ramp slot.
                spans=[(-90,150)] if not 109<x<120 else [(-90,-30),(65,150)]
                for a,b in spans:beams.box((x,(a+b)/2,z+2.59),(.30,b-a,.48))
        for y in range(-84,145,12):
            for a,b in ([(50,110),(118,130)] if -30<y<65 else [(50,130)]):beams.box(((a+b)/2,y,z+2.61),(b-a,.30,.44))
        beams.mesh(c,'parking_beams')
        for row,x in enumerate((63,81,99,123)):
            for j in range(82):
                y=-87+j*2.8
                # Keep bays clear of columns and the ramp approach.
                if any(abs(x-(54+k*12))<2.8 and abs(y-(-84+round((y+84)/12)*12))<1.7 for k in range(7)):continue
                for side in (-1,1):p.box(f'bay_{level}_{row}_{j}_{side}',(x,y+side*1.35,z+.008),(5,.06,.016),paint,kind='parking_bay_line')
                p.box(f'wheelstop_{level}_{row}_{j}',(x-2.05,y,z+.075),(.16,1.65,.15),con)
        for x in (73,91):
            for j,y in enumerate(range(-72,145,24)):
                p.box(f'lamp_body_{level}_{x}_{j}',(x,y,z+2.48),(.18,1.25,.08),steel)
                p.box(f'lamp_lens_{level}_{x}_{j}',(x,y,z+2.435),(.13,1.15,.012),light)
        for y in (-90,150):p.box(f'kerb_{level}_{y}',(90,y,z+.12),(80,.20,.24),con)
    # Continuous 8.34% straight ramp passes both decks; broad slab openings
    # provide vehicle clearance over its whole route. No invented historical route.
    a,b=(114,-30,-7.9248),(114,65,0)
    t=Batch('PARKING_ramp_and_edge_kerbs',con)
    t.bar(a,b,[(-3.5,-.20),(3.5,-.20),(3.5,0),(-3.5,0)])
    t.bar((110.6,-30,-7.9248),(110.6,65,0),[(-.10,0),(.10,0),(.10,.25),(-.10,.25)])
    t.bar((117.4,-30,-7.9248),(117.4,65,0),[(-.10,0),(.10,0),(.10,.25),(-.10,.25)])
    t.mesh(c,'parking_ramp');c['ramp_grade_CG']=7.9248/95;c['minimum_under_beam_clearance_m']=2.35;c['historical_as_built']=False


def apply():
    if bpy.context.scene.get('podium_parking_revision')==VERSION:return
    lowrises();parking();bpy.context.scene['podium_parking_revision']=VERSION
