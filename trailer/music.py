"""Soundtrack for the 风物 trailer, synthesised to the cut.
Plucked string (Karplus-Strong, guzheng-like) on a D 宫 pentatonic, a soft pad, wind, bells, a reverb.
usage: python3 music.py out.wav"""
import sys, numpy as np

SR = 44100
DUR = 61.2
rng = np.random.default_rng(7)
out = np.zeros((int(SR * DUR) + SR * 6, 2))

# the cut (seconds), matching render.js at 24 fps
T = dict(prologue=2.0, ask=8.3, wait=12.5, dark=15.5, flight=17.3, pin=21.5, spring=24.8, kites=28.4,
         summer=33.0, autumn=40.2, lantern=44.4, wide=48.6, line=50.6, black=55.5, title=56.1)

D = 146.83  # D3
SCALE = [0, 2, 4, 7, 9]  # 宫 商 角 徵 羽
def note(deg, octave=0):
    o, d = divmod(deg, 5)
    return D * 2 ** ((SCALE[d] + 12 * (o + octave)) / 12)

def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR); n = min(len(sig), len(out) - i)
    if n <= 0: return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:i + n, 0] += sig[:n] * gain * l * 1.41
    out[i:i + n, 1] += sig[:n] * gain * r * 1.41

def pluck(f, dur=3.5, bright=0.5):
    n = int(SR * dur); p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p) * np.hanning(p) ** 0.3
    y = np.zeros(n); y[:p] = buf
    damp = 0.996 - 0.004 * (1 - bright)
    for i in range(p, n):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p + 1 if i - p + 1 < i else i - p])
    # a little pitch bend down at the start, the way a 古筝 string is pressed
    env = np.exp(-np.arange(n) / (SR * dur * 0.35))
    return y * env * 0.5

_pl = {}
def pl(deg, octave=0, dur=3.5, bright=0.5):
    k = (deg, octave, dur, bright)
    if k not in _pl: _pl[k] = pluck(note(deg, octave), dur, bright)
    return _pl[k]

def pad(freqs, dur, attack=2.0, release=2.5, gain=0.06):
    n = int(SR * dur); t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):  # slightly detuned, slowly breathing
            s += np.sin(2 * np.pi * f * (1 + det / 100) * t + rng.uniform(0, 6)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t + rng.uniform(0, 6)))
            s += 0.25 * np.sin(2 * np.pi * 2 * f * t) * 0.5
    env = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / release)
    return s * np.clip(env, 0, 1) * gain / len(freqs)

def bell(f, dur=4.0, gain=0.25):
    n = int(SR * dur); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) for m, a, d in [(1, 1, 1.2), (2.76, 0.45, 2.4), (5.4, 0.22, 4.0), (8.93, 0.1, 6)])
    return s * np.minimum(1, t / 0.003) * gain

def wind(dur, curve, gain=0.12):
    n = int(SR * dur); x = rng.normal(0, 1, n)
    # band-limited, moving noise: a leaky integrator for body, its slope for hiss
    lo = np.zeros(n); a = 0.985
    for i in range(1, n): lo[i] = a * lo[i - 1] + (1 - a) * x[i]
    lo /= np.abs(lo).max() + 1e-9
    hi = np.diff(lo, prepend=0); hi /= np.abs(hi).max() + 1e-9
    t = np.arange(n) / dur / SR
    g = np.interp(t, np.linspace(0, 1, len(curve)), curve)
    gust = 0.7 + 0.3 * np.sin(2 * np.pi * 0.21 * np.arange(n) / SR)
    return (lo * 0.8 + hi * 0.25) * g * gust * gain

def thump(f=55, dur=1.2, gain=0.35):
    n = int(SR * dur); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t * (1 + 0.6 * np.exp(-t * 18))) * np.exp(-t * 5) * gain

# —— wind under everything, rising for the flight, falling away for the title
add(wind(DUR, [0, 0.9, 0.5, 0.5, 0.45, 0.2, 1.3, 1.0, 0.7, 0.7, 0.7, 0.6, 0.6, 0.45, 0.4, 0.15, 0]), 0, 0, 0.9)

# —— prologue: a low drone, a few plucks like someone tuning, unhurried
add(pad([note(0, -1), note(3, -1)], T['dark'] - T['prologue'] + 1.5, attack=3), T['prologue'], 0, 1.0)
for t, d, o, pan in [(3.0, 0, 0, -0.3), (4.6, 3, 0, 0.2), (6.4, 2, 0, -0.1), (8.6, 4, 0, 0.3), (10.3, 3, 0, -0.2), (11.4, 1, 1, 0.1),
                     (12.9, 0, 1, 0.0), (14.0, 4, 0, -0.3)]:
    add(pl(d, o), t, pan, 0.55)
# the dark beat: one bell, and almost nothing else
add(bell(note(0, 1), 5, 0.11), T['dark'] + 0.25, 0.1)

# —— the wind comes: plucks climb faster and faster to the pinwheel, then the chime
seq = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
t = T['flight'] + 0.3
for i, d in enumerate(seq):
    add(pl(d, 0, 2.5, 0.7), t, -0.5 + i * 0.1, 0.55 + 0.04 * i)
    t += 0.55 * (0.88 ** i)
for k, d in enumerate([5, 7, 9, 10]):
    add(bell(note(d, 1), 4.5, 0.16), T['pin'] + k * 0.07, -0.3 + 0.2 * k)
add(pad([note(0, -1), note(2, -1), note(4, -1)], T['lantern'] - T['pin'] + 2, attack=1.5, gain=0.07), T['pin'], 0)

# —— the seasons: a steady pulse and a melody over it, a low hit at each cut
bpm = 96; beat = 60 / bpm
mel = [5, 7, 8, 7, 5, 4, 3, 4, 5, 7, 9, 8, 7, 5, 4, 5, 7, 8, 9, 10, 9, 7, 8, 7, 5, 4, 5, 3, 4, 5]
pulse = [0, 3, 1, 3]
t = T['spring']; i = 0
while t < T['lantern'] - 0.3:
    add(pl(pulse[i % 4], -1, 1.6, 0.4), t, 0.25 if i % 2 else -0.25, 0.7)
    if i % 2 == 0: add(pl(mel[(i // 2) % len(mel)], 0, 2.8, 0.65), t + 0.01, -0.1, 1.0)
    t += beat / 2 * 2; i += 1
for c in ['spring', 'kites', 'summer', 'autumn']:
    add(thump(), T[c], 0, 0.9)
    add(bell(note(9, 0), 2.5, 0.07), T[c] + 0.02, 0.4)

# —— winter: the pulse stops; slow bells over a wide pad
add(pad([note(0, -1), note(3, -1), note(5, -1), note(7, -1)], T['title'] - T['lantern'] + 1.5, attack=2.5, release=2.0, gain=0.08), T['lantern'], 0)
for t, d, pan in [(44.6, 7, -0.2), (46.2, 9, 0.2), (47.8, 8, -0.1), (49.4, 7, 0.1), (50.8, 5, -0.2), (52.0, 7, 0.2), (53.1, 4, 0), (54.4, 5, 0)]:
    add(bell(note(d, 0), 5, 0.14), t, pan)
    add(pl(d, 0, 4, 0.5), t + 0.02, pan, 0.45)

# —— the title: one low bell and the open fifth, ringing out
add(bell(note(0, -1), 7, 0.3), T['title'] + 0.3, 0)
add(pl(0, -1, 6, 0.5), T['title'] + 0.3, -0.3, 0.7); add(pl(3, -1, 6, 0.5), T['title'] + 0.32, 0.3, 0.6)
add(pl(0, 0, 6, 0.5), T['title'] + 0.34, 0, 0.5)

# —— a hall: convolve with a decaying noise tail, mixed under the dry sound
ir_n = int(SR * 3.2); tt = np.arange(ir_n) / SR
ir = rng.normal(0, 1, (ir_n, 2)) * np.exp(-tt * 1.9)[:, None]; ir[:int(SR * 0.012)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
from numpy.fft import rfft, irfft
N = 1 << int(np.ceil(np.log2(len(out) + ir_n)))
wet = np.stack([irfft(rfft(out[:, c], N) * rfft(ir[:, c], N), N)[:len(out)] for c in range(2)], 1)
mix = out * 0.8 + wet * 0.55
mix = mix[:int(SR * DUR)]
fade = int(SR * 1.5); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix /= np.abs(mix).max() / 0.89
import wave
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', sys.argv[1], f'{DUR}s')
