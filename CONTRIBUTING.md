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

**The SVG is the only file you need to commit.** Everything else is rendered
from it by [`scripts/render_exports.py`](./scripts/render_exports.py) when your
change lands on `main`, so you do not hand-export anything and every wallpaper
gets the same set of resolutions.

- Name the SVG `<set>-<number>-<variant>.svg`, with no resolution in the name.
  A file in `desktop/night/1/no-marker/` is `night-1-no-marker.svg`.
- Exactly one SVG per variant folder.
- Set the `viewBox` to the real design size. Everything is rendered at that
  aspect ratio, so 3840x2160 for a desktop design.
- Keep the SVG editable rather than a single embedded bitmap. That is the whole
  point of shipping it.
- Lowercase letters, digits and hyphens for every folder and file name.

Current render targets, from
[`scripts/render_exports.py`](./scripts/render_exports.py):

| Platform | Widths |
| --- | --- |
| `desktop` | 3840, 2560, 1920 |
| `mobile` | 1290, 1080 |

Committing your own PNG or JPEG is allowed but pointless: CI overwrites the
ones it renders and deletes the rest.

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
files. If you are committing someone else's art, credit them with a trailer and
they will be listed first:

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
- New sets, and new variants of an existing set
- Reworks of existing wallpapers, as long as you keep the set recognisable
- Desktop and mobile exports, including resolutions we do not cover yet
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
be yours, and the SVG has to be a real vector file you built rather than an
auto-trace of a generated raster.

If any part of your submission used AI, say so in the pull request and explain
where. Undisclosed AI work found later gets removed.

## Licensing

By contributing you agree your work is released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), the same license as
the rest of this repo. Only submit art you made or have the rights to
relicense.
