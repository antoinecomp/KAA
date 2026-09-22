#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os
import numpy as np
import inspect

import kaasrc.controles

from . import Captum_computeExplanations


# ---------------------------------------------------------------------------
## Plot of explanations
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsTexts(pDictParams, pFctExplainToPlot=None, pFctDataToPlot=None):
    # it's a function to associate a color to a number
    def give_color(nombre):
        list_colors = ['#FFFFFF', '#FAEDED', '#FADBDB', '#FBBDBD', '#FB9E9E', '#FC8080', '#FD6161', '#FD4343', '#FE2424', '#FE0606', '#FE0606']
        color = list_colors[min(int(nombre * 10), 10)]
        return color

    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pMethod = pDictParams['method']
    _, aiModel = pDictParams['aiModel']
    pData, _  = pDictParams['xy']

    xEmb = aiModel.useCase.embedding
    toti = 0
    xEmb_f = []
    for i, _ in enumerate(pData):
        if i == 0:
            xEmb_f.append(xEmb[:len(pData[0])])
            toti += len(pData[0])
        else:
            xEmb_f.append(xEmb[toti:toti + len(pData[i])])
            toti += len(pData[i])
    pData = xEmb_f

    # Lecture des explications
    repertProd = os.path.join(pDictParams['code'], "%s_%s"%(pMethod, pDictParams[pMethod]['suffixMethod']))
    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    for index in range(pNbData):

        dataName = pDataList[index]
        data = pData[index]

        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", repertProd), '%s.pkl'%dataName)
        oneExplanation = Captum_computeExplanations.loadExplanations(pDictParams, ficExplanation)
        if oneExplanation is None:
            return

        # Application d'une fonction pour le plot de l'explication
        if pFctExplainToPlot is not None:
            oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index)

        for eNbExp, vNbExp in enumerate(oneExplanation):
            pInput = data[eNbExp]
            explanations = vNbExp
            explanations = explanations.numpy()
            if np.any(explanations):
                explanations = (explanations - np.min(explanations)) / (np.max(explanations) - np.min(explanations))  # j'ai normalisé les vecteurs de poids
            list_highlightWords = []
            kaasrc.controles.NOcontrol_plotExplanationInput(pDictParams)

            for i in range(1, len(explanations[0])):
                token = aiModel.useCase.tokenizer.decode(pInput['input_ids'][i])
                list_highlightWords.append(f'<span style="background-color: {give_color(abs(explanations[0][i]))}">{token}</span>')

            # Save image
            ficPlot = kaasrc.communs.createDirName(resultSavedOn, "%s--i_%d.html"%(dataName, eNbExp))
            with open(ficPlot, mode='wt', encoding='utf-8') as f:
                f.write(' '.join(list_highlightWords))
            print("       saved in:", ficPlot, flush=True)

# ---------------------------------------------------------------------------
## Plot of explanations
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsImages(pDictParams, pFctExplainToPlot=None, pFctDataToPlot=None):
    # shortcuts
    pNbData = pDictParams['nbData']
    pDataPathList = pDictParams['dataPathList']
    pDataList = pDictParams['dataList']
    pData, _  = pDictParams['xy']
    _, aiModel = pDictParams['aiModel']
    pPlotDataSize = pDictParams['plotDataSize']
    pDataSize = pDictParams['datasize']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']
    outputXAIFramework = pDictParams['outputXAIFramework']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    # Boucle sur les données
    for index in range(pNbData):

        dataName = pDataList[index]
        data = pData[index]
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)

        # Lecture de l'explication de la donnée
        dirName = os.path.dirname(dataName)
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s.pkl'%os.path.basename(dataName))
        oneExplanation = Captum_computeExplanations.loadExplanations(pDictParams, ficExplanation)
        if oneExplanation is None:
            return

        # Application d'une fonction pour le plot de l'explication
        if pFctExplainToPlot is not None:
            oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index)
        else:
            oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, index)

        if pFctDataToPlot is not None:
            nbParams = len(inspect.signature(pFctDataToPlot).parameters)
            if nbParams == 2:
                data = pFctDataToPlot(pDictParams, pDataPathList[index])
            elif nbParams == 3:
                data = pFctDataToPlot(pDictParams, pDataPathList[index], index)
        else:
            data = kaasrc.communs.fctDataToPlotResized(pDictParams, data)

        # fonction de tracé
        pParamSpecif = {"explOutputDim": aiModel.useCase.numDataChannels, "dataSize": pDataSize[index]}
        kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)
        kaasrc.communs.plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, data, dataName)

# ===============================================================================
# end of file
