#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os
import numpy as np

from kaasrc.communs import colPrint
import kaasrc.plugin_collection

from . import Shap_computeExplanations
from . import Shap_plotExplanations

# ---------
# To control the library version
# versionPlugin = "0.41.0"  # v24.09
versionPlugin = "0.44.1"  # v25.09
version = None
try:
    import shap
    version = shap.__version__
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Shap' is not or not properly installed.", "Error")
# ---------

# -------------------------------------------------------------------------------
class Shap(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.nom = "Shap"
        self.description = "Shap"
        self.inputXAIframework = (np.ndarray, np.ndarray)
        self.outputXAIFramework = shap.Explanation
        self.clef = "s"
        self.methodes = {
            # Shap:Partition
            "PartitionTabular": ('pt', [
                ("Max evaluations", "me", 500, "Maximum number of evaluations"),
                ("Max samples    ", "ms", 100, "Maximum number of samples"),
                ("Clustering     ", "cl", 0, {"options": ["correlation", "cosine", "euclidean", "independent"]}, "Clustering method")
            ]),
            "PartitionText": ('px', [
                ("Max evaluations", "me", 500, "Maximum number of evaluations"),
                ("Max samples    ", "ms", 100, "Maximum number of samples"),
                ("Clustering     ", "cl", 0, {"options": ["correlation", "cosine", "euclidean", "independent"]}, "Clustering method")
            ]),
            "PartitionImage": ('pi', [
                ("Max evaluations", "me", 500, "Maximum number of evaluations"),
                ("Max samples    ", "ms", 100, "Maximum number of samples"),
                ("Mask value     ", "mv", 1, {"options": ["blur", "inpaint_ns", "inpaint_telea"]}, "Mask value type"),
                ("Kernel x size  ", "kx", 3, {"lien": ("spimv", [0])}, "Kernel size in the x-direction"),
                ("Kernel y size  ", "ky", 3, {"lien": ("spimv", [0])}, "Kernel size in the y-direction")
            ])
        }

        self.metriques = None

    # ---------------------------------------------------------------------------
    ## Compute explanations
    # @param pDictParams : parameter dictionary
    def XAI_computeExplanations(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        if pDataType == "tabular":
            Shap_computeExplanations.computeExplanationsTables(pDictParams)
        elif pDataType == "text":
            Shap_computeExplanations.computeExplanationsTexts(pDictParams)
        elif pDataType == "image":
            Shap_computeExplanations.computeExplanationsImages(pDictParams)

    # -------------------------------------------------------------------------------
    ## Plot explanations
    # @param pDictParams : parameter dictionary
    # @param pFctExplainToPlot : function to apply to explaination before plotting
    # @param pFctDataToPlot : function to apply to data before plotting
    def XAI_plotExplanations(self, pDictParams, pFctExplainToPlot=None, pFctDataToPlot=None):
        # shortcuts
        pDataType = pDictParams['datatype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        if pDataType == "tabular":
            Shap_plotExplanations.plotExplanationsTables(pDictParams, pFctExplainToPlot, pFctDataToPlot)
        elif pDataType == "text":
            Shap_plotExplanations.plotExplanationsTexts(pDictParams, pFctExplainToPlot, pFctDataToPlot)
        elif pDataType == "image":
            Shap_plotExplanations.plotExplanationsImages(pDictParams, pFctExplainToPlot, pFctDataToPlot)

    # -------------------------------------------------------------------------------
    ## Write report function : generate a latex report of plots and other elements
    # @param pDictParams : parameter dictionary
    def XAI_writeReport(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']
        pRepertProd = pDictParams['repertProd']
        pDataProd = pDictParams['dataProd']

        if pDataType == "tabular":
            kaasrc.reports.writeReportTabText(pDictParams, pExtension="pkl", pClasses=pDictParams['classes'], pSuffixes=["", "mean"])
#        elif pDataType == "text":
#            kaasrc.reports.writeReportTabText(pDictParams, pExtension="pkl", pClasses=pDictParams['classes'], pSuffixes=["", "mean"])
        elif pDataType == "image":
            kaasrc.reports.writeReportImage(pDictParams, pExtension="pkl")
        else:
            colPrint("Quick report not available.","Info")
            resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
            kaasrc.reports.builtTGZ(resultSavedOn)


# ===============================================================================
# end of file
