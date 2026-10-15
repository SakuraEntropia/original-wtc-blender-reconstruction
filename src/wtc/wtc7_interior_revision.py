"""NIST7-2/3/6 elevator/core topology and explicitly fitted interior types."""
import math
import bpy
from .interior_parts import Parts,collection,finish,lift
from .lobby_plan_revision import slab_mesh

VERSION='2026-10-16-wtc7-interior-v1'
SOURCE='https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=861611; NIST1-9 Figs2-3,7-2,7-3,7-6,pp48-49,311-312'
LIMIT='NIST spatial/program reference manually fitted to existing staged trapezoid; small sections, absolute floor registration, furniture and finish are CG types; unknown tenant rooms omitted'


def register_lamps():
    col=bpy.data.collections['WTC7_INTERIOR_NIST_core_and_public_lobbies']
    for level in (1,3):
        for j in range(8):
            ceiling=7.62 if level==1 else 15.315 if j<4 else 11.43
            col.objects[f'WTC7_INSIDE_lobby_lamp{level}_{j}'].location.z=ceiling-.12
            col.objects[f'WTC7_INSIDE_lobby_light{level}_{j}'].location.z=ceiling-.16


def apply():
    if bpy.context.scene.get('wtc7_interior_revision')==VERSION:register_lamps();return
    shell=bpy.data.objects['WTC7_47_story_envelope'];corners=[shell.matrix_world@v.co for v in list(shell.data.vertices)[:4]]
    xy=(sum(v.x for v in corners)/4,sum(v.y for v in corners)/4)
    ring=[(v.x-xy[0],v.y-xy[1]) for v in corners]
    col=collection('WTC7_INTERIOR_NIST_core_and_public_lobbies',bpy.data.collections['WTC7__NIST_massing_position_schematic'],SOURCE,LIMIT,xy)
    p=Parts('WTC7_INSIDE',col,xy)
    concrete=finish('W7_concrete',(.43,.43,.39),0,.85,250);stone=finish('W7_polished_stone',(.42,.30,.21),0,.3,130)
    metal=finish('W7_lift_metal',(.40,.43,.42),.88,.24,400);mirror=finish('W7_lift_mirror',(.45,.52,.53),.95,.08)
    wall=finish('W7_gypsum',(.68,.66,.59),0,.85,180);carpet=finish('W7_carpet_TYPE',(.15,.16,.13),0,.95,1500)
    rows={};roof=610*.3048;f46=roof-28*.3048;f24=f46-22*12.75*.3048;f22=f24-28*.3048;f7=f22-15*12.75*.3048
    for n in range(7,48):rows[n]=f7+(n-7)*12.75*.3048 if n<22 else f22+(n-22)*14*.3048 if n<24 else f24+(n-24)*12.75*.3048 if n<46 else f46+(n-46)*14*.3048
    rows.update({1:0,2:3.81,3:7.62,4:11.43,5:15.315,6:19.30})
    cars=[]
    for bank in range(4):
        for j in range(5):cars.append((-23+bank*7,-12+j*3.7,(13,21,28,35)[bank]))
    for j in range(8):cars.append((7+(j//4)*3.2,-12+(j%4)*3.7,45))
    cars.extend(((19,-8,45),(19,-3,45),(19,3,46)))
    holes=[[(x-1.55,y-1.75),(x+1.55,y-1.75),(x+1.55,y+1.75),(x-1.55,y+1.75)] for x,y,_ in cars]
    holes += [[(-34,-4),(-30,-4),(-30,4),(-34,4)],[(24,-4),(28,-4),(28,4),(24,4)]]
    typical=slab_mesh('WTC7_5p5in_typical_slab',ring,holes,.1397,concrete)
    lower=slab_mesh('WTC7_lower_lobby_slab',ring,holes,.20,stone)
    for level,z in rows.items():
        if level==2:continue  # lobby is open at the mezzanine, not a filled plate
        if level==4:
            m=slab_mesh('WTC7_floor4_open_south_atrium',ring,holes+[[(-60,-30),(60,-30),(60,-13),(-60,-13)]],.1397,concrete)
        else:m=typical if level>=7 else lower
        ob=p.mesh(f'floor{level:02d}',m,(0,0,z),kind='wtc7_floor_slab');ob['floor']=level;ob['elevation_confidence']='Typical pitch and roof anchored; lower absolute datums fitted'
    for i,(x,y,topfloor) in enumerate(cars):
        top=rows[topfloor]+3
        for side in (-1,1):p.box(f'shaft{i}_side{side}',(x+side*1.48,y,top/2),(.12,3.4,top),wall,kind='wtc7_shaft_enclosure')
        p.box(f'shaft{i}_back',(x,y+1.68,top/2),(3.08,.12,top),wall)
        lift(p,f'lift{i+1:02d}',(x,y),rows[3]+.01,top,metal,mirror,stone,i==0,8)
        o=col.objects.get(f'WTC7_INSIDE_lift{i+1:02d}_floor');o['elevator_number']=i+1;o['top_service_floor_reference']=topfloor
    # Two independently selectable stairs, with physical flights and railings.
    for side,x in ((0,-32),(1,26)):
        for level in range(3,46):
            a=rows[level];b=rows[level+1];rise=(b-a)/2;n=12
            for flight in (0,1):
                direction=1 if flight==0 else -1
                for j in range(n):
                    y=direction*(-1.7+j*.28);z=a+flight*rise+(j+1)*rise/n
                    p.box(f'stair{side}_F{level}_{flight}_{j}',(x+flight*1.1,y,z),(1.04,.29,.10),concrete,kind='wtc7_stair_tread')
                p.tube(f'stair_rail{side}_{level}_{flight}',(x+flight*1.1-.48,-direction*1.7,a+flight*rise+.95),(x+flight*1.1-.48,direction*1.38,a+(flight+1)*rise+.95),.023,metal)
            p.box(f'stair_landing{side}_{level}',(x+.55,1.8,a+rise),(2.2,1.0,.12),concrete)
    # Source-confirmed street/main-lobby escalators, with estimated mechanisms.
    for bank,x in enumerate((7.5,10.2)):
        n=48;run=rows[3]/math.tan(math.pi/6)
        for j in range(n):
            y=-18+j*run/n;z=(j+.5)*rows[3]/n
            p.box(f'escalator{bank}_step{j}',(x,y,z),(1.05,run/n+.005,.09),metal,kind='wtc7_escalator_tread')
        for s in (-1,1):p.tube(f'escalator{bank}_rail{s}',(x+s*.58,-18,.95),(x+s*.58,-18+run,rows[3]+.95),.055,metal)
    for j in range(15):
        a=j*math.pi/28
        p.box('fire_command_desk'+str(j),(24+3.2*math.cos(a),7+3.2*math.sin(a),rows[3]+.57),(.75,.8,1.14),stone,a+math.pi/2,'wtc7_fire_command_fitout')
    # Limited, explicitly generic office fit-out, not fabricated tenant plans.
    for i in range(12):
        x=-28+(i%6)*10;y=12+(i//6)*5;z=rows[12]
        p.box('office_carpet'+str(i),(x,y,z+.009),(9.7,4.7,.018),carpet)
        p.box('office_desk'+str(i),(x,y,z+.75),(1.6,.8,.055),stone,kind='office_furniture_TYPE')
        for s in (-1,1):p.box(f'office_desk_leg{i}_{s}',(x+s*.65,y,z+.35),(.065,.65,.7),metal)
        p.box('office_CRT'+str(i),(x,y+.15,z+1.02),(.39,.38,.35),metal)
    for level in (1,3):
        for j in range(8):
            x=-28+(j%4)*18;y=-18+(j//4)*34
            p.box(f'lobby_lamp{level}_{j}',(x,y,rows[level]+3.4),(.6,.6,.06),metal)
            p.area(f'lobby_light{level}_{j}',(x,y,rows[level]+3.36),95,2.2)
    col['elevator_count']=31;col['source_typical_slab_total_m']=.1397;col['floor3_fitted_z_m']=rows[3]
    col['fitout_scope']='Source core/public-lobby topology; full unknown tenant interiors and proprietary artwork not recreated'
    register_lamps()
    bpy.context.scene['wtc7_interior_revision']=VERSION
