#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os, json
import numpy as np
import matplotlib.pyplot as plt
import inspect

from kaasrc.communs import colPrint
import kaasrc.controles

from . import Xplique_computeExplanations

# ---------
try:
    import tensorflow.compat.v2 as tf
except Exception as err:
    print("Error:", err)
    colPrint("Package tensorflow is not or not properly installed.", "Error")
# ---------
try:
    from xplique.plots.tabular import summary_plot_tabular, plot_mean_feature_impact
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Xplique' is not or not properly installed.", "Error")
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
        dirName = os.path.dirname(dataName)
        data = pData[index]
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)

        # Lecture de l'explication de la donnée
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s.npy'%os.path.basename(dataName))
        oneExplanation = Xplique_computeExplanations.loadExplanations(pDictParams, ficExplanation)
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
## Plot explanation of image detection problem
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsObjDetection(pDictParams, pFctExplainToPlot, pFctDataToPlot):
    # shortcuts
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pDataPathList = pDictParams['dataPathList']
    pData, _ = pDictParams['xy']
    _, aiModel = pDictParams['aiModel']
    pPlotDataSize = pDictParams['plotDataSize']
    pDataSize = pDictParams['datasize']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']

    outputXAIFramework = pDictParams['outputXAIFramework']

    pDictParams = kaasrc.communs.updateListObjects(pDictParams)
    pListObjets = pDictParams['objets']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    # Boucle sur les données
    for index in range(pNbData):
        dataName = pDataList[index]
        dirName = os.path.dirname(dataName)
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)
        # Boucle sur les objets
        for objet in pListObjets[dataName]:

            # Lecture des informations collectées à l'inférence
            ficInference = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataInference", pRepertProd, dirName), '%s--i_%d.json'%(os.path.basename(dataName), objet))
            with open(ficInference, "r", encoding="utf-8") as json_data:
                jsonInference = json.load(json_data)

            # Lecture de l'explication de la donnée
            ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s--i_%d.npy'%(os.path.basename(dataName), objet))
            oneExplanation = Xplique_computeExplanations.loadExplanations(pDictParams, ficExplanation)
            if oneExplanation is None:
                return
            oneExplanation = np.swapaxes(oneExplanation, 0, 1)
            oneExplanation = np.squeeze(oneExplanation, axis=-1)

            # Application d'une fonction pour le plot de l'explication
            if pFctExplainToPlot is not None:
                oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index, objet)
            else:
                oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, index)

            data = pData[index]
            # Application d'une fonction pour le plot de la donnée
            if pFctDataToPlot is not None:
                data = pFctDataToPlot(pDictParams, pDataPathList[index], jsonInference["prediction"][0])
            else:
                data = kaasrc.communs.fctDataToPlotResized(pDictParams, data)

            # Contrôle
            pParamSpecif = {"explOutputDim": None, "dataSize": pDataSize[index]}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)
            # Tracé
            kaasrc.communs.plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, data, dataName, "--i_%d"%objet)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsObjSegmentation(pDictParams, pFctExplainToPlot, pFctDataToPlot):
    # shortcuts
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pDataPathList = pDictParams['dataPathList']
    pClasses = pDictParams['classes']
    _, aiModel = pDictParams['aiModel']
    pDataSize = pDictParams['datasize']
    pPlotDataSize = pDictParams['plotDataSize']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']

    outputXAIFramework = pDictParams['outputXAIFramework']
    pDictParams = kaasrc.communs.updateListObjects(pDictParams)
    pListObjets = pDictParams['objets']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    # Tracé
    for index in range(pNbData):
        dataName = pDataList[index]
        print("   .plot Explain #%d"%index, flush=True)
        print("       data: %s"%dataName, flush=True)

        # Boucle sur les classes
        listObjets = pListObjets[pDataList[index]]
        for classListObjets in listObjets:
            className = classListObjets[0]
            nClasse = pClasses.index(className)

            if len(classListObjets) == 1:
                print("     class: %s (%d)"%(className, nClasse), flush=True)
                ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s--c_%s.npy'%(dataName, className))
                oneExplanation = Xplique_computeExplanations.loadExplanations(pDictParams, ficExplanation, 1)
                if oneExplanation is None:
                    return
                oneExplanation = np.swapaxes(oneExplanation, 0, 1)
                oneExplanation = np.squeeze(oneExplanation, axis=2)

                # Application d'une fonction pour le plot de l'explication
                if pFctExplainToPlot is not None:
                    oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index, className)
                else:
                    oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, index)

                mskInference = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataInference", pRepertProd), '%s--c_%s.npy'%(dataName, className))
                mask = np.load(mskInference)
                if pFctDataToPlot is not None:
                    dataToPlot = pFctDataToPlot(pDictParams, pDataPathList[index], mask)
                else:
                    dataToPlot = kaasrc.communs.fctDataToPlotResized(pDictParams, mask)

                # Contrôle
                pParamSpecif = {"explOutputDim": None, "dataSize":
                    pDataSize[index]}
                kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, pPlotDataSize, oneExplanation, dataToPlot, aiModel.useCase, __file__, pParamSpecif)
                # Tracé
                kaasrc.communs.plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, dataToPlot, dataName, "--c_%s"%className)
            else:
                # Boucle sur les objets de chaque classe
                objects = classListObjets[1]
                for o in objects:
                    print("     class: %s (%d)  object: %d"%(className, nClasse, o))
                    ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s--i_%d--c_%s.npy'%(dataName, o, className))
                    oneExplanation = Xplique_computeExplanations.loadExplanations(pDictParams, ficExplanation, pNumData=1)
                    if oneExplanation is None:
                        return
                    oneExplanation = np.swapaxes(oneExplanation, 0, 1)
                    oneExplanation = np.squeeze(oneExplanation, axis=2)
#
                    # Application d'une fonction pour le plot de l'explication
                    if pFctExplainToPlot is not None:
                        oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index, o)
                    else:
                        oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, index)

                    ficExplanationTarget = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s--i_%d--c_%s--s_mask.npy'%(dataName, o, className))
                    target = Xplique_computeExplanations.loadExplanations(pDictParams, ficExplanationTarget, pNumClasses=aiModel.useCase.numClasses)
                    mask = tf.cast(target != 0, tf.float32)
                    mask = np.swapaxes(mask, -1, 0)
                    mask = mask[nClasse, :, :]
#
                    if pFctDataToPlot is not None:
                        dataToPlot = pFctDataToPlot(pDictParams, pDataPathList[index], mask)
                    else:
                        dataToPlot = kaasrc.communs.fctDataToPlotResized(pDictParams, mask)
#
                    # Contrôle
                    pParamSpecif = {"explOutputDim": None, "dataSize": pDataSize[index]}
                    kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, pPlotDataSize, oneExplanation, dataToPlot, aiModel.useCase, __file__, pParamSpecif)
                    # Tracé
                    kaasrc.communs.plotExplanationOnImage(pDictParams, resultSavedOn, oneExplanation, dataToPlot, dataName, "--i_%d--c_%s"%(o, className))

# -------------------------------------------------------------------------------
## Plot explanation of a specific tabular data
# @param pDictParams : parameter dictionary
# @param pFicExplanation : filename of saved explanation
# @param pIndexData : index of data to treat
# @param pDataName : data name to construct result filename
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
# @param pClasse : class name to treat or empty string to plot for all classes
def _plotExplanationOneTable(pDictParams, pFicExplanation, pIndexData, pDataName, pFctExplainToPlot, pFctDataToPlot, pClasse=""):
    # shortcuts
    pFeatureNames = pDictParams['aiModel'][1].useCase.features
    pPercentile = pDictParams["percentile"]
    pAlpha = pDictParams["alpha"]
    pCmap = pDictParams["cmap"]
    pDataPathList = pDictParams['dataPathList']
    pData, _ = pDictParams['xy']
    _, aiModel = pDictParams['aiModel']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
    outputXAIFramework = pDictParams['outputXAIFramework']

    oneExplanation = Xplique_computeExplanations.loadExplanations(pDictParams, pFicExplanation, pIndexData)
    if oneExplanation is None:
        return

    # Application d'une fonction pour le plot de l'explication
    if pFctExplainToPlot is not None:
        oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation)

    data = pData[pIndexData]
    # Application d'une fonction pour le plot de la donnée
    if pFctDataToPlot is not None:
        data = pFctDataToPlot(pDictParams, pDataPathList[pIndexData])

    pParamSpecif = {"dataSize": pDictParams['datasize'][pIndexData]}
    kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework, None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)

    # Plot
    plt.figure(facecolor='white', edgecolor='white')
    plot_mean_feature_impact(oneExplanation, features_name=pFeatureNames)
    plt.title('Mean impact of features')
    if pClasse == "":
        plt.title('Mean impact of features')
        extension = "--s_mean"
    else:
        plt.title('Mean impact of features on class %s'%pClasse)
        extension = "--c_%s"%pClasse

    # Save image
    ficPlot = kaasrc.communs.createDirName(resultSavedOn, "%s%s.png"%(pDataName, extension))
    plt.savefig(ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot)
    plt.close()

    plt.figure(facecolor='white', edgecolor='white')
    summary_plot_tabular(oneExplanation, features_values=data, features_name=pFeatureNames, cmap=pCmap, clip_percentile=pPercentile, alpha=pAlpha)
    if pClasse == "":
        plt.title('Impact of features')
    else:
        plt.title('Impact of features on class %s'%pClasse)
    # Save image
    ficPlot = kaasrc.communs.noSpace(resultSavedOn, "%s%s.png"%(pDataName, extension))
    plt.savefig(ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot, flush=True)
    plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of tablular data
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsTabText(pDictParams, pFctExplainToPlot, pFctDataToPlot):
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
