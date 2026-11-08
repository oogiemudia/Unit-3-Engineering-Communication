"""Build every model: STEP, STL, GLB (for the web viewer and the renders), B-rep edges and the catalogue.

Run from the repository root:  python3 tools/build_models.py
"""
import json, os, sys, math
import numpy as np
import trimesh
import cadquery as cq
from OCP.TopExp import TopExp
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.BRep import BRep_Tool
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.BRepAdaptor import BRepAdaptor_Curve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import parts  # noqa: E402

DOCS = os.path.join(ROOT, 'docs')
for d in ('step', 'stl', 'glb', 'edges'):
    os.makedirs(os.path.join(DOCS, d), exist_ok=True)


def to_gl(p):
    """CAD (Z up, Y back) to glTF (Y up, Z towards the viewer)."""
    return (p[0], p[2], -p[1])


def hex_rgba(h, a=255):
    return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a]


def mesh_of(shape, colour, tol=0.03, ang=0.15):
    """Tessellate face by face so flat faces stay flat and curved faces get smooth normals."""
    verts, faces, norms = [], [], []
    for f in shape.Faces():
        vs, tris = f.tessellate(tol, ang)
        if not tris:
            continue
        base = len(verts)
        planar = f.geomType() == 'PLANE'
        if planar:
            n = f.normalAt()
        for v in vs:
            nn = n if planar else f.normalAt(v)
            verts.append(to_gl((v.x, v.y, v.z)))
            norms.append(to_gl((nn.x, nn.y, nn.z)))
        for t in tris:
            faces.append((base + t[0], base + t[1], base + t[2]))
    m = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), vertex_normals=np.array(norms), process=False)
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.tile(hex_rgba(colour), (len(verts), 1)))
    return m


def edges_of(shape, defl=0.03):
    """Real model edges as polylines (no cylinder seams), in glTF coordinates."""
    emap = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape.wrapped, TopAbs_EDGE, TopAbs_FACE, emap)
    out = []
    for i in range(1, emap.Extent() + 1):
        e = emap.FindKey(i)
        flist = emap.FindFromIndex(i)
        faces = list(flist)
        seam = False
        for fc in faces:
            if BRep_Tool.IsClosed_s(cq.Edge(e).wrapped, cq.Face(fc).wrapped):
                seam = True
        if seam:
            continue
        try:
            c = BRepAdaptor_Curve(cq.Edge(e).wrapped)
            pts = GCPnts_QuasiUniformDeflection(c, defl, c.FirstParameter(), c.LastParameter())
            if not pts.IsDone() or pts.NbPoints() < 2:
                continue
            pl = []
            for k in range(1, pts.NbPoints() + 1):
                p = pts.Value(k)
                pl.extend(round(x, 3) for x in to_gl((p.X(), p.Y(), p.Z())))
            out.append(pl)
        except Exception:
            continue
    return out


def explode_offsets(items, axis):
    """Spread the parts out along the explode axis in the order they sit along it."""
    if not axis:
        return [[0, 0, 0] for _ in items]
    ax = np.array(to_gl(axis), dtype=float)
    cents = []
    for name, wp, col in items:
        bb = wp.val().BoundingBox()
        c = np.array(to_gl(((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)))
        cents.append(float(c @ ax))
    allbb = cq.Compound.makeCompound([w.val() for n, w, c in items]).BoundingBox()
    size = max(allbb.xlen, allbb.ylen, allbb.zlen)
    order = np.argsort(cents)
    rank = np.empty(len(items))
    rank[order] = np.arange(len(items))
    mid = (len(items) - 1) / 2
    return [list(np.round(ax * (r - mid) * size * 0.28, 2)) for r in rank]


def build():
    catalogue = []
    for m in parts.MODELS:
        name = m['name']
        items = m['fn']()
        print('building', name, len(items), 'parts')
        # STEP (an assembly keeps the part names and colours)
        assy = cq.Assembly(name=name)
        for pname, wp, col in items:
            assy.add(wp, name=pname, color=cq.Color(*[c / 255 for c in hex_rgba(col)[:3]]))
        assy.save(os.path.join(DOCS, 'step', name + '.step'))
        comp = cq.Compound.makeCompound([wp.val() for n, wp, c in items])
        coarse = any('spring' in n for n, w, c in items)
        cq.exporters.export(comp, os.path.join(DOCS, 'stl', name + '.stl'), tolerance=0.1 if coarse else 0.02,
                            angularTolerance=0.4 if coarse else 0.1)
        # GLB, one node per part
        scene = trimesh.Scene()
        for pname, wp, col in items:
            coarse = 'spring' in pname
            scene.add_geometry(mesh_of(wp.val(), col, *( (0.12, 0.5) if coarse else (0.03, 0.15))),
                               node_name=pname, geom_name=pname)
        scene.export(os.path.join(DOCS, 'glb', name + '.glb'))
        # edges
        edges = {pname: edges_of(wp.val(), 0.15 if 'spring' in pname else 0.03) for pname, wp, col in items}
        with open(os.path.join(DOCS, 'edges', name + '.json'), 'w') as f:
            json.dump(edges, f, separators=(',', ':'))
        bb = comp.BoundingBox()
        offs = explode_offsets(items, m.get('explode'))
        catalogue.append(dict(
            name=name, title=m['title'], criteria=m['criteria'], uses=m['uses'],
            description=(m['fn'].__doc__ or '').strip().replace('\n', ' '),
            parts=[dict(name=p, colour='#' + c, explode=o) for (p, w, c), o in zip(items, offs)],
            size_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)],
            section=m.get('section'), exploded=bool(m.get('explode')),
            iso=list(to_gl(m.get('iso', (1, -1, 1)))),
            files=dict(step='step/%s.step' % name, stl='stl/%s.stl' % name, glb='glb/%s.glb' % name,
                       edges='edges/%s.json' % name)))
    with open(os.path.join(DOCS, 'models.json'), 'w') as f:
        json.dump(catalogue, f, indent=1)
    print('done', len(catalogue))


if __name__ == '__main__':
    build()
