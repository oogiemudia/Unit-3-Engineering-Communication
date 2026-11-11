"""Build the stage models for the Build steps tab of the viewer.

For every step in models/inventor_steps.py this writes a GLB and an edges file, plus one JSON file per model
with the Inventor commands. Each GLB holds the parts as they stand after the step, the material the step
added ("added__" nodes) and the material it cut away ("removed__" nodes), so the viewer can highlight them.
It also checks that the last step matches the finished model in models/parts.py.

Run from the repository root:  python3 tools/build_steps.py [model ...]
"""
import json, os, sys
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'models'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import parts  # noqa: E402
import inventor_steps as bs  # noqa: E402
from build_models import mesh_of, edges_of  # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'steps')
HIGHLIGHT = 'E8A33D'
REMOVED = 'D64545'
MIN_VOL = 0.01


def vol(wp):
    try:
        return wp.val().Volume()
    except Exception:
        return 0.0


SCALE = {'k': 1}     # large models (pipework, aircraft) mesh with a coarser chord tolerance: the model's mesh_scale


def tess(name):
    tol, ang = (0.12, 0.5) if 'spring' in name else (0.05, 0.2)
    return tol * SCALE['k'], ang


def build_model(m):
    name = m['name']
    SCALE['k'] = m.get('mesh_scale') or 1
    steps = bs.STEPS[name]()
    final = {p: w for p, w, c in m['fn']()}
    last = {p: w for p, w, c in steps[-1]['parts']}
    assert set(final) == set(last), (name, set(final) ^ set(last))
    for p in final:
        a, b = vol(final[p]), vol(last[p])
        diff = vol(final[p].cut(last[p])) + vol(last[p].cut(final[p])) if 'spring' not in p else abs(a - b)
        if diff >= 0.5 and abs(a - b) < 0.5:
            # a boolean between two copies of the same curved solid can fail (it returns the whole solid);
            # then compare the volume, bounding box and centre of mass instead
            fa, fb = final[p].val(), last[p].val()
            ba, bb = fa.BoundingBox(), fb.BoundingBox()
            box = max(abs(u - v) for u, v in zip((ba.xmin, ba.xmax, ba.ymin, ba.ymax, ba.zmin, ba.zmax),
                                                  (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)))
            if box < 0.01 and (fa.Center() - fb.Center()).Length < 0.01:
                diff = 0
        assert diff < 0.5, (name, p, a, b, diff)
    base = parts.base_of(m)
    out_dir = os.path.join(ROOT, 'docs', base, 'steps')
    os.makedirs(os.path.join(out_dir, name), exist_ok=True)
    meta, prev = [], {}
    for i, s in enumerate(steps, 1):
        scene = trimesh.Scene()
        edges, info = {}, []
        for pname, wp, col in s['parts']:
            scene.add_geometry(mesh_of(wp.val(), col, *tess(pname)), node_name='part__' + pname, geom_name='part__' + pname)
            edges['part__' + pname] = edges_of(wp.val(), (0.15 if 'spring' in pname else 0.05) * SCALE['k'])
            entry = dict(name=pname, colour='#' + col, new=pname not in prev, added=False, removed=False)
            if pname in prev and 'spring' not in pname:
                for key, shape, c in (('added', wp.cut(prev[pname]), HIGHLIGHT), ('removed', prev[pname].cut(wp), REMOVED)):
                    if vol(shape) > MIN_VOL:
                        scene.add_geometry(mesh_of(shape.val(), c, *tess(pname)), node_name=key + '__' + pname,
                                           geom_name=key + '__' + pname)
                        entry[key] = True
            info.append(entry)
        if s.get('overlay') is not None:
            ov = s['overlay'].val()
            scene.add_geometry(mesh_of(ov, HIGHLIGHT, 0.05 * SCALE['k'], 0.2), node_name='overlay', geom_name='overlay')
            edges['overlay'] = edges_of(ov, 0.05 * SCALE['k'])
        fname = 'step_%02d' % i
        if len(scene.geometry):
            scene.export(os.path.join(out_dir, name, fname + '.glb'))
        with open(os.path.join(out_dir, name, fname + '.json'), 'w') as f:
            json.dump(edges, f, separators=(',', ':'))
        meta.append(dict(n=i, title=s['title'], command=s['command'], actions=s['actions'], note=s.get('note'),
                         parts=info, overlay=s.get('overlay') is not None,
                         glb=base + 'steps/%s/%s.glb' % (name, fname) if len(scene.geometry) else None,
                         edges=base + 'steps/%s/%s.json' % (name, fname)))
        prev = {p: w for p, w, c in s['parts']}
        print(' ', name, i, s['title'])
    with open(os.path.join(out_dir, name + '.json'), 'w') as f:
        json.dump(dict(name=name, title=m['title'], software='Autodesk Inventor', steps=meta), f, indent=1)


def main(only):
    for m in parts.MODELS:
        if not only or m['name'] in only:
            build_model(m)


if __name__ == '__main__':
    main(sys.argv[1:])
