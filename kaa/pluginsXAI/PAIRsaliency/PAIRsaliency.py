#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os

import numpy as np

from kaasrc.communs import colPrint
import kaasrc.plugin_collection

import PAIRsaliency_computeExplanations
import PAIRsaliency_plotExplanations

# ---------
try:
    import tensorflow.python.framework.ops as eTensor
except Exception as err:
    print("Error:", err)
    colPrint("Package tensorflow is not or not properly installed.", "Error")
# ---------
# To control the library version
#versionPlugin = "0.2.0-c"  # v24.09
versionPlugin = "0.2.1-c"  # v25.09
version = None
try:
    from saliency import version
    version = version.version
except Exception as err:
    print("Error:", err)
    colPrint("The library 'PAIRsaliency' is not or not properly installed.", "Error")
# ---------


# -------------------------------------------------------------------------------
class PAIRsaliency(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.nom = "PAIRsaliency"
        self.description = "Description PAIRsaliency"
        self.inputXAIframework = (eTensor.EagerTensor, eTensor.EagerTensor)
        self.outputXAIFramework = np.ndarray
        self.clef = "p"
        self.methodes = {
            # Keys: INPUT_OUTPUT_GRADIENTS
            "GuidedIG": ('g', [
                ("Riemann sum steps", "rs", 200, "Number of steps for Riemann sum"),
                ("Baseline         ", "bl", 0., "Baseline value"),
                ("Maximum distance ", "md", 0.02, "Maximum distance"),
                ("Features fraction", "ff", 0.25, "Fraction of features")
            ], "Guided IG improves upon Integrated Gradients by introducing the idea of an Adaptive Path Method and can take advantage of the knowledge of the model to dynamically construct a path that meets a desirable objective."),
            "SmoothGrad-GuidedIG": ('sg', [
                ("Riemann sum steps", "rs", 200, "Number of steps for Riemann sum"),
                ("Baseline         ", "bl", 0., "Baseline value"),
                ("Maximum distance ", "md", 0.02, "Maximum distance"),
                ("Features fraction", "ff", 0.25, "Fraction of features"),
                ("Stdev spread     ", 'sd', 0.15, "Standard deviation spread"),
                ("Number of samples", 'ns', 25, "Number of samples"),
                ("Magnitude        ", 'mg', 1, "Magnitude")
            ], "Equivalent to GuidedIG method; SmoothGrad often reduces the noise from irrelevant noisy regions."),
            # Keys: INPUT_OUTPUT_GRADIENTS (call to IntegratedGradients)
            "XRAI": ('x', [
                ("Batch size  ", "bz", 64, "Batch size"),
                ("Baseline min", "bm", 0., "Minimum baseline value"),
                ("Baseline max", "bx", 1., "Maximum baseline value")
            ], "This method attributes regions instead of individual pixels. It does it by aggregating pixel level attributions within regions to find image areas that positively or negatively impact the prediction."),
            # Keys: INPUT_OUTPUT_GRADIENTS
            "VanillaGradients": ('v', [], "This method computes the standard model gradients w.r.t. the features but can also compute its gradients averages."),
            "SmoothGrad-VanillaGradients": ('sv', [
                ("Stdev spread     ", 'sd', 0.15, "Standard deviation spread"),
                ("Number of samples", 'ns', 25, "Number of samples"),
                ("Magnitude        ", 'mg', 1, "Magnitude")
            ], "Equivalent to VanillaGradients method; SmoothGrad often reduces the noise from irrelevant noisy regions."),
            # Keys: INPUT_OUTPUT_GRADIENTS
            "IntegratedGradients": ('ig', [
                ("Batch size", "bz", 64, "Batch size"),
                ("Baseline  ", "bl", 0., "Baseline value"),
                ("Steps     ", 'st', 25, "Number of steps")
            ], "Integrated Gradients combines the implementation of gradients along a baseline and with the sensitivity"),
            # Keys: CONVOLUTION_LAYER_VALUES, CONVOLUTION_OUTPUT_GRADIENTS
            "GradCAM": ('gc', [
                ("Number of Bands", "bd", 1)
            ], "The approach of Grad-CAM is a generalization of Class Activation Maps (CAM), a technique for identifying discriminative regions, by using the gradient information flowing into a model layer"),
            # Keys: INPUT_OUTPUT_GRADIENTS
            "BlurIG": ('b', [
                ("Max sigma    ", "ms", 50, "Maximum sigma value"),
                ("Steps        ", "st", 100, "Number of steps"),
                ("Gradient step", "gs", 0.01, "Gradient step"),
                ("Square root  ", "sq", 0, {"options": ["False", "True"]}, "Square root option"),
                ("Batch size   ", "bz", 64, "Batch size")
            ], "BlurIG extends the Integrated Gradients technique. Blur Integrated Gradient relies on Gaussians and Laplacians of the Gaussian to construct human intelligible explanations."),
            "SmoothGrad-BlurIG": ('sb', [
                ("Max sigma        ", "ms", 50, "Maximum sigma value"),
                ("Steps            ", "st", 100, "Number of steps"),
                ("Gradient step    ", "gs", 0.01, "Gradient step"),
                ("Square root      ", "sq", 0, {"options": ["False", "True"]}, "Square root option"),
                ("Batch size       ", "bz", 64, "Batch size"),
                ("Stdev spread     ", 'sd', 0.15, "Standard deviation spread"),
                ("Number of samples", 'ns', 25, "Number of samples"),
                ("Magnitude        ", 'mg', 1, "Magnitude")
            ], "Equivalent to BlurIG method; SmoothGrad often reduces the noise from irrelevant noisy regions."),
            # Keys: OUTPUT_LAYER_VALUES
            "Occlusion": ('o', [
                ("Size  ", "sz", 15, "Size of the patches to apply"),
                ("Value ", "vl", 0, "Value used as occlusion"),
                ("Stride", "st", 1, "Stride between two patches")
            ], "Used to compute the Occlusion sensitivity method, sweep a patch that occludes pixels over the images and use the variations of the model prediction to deduce critical areas.")
        }

        self.metriques = None

    # ---------------------------------------------------------------------------
    ## Compute explanations
    # @param pDictParams : parameter dictionary
    # @param pExplainClasses : Boolean to indicate if classes have to be treated
    # @return parameter dictionary
    def XAI_computeExplanations(self, pDictParams, pExplainClasses=True):
        # shortcuts
        pDataType = pDictParams['datatype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        if pDataType == "tabular":
            pDictParams = PAIRsaliency_computeExplanations.computeExplanationsTables(pDictParams, pExplainClasses)
        elif pDataType == "image":
            pDictParams = PAIRsaliency_computeExplanations.computeExplanationsImages(pDictParams)

        return pDictParams

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

        # Tracé
        if pDataType == "tabular":
            PAIRsaliency_plotExplanations.plotExplanationsTable(pDictParams, pFctExplainToPlot, pFctDataToPlot)
        elif pDataType == "image":
            PAIRsaliency_plotExplanations.plotExplanationsImage(pDictParams, pFctExplainToPlot, pFctDataToPlot)

    # -------------------------------------------------------------------------------
    ## Write report function : generate a latex report of plots and other elements
    # @param pDictParams : parameter dictionary
    def XAI_writeReport(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']
        pRepertProd = pDictParams['repertProd']
        pDataProd = pDictParams['dataProd']

        if pDataType == "tabular":
            kaasrc.reports.writeReportTabText(pDictParams, pClasses=pDictParams['classes'], pSuffixes=["mean"])
        elif pDataType == "image":
            kaasrc.reports.writeReportImage(pDictParams)
        else:
            colPrint("Quick report not available.","Info")
            resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
            kaasrc.reports.builtTGZ(resultSavedOn)

# ===============================================================================
# end of file
