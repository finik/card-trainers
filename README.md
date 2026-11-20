# Card Trainers

A 3D-printed set of **cardistry trainers**: five solid packets that stack into one 17 mm deck. They're for practising cuts, pivots and packet flourishes without spilling, bending or wearing out real cards.

Each packet is a poker-size card, 3.4 mm thick. The front shows the 2 to 6 of diamonds. There are three backs: the FINIK FORGE logo, an all-over pattern of interlocking valknuts, or the logo set into that pattern. The designs are inlaid flush in a second and third colour, so the faces stay flat and the packets slide cleanly over each other.

<p align="center"><img src="images/hero.png" width="820" alt="The five trainers face-up, 2 to 6 of diamonds, then the logo, valknut-pattern and combined backs"></p>

## At a glance

| | |
|---|---|
| **Size** | 63.5 × 88.9 mm (poker size), 3.2 mm (1/8") corner radius |
| **Thickness** | 3.4 mm per packet, which is 17 layers at 0.2 mm. Five packets stack to 17 mm, the thickness of a new 54-card deck |
| **Colours** | 3: body black, back art red, pips gray. The combined back adds a 4th for the pattern around the logo. Each design is 3 layers (0.6 mm) deep |
| **Backs** | Logo (`trainers_logo.3mf`), valknut pattern (`trainers_tiles.3mf`), or logo in the pattern (`trainers_combo.3mf`) |
| **Printer** | Any multi-material printer. The plate is laid out for a 256 × 256 mm bed (Bambu X2D) |
| **Supports** | None |
| **Source** | One parametric Python script builds every card and writes the 3MF |

<p align="center"><img src="images/faces.png" width="900" alt="Card artwork: fronts 2 to 6 of diamonds, the logo, valknut-pattern and combined backs"></p>

The pattern back tiles upright and upside-down valknuts on a triangular grid, with an even 1 mm gap between neighbours. Where six of them meet, a solid six-pointed star fills the space between their cut-off corners. The grid is centred so the top and bottom rows end on whole valknuts, and the pattern is clipped on that same line on all four sides, leaving a plain border of about 3.4 mm. The combined back puts a 48 mm logo in the middle and clips the pattern 1 mm around it.

<p align="center"><img src="images/stack.png" width="420" alt="The five packets squared up into one deck"></p>

## Printing

Open `stl/trainers_logo.3mf`, `stl/trainers_tiles.3mf` or `stl/trainers_combo.3mf` in Bambu Studio. Each holds all five trainers on one plate. Each trainer is one object with three parts, with the filaments already assigned:

| Filament slot | Part | Colour |
|---|---|---|
| 1 | Body | Black |
| 2 | Back art | Red |
| 3 | Pips (front) | Gray |
| 4 | Pattern around the logo (`trainers_combo.3mf` only) | Your choice; gold in the renders |

Map the slots to your AMS spools and slice. The combined back uses four; to print it in three colours, set slot 4 to the same spool as slot 2. The files carry slot numbers, not colours, so any three colours work.

- **Layer height:** 0.2 mm, including the first layer, so each packet comes out exactly 17 layers thick.
- **Orientation:** pips up, as laid out. The logo prints mirrored against the build plate, so it reads correctly when you flip the card. A smooth plate gives a glossy back; a textured plate gives a matte, grippier back.
- **Colour changes:** on the logo and pattern backs, no layer uses more than two colours: the bottom 3 layers are black and red, and the top 3 are black and gray. On a two-nozzle printer like the X2D, that's a single filament swap per plate. The combined back's bottom 3 layers use three colours, so expect filament swaps on each of those layers.
- **Elephant's foot:** keep elephant's-foot compensation on (Bambu's default is 0.15 mm). A flared bottom edge would make the packets catch on each other.
- **Ironing:** leave it off, or test it on one card first. On a two-colour top it can smear the gray into the black.
- **Fine detail:** on the logo back, the thinnest strokes are the EST. and 2020 text, about 0.46 mm wide. That's one 0.4 mm nozzle line; check those layers in the slicer preview. On the pattern back, every red band is at least 0.93 mm wide and the black gaps are 0.7 mm or more.

## Customising

Everything is set by the constants at the top of `source/trainers.py`:

| Constant | Default | What it does |
|---|---|---|
| `CARD_W`, `CARD_H`, `CORNER_R` | 63.5, 88.9, 3.2 | Card size. Use 57 × 89 for bridge size |
| `LAYER`, `LAYERS` | 0.2, 17 | Packet thickness = `LAYER × LAYERS`. Measure your own deck and divide by 5 |
| `INK_LAYERS` | 3 | How deep each colour inlay goes |
| `RANKS` | 2 to 6 | Which cards to make, one packet each |
| `PIP`, `PIP_W`, `PIP_COL`, `PIP_ROW` | 13, 9.6, 14.5, 28 | Diamond size and spacing |
| `VARIANTS` | `"logo"`, `"tiles"`, `"combo"` | Which backs to export, one 3MF each. `"logo"` uses `art/finikforge_logo.svg`, `"tiles"` is the valknut pattern, `"combo"` is the logo inside the pattern, `"valknut"` is one large valknut |
| `LOGO_D`, `COMBO_LOGO_D` | 56, 48 | Logo diameter on the logo back and the combined back |
| `TILE_S`, `TILE_GAP`, `TILE_WEAVE` | 16, 1.0, 0.7 | Pattern: grid triangle size, gap between valknuts and stars, weave gap inside each valknut. The border follows from these |
| `FIL_BODY`, `FIL_LOGO`, `FIL_PIPS`, `FIL_PATTERN` | 1, 2, 3, 4 | Filament slots for each part (`FIL_PATTERN` is the combined back's pattern) |

To use your own artwork on the back, replace `art/finikforge_logo.svg`. Any SVG with filled paths works; it's scaled to `LOGO_D` and centred.

## Building

```bash
pip install -r requirements.txt
python3 source/trainers.py   # writes stl/trainers_<back>.3mf
python3 source/render.py     # writes images/
```

## License

- **Code** (`source/`): MIT, see [LICENSE](LICENSE).
- **Models and images** (`stl/`, `images/`): CC BY-SA 4.0, see [LICENSE-MODELS](LICENSE-MODELS).
- **FINIK FORGE logo:** not covered by either license; all rights reserved.
