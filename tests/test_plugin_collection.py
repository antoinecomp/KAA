import sys

import pytest

from kaasrc.plugin_collection import PluginCollection


@pytest.fixture(autouse=True)
def isolate_plugin_imports():
    """importPlugin() mutates sys.path and sys.modules as a side effect of
    __import__(); undo that after each test so plugin modules written to a
    tmp_path in one test can't leak into (or be shadowed by) another."""
    syspath_before = list(sys.path)
    modules_before = set(sys.modules)
    yield
    sys.path[:] = syspath_before
    for name in set(sys.modules) - modules_before:
        del sys.modules[name]


def write_plugin(root, dirname, filename, source):
    pluginDir = root / dirname
    pluginDir.mkdir(parents=True, exist_ok=True)
    (pluginDir / filename).write_text(source)


def test_matching_version_is_loaded_and_indexed(tmp_path):
    write_plugin(tmp_path, "PluginOk", "PluginOk.py", """
from kaasrc.plugin_collection import Plugin

version = "1.0"
versionPlugin = "1.0"

class PluginOk(Plugin):
    def __init__(self):
        super().__init__()
        self.nom = "PluginOk"
""")
    collection = PluginCollection()
    collection.loadPluginsXAI(str(tmp_path))

    assert [type(p).__name__ for p in collection.plugins] == ["PluginOk"]
    assert "PluginOk" in collection.dicoPlugins


def test_mismatched_version_is_rejected(tmp_path):
    write_plugin(tmp_path, "PluginBad", "PluginBad.py", """
from kaasrc.plugin_collection import Plugin

version = "1.0"
versionPlugin = "2.0"

class PluginBad(Plugin):
    def __init__(self):
        super().__init__()
""")
    collection = PluginCollection()
    collection.loadPluginsXAI(str(tmp_path))

    assert collection.plugins == []


def test_missing_versionPlugin_attribute_is_rejected_not_crashed(tmp_path):
    write_plugin(tmp_path, "PluginNoVersion", "PluginNoVersion.py", """
from kaasrc.plugin_collection import Plugin

version = "1.0"

class PluginNoVersion(Plugin):
    def __init__(self):
        super().__init__()
""")
    collection = PluginCollection()
    # must not raise, even though the plugin module never declares versionPlugin
    collection.loadPluginsXAI(str(tmp_path))

    assert collection.plugins == []


def test_base_plugin_class_itself_is_never_loaded(tmp_path):
    write_plugin(tmp_path, "PluginImportsBase", "PluginImportsBase.py", """
from kaasrc.plugin_collection import Plugin

version = "1.0"
versionPlugin = "1.0"

class PluginImportsBase(Plugin):
    def __init__(self):
        super().__init__()
""")
    collection = PluginCollection()
    collection.loadPluginsXAI(str(tmp_path))

    # inspect.getmembers() also picks up the imported `Plugin` symbol itself;
    # only the concrete subclass should be registered.
    assert [type(p).__name__ for p in collection.plugins] == ["PluginImportsBase"]


def test_loadPluginsUCXAI_only_keeps_classes_matching_an_active_library(tmp_path):
    write_plugin(tmp_path, "UCDemo", "UCDemo_LibA.py", """
from kaasrc.plugin_collection import Plugin

class UCDemo_LibA(Plugin):
    def __init__(self):
        super().__init__()
        self.bibliotheque = "LibA"
""")
    write_plugin(tmp_path, "UCDemo", "UCDemo_LibB.py", """
from kaasrc.plugin_collection import Plugin

class UCDemo_LibB(Plugin):
    def __init__(self):
        super().__init__()
        self.bibliotheque = "LibB"
""")

    class FakeLibraryPlugin:
        nom = "LibA"

    collection = PluginCollection(pluginsLibrary=[FakeLibraryPlugin()])
    collection.loadPluginsUCXAI(str(tmp_path))

    assert [type(p).__name__ for p in collection.plugins] == ["UCDemo_LibA"]


def test_same_named_helper_files_in_different_plugin_dirs_collide(tmp_path):
    """Characterizes a known hazard, it does not fix it: importPlugin() imports
    plugin entry files by bare module name, sharing the process-wide sys.modules
    cache. If two different use-case directories each ship a same-named helper
    file (a realistic case for a generic name like preprocess_utils.py), the
    entry file that gets discovered first "wins" that name for the rest of the
    process; the second use case silently gets the first one's helper instead
    of its own, with no error anywhere. This pins that behavior so a future fix
    (see the plugin-architecture roadmap) has something to regress-test against.
    """
    write_plugin(tmp_path, "UCAlpha", "helper.py", "VALUE = 'alpha'\n")
    write_plugin(tmp_path, "UCAlpha", "UCAlpha_Lib.py", """
from kaasrc.plugin_collection import Plugin
from helper import VALUE

class UCAlpha_Lib(Plugin):
    def __init__(self):
        super().__init__()
        self.value = VALUE
""")
    write_plugin(tmp_path, "UCBeta", "helper.py", "VALUE = 'beta'\n")
    write_plugin(tmp_path, "UCBeta", "UCBeta_Lib.py", """
from kaasrc.plugin_collection import Plugin
from helper import VALUE

class UCBeta_Lib(Plugin):
    def __init__(self):
        super().__init__()
        self.value = VALUE
""")

    collection = PluginCollection()
    collection.loadPluginsUCXAI(str(tmp_path))

    values = {type(p).__name__: p.value for p in collection.plugins}
    assert set(values) == {"UCAlpha_Lib", "UCBeta_Lib"}
    # Both plugins should see their own use case's helper (VALUE would be
    # "alpha" and "beta" respectively). Today they don't: whichever use case
    # is discovered first silently wins `helper` for both of them.
    assert values["UCAlpha_Lib"] == values["UCBeta_Lib"]
