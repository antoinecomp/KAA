# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

KAA is a Python framework/TUI (Text-based User Interface) for applying explainability (XAI) methods and metrics
from several third-party XAI libraries to AI models, in order to verify and compare them. It is a mediation tool:
it wraps heterogeneous XAI libraries (AIX360, Alibi, Captum, PAIR saliency, Shap, Xplique) behind a common plugin
interface and a common TUI so that different explainability methods/metrics can be run against a given "use case"
(a model + its data) with minimal glue code per combination.

Python **3.8** is required (see `setup.py`, `python_requires="==3.8"`).

## Commands

Install:
```bash
pip install -r requirements.txt
pip install -r requirementsXAIlibs.txt   # pulls in AIX360/Alibi/Captum/lime/saliency/shap/xplique — comment out any you don't need
```

Run the TUI interactively:
```bash
python3 kaa/kaa.py -u <path-to-pluginsUCXAI> -b <path-to-use-case-base> -r <path-to-results>
# e.g.
python3 kaa/kaa.py -u example/pluginsUCXAI/ -b example/UseCase/ -r ~/KAA_example
```

Run non-interactively from a command file (`.cmd`, see `example/example.cmd` for syntax):
```bash
python3 kaa/kaa.py -u example/pluginsUCXAI/ -b example/UseCase/ -r ~/KAA_example -c example/example.cmd
```

Key CLI flags (`kaa/kaa.py`):
- `-u/--pluginUCXAI` : path to the use-case plugins directory (required in practice)
- `-b/--useCaseBase` : path to the directory containing use case data/models (or `USECASE_BASE` env var)
- `-r/--resultProd` : output directory for generated reports/results (or `RESULT_PROD` env var)
- `-x/--pluginXAI` : extra directory of pluginsXAI to load in addition to the built-in `kaa/pluginsXAI`
- `-a/--activate` / `-d/--deactivate` : comma-separated use case plugin names to enable/disable (default all active)
- `-c/--command` : a `.cmd` script driving the TUI non-interactively
- `-D/--Debug` : debug mode

There is no test suite, linter config, or CI in this repo — don't assume `pytest`/`flake8`/etc. are wired up; verify
before adding tooling.

## Architecture

### Two plugin families, discovered by `kaasrc/plugin_collection.py`

`PluginCollection` walks a directory tree with `glob`, imports every `.py` module found, and registers any class that
subclasses `Plugin` (from the same module) via `issubclass`. There are two kinds of plugins, loaded in sequence from
`kaa.py`'s `mainKaa()`:

1. **pluginsXAI** — one per explainability *library* (AIX360, Alibi, Captum, PAIRsaliency, Shap, Xplique), living in
   `kaa/pluginsXAI/<Library>/<Library>.py`. Loaded first, with `ctrlVersion=True`: each module must expose
   `version` (the installed library's actual version, read at import time) and `versionPlugin` (the version this
   plugin was written against) — the plugin is silently rejected if they mismatch, so an XAI library plugin failing
   to load usually means an installed-library/plugin version drift, not a code bug.
   Each pluginsXAI class implements: `XAI_computeExplanations`, `XAI_plotExplanations`, `XAI_computeMetrics`,
   `XAI_plotMetrics`, `XAI_writeReport`, and declares `self.methodes` / `self.metriques` dicts. Each entry in those
   dicts is `"MethodName": (hotkey, [(label, paramCode, default, ...options/help), ...], long_description)` — this
   is what auto-generates the TUI's parameter-entry forms and CLI param codes (e.g. `xobz:64` in a `.cmd` file =
   Xplique/Occlusion/batch-size=64). When adding/editing a method, keep this tuple shape in sync with the TUI param
   parser in `kaasrc/kaaTUIapplication.py`.

2. **pluginsUCXAI** — one per (use case, XAI library) pair, living under `<pluginsUCXAI-root>/<UseCase>/`, loaded
   second with `ctrlVersion=False` and filename pattern `<UseCase>_*.py` (see `PluginCollection.loadPluginsUCXAI`).
   A use case directory (see `example/pluginsUCXAI/UCRenaultWeldingResnet/` for the reference layout) typically has:
   - `<UseCase>.json` — declares model classes, dataset path, `datatype` (`image`/`tabular`/...), `modeltype`
     (`classification`/`detection`/`segmentation`), model file paths.
   - `<UseCase>.py` — the shared, library-agnostic glue: `UC_createModel`, `UC_computeInference`,
     `UC_ImageDataToPlot`/`UC_ExplanationToPlot`, and a `UC_Model` wrapper class around the actual model.
   - `<Model>.py` — the actual model-specific wrapper (e.g. `RenaultWeldingResnet.py`) doing preprocessing/inference.
   - `<UseCase>_<Library>.py` (one per supported library, e.g. `_Xplique.py`, `_Captum.py`, `_Shap.py`,
     `_AIX360.py`, `_PAIRsaliency.py`) — a thin `Plugin` subclass declaring `self.modeles` (model names this
     combination supports) and `self.bibliotheque` (the XAI library name, must match a loaded pluginsXAI's `nom`),
     and delegating `UC_createModel`/`UC_computeInference`/plotting back to the shared `<UseCase>.py` module while
     wiring in the library-specific plotting function.
   `PluginCollection.addPlugin` cross-checks that a UC plugin's class-name suffix (after the last `_`) matches a
   `nom` in the already-loaded pluginsXAI collection — a UC plugin for a library that isn't installed/loaded is
   silently skipped, not errored.

### Runtime flow

`kaa.py::mainKaa()` → loads pluginsXAI, then pluginsUCXAI (filtered by `-a`/`-d`) → hands both collections to
`kaasrc/kaaTUIapplication.py::TUI`, which builds `MenuTUI`. `MenuTUI.__init__` builds `self.table` — a nested dict
`{useCase: {model: {library: {'methodes':..., 'metriques':...}}}}` — from the loaded plugins, and dynamically
generates the TUI's menu blocks/parameter fields from it. The actual character-cell TUI widget toolkit lives in
`kaasrc/mpTUI.py` (large, mostly self-contained curses-style menu engine — treat as a UI framework, not
application logic). `kaasrc/kaaActions.py` implements the actions the menu triggers (dataset collection, running
inference/explanations/metrics, invoking reports). `.cmd` files (see `example/example.cmd`) replay TUI keystrokes
non-interactively; sections are delimited by `k:<n>` (jump to menu block `n`: 0=use case, 1=explainability,
2=reports, 3=execution) and `l` triggers a run.

### Cross-plugin data contracts

`kaasrc/controles*.py` (`controles.py` common + per-datatype `controlesImage.py`, `controlesObject.py`,
`controlesSegment.py`, `controlesTabular.py`, `controlesText.py`) validate the shapes/types of data crossing the
UC-plugin ↔ XAI-plugin boundary at each pipeline stage (`control*Input`/`control*Output` pairs around inference,
`XAI_computeExplanations`, `XAI_computeMetrics`, plotting). When wiring a new use case or XAI library plugin, these
are the functions that will raise on a shape/type mismatch — check them first when debugging a "control" error.

`kaasrc/communs.py` holds cross-cutting utilities used by both plugin families (XAI-framework tensor conversion via
`convertToXAIframework`, image resize/mega-pixel helpers, torch device selection, dataset directory traversal).

`kaasrc/reports.py` + `kaasrc/ressources/*.tex` render LaTeX-based PDF reports (per-method contact sheets and
full reports) from the results a run produces; `kaasrc/graphMatplot.py` produces the plots those reports embed.

## Repo layout

- `kaa/kaa.py` — CLI entrypoint.
- `kaa/kaasrc/` — the framework core (TUI, plugin loading, controls, reports) described above.
- `kaa/pluginsXAI/` — built-in XAI library plugins shipped with KAA.
- `example/pluginsUCXAI/` — reference use-case plugin (`UCRenaultWeldingResnet`), useful as a template when adding
  a new use case.
- `example/UseCase/` — sample model/data for the example use case, and `example.cmd` sample command script.
- `documentation/Kaa_User_and_Integration_Manual.pdf` — full user/integration manual (source of truth beyond this
  file for TUI usage and plugin-authoring details).
