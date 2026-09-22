#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os

import kaasrc.controles

from . import Alibi_computeExplanations


# ---------------------------------------------------------------------------
## Plot explanation on file
# @param pResultSavedOn : path to save on
# @param pExplanations : explanations
# @param pDataName : data name for the filename of the image result
# @param pIdxItem : item index in data
def _plotExplanationsAnchors(pDictParams,pResultSavedOn, pExplanations, pDataName, pIdxItem):
    ficPlot = kaasrc.communs.createDirName(pResultSavedOn, "%s--i_%d.txt"%(pDataName, pIdxItem))

    kaasrc.controles.NOcontrol_plotExplanationInput(pDictParams)

    with open(ficPlot, "w", encoding="utf-8") as f:
        f.write('Item %d\n'%pIdxItem)
        if pExplanations is None:
            f.write('Alibi does not provide explanation for this item.\n')
        else:
            f.write('\tAnchor : %s\n' % (' AND '.join(pExplanations["Anchor"])))
            f.write('\tPrecision: %.2f\n' % pExplanations["Precision"])
            f.write('\tExamples where anchor applies and model predicts %s:\n' % pExplanations["Predictions"])
            if len(pExplanations['covered_true']) > 0:
                for x in pExplanations['covered_true']:
                    f.write('\t- %s\n'%x)
            else:
                f.write('\t- none\n')
            f.write('\nExamples where anchor applies and model predicts %s:\n' % pExplanations["Alternatives"])
            if len(pExplanations['covered_false']) > 0:
                for x in pExplanations['covered_false']:
                    f.write('\t- %s\n'%x)
            else:
                f.write('\t- none\n')
    print("    Saved in '%s'"%ficPlot)

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
    xData, _ = pDictParams['xy']

    # Tracé
    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
    for index in range(pNbData):
        dataName = pDataList[index]
        if pMethod == "Anchors":
            npxData = xData[index]
            ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd), '%s.json'%dataName)
            explanations = Alibi_computeExplanations.loadExplanations(pDictParams,ficExplanation)

            for entry, _ in enumerate(npxData):
                _plotExplanationsAnchors(pDictParams,resultSavedOn, explanations[str(entry)], dataName, entry)

        else:
            print("No explanation available for this method ", flush=True)

# ===============================================================================
# end of file
