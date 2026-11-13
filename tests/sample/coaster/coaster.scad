// Sample project for CI: a coaster with a stepped rim. Small and quick to render.
part = "assembly"; // [assembly, coaster, clash_none]

d = 90;       // outer diameter
h = 4;        // total height
floor_t = 2;  // floor under the recess
rim = 4;      // rim width
$fn = 64;

module coaster() {
    difference() {
        cylinder(d = d, h = h);
        translate([0, 0, floor_t]) cylinder(d = d - 2 * rim, h = h);
    }
}

if (part == "assembly" || part == "coaster") coaster();
if (part == "clash_none") intersection() { coaster(); translate([200, 0, 0]) cube(1); }
