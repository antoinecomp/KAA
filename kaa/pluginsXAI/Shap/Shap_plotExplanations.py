#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os
import numpy as np
import matplotlib.pyplot as plt
import inspect

from kaasrc.communs import colPrint
import kaasrc.controles

from . import Shap_computeExplanations

# ---------
# To control the library version
versionPlugin = "0.41.0"
version = None
try:
    import shap
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Shap' is not or not properly installed.", "Error")
# ---------


# -------------------------------------------------------------------------------
## Plot explanation of a specific tabular data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the data
# @param pData : data to draw
# @param pIndexData :
# @param pDataName : data name for the filename of the image result
# @param pFeatureNames : list of feature names
# @param pClassNames : list of class names
# @param pIndexClass : index to the class to treat
# @param pMeanImpact : compute mean impact of feature
def _plotExplanationOneTable(pDictParams, pResultSavedOn, pExplanation, pData, pIndexData, pDataName, pFeatureNames, pClassNames, pIndexClass, pMeanImpact):
    # shortcuts
    pCmap = pDictParams["cmap"]
    _, aiModel = pDictParams['aiModel']
    outputXAIFramework = pDictParams['outputXAIFramework']

    # Plot tabular data
    plt.figure(facecolor='white', edgecolor='white')
    if pMeanImpact:
        plt.title("Mean impact of features on model output '%s'"%pClassNames[pIndexClass])
        plot_type = "bar"  # <= entraîne le calcul du mean(0)
        extension = "--s_mean"
    else:
        plt.title("Impact of features on model output '%s'"%pClassNames[pIndexClass])
        plot_type = "dot"  # dot violin layered_violin
        extension = ""

    if pClassNames[pIndexClass] == "":
        plot_type = "bar"

    pParamSpecif = {"dataSize": pDictParams['datasize'][pIndexData]}
    kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, None, pExplanation, None, aiModel.useCase, __file__, pParamSpecif)

    if not isinstance(pData, np.ndarray):
        pData = pData.numpy()
    shap.summary_plot(pExplanation, features=pData, feature_names=np.asarray(pFeatureNames), class_names=pClassNames, plot_type=plot_type, cmap=pCmap)
    plt.xlabel('')

    # Save image
    ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--c_%s%s.png"%(pDataName, pClassNames[pIndexClass], extension))
    plt.savefig(ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot, flush=True)
    plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of tabular data type
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsTables(pDictParams, pFctExplainToPlot=None, pFctDataToPlot=None):
    # shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pClasses = pDictParams['classes']
    pData, _ = pDictParams['xy']
    _, aiModel = pDictParams['aiModel']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    for index in range(pNbData):
        dataName = pDataList[index]
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)

        # Lecture des explications
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s.pkl'%dataName)
        oneExplanation = Shap_computeExplanations.loadExplanations(pDictParams, ficExplanation, index)
        if oneExplanation is None:
            return

        # Application d'une fonction pour le plot de l'explication
        if pFctExplainToPlot is not None:
            oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index)

        for oneClasse in range((len(pClasses))):
            _plotExplanationOneTable(pDictParams, resultSavedOn, oneExplanation[:, :, oneClasse], pData[index], index, dataName, aiModel.useCase.features, pClasses, oneClasse, True)
            _plotExplanationOneTable(pDictParams, resultSavedOn, oneExplanation[:, :, oneClasse], pData[index], index, dataName, aiModel.useCase.features, pClasses, oneClasse, False)

# -------------------------------------------------------------------------------
## Plot explanation of tabular data type
# @param pExplanation : explanations of the text
# @param pDataName : data name for the filename of the result
# @param pResultSavedOn : path to save result
# @param pItem : item in text dataset to explain
def _plotExplanationsOneText(pExplanation, pDataName, pResultSavedOn, pItem):
    ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--i_%s.html"%(pDataName, pItem))
    with open(ficPlot, 'w', encoding="utf-8") as file:
        file.write(shap.text_plot(pExplanation, display=False))
    print("       saved in:", ficPlot, flush=True)

# -------------------------------------------------------------------------------
## Plot explanation of tabular data type
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsTexts(pDictParams, pFctExplainToPlot=None, pFctDataToPlot=None):
    # shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']
    xData, _ = pDictParams['xy']
    outputXAIFramework = pDictParams['outputXAIFramework']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    for index in range(pNbData):
        dataName = pDataList[index]
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)

        # Lecture des explications
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s.pkl'%dataName)
        oneExplanation = Shap_computeExplanations.loadExplanations(pDictParams, ficExplanation, pNbData)
        if oneExplanation is None:
            return

        for item, _ in enumerate(xData[index]):
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, None, oneExplanation, None, pDictParams['datasize'][index], aiModel.useCase, __file__)
            _plotExplanationsOneText(oneExplanation[item], dataName, resultSavedOn, item)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the image
# @param pData : image to show
# @param pDataName : data name for the filename of the image result
def _plotExplanationOnImage(pDictParams, pResultSavedOn, pExplanation, pData, pDataName):
    # shortcuts
    pPlotDataSize = pDictParams['plotDataSize']

    shap.plots.image(pExplanation, pixel_values=pData, labels=pDictParams['classes'], show=False)

    # Extension Data size
    txtDataSize = ""
    if pPlotDataSize == 1:
        txtDataSize = "--datasize"
        print("       plot with original data shape", flush=True)
    else:
        print("       plot with model input data shape", flush=True)

    # Save image
    ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s%s.png"%(pDataName, txtDataSize))
    plt.savefig(ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot, flush=True)
    plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of image data
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsImages(pDictParams, pFctExplainToPlot, pFctDataToPlot):
    # shortcuts
    pNbData = pDictParams['nbData']
    pDataPathList = pDictParams['dataPathList']
    pDataBandPathList = pDictParams['dataBandPathList']
    pDataList = pDictParams['dataList']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']
    pData, _ = pDictParams['xy']
    _, aiModel = pDictParams['aiModel']
    pPlotDataSize = pDictParams['plotDataSize']
    pDataSize = pDictParams['datasize']

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
        oneExplanation = Shap_computeExplanations.loadExplanations(pDictParams, ficExplanation, 1)
        if oneExplanation is None:
            return
        # Ajout>
        oneExplanation = [oneExplanation.values[..., i] for i in range(oneExplanation.values.shape[-1])]

        # Application d'une fonction pour le plot de l'explication
        if pFctExplainToPlot is not None:
            oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index)
        # Ajout>
        else:
            oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, index)

        # Application d'une fonction pour le plot de la donnée
        if pFctDataToPlot is not None and pDataBandPathList is not None:
            for fileDataBand in pDataBandPathList[index]:
                dataName, _ = os.path.splitext(os.path.basename(fileDataBand))
                dataName = os.path.join(dirName, dataName)
                if pFctDataToPlot is not None:
                    data = pFctDataToPlot(pDictParams, fileDataBand)
                else:
                    data = kaasrc.communs.fctDataToPlotResized(pDictParams, data)

                # contrôle
                pParamSpecif = {"dataSize": pDataSize[index], "nbBands": aiModel.useCase.numImageChannels, "explOutputDim": aiModel.useCase.numDataChannels}
                kaasrc.controles.control_plotExplanationInput(pDictParams, list, pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)
                # tracé
                _plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, data, dataName)
        else:
            if pFctDataToPlot is not None:
                nbParams = len(inspect.signature(pFctDataToPlot).parameters)
                if nbParams == 2:
                    data = pFctDataToPlot(pDictParams, pDataPathList[index])
                elif nbParams == 3:
                    data = pFctDataToPlot(pDictParams, pDataPathList[index], index)
            else:
                data = kaasrc.communs.fctDataToPlotResized(pDictParams, data)

            # contrôle
            pParamSpecif = {"dataSize": pDataSize[index], "nbBands": aiModel.useCase.numImageChannels, "explOutputDim": aiModel.useCase.numDataChannels}
            kaasrc.controles.control_plotExplanationInput(pDictParams, list, pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)
            # tracé
            _plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, data, dataName)

# ===============================================================================
# end of file
