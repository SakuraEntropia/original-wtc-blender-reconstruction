"""Restore existing floor plates and segmented core; retain the open mezzanine."""
import re
import bpy

VERSION='2026-10-15-restore-floor-core-v1'


def apply():
    scene=bpy.context.scene
    if scene.get('interior_visibility_revision')==VERSION:return
    parents={child:col for col in bpy.data.collections for child in col.children}
    enabled=set();objects=set()
    def enable(col):
        while col:
            col.hide_render=False;col.hide_viewport=False;enabled.add(col.name)
            col=parents.get(col)
    for tower in ('WTC1','WTC2'):
        root=bpy.data.collections[tower+'_COMPLETION_study']
        floors=next(c for c in root.children if c.name.startswith('all_110_floor_slabs'))
        core=next(c for c in root.children if c.name.startswith('47_core_columns'))
        head=bpy.data.collections[tower+'_CORE_roof_connections_STUDY']
        for col in (floors,core,head,*head.children_recursive):enable(col)
        for ob in floors.objects:
            # F002's obsolete full slab would fill both source-traced wells.
            if ob.name!=tower+'_F002_SLAB_STUDY':objects.add(ob)
        objects.update(o for o in core.objects if o.get('module')=='core_steel_column')
        objects.update(head.all_objects)
    def layer(col):
        if col.name in enabled:col.exclude=False;col.hide_viewport=False
        for child in col.children:layer(child)
    for view in scene.view_layers:layer(view.layer_collection)
    bpy.context.view_layer.update()
    for ob in objects:
        ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
    scene['interior_visibility_revision']=VERSION
    scene['restored_floor_core_objects']=len(objects)


def inspect(check):
    for tower in ('WTC1','WTC2'):
        slabs=[o for o in bpy.data.objects if re.fullmatch(tower+r'_F\d{3}_SLAB_STUDY',o.name)]
        active=[o for o in slabs if o.name!=tower+'_F002_SLAB_STUDY']
        check(tower+'_floor_stack_restored_open_plaza_preserved',len(slabs)==110 and len(active)==109 and all(o.visible_get() and not o.hide_render for o in active),
              {'visible_existing_slabs':len(active),'plaza_floor':'existing source-traced curved mezzanine replaces F002'})
        core=[o for o in bpy.data.objects if o.name.startswith(tower+'_') and o.get('module')=='core_steel_column']
        head=bpy.data.collections[tower+'_CORE_roof_connections_STUDY']
        check(tower+'_core_columns_shafts_roof_nodes_restored',len({o.get('axis_index') for o in core})==47 and all(o.visible_get() and not o.hide_render for o in core) and all(o.visible_get() and not o.hide_render for o in head.all_objects),
              {'core_axes':47,'segments':len(core),'roof_and_shaft_parts':len(head.all_objects)})
