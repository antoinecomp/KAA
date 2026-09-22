#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os
import numpy as np
import matplotlib.pyplot as plt
import inspect

from kaasrc.communs import colPrint
import kaasrc.controles

from . import PAIRsaliency_computeExplanations

# ---------
# To control the library version
versionPlugin = "0.2.0-c"
version = None
try:
    from saliency import version
    version = version.version
except Exception as err:
    print("Error:", err)
    colPrint("The library 'PAIRsaliency' is not or not properly installed.", "Error")
# ---------


# -------------------------------------------------------------------------------
## Plot explanation of image data
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsImage(pDictParams, pFctExplainToPlot, pFctDataToPlot):
    # shortcuts
    pNbData = pDictParams['nbData']
    pDataPathList = pDictParams['dataPathList']
    pDataBandPathList = pDictParams['dataBandPathList']
    pDataList = pDictParams['dataList']
    pData, _ = pDictParams['xy']
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
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s.npy'%os.path.basename(dataName))
        oneExplanation = PAIRsaliency_computeExplanations.loadExplanations(pDictParams, ficExplanation, 1)
        if oneExplanation is None:
            return
        oneExplanation = np.squeeze(oneExplanation, axis=-1)

        # Application d'une fonction pour le plot de l'explication
        if pFctExplainToPlot is not None:
            oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index)
        else:
            oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, index)

        # Application d'une fonction pour le plot de la donnée
        if pFctDataToPlot is not None and pDataBandPathList is not None:
            for fileDataBand in pDataBandPathList[index]:
                dataName, _ = os.path.splitext(os.path.basename(fileDataBand))
                dataName = os.path.join(dirName, dataName)
                data = pFctDataToPlot(pDictParams, fileDataBand)

                # fonction de tracé
                pParamSpecif = {"explOutputDim": None, "dataSize": pDataSize[index]}
                kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)
                kaasrc.communs.plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, data, dataName)
        else:
            if pFctDataToPlot is not None:
                nbParams = len(inspect.signature(pFctDataToPlot).parameters)
                if nbParams == 2:
                    data = pFctDataToPlot(pDictParams, pDataPathList[index])
                elif nbParams == 3:
                    data = pFctDataToPlot(pDictParams, pDataPathList[index], index)
            else:
                data = kaasrc.communs.fctDataToPlotResized(pDictParams, data)

            # fonction de tracé
            pParamSpecif = {"explOutputDim": None, "dataSize": pDataSize[index]}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)
            kaasrc.communs.plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, data, dataName)

# -------------------------------------------------------------------------------
## Plot a tabular explaination
# @param pDictParams : parameter dictionary
# @param pFicExplanation : filename of saved explanation
# @param pIndexData : index of the data to construct result filename
# @param pDataName : data file name
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
# @param pClasse : class name to treat or empty string to plot for all classes
def _plotExplanationOneTable(pDictParams, pFicExplanation, pIndexData, pDataName, pFctExplainToPlot, pFctDataToPlot, pClasse=""):
    # shortcuts
    pFeatureNames = pDictParams['aiModel'][1].useCase.features
    _, aiModel = pDictParams['aiModel']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
    outputXAIFramework = pDictParams['outputXAIFramework']

    oneExplanation = PAIRsaliency_computeExplanations.loadExplanations(pDictParams, pFicExplanation, pIndexData)
    if oneExplanation is None:
        return

    # Application d'une fonction pour le plot de l'explication
    if pFctExplainToPlot is not None:
        oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation)

    explanations = np.array(oneExplanation)
    explanations = np.mean(explanations, axis=0)
    if pFeatureNames is None:
        pFeatureNames = ['Feature %d'%k for k in range(explanations.shape[0])]

    pParamSpecif = {"dataSize": pDictParams['datasize'][pIndexData]}
    kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)

    # Plot
    fig, axes = plt.subplots(facecolor='white', edgecolor='white')
    bbox = axes.get_window_extent().transformed(fig.dpi_scale_trans.inverted())

    colors = np.where(explanations <= 0, 'slateblue', 'yellowgreen')
    y_pos = np.arange(len(pFeatureNames))
    axes.barh(y_pos, explanations, align='center', color=colors)
    xlen = plt.xlim()[1] - plt.xlim()[0]
    xscale = xlen / bbox.width
    for i in y_pos:
        if explanations[i] < 0:
            exp_sgn = -1
            horizontalalignment = 'right'
        else:
            exp_sgn = 1
            horizontalalignment = 'left'
        axes.text(explanations[i] + exp_sgn * 0.02 * xscale, y_pos[i], f"{str(round(explanations[i], 2))}",
                 horizontalalignment=horizontalalignment, verticalalignment='center', fontsize=10)
    plt.axvline(0, 0, 1, color="dimgray", linestyle="-", linewidth=1)
    axes.set_xlabel('Impact on output')
    axes.set_ylabel('')
    if pClasse == "":
        axes.set_title('Mean impact of features')
        extension = "--s_mean"
    else:
        axes.set_title('Mean impact of features on class %s'%pClasse)
        extension = "--c_%s--s_mean"%pClasse

    axes.set_yticks(y_pos)
    axes.set_yticklabels(pFeatureNames)

    # Save image
    ficData = os.path.basename(pDataName)
    dirName = os.path.dirname(pDataName)
    ficPlot = kaasrc.communs.createDirName(resultSavedOn, os.path.join(dirName, "%s%s.png"%(ficData, extension)))
    plt.savefig(ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot)
    plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of tablular data
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsTable(pDictParams, pFctExplainToPlot, pFctDataToPlot):
    # shortcuts
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pClasses = pDictParams['classes']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']

    # Boucle sur les données
    for index in range(pNbData):
        dataName = pDataList[index]
        dirName = os.path.dirname(dataName)
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)

        # fonction de tracé
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s.npy'%os.path.basename(dataName))
        _plotExplanationOneTable(pDictParams, ficExplanation, index, dataName, pFctExplainToPlot, pFctDataToPlot)

        for n, _ in enumerate(pClasses):
            print("      class:", pClasses[n], flush=True)
            ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s--c_%s.npy'%(dataName, pClasses[n]))
            if os.path.exists(ficExplanation):
                _plotExplanationOneTable(pDictParams, ficExplanation, index, dataName, pFctExplainToPlot, pFctDataToPlot, pClasses[n])

# ===============================================================================
# end of file
