# Running KAA on Apple Silicon (arm64) — validation notes

Written after the first real end-to-end run of KAA on an Apple Silicon Mac (M3, 8 GB,
macOS 26 "Tahoe"). Captures what actually worked, since `requirements.txt`'s pins
don't install cleanly on this hardware as-is — see #16. If you're picking this up on
another Mac (Apple Silicon is the default since late 2020), start here rather than
rediscovering the same blockers.

## The blocker: `tensorflow==2.9.0` has no arm64 wheel

Verified against PyPI directly: `tensorflow==2.9.0` (pinned, unconditionally, in the
base `requirements.txt`) only ships `x86_64` wheels for macOS. `pip install -r
requirements.txt` fails on arm64 before you get anywhere. `torch==2.4.1` (also
base-pinned) is fine — it has real arm64 wheels.

Workaround: `pip install tensorflow-macos` (Apple's ARM-native fork) instead of the
pinned version. Nothing in `plugin_collection.py`'s version-gating checks
tensorflow's *own* version — only each XAI library's `__version__` against its
declared `versionPlugin` — so this substitution is low-risk for anything that
doesn't specifically depend on TF 2.9.0 behavior. **Only validated so far against
Captum** (a torch-only XAI library); not yet tried against the tensorflow-dependent
ones (Xplique, AIX360, PAIRsaliency).

## No Python 3.9/3.10/3.11 by default

`pyproject.toml` requires `>=3.9,<3.11`; a fresh Mac (or one only used for other
work) likely only has whatever Homebrew's default `python3` currently is (was
3.14 during this validation). Install one in range:

```bash
brew install python@3.10
/opt/homebrew/bin/python3.10 -m venv .venv
```

## A working scoped install for a first validation pass (no company model yet)

Installing the *entire* `requirements.txt` + `requirementsXAIlibs.txt` pulls in
both deep learning frameworks plus 6 XAI libraries — heavy, and blocked outright by
the tensorflow issue above. For just confirming the pipeline works, this is much
lighter (skips tensorflow entirely, uses Captum — torch-only, has arm64 wheels):

```bash
.venv/bin/pip install \
  numpy==1.23.5 matplotlib==3.7.5 Pillow==9.1.1 colorama==0.4.6 \
  torch==2.4.1 torchvision==0.19.1 ultralytics==8.3.231
.venv/bin/pip install "git+https://github.com/pytorch/captum@v0.7.0"
```

This is enough for `example/pluginsUCXAI/UCRenaultWeldingResnet` + the `Captum`
plugin specifically. All other XAI library plugin entry files still get scanned by
`plugin_collection.py` at startup (it doesn't filter by what's installed) but
degrade gracefully (each import is `try/except`-guarded) rather than crashing — you'll
see a wall of "Error: No module named 'X'" during startup for the libraries you
didn't install; that's expected, not a failure.

**If you need actual explanation computation from a tensorflow-based library**
(Xplique, AIX360, PAIRsaliency), you'll hit the blocker above and need the
`tensorflow-macos` workaround too — not yet validated end-to-end on arm64.

## Known bugs hit during this validation (tracked separately)

Two crashes and one silent-degenerate-result issue were found in the vendored
example/library code while actually running it — not introduced by any of this
fork's modernization changes. Tracked as their own issues so they don't get lost:

- #13 — `RenaultWeldingResnet.py`: unguarded `eTensor` reference crashes any
  non-tensorflow XAI library when tensorflow isn't installed at all.
- #14 — `Captum_computeExplanations.py`: missing `None`-guard on Occlusion's `sz`
  parameter (has the exact same declared default as `bs`, which *is* guarded).
- #15 — Captum/Occlusion produced exactly-zero attribution values on the bundled
  example images — root cause not yet found; could be a real KAA-side wiring bug
  or a genuine degenerate case for this specific model+data. **Don't trust a
  Captum/Occlusion result on a new model without checking this first.**

## `kaa.py` writes runtime state to the current working directory

Independent of `-r`/`--resultProd`: `tuiKaa.cfg`, `tuiKaa.pal` (TUI config/palette
persistence) and `kaaJson/` (per-run parameter export) get written wherever
`kaa.py` is launched from. If you run it from the repo root (as the README's own
quickstart commands do), expect these to appear there — now gitignored, but they'll
still show up in your working directory each run.
