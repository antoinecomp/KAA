#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os

from kaasrc.communs import colPrint
import kaasrc.plugin_collection

from . import Xplique_computeExplanations
from . import Xplique_plotExplanations
from . import Xplique_computeMetrics
from . import Xplique_plotMetrics

# ---------
try:
    import tensorflow.python.framework.ops as eTensor
except Exception as err:
    print("Error:", err)
    colPrint("Package tensorflow is not or not properly installed.", "Error")
# ---------
# To control the library version
#versionPlugin = "1.3.3"  # v24.09
versionPlugin = "1.4.0"  # v25.09
version = None
try:
    from xplique import __version__
    version = __version__
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Xplique' is not or not properly installed.", "Error")
# ---------


# -------------------------------------------------------------------------------
## Function that check if a class has a member function
# @param pClass : the class to inspect
# @param pFunction : the function to check
def has_method(pClass, pFunction):
    return callable(getattr(pClass, pFunction, None))

# -------------------------------------------------------------------------------
class Xplique(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.nom = "Xplique"
        self.description = "Xplique DEEL"
        self.inputXAIframework = (eTensor.EagerTensor, eTensor.EagerTensor)
        self.outputXAIFramework = eTensor.EagerTensor
        self.clef = "x"
        self.methodes = {
            # Xplique:KernelShap
            "KernelShap": ('k', [
                ("Batch size            ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Number of samples     ", "ns", 800, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources."),
                ("Ref.value             ", "rv", 0, "It defines reference value which replaces each feature when the corresponding interpretable feature is set to 0. It should be provided as: a ndarray of shape (1) if there is no channels in your input and (C, ) otherwise."),
                ("Mega pixels           ", "mp", 0, {"options": ["Quickshift", "Watershed"]}, "Function which group features of an input corresponding to the same interpretable feature."),
                ("Threshold Mega pixels ", "sl", 0, {"lien": ("xkmp", [1])}, "Threshold for Mega pixels"),
                ("Mega pixels processing", "pt", 0, {"lien": ("xkmp", [1]), "options": ["blur", "dilate", "erode", "none"]}, "Processing method for Mega pixels"),
                ("Kernel Mega pixels    ", "ny", 3, {"lien": ("xkmp", [1])}, "Kernel size for Mega pixels")
            ], "By setting appropriately the perturbation function, the similarity kernel and the interpretable model in the LIME framework we can theoretically obtain the Shapley Values more efficiently. Therefore, KernelShap is a method based on LIME with specific attributes."),
            # Xplique:Occlusion
            "Occlusion": ('o', [
                ("Batch size     ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Patch size     ", "pz", 3, "Size of the patches to apply, if integer then assume an hypercube. It depends to the size of the object we want to detect. If the object is small you will have to fix it to a small value and vice versa."),
                ("Patch stride   ", "ps", 3, "Stride between two patches, if integer then assume an hypercube. It must be smaller than the patch size."),
                ("Occlusion Value", "ov", 0.5, "Value used as occlusion.")
            ], "Used to compute the Occlusion sensitivity method, sweep a patch that occludes pixels over the images and use the variations of the model prediction to deduce critical areas."),
            # Xplique:Rise
            "Rise": ('r', [
                ("Batch size          ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Number of samples   ", "ns", 150, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources."),
                ("Grid size           ", "gz", 7, "Size of the grid used to generate the scaled-down masks. Masks are then rescale to and cropped to input_size. Can be a tuple for different cutting depending on the dimension. Ignored for tabular data. Depends of the size of the class we want to detect. If the object is small you will have to fix it to a big value and vice versa."),
                ("Presence probability", "pp", 0.5, "Probability of preservation for each pixel (or the percentage of non-masked pixels in each masks), also the expectation value of the mask.")
            ], "Used to compute the RISE method, by probing the model with randomly masked versions of the input image and obtaining the corresponding outputs to deduce critical areas."),
            # Xplique:Lime
            "Lime": ('l', [
                ("Batch size            ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Number of samples     ", "ns", 150, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources."),
                ("Ref.value             ", "rv", 0, "It defines reference value which replaces each feature when the corresponding interpretable feature is set to 0. It should be provided as: a ndarray of shape (1) if there is no channels in your input and (C, ) otherwise."),
                ("Distance mode         ", "dm", 1, {"options": ["cosine", "euclidean"]}, "The distance mode used in the default similarity kernel, you can choose either 'euclidean' or 'cosine' (will compute cosine similarity)."),
                ("Kernel width          ", "kw", 45.0, "Width of your kernel. It is important to make it evolving depending on your inputs size otherwise you will get all similarity close to 0 leading to poor performance or NaN values."),
                ("Presence probability  ", "pp", 0.5, "Probability of preservation for each pixel (or the percentage of non-masked pixels in each masks), also the expectation value of the mask."),
                ("Mega pixels           ", "mp", 0, {"options": ["Quickshift", "Watershed"]}, "Function which group features of an input corresponding to the same interpretable feature."),
                ("Threshold Mega pixels ", "sl", 0, {"lien": ("xlmp", [1])}, "Threshold for Mega pixels"),
                ("Mega pixels processing", "pt", 0, {"lien": ("xlmp", [1]), "options": ["blur", "dilate", "erode", "none"]}, "Processing method for Mega pixels"),
                ("Kernel Mega pixels    ", "ny", 3, {"lien": ("xlmp", [1])}, "Kernel size for Mega pixels")
            ], "Used to compute the LIME method."),
            # Xplique:IntegratedGradients
            "IntegratedGradients": ('n', [
                ("Batch size     ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Number of steps", "ns", 50, "Number of points to interpolate between the baseline and the desired point."),
                ("Baseline       ", "bl", 0.0, "Scalar used to create the baseline point.")
            ], "Used to compute the Integrated Gradients, by cumulating the gradients along a path from a baseline to the desired point."),
            # Xplique:SmoothGrad
            "SmoothGrad": ('a', [
                ("Batch size       ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Number of samples", "ns", 50, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources."),
                ("Noise            ", "nz", 0.2, "Scalar, noise used as standard deviation of a normal law centered on zero.")
            ], "Used to compute the SmoothGrad, by averaging Saliency maps of noisy samples centered on the original sample."),
            # Xplique:VarGrad
            "VarGrad": ('v', [
                ("Batch size       ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Number of samples", "ns", 50, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources."),
                ("Noise            ", "nz", 0.2, "Scalar, noise used as standard deviation of a normal law centered on zero.")
            ], "VarGrad is a variance analog to SmoothGrad."),
            # Xplique:SquareGrad
            "SquareGrad": ('q', [
                ("Batch size       ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Number of samples", "ns", 50, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources."),
                ("Noise            ", "nz", 0.2, "Scalar, noise used as standard deviation of a normal law centered on zero.")
            ], "SquareGrad (or SmoothGrad$^2$) is an unpublished variant of classic SmoothGrad which squares each gradients of the noisy inputs before averaging."),
            # Xplique:GuidedBackprop
            "GuidedBackprop": ('g', [
                ("Batch size", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources.")
            ], "Used to compute the Guided Backpropagation, which modifies the classic Saliency procedure on ReLU's non linearities, allowing only the positive gradients from positive activations to pass through."),
            # Xplique:DeconvNet
            "DeconvNet": ('e', [
                ("Batch size", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources.")
            ], "Used to compute the DeconvNet method, which modifies the classic Saliency procedure on ReLU's non linearities, allowing only the positive gradients (even from negative inputs) to pass through."),
            # Xplique:GradientInput
            "GradientInput": ('t', [
                ("Batch size", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources.")
            ], "Used to compute elementwise product between the saliency maps and the input (Gradient x Input)."),
            # Xplique:Saliency
            "Saliency": ('y', [
                ("Batch size", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources.")
            ], "Used to compute the absolute gradient of the output relative to the input."),
            # Xplique:Sobol
            "Sobol": ('b', [
                ("Batch size           ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Grid size            ", "gz", 7, "Size of the grid used to generate the scaled-down masks. Masks are then rescale to and cropped to input_size. Can be a tuple for different cutting depending on the dimension. Ignored for tabular data. Depends of the size of the class we want to detect. If the object is small you will have to fix it to a big value and vice versa."),
                ("Number of designs    ", "nd", 32, "Number of design for the sampler"),
                ("Perturbation function", "fp", 2, {"options": ["amplitude", "blurring", "inpainting"]}, "Function which generate perturbed interpretable samples in the interpretation space from the number of interpretable features (e.g nb of super pixel) and the number of perturbed samples you want per original input.")
            ], "Compute the total order Sobol' indices using a perturbation function on a grid and an adapted sampling as described in the original paper."),
            # Xplique:Hsic
            "Hsic": ('h', [
                ("Batch size           ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Grid size            ", "gz", 7, "Size of the grid used to generate the scaled-down masks. Masks are then rescale to and cropped to input_size. Can be a tuple for different cutting depending on the dimension. Ignored for tabular data. Depends of the size of the class we want to detect. If the object is small you will have to fix it to a big value and vice versa."),
                ("Number of designs    ", "nd", 500, "Number of design for the sampler"),
                ("Perturbation function", "fp", 2, {"options": ["amplitude", "blurring", "inpainting"]}, "Function which generate perturbed interpretable samples in the interpretation space from the number of interpretable features (e.g nb of super pixel) and the number of perturbed samples you want per original input.")
            ], "Compute the dependance of each input dimension wrt the output using Hilbert-Schmidt Independance Criterion, a perturbation function on a grid and an adapted sampling as described in the original paper.")
        }
        self.metriques = {
            "CausalFidelity-Deletion": ('d', [
                ("Batch size       ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Baseline mode    ", "bm", 0.0, "Baseline mode"),
                ("Steps            ", "st", 10, "Number of points to interpolate between the baseline and the desired point."),
                ("Percent perturbed", "pp", 1.0, "Percent of input perturbed")
            ], "The deletion metric measures the drop in the probability of a class as important input features given by the explanation method (ex: important pixels) are gradually removed from the input (ex: image). A sharp drop, and thus a small area under the probability curve, are indicative of a good explanation."),
            "CausalFidelity-Insertion": ('i', [
                ("Batch size       ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Baseline mode    ", "bm", 0.0, "Baseline mode"),
                ("Steps            ", "st", 10, "Number of points to interpolate between the baseline and the desired point."),
                ("Percent perturbed", "pp", 1.0, "Percent of input perturbed")
            ], "The insertion metric captures the importance of the input features (ex:pixels) in terms of their ability to synthesize the input (ex: image) and is measured by the rise in the probability of the class of interest as input features (ex:pixels) are added according to the generated importance map."),
            "AverageStability": ('s', [
                ("Batch size       ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Radius           ", "rd", 0.1, "Radius"),
                ("Distance         ", "ds", 'l2', "Distance metric"),
                ("Number of samples", "ns", 150, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources.")
            ], "Used to compute the average sensitivity metric (or stability). This metric ensure that close inputs with similar predictions yields similar explanations. For each inputs we randomly sample noise to add to the inputs and compute the explanation for the noisy inputs. We then get the average distance between the original explanations and the noisy explanations."),
            "MuFidelity": ('f', [
                ("Batch size       ", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("Grid size        ", "gz", 9, "Size of the grid used to generate the scaled-down masks. Masks are then rescale to and cropped to input_size. Can be a tuple for different cutting depending on the dimension. Ignored for tabular data. Depends of the size of the class we want to detect. If the object is small you will have to fix it to a big value and vice versa."),
                ("Subset percentage", "sp", 0.2, "Subset percentage"),
                ("Baseline mode    ", "bm", 0.0, "Baseline mode"),
                ("Number of samples", "ns", 150, "Number of masks generated for Monte Carlo sampling. If too small the explanation will not converge. To test, if well defined you can increase the number and if the explanation not change your initial number is correct. If you fix a big number it will take lot of time and resources.")
            ], "Used to compute the fidelity correlation metric. This metric ensure there is a correlation between a random subset of input features (ex:pixels) and their attribution score. For each random subset created, we set the input features (ex:pixels) of the subset at a baseline state and obtain the prediction score. This metric measures the correlation between the drop in the score and the importance of the explanation."),
            "MeGe": ('m', [
                ("Batch size", "bz", 64, "Number of inputs to explain at once, if None compute all at once. If the batch size is higher, it takes less time to compute but required more resources."),
                ("K splits  ", "ks", 4, "Number of splits")
            ], "Used to compute the representativity of explanations. MeGe gives you an overview of the generalization of your explanations: how much seeing one explanation informs you about the others.")
        }

    # ---------------------------------------------------------------------------
    ## Compute explanations
    # @param pDictParams : parameter dictionary
    # @param pExplainClasses : Boolean to indicate if classes have to be treated
    # @return parameter dictionary
    def XAI_computeExplanations(self, pDictParams, pExplainClasses=True):
        # shortcuts
        pDataType = pDictParams['datatype']
        pModelType = pDictParams['modeltype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        if pDataType == "tabular":
            pDictParams = Xplique_computeExplanations.computeExplanationsTabText(pDictParams, pExplainClasses)
        elif pDataType == "image":
            if pModelType == "detection":
                pDictParams = Xplique_computeExplanations.computeExplanationsObjDetection(pDictParams)
            elif pModelType == "segmentation":
                pDictParams = Xplique_computeExplanations.computeExplanationsObjSegmentation(pDictParams)
            else:
                pDictParams = Xplique_computeExplanations.computeExplanationsImage(pDictParams)
        return pDictParams

    # -------------------------------------------------------------------------------
    ## Plot explanations
    # @param pDictParams : parameter dictionary
    # @param pClass : class to treat
    # @param pItem : item to treat
    # @param pFctExplainToPlot : function to apply to explaination before plotting
    # @param pFctDataToPlot : function to apply to data before plotting
    def XAI_plotExplanations(self, pDictParams, pClass=None, pItem=None, pFctExplainToPlot=None, pFctDataToPlot=None):
        # shortcuts
        pDataType = pDictParams['datatype']
        pModeltype = pDictParams['modeltype']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        # Tracé
        if pDataType == "tabular":
            Xplique_plotExplanations.plotExplanationsTabText(pDictParams, pFctExplainToPlot, pFctDataToPlot)
        elif pDataType == "image":
            if pModeltype == "detection":
                Xplique_plotExplanations.plotExplanationsObjDetection(pDictParams, pFctExplainToPlot, pFctDataToPlot)
            elif pModeltype == "segmentation":
                Xplique_plotExplanations.plotExplanationsObjSegmentation(pDictParams, pFctExplainToPlot, pFctDataToPlot)
            else:
                Xplique_plotExplanations.plotExplanationsImage(pDictParams, pFctExplainToPlot, pFctDataToPlot)

    # ---------------------------------------------------------------------------
    ## Compute metrics
    # @param pDictParams : parameter dictionary
    def XAI_computeMetrics(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']
        pModelType = pDictParams['modeltype']
        xData, yPred = pDictParams['xy']

        # recording XAI framework for transmission in case of specific previous modifications
        pDictParams['inputXAIframework'] = self.inputXAIframework
        pDictParams['outputXAIFramework'] = self.outputXAIFramework

        # convert data and prediction to XAI framework
        xData, yPred = kaasrc.communs.convertToXAIframework(pDictParams, self.inputXAIframework)
        pDictParams['xy'] = xData, yPred

        if pDataType == "tabular":
            Xplique_computeMetrics.computeMetricsTabText(pDictParams)
        elif pDataType == "image":
            if pModelType == "detection":
                Xplique_computeMetrics.computeMetricsObjDetection(pDictParams)
            elif pModelType == "segmentation":
                Xplique_computeMetrics.computeMetricsObjSegmentation(pDictParams)
            else:
                Xplique_computeMetrics.computeMetricsImage(pDictParams)

    # ---------------------------------------------------------------------------
    ## Plot metric results
    # @param pDictParams : parameter dictionary
    def XAI_plotMetrics(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']

        if pDataType == "tabular":
            Xplique_plotMetrics.plotMetricsTabText(pDictParams)
        else:
            Xplique_plotMetrics.plotMetricsImage(pDictParams)

    # -------------------------------------------------------------------------------
    ## Write report function : generate a latex report of plots and other elements
    # @param pDictParams : parameter dictionary
    def XAI_writeReport(self, pDictParams):
        # shortcuts
        pDataType = pDictParams['datatype']
        pModeltype = pDictParams['modeltype']
        pRepertProd = pDictParams['repertProd']
        pDataProd = pDictParams['dataProd']

        if pDataType == "tabular":
            kaasrc.reports.writeReportTabText(pDictParams, pClasses=pDictParams['classes'], pSuffixes=["", "mean"])
        elif pDataType == "image":
            if pModeltype == "detection":
                kaasrc.reports.writeReportObjDetection(pDictParams)
            elif pModeltype == "segmentation":
                kaasrc.reports.writeReportObjSegmentation(pDictParams)
            else:
                kaasrc.reports.writeReportImage(pDictParams)
        else:
            colPrint("Quick report not available.","Info")
            resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
            kaasrc.reports.builtTGZ(resultSavedOn)

# ===============================================================================
# end of file
