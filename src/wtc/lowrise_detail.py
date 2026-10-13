"""Panelized context assets. Measured WTC7 facade facts; tagged lowrise studies.

Sources: NIST NCSTAR 1-9 Ch.5, pp.98-114, Figs.5-10..5-25.
WTC3-6 footprint locations and finish schedules remain explicitly unverified.
No downloaded assets, images, trademarks or mural reproductions are included.
"""
import math
import bpy

FT = .3048
SOURCE = 'NIST NCSTAR 1-9 Ch5 pp98-114, Figs5-10..5-25'
SOURCE_URL = 'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=861611'
_meshes = {}


def material(name, color, metal=0, rough=.4):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = rough
    mat.diffuse_color = (*color, 1)
    return mat


def cube(name, size, position, angle, col, mat):
    """Actual dimensions in shared mesh, not scaled transforms."""
    key = (tuple(round(v, 6) for v in size), mat.name)
    mesh = _meshes.get(key)
    if mesh is None or mesh.name not in bpy.data.meshes:
        a, b, c = (v/2 for v in size)
        mesh = bpy.data.meshes.new('context_part_' + str(len(_meshes)))
        mesh.from_pydata([(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),
                         (-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)], [],
                        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
        mesh.materials.append(mat)
        mesh.update()
        _meshes[key] = mesh
    ob = bpy.data.objects.new(name, mesh)
    col.objects.link(ob)
    ob.location = position
    ob.rotation_euler.z = angle
    return ob


def subgroup(parent, name, source, confidence):
    col = bpy.data.collections.new(name)
    parent.children.link(col)
    col['source'] = source
    col['confidence'] = confidence
    return col


def face_piece(name, p1, p2, along, z, size, offset, col, mat):
    vx, vy = p2[0]-p1[0], p2[1]-p1[1]
    length = math.hypot(vx, vy)
    tx, ty = vx/length, vy/length
    nx, ny = -ty, tx  # clockwise polygon: left normal points outward
    return cube(name, size,
                (p1[0]+tx*along+nx*offset, p1[1]+ty*along+ny*offset, z),
                math.atan2(ty, tx), col, mat)


def window(name, p1, p2, along, z, width, height, col, glass, frame,
           offset=.177, frame_width=.0762, glass_depth=.0254):
    """Glass plus a reusable frame mesh containing four physical strips."""
    f = frame_width
    face_piece(name+'_GLASS', p1, p2, along, z,
               (width-2*f, glass_depth, height-2*f), offset, col, glass)
    key = ('window_frame', round(width,6), round(height,6), round(f,6),frame.name)
    mesh = _meshes.get(key)
    if mesh is None:
        verts=[]; faces=[]
        strips=[]
        for side in (-1,1):
            strips.extend([((side*(width-f)/2,0,0),(f,.065,height)),
                           ((0,0,side*(height-f)/2),(width-2*f,.065,f))])
        for (px,py,pz),(sx,sy,sz) in strips:
            a,b,c=sx/2,sy/2,sz/2; n=len(verts)
            verts.extend([(px+i*a,py+j*b,pz+k*c) for i,j,k in
                          ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                           (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))])
            faces.extend([tuple(n+i for i in indices) for indices in
                          ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))])
        mesh=bpy.data.meshes.new('context_window_frame_'+str(len(_meshes)))
        mesh.from_pydata(verts,[],faces);mesh.materials.append(frame);mesh.update()
        _meshes[key]=mesh
    vx,vy=p2[0]-p1[0],p2[1]-p1[1]; length=math.hypot(vx,vy)
    tx,ty=vx/length,vy/length; nx,ny=-ty,tx
    ob=bpy.data.objects.new(name+'_FRAME',mesh);col.objects.link(ob)
    ob.location=(p1[0]+tx*along+nx*(offset+.012),p1[1]+ty*along+ny*(offset+.012),z)
    ob.rotation_euler.z=math.atan2(ty,tx)


def visible_intervals(p1,p2,volume,others):
    """Subtract intersections with adjacent staged rectangular volumes."""
    vx,vy=p2[0]-p1[0],p2[1]-p1[1]; length=math.hypot(vx,vy)
    tx,ty=vx/length,vy/length
    intervals=[(0,length)]
    for other in others:
        if other==volume:
            continue
        ox,oy,_=other.location; sx,sy,_=other.dimensions
        x0,x1=ox-sx/2-.001,ox+sx/2+.001
        y0,y1=oy-sy/2-.001,oy+sy/2+.001
        if abs(tx)>.9:
            if not y0<=p1[1]<=y1:
                continue
            cut=sorted(((x0-p1[0])/tx,(x1-p1[0])/tx))
        else:
            if not x0<=p1[0]<=x1:
                continue
            cut=sorted(((y0-p1[1])/ty,(y1-p1[1])/ty))
        a,b=max(0,cut[0]),min(length,cut[1])
        next_intervals=[]
        for lo,hi in intervals:
            if b<=lo or a>=hi:
                next_intervals.append((lo,hi))
            else:
                if lo<a: next_intervals.append((lo,a))
                if b<hi: next_intervals.append((b,hi))
        intervals=next_intervals
    return intervals


def louver(name, p1, p2, start, width, z, height, col, dark):
    face_piece(name+'_back', p1, p2, start+width/2, z,
               (width,.065,height), .19, col, dark)
    count = max(2, round(height/.18))
    for i in range(count):
        ob = face_piece(name+f'_slat_{i}', p1, p2, start+width/2,
                        z-height/2+(i+.5)*height/count,
                        (width,.14,.046), .24, col, dark)
        ob.rotation_euler.x = math.radians(24)


def wtc7_detail():
    parent = bpy.data.collections.get('WTC7__NIST_massing_position_schematic')
    shell = bpy.data.objects.get('WTC7_47_story_envelope')
    if parent is None or shell is None:
        return
    # Remove the former band proxies from render and viewport.
    for ob in list(parent.objects):
        if 'glazing_bands_STUDY' in ob.name:
            bpy.data.objects.remove(ob, do_unlink=True)
    xy = [(v.co.x, v.co.y) for v in shell.data.vertices[:4]]
    roof = max(v.co.z for v in shell.data.vertices)
    red = material('WTC7_red_polished_granite', (.32,.145,.104), .08,.27)
    tan = material('WTC7_tan_polished_granite', (.52,.46,.36), .04,.30)
    black = material('WTC7_dark_granite', (.105,.11,.105), .04,.28)
    glass = material('WTC7_25mm_dark_insulated_glass', (.04,.075,.08), .52,.17)
    frame = material('WTC7_76mm_aluminum_window_frames', (.24,.26,.25), .8,.3)
    backing = material('WTC7_127mm_galvanized_cassette', (.21,.235,.23), .55,.45)
    shell.data.materials.clear()
    for mat in (red, tan, black):
        shell.data.materials.append(mat)
    for poly in shell.data.polygons:
        poly.material_index = 2 if poly.index < 2 else (0 if poly.index in (2,4) else 1)
    panels = subgroup(parent, 'WTC7_panelized_facades', SOURCE,
        'Window counts, nominal dimensions, frame/plate thickness sourced. Individual widths vary in original. '
        'Absolute floor datums inferred by anchoring typical pitches to 610ft roof; placement still staged.')
    panels['source_url'] = SOURCE_URL
    panels['dimensions'] = 'NS nominal window width 4ft7in, height6ft6in; EW glass6ft square, framed6ft6in; 3in aluminum frames; 1in glazing; 1.25in granite; 5in galvanized cassette'
    panels['count_basis'] = 'N 63 central+2 each end; S45 central+2 each end; E12 central+2 each end; W12 central+2 north+4 south'
    # Roof anchor preserves sourced 610ft height. Absolute Floor7 datum is inferred.
    pitch = 12.75*FT
    mech_pitch = 14*FT
    f46 = roof-2*mech_pitch
    f24 = f46-22*pitch
    f22 = f24-2*mech_pitch
    f7 = f22-15*pitch
    # The old full-height prism would occlude the recessed south crown glazing.
    # Replace it with a closed shell whose middle roof edge is set inward.
    sx,sy=xy[3][0]-xy[2][0],xy[3][1]-xy[2][1]
    sl=math.hypot(sx,sy);tx,ty=sx/sl,sy/sl;nx,ny=-ty,tx
    center_len=45*(4*FT+7*FT/12);start=(sl-center_len)/2
    central_points=[(xy[2][0]+tx*t,xy[2][1]+ty*t) for t in (start,start+center_len)]
    ring=[xy[0],xy[1],xy[2],*central_points,xy[3]]
    top_ring=[(px-nx*1.6,py-ny*1.6) if i in (3,4) else (px,py)
              for i,(px,py) in enumerate(ring)]
    verts=[(px,py,0) for px,py in xy]+[(px,py,f46) for px,py in ring]+[(px,py,roof) for px,py in top_ring]
    faces=[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,9,8,7,6),(3,0,4,9),tuple(range(10,16))]
    faces += [(4+i,4+(i+1)%6,10+(i+1)%6,10+i) for i in range(6)]
    shell_mesh=bpy.data.meshes.new('WTC7_south_recessed_crown_closed_shell_mesh')
    shell_mesh.from_pydata(verts,[],faces);shell_mesh.update()
    for mat in (red,tan,black): shell_mesh.materials.append(mat)
    for poly in shell_mesh.polygons:
        poly.material_index=(2 if poly.index in (0,5) else
                             1 if poly.index in (2,4,7,8,10,11) else 0)
    shell.data=shell_mesh
    shell['crown_confidence']='NIST 1-9 Figs5-8/14 south recessed slope documented; setback1.6m inferred'
    floor_z = {}
    for n in range(7,48):
        floor_z[n] = (f7+(n-7)*pitch if n<22 else
                      f22+(n-22)*mech_pitch if n<24 else
                      f24+(n-24)*pitch if n<46 else f46+(n-46)*mech_pitch)
    panels['floor7_inferred_z_m'] = f7
    for face in range(4):
        p1, p2 = xy[face], xy[(face+1)%4]
        length = math.dist(p1,p2)
        ns = face in (0,2)
        nominal = 4*FT+7*FT/12 if ns else 6.5*FT
        central_count = 63 if face==0 else 45 if face==2 else 12
        central_len = central_count*nominal if ns else central_count*2.82
        start = (length-central_len)/2
        positions = [(start+(j+.5)*(nominal if ns else 2.82), nominal)
                     for j in range(central_count)]
        if ns:
            # Tan end surrounds and the separating tan strips remain individual parts.
            edge_pitch = nominal
            for k in range(2):
                positions.extend([(1.1+(k+.5)*edge_pitch, nominal),
                                  (length-1.1-(k+.5)*edge_pitch, nominal)])
        else:
            pair_width = 8.5*FT
            for side in (0,1):
                center = 1.0+pair_width/2 if side==0 else length-1.0-pair_width/2
                for k in (-1,1):
                    positions.append((center+k*pair_width/4,pair_width/2))
            if face==3:
                # West south end has a second pair, unlike the east facade.
                pair_width = 11*FT
                center = 1.0+8.5*FT+1.0+pair_width/2
                for k in (-1,1):
                    positions.append((center+k*pair_width/4,pair_width/2))
        for floor in range(7,48):
            z = floor_z[floor]
            height = (8*FT+8*FT/12 if ns else 9.5*FT) if floor in (22,23) else 6.5*FT
            # South upper two stories use the separate sloping glazing below.
            for j,(along,width) in enumerate(positions):
                if ns and floor in (22,23) and j<central_count:
                    continue  # two tall window rows around the central glass band
                if face==2 and floor>=46 and j<central_count:
                    continue
                if face==0 and floor>=46 and 17<=j<45:
                    continue
                win_z = z+.762+height/2
                window(f'WTC7_FACE{face}_F{floor:02d}_WIN{j:02d}',p1,p2,along,
                       win_z,width,height,panels,glass,frame)
                # A physical granite plate with its own galvanized support box.
                plate_z = z+.762-1.873/2
                plate_mat = red if ns and j<central_count else tan
                face_piece(f'WTC7_FACE{face}_F{floor:02d}_GRANITE{j:02d}',
                           p1,p2,along,plate_z,(width-.015875,.03175,1.873),
                           .174,panels,plate_mat)
                face_piece(f'WTC7_FACE{face}_F{floor:02d}_CASSETTE{j:02d}',
                           p1,p2,along,plate_z,(width-.015875,.127,1.873),
                           .094,panels,backing)
        if ns:
            for j in range(central_count):
                base=f22+.60
                for row,height in enumerate((8*FT+8*FT/12,6.25*FT,8*FT+8*FT/12)):
                    window(f'WTC7_FACE{face}_F22_23_GLAZING_{j}_{row}',p1,p2,
                           start+(j+.5)*nominal,base+height/2,nominal,height,
                           panels,glass,frame)
                    base+=height
        if face==0:
            louver('WTC7_NORTH_F46_47_COOLING_INTAKE',p1,p2,
                   start+17*nominal,28*nominal,f46+mech_pitch,2*mech_pitch-.7,
                   panels,black)
    lower = subgroup(parent,'WTC7_lower_lobby_and_plant_STUDY',SOURCE,
        'South four-story atrium, lower service louvers, north3/4 glazing documented. Exact lower partition/entrance spacing estimated; mural excluded.')
    f5 = f7-13*FT-14*FT
    # Four lower south atrium levels: individual clear-looking panes and entrances.
    south1,south2 = xy[2],xy[3]
    sl = math.dist(south1,south2)
    for k in range(24):
        w = (sl-8)/24
        for section in range(3):
            h = (f5-.4)/3
            window(f'WTC7_ATRIUM_{k}_{section}_STUDY',south1,south2,
                   4+(k+.5)*w,.2+(section+.5)*h,w,h,lower,glass,frame)
    for k in range(5):
        along = sl*.50+(k-2)*2.9
        window(f'WTC7_SOUTH_ENTRY_{k}_STUDY',south1,south2,along,1.35,2.4,2.7,
               lower,glass,frame,offset=.255)
        face_piece(f'WTC7_SOUTH_ENTRY_HANDLE_{k}_STUDY',south1,south2,
                   along+.25,1.1,(.04,.16,.65),.40,lower,frame)
    for face in range(4):
        p1,p2 = xy[face],xy[(face+1)%4]
        length = math.dist(p1,p2)
        if face!=0:
            louver(f'WTC7_FACE{face}_F5_6_SERVICE_LOUVERS_STUDY',p1,p2,
                   4,length-8,(f5+f7)/2,f7-f5-.4,lower,black)
        else:
            for k in range(40):
                width = (length-8)/40
                for z,h in ((f5-5.6388+1.8288/2,1.8288),
                            (f5-3.81+1.9812/2,1.9812),
                            (f5-1.8288/2,1.8288)):
                    window(f'WTC7_N_F3_4_{k}_{z:.2f}_STUDY',p1,p2,4+(k+.5)*width,
                           z,width,h,lower,glass,frame)
            louver('WTC7_N_F5_SERVICE_LOUVERS_STUDY',p1,p2,4,length-8,
                   f5+2,3.7,lower,black)
    crown = subgroup(parent,'WTC7_south_sloping_crown_STUDY',SOURCE,
        'NIST Fig5-8/14: recessed south center and sloped curtain wall in 4 vertical glass sections. Setback 1.6m estimated.')
    p1,p2 = xy[2],xy[3]
    vx,vy=p2[0]-p1[0],p2[1]-p1[1]
    length=math.hypot(vx,vy); tx,ty=vx/length,vy/length; nx,ny=-ty,tx
    central=45*(4*FT+7*FT/12); start=(length-central)/2
    setback=1.6; base=f46; top=roof
    for j in range(45):
        for h in range(4):
            along0=start+j*central/45+.04; along1=start+(j+1)*central/45-.04
            u0=h/4+.006; u1=(h+1)/4-.006
            verts=[(p1[0]+tx*t+nx*(.21-setback*u),p1[1]+ty*t+ny*(.21-setback*u),base+(top-base)*u)
                   for t,u in ((along0,u0),(along1,u0),(along1,u1),(along0,u1))]
            m=bpy.data.meshes.new(f'WTC7_sloped_crown_{j}_{h}_mesh')
            m.from_pydata(verts,[],[(0,1,2,3)]);m.materials.append(glass)
            ob=bpy.data.objects.new(f'WTC7_sloped_crown_glass_{j}_{h}_STUDY',m);crown.objects.link(ob)
            solid=ob.modifiers.new('1inch_glazing','SOLIDIFY');solid.thickness=.0254
    return parent


def lowrise_detail():
    """Existing footprints are preserved; every supplementary profile is tagged."""
    metal=material('plaza_building_dark_anodized_frame_STUDY',(.09,.115,.115),.75,.32)
    glass=material('plaza_building_smoky_glass_STUDY',(.035,.075,.076),.55,.18)
    wall=material('plaza_building_dark_spandrel_STUDY',(.20,.225,.215),.12,.50)
    hotel=material('WTC3_warm_concrete_panel_STUDY',(.50,.47,.41),.02,.62)
    for name,stories in (('WTC3_Marriott',22),('WTC4',9),('WTC5',9),('WTC6',8)):
        parent=bpy.data.collections.get(name+'_massing_STUDY')
        if parent is None:
            continue
        volumes=[o for o in parent.objects if '_volume_' in o.name]
        for ob in list(parent.objects):
            if 'facade_band_' in ob.name or 'facade_north_band_' in ob.name or 'facade_side_band_' in ob.name:
                bpy.data.objects.remove(ob,do_unlink=True)
        col=subgroup(parent,name+'_panelized_envelope_STUDY',
            'NIST NCSTAR1-1 sec2.1: story counts; FEMA403 ch4 sec4.1: lowrise steel-frame office/retail buildings',
            'Dimensions from existing staged volume. Every bay pitch, frame, glass size, entrance, roof and material is a CG study; no as-built claim.')
        for idx,volume in enumerate(volumes):
            x,y,z=volume.location
            sx,sy,sz=volume.dimensions
            base=z-sz/2; roof=z+sz/2
            xy=[(x-sx/2,y+sy/2),(x+sx/2,y+sy/2),(x+sx/2,y-sy/2),(x-sx/2,y-sy/2)]
            finish=hotel if name=='WTC3_Marriott' else wall
            volume.data.materials.clear();volume.data.materials.append(finish)
            for face in range(4):
                p1,p2=xy[face],xy[(face+1)%4]
                length=math.dist(p1,p2)
                visible=visible_intervals(p1,p2,volume,volumes)
                if not visible:
                    continue
                count=max(4,round(length/(2.35 if name=='WTC3_Marriott' else 1.7)))
                bay=length/count; fh=sz/stories
                for floor in range(stories):
                    wz=base+(floor+.55)*fh
                    wh=fh*(.66 if floor==0 else .52)
                    for k in range(count):
                        if not any(lo<=(k+.5)*bay<=hi for lo,hi in visible):
                            continue
                        window(f'{name}_V{idx}_FACE{face}_F{floor+1}_BAY{k}_STUDY',
                               p1,p2,(k+.5)*bay,wz,bay*.94,wh,col,glass,metal,
                               offset=.085,frame_width=.05,glass_depth=.012)
                    for part,(lo,hi) in enumerate(visible):
                        face_piece(f'{name}_V{idx}_FACE{face}_F{floor+1}_SPANDREL{part}_STUDY',
                                   p1,p2,(lo+hi)/2,base+(floor+.10)*fh,
                                   (hi-lo,.08,fh*.26),.045,col,finish)
                # Coping, ground plinth and two-part entrances are physically distinct.
                for part,(lo,hi) in enumerate(visible):
                    face_piece(f'{name}_V{idx}_FACE{face}_COPING{part}_STUDY',p1,p2,(lo+hi)/2,
                               roof+.73,(hi-lo+.12,.36,.12),.08,col,metal)
                    face_piece(f'{name}_V{idx}_FACE{face}_PLINTH{part}_STUDY',p1,p2,(lo+hi)/2,
                               base+.22,(hi-lo,.16,.44),.10,col,finish)
                if face in (0,2) and any(lo<length/2-3 and hi>length/2+3 for lo,hi in visible):
                    for k in (-1,1):
                        window(f'{name}_V{idx}_FACE{face}_ENTRY{k}_STUDY',p1,p2,
                               length/2+k*.7,base+1.3,1.35,2.6,col,glass,metal,offset=.25)
                    face_piece(f'{name}_V{idx}_FACE{face}_CANOPY_STUDY',p1,p2,
                               length/2,base+3.05,(6,2.0,.15),.9,col,metal)
            # Segmented service bulkhead, louver faces and pipe risers, no external asset.
            for k in (-1,1):
                bx=x+k*sx*.17; by=y
                cube(f'{name}_V{idx}_ROOF_BULKHEAD{k}_STUDY',(4.2,5.1,2.8),
                     (bx,by,roof+1.4),0,col,finish)
                a,b=(bx-2.1,by-2.55),(bx+2.1,by-2.55)
                louver(f'{name}_V{idx}_ROOF_VENT{k}_STUDY',b,a,.3,3.6,
                       roof+1.4,1.9,col,metal)
                cube(f'{name}_V{idx}_ROOF_SERVICE_WALK{k}_STUDY',(1.4,sy*.55,.09),
                     (bx,by,roof+.085),0,col,metal)
                for j in range(3):
                    cube(f'{name}_V{idx}_ROOF_PIPE{k}_{j}_STUDY',(.10,.10,1.0),
                         (bx-.7+j*.7,by+2.0,roof+3.1),0,col,metal)
    return None


def enrich_context():
    """Call after completion.lowrise_context and context.wtc7_massing."""
    _meshes.clear()
    lowrise_detail()
    wtc7_detail()

