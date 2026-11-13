// Gridfinity bin base, no library. Copy into a model and keep the numbers.
// Foot profile matches kennetek/gridfinity-rebuilt-openscad: 0.8 chamfer + 1.8 straight + 2.15 chamfer.
// Printed and checked on a dozen bins (print-kit author, Bambu P2S, PLA, 0.4 nozzle).

grid_x = 2;             // cells along X
grid_y = 1;             // cells along Y
height_units = 6;       // 7 mm each
outer_chamfer = 0.8;    // top outside edge break

/* [Hidden] */
$fn    = 64;
pitch  = 42;
cell   = 41.5;          // cell footprint (0.25 mm gap each side)
base_h = 4.75;          // standard base profile height
outer_r = 3.75;
bin_h  = height_units * 7;
bin_x  = grid_x * pitch - 0.5;
bin_y  = grid_y * pitch - 0.5;

module rrect2(x, y, r) {
    offset(r) square([x - 2 * r, y - 2 * r], center = true);
}

module rrect(x, y, r, h) {
    linear_extrude(h) rrect2(x, y, r);
}

// One Gridfinity foot: 0.8 chamfer, 1.8 straight, 2.15 chamfer.
module foot() {
    hull() {
        rrect(cell - 2 * 2.95, cell - 2 * 2.95, 0.8, 0.01);
        translate([0, 0, 0.8])  rrect(cell - 2 * 2.15, cell - 2 * 2.15, 1.6, 1.8);
        translate([0, 0, base_h - 0.01]) rrect(cell, cell, outer_r, 0.01);
    }
}

module body() {
    for (i = [0 : grid_x - 1], j = [0 : grid_y - 1])
        translate([(i - (grid_x - 1) / 2) * pitch, (j - (grid_y - 1) / 2) * pitch, 0])
            foot();
    // Both hull parts start at base_h so the feet stay exposed. A hull from z = 0 buries them.
    hull() {
        translate([0, 0, base_h]) rrect(bin_x, bin_y, outer_r, bin_h - base_h - outer_chamfer);
        translate([0, 0, base_h])
            rrect(bin_x - 2 * outer_chamfer, bin_y - 2 * outer_chamfer, outer_r - outer_chamfer, bin_h - base_h);
    }
}

body();
