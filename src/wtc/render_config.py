"""Reproducible perspective cameras and Cycles Metal GPU review settings."""
import bpy
from mathutils import Vector


def perspective(ob,target,span=None,lens=None):
    distance=(Vector(target)-ob.location).length
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    ob.data.type='PERSP';ob.data.sensor_fit='HORIZONTAL';ob.data.sensor_width=36
    ob.data.lens=lens if lens is not None else 36*distance/span
    ob.data.clip_start=.1;ob.data.clip_end=max(100,distance+4*(span or 50))
    ob['review_target_m']=list(target)
    if span:ob['target_plane_span_m']=span


def configure():
    scene=bpy.context.scene
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.refresh_devices()
    selected=[]
    for device in prefs.devices:
        device.use=device.type=='METAL'
        if device.use:selected.append(device.name)
    if not selected:raise RuntimeError('Metal GPU unavailable; do not silently substitute CPU')
    scene.render.engine='CYCLES';scene.cycles.device='GPU'
    scene.cycles.samples=32;scene.cycles.use_denoising=True
    scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.06;scene.cycles.adaptive_min_samples=8
    scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3
    scene.cycles.glossy_bounces=3;scene.cycles.transmission_bounces=4
    scene.cycles.transparent_max_bounces=6
    scene.render.use_persistent_data=True
    scene['render_device_names']=selected
    scene['render_configuration']='Cycles / GPU / Metal only / 32 adaptive samples / denoised'
    return selected
