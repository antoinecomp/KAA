#!/usr/bin/env python3.,
# -*- coding: utf-8 -*-
# ===============================================================================
# import numpy as np
from kaasrc.communs import colPrint

# ---------
try:
    import torch
    ISTORCH = True
except Exception:
    ISTORCH = False
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
def controleRecursif(pType, pExpected, pObtained, pForm, pFunction, pFile, pIter=0):
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
        if isinstance(pObtained, list):
            controle(pType, pExpected[0], len(pObtained), pForm[0], pFunction, pFile)
        else:
            controle(pType, pExpected[0], pObtained.shape, pForm[0], pFunction, pFile)
        rForme = pForm[1:]

    if isinstance(pObtained, list):
        for item in pObtained:
            controleRecursif(pType, pExpected[1:], item, rForme, pFunction, pFile, pIter + 1)

# -------------------------------------------------------------------------------
## Function to control UC_computeInference output
# @param pXData : input data to control
# @param pYPred : prediction to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
def controlUC_computeInferenceOutputSegment(pXData, pYPred, pUseCase, pNbData, pFile):

    colPrint("List of Data", "Normal")

    expected = list
    obtained = type(pXData)
    controle(True, expected, obtained, "(list)", "controlUC_computeInferenceOutputSegment", pFile)

    expected = pNbData
    obtained = len(pXData)
    controle(False, expected, obtained, "n()", "controlUC_computeInferenceOutputSegment", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each data", "Normal")

    for e in range(pNbData):
        expected = pUseCase.inputModelFramework
        obtained = type(pXData[e])
        controle(True, expected, obtained, "(inputModelFramework)", "controlUC_computeInferenceOutputSegment", pFile)

        if ISTORCH and expected == torch.Tensor:
            expected = (1, pUseCase.numImageChannels, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1])
            forme = "(1, B, H, W)"
        else:
            expected = (1, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numImageChannels)
            forme = "(1, H, W, B)"
        obtained = pXData[e].shape
        controle(False, expected, obtained, forme, "controlUC_computeInferenceOutputSegment", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("List of predictions", "Normal")

    expected = list
    obtained = type(pYPred)
    controle(True, expected, obtained, "(list)", "controlUC_computeInferenceOutputSegment", pFile)

    expected = pNbData
    obtained = len(pYPred)
    controle(False, expected, obtained, "n()", "controlUC_computeInferenceOutputSegment", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each Prediction", "Normal")

    for e in range(pNbData):
        expected = pUseCase.outputModelFramework
        obtained = type(pYPred[e])
        controle(True, expected, obtained, "(outputModelFramework)", "controlUC_computeInferenceOutputObject", pFile)

        expected = pUseCase.outputModelSize
        obtained = pYPred[e].shape
        controle(False, expected, obtained, "(n, C)", "controlUC_computeInferenceOutputObject", pFile)

# -------------------------------------------------------------------------------
## Function to control XAI_computeExplanations output
# @param pInputXAIframework : framework of the method input
# @param pXData : input data to control
# @param pYPred : prediction to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlXAI_computeExplanationsInputSegment(pInputXAIframework, pXData, pYPred, pUseCase, pNbData, pFile, pParamSpecif):

    colPrint("List of Data", "Normal")

    expected = list
    obtained = type(pXData)
    controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsInputSegment", pFile)

    expected = pNbData
    obtained = len(pXData)
    controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsInputSegment", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each data", "Normal")

    if pParamSpecif["initFormat1"]:
        initExpected = (1, )
        initForme = "1, "
    else:
        initExpected = ()
        initForme = ""

    for e in range(pNbData):
        expected = pInputXAIframework[0]
        obtained = type(pXData[e])
        controle(True, expected, obtained, "(inputXAIframework)", "controlXAI_computeExplanationsInputSegment", pFile)

        if ISTORCH and pUseCase.inputModelFramework == torch.Tensor:
            expected = initExpected + (pUseCase.inputModelSize[1], pUseCase.inputModelSize[0], pUseCase.numImageChannels)
            forme = "(%sW, H, B)"%initForme
        else:
            expected = initExpected + (pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numImageChannels)
            forme = "(%sH, W, B)"%initForme
        obtained = pXData[e].shape
        controle(False, expected, obtained, forme, "controlXAI_computeExplanationsInputSegment", pFile)

    if pYPred is not None:
        colPrint(" --------------------------------------------", "Normal")
        colPrint("List of predictions", "Normal")

        expected = list
        obtained = type(pYPred)
        controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsInputSegment", pFile)

        expected = pNbData
        obtained = len(pYPred)
        controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsInputSegment", pFile)

        colPrint(" --------------------------------------------", "Normal")
        colPrint("Each Prediction", "Normal")

        pNbSegment = pParamSpecif["nbSegm"]
        # print("DNG >  - pNbSegment", pNbSegment)
        for e in range(pNbData):
            expected = pInputXAIframework[1]
            obtained = type(pYPred[e])
            controle(True, expected, obtained, "(inputXAIframework)", "controlXAI_computeExplanationsInputSegment", pFile)

            if ISTORCH and pUseCase.inputModelFramework == torch.Tensor:
                expected = (pUseCase.inputModelSize[1], pUseCase.inputModelSize[0], pNbSegment[e])
                forme = "(W, H, n)"
            else:
                expected = (pNbSegment[e], pUseCase.inputModelSize[0], pUseCase.inputModelSize[1])
                forme = "(n, H, W)"
            obtained = pYPred[e].shape
            controle(False, expected, obtained, "(n, C)", "controlXAI_computeExplanationsInputSegment", pFile)

# -------------------------------------------------------------------------------
## Function to control XAI_computeExplanations output
# @param pOutputXAIFramework : framework of the method output
# @param pExplanation : explanation to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlXAI_computeExplanationsOutputSegment(pOutputXAIFramework, pExplanation, pUseCase, pNbData, pFile, pParamSpecif):

    if "expected" in pParamSpecif:
        expectedShape = pParamSpecif["expected"]
        formeShape = pParamSpecif["format"]

        if isinstance(pOutputXAIFramework, tuple):
            expected = pOutputXAIFramework
            obtained = pExplanation
            controleRecursif(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation
            controleRecursif(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile)
        else:
            expected = pOutputXAIFramework
            obtained = type(pExplanation)
            controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation.shape
            controle(False, expected, obtained, formeShape, "controlXAI_computeExplanationsOutput", pFile)
    else:
        colPrint("List of explanation", "Normal")

        expected = list
        obtained = type(pExplanation)
        controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsOutputSegment", pFile)

        expected = pNbData
        obtained = len(pExplanation)
        controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsOutputSegment", pFile)

        colPrint(" --------------------------------------------", "Normal")
        colPrint("Each explanation", "Normal")

        for e in range(pNbData):
            expected = pOutputXAIFramework
            obtained = type(pExplanation[e])
            controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutputSegment", pFile)

            if ISTORCH and pUseCase.inputModelFramework == torch.Tensor:
                expected = (pUseCase.inputModelSize[1], pUseCase.inputModelSize[0], 1)
                forme = "(W, H, 1)"
            else:
                expected = (pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], 1)
                forme = "(H, W, 1)"
            obtained = pExplanation[e].shape
            controle(False, expected, obtained, forme, "controlXAI_computeExplanationsOutputSegment", pFile)

# ===============================================================================
# end of file
