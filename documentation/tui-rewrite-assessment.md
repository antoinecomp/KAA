# TUI engine: replace or keep? — effort/risk assessment

Step A3 of the technical-refonte breakdown (see PR history: #6 added characterization
tests, #7 narrowed the internal-attribute surface). This document costs out replacing
`kaa/kaasrc/mpTUI.py` with a modern TUI library. **It is not a plan to do so** — it's
the numbers needed to decide whether to.

## What's there today

`kaa/kaasrc/mpTUI.py` (2974 lines) is a self-contained, generic menu-widget toolkit —
zero KAA-specific imports, vendored from an external project (attribution comment:
"Ph Dejean 09.2018, from framagit.org/PhDejean/mp_TUI"). It is **not** curses-based:
it's a `print()`/`input()` loop that redraws the entire screen from scratch every
cycle, using `colorama` for color and Unicode box-drawing characters. No raw terminal
mode, no cursor positioning.

- 92 methods total on the `TUI` class.
- 16 widget types (separator, label, slider, edit box, spinner, checkbox, button,
  tabs, collapsible split panel, combobox, list, grid/table, radio, grouped-checkbox,
  scrollable zone), each with its own render function (~1270 lines combined) and its
  own interaction/update function (~320 lines combined).
- A `.cmd` non-interactive scripting mode (`TUI_ChargerCommandes` / `TUI_ExtraitCommande`),
  sharing the exact same token-dispatch loop as live interactive input — see PR #6.
- Command dispatch (both interactive and `.cmd`-sourced) via dynamic method-name
  construction + `eval()`: `mpTUI.py:2949,2954` build the string `'pMenuTUI.appli'
  + action[0]` and `eval()` it, i.e. mpTUI expects the object passed to `TUI_boucle`
  to expose methods literally named `appli<actionCode>`. `kaaTUIapplication.py`
  defines 14 such methods (`applic`, `applio`, `applih`, ..., `appliZ`, `appliV`).
- JSON-based config persistence (`.cfg`/`.pal`) and a color-palette system.

## How `kaaTUIapplication.py` (`MenuTUI`, 1339 lines) consumes it

After PR #7, every call from `MenuTUI` into `mpTUI.TUI` goes through a named method —
no more raw attribute access. Current tally (`grep -oE "self\.tui\.[A-Za-z_]+"`):

| Method | Calls |
|---|---|
| `TUI_getValeurParNom` | 62 |
| `TUI_getVariable` | 53 |
| `TUI_setVariable` | 28 |
| `TUI_setValeurParId` | 16 |
| `TUI_setValeurParNom` | 15 |
| `TUI_getGroupes` (added in #7) | 11 |
| `TUI_getWidgetParId` | 4 |
| `fonctGCB` | 2 |
| `TUI_setAideParNom` | 2 |
| `TUI_getWidgetParNom` | 2 |
| `TUI_getVariables` (added in #7) | 2 |
| `TUI_getAides` (added in #7) | 2 |
| `TUI_getAideParNom` | 2 |
| `TUI_SauvegardeConfig` | 1 |
| `TUI_ChargeConfig` | 1 |

**203 call sites, 15 distinct method names.** One of those, `fonctGCB`, is a
lower-level per-widget-type handler called directly rather than through the normal
action-dispatch path (`mpTUI.py:2115`) — everything else is a proper named accessor.

## Test coverage today

PR #6 added the only tests that exist anywhere on the TUI stack: 6 tests covering
`TUI_ChargerCommandes` and `TUI_ExtraitCommande` — **2 of the 92 methods on `TUI`**
(~2%), chosen because they're pure file/string parsing, cleanly separable from the
render loop. The 16 widget render/interaction functions (~1590 lines, the bulk of
the file) and the interactive input loop have **zero** coverage — they can't be
characterized without either a live terminal or output-snapshot testing against
captured `print()` calls, neither of which exists today.

## Two options, costed

**(a) Full compatibility shim.** Build a new renderer (e.g. Textual/prompt_toolkit)
behind an adapter that reproduces `mpTUI.TUI`'s 15-method surface (table above) plus
the `appli<actionCode>` eval-dispatch contract, so `kaaTUIapplication.py` needs zero
changes. Cost drivers: faithfully reproducing 15 method signatures × whatever the new
engine's own model requires internally, reimplementing 16 widget types' *behavior*
(not their rendering — their state transitions: what a keypress does to a combobox's
selected index, a slider's value, a split panel's collapsed state, etc.) against the
new engine, and deciding whether to keep the string-`eval()` dispatch (ugly but
zero-touch for the 14 `appli*` methods) or replace it with a real callback registry
(cleaner, but now `kaaTUIapplication.py` *does* need changes, just not to `MenuTUI`'s
203 `self.tui.*` calls).

**(b) Touch the call sites directly.** Replace `mpTUI.TUI` outright; update all ~203
`self.tui.*` call sites in `kaaTUIapplication.py` to whatever the new engine's API is,
and re-derive `.cmd` scripting independently (PR #6's tests give a starting
specification — token format, comment/blank-line handling incl. the empty-token
quirk — to build against, which is real head start). No shim layer to maintain
afterward, but ~203 call sites to touch and verify by hand, with no rendering-layer
test safety net for any of it.

Neither option is small. (a) concentrates risk into one adapter that's hard to get
subtly right (widget state-machine parity) but keeps `kaaTUIapplication.py` frozen.
(b) is more mechanical per-site but touches 5x more code with no net reduction in
total effort, and drops the shim-maintenance cost — the actual cost gap between them
is smaller than it first looks, since (a)'s "zero changes to MenuTUI" is true only if
the eval-dispatch contract is also kept, which (b) would replace anyway.

## Recommendation

Don't start this yet. The regression risk is concentrated exactly where there is no
test coverage (the 16 widget types' interaction behavior, ~1590 of 2974 lines), and
neither option above reduces that risk — both still require someone to manually
verify each widget type behaves identically, informed by nothing but the `.cmd`/menu
literals already in the codebase, since the render loop can't be unit-tested without
snapshot-style output capture (a separate, not-yet-built piece of infrastructure).
mpTUI works today and KAA's `.cmd` automation depends on it.

Not every one of the 16 widget types carries equal risk: counting `'TYPE': '..'` in
`kaaTUIapplication.py`'s own menu declarations shows KAA's actual menu only exercises
9 of them (`SEP` ×42, `EDT` ×14, `LBL`/`CBX` ×9 each, `SPB`/`CKB` ×4 each, `GCB` ×3,
`TAB`/`RAD`/`BTN` ×1 each) — `SLD`, `LST`, `GRD`, `SPL`, `ZED`, `BTN`-heavy usage
aren't in play at all today. If this gets picked up later, output-snapshot tests for
`EDT`/`CBX`/`SPB`/`CKB` first (the widgets actually driving interaction, `SEP`/`LBL`
being static) would do more to de-risk either option than committing to one now, and
the 7 unused-or-barely-used types wouldn't need day-one parity.
