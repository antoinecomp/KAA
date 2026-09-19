"""Characterization tests for the `.cmd` scripting mini-language implemented in
kaasrc/mpTUI.py (TUI_ChargerCommandes / TUI_ExtraitCommande). These document
current behavior, including a couple of surprising quirks, as a safety net for
any future refactor of the TUI layer -- see the technical-refonte roadmap.

TUI's constructor (mpTUI.TUI.__init__) builds a full widget tree from a large
declarative menu dict, which the two functions under test never touch (they
only read/write self.listeCommandes, self.affichageTUI, and self._print on the
error path). So tests build a bare, un-initialized TUI instance via
object.__new__() instead of fabricating a full menu declaration.
"""
import os

import pytest

from kaasrc.mpTUI import TUI

EXAMPLE_CMD = os.path.join(
    os.path.dirname(__file__), "..", "example", "example.cmd"
)


def bare_tui():
    """A TUI instance that skips __init__ (and its heavy menu-dict
    requirement), since TUI_ChargerCommandes/TUI_ExtraitCommande don't
    depend on any state __init__ would have set up."""
    return object.__new__(TUI)


def test_ChargerCommandes_tokenizes_and_switches_to_scripted_mode(tmp_path):
    cmdFile = tmp_path / "demo.cmd"
    cmdFile.write_text(
        "; full-line comment, skipped entirely\n"
        "k:0\n"
        "c:'Foo dm:1 dn:2\n"
        "a:d ;; inline comment stripped\n"
    )
    tui = bare_tui()
    tui.affichageTUI = True

    tui.TUI_ChargerCommandes(str(cmdFile))

    assert tui.affichageTUI is False
    assert tui.listeCommandes == ["k:0", "c:'Foo", "dm:1", "dn:2", "a:d", ""]


def test_ChargerCommandes_blank_lines_produce_empty_string_tokens(tmp_path):
    """A quirk, not a feature: a blank line is not skipped like a `;`-comment
    line is -- it still passes the `ligne[0] != ';'` filter and ends up
    contributing a literal empty-string token to the command queue."""
    cmdFile = tmp_path / "demo.cmd"
    cmdFile.write_text("k:0\n\nc:'Foo\n")
    tui = bare_tui()

    tui.TUI_ChargerCommandes(str(cmdFile))

    assert tui.listeCommandes == ["k:0", "", "c:'Foo"]


def test_ChargerCommandes_missing_file_reports_error_without_raising():
    tui = bare_tui()
    errors = []
    tui._print = lambda message, pType="Normal": errors.append((pType, message))

    tui.TUI_ChargerCommandes("does/not/exist.cmd")  # must not raise

    assert errors and errors[0][0] == "Error"
    assert not hasattr(tui, "listeCommandes")


def test_ExtraitCommande_pops_fifo_and_splits_on_colon():
    tui = bare_tui()
    tui.listeCommandes = ["k:0", "c:'Foo", "a:d"]

    assert tui.TUI_ExtraitCommande() == ["k", "0"]
    assert tui.TUI_ExtraitCommande() == ["c", "'Foo"]
    assert tui.listeCommandes == ["a:d"]
    assert tui.TUI_ExtraitCommande() == ["a", "d"]
    assert tui.listeCommandes == []


def test_ExtraitCommande_on_empty_string_token_yields_single_empty_element():
    """Matches the blank-line quirk above: an empty-string token (from a
    blank .cmd line) splits into [''] rather than [] -- action[0] is '' and
    action[1:] is empty, not "no command"."""
    tui = bare_tui()
    tui.listeCommandes = [""]

    assert tui.TUI_ExtraitCommande() == [""]


@pytest.mark.skipif(not os.path.exists(EXAMPLE_CMD), reason="example.cmd not found")
def test_ChargerCommandes_against_the_real_example_cmd_fixture():
    tui = bare_tui()

    tui.TUI_ChargerCommandes(EXAMPLE_CMD)

    nonEmpty = [c for c in tui.listeCommandes if c != ""]
    assert nonEmpty[0] == "k:0"
    assert nonEmpty[-1] == "X"
    assert "c:'UCRenaultWeldingResnet" in nonEmpty
