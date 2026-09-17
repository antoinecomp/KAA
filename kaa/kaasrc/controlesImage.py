#!/usr/bin/env python3
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
        elif isinstance(pObtained, dict) or pExpected[0] is None:
            colPrint("   --Cannot control the element size-- ", "Info")
        else:
            controle(pType, pExpected[0], pObtained.shape, pForm[0], pFunction, pFile)
        rForme = pForm[1:]

    if isinstance(pObtained, list):
        for item in pObtained:
            controleRecursif(pType, pExpected[1:], item, rForme, pFunction, pFile, pIter + 1)

# -------------------------------------------------------------------------------
## Function to control (1)
# @param pData : data to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
def controlFctPrepareDataOutputImage(pData, pUseCase, pFile):

    expected = pUseCase.inputModelFramework
    obtained = type(pData)
    controle(True, expected, obtained, "(inputModelFramework)", "controlFctPrepareDataOutput", pFile)

    if ISTORCH and expected == torch.Tensor:
        expected = (1, pUseCase.numDataChannels, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1])
        forme = "(1, B, H, W)"
    else:
        expected = (1, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numDataChannels)
        forme = "(1, H, W, B)"

    obtained = pData.shape
    controle(False, expected, obtained, forme, "controlFctPrepareDataOutput", pFile)

# -------------------------------------------------------------------------------
## Function to control (2)
# @param pData : data to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
def controlInferenceInputImage(pData, pUseCase, pFile):

    expected = pUseCase.inputModelFramework
    obtained = type(pData)
    controle(True, expected, obtained, "(inputModelFramework)", "controlInferenceInput", pFile)

    if ISTORCH and expected == torch.Tensor:
        expected = (1, pUseCase.numDataChannels, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1])
        forme = "(1, B, H, W)"
    else:
        expected = (1, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numDataChannels)
        forme = "(1, H, W, B)"
    obtained = pData.shape
    controle(False, expected, obtained, forme, "controlInferenceInput", pFile)

# -------------------------------------------------------------------------------
## Function to control (3)
# @param pData : data to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlInferenceOutputImage(pData, pUseCase, pFile, pParamSpecif):

    expected = pUseCase.outputModelFramework
    obtained = type(pData)
    controle(True, expected, obtained, "(outputModelFramework)", "controlInferenceOutput", pFile)

    pNbBbx = pParamSpecif["nbBbx"] if "nbBbx" in pParamSpecif else None
    pNbSegm = pParamSpecif["nbSegm"] if "nbSegm" in pParamSpecif else None

    if pNbBbx is not None:
        expected = (pNbBbx, pUseCase.outputModelSize)
        forme = "(n, C)"
    elif pNbSegm is not None:
        expected = pUseCase.outputModelSize
        forme = "(C, H, W)"
    else:
        expected = (1, pUseCase.outputModelSize)
        forme = "(1, C)"
    obtained = pData.shape
    controle(False, expected, obtained, forme, "controlInferenceOutput", pFile)

# -------------------------------------------------------------------------------
## Function to control (4)
# @param pXData : input data to control
# @param pYPred : prediction to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
def controlUC_computeInferenceOutputImage(pXData, pYPred, pUseCase, pNbData, pFile):

    expected = pUseCase.inputModelFramework
    obtained = type(pXData)
    controle(True, expected, obtained, "(inputModelFramework)", "controlUC_computeInferenceOutput", pFile)

    if ISTORCH and pUseCase.inputModelFramework == torch.Tensor:
        expected = (pNbData, pUseCase.numDataChannels, pUseCase.inputModelSize[1], pUseCase.inputModelSize[0])
        forme = "(n, B, W, H)"
    else:
        expected = (pNbData, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numDataChannels)
        forme = "(n, H, W, B)"
    obtained = pXData.shape
    controle(False, expected, obtained, forme, "controlUC_computeInferenceOutput", pFile)

    colPrint(" --------------------------------------------", "Normal")
    colPrint("Prediction", "Normal")

    expected = pUseCase.outputModelFramework
    obtained = type(pYPred)
    controle(True, expected, obtained, "(outputModelFramework)", "controlUC_computeInferenceOutput", pFile)

    expected = (pNbData, pUseCase.outputModelSize)
    obtained = pYPred.shape
    controle(False, expected, obtained, "(n, C)", "controlUC_computeInferenceOutput", pFile)

# -------------------------------------------------------------------------------
## Function to control (5)
# @param pInputXAIframework : framework of the method input
# @param pXData : input data to control
# @param pYPred : prediction to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
def controlXAI_computeExplanationsInputImage(pInputXAIframework, pXData, pYPred, pUseCase, pNbData, pFile):

    colPrint("Data", "Normal")
    expected = pInputXAIframework[0]
    obtained = type(pXData)
    controle(True, expected, obtained, "(inputXAIframework)", "controlXAI_computeExplanationsInput", pFile)

    if ISTORCH and expected==torch.Tensor:
        expected = (pNbData, pUseCase.numDataChannels, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1])
        forme = "(n, B, H, W)"
    else:
        expected = (pNbData, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pUseCase.numDataChannels)
        forme = "(n, H, W, B)"
    obtained = pXData.shape
    controle(False, expected, obtained, forme, "controlXAI_computeExplanationsInput", pFile)

    if pYPred is not None:
        colPrint(" --------------------------------------------", "Normal")
        colPrint("Prediction", "Normal")

        expected = pInputXAIframework[1]
        obtained = type(pYPred)
        controle(True, expected, obtained, "(inputXAIframework)", "controlXAI_computeExplanationsInput", pFile)

        expected = (pNbData, pUseCase.outputModelSize)
        obtained = pYPred.shape
        controle(False, expected, obtained, "(n, C)", "controlXAI_computeExplanationsInput", pFile)

# -------------------------------------------------------------------------------
## Function to control (6)
# @param pOutputXAIFramework : framework of the method output
# @param pExplanation : explanation to control
# @param pUseCase : class of the usecase plugin
# @param pNbData : number of data to treat
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def controlXAI_computeExplanationsOutputImage(pOutputXAIFramework, pExplanation, pUseCase, pNbData, pFile, pParamSpecif):

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
        expected = pOutputXAIFramework
        obtained = type(pExplanation)
        controle(True, expected, obtained, "(outputXAIFramework)", "controlXAI_computeExplanationsOutput", pFile)

        pNbClasses = pParamSpecif["nbClasses"] if "nbClasses" in pParamSpecif else None
        pExplOutputDim = pParamSpecif["explOutputDim"] if "explOutputDim" in pParamSpecif else pUseCase.numDataChannels
        if pNbClasses is not None:
            if ISTORCH and expected==torch.Tensor:
                forme = "(n, C, B, H, W)"
                expected = (pNbData, pNbClasses, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pExplOutputDim)
            else:
                forme = "(n, B, H, W, C)"
                expected = (pNbData, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pExplOutputDim, pNbClasses)
        else:
            if ISTORCH and expected==torch.Tensor:
                forme = "(n, B, H, W)"
                expected = (pNbData, pExplOutputDim, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1])
            else:
                forme = "(n, H, W, B)"
                expected = (pNbData, pUseCase.inputModelSize[0], pUseCase.inputModelSize[1], pExplOutputDim)
        obtained = pExplanation.shape
        controle(False, expected, obtained, forme, "controlXAI_computeExplanationsOutput", pFile)

# -------------------------------------------------------------------------------
## Function to control (7)
# @param pOutputXAIFramework : framework of the method output
# @param pExplanation : explanation to control
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def control_loadExplanationsOutputImage(pOutputXAIFramework, pExplanation, pUseCase, pFile, pParamSpecif):

    if "expected" in pParamSpecif:
        expectedShape = pParamSpecif["expected"]
        formeShape = pParamSpecif["format"]

        if isinstance(pOutputXAIFramework, tuple):
            expected = pOutputXAIFramework
            obtained = pExplanation
            controleRecursif(True, expected, obtained, "(outputXAIFramework)", "control_loadExplanationsOutput", pFile)

            expected = expectedShape
            obtained = pExplanation
            controleRecursif(False, expected, obtained, formeShape, "control_loadExplanationsOutput", pFile)
        else:
            expected = pOutputXAIFramework
            obtained = type(pExplanation)
            controle(True, expected, obtained, "(outputXAIFramework)", "control_loadExplanationsOutput", pFile)

            if expectedShape is None:
                colPrint("   --Cannot control the element size-- ", "Info")
            else:
                expected = expectedShape
                obtained = pExplanation.shape
                controle(False, expected, obtained, formeShape, "control_loadExplanationsOutput", pFile)
    else:
        if ISTENSORFLOW and pOutputXAIFramework == eTensor.EagerTensor:
            pOutputXAIFramework = np.ndarray

        expected = pOutputXAIFramework
        obtained = type(pExplanation)
        controle(True, expected, obtained, "outputXAIFramework", "control_loadExplanationsOutput", pFile)

        pNbClasses = pParamSpecif["nbClasses"] if "nbClasses" in pParamSpecif else None
        pFullData = pParamSpecif["fullData"] if "fullData" in pParamSpecif else None
        pExplOutputDim = pParamSpecif["explOutputDim"] if "explOutputDim" in pParamSpecif else pUseCase.numDataChannels

        if ISTORCH and pOutputXAIFramework == torch.Tensor:
            HWWH = [pUseCase.inputModelSize[1], pUseCase.inputModelSize[0]]
            subForme = "W, H"
        else:
            HWWH = [pUseCase.inputModelSize[0], pUseCase.inputModelSize[1]]
            subForme = "H, W"
        if pFullData is not None:
            HWWH.insert(0, pFullData)
            subForme = "o, %s"%subForme
        if pExplOutputDim is not None:
            if ISTORCH and pOutputXAIFramework == torch.Tensor:
                HWWH.insert(0, pExplOutputDim)
                subForme = "B ,%s"%subForme
            else:
                HWWH.append(pExplOutputDim)
                subForme = "%s, B"%subForme
        if pNbClasses is not None:
            HWWH.append(pNbClasses)
            subForme = "%s, C"%subForme
        expected = tuple(HWWH)
        forme = "(%s)"%subForme

        obtained = pExplanation.shape
        controle(False, expected, obtained, forme, "control_loadExplanationsOutput", pFile)

# -------------------------------------------------------------------------------
## Function to control (8)
# @param pOutputXAIFramework : framework of the method output
# @param pPlotDataSize : data size when plotting
# @param pExplanation : explanation to control
# @param pData : data to plot
# @param pUseCase : class of the usecase plugin
# @param pFile : file in which the control is done
# @param pParamSpecif : specific params in dictionnary
def control_plotExplanationInputImage(pOutputXAIFramework, pPlotDataSize, pExplanation, pData, pUseCase, pFile, pParamSpecif):

    if "expected" in pParamSpecif:
        for item, message, expectedType, expectedShape, formeShape in zip([pExplanation, pData], ["Explanation", "Data"], [pOutputXAIFramework, np.ndarray], pParamSpecif["expected"], pParamSpecif["format"]):
            if message == "Data":
                colPrint(" --------------------------------------------", "Normal")
            colPrint(message, "Normal")

            if isinstance(expectedType, tuple):
                expected = expectedType
                obtained = item
                controleRecursif(True, expected, obtained, "(outputXAIFramework)", "control_plotExplanationInput", pFile)

                expected = expectedShape
                obtained = item
                controleRecursif(False, expected, obtained, formeShape, "control_plotExplanationInput", pFile)
            else:
                expected = expectedType
                obtained = type(item)
                controle(True, expected, obtained, "(outputXAIFramework)", "control_plotExplanationInput", pFile)

                if expectedShape is None:
                    colPrint("   --Cannot control the element size-- ", "Info")
                else:
                    expected = expectedShape
                    obtained = item.shape
                    controle(False, expected, obtained, formeShape, "control_plotExplanationInput", pFile)
    else:
        colPrint("Explanation", "Normal")
        if ISTENSORFLOW and pOutputXAIFramework == eTensor.EagerTensor:
            pOutputXAIFramework = np.ndarray
        expected = pOutputXAIFramework
        obtained = type(pExplanation)
        controle(True, expected, obtained, "(outputXAIFramework)", "control_plotExplanationInput", pFile)

        pNbClasses = pParamSpecif["nbClasses"] if "nbClasses" in pParamSpecif else None
        pExplOutputDim = pParamSpecif["explOutputDim"] if "explOutputDim" in pParamSpecif else pUseCase.numDataChannels
        pDataSize = pParamSpecif["dataSize"] if "dataSize" in pParamSpecif else None
        pNbBands = pParamSpecif["nbBands"] if "nbBands" in pParamSpecif else pUseCase.numImageChannels

        if pPlotDataSize == 0:
            height = pUseCase.inputModelSize[0]
            width = pUseCase.inputModelSize[1]
        else:
            height = pDataSize[0]
            width = pDataSize[1]

        if pNbClasses is not None:
            if ISTORCH and expected==torch.Tensor:
                expected = (pExplOutputDim, height, width, pNbClasses)
                forme = "(B, H, W, C)"
            else:
                expected = (height, width, pExplOutputDim, pNbClasses)
                forme = "(H, W, B, C)"
        elif pExplOutputDim is not None:
            if ISTORCH and expected==torch.Tensor:
                expected = (pExplOutputDim, height, width)
                forme = "(B, H, W)"
            else:
                expected = (height, width, pExplOutputDim)
                forme = "(H, W, B)"
        else:
            expected = (height, width)
            forme = "(H, W)"
        if isinstance(pExplanation, list):
            for expl in pExplanation:
                obtained = expl.shape
                controle(False, expected, obtained, forme, "control_plotExplanationInput", pFile)
        else:
            obtained = pExplanation.shape
            controle(False, expected, obtained, forme, "control_plotExplanationInput", pFile)

        colPrint(" --------------------------------------------", "Normal")
        colPrint("Data", "Normal")

        expected = np.ndarray
        obtained = type(pData)
        controle(True, expected, obtained, "(np.ndarray)", "control_plotExplanationInput", pFile)

        if pPlotDataSize == 0:
            height = pUseCase.inputModelSize[0]
            width = pUseCase.inputModelSize[1]
        else:
            height = pDataSize[0]
            width = pDataSize[1]

        if pNbBands == 0:
            expected = (height, width)
            forme = "(H, W)"
        else:
            expected = (height, width, pNbBands)
            forme = "(H, W, B)"

        obtained = pData.shape
        controle(False, expected, obtained, forme, "control_plotExplanationInput", pFile)

# ===============================================================================
# end of file
