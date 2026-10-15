"""Allocate the existing six-foot height difference to North43/67, once."""
import bpy
from bisect import bisect_right
from . import facade_revision as f

VERSION='2026-10-15-port-authority43-67-v1'


def annotate(root):
    for ob in root.all_objects:
        if ob.get('floor') in (43,67):
            ob['special_height_source']='User14ft/16ft; archive note confirms43/67 distinction'
            ob['special_window_inference']='Window enlarged by added story height, retaining normal spandrel; not independently dimensioned'


def apply():
    scene=bpy.context.scene
    root=bpy.data.collections['WTC1_FACADE_REVISION']
    if scene.get('floor_schedule_revision')==VERSION:
        annotate(root);return
    if not root.get('port_authority_heights_applied'):
        old=f._story_schedule(1368*f.FT,False);new=f._story_schedule(1368*f.FT)
        xs=[r['z'] for r in old]+[1368*f.FT-f.CROWN_DEPTH]
        ys=[r['z'] for r in new]+[1368*f.FT-f.CROWN_DEPTH]
        def warp(z):
            if z<=xs[0] or z>=xs[-1]:return z
            i=bisect_right(xs,z)-1;t=(z-xs[i])/(xs[i+1]-xs[i])
            return ys[i]*(1-t)+ys[i+1]*t
        for suffix in ('_corner_three_panels','_FACADE_corner_transition_frames'):
            for ob in bpy.data.collections['WTC1'+suffix].objects:
                matrix=ob.matrix_world.copy();inverse=matrix.inverted()
                if not any(abs(warp((matrix@v.co).z)-(matrix@v.co).z)>1e-5 for v in ob.data.vertices):continue
                ob.data=ob.data.copy()
                for v in ob.data.vertices:
                    p=matrix@v.co;p.z=warp(p.z);v.co=inverse@p
                ob['height_registration']='43/67 corrected floor proxy; corner section dimensions retained'
        for suffix in ('_window_frames','_story_column_covers','_recessed_window_rows','_spandrel_covers','_sky_lobby_facade','_mechanical_facade'):
            col=bpy.data.collections.get('WTC1'+suffix)
            if col:bpy.data.batch_remove(ids=list(col.objects)+[col])
        f._regular_facade('WTC1',(-55,55),1368*f.FT,root,bpy.data.materials['silver_cladding_color_study'],bpy.data.materials['FACADE_REV_bronze_glazing'])
    annotate(root)
    for tower,roof in (('WTC1',1368*f.FT),('WTC2',1362*f.FT)):
        rows=f._story_schedule(roof)
        for row in rows:
            ob=bpy.data.objects[tower+f"_F{row['level']:03d}_SLAB_STUDY"]
            ob.location.z=row['z'];ob['story_height_m']=row['pitch'];ob['floor_schedule_revision']=VERSION
            ob['elevation_confidence']='Facade floor proxy;43/67 differential from user; absolute registration remains estimated'
        scene[tower+'_story_schedule_m']=[r['z'] for r in rows]
    scene['floor_schedule_revision']=VERSION
