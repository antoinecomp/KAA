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
## Function to control UC_computeInference output
# @param pXData : input data to control
# @param pYPred : prediction to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlUC_computeInferenceOutputObject(pXData, pYPred, pUseCase, pNbData, pFile, pParamSpecif):

    colPrint("List of Data", "Normal")

    expected = list
    obtained = type(pXData)
    controle(True, expected, obtained, "(list)", "controlUC_computeInferenceOutputObject", pFile)

    expected = pNbData
    obtained = len(pXData)
    controle(False, expected, obtained, "n()", "controlUC_computeInferenceOutputObject", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each data", "Normal")

    for e in range(pNbData):
        expected = pUseCase.inputModelFramework
        obtained = type(pXData[e])
        controle(True, expected, obtained, "(inputModelFramework)", "controlUC_computeInferenceOutputObject", pFile)

        if ISTORCH and expected == torch.Tensor:
            expected = (1, pUseCase.numImageChannels, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1])
            forme = "(1, B, H, W)"
        else:
            expected = (1, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numImageChannels)
            forme = "(1, H, W, B)"
        obtained = pXData[e].shape
        controle(False, expected, obtained, forme, "controlUC_computeInferenceOutputObject", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("List of predictions", "Normal")

    expected = list
    obtained = type(pYPred)
    controle(True, expected, obtained, "(list)", "controlUC_computeInferenceOutputObject", pFile)

    expected = pNbData
    obtained = len(pYPred)
    controle(False, expected, obtained, "n()", "controlUC_computeInferenceOutputObject", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each Prediction", "Normal")

    for e in range(pNbData):
        expected = pUseCase.outputModelFramework
        obtained = type(pYPred[e])
        controle(True, expected, obtained, "(outputModelFramework)", "controlUC_computeInferenceOutputObject", pFile)

        expected = (pParamSpecif["nbBbx"][e], pUseCase.outputModelSize)
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
def controlXAI_computeExplanationsInputObject(pInputXAIframework, pXData, pYPred, pUseCase, pNbData, pFile, pParamSpecif):

    colPrint("List of Data", "Normal")

    expected = list
    obtained = type(pXData)
    controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsInputObject", pFile)

    expected = pNbData
    obtained = len(pXData)
    controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsInputObject", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each data", "Normal")

    for e in range(pNbData):
        expected = pInputXAIframework[0]
        obtained = type(pXData[e])
        controle(True, expected, obtained, "(inputXAIframework)", "controlXAI_computeExplanationsInputObject", pFile)

        if ISTORCH and pUseCase.inputModelFramework == torch.Tensor:
            expected = (1, pUseCase.inputModelSize[1], pUseCase.inputModelSize[0], pUseCase.numImageChannels)
            forme = "(1, W, H, B)"
        else:
            expected = (1, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numImageChannels)
            forme = "(1, H, W, B)"
        obtained = pXData[e].shape
        controle(False, expected, obtained, forme, "controlXAI_computeExplanationsInputObject", pFile)

    if pYPred is not None:
        colPrint(" --------------------------------------------", "Normal")
        colPrint("List of predictions", "Normal")

        expected = list
        obtained = type(pYPred)
        controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsInputObject", pFile)

        expected = pNbData
        obtained = len(pYPred)
        controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsInputObject", pFile)

        colPrint(" --------------------------------------------", "Normal")
        colPrint("Each Prediction", "Normal")

        for e in range(pNbData):
            expected = pInputXAIframework[1]
            obtained = type(pYPred[e])
            controle(True, expected, obtained, "(inputXAIframework)", "controlXAI_computeExplanationsInputObject", pFile)

            expected = (pParamSpecif["nbBbx"][e], pUseCase.outputModelSize)
            obtained = pYPred[e].shape
            controle(False, expected, obtained, "(n, C)", "controlXAI_computeExplanationsInputObject", pFile)

# -------------------------------------------------------------------------------
## Function to control XAI_computeExplanations output
# @param pOutputXAIFramework : framework of the method output
# @param pExplanation : explanation to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
def controlXAI_computeExplanationsOutputObject(pOutputXAIFramework, pExplanation, pUseCase, pNbData, pFile):

    colPrint("List of explanation", "Normal")

    expected = list
    obtained = type(pExplanation)
    controle(True, expected, obtained, "(list)", "controlXAI_computeExplanationsOutputObject", pFile)

    expected = pNbData
    obtained = len(pExplanation)
    controle(False, expected, obtained, "n()", "controlXAI_computeExplanationsOutputObject", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Each explanation", "Normal")

    for e in range(pNbData):
        expected = pOutputXAIFramework
        obtained = type(pExplanation[e])
        controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutputObject", pFile)

        if ISTORCH and pUseCase.inputModelFramework == torch.Tensor:
            expected = (pUseCase.inputModelSize[1], pUseCase.inputModelSize[0], 1)
            forme = "(W, H, 1)"
        else:
            expected = (pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], 1)
            forme = "(H, W, 1)"
        obtained = pExplanation[e].shape
        controle(False, expected, obtained, forme, "controlXAI_computeExplanationsOutputObject", pFile)

# ===============================================================================
# end of file
