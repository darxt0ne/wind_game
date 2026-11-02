"""Soundtrack for the 风物 trailer, synthesised to the cut — quiet and spacious.
Soft felt-piano-like tones on a D 宫 pentatonic, a low warm pad, a breath of wind, a few soft bells, a smooth hall.
usage: python3 music.py out.wav"""
import sys, wave, numpy as np
from numpy.fft import rfft, irfft

SR = 44100
DUR = 61.2
rng = np.random.default_rng(11)
out = np.zeros((int(SR * DUR) + SR * 8, 2))

# the cut (seconds), matching render.js at 24 fps
T = dict(prologue=2.0, ask=8.3, wait=12.5, dark=15.5, flight=17.3, pin=21.5, spring=24.8, kites=28.4,
         summer=33.0, autumn=40.2, lantern=44.4, line=50.6, black=55.5, title=56.1)

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

def lowpass(x, a):  # one-pole, a in (0,1): higher = darker
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc = a * acc + (1 - a) * x[i]; y[i] = acc
    return y

def soft(f, dur=4.0):
    """a felt-hammer tone: a few harmonics, the upper ones dying fast, a soft 12 ms attack"""
    n = int(SR * dur); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 0.9)
         + 0.28 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 2.2)
         + 0.08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 4.0)
         + 0.03 * np.sin(2 * np.pi * 4.01 * f * t) * np.exp(-t * 6.0))
    env = np.minimum(1, t / 0.012) * np.minimum(1, (dur - t) / 0.4)
    return s * env * 0.32

_c = {}
def tone(deg, octave=0, dur=4.0):
    k = (deg, octave, dur)
    if k not in _c: _c[k] = soft(note(deg, octave), dur)
    return _c[k]

def pad(freqs, dur, attack=3.0, release=3.0, gain=0.035):
    n = int(SR * dur); t = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        for det in (-0.08, 0.07):
            s += np.sin(2 * np.pi * f * (1 + det / 100) * t + rng.uniform(0, 6)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.09 * t + rng.uniform(0, 6)))
    env = np.clip(np.minimum(t / attack, (dur - t) / release), 0, 1) ** 1.5
    return s * env * gain / len(freqs)

def bell(f, dur=5.0, gain=0.08):  # soft: few partials, all fading quickly except the fundamental
    n = int(SR * dur); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 0.9) + 0.25 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3) + 0.08 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6)
    return s * np.minimum(1, t / 0.006) * gain

def breath(dur, curve, gain=0.05):
    """wind as a low breath, no hiss: heavily low-passed noise, slowly swelling"""
    x = rng.normal(0, 1, int(SR * dur))
    y = lowpass(lowpass(x, 0.993), 0.99); y /= np.abs(y).max() + 1e-9
    t = np.linspace(0, 1, len(y))
    return y * np.interp(t, np.linspace(0, 1, len(curve)), curve) * gain

# —— a breath of wind under the opening and the flight only
add(breath(26, [0, 0.8, 0.5, 0.4, 0.4, 0.3, 0.2, 0.7, 1.0, 0.6, 0.2, 0]), 0)
add(breath(13, [0, 0.3, 0.5, 0.5, 0.3, 0]), 44.0, 0, 0.7)

# —— prologue: a low pad and a few unhurried notes
add(pad([note(0, -1), note(3, -1)], T['dark'] - T['prologue'] + 2.5), T['prologue'])
for t, d, o, pan in [(3.2, 0, 0, -0.2), (5.4, 2, 0, 0.15), (7.6, 3, 0, -0.1), (10.0, 4, 0, 0.2), (12.6, 3, 0, -0.15), (14.2, 1, 0, 0.1)]:
    add(tone(d, o, 5), t, pan)
# the dark beat: a single soft high note
add(tone(5, 0, 5), T['dark'] + 0.35, 0, 0.7)

# —— the wind comes: a rising line, then a soft chord of bells as the pinwheel turns
t = T['flight'] + 0.4
for i, d in enumerate([0, 1, 2, 3, 4, 5, 6, 7]):
    add(tone(d, 0, 3), t, -0.3 + i * 0.08, 0.75)
    t += 0.62 * (0.9 ** i)
for k, d in enumerate([5, 7, 9]):
    add(bell(note(d, 1), 5, 0.06), T['pin'] + k * 0.09, -0.2 + 0.2 * k)
add(tone(5, 0, 5), T['pin'], 0, 0.8)
add(pad([note(0, -1), note(2, -1), note(4, -1)], T['lantern'] - T['pin'] + 3), T['pin'])

# —— the seasons: an unhurried melody, one note a beat, a low note every two bars; a soft bell at each cut
beat = 60 / 76
mel = [5, 7, 8, 7, 5, 4, 3, None, 4, 5, 7, 8, 7, None, 5, 4, 5, 7, 8, 9, 8, 7, None, 5, 7, 5, 4, 3, 4, None]
t = T['spring'] + 0.2; i = 0
while t < T['lantern'] - 0.5:
    d = mel[i % len(mel)]
    if d is not None: add(tone(d, 0, 3.5), t, 0.15 * np.sin(i * 0.9), 0.85)
    if i % 8 == 0: add(tone([0, 3, 1, 3][(i // 8) % 4], -1, 5), t, 0, 0.7)
    t += beat; i += 1
for c in ['kites', 'summer', 'autumn']:
    add(bell(note(9, 0), 3, 0.035), T[c], 0.3)

# —— winter: the melody stops; a wider pad, slow high notes
add(pad([note(0, -1), note(3, -1), note(5, -1)], T['title'] - T['lantern'] + 2, attack=2.5, release=2.0, gain=0.045), T['lantern'])
for t, d, pan in [(44.8, 7, -0.15), (47.0, 9, 0.15), (49.0, 8, -0.1), (51.0, 7, 0.1), (52.6, 5, -0.1), (54.2, 4, 0.05)]:
    add(tone(d, 0, 5), t, pan, 0.8)
add(bell(note(5, 1), 5, 0.04), 51.0, 0.2)

# —— the title: one low note and the open fifth, ringing out
add(tone(0, -1, 6), T['title'] + 0.4, -0.15, 0.9); add(tone(3, -1, 6), T['title'] + 0.43, 0.15, 0.7)
add(tone(0, 0, 6), T['title'] + 0.46, 0, 0.6)

# —— a smooth hall: a dark, decaying tail
ir_n = int(SR * 3.0); tt = np.arange(ir_n) / SR
ir = np.stack([lowpass(rng.normal(0, 1, ir_n), 0.6) for _ in range(2)], 1) * np.exp(-tt * 2.2)[:, None]
ir[:int(SR * 0.015)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
N = 1 << int(np.ceil(np.log2(len(out) + ir_n)))
wet = np.stack([irfft(rfft(out[:, c], N) * rfft(ir[:, c], N), N)[:len(out)] for c in range(2)], 1)
mix = (out * 0.75 + wet * 0.5)[:int(SR * DUR)]
fade = int(SR * 2.0); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix[:int(SR * 0.05)] *= np.linspace(0, 1, int(SR * 0.05))[:, None]
mix /= np.abs(mix).max() / 0.8
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', sys.argv[1])
