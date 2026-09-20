# Contributing

Thanks for wanting to add to the Pelton wallpaper set. This repo is art plus a
small script, so the bar is mostly about file layout and consistency.

## Folder layout

Every wallpaper lives in its own variant folder:

```
wallpapers/<platform>/<set>/<number>/<variant>/
```

- **platform** is `desktop` or `mobile`
- **set** is the design family, for example `night` or `plate`
- **number** separates designs inside a set, starting at `1`
- **variant** describes what is different, for example `default`,
  `no-marker`, `no-marker-no-compass`

A real example, with the PNG and JPEG files rendered by CI:

```
wallpapers/desktop/night/1/default/
  night-1-default.svg            <- you commit this
  night-1-default-3840x2160.png  <- generated
  night-1-default-3840x2160.jpg  <- generated
  night-1-default-2560x1440.png  <- generated
  ...
```

## File rules

**You commit one file per wallpaper: the master.** Every export is rendered
from it by [`scripts/render_exports.py`](./scripts/render_exports.py) when your
change lands on `main`, so you do not hand-export anything and every wallpaper
gets the same set of resolutions.

A master is one of two things.

**A vector master**, for anything drawn as vectors:

- Named `<set>-<number>-<variant>.svg`, no resolution in the name. A file in
  `desktop/night/1/no-marker/` is `night-1-no-marker.svg`.
- Its `viewBox` is the real design size, since everything is rendered at that
  aspect ratio. So 3840x2160 for a desktop design.
- Real drawing markup, not one embedded bitmap. If your art is a bitmap, ship
  it as a raster master instead of hiding it inside an SVG.

**A raster master**, for hand-drawn art, painting, photography and anything
else that has no meaningful vector form:

- Named `<set>-<number>-<variant>-master.png` or `-master.jpg`. The `-master`
  marker is what separates it from the generated exports, so it is required.
- PNG for drawn and scanned art, JPEG for photography.
- At least as wide as the largest target you want, since a raster master is
  never upscaled. A 2400px wide desktop master simply produces the 1920 export
  and skips 3840 and 2560.
- Keep it at the highest quality you have. It is the archive copy everything
  else is derived from.

Either way: exactly one master per variant folder, and lowercase letters,
digits and hyphens for every folder and file name.

Current render targets, from
[`scripts/render_exports.py`](./scripts/render_exports.py):

| Platform | Widths |
| --- | --- |
| `desktop` | 3840, 2560, 1920 |
| `mobile` | 1290, 1080 |

Committing your own exports is pointless: CI overwrites the ones it renders and
deletes every other PNG and JPEG in the folder. Your `-master` file is the
one raster file it never touches.

## Source files

Exports are what people download, but the editable project file is what keeps a
design alive. Dropping yours in `source/` alongside the existing Affinity file
is much appreciated, whatever you work in: Affinity, Figma, Illustrator, Inkscape
or anything else.

It is not required, and no submission is turned down for lacking one. It just
means the next person can adjust a design instead of rebuilding it from scratch.
Keep the file named after the set it belongs to, and leave out anything you
cannot relicense under CC BY 4.0, such as bought fonts or stock assets.

## Generated files

Three things are generated, and none of them should be hand-edited:

- the PNG and JPEG exports in every variant folder
- the gallery section of `README.md`, between the `<!-- gallery:start -->` and
  `<!-- gallery:end -->` markers
- `wallpapers.json`, a manifest of every wallpaper with its formats,
  resolutions and authors, for the app or a site to read

The Build workflow rewrites all three on every push to `main` and commits the
result. The prose around the gallery markers is yours to edit freely.

## Running it locally

```sh
python3 scripts/render_exports.py     # rasters from the SVGs
python3 scripts/generate_gallery.py   # README gallery and wallpapers.json
python3 scripts/check_svgs.py         # SVG safety rules
python3 scripts/check_structure.py    # layout and naming
```

The two checks need nothing but Python 3. Rendering needs `rsvg-convert` and
Pillow:

```sh
brew install librsvg && pip install pillow      # macOS
sudo apt-get install librsvg2-bin && pip install pillow   # Debian, Ubuntu
```

Authors are read from git, so run these in a real checkout with history. A new
platform folder shows up automatically, and an empty one renders as *Nothing
here yet.*

Both checks run on every pull request. Rendering and generating do not, since
`main` handles that for you.

## Attribution

The author shown under each wallpaper comes from the newest commit touching its
master file. The generated exports are ignored on purpose, since CI rewrites
those and would otherwise credit itself. If you are committing someone else's
art, credit them with a trailer and they will be listed first:

```
Co-authored-by: Their Name <their@email>
```

## Submission rules

**We do NOT accept:**

- Sexual, gory, shocking or otherwise not-safe-for-work imagery
- Hateful, harassing or discriminatory content, including slurs and hate
  symbols, whether obvious or hidden in the art
- Violence, self-harm, or anything glorifying either
- Drug, weapon or gambling themes
- Politically or religiously charged messaging
- Third-party logos, trademarks, characters or brands you do not own
- Real people's likenesses without their permission
- Hidden or disguised payloads: text you only see at certain zoom levels,
  steganography, tracking pixels, scripts or external references inside the
  SVG, QR codes, or links to anything outside the Pelton project
- Fully AI-generated art, see [below](#no-fully-ai-generated-art)

**We do accept:**

- Original artwork you made yourself, in any style
- Vector work, and hand-drawn art, painting or photography through a raster
  master
- New sets, and new variants of an existing set
- Reworks of existing wallpapers, as long as you keep the set recognisable
- Desktop and mobile wallpapers alike
- Editable source files, see [below](#source-files)

Keep SVGs to plain drawing markup. No `<script>`, no `<foreignObject>`, no
remote `href` fetches, no embedded fonts pulled off a CDN. Anything that makes
a network request or executes will be rejected on sight. The
[SVG check](./.github/workflows/checks.yml) enforces this on every pull
request, and you can run it yourself with `python3 scripts/check_svgs.py`.

## No fully AI-generated art

Fully AI-generated wallpapers are not accepted. Nothing where you wrote a
prompt and submitted what came back, and nothing traced or lightly retouched
on top of that output.

AI is fine as a tool inside your own work: upscaling, denoising, masking,
background removal, or generating a reference you then draw from yourself. The
line is authorship. The composition, the shapes and the final artwork have to
be yours. A vector master has to be a file you built rather than an auto-trace
of a generated raster, and a raster master has to be your own drawing, painting
or photograph rather than a generated image you cleaned up.

If any part of your submission used AI, say so in the pull request and explain
where. Undisclosed AI work found later gets removed.

## Licensing

By contributing you agree your work is released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), the same license as
the rest of this repo. Only submit art you made or have the rights to
relicense.
