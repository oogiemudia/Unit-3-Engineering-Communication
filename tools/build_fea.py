"""Run the FEA for the FEA tab of the viewer and write docs/fea/<model>.json.

For each load case in models/fea_cases.py: mesh the part with gmsh (tetrahedra), solve linear static
elasticity with quadratic (10 node) elements in scikit-fem, and recover von Mises stress, displacement and
safety factor at the nodes. The JSON holds the outer surface of the mesh, the results on it, which faces are
fixed and loaded, and the Inventor Stress Analysis steps.

Needs: pip install cadquery gmsh scikit-fem   (gmsh needs libGLU)
Run from the repository root:  python3 tools/build_fea.py [model ...]
"""
import json, math, os, sys, tempfile
import numpy as np
import gmsh
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from skfem import MeshTet, Basis, FacetBasis, ElementTetP2, ElementVector, LinearForm, asm, condense, solve
from skfem.models.elasticity import linear_elasticity, lame_parameters

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
import parts  # noqa: E402
import fea_cases  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'fea')


def to_gl(p):
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1)


def describe(face):
    """The small description of a face that the load case tests use."""
    t = face.geomType()
    c = face.Center()
    n = None
    if t == 'PLANE':
        nv = face.normalAt(c)
        n = (nv.x, nv.y, nv.z)
    r = None
    if t == 'CYLINDER':
        r = BRepAdaptor_Surface(face.wrapped).Cylinder().Radius()
    return dict(t=t, c=(c.x, c.y, c.z), n=n, r=r, a=face.Area())


def pick(shape, test):
    out = []
    for f in shape.Faces():
        d = describe(f)
        if test(d):
            out.append(d)
    return out


def gmsh_mesh(shape, groups, size):
    """Mesh the solid; return nodes, tets and, per group, the surface triangles (as node index triples)."""
    tmp = tempfile.NamedTemporaryFile(suffix='.brep', delete=False).name
    shape.exportBrep(tmp)
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.model.add('part')
    gmsh.model.occ.importShapes(tmp)
    gmsh.model.occ.synchronize()
    os.unlink(tmp)
    surf = []
    for dim, tag in gmsh.model.getEntities(2):
        c = gmsh.model.occ.getCenterOfMass(2, tag)
        a = gmsh.model.occ.getMass(2, tag)
        surf.append((tag, np.array(c), a))
    group_tags = []
    for faces in groups:
        tags = []
        for d in faces:
            best = min(surf, key=lambda s: np.linalg.norm(s[1] - np.array(d['c'])) + abs(s[2] - d['a']) / max(d['a'], 1))
            assert np.linalg.norm(best[1] - np.array(d['c'])) < 0.05 and abs(best[2] - d['a']) < 1e-3 * d['a'] + 1e-3, d
            tags.append(best[0])
        group_tags.append(tags)
    gmsh.option.setNumber('Mesh.MeshSizeMax', size)
    gmsh.option.setNumber('Mesh.MeshSizeMin', size / 5)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 14)
    gmsh.option.setNumber('Mesh.Algorithm3D', 1)
    gmsh.model.mesh.generate(3)
    tags, xyz, _ = gmsh.model.mesh.getNodes()
    xyz = xyz.reshape(-1, 3)
    _, en = gmsh.model.mesh.getElementsByType(4)
    used = np.unique(en)
    index = np.full(int(tags.max()) + 1, -1)
    index[used.astype(int)] = np.arange(len(used))
    lookup = np.full(int(tags.max()) + 1, -1)
    lookup[tags.astype(int)] = np.arange(len(tags))
    nodes = xyz[lookup[used.astype(int)]]
    tets = index[en.astype(int)].reshape(-1, 4)
    tris = []
    for tag_list in group_tags:
        g = []
        for tag in tag_list:
            types, _, ntags = gmsh.model.mesh.getElements(2, tag)
            for ty, nt in zip(types, ntags):
                if ty == 2:
                    g.append(index[nt.astype(int)].reshape(-1, 3))
        tris.append(np.vstack(g))
    gmsh.finalize()
    return nodes, tets, tris


def von_mises(s):
    return np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2)
                   + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[2, 0] ** 2))


def solve_case(name, case):
    model = next(m for m in parts.MODELS if m['name'] == name)
    shape = dict((p, w) for p, w, c in model['fn']())[case['part']].val()
    fixed_faces = [pick(shape, f['test']) for f in case['fixed']]
    load_faces = [pick(shape, l['test']) for l in case['loads']]
    for f, g in zip(case['fixed'] + case['loads'], fixed_faces + load_faces):
        assert g, (name, f['where'])
    bb = shape.BoundingBox()
    diag = math.sqrt(bb.xlen ** 2 + bb.ylen ** 2 + bb.zlen ** 2)
    size = diag / 24
    nodes, tets, tris = gmsh_mesh(shape, fixed_faces + load_faces, size)
    m = MeshTet(nodes.T.copy(), tets.T.copy())
    e = ElementVector(ElementTetP2())
    ib = Basis(m, e)
    mat = case['material']
    lam, mu = lame_parameters(mat['E'], mat['nu'])
    K = asm(linear_elasticity(lam, mu), ib)

    # facet index for each group triangle
    fkey = {tuple(sorted(t)): i for i, t in enumerate(m.facets.T)}
    gfacets = [np.array([fkey[tuple(sorted(t))] for t in g]) for g in tris]
    nf = len(case['fixed'])
    fixed_facets = np.unique(np.concatenate(gfacets[:nf]))
    f = np.zeros(K.shape[0])
    arrows = []
    for load, facets in zip(case['loads'], gfacets[nf:]):
        fb = FacetBasis(m, e, facets=facets)
        # area of the group
        p = m.p[:, m.facets[:, facets]]
        tri_area = 0.5 * np.linalg.norm(np.cross((p[:, 1] - p[:, 0]).T, (p[:, 2] - p[:, 0]).T), axis=1)
        A = tri_area.sum()
        if load['kind'] == 'pressure':
            P = load['value']
            f += asm(LinearForm(lambda v, w: -P * (v[0] * w.n[0] + v[1] * w.n[1] + v[2] * w.n[2])), fb)
        elif load['dir'] == 'normal':
            t = load['value'] / A
            f += asm(LinearForm(lambda v, w: -t * (v[0] * w.n[0] + v[1] * w.n[1] + v[2] * w.n[2])), fb)
        else:
            d = np.array(load['dir'], float) / np.linalg.norm(load['dir'])
            t = load['value'] / A * d
            f += asm(LinearForm(lambda v, w: t[0] * v[0] + t[1] * v[1] + t[2] * v[2]), fb)
        # arrows: a spread of triangle centres, pointing the way the load acts
        cen = p.mean(axis=1).T
        nrm = np.cross((p[:, 1] - p[:, 0]).T, (p[:, 2] - p[:, 0]).T)
        nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        # make normals point out of the solid
        el = m.f2t[0, facets]
        inside = m.p[:, m.t[:, el]].mean(axis=1).T
        flip = np.einsum('ij,ij->i', nrm, cen - inside) < 0
        nrm[flip] *= -1
        rng = np.random.default_rng(1)
        k = min(14, len(cen))
        sel = [0]
        for _ in range(k - 1):  # farthest point sampling
            dmin = np.min(np.linalg.norm(cen[:, None, :] - cen[sel][None, :, :], axis=2), axis=1)
            sel.append(int(np.argmax(dmin)))
        for i in sel:
            if load['kind'] == 'pressure' or load['dir'] == 'normal':
                dv = -nrm[i]
            else:
                dv = np.array(load['dir'], float)
            arrows.append(dict(p=np.round(to_gl(cen[i]), 2).tolist(), d=np.round(to_gl(dv / np.linalg.norm(dv)), 3).tolist(),
                               out=bool(load['kind'] == 'pressure')))
    D = ib.get_dofs(fixed_facets).all()
    u = solve(*condense(K, f, D=D))

    # stress at the corners of every element, averaged at each node
    X = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], float)
    vb = Basis(m, e, quadrature=(X, np.ones(4) / 24))
    G = vb.interpolate(u).grad                          # (3, 3, nel, 4)
    eps = 0.5 * (G + G.transpose(1, 0, 2, 3))
    tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
    sig = 2 * mu * eps + lam * tr * np.eye(3)[:, :, None, None]
    vm_c = von_mises(sig)                                # (nel, 4), in element vertex order
    vm = np.zeros(m.p.shape[1])
    cnt = np.zeros(m.p.shape[1])
    np.add.at(vm, m.t.T.ravel(), vm_c.ravel())
    np.add.at(cnt, m.t.T.ravel(), 1)
    vm /= np.maximum(cnt, 1)
    U = np.stack([u[ib.nodal_dofs[k]] for k in range(3)], axis=1)

    # outer surface, wound outwards
    bf = m.boundary_facets()
    tri = m.facets[:, bf].T.copy()
    el = m.f2t[0, bf]
    opp = np.array([np.setdiff1d(m.t[:, t], fc)[0] for t, fc in zip(el, tri)])
    a, b, c = (m.p[:, tri[:, k]].T for k in range(3))
    nrm = np.cross(b - a, c - a)
    flip = np.einsum('ij,ij->i', nrm, m.p[:, opp].T - a) > 0
    tri[flip] = tri[flip][:, [0, 2, 1]]
    group = np.zeros(len(bf), int)
    pos_of = {f: i for i, f in enumerate(bf)}
    for gi, facets in enumerate(gfacets):
        for fc in facets:
            group[pos_of[fc]] = 1 if gi < nf else 2
    used = np.unique(tri)
    remap = np.full(m.p.shape[1], -1)
    remap[used] = np.arange(len(used))
    P = to_gl(m.p[:, used].T)
    Ug = to_gl(U[used])
    vm_s = vm[used]
    i_max = int(np.argmax(vm))
    res = dict(vm_max=float(vm.max()), disp_max=float(np.linalg.norm(U, axis=1).max()),
               sf_min=float(mat['yield_strength'] / vm.max()),
               vm_max_at=np.round(to_gl(m.p[:, i_max]), 2).tolist())
    mesh = dict(nodes=int(m.p.shape[1]), elements=int(m.t.shape[1]), size=round(size, 2),
                dofs=int(K.shape[0]), solid_nodes_p2=int(K.shape[0] // 3))
    surf = dict(pos=np.round(P, 3).ravel().tolist(), tri=remap[tri].ravel().tolist(), group=group.tolist(),
                u=np.round(Ug, 6).ravel().tolist(), vm=np.round(vm_s, 3).tolist())
    return res, mesh, surf, arrows


def fmt(x, unit, sig=3):
    return ('%.' + str(sig) + 'g') % x + ' ' + unit


def inventor_steps(model, case, res, mesh):
    mat = case['material']
    fixed = ' and '.join(f['where'] for f in case['fixed'])
    steps = [
        dict(view='part', title='Open the Stress Analysis environment', command='Environments tab > Begin panel > Stress Analysis',
             actions=['Open the part (%s) in Inventor.' % case['part'],
                      'Click the Environments tab, then Stress Analysis. The Stress Analysis tab opens.'],
             note='The study here: ' + case['story']),
        dict(view='part', title='Create a static study', command='Stress Analysis tab > Manage panel > Create Simulation',
             actions=['Click Create Simulation. Give it a name, for example "%s load test".' % model['title'],
                      'Simulation Type: Static Analysis. Design Objective: Single Point. Click OK.']),
        dict(view='part', title='Assign the material', command='Stress Analysis tab > Material panel > Assign',
             actions=['Click Assign. In the Override Material column pick %s.' % mat['name'],
                      "Check its properties in the Material Browser: Young's modulus %s, Poisson's ratio %s, yield strength %s." % (
                          fmt(mat['E'] / 1000, 'GPa'), mat['nu'], fmt(mat['yield_strength'], 'MPa')),
                      'Click OK.'],
             note='The results below use these values. If your library values differ, your answers will differ a little.'),
        dict(view='fixed', title='Fix the part', command='Stress Analysis tab > Constraints panel > Fixed',
             actions=['Click Fixed and pick %s.' % fixed, 'Click OK. A Fixed Constraint appears in the browser under Constraints.'],
             note='A fixed constraint stops the face moving in any direction. It stands in for the bolts, the bench or the wall.'),
    ]
    for l in case['loads']:
        cmd = 'Pressure' if l['kind'] == 'pressure' else 'Force'
        steps.append(dict(view='load', title='Apply the load: ' + cmd.lower(),
                          command='Stress Analysis tab > Loads panel > ' + cmd,
                          actions=['Click %s and pick %s.' % (cmd, l['where']),
                                   'Set: %s. Use the Direction button and Flip if the arrow points the wrong way.' % l['how'],
                                   'Click OK.'],
                          note='The arrows show where the load acts and which way.'))
    steps += [
        dict(view='mesh', title='Set up and view the mesh', command='Stress Analysis tab > Prepare panel > Mesh Settings, then Mesh View',
             actions=['Click Mesh Settings. Average Element Size 0.1, Minimum Element Size 0.2, Grading Factor 1.5, Maximum Turn Angle 60 degrees. Tick Create Curved Mesh Elements. Click OK.',
                      'Click Mesh View. Inventor splits the part into small tetrahedra (four sided elements).',
                      'Look for small elements round holes and fillets: that is where stress changes fastest.'],
             note='Sizes in Mesh Settings are a fraction of the part size, not millimetres. The hub mesh: %d elements, %d nodes, about %s mm across.' % (
                 mesh['elements'], mesh['solid_nodes_p2'], mesh['size'])),
        dict(view='mesh', title='Converge the answer (optional)', command='Stress Analysis tab > Prepare panel > Convergence Settings',
             actions=['Click Convergence Settings. Set Maximum Number of h Refinements to 2 and Stop Criteria to 10 %.',
                      'Inventor then refines the mesh where the stress is highest and solves again, until the answer changes by less than 10 %.'],
             note='A finer mesh gives a more trustworthy peak stress, but takes longer to solve.'),
        dict(view='deformed', title='Run the simulation', command='Stress Analysis tab > Solve panel > Simulate',
             actions=['Click Simulate, then Run.', 'When it finishes, the results appear in the browser under Results.'],
             note='The shape is drawn with the movement exaggerated so you can see how the part bends. Use the slider to change the scale.'),
        dict(view='vm', title='Read the von Mises stress', command='Results in the browser > Von Mises Stress',
             actions=['Double click Von Mises Stress in the browser.',
                      'Display panel: tick Maximum to show where the highest stress is.',
                      'Compare it with the yield strength of the material.'],
             note='Maximum von Mises stress: %s (yield strength %s).' % (fmt(res['vm_max'], 'MPa'), fmt(mat['yield_strength'], 'MPa'))
             + ' Stress right at the edge of a fixed face can read higher than real life, because a fixed face is perfectly rigid; look at the stress just away from it too.'),
        dict(view='disp', title='Read the displacement', command='Results in the browser > Displacement',
             actions=['Double click Displacement.', 'Use Result panel > Animate to watch the part deflect under load.'],
             note='Maximum displacement: %s.' % fmt(res['disp_max'], 'mm')),
        dict(view='sf', title='Check the safety factor', command='Results in the browser > Safety Factor',
             actions=['Double click Safety Factor. Inventor divides the yield strength by the stress at every point.',
                      'Anywhere below 1 would yield. Most designs aim for 2 or more.'],
             note='Lowest safety factor: %s.' % ('%.1f' % res['sf_min'] if res['sf_min'] < 1000 else 'over 1000')),
        dict(view='vm', title='Write the report', command='Stress Analysis tab > Report panel > Report',
             actions=['Click Report. Choose the study, a format (HTML or Word) and where to save it. Click OK.',
                      'The report lists the material, the constraints, the loads, the mesh and every result, with pictures.'],
             note='Hand in the report, or copy its tables into your portfolio.'),
    ]
    return steps


def build(name):
    case = fea_cases.CASES[name]
    model = next(m for m in parts.MODELS if m['name'] == name)
    res, mesh, surf, arrows = solve_case(name, case)
    steps = inventor_steps(model, case, res, mesh)
    mat = dict(case['material'])
    out = dict(name=name, title=model['title'], part=case['part'], story=case['story'], material=mat,
               fixed=[f['where'] for f in case['fixed']],
               loads=[dict(kind=l['kind'], value=l['value'], where=l['where'], how=l['how']) for l in case['loads']],
               results=res, mesh=mesh, steps=steps, surface=surf, arrows=arrows)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + '.json'), 'w') as f:
        json.dump(out, f, separators=(',', ':'))
    print('%-20s %6d elems  vm %8.2f MPa  disp %.4f mm  SF %.1f' % (name, mesh['elements'], res['vm_max'], res['disp_max'], res['sf_min']))


if __name__ == '__main__':
    for n in (sys.argv[1:] or fea_cases.CASES):
        build(n)
