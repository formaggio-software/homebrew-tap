# Formaggio Software Homebrew tap

Homebrew distribution for [rhtop](https://github.com/formaggio-software/rhtop),
the read-only Robinhood terminal dashboard from Formaggio LLC.
Product, subscription, and licensing information: [rhtop.dev](https://rhtop.dev).

## Install

```sh
brew tap formaggio-software/tap
brew install formaggio-software/tap/rhtop
rhtop --demo
```

Upgrade with `brew update` then `brew upgrade formaggio-software/tap/rhtop`.
Remove with `brew uninstall rhtop`.

## Maintainers

Generate the formula using three genuine release archives:

```sh
python3 -m venv .venv
.venv/bin/python scripts/update_formula.py v0.1.0 --assets-dir /path/to/release-assets
```

The generator validates archives and calculates SHA-256 values locally for
one universal2 macOS archive and Linux arm64/amd64 archives. The Mac archive must
contain both Intel and ARM Mach-O slices; relabelled Intel files are rejected.
Keep `scripts/macho.py` with the generator. Publish the exact archives on the matching
`formaggio-software/rhtop` GitHub Release before publishing the formula.
Use checksums calculated from the exact published archives.

Run `brew audit --strict formaggio-software/tap/rhtop`, install, and run
`brew test formaggio-software/tap/rhtop` on supported native platforms.
The formula installs the executable and proprietary/third-party notices.
For licensing information and support, visit [rhtop.dev](https://rhtop.dev) or
email [contact@formaggio.software](mailto:contact@formaggio.software).

## Binary-use license

Installation does not grant unpaid use or redistribution rights. Review the
[complete binary-use license](https://rhtop.dev/terms/) before use.
Homebrew installs `LICENSE.txt`, `NOTICE`, and `THIRD_PARTY_NOTICES` under `brew --prefix rhtop`.
