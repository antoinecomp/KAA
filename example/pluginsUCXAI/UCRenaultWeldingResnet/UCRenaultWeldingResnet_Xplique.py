#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import kaasrc.plugin_collection
import kaasrc.communs

from . import UCRenaultWeldingResnet

# ------------------------------------------------------------------------------
## Class for Use case vs Library
class UCRenaultWeldingResnet_Xplique(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------------
    ## Class constructor
    # @param self : l'instance de la classe
    def __init__(self):
        super().__init__()
        self.nom = "UCRenaultWeldingResnet"
        self.description = UCRenaultWeldingResnet.RenaultWeldingResnet.RenaultWeldingResnet.description
        self.modeles = ["Resnet"]
        self.bibliotheque = "Xplique"
        self.methodes = ["Hsic", "KernelShap", "Lime", "Occlusion", "Rise", "Sobol"]
        self.metriques = ["CausalFidelity-Deletion", "CausalFidelity-Insertion", "AverageStability", "MuFidelity"]
        self.UC = UCRenaultWeldingResnet

    # ---------------------------------------------------------------------------
    ## Create an instance of the model
    # @param pDictParams : parameter dictionary
    # @return the instance of the model
    # @remark Call directly UC_createModel() of UC model
    def UCXAI_createModel(self, pDictParams):
        if hasattr(self.UC.RenaultWeldingResnet.RenaultWeldingResnet, 'predict_proba'):
            delattr(self.UC.RenaultWeldingResnet.RenaultWeldingResnet, 'predict_proba')
        return self.UC.UC_createModel(pDictParams)

    # ---------------------------------------------------------------------------
    ## Compute the data inference with model
    # @param pAiModel : model instance
    # @param pDictParams : parameter dictionary
    # @return data, prediction, list of inference error against truth
    # @remark Call directly UC_computeInference() of UC model
    def UCXAI_computeInference(self, pAiModel, pDictParams):
        return self.UC.UC_computeInference(pAiModel, pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the explanations computation
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_computeExplanations() of XAI plugin
    def UCXAI_computeExplanations(self, pDictParams):
        pDictParams['pluginXAI'].XAI_computeExplanations(pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the explanations plotting
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_plotExplanations() of XAI plugin
    def UCXAI_plotExplanations(self, pDictParams):
        pDictParams['pluginXAI'].XAI_plotExplanations(pDictParams, pFctExplainToPlot=None, pFctDataToPlot=self.UC.UC_ImageDataToPlot)

    # ---------------------------------------------------------------------------
    ## Launch the metrics computation
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_computeMetrics() of XAI plugin
    def UCXAI_computeMetrics(self, pDictParams):
        pDictParams['pluginXAI'].XAI_computeMetrics(pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the metrics plotting
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_plotMetrics() of XAI plugin
    def UCXAI_plotMetrics(self, pDictParams):
        pDictParams['pluginXAI'].XAI_plotMetrics(pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the report writing as contact sheet
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_writeReport() of XAI plugin
    def UCXAI_writeReport(self, pDictParams):
        pDictParams['pluginXAI'].XAI_writeReport(pDictParams)

# ===============================================================================
# end of file
