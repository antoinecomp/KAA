#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os

from kaasrc.communs import colPrint
import kaasrc.plugin_collection

from . import Alibi_computeExplanations
from . import Alibi_plotExplanations

# ---------
# To control the library version
#versionPlugin = "0.9.1"  # v24.09
versionPlugin = "0.9.6"  # v25.09
version = None
try:
    from alibi import __version__
    version = __version__
except Exception as err:
    print("Error:", err)
    colPrint("The 'Alibi' library is not or not properly installed.", "Error")
# ---------


# -------------------------------------------------------------------------------
class Alibi(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.nom = "Alibi"
        self.description = "Alibi"
        self.inputXAIframework = (None, None)
        self.outputXAIFramework = None
        self.clef = "i"
        self.methodes = {
            # Alibi:Anchors
            "Anchors": ('a', [
                ("Threshold                ", "th", 0.95, "Threshold value for selecting anchors"),
                ("Sample Probability       ", "sp", 0.5,  "Probability of sampling"),
                ("Sampling Strategy        ", "ss", 1,    {"options": ["language_model", "similarity", "unknown"]}, "Strategy for sampling"),
                ("Spacy Model              ", "sm", 0,    {"lien": ("iass", [1, 2]), "options": ["en_core_web_md"]}, "Spacy model to use"),
                ("Top N                    ", "tn", 100,  {"lien": ("iass", [0, 1])}, "Top N samples to consider"),
                ("Temperature              ", "te", 0.1,  {"lien": ("iass", [0, 1])}, "Temperature parameter"),
                ("Use Probability          ", "up", 0,    {"lien": ("iass", [0, 1]), "options": ["True", "False"]}, "Flag to use probability"),
                ("Filling                  ", "f", 0,     {"lien": ("iass", [0]), "options": ["parallel", "filling"]}, "Method for filling"),
                ("Fraction Mask Template   ", "fm", 0.1,  {"lien": ("iass", [0])}, "Fraction of mask template"),
                ("Batch Size Language Model", "bs", 32,   {"lien": ("iass", [0])}, "Batch size for language model"),
                ("Punctuation              ", "p", "['!',  '#', '$', '%', '&',  '(', ')', '*', '+', ', ', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', ']', '^', '_', '`', '{', '|', '}', '~']", {"lien": ("iass", [0])}, "List of punctuation marks"),
                ("Stopwords                ", "s", [],    {"lien": ("iass", [0])}, "List of stopwords"),
                ("Sample Punctuation       ", "spc", 0,   {"lien": ("iass", [0]), "options": ["True", "False"]}, "Flag to sample punctuation")],
                "The anchor algorithm is based on the Anchors: High-Precision Model-Agnostic Explanations paper by Ribeiro et al.(2018). The idea behind anchors is to explain the behaviour of complex models with high-precision rules called anchors. These anchors are locally sufficient conditions to ensure a certain prediction with a high degree of confidence.")}
        self.metriques = None

    # ---------------------------------------------------------------------------
    ## Compute explanations
    # @param pDictParams : parameter dictionary
    # @return parameter dictionary
    def XAI_computeExplanations(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        if pDataType == "text":
            pDictParams = Alibi_computeExplanations.computeExplanationsTexts(pDictParams)
        return pDictParams

    # ---------------------------------------------------------------------------
    ## Launch the explanations plotting
    # @param pDictParams : parameter dictionary
    # @param pFctExplainToPlot : function to apply to explaination before plotting
    # @param pFctDataToPlot : function to apply to data before plotting
    def XAI_plotExplanations(self, pDictParams, pFctExplainToPlot=None, pFctDataToPlot=None):
        # shortcuts
        pDataType = pDictParams['datatype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        if pDataType == "text":
            Alibi_plotExplanations.plotExplanationsTexts(pDictParams, pFctExplainToPlot, pFctDataToPlot)

    # ---------------------------------------------------------------------------
    ## Start the report writing action
    # @param pDictParams : dictionnary of parameters
    def XAI_writeReport(self, pDictParams):
        # shortcuts
        pRepertProd = pDictParams['repertProd']
        pDataProd = pDictParams['dataProd']

        colPrint("Quick report not available.","Info")
        resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
        kaasrc.reports.builtTGZ(resultSavedOn)

# ===============================================================================
# end of file
