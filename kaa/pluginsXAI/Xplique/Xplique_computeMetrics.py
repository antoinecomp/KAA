#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os, json
import numpy as np
# import random : pour accelerer les tests

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
    from xplique.metrics import MuFidelity, Deletion, Insertion, AverageStability, MeGe
    from xplique.commons.operators import regression_operator
    from xplique.commons.operators import object_detection_operator
    from xplique.commons.operators import semantic_segmentation_operator
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Xplique' is not or not properly installed.", "Error")
# ---------


# ---------------------------------------------------------------------------
## Create an instance of the explainability metric
# @param pAiModel : model instance
# @param pData : data prepared for inference
# @param pPred : inference result
# @param pMetric : metric used for measurement
# @param pMetricParam : metric params used for measurement
# @param pOperator : specific operator (cf. Xplique library)
# @param pActivation : Xplique activation parameter
# @return method instance
def _getMetricEvaluator(pAiModel, pData, pPred, pMetric, pMetricParam, pOperator, pActivation):
    # CausalFidelity-Deletion
    if pMetric == "CausalFidelity-Deletion":
        bz = int(pMetricParam["bz"])
        bm = float(pMetricParam["bm"])
        st = int(pMetricParam["st"])
        pp = float(pMetricParam["pp"])
        metricEvaluator = Deletion(pAiModel.useCase,
                              pData,
                              pPred,
                              batch_size=bz,
                              baseline_mode=bm,
                              steps=st,
                              max_percentage_perturbed=pp,
                              operator=pOperator,
                              activation=pActivation)
    # CausalFidelity-Insertion
    elif pMetric == "CausalFidelity-Insertion":
        bz = int(pMetricParam["bz"])
        bm = float(pMetricParam["bm"])
        st = int(pMetricParam["st"])
        pp = float(pMetricParam["pp"])
        metricEvaluator = Insertion(pAiModel.useCase,
                              pData,
                              pPred,
                              batch_size=bz,
                              baseline_mode=bm,
                              steps=st,
                              max_percentage_perturbed=pp,
                              operator=pOperator,
                              activation=pActivation)
    # AverageStability
    elif pMetric == "AverageStability":
        bz = int(pMetricParam["bz"])
        rd = float(pMetricParam["rd"])
        ds = pMetricParam["ds"]
        ns = int(pMetricParam["ns"])
        metricEvaluator = AverageStability(pAiModel.useCase,
                                pData,
                                pPred,
                                batch_size=bz,
                                radius=rd,
                                distance=ds,
                                nb_samples=ns)
    # MuFidelity
    elif pMetric == "MuFidelity":
        bz = int(pMetricParam["bz"])
        gz = int(pMetricParam["gz"])
        sp = float(pMetricParam["sp"])
        bm = float(pMetricParam["bm"])
        ns = int(pMetricParam["ns"])
        metricEvaluator = MuFidelity(pAiModel.useCase,
                          pData,
                          pPred,
                          batch_size=bz,
                          grid_size=gz,
                          subset_percent=sp,
                          baseline_mode=bm,
                          nb_samples=ns,
                          operator=pOperator,
                          activation=pActivation)
    # MuFidelity
    elif pMetric == "MeGe":
        bz = int(pMetricParam["bz"])
        ks = int(pMetricParam["ks"])
        metricEvaluator = MeGe(pAiModel.useCase,
                    pData,
                    pPred,
                    batch_size=bz,
                    k_splits=ks)
    else:
        metricEvaluator = None

    return metricEvaluator

# ---------------------------------------------------------------------------
## Define key to store score
# @param pIndex : index of the data
# @param pDataList : list of data filename
# @param pDict : dictonnary
# @return key, dictionnary
def _defineKeyScore(pIndex, pDataList, pDict):
    # Si l'index de donnée est nul  : la clef est 'allData'
    if pIndex is None:
        keyScore = "allData"
    else:
        keyScore = pDataList[pIndex]
    # si la clef n'est pas présente, on l'ajoute
    if keyScore not in pDict:
        pDict[keyScore] = {}

    return keyScore, pDict

# ---------------------------------------------------------------------------
## Compute CausalFidelity metric
# @param pDictParams : parameter dictionary
# @param pMetric : metric name
# @param pMetricEvaluator : metric evaluator instance
# @param pMethods4metric : explainability method list
# @param pSuffixesMethods : suffix of method (params to add to the result filename
# @param pExplanations : explanations to measure
# @param pIndex : index of the data to treat in list
def _metricEvaluateCausalFidelity(pDictParams, pMetric, pMetricEvaluator, pMethods4metric, pSuffixesMethods, pExplanations, pIndex):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pMetrique = pDictParams['metric']
    pSuffixMetric = pDictParams["suffixMetric"]
    pDataList = pDictParams['dataList']

    dataKey = "allData"
    if pIndex is not None:
        dataKey = pDataList[pIndex]

    print("Metric %s"%pMetric)

    # fichier de resultats
    fichProd = os.path.join(pDataProd, "dataMetrics", pDictParams['code'], '%s_%s'%(pMetrique, pSuffixMetric))

    results = {}

    courbeAucByMethod = {}
    scoresAucByMethod = {}

    for methode in pMethods4metric:
        courbeAuc = pMetricEvaluator.detailed_evaluate(pExplanations[methode])
        courbeAucIntKeys = {}
        for k in courbeAuc.keys():
            courbeAucIntKeys[int(k)] = float(courbeAuc[k])

        # ----------------------------
        #print("pour accelerer les tests")
        #courbeAucIntKeys = {}
        #for e in range(20):
        #    courbeAucIntKeys[e] = random.random()
        # ----------------------------
        methodWithSuffix = "%s_%s"%(methode, pSuffixesMethods[methode])
        # compute auc using trapezoidal rule (the steps are equally distributed)
        npCourbeAuc = np.array(list(courbeAucIntKeys.values()))
        scoreAuc = float(np.mean(npCourbeAuc[:-1] + npCourbeAuc[1:])) * 0.5
        print("%s auc value is: %0.3f"%(methodWithSuffix.lower(), scoreAuc), flush=True)

        # Pour la courbe de AUC de la donnée
        courbeAucByMethod.setdefault(methodWithSuffix, {}).setdefault(dataKey, {}).setdefault("values", courbeAucIntKeys)
        courbeAucByMethod[methodWithSuffix][dataKey]["score"] = scoreAuc

        # Pour le score de AUC de la donnée (--d_ dans le fichier)
        scoresAucByMethod.setdefault(methodWithSuffix, scoreAuc)

        # Pour le score de AUC de la donnée (toutes les données)
        results.setdefault(methodWithSuffix, {}).setdefault(dataKey, scoreAuc)

    # save metric results
    print("    results saved in '%s.json'"%fichProd)
    with open("%s.json"%fichProd, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    # ajustement du nom de fichier s'il y a une répartition des résultats par donnée
    if pIndex is not None:
        fichProd = "%s--d_%s"%(fichProd, pDataList[pIndex].replace(' ', ''))

    # save metric AUC graphic
    print("    results saved in '%s--s_AUCvalues.json'"%fichProd)
    with open("%s--s_AUCvalues.json"%fichProd, "w", encoding="utf-8") as f:
        json.dump(courbeAucByMethod, f, indent=4)

    # save metric AUC score
    if pIndex is not None:
        print("    results saved in '%s.json'"%fichProd)
        with open("%s.json"%fichProd, "w", encoding="utf-8") as f:
            json.dump(scoresAucByMethod, f, indent=4)

    return results

# ---------------------------------------------------------------------------
## Compute AverageStability metric
# @param pDictParams : parameter dictionary
# @param pMetric : metric name
# @param pMetricEvaluator : metric evaluator instance
# @param pMethods4metric : explainability method list
# @param pSuffixesMethods : suffix of method (params to add to the result filename
# @param pExplainer : method explainer from explainability method list to compute metric
# @param pExplanations : explanations to measure
# @param pIndex : index of the data to treat in list
def _metricEvaluateAverageStability(pDictParams, pMetric, pMetricEvaluator, pMethods4metric, pSuffixesMethods, pExplainer, pExplanations, pIndex):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pMetrique = pDictParams['metric']
    pSuffixMetric = pDictParams["suffixMetric"]
    pDataList = pDictParams['dataList']

    dataKey = "allData"
    if pIndex is not None:
        dataKey = pDataList[pIndex]

    print("Metric %s"%pMetric)

    # fichier de resultats
    fichProd = os.path.join(pDataProd, "dataMetrics", pDictParams['code'], '%s_%s'%(pMetrique, pSuffixMetric))

    results = {}
    # Si le fichier Json existe déjà : on le lit
    if os.path.exists("%s.json"%fichProd):
        print("    results loaded from '%s.json'"%fichProd)
        with open("%s.json"%fichProd, "r", encoding="utf-8") as f:
            results = json.load(f)

    for methode in pMethods4metric:
        score = pMetricEvaluator.evaluate(pExplainer[methode], pExplanations[methode])
        # ----------------------------
        # pour accelerer les tests
        # score = random.random()
        # ----------------------------
        methodWithSuffix = "%s_%s"%(methode, pSuffixesMethods[methode])
        results.setdefault(methodWithSuffix, {}).setdefault(dataKey, score)
        print("    %s score value is: %0.3f"%(methodWithSuffix, score), flush=True)

    # save metric
    print("    results saved in '%s.json'"%fichProd)
    with open("%s.json"%fichProd, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    if pIndex is not None:
        fichProdData = "%s--d_%s"%(fichProd, pDataList[pIndex].replace(' ', ''))
        resultatData = {}
        for key in results:
            resultatData[key] = results[key][dataKey]
        print("    results by data saved in '%s.json'"%fichProdData)
        with open("%s.json"%fichProdData, "w", encoding="utf-8") as f:
            json.dump(resultatData, f, indent=4)

    return results

# ---------------------------------------------------------------------------
## Compute MuFidelity metric
# @param pDictParams : parameter dictionary
# @param pMetric : metric name
# @param pMetricEvaluator : metric evaluator instance
# @param pMethods4metric : explainability method list
# @param pSuffixesMethods : suffix of method (params to add to the result filename
# @param pExplanations : explanations to measure
# @param pIndex : index of the data to treat in list
def _metricEvaluateMuFidelity(pDictParams, pMetric, pMetricEvaluator, pMethods4metric, pSuffixesMethods, pExplanations, pIndex):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pMetrique = pDictParams['metric']
    pSuffixMetric = pDictParams["suffixMetric"]
    pDataList = pDictParams['dataList']

    dataKey = "allData"
    if pIndex is not None:
        dataKey = pDataList[pIndex]

    print("Metric %s"%pMetric)

    # fichier de resultats
    fichProd = os.path.join(pDataProd, "dataMetrics", pDictParams['code'], '%s_%s'%(pMetrique, pSuffixMetric))

    results = {}
    # Si le fichier Json existe déjà : on le lit
    if os.path.exists("%s.json"%fichProd):
        print("    results loaded from '%s.json'"%fichProd)
        with open("%s.json"%fichProd, "r", encoding="utf-8") as f:
            results = json.load(f)

    for methode in pMethods4metric:
        score = pMetricEvaluator.evaluate(pExplanations[methode])
        # ----------------------------
        # pour accelerer les tests
        # score = random.random()
        # ----------------------------
        methodWithSuffix = "%s_%s"%(methode, pSuffixesMethods[methode])
        results.setdefault(methodWithSuffix, {}).setdefault(dataKey, score)
        print("    %s score value is: %0.3f"%(methodWithSuffix, score), flush=True)

    # save metric
    print("    results saved in '%s.json'"%fichProd)
    with open("%s.json"%fichProd, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    if pIndex is not None:
        fichProdData = "%s--d_%s"%(fichProd, pDataList[pIndex].replace(' ', ''))
        resultatData = {}
        for key in results:
            resultatData[key] = results[key][dataKey]
        print("    results by data saved in '%s.json'"%fichProdData)
        with open("%s.json"%fichProdData, "w", encoding="utf-8") as f:
            json.dump(resultatData, f, indent=4)

    return results

# ---------------------------------------------------------------------------
## Compute metrics
# @param pDictParams : parameter dictionary
# @param pData : data prepared for inference
# @param pPred : inference result
# @param pOperator : specific operator (cf. Xplique library)
# @param pActivation : Xplique activation parameter
# @param pIndex : index of data to treat
def computeMetrics(pDictParams, pData, pPred, pOperator=None, pActivation=None, pIndex=None):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pMetrique = pDictParams['metric']
    pMetricParam = pDictParams[pMetrique]
    pNbData = pDictParams['nbData']
    _, aiModel = pDictParams['aiModel']
    pModelType = pDictParams['modeltype']
    pDataList = pDictParams['dataList']

    if pDictParams['methods4metric'] == "":
        print("No method selected!")
        return
    pMethods4metric = pDictParams['methods4metric'].split(',')

    # compute
    print("   .get metric %s:%s"%(pDictParams['library'], pMetrique), flush=True)
    aiModel.setInferenceCible(False)

    metricEvaluator = _getMetricEvaluator(aiModel, pData, pPred, pMetrique, pMetricParam, pOperator, pActivation)

    dicoExplainers = {}
    dicoExplanations = {}
    dicoSuffixesMethods = {}
    for methode in pMethods4metric:
        print("   .Metric on %s method"%methode, flush=True)
        pMethodParam = pDictParams[methode]
        if pModelType == "regression":
            operator = regression_operator
        elif pModelType == "detection":
            operator = object_detection_operator
        elif pModelType == "segmentation":
            operator = semantic_segmentation_operator
        else:
            operator = None
        dicoExplainers[methode] = Xplique_computeExplanations.getExplainer(aiModel, methode, pMethodParam, operator)

        # Load explanations
        repertProd = os.path.join(pDictParams['code'], "%s_%s"%(methode, pDictParams[methode]['suffixMethod']))
        if pIndex is not None:
            ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", repertProd), '%s.npy'%pDataList[pIndex])
        else:
            ficExplanation = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", repertProd), 'allData.npy')
        print("     Load explanation from %s"%ficExplanation)
        fullData = 0
        if pModelType == "detection":
            for data in pDictParams['objets']:
                fullData += len(pDictParams['objets'][data])
        elif pModelType == "segmentation":
            for data in pDictParams['objets']:
                for classe in pDictParams['objets'][data]:
                    if len(classe) == 1:
                        fullData += 1
                    else:
                        fullData += len(classe[1])
        else:
            fullData = pNbData

        explanations = Xplique_computeExplanations.loadExplanations(pDictParams, ficExplanation, pNumData=pIndex, pFullData=fullData, pNumClasses=1)

        dicoExplanations[methode] = explanations
        dicoSuffixesMethods[methode] = pDictParams[methode]['suffixMethod']

    scores = None

    # CausalFidelity-Deletion
    if pMetrique in ["CausalFidelity-Deletion", "CausalFidelity-Insertion"]:
        scores = _metricEvaluateCausalFidelity(pDictParams, pMetrique, metricEvaluator, pMethods4metric, dicoSuffixesMethods, dicoExplanations, pIndex)

    # AverageStability
    elif pMetrique == "AverageStability":
        scores = _metricEvaluateAverageStability(pDictParams, pMetrique, metricEvaluator, pMethods4metric, dicoSuffixesMethods, dicoExplainers, dicoExplanations, pIndex)

    # MuFidelity
    elif pMetrique == "MuFidelity":
        scores = _metricEvaluateMuFidelity(pDictParams, pMetrique, metricEvaluator, pMethods4metric, dicoSuffixesMethods, dicoExplanations, pIndex)

    return scores

# ---------------------------------------------------------------------------
## Compute metrics for tabular data
# @param pDictParams : parameter dictionary
# @param pIndex : index of the data to treat
def _computeMetricsTable(pDictParams, pIndex):
    # shortcuts
    xData, yPred = pDictParams['xy']

    data = xData[pIndex]
    pred = yPred[pIndex]

    if not isinstance(data, np.ndarray):
        data = np.array(data)
    if not isinstance(pred, np.ndarray):
        pred = np.array(pred)

    scores = computeMetrics(pDictParams, data, pred, pIndex=pIndex)
    return scores

# ---------------------------------------------------------------------------
## Compute metrics for tabular data
# @param pDictParams : parameter dictionary
def computeMetricsTabText(pDictParams):
    # shortcuts
    pNbData = pDictParams['nbData']
    _, aiModel = pDictParams['aiModel']
    xData, yPred = pDictParams['xy']
    inputXAIframework = pDictParams['inputXAIframework']

    # control function for XAI_computeMetrics inputs
    pParamSpecif = {"dataSize": pDictParams['datasize']}
    kaasrc.controles.controlXAI_computeMetricsInput(pDictParams, inputXAIframework, xData, yPred, aiModel.useCase, pNbData, __file__, pParamSpecif)

    for index in range(pNbData):
        _computeMetricsTable(pDictParams, index)

# ---------------------------------------------------------------------------
## Compute metrics for Image Segmentation
# @param pDictParams : parameter dictionary
def computeMetricsObjSegmentation(pDictParams):
    # shortcuts
    pNbData = pDictParams['nbData']
    _, aiModel = pDictParams['aiModel']
    xData, yPred = pDictParams['xy']
    inputXAIframework = pDictParams['inputXAIframework']

    # Chargement de la liste des objets détectés pendant l'explication
    pDictParams = kaasrc.communs.updateListObjects(pDictParams)
    pListObjets = pDictParams['objets']

    for iexp, _ in enumerate(xData):
        xData[iexp] = tf.squeeze(xData[iexp], axis=0)
    # control function for XAI_computeMetrics inputs
    pParamSpecif = {"nbSegm": aiModel.useCase.nbObjects}
    kaasrc.controles.controlXAI_computeMetricsInput(pDictParams, inputXAIframework, xData, yPred, aiModel.useCase, pNbData, __file__, pParamSpecif)

    if not isinstance(xData, np.ndarray):
        xData = np.array(xData)
    if not isinstance(yPred, np.ndarray):
        yPred = np.array(yPred)

    # calculate the number of the explained elements (classes or objects) for each data
    nb_elements_list = [sum(1 if len(classListObjets) == 1 else len(classListObjets[1]) for classListObjets in listObjets) for listObjets in list(pListObjets.values())[:pNbData]]

    # repeat xData and yPred for all elements (classes or objects) of the same data
    xData = np.repeat(xData, nb_elements_list, axis=0)
    yPred = np.repeat(yPred, nb_elements_list, axis=0)

    computeMetrics(pDictParams, xData, yPred, pOperator=semantic_segmentation_operator)

# ---------------------------------------------------------------------------
## Compute metrics for Image Detection
# @param pDictParams : parameter dictionary
def computeMetricsObjDetection(pDictParams):
    # shortcuts
    pNbData = pDictParams['nbData']
    _, aiModel = pDictParams['aiModel']
    xData, yPred = pDictParams['xy']
    inputXAIframework = pDictParams['inputXAIframework']

    # Chargement de la liste des objets détectés pendant l'explication
    pDictParams = kaasrc.communs.updateListObjects(pDictParams)
    pListObjets = pDictParams['objets']

    # control function for XAI_computeMetrics inputs
    pParamSpecif = {"nbBbx": aiModel.useCase.nbObjects}
    kaasrc.controles.controlXAI_computeMetricsInput(pDictParams, inputXAIframework, xData, yPred, aiModel.useCase, pNbData, __file__, pParamSpecif)

    if not isinstance(xData, np.ndarray):
        xData = np.array(xData)
    if not isinstance(yPred, np.ndarray):
        yPred = np.array(yPred)

    # repeat xData and yPred for all elements (classes or objects) of the same data
    xDataRepeated = []
    yPredSelection = []
    for idx, dataIdx in enumerate(xData):
        lobjets = list(pListObjets.values())[idx]
        xDataRepeated.append(np.repeat(dataIdx, len(lobjets), axis=0))
        for o in lobjets:
            yPredSelection.append(yPred[idx][o])

    xData = np.concatenate(xDataRepeated)
    yPred = np.array(yPredSelection)

    computeMetrics(pDictParams, xData, yPred, pOperator=object_detection_operator)

# ---------------------------------------------------------------------------
## Compute metrics for Image Detection
# @param pDictParams : parameter dictionary
def computeMetricsImage(pDictParams):
    # shortcuts
    pNbData = pDictParams['nbData']
    _, aiModel = pDictParams['aiModel']
    xData, yPred = pDictParams['xy']
    inputXAIframework = pDictParams['inputXAIframework']

    # control function for XAI_computeMetrics inputs
    kaasrc.controles.controlXAI_computeMetricsInput(pDictParams, inputXAIframework, xData, yPred, aiModel.useCase, pNbData, __file__)
    computeMetrics(pDictParams, xData, yPred)

# ===============================================================================
# end of file
