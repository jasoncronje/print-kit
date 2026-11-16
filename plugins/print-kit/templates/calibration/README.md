# Calibration gauge

A plate with twelve holes and one key. It finds the gaps your printer needs, so later parts fit
the first time.

| Part | File | Qty | Print |
|---|---|---|---|
| Gauge plate | `stl/gauge.stl` | 1 | Flat, no supports |
| Key | `stl/key.stl` | 1 | Square end on the bed, no supports |

Print both with the nozzle, filament and settings you normally use. Then push the key's round
end into the round holes and its square end into the square sockets, and tell Claude which ones
fit. The dots count the position: 1 dot is the tightest, 6 dots the loosest.

Gaps per side: 0.05, 0.10, 0.15, 0.20, 0.30, 0.40 mm. With calipers you can also check the plate
(80 × 32 × 4 mm) and the key (8 mm).

Regenerate:

```bash
openscad -D 'part="gauge"' -o stl/gauge.stl calibration.scad
openscad -D 'part="key"' -o stl/key.stl calibration.scad
```
