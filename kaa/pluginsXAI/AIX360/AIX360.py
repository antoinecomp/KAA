#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os, json
import numpy as np

from kaasrc.communs import colPrint

import kaasrc.plugin_collection

from . import AIX360_computeExplanations
from . import AIX360_plotExplanations
from . import AIX360_computeMetrics
from . import AIX360_plotMetrics

# ---------
# To control the library version
#versionPlugin = "0.2.1c"  # v24.09
versionPlugin = "0.3.0"  # v25.09
version = None
try:
    from aix360.algorithms.rbm import LinearRuleRegression, LogisticRuleRegression
    from aix360 import version
    version = version.version
except Exception as err:
    print("Error:", err)
    colPrint("The library 'AIX360' is not or not properly installed.", "Error")
# ---------
try:
    from lime.explanation import Explanation
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Lime' is not or not properly installed.", "Error")
    Explanation = None
# ---------
try:
    import tensorflow.python.framework.ops as eTensor
except Exception as err:
    print("Error:", err)
    colPrint("Package tensorflow is not or not properly installed.", "Error")
# ---------

# -------------------------------------------------------------------------------
class AIX360(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.nom = "AIX360"
        self.description = "AIX360 d'IBM360"
        self.inputXAIframework = (eTensor.EagerTensor, eTensor.EagerTensor)
        self.outputXAIFramework = {"LimeImage": (list, list, Explanation),
                                   "LimeTabular": (list, list, Explanation),
                                   "LimeText": (list, list, Explanation),
                                   "Shap": (list, list, np.ndarray),
                                   "Protodash": (list, list, tuple, np.ndarray),
                                   "BRCGE": (list, list, dict),
                                   "LinearRuleRegression": (list, list, LinearRuleRegression),
                                   "LogisticRuleRegression": (list, list, LogisticRuleRegression)}
        self.clef = "a"
        self.methodes = {
            # AIX360:Lime
            "LimeImage": ('lg', [
                ("Kernel Width     ", "kw", 25 , "Width of the kernel used for weighting"),
                ("Feature Selection", "fs", 0  , {"options": ["auto", "none", "lasso_path", "forward_selection"]}, "Method for feature selection")],
                "Wrap lime method of marcotcr/lime library for image data type."),
            # AIX360:Lime
            "LimeTabular": ('lt', [],
                "Wrap lime method of marcotcr/lime library for tabular data type."),
            # AIX360:Lime
            "LimeText": ('lx', [
                ("Kernel Width     ", "kw", 25, "Width of the kernel used for weighting"),
                ("Feature Selection", "fs", 0, {"options": ["auto", "none", "lasso_path", "forward_selection"]}, "Method for feature selection")],
                "Wrap lime method of marcotcr/lime library for text data type."),
            # AIX360:Shap
            "Shap": ('s', [("Mega pixels     ", "mp", 0, {"options": ["Pixel_grid", "Watershed"]}),
                          ("Nb.Mask.Pixels  ", "nm", 7, {"lien": ("asmp", [0])}),
                          ("Seuil M.-pix.   ", "sl", 0, {"lien": ("asmp", [1])}),
                          ("p.Trait. M.-pix.", "pt", 0, {"lien": ("asmp", [1]), "options": ["blur", "dilate", "erode", "none"]}),
                          ("Noyau M.-pix.   ", "ny", 3, {"lien": ("asmp", [1])}),
                          ("NB samples      ", "ns", 1000, "")],
                          "Wrap shap method of SHAP library."),
            # AIX360:Protodash
            "Protodash": ('p', [
                ("Number of Prototypes", "m", 10, "Number of prototypes to generate")],
                "ProtodashExplainer provides exemplar-based explanations for summarizing datasets as well as explaining predictions made by an AI model. It employs a fast gradient based algorithm to find prototypes along with their (non-negative) importance weights. The algorithm minimizes the maximum mean discrepancy metric and has constant factor approximation guarantees for this weakly submodular function."),
            # AIX360:BRCGE
            "BRCGE": ('b', [
                ("Lambda0", "l0", 1e-3, "Regularization parameter for l0 penalty term"),
                ("Lambda1", "l1", 1e-3, "Regularization parameter for l1 penalty term"),
                ("CNF    ", "cf", 1, {"options": ["False", "True"]}, "If True, performs channel-wise normalization")],
                "BooleanRuleCG is a directly interpretable supervised learning method for binary classification that learns a Boolean rule in disjunctive normal form (DNF) or conjunctive normal form (CNF) using column generation (CG). AIX360 implements a heuristic beam search version of BRCG that is less  computationally intensive than the published integer programming version [#NeurIPS2018]_."),
            # AIX360:LinearRuleRegression
            "LinearRuleRegression": ('li', [
                ("Lambda0   ", "l0", 1e-3, "Regularization parameter for l0 penalty term"),
                ("Lambda1   ", "l1", 1e-3, "Regularization parameter for l1 penalty term"),
                ("Use Orders", "uo", 1, {"options": ["False", "True"]}, "If True, utilizes orders in regression")],
                "Linear Rule Regression is a directly interpretable supervised learning method that performs linear regression on rule-based features."),
            # AIX360:LogisticRuleRegression
            "LogisticRuleRegression": ('lo', [
                ("Lambda0   ", "l0", 1e-3, "Regularization parameter for l0 penalty term"),
                ("Lambda1   ", "l1", 1e-3, "Regularization parameter for l1 penalty term"),
                ("Use Orders", "uo", 1, {"options": ["False", "True"]}, "If True, utilizes orders in regression")],
                "Logistic Rule Regression is a directly interpretable supervised learning method that performs logistic regression on rule-based features.")}

        self.metriques = {
            "Sklearn-Scores": ('ss', [], ["LinearRuleRegression", "LogisticRuleRegression"],
                              "Wrap accuracy, recall and f1 score of the sklearn library"),
            "Monotonicity"  : ('m', [("Baseline", "b", 0.0, "Baseline description")], ["LimeImage", "LimeTabular", "LimeText"],
                              "This metric measures the effect of individual features on model performance by evaluating the effect on model performance of incrementally adding each attribute in order of increasing importance. As each feature is added, the performance of the model should correspondingly increase, thereby resulting in monotonically increasing model performance."),
            "Faithfulness"  : ('f', [("Baseline", "b", 0.0, "Baseline description")], ["LimeImage", "LimeTabular", "LimeText"],
                              "This metric evaluates the correlation between the importance assigned by the interpretability algorithm to attributes and the effect of each of the attributes on the performance of the predictive model. The higher the importance, the higher should be the effect, and vice versa, The metric evaluates this by incrementally removing each of the attributes deemed important by the interpretability metric, and evaluating the effect on the performance, and then calculating the correlation between the weights (importance) of the attributes and corresponding model performance.")}

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

        if pDataType == "tabular":
            pDictParams = AIX360_computeExplanations.computeExplanationsTables(pDictParams)
        elif pDataType == "text":
            pDictParams = AIX360_computeExplanations.computeExplanationsTexts(pDictParams)
        elif pDataType == "image":
            pDictParams = AIX360_computeExplanations.computeExplanationsImages(pDictParams)
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

        if pDataType == "tabular":
            AIX360_plotExplanations.plotExplanationsTables(pDictParams, pFctExplainToPlot, pFctDataToPlot)
        elif pDataType == "image":
            AIX360_plotExplanations.plotExplanationsImages(pDictParams, pFctExplainToPlot, pFctDataToPlot)
        elif pDataType == "text":
            AIX360_plotExplanations.plotExplanationsTexts(pDictParams, pFctExplainToPlot, pFctDataToPlot)

    # ---------------------------------------------------------------------------
    ## Compute metric
    # @param pDictParams : parameter dictionary
    # @return score
    def XAI_computeMetrics(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        if pDataType == "tabular":
            AIX360_computeMetrics.computeMetricsTabular(pDictParams)
        elif pDataType == "image":
            AIX360_computeMetrics.computeMetricsImage(pDictParams)

    # ---------------------------------------------------------------------------
    ## Plot metric results
    # @param pDictParams : parameter dictionary
    def XAI_plotMetrics(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']

        if pDataType == "tabular":
            AIX360_plotMetrics.plotMetricsTabular(pDictParams)
        elif pDataType == "image":
            AIX360_plotMetrics.plotMetricsImage(pDictParams)

    # -------------------------------------------------------------------------------
    ## Write report function : generate a latex report of plots and other elements
    # @param pDictParams : parameter dictionary
    def XAI_writeReport(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']
        pMethod = pDictParams['method']
        pRepertProd = pDictParams['repertProd']
        pDataProd = pDictParams['dataProd']

        if pDataType == "tabular":
            if pMethod == "LimeTabular":
                # Récupération de la liste des items
                ficItems = os.path.join(pDataProd, "dataExplanations", pRepertProd, 'listItems.json')
                with open(ficItems, 'r', encoding="utf-8") as json_data:
                    listItems = json.load(json_data)['listItems']
                kaasrc.reports.writeReportTabText(pDictParams, pExtension="pkl", pListItems=listItems, pClasses=pDictParams['classes'])
            elif pMethod == "Protodash":
                # Récupération de la liste des items
                ficItems = os.path.join(pDataProd, "dataExplanations", pRepertProd, 'listItems.json')
                with open(ficItems, 'r', encoding="utf-8") as json_data:
                    listItems = json.load(json_data)['listItems']
                kaasrc.reports.writeReportTabText(pDictParams, pExtension="pkl", pListItems=listItems, pClasses=[""], pSuffixes=["", "differences"])
            elif pMethod == "Shap":
                kaasrc.reports.writeReportTabText(pDictParams, pExtension="pkl", pClasses=pDictParams['classes'], pSuffixes=["", "mean"])
            else:
                colPrint("Quick report not available.","Info")
                resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
                kaasrc.reports.builtTGZ(resultSavedOn)
        elif pDataType == "image":
            if pMethod == "LimeImage":
                kaasrc.reports.writeReportImage(pDictParams, pExtension="pkl", pClasses=pDictParams['classes'])
            elif pMethod == "Shap":
                kaasrc.reports.writeReportImage(pDictParams, pExtension="pkl")
            else:
                colPrint("Quick report not available.","Info")
                resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
                kaasrc.reports.builtTGZ(resultSavedOn)
        else:
            colPrint("Quick report not available.","Info")
            resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
            kaasrc.reports.builtTGZ(resultSavedOn)

# ===============================================================================
# end of file
