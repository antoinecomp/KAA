#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os, json
import numpy as np

import kaasrc.plugin_collection
import kaasrc.communs

from . import UCRenaultWeldingResnet

# ------------------------------------------------------------------------------
## Classe Cas d'usage vs Bibliothèque
class UCRenaultWeldingResnet_Captum(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------------
    ## Constructeur de la classe de gestion des interfaces
    # @param self : l'instance de la classe
    def __init__(self):
        super().__init__()
        self.nom = "UCRenaultWeldingResnet"
        self.description = UCRenaultWeldingResnet.RenaultWeldingResnet.RenaultWeldingResnet.description
        self.modeles = ["Resnet"]
        self.bibliotheque = "Captum"
        self.methodes = ["FeatureAblation", "FeaturePermutation", "ShapleyValueSampling", "Occlusion", "KernelSHAP", "Lime"]
        self.metriques = None
        self.UC = UCRenaultWeldingResnet

    # ---------------------------------------------------------------------------
    ## Create an instance of the model
    # @param pDictParams : parameter dictionary
    # @return the instance of the model
    # @remark Call directly UC_createModel() of UC model
    def UCXAI_createModel(self, pDictParams):
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
    ## Compute metrics
    # @param pDictParams : dictionnaire des paramètres
    def UCXAI_computeMetrics(self, pDictParams):
        # shortcuts
        pDataProd = pDictParams['dataProd']
        pMetrique = pDictParams['metric']
        pMetricParam = pDictParams[pMetrique]
        pSuffixMetric = pDictParams["suffixMetric"]
        pNbData = pDictParams['nbData']
        _, aiModel = pDictParams['aiModel']
        xData, yPred = pDictParams['xy']

        if pDictParams['methods4metric'] == "":
            print("No method selected!")
            return
        pMethods4metric = pDictParams['methods4metric'].split(',')

        # compute
        print("   .get metric %s:%s"%(pDictParams['library'], pMetrique), flush=True)
        metricEvaluator = pDictParams['pluginXAI'].XAI_getMetricEvaluator(aiModel, xData.numpy()[:pNbData], yPred[:pNbData], pMetrique, pMetricParam)

        dicoExplainers = {}
        dicoExplanations = {}
        for methode in pMethods4metric:
            print("   .Metric on %s method"%methode, flush=True)
            pMethodParam = pDictParams[methode]
            dicoExplainers[methode] = pDictParams['pluginXAI'].XAI_getExplainer(aiModel, methode, pMethodParam)

            # construct subpath to store results
            repertProd = os.path.join(pDictParams['code'], "%s_%s"%(methode, pDictParams[methode]['suffixMethod']))
            # Load explanations
            dicoExplanations[methode] = None
            ficExplanation = os.path.join(pDataProd, "dataExplanations", repertProd, 'allData.npy')
            if not os.path.exists(ficExplanation):
                print("     -Le fichier d'explication '%s' n'existe pas."%ficExplanation, flush=True)
            else:
                explanations = np.load(ficExplanation)
                if len(explanations) < pNbData:
                    print("     -Le fichier d'explication ne contient pas assez de données: %d vs %d."%(len(explanations), pNbData), flush=True)
                else:
                    dicoExplanations[methode] = explanations[:pNbData]
        fichProd = os.path.join(pDataProd, "dataMetrics", pDictParams['code'], '%s_%s'%(pMetrique, pSuffixMetric))
        pDictParams['pluginXAI'].XAI_metricEvaluate(pMetrique, metricEvaluator, pMethods4metric, dicoExplainers, dicoExplanations, fichProd)

    # ---------------------------------------------------------------------------
    ## Plot of metrics
    # @param pDictParams : dictionnaire des paramètres
    def UCXAI_plotMetrics(self, pDictParams):
        # shortcuts
        pDataProd = pDictParams['dataProd']
        pMetrique = pDictParams['metric']
        pSuffixMetric = pDictParams["suffixMetric"]
        if pDictParams['methods4metric'] == "":
            print("No method selected!")
            return
        pMethods4metric = pDictParams['methods4metric'].split(',')

        fichierJson = os.path.join(pDataProd, "dataMetrics", pDictParams['code'], '%s_%s.json'%(pMetrique, pSuffixMetric))
        print("Metric results loaded from '%s'"%fichierJson)
        if not os.path.exists(fichierJson):
            print("ERROR: file '%s' does not exist !"%fichierJson)
            return
        with open(fichierJson, "r", encoding="utf-8") as f:
            results = json.load(f)
        f.close()

        # Plot metrics
        fichProd = os.path.join(pDataProd, "dataPlotExplanations", pDictParams['code'], '%s_%s'%(pMetrique, pSuffixMetric))
        pDictParams['pluginXAI'].XAI_metricPlot(pMetrique, pMethods4metric, results, fichProd)

    # ---------------------------------------------------------------------------
    ## Launch the report writing as contact sheet
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_writeReport() of XAI plugin
    def UCXAI_writeReport(self, pDictParams):
        pDictParams['pluginXAI'].XAI_writeReport(pDictParams)

# ===============================================================================
# end of file
