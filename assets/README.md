# Brand assets

This directory contains the existing Tuxedo Fitness brand artwork.

| Asset | Current property | Planned use |
| --- | --- | --- |
| `icons/AthleticTuxedoCat.png` | RGB hero image | Optional landing-page or documentation hero after web optimization. |
| `icons/AthleticTuxedoCatEmblemWithBackground.png` | RGBA emblem | Primary emblem candidate. |
| `icons/AthleticTuxedoCatEmblemWithoutBackground.png` | RGB image with a visible checkerboard | Do not treat as transparent until a derivative is corrected. |

The MVP reuses these assets. It does not require a new logo. Generated web
derivatives must retain a reference to their source asset and must not replace
the original files.

The Sprint 1 shell uses `static/brand/tuxedo-fitness-emblem-128.png`, a 128px
RGBA derivative of `AthleticTuxedoCatEmblemWithBackground.png`.

Browser assets are kept under `static/js/`: HTMX is pinned at `2.0.10`, and
small delegated application scripts handle navigation, theme, mobile menu, and
busy states. Charts are server-rendered SVG and require no chart library.

Pinned asset hashes:

- HTMX: `71ea67185bfa8c98c39d31717c6fce5d852370fcdfd129db4543774d3145c0de`
