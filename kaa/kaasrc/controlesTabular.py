#!/usr/bin/env python3.,
# -*- coding: utf-8 -*-
# ===============================================================================
import numpy as np
from kaasrc.communs import colPrint

# ---------
try:
    import tensorflow.python.framework.ops as eTensor
    ISTENSORFLOW = True
except Exception:
    ISTENSORFLOW = False
# ---------
try:
    import shap
    ISSHAP = True
except Exception:
    ISSHAP = False
# ---------

# -------------------------------------------------------------------------------
## Basis control function
# @param pType : type of control (type vs size of data)
# @param pExpected : expected value
# @param pObtained : obtained value to control
# @param pForm : data schema
# @param pFunction : function in which the control is done
# @param pFile : file in which the control is done
def controle(pType, pExpected, pObtained, pForm, pFunction, pFile):
    if pType:
        strTypeShape = "  TYPE:  "
    else:
        strTypeShape = "  SHAPE: "
    if pObtained == pExpected:
        colPrint("%sOK - %s - %s"%(strTypeShape, str(pExpected), pForm), "Action")
    elif pType and (pObtained == type(None)):
        colPrint("%sNA"%strTypeShape, "Select")
        colPrint("    expected %s %s"%(str(pExpected), pForm), "Select")
        colPrint("    obtained %s"%str(pObtained), "Select")
        colPrint("  Checked by '%s()' in file: "%pFunction, "Debug")
        colPrint("    %s"%pFile, "Debug")
    else:
        colPrint("%sKO"%strTypeShape, "Config")
        colPrint("    expected %s %s"%(str(pExpected), pForm), "Config")
        colPrint("    obtained %s"%str(pObtained), "Config")
        colPrint("  Checked by '%s()' in file: "%pFunction, "Debug")
        colPrint("    %s"%pFile, "Debug")

# -------------------------------------------------------------------------------
## recursive control function
# @param pType : type of control (type vs size of data)
# @param pExpected : expected value
# @param pObtained : obtained value to control
# @param pForm : data schema
# @param pFunction : function in which the control is done
# @param pFile : file in which the control is done
# @param pIter : iteration number
# @param pLevelData : level of data if its list or tuple
# @param pCurLevelData : current level
def controleRecursif(pType, pExpected, pObtained, pForm, pFunction, pFile, pIter=0, pLevelData=None, pCurLevelData=None):
    # sauvegarede du message
    forme = pForm

    # Cas du test TYPE
    if pType:
        if pIter > 0:
            forme = forme + " - level %d"%pIter
        controle(pType, pExpected[0], type(pObtained), forme, pFunction, pFile)
        rForme = pForm
    else:
        # Cas du test SHAPE
        if type(pObtained) in [list, tuple]:
            controle(pType, pExpected[0], len(pObtained), pForm[0], pFunction, pFile)
        elif isinstance(pObtained, dict) or pExpected[0] is None or pObtained is None:
            colPrint("   --Cannot control the element size-- ", "Info")
        else:
            controle(pType, pExpected[0], pObtained.shape, pForm[0], pFunction, pFile)
        rForme = pForm[1:]

    if type(pObtained) in [list, tuple]:
        if pLevelData is not None:
            for item, _ in enumerate(pObtained):
                newExpected = pExpected[1:]
                if newExpected[0] is None:
                    colPrint("   --Cannot control the element size-- ", "Info")
                    break
                if pIter == pLevelData[0]:
                    pCurLevelData = item
                if pIter == pLevelData[1] - 1:
                    curData = pExpected[1:][0][pCurLevelData]
                    newExpected = [curData]
                    if len(pExpected) > 2:
                        newExpected.extend(pExpected[2:])
                controleRecursif(pType, newExpected, pObtained[item], rForme, pFunction, pFile, pIter + 1, pLevelData, pCurLevelData)
        else:
            for item in pObtained:
                controleRecursif(pType, pExpected[1:], item, rForme, pFunction, pFile, pIter + 1)

# -------------------------------------------------------------------------------
## Function to control (1)
# @param pData : data to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlFctPrepareDataOutputTabular(pData, pUseCase, pFile, pParamSpecif):

    expected = pUseCase.inputModelFramework
    obtained = type(pData)
    controle(True, expected, obtained, "(inputModelFramework)", "controlFctPrepareDataOutput", pFile)

    numLig = pParamSpecif["numLig"] if "numLig" in pParamSpecif else None
    if pUseCase.inputModelSize[0] is not None:
        numLig = pUseCase.inputModelSize[0]
    if numLig is None:
        colPrint("    Undefined line number.", "Error")

    numCol = pParamSpecif["numCol"] if "numCol" in pParamSpecif else None
    if pUseCase.inputModelSize[1] is not None:
        numCol = pUseCase.inputModelSize[1]
    if numCol is None:
        colPrint("    Undefined column number.", "Error")

    expected = (numLig, numCol)
    forme = "(l, f)"
    obtained = pData.shape
    controle(False, expected, obtained, forme, "controlFctPrepareDataOutput", pFile)

# -------------------------------------------------------------------------------
## Function to control (2)
# @param pData : data to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlInferenceInputTabular(pData, pUseCase, pFile, pParamSpecif):

    expected = pUseCase.inputModelFramework
    obtained = type(pData)
    controle(True, expected, obtained, "(inputModelFramework)", "controlInferenceInput", pFile)

    numLig = pParamSpecif["numLig"] if "numLig" in pParamSpecif else None
    if pUseCase.inputModelSize[0] is not None:
        numLig = pUseCase.inputModelSize[0]
    if numLig is None:
        colPrint("    Undefined line number.", "Error")

    numCol = pParamSpecif["numCol"] if "numCol" in pParamSpecif else None
    if pUseCase.inputModelSize[1] is not None:
        numCol = pUseCase.inputModelSize[1]
    if numCol is None:
        colPrint("    Undefined column number.", "Error")

    expected = (numLig, numCol)
    forme = "(l, f)"
    obtained = pData.shape
    controle(False, expected, obtained, forme, "controlInferenceInput", pFile)

# -------------------------------------------------------------------------------
## Function to control (3)
# @param pData : data to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlInferenceOutputTabular(pData, pUseCase, pFile, pParamSpecif):

    colPrint("Control Inference outputs", "Normal")

    expected = pUseCase.outputModelFramework
    obtained = type(pData)
    controle(True, expected, obtained, "(outputModelFramework)", "controlInferenceOutput", pFile)

    numLig = pParamSpecif["numLig"] if "numLig" in pParamSpecif else None
    if pUseCase.inputModelSize[0] is not None:
        numLig = pUseCase.inputModelSize[0]
    if numLig is None:
        colPrint("    Undefined line number.", "Error")

    numCol = pParamSpecif["numCol"] if "numCol" in pParamSpecif else None
    if pUseCase.inputModelSize[1] is not None:
        numCol = pUseCase.inputModelSize[1]
    if numCol is None:
        colPrint("    Undefined column number.", "Error")

    expected = (numLig, numCol)
    forme = "(l, f)"
    obtained = pData.shape
    controle(False, expected, obtained, forme, "controlInferenceOutput", pFile)

# -------------------------------------------------------------------------------
## Function to control UC_computeInference output
# @param pXData : input data to control
# @param pYPred : prediction to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlUC_computeInferenceOutputTabular(pXData, pYPred, pUseCase, pNbData, pFile, pParamSpecif):

    colPrint("List of Data", "Normal")
    pDataSize = pParamSpecif["dataSize"]

    expected = list
    obtained = type(pXData)
    controle(True, expected, obtained, "(list)", "controlUC_computeInferenceOutputTabular", pFile)

    expected = pNbData
    obtained = len(pXData)
    controle(False, expected, obtained, "n()", "controlUC_computeInferenceOutputTabular", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each data", "Normal")

    for e in range(pNbData):
        expected = pUseCase.inputModelFramework
        obtained = type(pXData[e])
        controle(True, expected, obtained, "(inputModelFramework)", "controlUC_computeInferenceOutputTabular", pFile)

        if pUseCase.inputModelSize[0] is not None:
            numLig = pUseCase.inputModelSize[0]
        else:
            numLig = pDataSize[e][0]
        if pUseCase.inputModelSize[1] is not None:
            numCol = pUseCase.inputModelSize[1]
        else:
            numCol = pDataSize[e][1]
        expected = (numLig, numCol)
        forme = "(l, f)"
        if not isinstance(pXData[e], list):
            obtained = pXData[e].shape
            controle(False, expected, obtained, forme, "controlUC_computeInferenceOutputTabular", pFile)
        else:
            colPrint("  KO  --Cannot control the size of the data  --(%s)"%type(pXData[e]), "Config")

    colPrint(" --------------------------------------------", "Normal")
    colPrint("List of predictions", "Normal")

    expected = list
    obtained = type(pYPred)
    controle(True, expected, obtained, "(list)", "controlUC_computeInferenceOutputTabular", pFile)

    expected = pNbData
    obtained = len(pYPred)
    controle(False, expected, obtained, "n()", "controlUC_computeInferenceOutputTabular", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each Prediction", "Normal")

    for e in range(pNbData):
        expected = pUseCase.outputModelFramework
        obtained = type(pYPred[e])
        controle(True, expected, obtained, "(outputModelFramework)", "controlUC_computeInferenceOutputTabular", pFile)

        if pUseCase.outputModelSize[0] is not None:
            numLig = pUseCase.outputModelSize[0]
        else:
            numLig = pDataSize[e][0]
        if pUseCase.outputModelSize[1] is not None:
            numCol = pUseCase.outputModelSize[1]
        else:
            numCol = pDataSize[e][1]
        expected = (numLig, numCol)
        forme = "(l, f)"
        obtained = pYPred[e].shape
        controle(False, expected, obtained, "(n, C)", "controlUC_computeInferenceOutputTabular", pFile)

# -------------------------------------------------------------------------------
## Function to control UC_computeInference output
# @param pInputXAIframework : framework of the method input
# @param pXData : input data to control
# @param pYPred : prediction to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlXAI_computeExplanationsInputTabular(pInputXAIframework, pXData, pYPred, pUseCase, pNbData, pFile, pParamSpecif):

    colPrint("List of Data", "Normal")
    pDataSize = pParamSpecif["dataSize"]

    expected = list
    obtained = type(pXData)
    controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsInputTabular", pFile)

    expected = pNbData
    obtained = len(pXData)
    controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsInputTabular", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each data", "Normal")

    for e in range(pNbData):
        expected = pInputXAIframework[0]
        obtained = type(pXData[e])
        controle(True, expected, obtained, "(inputModelFramework)", "controlXAI_computeExplanationsInputTabular", pFile)

        if pUseCase.inputModelSize[0] is not None:
            numLig = pUseCase.inputModelSize[0]
        else:
            numLig = pDataSize[e][0]
        if pUseCase.inputModelSize[1] is not None:
            numCol = pUseCase.inputModelSize[1]
        else:
            numCol = pDataSize[e][1]
        expected = (numLig, numCol)
        forme = "(l, f)"
        obtained = pXData[e].shape
        controle(False, expected, obtained, forme, "controlXAI_computeExplanationsInputTabular", pFile)

    if pYPred is not None:
        colPrint(" --------------------------------------------", "Normal")
        colPrint("List of predictions", "Normal")

        expected = list
        obtained = type(pYPred)
        controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsInputTabular", pFile)

        expected = pNbData
        obtained = len(pYPred)
        controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsInputTabular", pFile)

        colPrint(" --------------------------------------------", "Normal")
        colPrint("Each Prediction", "Normal")

        for e in range(pNbData):
            expected = pInputXAIframework[1]
            obtained = type(pYPred[e])
            controle(True, expected, obtained, "(inputXAIframework)", "controlXAI_computeExplanationsInputTabular", pFile)

            if pUseCase.outputModelSize[0] is not None:
                numLig = pUseCase.outputModelSize[0]
            else:
                numLig = pDataSize[e][0]
            if pUseCase.outputModelSize[1] is not None:
                numCol = pUseCase.outputModelSize[1]
            else:
                numCol = pDataSize[e][1]
            expected = (numLig, numCol)
            forme = "(l, f)"
            obtained = pYPred[e].shape
            controle(False, expected, obtained, "(n, C)", "controlXAI_computeExplanationsInputTabular", pFile)

# -------------------------------------------------------------------------------
## Function to control XAI_computeExplanations output
# @param pOutputXAIFramework : framework of the method output
# @param pExplanation : explanation to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlXAI_computeExplanationsOutputTabular(pOutputXAIFramework, pExplanation, pUseCase, pNbData, pFile, pParamSpecif):

    if "expected" in pParamSpecif:
        expectedShape = pParamSpecif["expected"]
        levelData = pParamSpecif["levelData"] if "levelData" in pParamSpecif else None
        formeShape = pParamSpecif["format"]

        if isinstance(pOutputXAIFramework, tuple):
            expected = pOutputXAIFramework
            obtained = pExplanation
            controleRecursif(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation
            controleRecursif(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile, pLevelData=levelData)
        else:
            expected = pOutputXAIFramework
            obtained = type(pExplanation)
            controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation.shape
            controle(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile)
    else:
        expected = pOutputXAIFramework
        for e in pExplanation:
            obtained = type(e)
            controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutputTabular", pFile)

        colPrint("Each explanation", "Normal")

        xDataSize = pParamSpecif['dataSize']
        nbClasses = pParamSpecif['nbClasses'] if 'nbClasses' in pParamSpecif else None
        for d in range(pNbData):

            if pUseCase.inputModelSize[0] is not None:
                numLig = pUseCase.inputModelSize[0]
            else:
                numLig = xDataSize[d][0]
            if pUseCase.inputModelSize[1] is not None:
                numCol = pUseCase.inputModelSize[1]
            else:
                numCol = xDataSize[d][1]
            if nbClasses is None:
                expected = (numLig, numCol)
                forme = "(l, f)"
            else:
                expected = (numLig, numCol, nbClasses)
                forme = "(l, f, C)"
            if isinstance(pExplanation[d], list):
                colPrint(" --Cannot control the size of the data  --%s", "Config")
            elif ISTENSORFLOW and type(pExplanation[d]) in [np.ndarray, eTensor.EagerTensor]:
                obtained = pExplanation[d].shape
                controle(False, expected, obtained, forme, "controlXAI_computeExplanationsOutputTabular", pFile)
            elif ISSHAP and type(pExplanation[d]) == shap._explanation.Explanation:
                obtained = pExplanation[d].shape
                controle(False, expected, obtained, forme, "controlXAI_computeExplanationsOutputTabular", pFile)
            else:
                colPrint(" --Cannot control the size of the data-- ", "Config")

# -------------------------------------------------------------------------------
## Function to control XAI_computeExplanations output
# @param pOutputXAIFramework : framework of the method output
# @param pExplanation : explanation to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def control_loadExplanationsOutputTabular(pOutputXAIFramework, pExplanation, pUseCase, pFile, pParamSpecif):

    if "expected" in pParamSpecif:
        expectedShape = pParamSpecif["expected"]
        levelData = pParamSpecif["levelData"] if "levelData" in pParamSpecif else None
        formeShape = pParamSpecif["format"]

        if isinstance(pOutputXAIFramework, tuple):
            expected = pOutputXAIFramework
            obtained = pExplanation
            controleRecursif(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation
            controleRecursif(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile, pLevelData=levelData)
        else:
            expected = pOutputXAIFramework
            obtained = type(pExplanation)
            controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation.shape
            controle(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile)
    else:
        if ISTENSORFLOW and pOutputXAIFramework == eTensor.EagerTensor:
            pOutputXAIFramework = np.ndarray
        expected = pOutputXAIFramework
        obtained = type(pExplanation)
        controle(True, expected, obtained, "(outputXAIFramework)", "control_loadExplanationsOutputTabular", pFile)

        xDataSize = pParamSpecif['dataSize']
        nbClasses = pParamSpecif['nbClasses'] if 'nbClasses' in pParamSpecif else None

        if pUseCase.inputModelSize[0] is not None:
            numLig = pUseCase.inputModelSize[0]
        else:
            numLig = xDataSize[0]
        if pUseCase.inputModelSize[1] is not None:
            numCol = pUseCase.inputModelSize[1]
        else:
            numCol = xDataSize[1]
        if nbClasses is not None:
            expected = (numLig, numCol, nbClasses)
            forme = "(l, f, c)"
        else:
            expected = (numLig, numCol)
            forme = "(l, f)"
        obtained = pExplanation.shape
        controle(False, expected, obtained, forme, "control_loadExplanationsOutputTabular", pFile)

# -------------------------------------------------------------------------------
## Function to control (8)
# @param pOutputXAIFramework : framework of the method output
# @param pExplanation : explanation to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def control_plotExplanationOneTable(pOutputXAIFramework, pExplanation, pUseCase, pFile, pParamSpecif):

    if "expected" in pParamSpecif:
        expectedShape = pParamSpecif["expected"]
        formeShape = pParamSpecif["format"]

        if isinstance(pOutputXAIFramework, tuple):
            expected = pOutputXAIFramework
            obtained = pExplanation
            controleRecursif(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            if "noShapeControl" not in pParamSpecif or not pParamSpecif["noShapeControl"]:
                expected = expectedShape
                obtained = pExplanation
                controleRecursif(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile)
            else:
                colPrint("   --Cannot control the size of the element  --(%s)"%str(expected), "Select")

        else:
            expected = pOutputXAIFramework
            obtained = type(pExplanation)
            controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation.shape
            controle(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile)
    else:
        if ISTENSORFLOW and pOutputXAIFramework == eTensor.EagerTensor:
            pOutputXAIFramework = np.ndarray
        expected = pOutputXAIFramework
        obtained = type(pExplanation)
        controle(True, expected, obtained, "(outputXAIFramework)", "control_plotExplanationOneTable", pFile)

        xDataSize = pParamSpecif['dataSize']
        nbClasses = pParamSpecif['nbClasses'] if 'nbClasses' in pParamSpecif else None

        if pUseCase.inputModelSize[0] is not None:
            numLig = pUseCase.inputModelSize[0]
        else:
            numLig = xDataSize[0]
        if pUseCase.inputModelSize[1] is not None:
            numCol = pUseCase.inputModelSize[1]
        else:
            numCol = xDataSize[1]
        if nbClasses is not None:
            expected = (numLig, numCol, nbClasses)
            forme = "(l, f, c)"
        else:
            expected = (numLig, numCol)
            forme = "(l, f)"
        obtained = pExplanation.shape
        controle(False, expected, obtained, forme, "control_plotExplanationOneTable", pFile)

# ===============================================================================
# end of file
