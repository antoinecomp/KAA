#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import importlib, inspect, os, glob, sys

# -------------------------------------------------------------------------------
class Plugin(object):
    """Base class that each plugin must inherit from. within this class
    you must define the methods that all of your plugins must implement
    """

    # ---------------------------------------------------------------------------
    def __init__(self):
        self.description = 'UNKNOWN'

#    # ---------------------------------------------------------------------------
#    def perform_operation(self, argument):
#        """The method that we expect all plugins to implement. This is the
#        method that our framework will call
#        """
#        raise NotImplementedError

# -------------------------------------------------------------------------------
class PluginCollection(object):
    """Upon creation, this class will read the plugins package for modules
    that contain a class definition that is inheriting from the Plugin class
    """

    # ---------------------------------------------------------------------------
    def __init__(self, pluginsLibrary=None, pluginsActive="All", pluginsDeactive=""):
        """Constructor that initiates the reading of all available plugins
        when an instance of the PluginCollection object is created
        """
        self.plugins = []
        self.dicoPlugins = {}
        self.seenPaths = []
        self.pluginsLibrary = pluginsLibrary
        self.pluginsActive = pluginsActive
        self.pluginsDeactive = pluginsDeactive
        self.pluginsUCXAIdirectory = ""

    # ---------------------------------------------------------------------------
    def loadPluginsUCXAI(self, pluginsDirectory):
        """Reset the list of all plugins and initiate the walk over the main
        provided plugin package to load all available plugins
        """
        self.pluginsUCXAIdirectory = pluginsDirectory
        self.loadPluginsXAI(pluginsDirectory, ctrlVersion=False, extension="_*")

    # ---------------------------------------------------------------------------
    def loadPluginsXAI(self, pluginsDirectory, ctrlVersion=True, extension=""):
        """Recursively walk the supplied package to retrieve all plugins
        """
        for data in glob.glob(os.path.join(pluginsDirectory, '*')):
            if os.path.isdir(data) and (os.path.basename(data)[0] not in ['_', '.']):
                for fichier in glob.glob(os.path.join(data, "%s%s.py"%(os.path.basename(data), extension))):
                    self.importPlugin(fichier, ctrlVersion)
            else:
                self.importPlugin(data, ctrlVersion)

    # ---------------------------------------------------------------------------
    def importPlugin(self, package, ctrlVersion):
        # Each plugin directory is imported as its own package (see the
        # __init__.py living alongside every plugin) rather than as a bare
        # top-level module: this is what lets a plugin's sibling helper
        # files be reached with `from . import ...` without colliding, in
        # sys.modules, with a same-named helper file in a different plugin
        # directory. The parent directory (not the plugin directory itself)
        # goes on sys.path, since it's the parent that must be searchable
        # for the plugin's package name.
        pluginDir = os.path.dirname(package)
        parentDir = os.path.dirname(pluginDir)
        if parentDir not in sys.path:
            sys.path.append(parentDir)
        packageName = os.path.basename(pluginDir)
        useCase = packageName
        if (self.pluginsActive == "All") or (useCase in self.pluginsActive):
            if (self.pluginsDeactive == "") or (useCase not in self.pluginsDeactive):
                moduleBasename = os.path.basename(package).replace('.py', '')
                pluginModule = importlib.import_module("%s.%s"%(packageName, moduleBasename))
                clsmembers = inspect.getmembers(pluginModule, inspect.isclass)
                self.addPlugin(clsmembers, pluginModule, ctrlVersion)

    # ---------------------------------------------------------------------------
    def addPlugin(self, clsmembers, pluginModule, ctrlVersion):
        for (_, c) in clsmembers:
            # Only add classes that are a sub class of Plugin, but NOT Plugin itself
            if issubclass(c, Plugin) & (c is not Plugin):
                if self.pluginsLibrary is not None:
                    if c.__name__.split('_')[-1] in [pluginsLib.nom for pluginsLib in self.pluginsLibrary]:
                        self.addCorrectPlugin(c, pluginModule, ctrlVersion)
                else:
                    self.addCorrectPlugin(c, pluginModule, ctrlVersion)

    # ---------------------------------------------------------------------------
    def addCorrectPlugin(self, c, pluginModule, ctrlVersion):
        print(f'    Plugin found : {c.__name__}')
        ctrlVersionOK = True
        if ctrlVersion:
            ctrlVersionOK = False
            pluginVersion = "ND"
            if hasattr(pluginModule, 'version') and pluginModule.version is not None:
                pluginVersion = pluginModule.version
                print(f'         library version : {pluginVersion}')
            if hasattr(pluginModule, 'versionPlugin') and pluginModule.versionPlugin == pluginVersion:
                ctrlVersionOK = True
        if ctrlVersionOK:
            self.plugins.append(c())
            self.dicoPlugins[c.__name__] = c()
        else:
            requiredVersion = getattr(pluginModule, 'versionPlugin', 'ND')
            print('\033[31m' + 'ERROR > incompatible library version: ' + str(requiredVersion) + ' required.' + '\033[36m')

# ===============================================================================
# end of file
