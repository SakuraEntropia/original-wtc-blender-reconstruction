"""Render reproducible review states without rebuilding the scene."""
from pathlib import Path
import sys,bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
VIEWS={'overview':'CAM_overview','site_plan':'CAM_site_plan','trident':'CAM_trident','lobby':'CAM_lobby_inside',
 'globe':'CAM_plaza_globe','roof1':'CAM_roof_WTC1','roof2':'CAM_roof_WTC2','antenna':'CAM_antenna',
 'mep':'CAM_MEP_cutaway','hat_truss':'CAM_hat_truss','core':'CAM_core_cutaway','steel_panels':'CAM_segmented_steel',
 'section':'CAM_steel_cover_section','wtc7':'CAM_WTC7','lowrise':'CAM_WTC3_6','roof_plan':'CAM_roof_plan',
 'crown':'CAM_crown_detail','core_top':'CAM_core_roof_connection','plaza':'CAM_plaza_furniture',
 'mep_detail':'CAM_industrial_type_components','facade_corner':'CAM_facade_corner',
 'sky_lobby':'CAM_sky_lobby_band','wtc7_roof':'CAM_WTC7_roof',
 'lobby_ceiling':'CAM_lobby_ceiling','paving_seam':'CAM_paving_seam','cap_structure':'CAM_cap_structure'}

def camera(name,loc,target,scale):
    ob=bpy.data.objects.get(name)
    if not ob:
        data=bpy.data.cameras.new(name);data.type='ORTHO';data.clip_end=10000;data.clip_start=.05
        ob=bpy.data.objects.new(name,data);bpy.data.collections['REVIEW_CAMERAS'].objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.ortho_scale=scale
    return ob

def create_detail_cameras():
    camera('CAM_crown_detail',(100,-160,433),(69,-85,404),46)
    camera('CAM_core_roof_connection',(116,-117,449),(55,-55,409),76)
    camera('CAM_plaza_furniture',(0,-40,135),(0,0,9),106)
    camera('CAM_industrial_type_components',(-66,33,416),(-74,43,409.6),16)
    camera('CAM_plaza_globe',(0,-38,26),(0,0,9),62)
    camera('CAM_segmented_steel',(253,-154,10),(245,-140,5.3),14.5)
    camera('CAM_facade_corner',(99,-104,109),(85.9,-85.9,103),15)
    z=1362*.3048*77/110
    camera('CAM_sky_lobby_band',(94,-133,z+8),(68,-86.6,z+4),25)
    camera('CAM_WTC7_roof',(69,135,250),(-20,230,188),138)
    camera('CAM_paving_seam',(27,-15,32),(15,-6,6.74),24)
    ob=camera('CAM_lobby_ceiling',(78,-81,12),(70,-73,21),36)
    ob.data.type='PERSP';ob.data.lens=22
    camera('CAM_cap_structure',(113,-124,438),(83,-83,414),27)

def child(root,prefix):return next((c for c in root.children if c.name.startswith(prefix)),None)

def render_reviews(keys=None):
    scene=bpy.context.scene;scene.eevee.shadow_pool_size='2048'
    requested=next((a.split('=',1)[1].split(',') for a in sys.argv if a.startswith('--views=')),None)
    keys=keys or requested or list(VIEWS)
    if keys==['none']:
        scene.camera=bpy.data.objects['CAM_overview'];return
    for key in keys:
        state=[]
        def visibility(items,hidden):
            for item in items:
                if item is None:continue
                state.append((item,item.hide_render));item.hide_render=hidden
        def exterior_hidden(name):
            root=bpy.data.collections[name];completion=bpy.data.collections[name+'_COMPLETION_study']
            visibility([child(root,p) for p in ('01_envelope','02_perimeter','06_glazing',name+'_CROWN',name+'_CORNER',name+'_FACADE_REVISION')],True)
            visibility([c for c in root.children if c.name.startswith(name+'_CROWN_CAP')],True)
            visibility([child(completion,p) for p in ('roof_mechanical',name+'_ROOF')],True)
            visibility([bpy.data.objects[name+'_roof_datum']],True)
            if name=='WTC1':visibility([bpy.data.collections.get('WTC1_antenna_photo_interpretation_STUDY') or bpy.data.collections.get('WTC1_antenna_lattice_STUDY'),bpy.data.collections.get('WTC1_ROOF_auxiliary_antenna_interpretation')],True)
            return completion
        try:
            if key in ('mep','mep_detail','hat_truss'):
                completion=exterior_hidden('WTC1')
                visibility([bpy.data.collections['WTC2'],bpy.data.collections['WTC2_COMPLETION_study']],True)
                visibility([child(completion,'MEP_108_109_type_reference') if key!='hat_truss' else child(completion,'hat_truss_structure')],False)
            elif key in ('core','core_top'):
                completion=exterior_hidden('WTC2');visibility([child(completion,'roof_observation')],True)
                visibility([bpy.data.collections['WTC1'],bpy.data.collections['WTC1_COMPLETION_study'],bpy.data.collections.get('WTC1_antenna_photo_interpretation_STUDY') or bpy.data.collections.get('WTC1_antenna_lattice_STUDY')],True)
                visibility([child(completion,'47_core_columns'),child(completion,'WTC2_CORE_roof_connections')],False)
                if key=='core_top':visibility([child(completion,'hat_truss_structure')],False)
                else:visibility(list(child(completion,'skylobby_and_MEP').objects),False)
            elif key=='steel_panels':visibility([bpy.data.collections['WTC_TYPICAL_STEEL_PANEL_STUDY']],False)
            elif key=='section':visibility(list(bpy.data.collections['SECTION_REVIEW_steel_and_aluminum'].objects),False)
            elif key=='cap_structure':visibility([bpy.data.collections.get('WTC2_CROWN_CAP_mitered_panels')],True)
            scene.camera=bpy.data.objects[VIEWS[key]];scene.render.filepath=str(ROOT/'renders'/('detail_'+key+'.png'))
            print('REVIEW_START '+key,flush=True);bpy.ops.render.render(write_still=True);print('REVIEW_DONE '+key,flush=True)
        finally:
            for item,old in reversed(state):item.hide_render=old
    scene.camera=bpy.data.objects['CAM_overview']

if __name__=='__main__':create_detail_cameras();render_reviews()
