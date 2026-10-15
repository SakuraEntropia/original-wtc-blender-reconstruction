"""AB302 relative107/108/109/110 datums replace the17m crown envelope.

FIN107→108=17ft6in,108→109=14ft,109→110=14ft. NIST p37
places FIN107 seventeen inches below the107 spandrel head. Absolute FIN110
registration remains the separately documented AB321/323 study assumption.
"""
import bpy
from . import facade_revision as facade

VERSION='2026-10-15-ab302-full-crown-height-v1'
FT=.3048
DEPTH=(15+17.5+14+14+7+1/12-17/12)*FT


def apply():
    scene=bpy.context.scene
    if scene.get('crown_full_height_revision')==VERSION:return
    facade.CROWN_DEPTH=DEPTH
    for tower,xy,roof in (('WTC1',(-55,55),1368*FT),('WTC2',(55,-55),1362*FT)):
        root=bpy.data.collections[tower+'_FACADE_REVISION']
        col=bpy.data.collections[tower+'_crown_curved_cladding']
        finish110=roof-15*FT;finish107=finish110-(17.5+14+14)*FT
        z0=roof-DEPTH;a=finish107+(17/12+11+7/12)*FT
        delta=a-col['z_transition_lower_estimated_m']
        if abs(delta)>.001:
            # Rebalance the already-estimated intermediate MER datums while
            # keeping every sourced ordinary window/story size unchanged.
            suffixes=('_window_frames','_story_column_covers','_recessed_window_rows',
                      '_spandrel_covers','_sky_lobby_facade','_mechanical_facade')
            for suffix in suffixes:
                old=bpy.data.collections.get(tower+suffix)
                if old:bpy.data.batch_remove(ids=list(old.objects)+[old])
            metal=bpy.data.materials['silver_cladding_color_study']
            glass=bpy.data.materials['FACADE_REV_bronze_glazing']
            facade._regular_facade(tower,xy,roof,root,metal,glass)
            for ob in col.objects:
                if ob.get('module') in ('crown_107_cover','crown_107_glazing','raised_window_frame'):
                    ob.location.z+=delta
        col['z_base107_estimated_m']=z0
        col['z_window107_bottom_estimated_m']=finish107+17/12*FT
        col['z_transition_lower_estimated_m']=a
        col['z_transition_middle_estimated_m']=a+col['lower_transition_height_m']
        col['source_FIN107_z_m']=finish107;col['source_FIN108_z_m']=finish110-28*FT
        col['source_FIN109_z_m']=finish110-14*FT;col['source_FIN110_z_m']=finish110
        col['source_relative_floor_rises_m']=[17.5*FT,14*FT,14*FT]
        col['crown_full_height_revision']=VERSION
        col['full_height_source']='Original A-AB-302 printed floor chain; NIST1-5A p37 spandrel/window dimensions'
        for level,z in ((107,finish107),(108,finish110-28*FT),(109,finish110-14*FT),(110,finish110)):
            for name in (tower+f'_F{level:03d}_SLAB_STUDY',tower+f'_F{level}_'+('PUBLIC_TOP' if level==107 else 'MEP')+'_STUDY'):
                ob=bpy.data.objects.get(name)
                if ob:ob.location.z=z;ob['elevation_confidence']='AB302 relative floor chain; absolute roof registration study'
    scene['crown_full_height_revision']=VERSION
