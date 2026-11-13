# Default design taste

The house taste print-kit ships with, drawn from its author's feedback on real prints. Quotes are
the author's words. The user's own `taste` list in `print-kit.json` wins wherever they disagree;
when the user corrects a design, suggest adding the rule there.

## Shape

- **Products, not boxes.** Curved stems, cups rounded to fit the rod, sculpted pods.
  "does the rest of the hook need to be so square and fugly"
- **The benchmark for refined is a good watch dock**: a low plinth (~15 mm), a tapered wedge
  backrest (17 → 11 mm; 14 → 9 on the iPhone dock), 8–14 mm top corner radii. Stands share
  this family look.
- **Crisp, not puffy.** Flat faces, ~1 mm edge breaks, radii in plan and front view only. Hull-of-spheres
  edges look like a balloon.
- **Functional faces are flat planes**, tilted if needed, never domed. Soften only their corners.
  "keep the face part flat"
- **No lips, steps or ledges where surfaces meet.** A straight transition edge to edge, or a plain
  fillet. "now theres a lip here"
- **Add-ons look native to the host**: blended into its surfaces, matching its edge language. If
  the host uses chamfers or small fillets, don't add big rounds.
  "nothing else on the keyboard is rounded like this"
- **Front faces are plain**, or carry a functional angled louver grille. No decorative flutes.
  Patterns run the wide way.
- **Cradle, don't trap.** An open sculpted seat the object slides in and out of, never a
  restrictive slot. A dock narrower than the case so the phone lifts straight out.
- **Round seats on round things**, so a rod or puck rests on flush curved faces, not square edges.
- **Lead-ins** wherever something slides on or in, so it can't catch.

## Layout

- **Centre features** on what they belong to: labels, lips, holes, cable exits. Off-centre reads
  as a mistake.
- **Line things up**: aligned bands, shared grid lines, pocket edges that line up. A ragged
  column with an empty patch reads as a mistake.
- **Size each pocket to its item**, pack items close, and don't fill leftover space with bigger
  pockets. "why is the box bigger"
- **Spend spare room on thicker walls.**
- **Fewer openings**: drop slots and windows nobody uses.
- **A bin family shares one wall style** (1.6 mm drawer-bin walls).
- **Plain when the object is plain**: kitchen bins needed no trace, scoops or styling.

## Solid and hidden

- **Solid, not hollow.** Fill the gaps between pockets and walls. Never hollow to save plastic.
  "ever heard of infill my guy? lol"
- **Hide cables and mechanics**: an internal duct, a hidden rear bulge, a buttress narrower and
  lower than the backrest. No visible notch for a cable end.
- **Cables leave through the middle of the back.**
- **Electronics mount positively**: boards snap into sockets, never sit loose.
- **Bottom lids cover the whole underside**, so feet and tape spread evenly.

## Labels

- **Engraved in the pocket floor**, centred under the object, visible when the tool is out. Not
  on the rim or a side lip.
- **Short and big**: "Needle", not "Draw Needle". Split a long word over two lines across the
  middle (THERMO / METER).
- 0.6 mm deep, Liberation Sans Bold, 6–10 mm tall. Keep ≥1.2 mm of floor under the text and the
  text ≥2 mm inside the flat floor, past the chamfer.

## Mounting

- **Wall-mounted parts sit flush**: no feet, adhesive in recessed pockets, as thin as possible.
- **Hardware-free slide-on or snap** when it's strong enough; the least material that works.
- **Scale hardware to the part**: M2, not M3, on small stands. Countersunk screws for lids that
  rarely open; inserts only where they open often. Design for screws the user owns
  (`data/hardware.json`).
- **Tape recesses keep square corners** (tape is cut square and rode up in rounded corners), and
  sit ~5 mm in from edges so the tape doesn't show.

## Holding things

- **Grab room.** Tools stand proud of the rim or get a scoop. Upright items (vials, bags) sit in
  shallow holders with a third to a half sticking out: **no scoops** needed for those.
- **Reach-through grab points** where the object allows, like joined scissor finger holes.
- **Pocket floors follow the object** so it sits level: deeper under fat ends, a pad under thin or
  angled sections. "I want the butt deeper and the shaft supported"
