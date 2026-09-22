#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os, json
import numpy as np

# import random : pour accelerer les tests

from kaasrc.communs import colPrint
import kaasrc.plugin_collection
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
    from aix360.metrics import faithfulness_metric, monotonicity_metric
    from aix360.algorithms.rbm import FeatureBinarizer
except Exception as err:
    print("Error:", err)
    colPrint("The library 'AIX360' is not or not properly installed.", "Error")
# ---------
try:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
except Exception as err:
    print("Error:", err)
    colPrint("The library 'Sklearn' is not or not properly installed.", "Error")
# ---------


# ---------------------------------------------------------------------------
## Compute Sklearn Scores metric
# @param pDictParams : parameter dictionary
# @param pData : data prepared for inference
# @param pExplanation : explanation
# @param pMethode : method to measure
# @param pResPredictionsCibles : target predictions (inference)
# @param pFichProd : file to save without extension
# @param pIdxData : data index in the list of data treated
# @return score
def _metricSklearnScore(pDictParams, pData, pMethode, pExplanation, pResPredictionsCibles, pFichProd, pIdxData=None):
    # shortcuts
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']
    pClasses = pDictParams['classes']

    fb = FeatureBinarizer(negations=True, returnOrd=True)
    data = pd.DataFrame(np.array(pData), columns=aiModel.useCase.features)
    dfData, dfDataStd = fb.fit_transform(data)

    score = {}
    # Si le fichier Json existe déjà : on le lit
    if pIdxData is not None:
        ficProd = '%s--d_%s.json'%(pFichProd, pDataList[pIdxData].replace(' ', ''))
    else:
        ficProd = "%s.json"%pFichProd
    if os.path.exists(ficProd):
        print("    Metric results loaded from '%s'"%ficProd)
        with open(ficProd, "r", encoding="utf-8") as f:
            score = json.load(f)
    score[pMethode] = {}

    for iClasse, _ in enumerate(pClasses):
        classe = pClasses[iClasse]
        score[pMethode][classe] = {}

        yPred = np.array([1 if np.argmax(pred) == iClasse else 0 for pred in np.array(pResPredictionsCibles)])

        if pExplanation[iClasse] is not None:
            try:
                if pMethode.split('__')[0] in ["LinearRuleRegression", "LogisticRuleRegression"]:
                    prediction_explanation = np.round(pExplanation[iClasse].predict(dfData, dfDataStd))
                else:
                    prediction_explanation = np.round(pExplanation[iClasse].predict(dfData))
                score[pMethode][classe]["accuracy"] = accuracy_score(yPred, prediction_explanation)
                score[pMethode][classe]["precision"] = precision_score(yPred, prediction_explanation, average="macro")
                score[pMethode][classe]["recall"] = recall_score(yPred, prediction_explanation, average="macro")
                score[pMethode][classe]["f1"] = f1_score(yPred, prediction_explanation, average="macro")
                # ----------------------------
                #print("ATTENTION :pour accelerer les tests")
                #score[pMethode][classe]["accuracy"] = random.random()
                #score[pMethode][classe]["precision"] = random.random()
                #score[pMethode][classe]["recall"] = random.random()
                #score[pMethode][classe]["f1"] = random.random()
                # ----------------------------

            except Exception as err:
                print("Error:", err)
                colPrint("An error occured (pb of dimension)", "Config")
        else :
            print("No explanation available for the class %s"%classe, flush=True)
    # save metric
    print("Metric results saved in '%s'"%ficProd)
    with open(ficProd, "w", encoding="utf-8") as f:
        json.dump(score, f, indent=4)

    return score

# ---------------------------------------------------------------------------
## Compute Monotonicity metric for tabular and text data
# @param pDictParams : parameter dictionary
# @param pData : data prepared for inference
# @param pBaseline : baseline value for explanation and metric
# @param pMethode : method to measure
# @param pExplanation : explanation
# @param pResPredictionsCibles : target predictions (inference)
# @param pFichProd : file to save without extension
# @param pEmbedding : embedding data param for text use case
# @param pIdxData : data index in the list of data treated
# @return score
def _metricMonotonicityTabular(pDictParams, pData, pBaseline, pMethode, pExplanation, pResPredictionsCibles, pEmbedding, pFichProd, pIdxData=None):
    # shortcuts
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']

    if not hasattr(aiModel.useCase, 'predict_proba'):
        colPrint("/!\\ The model must implement a method 'predict_proba()'. No calculated metric.", "Error")
        return

    score = {}
    # Si le fichier Json existe déjà : on le lit
    if pIdxData is not None:
        ficProd = '%s--d_%s.json'%(pFichProd, pDataList[pIdxData].replace(' ', ''))
    else:
        ficProd = "%s.json"%pFichProd
    if os.path.exists(ficProd):
        print("    Metric results loaded from '%s'"%ficProd)
        with open(ficProd, "r", encoding="utf-8") as f:
            score = json.load(f)
    score[pMethode] = {}
    scores = []
    nb_trueFalse = {1: 0, 0: 0}

    for idxItem, data in enumerate(pData):
        pred = np.array(pResPredictionsCibles[idxItem])
        dim = pData.shape[1]
        le = pExplanation[idxItem].local_exp[np.argmax(pred)]

        if pEmbedding is not None:
            npData = np.array(pEmbedding)
            coefs = np.zeros(data["input_ids"].numpy().shape[0])
            base = np.array([pBaseline] * (data["input_ids"].numpy().shape[0]))
        else:
            npData = np.array(pData[idxItem])
            coefs = np.zeros(dim)
            base = np.array([pBaseline] * dim)
        for v in le:
            coefs[v[0]] = v[1]

        score[pMethode][idxItem] = 1 if monotonicity_metric(aiModel.useCase, npData, coefs, base) else 0
        # ----------------------------
        #print("ATTENTION :pour accelerer les tests")
        #score[pMethode][idxItem]=1 if random.random()>0.5 else 0
        # ----------------------------

        scores.append(score[pMethode][idxItem])

        nb_trueFalse[score[pMethode][idxItem]] += 1
    score[pMethode]["mean"] = np.mean(scores)

    print("Metric mean score value is: %f"%score[pMethode]["mean"], flush=True)

    print("Metric results saved in '%s'"%ficProd)
    with open(ficProd, "w", encoding="utf-8") as f:
        json.dump(score, f, indent=4)

    return score

# ---------------------------------------------------------------------------
## Compute Monotonicity metric for image data
# @param pDictParams : parameter dictionary
# @param pData : data prepared for inference
# @param pBaseline : baseline value for explanation and metric
# @param pMethode : method to measure
# @param pExplanation : explanation
# @param pResPredictionsCibles : target predictions (inference)
# @param pFichProd : file to save without extension
# @param pEmbedding : embedding data param for text use case
# @param pIdxData : data index in the list of data treated
# @return score
def _metricMonotonicityImage(pDictParams, pData, pBaseline, pMethode, pExplanation, pResPredictionsCibles, pFichProd, pEmbedding, pIdxData=None):
    # shortcuts
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']

    if not hasattr(aiModel.useCase, 'predict_proba'):
        colPrint("/!\\ The model must implement a method 'predict_proba()'. No calculated metric.", "Error")
        return

    score = {}
    # Si le fichier Json existe déjà : on le lit
    if pIdxData is not None:
        ficProd = '%s--d_%s.json'%(pFichProd, pDataList[pIdxData].replace(' ', ''))
    else:
        ficProd = "%s.json"%pFichProd
    if os.path.exists(ficProd):
        print("    Metric results loaded from '%s'"%ficProd)
        with open(ficProd, "r", encoding="utf-8") as f:
            score = json.load(f)
    score[pMethode] = {}

    pred = np.array(pResPredictionsCibles)
    dim = pData.numpy().shape

    le = pExplanation.local_exp[np.argmax(pred)]

    if pEmbedding is not None:
        data = pEmbedding
        coefs = np.zeros(pData["input_ids"].numpy().shape[0])
        base = np.array([pBaseline] * (pData["input_ids"].numpy().shape[0]))
    else:
        data = pData
        coefs = np.zeros(dim)
        base = np.full(dim, pBaseline)

    for v in le:
        coefs[v[0]] = v[1]

    score[pMethode] = 1 if monotonicity_metric(aiModel.useCase, np.array(data), coefs, base) else 0
    # ----------------------------
    #print("ATTENTION :pour accelerer les tests")
    #score[pMethode]=1 if random.random()>0.5 else 0
    # ----------------------------

    print("Metric results saved in '%s.json'"%ficProd)
    with open(ficProd, "w", encoding="utf-8") as f:
        json.dump(score, f, indent=4)

    return score

# ---------------------------------------------------------------------------
## Compute Faithfulness metric for tabular and text data
# @param pDictParams : parameter dictionary
# @param pData : data prepared for inference
# @param pBaseline : baseline value for explanation and metric
# @param pMethode : method on which the meric is computed
# @param pExplanation : explanation
# @param pResPredictionsCibles : target predictions (inference)
# @param pFichProd : file to save without extension
# @param pIdxData : data index in the list of data treated
# @return score
def _metricFaithfulnessTabular(pDictParams, pData, pBaseline, pMethode, pExplanation, pResPredictionsCibles, pFichProd, pIdxData=None):
    # shortcuts
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']

    if not hasattr(aiModel.useCase, 'predict_proba'):
        colPrint("/!\\ The model must implement a method 'predict_proba()'. No calculated metric.", "Error")
        return

    score = {}
    # Si le fichier Json existe déjà : on le lit
    if pIdxData is not None:
        ficProd = '%s--d_%s.json'%(pFichProd, pDataList[pIdxData].replace(' ', ''))
    else:
        ficProd = "%s.json"%pFichProd
    if os.path.exists(ficProd):
        print("    Metric results loaded from '%s'"%ficProd)
        with open(ficProd, "r", encoding="utf-8") as f:
            score = json.load(f)
    score[pMethode] = {}
    scores = []

    for idxItem, _ in enumerate(pData):
        pred = np.array(pResPredictionsCibles[idxItem])
        le = pExplanation[idxItem].local_exp[np.argmax(pred)]

        dim = pData.shape[1]
        coefs = np.zeros(dim)
        for v in le:
            coefs[v[0]] = v[1]

        base = np.array([pBaseline] * dim)
        score[pMethode][idxItem] = faithfulness_metric(aiModel.useCase, np.array(pData[idxItem]), coefs, base)
        # ----------------------------
        #print("ATTENTION :pour accelerer les tests")
        #score[pMethode][idxItem]=random.random()
        # ----------------------------

        scores.append(score[pMethode][idxItem])

    score[pMethode]["mean"] = np.mean([s for s in scores if str(s) != 'nan'])
    print("Metric mean score value is: %s"%str(score[pMethode]["mean"]), flush=True)

    print("Metric results saved in '%s'"%ficProd)
    with open(ficProd, "w", encoding="utf-8") as f:
        json.dump(score, f, indent=4)

    return score

# ---------------------------------------------------------------------------
## Compute Faithfulness metric for image data
# @param pDictParams : parameter dictionary
# @param pData : data prepared for inference
# @param pBaseline : baseline value for explanation and metric
# @param pMethode : method on which the meric is computed
# @param pExplanation : explanation
# @param pResPredictionsCibles : target predictions (inference)
# @param pFichProd : file without extension to store result
# @param pIdxData : data index in the list of data treated
# @return score
def _metricFaithfulnessImage(pDictParams, pData, pBaseline, pMethode, pExplanation, pResPredictionsCibles, pFichProd, pIdxData=None):
    # shortcuts
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']

    if not hasattr(aiModel.useCase, 'predict_proba'):
        colPrint("/!\\ The model must implement a method 'predict_proba()'. No calculated metric.", "Error")
        return

    score = {}
    # Si le fichier Json existe déjà : on le lit
    if pIdxData is not None:
        ficProd = '%s--d_%s.json'%(pFichProd, pDataList[pIdxData].replace(' ', ''))
    else:
        ficProd = "%s.json"%pFichProd
    if os.path.exists(ficProd):
        print("    Metric results loaded from '%s'"%ficProd)
        with open(ficProd, "r", encoding="utf-8") as f:
            score = json.load(f)
    score[pMethode] = {}

    pred = np.array(pResPredictionsCibles)
    dim = pData.numpy().shape
    le = pExplanation.local_exp[np.argmax(pred)]

    coefs = np.zeros(dim)
    base = np.full(dim, pBaseline)

    for v in le:
        coefs[v[0]] = v[1]

    score[pMethode] = faithfulness_metric(aiModel.useCase, np.array(pData), coefs, base)
    # ----------------------------
    #print("ATTENTION :pour accelerer les tests")
    #score[pMethode]=random.random()
    # ----------------------------

    print("Metric results saved in '%s'"%ficProd)
    with open(ficProd, "w", encoding="utf-8") as f:
        json.dump(score, f, indent=4)

    return score

# ---------------------------------------------------------------------------
## Compute metric
# @param pDictParams : parameter dictionary
# @return score
def computeMetricsTabular(pDictParams):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pMetrique = pDictParams['metric']
    pMetricParam = pDictParams[pMetrique]
    pSuffixMetric = pDictParams["suffixMetric"]
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']
    xData, _ = pDictParams['xy']
    pDataProd = pDictParams['dataProd']
    inputXAIframework = pDictParams['inputXAIframework']

    if pDictParams['methods4metric'] == "":
        print("No method selected!")
        return
    pMethods4metric = pDictParams['methods4metric'].split(',')

    # control function for XAI_computeMetrics inputs
    if pMetrique == "Sklearn-Scores":
        inputXAIframework = (pd.DataFrame, inputXAIframework[1])
    pParamSpecif = {"dataSize": pDictParams['datasize']}

    # convert data and prediction to XAI framework
    xData, _ = kaasrc.communs.convertToXAIframework(pDictParams, inputXAIframework)

    kaasrc.controles.controlXAI_computeMetricsInput(pDictParams, inputXAIframework, xData, None, aiModel.useCase, pNbData, __file__, pParamSpecif)

    # compute
    print("   .get metric %s:%s"%(pDictParams['library'], pMetrique), flush=True)
    resultSavedOn = os.path.join(pDataProd, "dataMetrics")

    dicoExplanations = {}
    allScore = {}
    for index in range(pNbData):
        nomData = pDataList[index].replace(' ', '')
        for methode in pMethods4metric:
            methodWithSuffix = "%s_%s"%(methode, pDictParams[methode]['suffixMethod'])

            print("   .Metric on %s method"%methode, flush=True)
            repertProd = os.path.join(pDictParams['code'], "%s_%s"%(methode, pDictParams[methode]['suffixMethod']))
            pDictParams['method'] = methode

            ficExplanation = os.path.join(pDataProd, "dataExplanations", repertProd, 'allData.pkl')
            dicoExplanations[methode] = AIX360_computeExplanations.loadExplanations(pDictParams, ficExplanation, pNbData, True)

            fichProd = kaasrc.communs.noSpace(os.path.join(resultSavedOn, pDictParams['code']), '%s_%s'%(pMetrique, pSuffixMetric))

            if dicoExplanations[methode] is None:
                print("Compute the method %s before to compute the metric"%methode)
                continue

            # Sklearn-Scores
            if pMetrique == "Sklearn-Scores":
                if methode in ["LinearRuleRegression", "LogisticRuleRegression", "BRCGE"]:
                    dicoScores = _metricSklearnScore(pDictParams, xData[index], methodWithSuffix, dicoExplanations[methode][index], aiModel.useCase.resPredictionsCibles[index], fichProd, index)
                    allScore.setdefault(methodWithSuffix, {}).setdefault(nomData, dicoScores[methodWithSuffix])
                else:
                    print("The method %s is not available with the metric Sklearn Scores."%methode, flush=True)

            # Monotonicity
            elif pMetrique == "Monotonicity":
                if methode == "LimeTabular":
                    baseline = float(pMetricParam["b"])
                    embedding = None
                    if 'embedding' in pDictParams:
                        embedding = pDictParams['embedding'][index]
                    dicoScores = _metricMonotonicityTabular(pDictParams, xData[index], baseline, methodWithSuffix, dicoExplanations[methode][index], aiModel.useCase.resPredictionsCibles[index], embedding, fichProd, index)
                    allScore.setdefault(methodWithSuffix, {}).setdefault(nomData, dicoScores[methodWithSuffix]["mean"])
                else:
                    print("The method %s is not available with the metric Monotonicity."%methode, flush=True)

            # Faithfulness
            elif pMetrique == "Faithfulness":
                if methode == "LimeTabular":
                    baseline = float(pMetricParam["b"])
                    dicoScores = _metricFaithfulnessTabular(pDictParams, xData[index], baseline, methodWithSuffix, dicoExplanations[methode][index], aiModel.useCase.resPredictionsCibles[index], fichProd, index)
                    allScore.setdefault(methodWithSuffix, {}).setdefault(nomData, dicoScores[methodWithSuffix]["mean"])
                else:
                    print("The method %s is not available with the metric Faithfulness."%methode, flush=True)

    # save metrics
    fichProd = os.path.join(resultSavedOn, pDictParams['code'], '%s_%s'%(pMetrique, pSuffixMetric))

    print("Metric results saved in '%s.json'"%fichProd)
    with open("%s.json"%fichProd, "w", encoding="utf-8") as f:
        json.dump(allScore, f, indent=4)

    return allScore

# ---------------------------------------------------------------------------
## Compute metric
# @param pDictParams : parameter dictionary
# @return score
def computeMetricsImage(pDictParams):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pMetrique = pDictParams['metric']
    pMetricParam = pDictParams[pMetrique]
    pSuffixMetric = pDictParams["suffixMetric"]
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    _, aiModel = pDictParams['aiModel']
    xData, _ = pDictParams['xy']
    pDataProd = pDictParams['dataProd']
    inputXAIframework = pDictParams['inputXAIframework']

    if pDictParams['methods4metric'] == "":
        print("No method selected!")
        return
    pMethods4metric = pDictParams['methods4metric'].split(',')

    # convert data and prediction to XAI framework
    xData, _ = kaasrc.communs.convertToXAIframework(pDictParams, inputXAIframework)

    # control function for XAI_computeMetrics inputs
    kaasrc.controles.controlXAI_computeMetricsInput(pDictParams, inputXAIframework, xData, None, aiModel.useCase, pNbData, __file__)

    # compute
    print("   .get metric %s:%s"%(pDictParams['library'], pMetrique), flush=True)
    resultSavedOn = os.path.join(pDataProd, "dataMetrics")

    dicoExplanations = {}
    allScore = {}
    fichProd = kaasrc.communs.noSpace(os.path.join(resultSavedOn, pDictParams['code']), '%s_%s'%(pMetrique, pSuffixMetric))

    for methode in pMethods4metric:

        methodWithSuffix = "%s_%s"%(methode, pDictParams[methode]['suffixMethod'])

        print("   .Metric on %s method"%methode, flush=True)
        repertProd = os.path.join(pDictParams['code'], "%s_%s"%(methode, pDictParams[methode]['suffixMethod']))
        ficExplanation = os.path.join(pDataProd, "dataExplanations", repertProd, 'allData.pkl')
        pDictParams['method'] = methode
        dicoExplanations[methode] = AIX360_computeExplanations.loadExplanations(pDictParams, ficExplanation, pNbData, True)

        if dicoExplanations[methode] is None:
            print("Compute the method %s before to compute the metric"%methode)
            continue

        # Sklearn-Scores
        if pMetrique == "Sklearn-Scores":
            if methode in ["LinearRuleRegression", "LogisticRuleRegression", "BRCGE"]:
                for index in range(pNbData):
                    nomData = pDataList[index].replace(' ', '')
                    dicoScores = _metricSklearnScore(pDictParams, xData[index], methodWithSuffix, dicoExplanations[methode][index], aiModel.useCase.resPredictionsCibles[index], "%s--d_%s"%(fichProd, nomData))
                    allScore.setdefault(methodWithSuffix, {}).setdefault(nomData, dicoScores[methodWithSuffix])
            else:
                print("The method %s is not available with the metric Sklearn Scores."%methode, flush=True)

        # Monotonicity
        elif pMetrique == "Monotonicity":
            if methode == "LimeImage":
                baseline = float(pMetricParam["b"])
                scores = []
                for index in range(pNbData):
                    nomData = pDataList[index].replace(' ', '')
                    embedding = None
                    if 'embedding' in pDictParams:
                        embedding = pDictParams['embedding'][index]
                    dicoScores = _metricMonotonicityImage(pDictParams, xData[index], baseline, methodWithSuffix, dicoExplanations[methode][index], aiModel.useCase.resPredictionsCibles[index], fichProd, embedding, index)
                    allScore.setdefault(methodWithSuffix, {}).setdefault(nomData, dicoScores[methodWithSuffix])
                    if dicoScores[methodWithSuffix] != 'nan':
                        scores.append(dicoScores[methodWithSuffix])
                scoreAllData = np.mean(list(scores))
                print("Metric mean score value is: %s"%str(scoreAllData), flush=True)
            else:
                print("The method %s is not available with the metric Monotonicity."%methode, flush=True)

        # Faithfulness
        elif pMetrique == "Faithfulness":
            if methode == "LimeImage":
                baseline = float(pMetricParam["b"])
                scores = []
                for index in range(pNbData):
                    nomData = pDataList[index].replace(' ', '')
                    dicoScores = _metricFaithfulnessImage(pDictParams, xData[index], baseline, methodWithSuffix, dicoExplanations[methode][index], aiModel.useCase.resPredictionsCibles[index], fichProd, index)
                    allScore.setdefault(methodWithSuffix, {}).setdefault(nomData, dicoScores[methodWithSuffix])
                    if dicoScores[methodWithSuffix] != 'nan':
                        scores.append(dicoScores[methodWithSuffix])
                scoreAllData = np.mean(list(scores))
                print("Metric mean score value is: %s"%str(scoreAllData), flush=True)
            else:
                print("The method %s is not available with the metric Faithfulness."%methode, flush=True)

    # save metrics
    fichProd = kaasrc.communs.noSpace(os.path.join(resultSavedOn, pDictParams['code']), '%s_%s'%(pMetrique, pSuffixMetric))

    print("Metric results saved in '%s.json'"%fichProd)
    with open("%s.json"%fichProd, "w", encoding="utf-8") as f:
        json.dump(allScore, f, indent=4)

    return allScore

# ===============================================================================
# end of file
