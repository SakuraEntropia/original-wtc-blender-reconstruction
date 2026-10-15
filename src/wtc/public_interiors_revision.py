"""Source-labelled public interiors; furniture and small sections are CG fits."""
import math
import bpy
from .interior_parts import Parts,collection,finish,profile,lift
from .lobby_plan_revision import well,slab_mesh
from .facade_revision import _prism_profile,_mesh
from .completion import PLAZA_Z

VERSION='2026-10-16-public-interiors-v1'
CARPET='https://www.taipingcarpets.com/projects/twin-towers-at-world-trade-center-ny'
WINDOWS='https://www.architecturalrecord.com/ext/resources/archives/news/wtc/archives/windows1977.pdf'
LIMIT='Self-modelled CG fit; source spatial/material characteristics, not surveyed furniture, finish or machinery dimensions'


def lobby(tower,xy):
    col=collection(tower+'_LOBBY_stone_carpet_lamps_DETAIL',bpy.data.collections[tower+'_LOBBY_photo_interpretation_STUDY'],CARPET,LIMIT,xy)
    p=Parts(tower+'_PUBLIC',col,xy,0 if tower=='WTC1' else math.pi/2)
    stone=finish('PI_honed_travertine',(.57,.52,.40),0,.38,95)
    # Layered veining and fine pores remain procedural, with object-level cuts.
    n=stone.node_tree.nodes;l=stone.node_tree.links;bs=n.get('Principled BSDF')
    if not stone.get('layered_stone'):
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=2.7;tex.inputs['Detail'].default_value=4;tex.inputs['Roughness'].default_value=.72
        coord=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(3,3,27)
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.26,.22,.15,1);ramp.color_ramp.elements[0].position=.20;ramp.color_ramp.elements[1].color=(.67,.61,.47,1)
        l.new(coord.outputs['Object'],scale.inputs[0]);l.new(scale.outputs[0],tex.inputs['Vector']);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color']);stone['layered_stone']=True
    metal=finish('PI_brushed_bronze',(.37,.25,.10),.85,.25,320)
    terra=finish('PI_terrazzo',(.56,.53,.44),0,.47,800)
    rugs=[finish('PI_carpet_red'+str(i),(.24+i*.012,.025+i*.004,.022+i*.003),0,.96,1700) for i in range(4)]
    for old in bpy.data.objects:
        if old.name.startswith(tower+'_LP_outer_carpet_'):old.hide_render=True;old.hide_viewport=True
        if old.name.startswith(tower+'_LR_') and '_pier_' in old.name:old.data.materials[0]=stone
    zones=[(x,s*25,12.192,6.096) for s in (-1,1) for x in (-18.288,-6.096,6.096,18.288)]
    zones += [(s*25,y,6.096,12.192) for s in (-1,1) for y in (-6.096,6.096)]
    holes=[well(-1),well(1),[(22,3.5),(25.8,3.5),(25.8,18),(22,18)]]
    for level,z in enumerate((.24,PLAZA_Z)):
        for i,(x,y,w,d) in enumerate(zones):
            ring=[(x-w/2+.07,y-d/2+.07),(x+w/2-.07,y-d/2+.07),(x+w/2-.07,y+d/2-.07),(x-w/2+.07,y+d/2-.07)]
            m=slab_mesh(f'{tower}_carpet_{level}_{i}',ring,holes if level else [],.012,rugs[i%4])
            if not m.polygons:bpy.data.meshes.remove(m);continue
            o=p.mesh(f'carpet_zone{level}_{i}',m,(0,0,z+.018),kind='carpet_zone');o['source_zone_ft']=[20,40];o['clipped_to_mezzanine']=bool(level)
            # Flush metal strips delimit zones; uncarpeted floor supplies terrazzo.
            if not level:
                for s in (-1,1):
                    p.box(f'jointX{i}_{s}',(x+s*w/2,y,z+.002),(.008,d,.004),metal)
                    p.box(f'jointY{i}_{s}',(x,y+s*d/2,z+.002),(w,.008,.004),metal)
    # Individually jointed stone reveals on the curved platform edge.
    for side in (-1,1):
        path=well(side)
        for j,(a,b) in enumerate(zip(path,path[1:])):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            p.box(f'stone_fascia{side}_{j}',((a[0]+b[0])/2,(a[1]+b[1])/2,PLAZA_Z-.29),(length-.006,.055,.54),stone,math.atan2(dy,dx),'jointed_stone_fascia')
    for i,(x,y) in enumerate([(x,s*25) for s in (-1,1) for x in (-18,-6,6,18)]+[(s*25,y) for s in (-1,1) for y in (-8,8)]):
        p.box('lamp_mount'+str(i),(x,y,21.70),(.51,.51,.055),metal)
        p.tube('lamp_stem'+str(i),(x,y,21.67),(x,y,21.27),.018,metal)
        p.box('lamp_case'+str(i),(x,y,21.09),(.46,.46,.36),metal)
        lens=finish('PI_warm_opal_glass',(.85,.72,.43),0,.26)
        bs=lens.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.76,.40,1);bs.inputs['Emission Strength'].default_value=3
        p.box('lamp_lens'+str(i),(x,y,20.90),(.39,.39,.018),lens)
        p.area('lamp_light'+str(i),(x,y,20.86),130,1)
    return col


def open_lift_portal(tower,xy,col):
    p=Parts(tower+'_LIFT',col,xy)
    stone=bpy.data.materials['PI_honed_travertine']
    hx,hy=((137*.3048/2,87*.3048/2) if tower=='WTC1' else (87*.3048/2,137*.3048/2))
    count=max(6,round(hx*2/3.05));bay=count//2;u=-hx+(bay+.5)*hx*2/count
    for label in ('portal','leafL','leafR'):
        o=bpy.data.objects.get(f'{tower}_LR_core_s0_concourse_{label}_{bay}_STUDY')
        if o:o.hide_render=True;o.hide_viewport=True
    old=bpy.data.objects[tower+'_LR_core_s0_opaque_inner_wall_STUDY']
    old.hide_render=True;old.hide_viewport=True
    if col.objects.get(tower+'_LIFT_core_backing_left'):return
    top=old.dimensions.z
    for name,a,b in (('left',-hx,u-.9),('right',u+.9,hx)):
        p.box('core_backing_'+name,((a+b)/2,-hy+.17,top/2),(b-a,.12,top),stone)
    p.box('core_backing_head',(u,-hy+.17,(top+2.8)/2),(1.8,.12,top-2.8),stone)
    p.box('portal_head_infill',(u,-hy-.02,3.21),(hx*2/count-.66,.18,.96),stone)


def elevators(tower,xy):
    col=collection(tower+'_ELEVATOR_cab_and_mechanism_TYPE',bpy.data.collections[tower+'_COMPLETION_study'],'NIST1-7 elevator/sky-lobby functions; mechanical sections are CG types',LIMIT,xy)
    p=Parts(tower+'_LIFT',col,xy)
    metal=finish('PI_elevator_stainless',(.43,.46,.44),.86,.26,500)
    glass=finish('PI_elevator_mirror',(.54,.59,.57),.96,.08)
    stone=finish('PI_elevator_floor',(.19,.17,.12),0,.35,150)
    hx,hy=((137*.3048/2,87*.3048/2) if tower=='WTC1' else (87*.3048/2,137*.3048/2))
    count=max(6,round(hx*2/3.05));bay=count//2;u=-hx+(bay+.5)*hx*2/count
    open_lift_portal(tower,xy,col)
    lift(p,'inspection_car',(u,-hy+.975),.24,7.0,metal,glass,stone,True,16)
    p.area('cab_light',(u,-hy+.975,2.72),35,1.2,(1,.86,.64))
    return col


def windows():
    tower='WTC1';xy=(-55,55)
    col=collection('WTC1_WINDOWS_1977_Platner_STUDY',bpy.data.collections[tower+'_COMPLETION_study'],WINDOWS,LIMIT+'; 1976/1977 period, not1996/2001 fit-out',xy)
    col['period']='1976/1977';p=Parts('WTC1_WINDOWS1977',col,xy)
    z=bpy.data.collections[tower+'_crown_curved_cladding']['source_FIN107_z_m']
    gold=finish('WOW_brass',(.52,.35,.12),.85,.24);cream=finish('WOW_ivory_laminate',(.76,.70,.53),.05,.35)
    carpet=finish('WOW_warm_wool',(.25,.16,.075),0,.94,1600);cloth=finish('WOW_linen',(.86,.82,.68),0,.9,1100)
    seat=finish('WOW_moss_upholstery',(.19,.23,.105),0,.85,700);wood=finish('WOW_walnut',(.13,.055,.021),0,.35,100)
    glass=finish('WOW_mirrored_glass',(.47,.59,.58),.78,.10)
    for o in bpy.data.objects:
        if o.name.startswith('WTC1_public_top_table_') or o.name.startswith('WTC1_public_top_table_leg_'):o.hide_render=True;o.hide_viewport=True
    # Terraced perimeter dining; geometry follows the published spatial account.
    for side in (-1,1):
        p.box('west_east_carpet'+str(side),(side*25,0,z+.018),(10,58,.036),carpet)
        p.box('north_south_carpet'+str(side),(0,side*25,z+.018),(40,10,.036),carpet)
    table_i=0
    for region in ('north','east','west','southeast'):
        for row in range(2):
            for j in range(7 if region!='southeast' else 4):
                if region=='north':x,y=-17+j*5.6,25+row*3
                elif region=='east':x,y=25+row*3,-12+j*5.8
                elif region=='west':x,y=-25-row*3,-21+j*7
                else:x,y=16+j*3.3,-24-row*3
                zz=z+row*.24
                if row:p.box(f'terrace{region}_{j}',(x,y,z+.12),(3.6,3.4,.24),carpet)
                p.disk(f'table{table_i}',(x,y,zz+.74),.70,.05,cloth,'restaurant_table')
                p.tube(f'table_leg{table_i}',(x,y,zz+.03),(x,y,zz+.74),.045,gold)
                for k in range(4):
                    a=k*math.pi/2;cx,cy=x+math.cos(a)*1.05,y+math.sin(a)*1.05
                    p.box(f'chair{table_i}_{k}',(cx,cy,zz+.47),(.48,.48,.12),seat,a,'restaurant_chair')
                    p.box(f'chair_back{table_i}_{k}',(cx+math.cos(a)*.20,cy+math.sin(a)*.20,zz+.78),(.10,.49,.55),seat,a)
                    for s in (-1,1):p.tube(f'chair_leg{table_i}_{k}_{s}',(cx+s*.17,cy,zz+.04),(cx+s*.17,cy,zz+.43),.018,gold)
                table_i+=1
    # West banquet divisions and low mirrored banquettes preserve sight lines.
    for i in range(6):p.box('banquet_partition'+str(i),(-25,-17+i*7,z+1.35),(9,.10,2.7),wood)
    p.box('bar_counter',(22,-20,z+1.1),(13,1.1,.14),wood)
    for j in range(11):p.box('bar_front'+str(j),(16+j*1.15,-20,z+.52),(1.10,.8,1),wood)
    p.box('back_bar',(22,-17.8,z+1.35),(13,.45,2.7),gold)
    for j in range(30):
        p.tube('bottle'+str(j),(16.2+j*.39,-18,z+1.2),(16.2+j*.39,-18,z+1.47),.045,glass)
    # Glass-gallery arches; fine planar strips, with no murals or copied artwork.
    for j in range(9):
        x=-17+j*4.2
        for k in range(20):
            a=k*math.pi/20;b=(k+1)*math.pi/20
            p.tube(f'gallery_arch{j}_{k}',(x,-20+1.35*math.cos(a),z+1.8+1.35*math.sin(a)),(x,-20+1.35*math.cos(b),z+1.8+1.35*math.sin(b)),.025,gold)
        p.box('gallery_mirror'+str(j),(x,-18.6,z+1.5),(.018,.05,3),glass)
    for side in range(4):
        for axis in range(59):
            a=axis*1.016-29*1.016
            pts=[(.17*math.cos(t*math.pi/20),.17*math.sin(t*math.pi/20)) for t in range(21)]
            pts += [(.158*math.cos(t*math.pi/20),.158*math.sin(t*math.pi/20)) for t in range(20,-1,-1)]
            ob=p.mesh(f'ivory_half_column{side}_{axis}',profile(pts,3.6576,cream),(a,-30.95,z+.03),kind='restaurant_half_column')
            c,s=math.cos(side*math.pi/2),math.sin(side*math.pi/2);ob.location=p.point((a*c+30.95*s,a*s-30.95*c,z+.03));ob.rotation_euler.z=side*math.pi/2
    for j,(x,y) in enumerate(((-25,12),(-25,-12),(25,12),(25,-12),(0,25),(0,-25))):
        p.box('ceiling_lamp'+str(j),(x,y,z+3.48),(.7,.7,.05),gold);p.area('dining_light'+str(j),(x,y,z+3.44),80,3)
    col['floor_z_m']=z;col['ceiling_clear_height_reference_m']=3.6576


def restaurant_enclosure():
    col=bpy.data.collections['WTC1_WINDOWS_1977_Platner_STUDY']
    if col.get('enclosure_complete'):return
    p=Parts('WTC1_WINDOWS1977',col,(-55,55));z=col['floor_z_m']
    cream=bpy.data.materials['WOW_ivory_laminate'];gold=bpy.data.materials['WOW_brass'];carpet=bpy.data.materials['WOW_warm_wool']
    ring=[(-30.88,-30.88),(30.88,-30.88),(30.88,30.88),(-30.88,30.88)]
    core=[(-20.9,-13.26),(-20.9,13.26),(20.9,13.26),(20.9,-13.26)]
    p.mesh('floor_finish',slab_mesh('WOW_floor_finish',ring,[core],.018,carpet),(0,0,z+.118),kind='restaurant_floor_finish')
    p.mesh('ceiling',slab_mesh('WOW_ceiling_ring',ring,[core],.08,cream),(0,0,z+3.7376),kind='restaurant_ceiling')
    for side in (-1,1):
        p.box('core_east_west'+str(side),(side*20.88,0,z+1.84),(.10,26.52,3.68),cream)
        p.box('core_north_south'+str(side),(0,side*13.24,z+1.84),(41.76,.10,3.68),cream)
        p.box('window_headX'+str(side),(0,side*30.87,z+3.53),(61.9,.14,.26),cream)
        p.box('window_headY'+str(side),(side*30.87,0,z+3.53),(.14,61.9,.26),cream)
    # Four physical legs and softened upholstery edges; all are fitted types.
    for ob in list(col.objects):
        if ob.get('module')=='restaurant_chair' or '_chair_back' in ob.name:
            mod=ob.modifiers.new('Upholstery edge radius TYPE','BEVEL');mod.width=.018;mod.segments=3
        if '_chair_leg' in ob.name:
            ob.location.y-=.17
            other=ob.copy();other.data=ob.data;other.name=ob.name+'_rear';col.objects.link(other);other.location.y+=.34
        if ob.type=='LIGHT':ob.data.energy=170
    col['enclosure_complete']=True


def apply():
    scene=bpy.context.scene
    if scene.get('public_interiors_revision')!=VERSION:
        for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):lobby(tower,xy);elevators(tower,xy)
        windows()
    for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):open_lift_portal(tower,xy,bpy.data.collections[tower+'_ELEVATOR_cab_and_mechanism_TYPE'])
    restaurant_enclosure();scene['public_interiors_revision']=VERSION
