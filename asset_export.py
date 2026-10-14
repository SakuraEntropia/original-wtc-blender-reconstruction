"""Write the current asset set and retire superseded standalone variants."""
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parent


def export_assets():
    retired=['WTC1_CORNER_aluminum_photo_interpretation',
             'WTC2_CORNER_aluminum_photo_interpretation','WTC7_ROOF_detail_components',
             'WTC1_CROWN_photo_interpretation','WTC2_CROWN_photo_interpretation']
    for name in retired:
        col=bpy.data.collections.get(name)
        if col and '_CROWN_photo' in name and bpy.data.collections.get(name[:4]+'_CROWN_CAP_mitered_panels'):
            col['superseded_by']='current curved cladding and mitered cap assets'
        if col and col.get('superseded_by'):
            if col.asset_data:col.asset_clear()
            path=ROOT/'assets'/(name+'.blend')
            if path.exists():path.unlink()
    for tower,xy in (('WTC1',(-55,55)),('WTC2',(55,-55))):
        for suffix in ('_corner_three_panels','_crown_curved_cladding'):
            col=bpy.data.collections.get(tower+suffix)
            if col:
                col.asset_mark();col.instance_offset=(*xy,0)
                col.asset_data.description=col.get('confidence','Source-labelled CG study')
    (ROOT/'assets').mkdir(exist_ok=True)
    for col in bpy.data.collections:
        if not col.asset_data:continue
        safe=''.join(c if c.isalnum() or c in '_-' else '_' for c in col.name)
        bpy.data.libraries.write(str(ROOT/'assets'/(safe+'.blend')),{col},fake_user=True,compress=True)
    print('CURRENT_ASSET_EXPORT_DONE',flush=True)


if __name__=='__main__':
    export_assets()
    bpy.context.scene.render.filepath='//renders/preview.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'wtc_detailed_cg.blend'),compress=True)
