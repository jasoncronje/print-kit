// print-kit calibration gauge: finds the gaps your printer needs for parts that fit.
// Print the plate and the key. Push the key's round end into the round holes and its square
// end into the square sockets, then tell Claude which ones fit (count the dots).
part = "assembly"; // [assembly, plate, gauge, key]

steps = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40]; // gap per side at each position: 1 dot to 6 dots
key_d = 8;      // key: round end diameter and square end width
key_end = 10;   // length of each end of the key
gauge_l = 80;   // plate length (caliper check, X)
gauge_w = 32;   // plate width (caliper check, Y)
gauge_t = 4;    // plate thickness (caliper check, Z)
pitch = 12.5;   // hole spacing
foot = 0.4;     // chamfer on every bed edge, so first-layer squish can't change a fit
$fn = 64;

n = len(steps);
x0 = (gauge_l - (n - 1) * pitch) / 2;
row_round = 8.5;
row_square = gauge_w - 8.5;
row_dots = gauge_w / 2;

// The key's cross-section, grown by `grow` per side. Square end has r 1 corners.
module profile(grow, square) {
    if (square) offset(r = 1 + grow) square(key_d - 2, center = true);
    else circle(d = key_d + 2 * grow);
}

// A through hole with its bed edge flared by `foot`.
module bore(grow, square) {
    translate([0, 0, -0.01]) linear_extrude(gauge_t + 0.02) profile(grow, square);
    hull() {
        translate([0, 0, -0.01]) linear_extrude(0.01) profile(grow + foot, square);
        translate([0, 0, foot]) linear_extrude(0.01) profile(grow, square);
    }
}

module gauge_outline() translate([gauge_l / 2, gauge_w / 2]) offset(r = 3) square([gauge_l - 6, gauge_w - 6], center = true);

// Dots like a die face: i + 1 of them, three per row.
module dots(count) {
    rows = ceil(count / 3);
    for (k = [0 : count - 1]) {
        in_row = (floor(k / 3) == rows - 1) ? count - 3 * (rows - 1) : 3;
        translate([((k % 3) - (in_row - 1) / 2) * 2.4, ((rows - 1) / 2 - floor(k / 3)) * 2.4, 0])
            cylinder(d = 1.6, h = 1, $fn = 20);
    }
}

module gauge() {
    difference() {
        hull() {
            linear_extrude(0.01) offset(delta = -foot) gauge_outline();
            translate([0, 0, foot]) linear_extrude(gauge_t - foot) gauge_outline();
        }
        for (i = [0 : n - 1]) {
            translate([x0 + i * pitch, row_round, 0]) bore(steps[i], false);
            translate([x0 + i * pitch, row_square, 0]) bore(steps[i], true);
            translate([x0 + i * pitch, row_dots, gauge_t - 0.6]) dots(i + 1);
        }
    }
}

// Square end on the bed, round end on top.
module key() {
    hull() {
        linear_extrude(0.01) profile(-foot, true);
        translate([0, 0, foot]) linear_extrude(key_end - foot) profile(0, true);
    }
    translate([0, 0, key_end]) {
        cylinder(d = key_d, h = key_end - foot);
        translate([0, 0, key_end - foot]) cylinder(d1 = key_d, d2 = key_d - 2 * foot, h = foot);
    }
}

if (part == "gauge" || part == "plate" || part == "assembly") gauge();
if (part == "key") key();
if (part == "plate") translate([gauge_l + 10, gauge_w / 2, 0]) key();
// Assembly: the key's round end sitting in the 4-dot round hole.
if (part == "assembly") translate([x0 + 3 * pitch, row_round, 2 * key_end]) rotate([180, 0, 0]) key();
