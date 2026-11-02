// Renders the 风物 trailer frame by frame from the game itself.
// The game's own requestAnimationFrame loop is switched off; every frame we advance the world by 1/24 s,
// place the camera and the wind on their scripted paths, draw, and screenshot. Cards are HTML over the canvas.
// usage: node render.js <outDir> [onlyShot]
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.argv[2], ONLY = process.argv[3];
const FPS = +(process.env.FPS || 24), DT = 1 / FPS, W = +(process.env.TW || 1280), H = Math.round(W * 9 / 16);
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: W, height: H } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.addInitScript(() => { window.requestAnimationFrame = () => 1; }); // we drive the frames
  await p.goto('http://localhost:8765/index.html'); await p.waitForTimeout(3000);
  await p.addStyleTag({ url: 'https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@200;300;400&display=block' });
  await p.addStyleTag({ content: `
    #season,#line,#hint,#dots,#edge{display:none!important}
    #tr-black{position:fixed;inset:0;background:#000;z-index:50;pointer-events:none}
    .tr{position:fixed;z-index:60;pointer-events:none;font-family:"Noto Serif SC",serif;font-weight:300;color:rgba(247,242,232,.94);opacity:0;
        -webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
    /* subtitles: small, light, widely spaced, low on the frame */
    #tr-sub{left:0;right:0;bottom:38px;padding:16px 0;background:radial-gradient(ellipse 34% 100% at 50% 50%,rgba(8,10,14,.26),rgba(8,10,14,0) 100%);text-align:center;font-size:19px;letter-spacing:.42em;text-indent:.42em;text-shadow:0 0 14px rgba(0,0,0,.38),0 1px 2px rgba(0,0,0,.25)}
    #tr-card{left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;font-size:21px;font-weight:200;letter-spacing:.7em;text-indent:.7em}
    /* season: a hairline of vermilion, then the name, very small */
    #tr-season{left:56px;bottom:52px;font-size:13px;font-weight:400;letter-spacing:.6em;display:flex;align-items:center;gap:14px;color:rgba(247,242,232,.9);text-shadow:0 0 10px rgba(0,0,0,.35)}
    #tr-season i{width:22px;height:1px;background:#d0503f;display:block}
    #tr-title{left:0;right:0;top:46%;transform:translateY(-50%);text-align:center}
    #tr-title h1{margin:0;font-weight:200;font-size:58px;letter-spacing:.62em;text-indent:.62em;color:#f2ece0}
    #tr-title .rule{width:36px;height:1px;background:rgba(208,80,63,.85);margin:30px auto 22px}
    #tr-title div.s{font-size:11px;font-weight:300;letter-spacing:.7em;text-indent:.7em;color:rgba(214,206,192,.7)}` });
  await p.evaluate(() => {
    for (const id of ['tr-black', 'tr-sub', 'tr-card', 'tr-season', 'tr-title']) { const d = document.createElement('div'); d.id = id; if (id !== 'tr-black') d.className = 'tr'; document.body.appendChild(d); }
    document.getElementById('tr-title').innerHTML = '<h1>风物</h1><div class="rule"></div><div class="s">立春　清明　夏至　秋分　冬至</div>';
    const w = window.__wind, $ = id => document.getElementById(id);
    // one frame: optional scripted wind and camera, advance, draw, set the overlays
    window.__T = (f) => {
      if (f.wind) { const [x, y, z, yaw, pitch] = f.wind; w.player.pos.set(x, y, z); w.player.yaw = yaw; w.player.pitch = pitch; }
      if (f.cam) w.peek(f.cam[0], f.cam[1]);
      w.step(f.dt);
      if (f.cam) { w.camera.position.set(...f.cam[0]); w.camera.lookAt(...f.cam[1]); }
      w.renderer.render(w.scene, w.camera);
      $('tr-black').style.opacity = f.black ?? 0;
      for (const k of ['sub', 'card', 'season']) { const el = $('tr-' + k), v = f[k]; el.style.opacity = v ? v[1] : 0; if (v && el.dataset.t !== v[0]) { el.dataset.t = v[0]; el.innerHTML = k === 'season' ? `<i></i>${v[0]}` : v[0]; } }
      $('tr-title').style.opacity = f.title ?? 0;
    };
  });
  await p.evaluate(async () => { const t = '爷它怎么不转等风来你是立春清明夏至秋分冬他说一就了物'; for (const w of [200, 300, 400]) await document.fonts.load(`${w} 20px "Noto Serif SC"`, t); await document.fonts.ready; });
  console.log('font ok', await p.evaluate(() => document.fonts.check('300 20px "Noto Serif SC"', '风')));
  const T = f => p.evaluate(f => window.__T(f), f);
  const ff = s => p.evaluate(n => { const w = window.__wind; for (let i = 0; i < n; i++) w.step(1 / 24); }, Math.round(s * FPS));
  const q = fn => p.evaluate(fn);
  let frame = 0;
  const shoot = async f => { await T({ dt: DT, ...f }); await p.screenshot({ path: `${OUT}/f${String(frame).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 88 }); frame++; };
  const fade = (t, d, a, b2) => Math.max(0, Math.min(1, Math.min((t - a) / d, (b2 - t) / d)));   // in over d after a, out over d before b2
  const ease = u => u * u * (3 - 2 * u), mix = (a, c, u) => a.map((v, i) => v + (c[i] - v) * u);
  const yawTo = (a, c) => [Math.atan2(-(c[0] - a[0]), -(c[2] - a[2])), Math.atan2(c[1] - a[1], Math.hypot(c[0] - a[0], c[2] - a[2]))];
  // a wind path through points (Catmull-Rom), giving position and heading
  const path = pts => u => {
    const n = pts.length - 1, s = Math.min(n - 1e-6, Math.max(0, u * n)), i = Math.floor(s), t = s - i;
    const P0 = pts[Math.max(0, i - 1)], P1 = pts[i], P2 = pts[i + 1], P3 = pts[Math.min(n, i + 2)];
    const c = k => 0.5 * (2 * P1[k] + (-P0[k] + P2[k]) * t + (2 * P0[k] - 5 * P1[k] + 4 * P2[k] - P3[k]) * t * t + (-P0[k] + 3 * P1[k] - 3 * P2[k] + P3[k]) * t * t * t);
    return [c(0), c(1), c(2)];
  };
  const windAt = (pf, u) => { const a = pf(u), c = pf(Math.min(1, u + 0.01)); return [...a, ...yawTo(a, c)]; };
  const seasonCard = (name, t, len) => [name, fade(t, 0.6, 0.3, len - 0.2) * 0.95];
  const shots = {};

  // —— 0 · black, the wind is heard before anything is seen
  shots.open = async () => { for (let i = 0; i < 2 * FPS; i++) await shoot({ dt: 0, black: 1 }); };

  // —— 1–3 · the prologue as the game plays it: down into the valley, the pinwheel that won't turn
  shots.prologue = async () => {
    await p.click('#title'); await p.evaluate(() => { document.getElementById('title').style.display = 'none'; });
    for (let i = 0; i < 6.3 * FPS; i++) { const t = i / FPS; await shoot({ black: 1 - Math.min(1, t / 1.4) }); }
    for (let i = 0; i < 4.2 * FPS; i++) { const t = i / FPS; await shoot({ sub: ['“爷爷，它怎么不转？”', fade(t, 0.35, 0.2, 4.0)] }); }
    await ff(0.3);
    for (let i = 0; i < 3 * FPS; i++) { const t = i / FPS; await shoot({ sub: ['“等风来。”', fade(t, 0.35, 0.1, 2.7)], black: Math.max(0, (t - 2.5) / 0.5) }); }
    // the beat in the dark, while the world catches up to the moment the wind arrives
    await ff(17.5 - 14.3 - 1.8);
    for (let i = 0; i < 1.8 * FPS; i++) { const t = i / FPS; await shoot({ dt: DT, black: 1, card: ['你是风。', fade(t, 0.4, 0.15, 1.75)] }); }
    // —— 4 · the wind comes, finds the pinwheel, circles it, and goes off down the valley
    for (let i = 0; i < 7.5 * FPS; i++) { const t = i / FPS; await shoot({ black: Math.max(0, 1 - t / 0.35) }); }
  };

  // —— 5 · 立春: low over the mist, the wind's trail through it
  shots.spring = async () => {
    await q(() => window.__wind.startChapter(0)); await ff(4);
    const pts = await q(() => { const w = window.__wind, z0 = w.VZ + 120, a = []; for (let k = 0; k <= 4; k++) { const z = z0 - k * 45; a.push([w.riverX(z) + 18 - k * 4, w.WATER + 9 + Math.sin(k) * 2, z]); } return a; });
    const pf = path(pts);
    for (let i = 0; i < 3.6 * FPS; i++) { const t = i / FPS, u = t / 3.6, wp = windAt(pf, 0.15 + u * 0.7);
      const cp = pf(Math.max(0, 0.15 + u * 0.7 - 0.08)); await shoot({ wind: wp, cam: [[cp[0] + 9, cp[1] + 4, cp[2] + 6], [wp[0], wp[1], wp[2]]], season: seasonCard('立春', t, 3.6) }); }
  };

  // —— 6 · 清明: the wind runs in behind a child and the kite goes up
  shots.kites = async () => {
    await q(() => window.__wind.startChapter(1)); await ff(2.5);
    const s = await q(() => { const w = window.__wind, t = w.targets[2].pos, Wd = [0.75, -0.66], n = Math.hypot(...Wd); const W2 = [Wd[0] / n, Wd[1] / n], S = [-W2[1], W2[0]];
      return { t: [t.x, t.y, t.z], W: W2, S }; });
    const [tx, ty, tz] = s.t, [wx, wz] = s.W, [sx, sz] = s.S;
    const pf = path([[tx - wx * 40 + sx * 6, ty + 6, tz - wz * 40 + sz * 6], [tx - wx * 14, ty + 3, tz - wz * 14], [tx, ty + 2.5, tz], [tx + wx * 16, ty + 12, tz + wz * 16], [tx + wx * 34, ty + 24, tz + wz * 34]]);
    const cam0 = [tx - wx * 11 + sx * 6, ty + 0.4, tz - wz * 11 + sz * 6];
    for (let i = 0; i < 4.6 * FPS; i++) { const t = i / FPS, u = Math.min(1, t / 4.2);
      const look = mix([tx, ty + 1, tz], [tx + wx * 18, ty + 13, tz + wz * 18], ease(Math.min(1, Math.max(0, (t - 1) / 3))));
      await shoot({ wind: windAt(pf, u), cam: [cam0, look], season: seasonCard('清明', t, 4.6) }); }
  };

  // —— 7 · 夏至: a sail fills as the wind goes by; then on the bank, the butterfly
  shots.summer = async () => {
    await q(() => window.__wind.startChapter(2)); await ff(2.5);
    const s = await q(() => { const w = window.__wind, t = w.targets[1], z = t.pos.z; return { z, x: w.riverX(z), up: w.riverX(z + 30), WATER: w.WATER, off: t.pos.x - w.riverX(z) }; });
    const bx = s.x + s.off, bz = s.z, Y = s.WATER;
    const pf = path([[bx + 30, Y + 5, bz + 30], [bx + 8, Y + 3, bz + 6], [bx, Y + 3, bz], [bx - 10, Y + 5, bz - 14], [bx - 18, Y + 12, bz - 40]]);
    for (let i = 0; i < 4.2 * FPS; i++) { const t = i / FPS, u = Math.min(1, t / 3.4);
      const bp = await q(() => { const p0 = window.__wind.targets[1].pos; return [p0.x, p0.y, p0.z]; });
      await shoot({ wind: windAt(pf, u), cam: [[bx - 16, Y + 2.4, bz + 14], [bp[0], Y + 2.5, bp[2] - 4]], season: seasonCard('夏至', t, 7.2) }); }
    const c = await q(() => { const g = window.__wind.chaser.position; return [g.x, g.y, g.z]; });
    for (let i = 0; i < 3 * FPS; i++) { const t = i / FPS + 4.2;
      const g = await q(() => { const g = window.__wind.chaser.position; return [g.x, g.y, g.z]; });
      await shoot({ cam: [[c[0] - 6.5, c[1] + 1.6, c[2] - 3.5], [g[0], g[1] + 0.9, g[2]]], wind: [c[0], c[1] + 300, c[2], 0, 0], season: seasonCard('夏至', t, 7.2) }); }
  };

  // —— 8 · 秋分: through the threshing floor, and the chaff goes up gold
  shots.autumn = async () => {
    await q(() => window.__wind.startChapter(3)); await ff(2.5);
    const t0 = await q(() => { const p0 = window.__wind.targets[0].pos; return [p0.x, p0.y, p0.z]; });
    const [x, y, z] = t0;
    const pf = path([[x - 40, y + 6, z + 18], [x - 14, y + 3, z + 6], [x, y + 1, z], [x + 16, y + 6, z - 6], [x + 40, y + 16, z - 16]]);
    for (let i = 0; i < 4.2 * FPS; i++) { const t = i / FPS, u = Math.min(1, t / 3);
      await shoot({ wind: windAt(pf, u), cam: [[x - 2, y + 2.5, z + 24], [x + 4 * ease(Math.min(1, t / 4)), y + 2 + 3 * ease(Math.min(1, t / 4)), z - 2]], season: seasonCard('秋分', t, 4.2) }); }
  };

  // —— 9 · 冬至: one lantern lifts off the snow; then the whole village's
  shots.winter = async () => {
    await q(() => window.__wind.startChapter(4)); await ff(3);
    const t0 = await q(() => { const w = window.__wind, p0 = w.targets[0].pos; return [p0.x, p0.y, p0.z]; });
    const [x, y, z] = t0;
    const pf = path([[x - 30, y + 4, z + 22], [x - 10, y + 2, z + 8], [x, y + 1, z], [x + 4, y + 10, z - 4], [x + 6, y + 30, z - 8]]);
    for (let i = 0; i < 4.2 * FPS; i++) { const t = i / FPS, u = Math.min(1, t / 3.6);
      const lp = await q(() => { const p0 = window.__wind.targets[0].pos; return [p0.x, p0.y, p0.z]; }); // the lantern itself, as it rises
      const look = [lp[0], lp[1] + 0.5, lp[2]];
      await shoot({ wind: windAt(pf, u), cam: [[x - 9, y + 1.2, z + 10], look], season: seasonCard('冬至', t, 4.2) }); }
    // every lantern in the village goes up; a wide, slow push in over the valley
    await q(() => { const w = window.__wind; for (const t of w.targets) { if (t.done) continue; w.player.pos.copy(t.pos); for (let i = 0; i < 40 && !t.done; i++) w.step(1 / 24); } });
    await ff(4.5);
    const v = await q(() => { const w = window.__wind, F = w.FAM, a = F.at(78, -78), b2 = F.at(52, -52); return { a: [a.x, Math.max(a.y, w.WATER) + 40, a.z], b: [b2.x, Math.max(b2.y, w.WATER) + 30, b2.z], at: [F.stool.x, F.stool.y + 24, F.stool.z + 10] }; });
    for (let i = 0; i < 7.5 * FPS; i++) { const t = i / FPS;
      await shoot({ cam: [mix(v.a, v.b, ease(t / 7.5)), v.at], wind: [v.a[0], v.a[1] + 300, v.a[2], 0, 0],
        sub: ['他说，风一来，春天就来了。', fade(t, 0.8, 2.0, 7.4)], black: Math.max(0, (t - 6.9) / 0.6) }); }
  };

  // —— 10 · the title
  shots.title = async () => { for (let i = 0; i < 5 * FPS; i++) { const t = i / FPS; await shoot({ dt: 0, black: 1, title: fade(t, 0.9, 0.3, 4.9) }); } };

  const order = ['open', 'prologue', 'spring', 'kites', 'summer', 'autumn', 'winter', 'title'];
  for (const name of order) {
    if (ONLY && name !== ONLY && !(ONLY === 'prologue' && name === 'open')) { if (name === 'prologue') { await p.click('#title'); await p.evaluate(() => { document.getElementById('title').style.display = 'none'; }); } continue; }
    const f0 = frame; const t0 = Date.now();
    await shots[name]();
    console.log(name, 'frames', f0, '-', frame - 1, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  console.log('total frames', frame, 'errors', JSON.stringify(errs));
  await b.close();
})();
