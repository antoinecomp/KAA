#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os, json, PIL
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import inspect

from kaasrc.communs import colPrint
import kaasrc.communs
import kaasrc.controles

from . import AIX360_computeExplanations

# ---------
try:
    import pandas as pd
except Exception as err:
    print("Error:", err)
    colPrint("Package pandas is not or not properly installed.", "Error")
# ---------
try:
    import shap
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Shap' is not or not properly installed.", "Error")
# ---------


# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the method BRCGE
# @param pDataName : data name for the filename of the image result
def _plotExplanationsTabularBRCGE(pDictParams, pResultSavedOn, pExplanation, pDataName):
    # shortcuts
    pClasses = pDictParams['classes']

    # Explication de chaque classe
    for oneClass, _ in enumerate(pClasses):
        if pExplanation[oneClass] is None:
            print("      No explanation available for class %s"%pClasses[oneClass])
            continue
        ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--c_%s.json"%(pDataName, pClasses[oneClass]))

        with open(ficPlot, "w", encoding="utf-8") as f:
            json.dump(pExplanation[oneClass], f, indent=4)

        print("    Saved in '%s'"%ficPlot)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanations : explanations by the method Lime
# @param pDataName : data name for the filename of the image result
# @param pIndex : index of the data treated
def _plotExplanationsTabularLime(pDictParams, pResultSavedOn, pExplanations, pDataName, pIndex):
    # shortcuts
    pClasses = pDictParams['classes']
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    xData, _ = pDictParams['xy']

    # Sauvegarde de la liste des items à traiter
    resultSavedOn = os.path.join(pDataProd, "dataExplanations", pRepertProd)
    pTabItems = kaasrc.communs.string2list(pDictParams['items'], range(len(pExplanations)), os.path.join(resultSavedOn, 'listItems.json'))

    for idxItem in pTabItems:

        if idxItem >= len(pExplanations):
            print("No input n°%d"%idxItem, flush=True)
            continue
        if pExplanations[idxItem] is None:
            print("No explanation available for the input %s"%str(xData[pIndex][idxItem]), flush=True)
            continue

        ficPlotHtml = kaasrc.communs.createDirName(pResultSavedOn, "%s--i_%d.html"%(pDataName, idxItem))
        pExplanations[idxItem].save_to_file(ficPlotHtml)

        for eClasse, vClasse in enumerate(pClasses):
            pExplanations[idxItem].as_pyplot_figure(label=eClasse)

            # Save image
            ficPlot = kaasrc.communs.noSpace(pResultSavedOn, "%s--i_%d--c_%s.png"%(pDataName, idxItem, vClasse))
            plt.savefig(ficPlot, bbox_inches='tight')
            print("       saved in:", ficPlot, flush=True)
            plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the image
# @param pIndex : index of the of the image
# @param pData : image to show
# @param pDataName : data name for the filename of the image result
# @param pNumClasses : number of class to detect
def _plotExplanationsImageLime(pDictParams, pResultSavedOn, pExplanation, pIndex, pData, pDataName, pNumClasses):
    # shortcuts
    pClasses = pDictParams['classes']
    _, aiModel = pDictParams['aiModel']

    dataSize = (aiModel.useCase.inputModelSize[0], aiModel.useCase.inputModelSize[1])
    explanationData = None
    for c in range(pNumClasses):
        explanationClasses = np.zeros(dataSize)
        for f, w in pExplanation.local_exp[c]:
            explanationClasses[pExplanation.segments == f] = w
        explanationClasses = np.expand_dims(explanationClasses, axis=2)
        if explanationData is None:
            explanationData = explanationClasses
        else:
            explanationData = np.concatenate((explanationData, explanationClasses), axis=2)

    for eClasse, vClasse in enumerate(pClasses):
        oneExplanation = explanationData[:, :, eClasse]
        oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, pIndex)
        kaasrc.communs.plotExplanationOnImage(pDictParams, pResultSavedOn, oneExplanation, pData, pDataName, pSuffixe="--c_%s"%vClasse)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the method Linear Rule Regression
# @param pDataName : data name for the filename of the image result
def _plotExplanationsTabularLinRR(pDictParams, pResultSavedOn, pExplanation, pDataName):
    # shortcuts
    pClasses = pDictParams['classes']

    # Explication de chaque classe
    for oneClass, _ in enumerate(pClasses):
        ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--c_%s.csv"%(pDataName, pClasses[oneClass]))
        if pExplanation[oneClass] is None:
            print("      No explanation available for class %s"%pClasses[oneClass])
            with open(ficPlot, "w", encoding="utf-8") as f:
                f.write("No explanation available for class %s"%pClasses[oneClass])
        else:
            pExplanation[oneClass].explain().to_csv(ficPlot)

        print("    Saved in '%s'"%ficPlot)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the method Logistic Rule Regression
# @param pDataName : data name for the filename of the image result
def _plotExplanationsTabularLogRR(pDictParams, pResultSavedOn, pExplanation, pDataName):
    # shortcuts
    pClasses = pDictParams['classes']

    # Explication de chaque classe
    for oneClass, _ in enumerate(pClasses):
        ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--c_%s.csv"%(pDataName, pClasses[oneClass]))
        if pExplanation[oneClass] is None:
            print("      No explanation available for class %s"%pClasses[oneClass])
            with open(ficPlot, "w", encoding="utf-8") as f:
                f.write("No explanation available for class %s"%pClasses[oneClass])
        else:
            pExplanation[oneClass].explain().to_csv(ficPlot)

        print("    Saved in '%s'"%ficPlot)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanations : explanations of the image
# @param pDataName : data name for the filename of the image result
# @param pIndex : table index to explain in case of tabular problem.
def _plotExplanationsTabularProtodash(pDictParams, pResultSavedOn, pExplanations, pDataName, pIndex):
    # shortcuts
    pClasses = pDictParams['classes']
    pResultats = pDictParams['predictions']
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    _, aiModel = pDictParams['aiModel']
    xData, _ = pDictParams['xy']
    modLabel = aiModel.useCase.label[pIndex]

    if 'sameTrainingPrediction' not in pDictParams:
        colPrint("The UCXAI plugin must implement a method of searching for similar elements.", "Error")
        return
    sameTrainingPrediction = pDictParams['sameTrainingPrediction']

    # Sauvegarde de la liste des items à traiter
    resultSavedOn = os.path.join(pDataProd, "dataExplanations", pRepertProd)
    pTabItems = kaasrc.communs.string2list(pDictParams['items'], range(len(pExplanations)), os.path.join(resultSavedOn, 'listItems.json'))

    for idxItem in pTabItems:
        if idxItem >= len(pExplanations):
            print("No input n°%d"%idxItem, flush=True)
            continue
        if pExplanations[idxItem][0] is None:
            print("No explanation available for the input %s"%str(xData[pIndex][idxItem]), flush=True)
            continue

        dataItem, prediction, _, indexPred = sameTrainingPrediction(pXData=xData[pIndex], pYPred=pResultats[pIndex], pItem=idxItem, pAiModel=aiModel)

        W, S, _ = pExplanations[idxItem]
        W = np.around(W / np.sum(W), 5)
        indexPrototype = indexPred[S]
        prototypes = np.array(aiModel.useCase.dataOrigin[pIndex])[indexPrototype]

        tabData = [np.around(dataItem.astype('double'), 3).tolist()[0] + ["--", str(pClasses[modLabel[idxItem]]), "--"]]
        tabData.extend(np.around(prototypes.astype('double'), 3).tolist())

        for eIndexPrototype, vIndexPrototype in enumerate(indexPrototype):
            tabData[eIndexPrototype + 1].append(str(pClasses[np.argmax(prediction)]))
            tabData[eIndexPrototype + 1].append(str(pClasses[modLabel[vIndexPrototype]]))
            tabData[eIndexPrototype + 1].append(W[eIndexPrototype])

        fig, ax = plt.subplots(figsize=(len(tabData[0]), len(tabData) / 3))
        ax.set_axis_off()

        labelsRow = [" item #%d"%idxItem] + ["proto #%d"%s for s in indexPrototype]
        labelsCol = aiModel.useCase.features + ["Pred.", "Label", "Weight"]
        rowColors = ["darkkhaki"]
        rowColors.extend(["tan"] * (len(labelsRow) - 1))
        tabColors = [["yellowgreen" for c, _ in enumerate(labelsCol)]]
        tabColors.extend([["lavender" for c, _ in enumerate(labelsCol)] for r in range(len(labelsRow) - 1)])

        ax.table(
            cellText=tabData,
            rowLabels=labelsRow,
            colLabels=labelsCol,
            rowColours=rowColors,
            colColours=["tan"] * len(labelsCol),
            cellColours=tabColors,
            cellLoc='center',
            loc='upper left')
        fig.tight_layout()

        ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--i_%s.png"%(pDataName, str(idxItem)))
        plt.title('Prototypes vs item #%d'%idxItem)
        plt.savefig(ficPlot, bbox_inches="tight")
        plt.close()

        # Differences
        eps = 1e-10  # Small constant defined to eliminate divide-by-zero errors
        fwt = np.zeros(prototypes.shape)
        for i in range(prototypes.shape[0]):
            for j in range(prototypes.shape[1]):
                fwt[i, j] = np.exp(-1 * abs(dataItem[0, j] - prototypes[i, j]) / (np.std(prototypes[:, j]) + eps))  # Compute feature similarity in [0, 1]
        tabData = np.around(fwt, 3).tolist()

        fig, ax = plt.subplots(figsize=(len(tabData[0]), len(tabData) / 3))
        ax.set_axis_off()

        labelsRow = labelsRow[1:]
        labelsCol = aiModel.useCase.features
        rowColors = rowColors[1:]
        tabColors = tabColors[1:]
        for r, _ in enumerate(tabColors):
            tabColors[r] = tabColors[r][:-3]

        ax.table(
            cellText=tabData,
            rowLabels=labelsRow,
            colLabels=labelsCol,
            rowColours=rowColors,
            colColours=["tan"] * len(labelsCol),
            cellColours=tabColors,
            cellLoc='center',
            loc='upper left')
        fig.tight_layout()

        ficPlot = kaasrc.communs.noSpace(pResultSavedOn, "%s--i_%s--s_differences.png"%(pDataName, str(idxItem)))
        plt.title('Difference beetween data and its prototypes')
        plt.savefig(ficPlot, bbox_inches="tight")
        plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of a specific tabular data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the data
# @param pIndex : table index to explain in case of tabular problem.
# @param pDataName : data name for the filename of the image result
# @param pOneClass : image index in the list of data to treat
# @param pMeanImpact : compute mean impact of feature
def _plotExplanationsTabularShap(pDictParams, pResultSavedOn, pExplanation, pIndex, pDataName, pOneClass, pMeanImpact=True):
    # shortcuts
    pClasses = pDictParams['classes']
    pData, _ = pDictParams['xy']
    _, aiModel = pDictParams['aiModel']
    pCmap = pDictParams["cmap"]

    # Plot tabular data
    plt.figure(facecolor='white', edgecolor='white')
    if pMeanImpact:
        plt.title("Mean impact of features on model output '%s'"%pClasses[pOneClass])
        plot_type = "bar"  # <= entraîne le calcul du mean(0)
        extension = "--s_mean"
    else:
        plt.title("Impact of features on model output '%s'"%pClasses[pOneClass])
        plot_type = "dot"  # dot violin layered_violin
        extension = ""

    if pOneClass is None:
        plot_type = "bar"
    shap.summary_plot(pExplanation[pOneClass], features=pData[pIndex].numpy(), feature_names=np.asarray(aiModel.useCase.features), class_names=pClasses, plot_type=plot_type, cmap=pCmap)
    plt.xlabel('')

    # Save image
    ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--c_%s%s.png"%(pDataName, pClasses[pOneClass], extension))
    plt.savefig(ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot, flush=True)
    plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the data
# @param pIndex : table index to explain in case of tabular problem
# @param pData2plot : data to treat
# @param pDataName : data name for the filename of the image result
def _plotExplanationsImageShap(pDictParams, pResultSavedOn, pExplanation, pIndex, pData2plot, pDataName):
    # shortcuts
    pClasses = pDictParams['classes']
    pData, yPred = pDictParams['xy']
    _, aiModel = pDictParams['aiModel']
    pMethod = pDictParams['method']
    pMethodParam = pDictParams[pMethod]
    pPlotDataSize = pDictParams['plotDataSize']

    # make a color map
    colors = []
    for i in np.linspace(1, 0, 100):
        colors.append((245 / 255, 39 / 255, 87 / 255, i))
    for i in np.linspace(0, 1, 100):
        colors.append((24 / 255, 196 / 255, 93 / 255, i))
    cm = LinearSegmentedColormap.from_list("shap", colors)

    def fill_segmentation(values, segmentation):
        out = np.zeros(segmentation.shape)
        for i, _ in enumerate(values):
            out[segmentation == i] = values[i]
        return out

    mp = pMethodParam["mp"]
    if mp == "Watershed":
        sl = int(pMethodParam["sl"])
        pt = pMethodParam["pt"]
        ny = int(pMethodParam["ny"])
        aiModel.megaPixelsParametres.update({"mapPixels": 0, "seuil": sl, "pretraitement": pt, "noyau": ny})
    else:
        nm = int(pMethodParam["nm"])
        aiModel.megaPixelsParametres["mapPixels"] = nm
    segmentation = aiModel.megaPixels(pData[pIndex])

    # plot our explanations
    nbCols = len(pClasses) + 1
    fig, axes = plt.subplots(nrows=1, ncols=nbCols, figsize=(12, nbCols))
    inds = np.argsort(yPred[pIndex])
    axes[0].imshow(np.array(pData2plot))
    axes[0].axis('off')
    max_val = np.max([np.max(np.abs(vExplanation[:, :-1])) for _, vExplanation in enumerate(pExplanation)])

    # top 3 des explications.
    for i in range(min(3, len(pClasses))):
        m = fill_segmentation(pExplanation[inds[-(i + 1)]][0], segmentation)
        m = PIL.Image.fromarray(m)
        m = m.resize((pData2plot.shape[1], pData2plot.shape[0]))
        m = np.asarray(m)
        axes[i + 1].set_title(pClasses[inds[-(i + 1)]])
        axes[i + 1].imshow(np.array(pData2plot), alpha=0.15)
        im = axes[i + 1].imshow(m, cmap=cm, vmin=-max_val, vmax=max_val)
        axes[i + 1].axis('off')
    cb = fig.colorbar(im, ax=axes.ravel().tolist(), label="SHAP value", orientation="horizontal", aspect=60)
    cb.outline.set_visible(False)

    # Save image
    txtDataSize = ""
    if pPlotDataSize == 1:
        txtDataSize = "--datasize"
    ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s%s.png"%(pDataName, txtDataSize))
    plt.savefig(ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot, flush=True)
    plt.close()

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanations : explanations of the text
# @param pData : data to treat
# @param pDataName : data name for the filename of the image result
# @param pIdxItem : item index in data
#def _plotExplanationsTextLime(pDictParams, pResultSavedOn, pExplanations, pData, pDataName, pIdxItem):
#
#    ficPlotHtml = kaasrc.communs.noSpace(pResultSavedOn, "%s_%i.html"%(pDataName.replace(' ', ''), pIdxItem))
#    pExplanations.save_to_file(ficPlotHtml)
#    print("    Saved in '%s'"%ficPlotHtml)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pResultSavedOn : path to save result
# @param pExplanations : explanations of the text
# @param pDataName : data name for the filename of the image result
# @param pIdxItem : item index in data
# @param pProtodashArguments : set of protodash plot arguments (cf._plotProtodashExplanations)
def _plotExplanationsTextProtodash(pDictParams,pResultSavedOn, pExplanations, pDataName, pIdxItem, pProtodashArguments):
    # shortcuts
    pTrainingExamples = pProtodashArguments["trainingExamples"]
    pPred = pProtodashArguments["pred"]
    pIndexPredTrainingExamples = pProtodashArguments["indexPredTrainingExamples"]
    pLabel = pProtodashArguments["label"]
    pClasses = pProtodashArguments["classes"]

    kaasrc.controles.NOcontrol_plotExplanationInput(pDictParams)

    (W, S, _) = pExplanations
    index_prototype = pIndexPredTrainingExamples[S]
    RP = []
    label = []
    prototypes = np.array(pTrainingExamples)[index_prototype]
    dfs = pd.DataFrame(prototypes)
    for i in index_prototype:
        RP.append(str(pClasses[np.argmax(pPred)]))      # Append class names
        label.append(str(pClasses[pLabel[i]]))          # Append real class names
    dfs[len(RP) + 1] = RP
    dfs.columns = ["sentences", "best_score"]

    dfs["Label"] = label
    dfs["Weight"] = np.around(W, 5) / np.sum(np.around(W, 5))  # Calculate normalized importance weights

    ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--i_%d.csv"%(pDataName.replace(' ', ''), pIdxItem))
    dfs.to_csv(ficPlot, sep=";", encoding='utf-8-sig')
    print("    Saved in '%s'"%ficPlot)

# -------------------------------------------------------------------------------
## Plot explanation of tablular data
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsTables(pDictParams, pFctExplainToPlot, pFctDataToPlot):
    # shortcuts
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']
    pClasses = pDictParams['classes']
    _, aiModel = pDictParams['aiModel']
    pMethod = pDictParams['method']
    pMethodParam = pDictParams[pMethod]

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    _, outputXAIFramework = AIX360_computeExplanations.resetXAIFramework()

    # Boucle sur les données
    for index in range(pNbData):
        dataName = pDataList[index]
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)

        # Lecture de l'explication de la donnée
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s.pkl'%dataName)
        oneExplanation = AIX360_computeExplanations.loadExplanations(pDictParams, ficExplanation, index)
        if oneExplanation is None:
            return

        # Application d'une fonction pour le plot de l'explication
        if pFctExplainToPlot is not None:
            oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index)

        if pMethod == "BRCGE":
            pParamSpecif = {"expected": (aiModel.useCase.numClasses, None), "format": ("[C]", None)}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod][1:], None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)
            _plotExplanationsTabularBRCGE(pDictParams, resultSavedOn, oneExplanation, dataName)
        elif pMethod == "LimeTabular":
            pParamSpecif = {"expected": (pDictParams['datasize'][index][0], None), "format": ("l", "?")}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod][1:], None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)
            _plotExplanationsTabularLime(pDictParams, resultSavedOn, oneExplanation, dataName, index)
        elif pMethod == "LinearRuleRegression":
            pParamSpecif = {"expected": (aiModel.useCase.numClasses, None), "format": ("C", "?")}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod][1:], None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)
            _plotExplanationsTabularLinRR(pDictParams, resultSavedOn, oneExplanation, dataName)
        elif pMethod == "LogisticRuleRegression":
            pParamSpecif = {"expected": (aiModel.useCase.numClasses, None), "format": ("C", "?")}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod][1:], None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)
            _plotExplanationsTabularLogRR(pDictParams, resultSavedOn, oneExplanation, dataName)
        elif pMethod == "Protodash":
            nbProtos = int(pMethodParam["m"])
            pParamSpecif = {"expected": (pDictParams['datasize'][index][0], 3, (nbProtos, )), "format": ("n", "l", "w/p/v", "Proto"), "levelData": (0, 1)}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod][1:], None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)
            _plotExplanationsTabularProtodash(pDictParams, resultSavedOn, oneExplanation, dataName, index)
        elif pMethod == "Shap":
            pParamSpecif = {"expected": (aiModel.useCase.numClasses, pDictParams['datasize'][index]), "format": ("[C]", "(l, f)")}
            kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod][1:], None, oneExplanation, None, aiModel.useCase, __file__, pParamSpecif)
            for oneClass, _ in enumerate(pClasses):
                _plotExplanationsTabularShap(pDictParams, resultSavedOn, oneExplanation, index, dataName, oneClass)
                _plotExplanationsTabularShap(pDictParams, resultSavedOn, oneExplanation, index, dataName, oneClass, False)
        else:
            kaasrc.controles.NOcontrol_plotExplanationInput(pDictParams)

# -------------------------------------------------------------------------------
## Plot explanation of tablular data
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsImages(pDictParams, pFctExplainToPlot, pFctDataToPlot):
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
    pClasses = pDictParams['classes']
    pMethod = pDictParams['method']
    outputXAIFramework = pDictParams['outputXAIFramework']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    # Boucle sur les données
    for index in range(pNbData):
        dataName = pDataList[index]
        data = pData[index]
        print("   .plot Explain #%d"%index, flush=True)
        print("       data:", dataName, flush=True)

        # Lecture des informations collectées à l'inférence

        # Lecture de l'explication de la donnée
        dirName = os.path.dirname(dataName)
        ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s.pkl'%os.path.basename(dataName))
        oneExplanation = AIX360_computeExplanations.loadExplanations(pDictParams, ficExplanation, index)
        if oneExplanation is None:
            return

        # Application d'une fonction pour le plot de l'explication
        if pFctExplainToPlot is not None:
            oneExplanation = pFctExplainToPlot(pDictParams, oneExplanation, index)
        elif pMethod == "Shap":
            oneExplanation = [kaasrc.communs.resizeData(expl, pDataSize[index]) for expl in oneExplanation]
        elif pMethod != "LimeImage":
            oneExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, oneExplanation, index)
        # Resize de l'explication pour claquer sur la donnée

        if pFctDataToPlot is not None and pDataBandPathList is not None:
            for fileDataBand in pDataBandPathList[index]:

                # Application d'une fonction pour le plot de la donnée
                dataName, _ = os.path.splitext(os.path.basename(fileDataBand))
                dataName = os.path.join(dirName, dataName)
                data = pFctDataToPlot(pDictParams, fileDataBand)

                # contrôle
                if pMethod == "LimeImage":
                    dataSize = (aiModel.useCase.inputModelSize[0], aiModel.useCase.inputModelSize[1])
                elif pPlotDataSize == 1:
                    dataSize = pDataSize[index]
                else:
                    dataSize = (aiModel.useCase.inputModelSize[0], aiModel.useCase.inputModelSize[1])
                kaasrc.controles.control_plotExplanationImagesInput(pDictParams, outputXAIFramework[pMethod], pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, nbBands=0, pDataSize=dataSize, explOutputDim=1, nbClasses=len(pClasses))
                # fonction de tracé
                if pMethod == "LimeImage":
                    _plotExplanationsImageLime(pDictParams, resultSavedOn, oneExplanation, index, data, dataName, aiModel.useCase.numClasses)
                elif pMethod == "Shap":
                    _plotExplanationsImageShap(pDictParams, resultSavedOn, oneExplanation, index, data, dataName)
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
            if pMethod == "LimeImage":
                # Contrôle de l'explication
                if pPlotDataSize == 1:
                    aAtteindre = (pDataSize[index][0], pDataSize[index][1], aiModel.useCase.numImageChannels)
                else:
                    aAtteindre = (aiModel.useCase.inputModelSize[0], aiModel.useCase.inputModelSize[1], aiModel.useCase.numImageChannels)
                strFormat = "(H, W, B) - explanation"
                pParamSpecif = {"expected": (None, aAtteindre), "format": ("?", strFormat)}
                kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod], pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)

            elif pMethod in ["Shap"]:
                # Contrôle de l'explication
                if pPlotDataSize == 1:
                    aAtteindre = (pDataSize[index][0], pDataSize[index][1], aiModel.useCase.numImageChannels)
                else:
                    aAtteindre = (aiModel.useCase.inputModelSize[0], aiModel.useCase.inputModelSize[1], aiModel.useCase.numImageChannels)
                pParamSpecif = {"expected": [(aiModel.useCase.numClasses, None), aAtteindre], "format": [("[C]", None), "(H, W, B)"]}
                kaasrc.controles.control_plotExplanationInput(pDictParams, outputXAIFramework[pMethod][1:], pPlotDataSize, oneExplanation, data, aiModel.useCase, __file__, pParamSpecif)

            else:
                colPrint("TODO: Controle de AIX360 %s dans plotExplanationsImages"%pMethod, "Select")

            # fonction de tracé
            if pMethod == "LimeImage":
                _plotExplanationsImageLime(pDictParams, resultSavedOn, oneExplanation, index, data, pDataList[index], aiModel.useCase.numClasses)
            elif pMethod == "Shap":
                _plotExplanationsImageShap(pDictParams, resultSavedOn, oneExplanation, index, data, pDataList[index])

# ---------------------------------------------------------------------------
## Launch the explanations plotting
# @param pDictParams : parameter dictionary
# @param pFctExplainToPlot : function to apply to explaination before plotting
# @param pFctDataToPlot : function to apply to data before plotting
def plotExplanationsTexts(pDictParams, pFctExplainToPlot, pFctDataToPlot):
    # Shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pMethod = pDictParams['method']
    pClasses = pDictParams['classes']

    _, aiModel = pDictParams['aiModel']
    xData, _ = pDictParams['xy']
    pUseCaseBase = pDictParams['useCaseBase']

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)

    # Tracé
    for index in range(pNbData):
        dataName = pDataList[index]
        dirName = os.path.dirname(dataName)
        if pMethod == "Protodash":
            ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s.pkl'%dataName)
            explanations = AIX360_computeExplanations.loadExplanations(pDictParams, ficExplanation)
            if explanations is None:
                return

            if 'sameTrainingPrediction' not in pDictParams:
                colPrint("The UCXAI plugin must implement a method of searching for similar elements.", "Error")
                return
            sameTrainingPrediction = pDictParams['sameTrainingPrediction']
            for idxItem, _ in enumerate(xData[index]):
                if explanations[idxItem] is not None:
                    train_comment, train_label = aiModel.useCase.getData(pUseCaseBase, pDictParams['dataTrainPath'])
                    example, pred, _, index_pred_training_examples = sameTrainingPrediction(xData[index], train_comment, train_label, index, idxItem, aiModel)
                    protodashArguments = {}
                    protodashArguments["trainingExamples"] = train_comment
                    protodashArguments["pred"] = pred
                    protodashArguments["indexPredTrainingExamples"] = index_pred_training_examples
                    protodashArguments["example"] = example
                    protodashArguments["label"] = train_label
                    protodashArguments["classes"] = pClasses
                    kaasrc.controles.NOcontrol_plotExplanationInput(pDictParams)
                    _plotExplanationsTextProtodash(pDictParams,resultSavedOn, explanations[idxItem], dataName, idxItem, protodashArguments)

        elif pMethod == "LimeText":
            ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s.pkl'%dataName)
            explanations = AIX360_computeExplanations.loadExplanations(pDictParams, ficExplanation)
            if explanations is None:
                return
            kaasrc.controles.NOcontrol_plotExplanationInput(pDictParams)
            for idxItem, _ in enumerate(xData[index]):
                ficPlot = kaasrc.communs.createDirName(resultSavedOn, os.path.join(dirName, "%s--i_%d.html"%(dataName.replace(' ', ''), idxItem)))
                explanations[idxItem].save_to_file(ficPlot)
                print("    Saved in '%s'"%ficPlot)

        else:
            print("No explanation available for this method ", flush=True)

# ===============================================================================
# end of file
