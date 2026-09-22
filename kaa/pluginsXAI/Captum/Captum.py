#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os
from kaasrc.communs import colPrint
import kaasrc.plugin_collection

from . import Captum_computeExplanations
from . import Captum_plotExplanations

# ---------
try:
    import torch
except Exception as err:
    print("Error:", err)
    colPrint("Package torch is not or not properly installed.", "Error")
# ---------
# To control the library version
#versionPlugin = "0.5.0-c"  # v24.09
versionPlugin = "0.7.0"  # v25.09
version = None
try:
    from captum import __version__
    version = __version__
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Captum' is not or not properly installed.", "Error")
# ---------


# -------------------------------------------------------------------------------
class Captum(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.nom = "Captum"
        self.description = "Captum"
        self.inputXAIframework = (torch.Tensor, torch.Tensor)
        self.outputXAIFramework = torch.Tensor
        self.clef = "c"
        self.methodes = {
            # Captum: Occlusion
            "Occlusion": ('o', [
                ("Window Size (X)        ", "wx", 25, "Size of the sliding window in the X dimension"),
                ("Window Size (Y)        ", "wy", 25, "Size of the sliding window in the Y dimension"),
                ("Stride Size            ", "sz", None, "Stride of the sliding window (defaults to window size)"),
                ("Baselines              ", "bs", None, "List of baseline predictions for comparison"),
                ("Number of Perturbations", "np", 1, "Number of times to apply the occlusion mask")
            ], "A perturbation based approach to compute attribution, involving replacing each contiguous rectangular region with a given baseline / reference, and computing the difference in output. For features located in multiple regions (hyperrectangles), the corresponding output differences are averaged to compute the attribution for that feature."),
            # Captum: Shapley Value Sampling
            "ShapleyValueSampling": ('s', [
                ("Number of Samples         ", "ns", 2500, "Number of samples to draw for Shapley value estimation"),
                ("Baselines                 ", "bs", None, "List of baseline predictions for comparison"),
                ("Masking Method            ", "mp", 0, {"options": ["Pixel_grid", "Watershed"]}, "Method for generating mask regions"),
                ("Number of Mask Pixels     ", "nm", 7, {"lien": ("csmp", [0])}, "Number of pixels to mask at a time"),
                ("Masking Threshold         ", "sl", 0, {"lien": ("csmp", [1])}, "Threshold for selecting pixels to mask"),
                ("Mask Transf. (Type)       ", "pt", 0, {"lien": ("csmp", [1]), "options": ["blur", "dilate", "erode", "none"]}, "Transformation to apply to the mask"),
                ("Mask Transf. (Kernel Size)", "ny", 3, {"lien": ("csmp", [1])}, "Kernel size for the mask transformation"),
                ("Number of Perturbations   ", "np", 1, "Number of times to apply the mask for each sample")
            ], "A perturbation based approach to compute attribution, based on the concept of Shapley Values from cooperative game theory. This method involves taking a random permutation of the input features and adding them one-by-one to the given baseline. The output difference after adding each feature corresponds to its attribution, and these difference are averaged when repeating this process n_samples times, each time choosing a new random permutation of the input features."),
            # Captum: LimeBase
            "LimeBase": ('b', [
                ("Similarity Function        ", "sf", "exp_embedding_cosine_distance", "Function to measure similarity between input and explanation"),
                ("Perturbation Function      ", "pf", "bernoulli_perturb", "Function to generate perturbations"),
                ("Perturb Interpretable Space", "ps", 1, {"options": ["False", "True"]}, "Flag to perturb in the interpretable space"),
                ("Input Transf. (From)       ", "it", "interp_to_input", "Transformation to apply before computing interpretability"),
                ("Input Transf. (To)         ", "rp", None, "Transformation to apply after computing interpretability (defaults to None)"),
                ("Masking Method             ", "mp", 0, {"options": ["Pixel_grid", "Watershed"]}, "Method for generating mask regions"),
                ("Number of Mask Pixels      ", "nm", 7, {"lien": ("cbmp", [0])}, "Number of pixels to mask at a time"),
                ("Masking Threshold          ", "sl", 0, {"lien": ("cbmp", [1])}, "Threshold for selecting pixels to mask"),
                ("Mask Transf. (Type)        ", "pt", 0, {"lien": ("cbmp", [1]), "options": ["blur", "dilate", "erode", "none"]}, "Transformation to apply to the mask"),
                ("Mask Trans. (Kernel Size)  ", "ny", 3, {"lien": ("cbmp", [1])}, "Kernel size for the mask transformation"),
                ("Number of Samples          ", "ns", 100000, "Number of samples to draw for explanation"),
                ("Number of Perturbations    ", "np", 1, "Number of times to apply the mask for each sample")
            ], "Lime is an interpretability method that trains an interpretable surrogate model by sampling points around a specified input example and using model evaluations at these points to train a simpler interpretable 'surrogate' model, such as a linear model."),
            # Captum: Lime
            "Lime": ('l', [
                ("Masking Method            ", "mp", 0, {"options": ["Pixel_grid", "Watershed"]}, "Method for generating mask regions"),
                ("Number of Mask Pixels     ", "nm", 7, {"lien": ("clmp", [0])}, "Number of pixels to mask at a time"),
                ("Masking Threshold         ", "sl", 0, {"lien": ("clmp", [1])}, "Threshold for selecting pixels to mask"),
                ("Mask Transf. (Type)       ", "pt", 0, {"lien": ("clmp", [1]), "options": ["blur", "dilate", "erode", "none"]}, "Transformation to apply to the mask"),
                ("Mask Transf. (Kernel Size)", "ny", 3, {"lien": ("clmp", [1])}, "Kernel size for the mask transformation"),
                ("Number of Samples         ", "ns", 100000, "Number of samples to draw for explanation"),
                ("Number of Perturbations   ", "np", 1, "Number of times to apply the mask for each sample")
            ], "Lime is an interpretability method that trains an interpretable surrogate model by sampling points around a specified input example and using model evaluations at these points to train a simpler interpretable 'surrogate' model, such as a linear model."),
            # Captum: Kernel Shap
            "KernelSHAP": ('k', [
                ("Number of Samples         ", "ns", 100000, "Number of samples for KernelSHAP estimation"),
                ("Baselines                 ", "bs", None, "List of baseline predictions for comparison"),
                ("Masking Method            ", "mp", 0, {"options": ["Pixel_grid", "Watershed"]}, "Method for generating mask regions"),
                ("Number of Mask Pixels     ", "nm", 7, {"lien": ("ckmp", [0])}, "Number of pixels to mask at a time"),
                ("Masking Threshold         ", "sl", 0, {"lien": ("ckmp", [1])}, "Threshold for selecting pixels to mask"),
                ("Mask Transf. (Type)       ", "pt", 0, {"lien": ("ckmp", [1]), "options": ["blur", "dilate", "erode", "none"]}, "Transformation to apply to the mask"),
                ("Mask Transf. (Kernel Size)", "ny", 3, {"lien": ("ckmp", [1])}, "Kernel size for the mask transformation"),
                ("Number of Perturbations   ", "np", 1, "Number of times to apply the mask for each sample"),
                ("Return Input shape        ", "ri", 1, {"options": ["False", "True"]}, "Flag to return input shape")
            ], "Kernel SHAP is a method that uses the LIME framework to compute Shapley Values. Setting the loss function, weighting kernel and regularization terms appropriately in the LIME framework allows theoretically obtaining Shapley Values more efficiently than directly computing Shapley Values."),
            # Captum: FeatureAblation
            "FeatureAblation": ('a', [
                ("Baselines                 ", "bs", None, "List of baseline predictions for comparison"),
                ("Masking Method            ", "mp", 0, {"options": ["Pixel_grid", "Watershed"]}, "Method for generating mask regions"),
                ("Number of Mask Pixels     ", "nm", 7, {"lien": ("camp", [0])}, "Number of pixels to mask at a time"),
                ("Masking Threshold         ", "sl", 0, {"lien": ("camp", [1])}, "Threshold for selecting pixels to mask"),
                ("Mask Transf. (Type)       ", "pt", 0, {"lien": ("camp", [1]), "options": ["blur", "dilate", "erode", "none"]}, "Transformation to apply to the mask"),
                ("Mask Transf. (Kernel Size)", "ny", 3, {"lien": ("camp", [1])}, "Kernel size for the mask transformation"),
                ("Number of Perturbations   ", "np", 1, "Number of times to apply the mask for each sample")
            ], "A perturbation based approach to computing attribution, involving replacing each input feature with a given baseline / reference, and computing the difference in output. By default, each scalar value within each input tensor is taken as a feature and replaced independently. Passing a feature mask, allows grouping features to be ablated together. This can be used in cases such as images, where an entire segment or region can be ablated, measuring the importance of the segment (feature group). Each input scalar in the group will be given the same attribution value equal to the change in target as a result of ablating the entire feature group."),
            # Captum: FeaturePermutation
            "FeaturePermutation": ('p', [
                ("Number of Mask Pixels  ", "nm", 7, "Number of pixels to mask at a time"),
                ("Number of Perturbations", "np", 1, "Number of times to apply the mask for each sample")
            ], "A perturbation based approach to compute attribution, which takes each input feature, permutes the feature values within a batch, and computes the difference between original and shuffled outputs for the given batch. This difference signifies the feature importance for the permuted feature.")
        }

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
            pDictParams = Captum_computeExplanations.computeExplanationsTexts(pDictParams)
        elif pDataType == "image":
            pDictParams = Captum_computeExplanations.computeExplanationsImages(pDictParams)
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

        if pDataType == "text":
            Captum_plotExplanations.plotExplanationsTexts(pDictParams, pFctExplainToPlot, pFctDataToPlot)
        elif pDataType == "image":
            Captum_plotExplanations.plotExplanationsImages(pDictParams, pFctExplainToPlot, pFctDataToPlot)

    # ---------------------------------------------------------------------------
    ## Write report function : generate a latex report of plots and other elements
    # @param pDictParams : parameter dictionary
    def XAI_writeReport(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']
        pRepertProd = pDictParams['repertProd']
        pDataProd = pDictParams['dataProd']

        if pDataType == "tabular":
            kaasrc.reports.writeReportTabText(pDictParams, pExtension="pkl")
        elif pDataType == "image":
            kaasrc.reports.writeReportImage(pDictParams, pExtension="pkl")
        else:
            colPrint("Quick report not available.","Info")
            resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
            kaasrc.reports.builtTGZ(resultSavedOn)

# ===============================================================================
# end of file
