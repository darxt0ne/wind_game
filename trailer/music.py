"""Score for the 风物 trailer: quiet, warm, and toward the end a little fated.
A synthesised piano over a soft string section, with real harmony:
  prologue    D major, Dmaj9 / Gmaj7 rocking, a few melody notes — calm, at home
  the dark    a held Gmaj7 in the strings, one high note — something waiting
  the wind    an arpeggio climbing over Asus4, resolving to D as the pinwheel turns — warmth, release
  seasons     D  A/C#  Bm7  Gmaj7  Em7  Asus4–A, a falling bass and a singing line — the year going by
  winter      Bm(add9)  Gmaj7  D/F#  Em7  Asus4, the cello stepping down — the turn, inevitability
  title       left on Asus4, then an open D fifth, the third arriving last — settled, but not quite
usage: python3 music.py out.wav"""
import sys, wave, numpy as np
from numpy.fft import rfft, irfft
from scipy.signal import lfilter, butter

SR = 44100
DUR = 61.2
rng = np.random.default_rng(5)
out = np.zeros((int(SR * DUR) + SR * 8, 2))
m2f = lambda m: 440.0 * 2 ** ((m - 69) / 12)

def add(sig, t, pan=0.0, gain=1.0):
    i = int(round(t * SR)); n = min(len(sig), len(out) - i)
    if n <= 0 or i < 0: return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:i + n, 0] += sig[:n] * gain * l * 1.41
    out[i:i + n, 1] += sig[:n] * gain * r * 1.41

# ---------------------------------------------------------------- instruments
_pc = {}
def piano(m, vel=0.6, ring=4.0):
    """additive piano: slightly stretched partials, upper ones dying faster, brighter when struck harder"""
    key = (m, round(vel, 2), round(ring, 1))
    if key in _pc: return _pc[key]
    f = m2f(m); n = int(SR * (ring + 1.2)); t = np.arange(n) / SR
    s = np.zeros(n); B = 0.00035
    base = 0.55 + 0.012 * (m - 48)             # higher notes die sooner
    for k in range(1, 11):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > SR / 2.2: break
        amp = (1 / k ** 1.35) * (vel ** (0.6 * (k - 1) / 3 + 0.4)) * (1 + 0.3 * (k == 2))
        s += amp * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6)) * np.exp(-t * base * (1 + 0.55 * (k - 1)))
    # two strings a hair apart: a slow beating that makes it sound like an instrument rather than a tone
    s *= 1 + 0.08 * np.sin(2 * np.pi * 0.7 * t)
    env = np.minimum(1, t / 0.004) * np.clip((ring + 1.0 - t) / 1.0, 0, 1)   # pedal up after `ring`
    _pc[key] = s * env * vel * 0.22
    return _pc[key]

def strings(ms, dur, attack=1.4, release=1.8, bright=6.0, gain=0.05):
    """a soft section: detuned sawtooth voices (built from harmonics), gentle vibrato, slow swell"""
    n = int(SR * (dur + release)); t = np.arange(n) / SR; s = np.zeros(n)
    vib = 1 + 0.0022 * np.sin(2 * np.pi * 5.1 * t) * np.minimum(1, t / 1.2)
    for m in ms:
        f = m2f(m)
        for det in (-7, -2, 3, 8):
            fv = f * 2 ** (det / 1200); ph = 2 * np.pi * np.cumsum(fv * vib) / SR + rng.uniform(0, 6)
            for k in range(1, 16):
                if k * fv > 9000: break
                s += np.sin(k * ph) * (1 / k) * np.exp(-k / bright)
    env = np.clip(np.minimum(t / attack, 1) * np.clip((dur + release - t) / release, 0, 1), 0, 1) ** 1.6
    return s * env * gain / (len(ms) * 4)

def bell(m, dur=5.0, gain=0.05):
    f = m2f(m); n = int(SR * dur); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 0.8) + 0.2 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 2.5) + 0.06 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 5)
    return s * np.minimum(1, t / 0.005) * gain

def breath(dur, curve, gain=0.035):
    x = rng.normal(0, 1, int(SR * dur)); b, a = butter(2, 380 / (SR / 2)); y = lfilter(b, a, x); y /= np.abs(y).max()
    tt = np.linspace(0, 1, len(y)); return y * np.interp(tt, np.linspace(0, 1, len(curve)), curve) * gain

# ---------------------------------------------------------------- harmony
# each chord: bass, left hand, right-hand chord tones (MIDI)
CH = {
    'Dmaj9':  (38, [50, 57], [66, 69, 73, 76]),
    'Gmaj7/D': (38, [50, 59], [66, 67, 71, 74]),
    'Gmaj7':  (43, [50, 55], [66, 71, 74]),
    'Asus4':  (45, [52, 57], [62, 64, 69]),
    'A':      (45, [52, 57], [61, 64, 69]),
    'D':      (38, [50, 57], [62, 66, 69, 74]),
    'A/C#':   (37, [49, 57], [64, 69, 73]),
    'Bm7':    (35, [47, 54], [62, 66, 69]),
    'Em7':    (40, [52, 59], [62, 67, 71]),
    'Bm9':    (35, [47, 54], [66, 71, 73, 74]),
    'D/F#':   (42, [50, 57], [62, 69, 74]),
}
def arpeggio(ch, t0, bar, beats=4, vel=0.42, pattern=(0, 1, 2, 3, 2, 1, 2, 3), ring=None, sub=2):
    """the bass on the downbeat, then the chord broken in eighths across both hands, pedal held for the bar"""
    b, lh, rh = CH[ch]; tones = lh + rh; step = bar / beats / sub; ring = ring or bar + 0.6
    add(piano(b, vel * 0.95, ring), t0, -0.25)
    for i in range(beats * sub):
        m = tones[pattern[i % len(pattern)] % len(tones)] if i else lh[0]
        add(piano(m, vel * (0.85 if i % 2 else 1.0), ring - i * step), t0 + i * step + rng.normal(0, 0.004), -0.15 + 0.3 * (m - 50) / 30)
def pad(ch, t0, dur, gain=0.05, octave=0, bright=6.0, attack=1.4):
    b, lh, rh = CH[ch]
    add(strings([x + 12 * octave for x in lh[:1] + rh[:3]], dur, attack=attack, bright=bright, gain=gain), t0, 0)
def melody(notes, t0, beat, vel=0.55, pan=0.12):
    tt = t0
    for m, d in notes:
        if m: add(piano(m, vel, d * beat + 1.2), tt + rng.normal(0, 0.006), pan)
        tt += d * beat

# ---------------------------------------------------------------- the cut (seconds, matching render.js)
T = dict(prologue=2.0, dark=15.5, flight=17.3, pin=21.5, spring=24.8, lantern=44.4, line=50.6, black=55.5, title=56.1)

# opening: a breath, then one high note out of the silence
add(breath(26, [0, 0.7, 0.4, 0.3, 0.3, 0.2, 0.15, 0.6, 1.0, 0.5, 0.2, 0]), 0)
add(piano(78, 0.35, 4), 0.9, 0.2)

# prologue — 66 bpm, rocking between home and the fourth
bar = 4 * 60 / 66; beat = bar / 4
for i, ch in enumerate(['Dmaj9', 'Gmaj7/D', 'Dmaj9', 'Gmaj7/D']):
    arpeggio(ch, T['prologue'] + i * bar, bar, vel=0.36 if i == 0 else 0.4, pattern=(0, 2, 3, 4, 5, 4, 3, 2))
    pad(ch, T['prologue'] + i * bar, bar + 0.4, gain=0.022 + 0.006 * i)
melody([(None, 4), (78, 1.5), (76, 0.5), (74, 2), (73, 1), (74, 1), (76, 2), (69, 3)], T['prologue'], beat, vel=0.5)

# the dark — strings hold Gmaj7, one high B, waiting
pad('Gmaj7', T['dark'] - 0.3, 2.2, gain=0.045, attack=0.8)
add(piano(83, 0.3, 3), T['dark'] + 0.4, 0.3)

# the wind — an arpeggio climbing over Asus4, faster and faster, strings swelling
seq = [57, 62, 64, 69, 74, 76, 81, 86, 88, 93]
tt = T['flight'] + 0.25
for i, m in enumerate(seq):
    add(piano(m, 0.32 + 0.035 * i, 2.5), tt, -0.4 + 0.08 * i); tt += 0.5 * 0.86 ** i
add(strings([45, 57, 62, 64, 69], T['pin'] - T['flight'] + 0.4, attack=3.2, bright=7, gain=0.07), T['flight'], 0)
# …and home: D major as the pinwheel turns, warm and full
add(piano(26, 0.5, 4), T['pin'], -0.2); add(piano(38, 0.55, 4), T['pin'], -0.2)
for m in [57, 62, 66, 69, 74, 78]: add(piano(m, 0.5, 3.6), T['pin'] + 0.012 * (m - 57) / 3, 0.1)
for k, m in enumerate([86, 90, 93]): add(bell(m, 4, 0.03), T['pin'] + 0.08 * k, -0.2 + 0.2 * k)
add(strings([38, 50, 57, 66, 69], 3.6, attack=0.6, bright=7, gain=0.075), T['pin'], 0)
melody([(78, 1), (81, 1), (83, 1.5), (81, 0.5), (78, 2)], T['pin'] + 0.9, 60 / 76, vel=0.5)

# the seasons — 76 bpm, the bass walking down, the line singing over it
bar = 4 * 60 / 76; beat = bar / 4; t0 = T['spring']
prog = ['D', 'A/C#', 'Bm7', 'Gmaj7', 'Em7', 'Asus4']
for i, ch in enumerate(prog):
    arpeggio(ch, t0 + i * bar, bar, vel=0.4, pattern=(0, 2, 3, 4, 3, 2, 4, 3))
    pad(ch, t0 + i * bar, bar + 0.3, gain=0.04 + 0.004 * i, bright=6.5)
add(piano(61, 0.4, 2), t0 + 5.5 * bar, 0.1)  # Asus4 → A, the C# lands on the last half bar
melody([(81, 1), (78, 1), (76, 0.5), (74, 0.5), (76, 1),
        (73, 1.5), (76, 0.5), (81, 2),
        (83, 1), (81, 1), (78, 1), (74, 1),
        (74, 1.5), (76, 0.5), (78, 1), (79, 1),
        (76, 1), (79, 1), (83, 1.5), (81, 0.5),
        (81, 2), (76, 1), (73, 1)], t0, beat, vel=0.56)
# a cello under the second half, carrying the falling line
for i, m in enumerate([47, 43, 40, 45]):
    add(strings([m], bar + 0.2, attack=0.9, bright=8, gain=0.06), t0 + (2 + i) * bar, -0.2)

# winter — 60 bpm, B minor; the cello steps down B G F# E A; slow, high, sparse notes above
t0 = T['lantern']
plan = [('Bm9', 4.0, 47), ('Gmaj7', 2.2, 43), ('D/F#', 2.0, 42), ('Em7', 2.0, 40), ('Asus4', 1.5, 45)]
tt = t0
for i, (ch, d, cello) in enumerate(plan):
    arpeggio(ch, tt, d, beats=max(2, round(d)), vel=0.34 + 0.02 * i, pattern=(0, 2, 3, 2), sub=1, ring=d + 0.8)
    pad(ch, tt, d + 0.2, gain=0.05 + 0.012 * i, bright=6, attack=1.0 if i else 1.8)
    add(strings([cello], d + 0.3, attack=0.7, bright=8, gain=0.075 + 0.01 * i), tt, -0.2)
    tt += d
melody([(78, 2), (74, 1), (73, 1),        # Bm9
        (71, 2.2),                        # Gmaj7
        (81, 1), (78, 1),                 # D/F#  — 他说，风一来，
        (79, 1), (78, 0.5), (76, 0.5),    # Em7   — 春天就来了。
        (74, 1.5)], t0, 1.0, vel=0.48)    # Asus4 — left hanging

# the title — the Asus4 still in the air; then a low open fifth on D, and the third, last and quiet
add(strings([45, 57, 62, 64, 69], 2.0, attack=0.2, bright=6, gain=0.05), T['black'], 0)
add(piano(26, 0.5, 5.5), T['title'] + 0.35, -0.1); add(piano(38, 0.5, 5.5), T['title'] + 0.35, -0.1)
add(piano(45, 0.42, 5.5), T['title'] + 0.37, 0.1); add(piano(50, 0.38, 5.5), T['title'] + 0.39, 0.0)
add(strings([38, 45, 50, 57], 4.5, attack=1.2, bright=5, gain=0.05), T['title'] + 0.35, 0)
add(piano(66, 0.3, 4.5), T['title'] + 2.1, 0.2)       # F#: the major third, arriving late
add(piano(76, 0.24, 3.5), T['title'] + 3.0, 0.25)     # and an E above it, unresolved, fading

# ---------------------------------------------------------------- a warm hall
ir_n = int(SR * 3.6); tt_ = np.arange(ir_n) / SR
b_, a_ = butter(1, 3200 / (SR / 2))
ir = np.stack([lfilter(b_, a_, rng.normal(0, 1, ir_n)) for _ in range(2)], 1) * np.exp(-tt_ * 1.7)[:, None]
ir[:int(SR * 0.02)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
N = 1 << int(np.ceil(np.log2(len(out) + ir_n)))
wet = np.stack([irfft(rfft(out[:, c], N) * rfft(ir[:, c], N), N)[:len(out)] for c in range(2)], 1)
mix = (out * 0.72 + wet * 0.55)[:int(SR * DUR)]
# a touch of warmth: roll off the very top
b2, a2 = butter(2, 9000 / (SR / 2)); mix = lfilter(b2, a2, mix, axis=0)
fade = int(SR * 2.2); mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
mix /= np.abs(mix).max() / 0.85
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', sys.argv[1])
