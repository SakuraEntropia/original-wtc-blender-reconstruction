"""Small dependency-free convex clipping helpers, all polygons counterclockwise."""
import math

EPS = 1e-8


def area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2


def clip(poly, a, b, inside=True):
    if not poly:
        return []
    def side(p):
        return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        dp,dq=side(p),side(q)
        ip=dp>=0 if inside else dp<=0
        iq=dq>=0 if inside else dq<=0
        if ip:out.append(p)
        if ip!=iq:
            t=dp/(dp-dq)
            out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    clean=[]
    for p in out:
        if not clean or math.dist(p,clean[-1])>EPS:clean.append(p)
    if len(clean)>1 and math.dist(clean[0],clean[-1])<EPS:clean.pop()
    return clean if len(clean)>2 and area(clean)>EPS else []


def subtract_convex(poly, cutter):
    """Partition poly minus convex cutter into nonoverlapping convex polygons."""
    result=[]
    remaining=poly
    for a,b in zip(cutter,cutter[1:]+cutter[:1]):
        outside=clip(remaining,a,b,False)
        if outside:result.append(outside)
        remaining=clip(remaining,a,b,True)
        if not remaining:break
    return result


def regular_polygon(x,y,r,n):
    return [(x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n)) for i in range(n)]


def extrude_union(parts,z0,z1):
    """Extrude a partition; node T-junctions and omit internal side walls.

    The top/bottom partitions share vertices. Hole boundaries remain real holes,
    so circular planter cuts do not contain buried coplanar internal walls.
    """
    points=list(dict.fromkeys((round(x,7),round(y,7)) for p in parts for x,y in p))
    index={p:i for i,p in enumerate(points)}
    caps=[];edges={}
    for poly in parts:
        cap=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            a=(round(a[0],7),round(a[1],7));b=(round(b[0],7),round(b[1],7))
            dx,dy=b[0]-a[0],b[1]-a[1];length2=dx*dx+dy*dy
            if length2<EPS*EPS:continue
            nodes=[]
            for p in points:
                t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length2
                distance=abs(dx*(p[1]-a[1])-dy*(p[0]-a[0]))/math.sqrt(length2)
                if -EPS<=t<1-EPS and distance<2e-7:nodes.append((t,index[p]))
            cap.extend(i for t,i in sorted(nodes))
        cap=list(dict.fromkeys(cap))
        if len(cap)<3:continue
        caps.append(cap)
        for a,b in zip(cap,cap[1:]+cap[:1]):
            key=tuple(sorted((a,b)))
            edges.setdefault(key,[]).append((a,b))
    n=len(points)
    verts=[(x,y,z) for z in (z0,z1) for x,y in points]
    faces=[]
    for cap in caps:faces.extend((tuple(reversed(cap)),tuple(i+n for i in cap)))
    for uses in edges.values():
        if len(uses)==1:
            a,b=uses[0];faces.append((a,b,b+n,a+n))
        elif len(uses)!=2:raise ValueError('Overlapping paving partition')
    return verts,faces
