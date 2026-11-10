// Shared code for the lesson demonstrations: the 3D stage, camera moves, drawn lines, labels and the step panel.
// CAD axes (Z up, Y back) are turned into viewer axes (Y up, Z towards you) by G(), as in the 3D viewer.
import * as THREE from 'three';
import { OrbitControls } from './vendor/controls/OrbitControls.js';
import { GLTFLoader } from './vendor/loaders/GLTFLoader.js';
import { mergeGeometries } from './vendor/utils/BufferGeometryUtils.js';
export { THREE };

export const G = (x, y, z) => new THREE.Vector3(x, z, -y);
export const GA = a => G(a[0], a[1], a[2]);
export const INK = 0x1D2B3A, HI = 0x6B2FB3, FAINT = 0x9AA5B1, AMBER = 0xE8A33D;
export const WIDTH = { thick: 0.42, thin: 0.2, faint: 0.14 };   // tube radii in mm: thick lines are twice thin ones
const PATTERN = { dash: [4, 2], chain: [10, 2, 1.6, 2] };

export async function loadData() { return (await fetch('demos/data.json')).json(); }

// ---------------------------------------------------------------- the stage
export function makeStage() {
  const el = document.getElementById('stage');
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#F4F6F8');
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a96a3, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(2, 3, 2.5); scene.add(sun);
  const fill = new THREE.DirectionalLight(0xffffff, 0.6); fill.position.set(-3, 1, -2); scene.add(fill);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 6000);
  const controls = new OrbitControls(cam, el);
  controls.enableDamping = true;
  const S = { el, renderer, scene, cam, controls, half: 60, labels: [], frameFns: [], tween: null };

  S.resize = () => {
    const w = el.clientWidth, h = el.clientHeight;
    renderer.setSize(w, h, false);
    const a = w / Math.max(1, h);
    cam.left = -S.half * a; cam.right = S.half * a; cam.top = S.half; cam.bottom = -S.half;
    cam.updateProjectionMatrix();
  };
  new ResizeObserver(S.resize).observe(el);

  // place the camera looking along -dir at a centre, with half the view height = half
  S.place = (dir, centre, half) => {
    S.half = half; controls.target.copy(centre);
    cam.position.copy(centre.clone().add(dir.clone().normalize().multiplyScalar(2000)));
    cam.up.set(0, 1, 0); cam.lookAt(centre); S.resize(); controls.update();
  };
  // a smooth camera move: the direction turns, the centre slides and the zoom changes together
  S.fly = (dir, centre, half, ms = 1000) => {
    const from = { dir: cam.position.clone().sub(controls.target).normalize(), centre: controls.target.clone(), half: S.half };
    S.tween = { from, to: { dir: dir.clone().normalize(), centre: centre.clone(), half }, t0: performance.now(), ms };
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) S.tween.ms = 1;
  };
  // the centre and zoom that fit a box when it is seen from dir
  S.fit = (dir, box, margin = 1.18) => {
    const d = dir.clone().normalize();
    let up = new THREE.Vector3(0, 1, 0);
    if (Math.abs(d.dot(up)) > 0.999) up = new THREE.Vector3(0, 0, -1);
    const right = new THREE.Vector3().crossVectors(up, d).normalize();
    const vup = new THREE.Vector3().crossVectors(d, right).normalize();
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const i of [0, 1]) for (const j of [0, 1]) for (const k of [0, 1]) {
      const p = new THREE.Vector3(i ? box.max.x : box.min.x, j ? box.max.y : box.min.y, k ? box.max.z : box.min.z);
      x0 = Math.min(x0, p.dot(right)); x1 = Math.max(x1, p.dot(right)); y0 = Math.min(y0, p.dot(vup)); y1 = Math.max(y1, p.dot(vup));
    }
    const a = el.clientWidth / Math.max(1, el.clientHeight);
    const centre = right.clone().multiplyScalar((x0 + x1) / 2).add(vup.clone().multiplyScalar((y0 + y1) / 2))
      .add(d.clone().multiplyScalar(box.getCenter(new THREE.Vector3()).dot(d)));
    return { centre, half: Math.max((y1 - y0) / 2, (x1 - x0) / 2 / a) * margin };
  };
  S.flyFit = (dir, box, margin, ms) => { const f = S.fit(dir, box, margin); S.fly(dir, f.centre, f.half, ms); };

  // labels: HTML text pinned to a 3D point
  S.label = (text, pos, cls = '') => {
    const div = document.createElement('div'); div.className = 'lab3d ' + cls; div.innerHTML = text;
    el.appendChild(div);
    const L = { div, pos: pos.clone(), visible: true, set(v) { this.visible = v; div.classList.toggle('hide', !v); return this; } };
    S.labels.push(L); return L;
  };

  function slerpDir(a, b, t) {
    const ang = a.angleTo(b);
    if (ang < 1e-5) return b.clone();
    let axis = new THREE.Vector3().crossVectors(a, b);
    if (axis.lengthSq() < 1e-10) axis = new THREE.Vector3(0, 1, 0);
    return a.clone().applyAxisAngle(axis.normalize(), ang * t);
  }
  function frame(now) {
    requestAnimationFrame(frame);
    if (S.tween) {
      const tw = S.tween, t = Math.min(1, (now - tw.t0) / tw.ms), e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      const d = slerpDir(tw.from.dir, tw.to.dir, e), c = tw.from.centre.clone().lerp(tw.to.centre, e);
      S.half = tw.from.half + (tw.to.half - tw.from.half) * e;
      controls.target.copy(c); cam.position.copy(c.clone().add(d.multiplyScalar(2000))); cam.lookAt(c); S.resize();
      if (t >= 1) { S.tween = null; controls.update(); }
    } else controls.update();
    for (const f of S.frameFns) f(now);
    const w = el.clientWidth, h = el.clientHeight;
    for (const L of S.labels) {
      const v = L.pos.clone().project(cam), x = (v.x + 1) / 2 * w, y = (1 - v.y) / 2 * h;
      // keep every label inside the picture, even on a narrow phone screen
      const lw = L.div.offsetWidth, cl = L.div.classList;
      const shift = cl.contains('l') ? 0 : cl.contains('r') ? lw : lw / 2;
      const left = Math.max(4, Math.min(w - 4 - lw, x - shift)) + shift;
      L.div.style.left = left.toFixed(1) + 'px';
      L.div.style.top = y.toFixed(1) + 'px';
    }
    renderer.render(scene, cam);
  }
  S.resize(); requestAnimationFrame(frame);
  window.DEMO = S;
  return S;
}

// ---------------------------------------------------------------- the CAD model from the hub
export async function loadModel(S, name, colour) {
  const cat = await (await fetch('models.json')).json();
  const entry = cat.find(e => e.name === name);
  const gltf = await new GLTFLoader().loadAsync(entry.files.glb);
  const edges = await (await fetch(entry.files.edges)).json();
  const group = new THREE.Group();
  const mats = [];
  gltf.scene.traverse(o => {
    if (!o.isMesh) return;
    const mat = new THREE.MeshStandardMaterial({ color: new THREE.Color(colour || entry.parts[0].colour), metalness: 0.1, roughness: 0.6,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
    mats.push(mat); group.add(new THREE.Mesh(o.geometry, mat));
  });
  const pos = [];
  for (const k of Object.keys(edges)) for (const pl of edges[k]) for (let i = 0; i + 5 < pl.length; i += 3) pos.push(pl[i], pl[i + 1], pl[i + 2], pl[i + 3], pl[i + 4], pl[i + 5]);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  const edgeMat = new THREE.LineBasicMaterial({ color: INK, transparent: true });
  const edgeLines = new THREE.LineSegments(g, edgeMat); group.add(edgeLines);
  S.scene.add(group);
  const M = { entry, group, mats, edgeLines, edgeMat,
    setOpacity(o) { for (const m of mats) { m.transparent = o < 1; m.opacity = o; m.depthWrite = o >= 1; m.needsUpdate = true; } },
    setEdges(o) { edgeLines.visible = o > 0; edgeMat.opacity = o; } };
  return M;
}

// ---------------------------------------------------------------- drawn lines as thin tubes, so thick and thin really differ
function cyl(a, b, r) {
  const d = b.clone().sub(a), L = d.length();
  if (L < 1e-4) return null;
  const g = new THREE.CylinderGeometry(r, r, L, 10, 1, true);
  g.translate(0, L / 2, 0);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize()));
  g.translate(a.x, a.y, a.z);
  return g;
}
function ball(p, r) { const g = new THREE.SphereGeometry(r, 12, 8); g.translate(p.x, p.y, p.z); return g; }

// polys: arrays of THREE.Vector3; kind: 'thick', 'thin' or 'faint'; pattern: null, 'dash' or 'chain'
export function lines(polys, { kind = 'thin', pattern = null, color = INK, opacity = 1, onTop = false } = {}) {
  const r = WIDTH[kind] || kind, geos = [], pat = pattern ? PATTERN[pattern] : null;
  for (const pts of polys) {
    if (!pat) {
      for (let i = 0; i + 1 < pts.length; i++) { const g = cyl(pts[i], pts[i + 1], r); if (g) geos.push(g); }
      if (kind === 'thick') for (const p of pts) geos.push(ball(p, r));
      continue;
    }
    let k = 0, left = pat[0];
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i], b = pts[i + 1], len = a.distanceTo(b), dir = b.clone().sub(a).normalize();
      let pos = 0;
      while (pos < len - 1e-6) {
        const step = Math.min(left, len - pos);
        if (k % 2 === 0) { const g = cyl(a.clone().addScaledVector(dir, pos), a.clone().addScaledVector(dir, pos + step), r); if (g) geos.push(g); }
        pos += step; left -= step;
        if (left <= 1e-6) { k = (k + 1) % pat.length; left = pat[k]; }
      }
    }
  }
  const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthTest: !onTop, depthWrite: !onTop });
  const mesh = new THREE.Mesh(geos.length ? mergeGeometries(geos) : new THREE.BufferGeometry(), mat);
  mesh.renderOrder = onTop ? 10 : 2;
  return mesh;
}
export function cone(tip, dir, { len = 3.6, r = 1.15, color = INK } = {}) {
  const d = dir.clone().normalize();
  const g = new THREE.ConeGeometry(r, len, 16);
  g.translate(0, -len / 2, 0);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d));
  g.translate(tip.x, tip.y, tip.z);
  return new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color, transparent: true }));
}
export function dot(p, { r = 0.9, color = INK } = {}) {
  return new THREE.Mesh(ball(p, r), new THREE.MeshBasicMaterial({ color, transparent: true }));
}
// set the colour and opacity of every mesh in a group
export function tint(obj, color, opacity) {
  obj.traverse(o => { if (o.material) { if (color !== null) o.material.color.set(color);
    if (opacity !== undefined) { o.material.opacity = opacity; o.visible = opacity > 0.001; } } });
}
// fade a group in or out over a short time
export function fade(S, obj, to, ms = 450) {
  const mats = []; obj.traverse(o => { if (o.material) mats.push(o); });
  const from = mats.map(o => (o.visible ? o.material.opacity : 0));
  const t0 = performance.now();
  if (to > 0) mats.forEach(o => { o.visible = true; });
  const goal = mats.map(o => to * (o.material.userData.base ?? 1));    // a see-through material keeps its own strength
  const fn = now => {
    const t = Math.min(1, (now - t0) / ms);
    mats.forEach((o, i) => { o.material.opacity = from[i] + (goal[i] - from[i]) * t; });
    if (t >= 1) { if (to <= 0.001) mats.forEach(o => { o.visible = false; }); S.frameFns.splice(S.frameFns.indexOf(fn), 1); }
  };
  S.frameFns.push(fn);
}

// ---------------------------------------------------------------- the step panel (Next and Back, arrow keys and clickers)
export function stepper(steps, apply) {
  const sn = document.getElementById('sn'), st = document.getElementById('st'), sh = document.getElementById('sh'), sp = document.getElementById('sp');
  const prev = document.getElementById('prev'), next = document.getElementById('next'), dots = document.getElementById('dots');
  let i = 0;
  st.textContent = steps.length;
  dots.innerHTML = steps.map((s, k) => `<button aria-label="Step ${k + 1}: ${s.title}" title="${s.title}">${s.dot || k + 1}</button>`).join('');
  const go = (k, instant = false) => {
    i = Math.max(0, Math.min(steps.length - 1, k));
    sn.textContent = i + 1; sh.textContent = steps[i].title; sp.innerHTML = steps[i].text;
    prev.disabled = i === 0; next.textContent = i === steps.length - 1 ? 'Start again' : 'Next';
    [...dots.children].forEach((b, j) => b.classList.toggle('on', j === i));
    history.replaceState(null, '', location.pathname + location.search + '#' + (i + 1));
    apply(i, instant);
  };
  prev.onclick = () => go(i - 1);
  next.onclick = () => go(i === steps.length - 1 ? 0 : i + 1);
  [...dots.children].forEach((b, j) => { b.onclick = () => go(j); });
  window.addEventListener('keydown', e => {
    if (e.target.closest && e.target.closest('input,select,textarea')) return;
    if (['ArrowRight', 'PageDown', ' ', 'n', 'N'].includes(e.key)) { e.preventDefault(); go(i === steps.length - 1 ? i : i + 1); }
    if (['ArrowLeft', 'PageUp', 'p', 'P'].includes(e.key)) { e.preventDefault(); go(i - 1); }
  });
  const start = parseInt(location.hash.slice(1), 10);
  return { go, start: () => go(Number.isFinite(start) ? start - 1 : 0, true), get i() { return i; } };
}

// 2D polylines from the data file, lifted into 3D by a function f(u, v)
export const lift = (pls, f) => pls.map(pl => pl.map(p => f(p[0], p[1])));
// a centre line made a little longer at each end, as on a drawing
export function extend(a, b, by = 4) {
  const d = [b[0] - a[0], b[1] - a[1]], L = Math.hypot(d[0], d[1]) || 1;
  return [[a[0] - d[0] / L * by, a[1] - d[1] / L * by], [b[0] + d[0] / L * by, b[1] + d[1] / L * by]];
}
