#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================
import os, json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# import kaasrc.kaaActions
#from kaasrc import TUI

# ---------
try:
    import cv2
except Exception as err:
    print("Error:", err)
    print("Package cv2 is uninstalled.", "Error")
# ---------
try:
    import torch
    ISTORCH = True
except Exception:
    ISTORCH = False
# ---------
try:
    from skimage.segmentation import watershed
except Exception:
    print("Package skimage is uninstalled.", "Error")
# ---------

# check if we can compile latex reports
# print("LaTeX presence check for possible report compilation:")
# ISLATEX = os.system("which latex") == 0

# -------------------------------------------------------------------------------
# def foo(pDictParams, pExplanation, pIndex = "", pObject = ""):
#    print("-FOO-")
#    return pExplanation

try:
    import colorama
    colorama.init(autoreset=True)
    COLORAMA = True
except Exception as err:
    print("Error:", err)
    print("RESTRICTION : Module 'Colorama' non installe")
    print("               = > Les affichages ne seront pas mis en couleur.")
    COLORAMA = False

if COLORAMA:
    fRed      = colorama.Fore.RED
    fGreen    = colorama.Fore.GREEN
    fYellow   = colorama.Fore.YELLOW
    fWhite    = colorama.Fore.WHITE
    fBlue     = colorama.Fore.BLUE
    fMagenta  = colorama.Fore.MAGENTA
    fCyan     = colorama.Fore.CYAN
#    fBlack    = colorama.Fore.BLACK
#
    fLblack    = colorama.Fore.LIGHTBLACK_EX
#    fLblue     = colorama.Fore.LIGHTBLUE_EX
#    fLcyan     = colorama.Fore.LIGHTCYAN_EX
#    fLgreen    = colorama.Fore.LIGHTGREEN_EX
#    fLmagenta  = colorama.Fore.LIGHTMAGENTA_EX
#    fLred      = colorama.Fore.LIGHTRED_EX
#    fLwhite    = colorama.Fore.LIGHTWHITE_EX
#    fLyellow   = colorama.Fore.LIGHTYELLOW_EX
#
#    bRed      = colorama.Back.RED
#    bGreen    = colorama.Back.GREEN
#    bYellow   = colorama.Back.YELLOW
#    bWhite    = colorama.Back.WHITE
#    bBlue     = colorama.Back.BLUE
#    bMagenta  = colorama.Back.MAGENTA
#    bCyan     = colorama.Back.CYAN
#    bBlack    = colorama.Back.BLACK
#
#    bLblack    = colorama.Back.LIGHTBLACK_EX
#    bLblue     = colorama.Back.LIGHTBLUE_EX
#    bLcyan     = colorama.Back.LIGHTCYAN_EX
#    bLgreen    = colorama.Back.LIGHTGREEN_EX
#    bLmagenta  = colorama.Back.LIGHTMAGENTA_EX
#    bLred      = colorama.Back.LIGHTRED_EX
#    bLwhite    = colorama.Back.LIGHTWHITE_EX
#    bLyellow   = colorama.Back.LIGHTYELLOW_EX
#
    sBright   = colorama.Style.BRIGHT
#    sDim      = colorama.Style.DIM
#    sNormal   = colorama.Style.NORMAL
#    sReset    = colorama.Style.RESET_ALL
else:
    fRed      = ""
    fGreen    = ""
    fYellow   = ""
    fWhite    = ""
    fBlue     = ""
    fMagenta  = ""
    fCyan     = ""
#    fBlack    = ""
#
    fLblack    = ""
#    fLblue     = ""
#    fLcyan     = ""
#    fLgreen    = ""
#    fLmagenta  = ""
#    fLred      = ""
#    fLwhite    = ""
#    fLyellow   = ""
#
#    bRed      = ""
#    bGreen    = ""
#    bYellow   = ""
#    bWhite    = ""
#    bBlue     = ""
#    bMagenta  = ""
#    bCyan     = ""
#    bBlack    = ""
#
#    bLblack    = ""
#    bLblue     = ""
#    bLcyan     = ""
#    bLgreen    = ""
#    bLmagenta  = ""
#    bLred      = ""
#    bLwhite    = ""
#    bLyellow   = ""
#
    sBright   = ""
#    sDim      = ""
#    sNormal   = ""
#    sReset    = ""


# ---------------------------------------------------------------------------------
## Print a colored message
# @param pMessage : message to print
# @param pType : message type to define color
# @param pEcho : active display
def colPrint(pMessage, pType="Normal", pEcho=True):
    if not pEcho:
        return
    if pType == "Normal":
        print(fWhite + pMessage, flush=True)
    elif pType == "Error":
        print(fRed + "%s > %s"%(pType, pMessage), flush=True)
    elif pType == "Alert":
        print(fRed + "%s > %s"%(pType, pMessage), flush=True)
    elif pType == "Warning":
        print(fCyan + "%s > %s"%(pType, pMessage), flush=True)
    elif pType == "Action":
        print(fGreen + pMessage, flush=True)
    elif pType == "Config":
        print(fMagenta + pMessage, flush=True)
    elif pType == "Select":
        print(fBlue + pMessage, flush=True)
    elif pType == "Debug":
        print(fLblack + pMessage, flush=True)
    elif pType == "Info":
        print(fYellow + sBright + pMessage, flush=True)
    else:
        print(fRed, "type '%s' inconnu, message '%s'"%(pType, pMessage), flush=True)

# -------------------------------------------------------------------------------
## Function conversion string to list from tabular rule to plot
# @param pText : string for set : * for all or 3, 5-7, 9 for 3, 5, 6, 7, 9
# @param pRange : range to replace  *
# @param pFicItems : file to store list for reuse
def string2list(pText, pRange, pFicItems):
    pText = pText.split(',')
    liste = []
    for item in pText:
        if item == "*":
            liste = pRange
            break
        if item.isdigit():
            liste.append(int(item))
        else:
            item = item.split('-')
            liste.extend(list(range(int(item[0]), int(item[1]) + 1)))

    with open(pFicItems, 'w', encoding="utf-8") as f:
        json.dump({"listItems": liste}, f, indent=2)

    return liste

# -------------------------------------------------------------------------------
## Function to select device for pyTorch according to the CUDA_VISIBLE_DEVICES variable
# @return n-uplet boolean (is gpu activated), gpu device or cpu
def selDeviceForTorch():
    envDevice = int(os.getenv("CUDA_VISIBLE_DEVICES", '-1'))
    # device = 'cpu' or '0' or '0, 1, 2, 3'
    cpu = envDevice == -1
    cuda = False
    device = 'cpu'
    if ISTORCH:
        if not cpu:
            assert torch.cuda.is_available(), f'CUDA unavailable, invalid device {envDevice} requested'  # check availability
        cuda = not cpu and torch.cuda.is_available()
        device = torch.device('cuda:0' if cuda else 'cpu')

    #print("Device selDevice():", envDevice)
    #print("     cpu:", cpu)
    #print("    cuda:", cuda)
    #print('  Result: ', 'cuda:0' if cuda else 'cpu')
    return cuda, device

# -------------------------------------------------------------------------------
## Function to resize images using pillow
# @param pData : data to treat
# @param pNewSize : new size for pData [height, width]
# @param pLoop : resize data in a list if True
# @param pTranspose : list of tranposition factor before and after resize process
# @return the resized data
def resizeData(pData, pNewSize, pLoop=0, pTranspose=None):

    typeData = type(pData)
    shapeData = pData.shape
    if ISTORCH and typeData == torch.Tensor:
        pData = pData.numpy()
        pData = np.swapaxes(pData, 0, -1)
    if len(shapeData) == 2:
        pData = np.transpose(pData, (1, 0))
    elif len(shapeData) == 3:
        pData = np.transpose(pData, (1, 0, 2))

    if pTranspose is not None:
        pData = np.transpose(pData, pTranspose[0])
    if pLoop == 0:
        image = cv2.resize(pData, dsize=pNewSize, interpolation=cv2.INTER_CUBIC)
        if len(shapeData) > len(image.shape):
            image = np.expand_dims(image, axis=-1)
    else:
        image = [cv2.resize(data, dsize=pNewSize, interpolation=cv2.INTER_CUBIC) for data in pData]
        image = np.stack(image, axis=0)
    if pTranspose is not None:
        image = np.transpose(image, pTranspose[1])

    if len(shapeData) == 2:
        image = np.transpose(image, (1, 0))
    elif len(shapeData) == 3:
        image = np.transpose(image, (1, 0, 2))
    if ISTORCH and typeData == torch.Tensor:
        image = np.swapaxes(image, 0, -1)
        image = torch.tensor(image)
    return image

# -------------------------------------------------------------------------------
# Resize the data according to the plot shape (plotDataSize)
# @param pDictParams : parameter dictionary
# @param pData : the data to reshape
# return updated data
def fctDataToPlotResized(pDictParams, pData):
    # shortcuts
    _, aiModel = pDictParams['aiModel']
    pPlotDataSize = pDictParams['plotDataSize']

    # resize de la donnée dans le cas d'un plot "model size"
    if pPlotDataSize == 0:
        pData = resizeData(pData, aiModel.useCase.inputModelSize)

    return pData

# -------------------------------------------------------------------------------
# Resize the explanation according to the plot shape (plotDataSize)
# @param pDictParams : parameter dictionary
# @param pExplanation : the explanation to reshape
# @param pIndex : the index of the data
# return updated explanation
def fctExplanationToPlotResized(pDictParams, pExplanation, pIndex):
    # shortcuts
    pDataSize = pDictParams['datasize']
    pPlotDataSize = pDictParams['plotDataSize']

    # resize de l'explication dans le cas d'un plot "data size"
    if pPlotDataSize == 1:

        if isinstance(pExplanation, list):
            pExplanation = [resizeData(expl, pDataSize[pIndex]) for expl in pExplanation]
        else:
            pExplanation = resizeData(pExplanation, pDataSize[pIndex])

    return pExplanation

# -------------------------------------------------------------------------------
## Function to get plottable box
# @param pBox : yolo Box [0.6, 0.9, 0.1, 0.2]
# @param pNewSize : new size for pData [height, width]
# @return the resized box
def transformYoloBoxToPascalBox(pBox, pNewSize):
    new_box = [0, 0, 0, 0]
    new_box[0] = int((pBox[0] - pBox[2] / 2) * pNewSize[1])
    new_box[1] = int((pBox[1] - pBox[3] / 2) * pNewSize[0])
    new_box[2] = int((pBox[0] + pBox[2] / 2) * pNewSize[1])
    new_box[3] = int((pBox[1] + pBox[3] / 2) * pNewSize[0])
    return new_box

# -------------------------------------------------------------------------------
## Function to truth class of a predicted Box
# @param pTruthBoxes : List of Boxs [[(box), class_id]]
# @param pCenterPredicted : emplacement of the center of the predicted box [x, y]
# @param pPredictedClass : id of the predicted class
# @return the truth id of the box, None if no real BB at this place
def checkInferenceClassTruthBB(pTruthBoxes, pCenterPredicted, pPredictedClass):
    truth_class = None
    for b in pTruthBoxes:
        contour_box = b[0]
        if pCenterPredicted[0] > contour_box[0] and pCenterPredicted[0] < contour_box[2] and pCenterPredicted[1] > contour_box[1] and pCenterPredicted[1] < contour_box[3]:
            truth_class = b[1]
            if pPredictedClass == b[1]:
                break
    return truth_class

# -------------------------------------------------------------------------------
# Update the list ob detected objects in dicttParams
# @param pDictParams : parameter dictionary
# return updated pDictParams
def updateListObjects(pDictParams):
    # shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']

    resultSavedOn = os.path.join(pDataProd, "dataExplanations", pRepertProd)
    ficObjets = os.path.join(resultSavedOn, 'listObjects.json')
    if os.path.exists(ficObjets):
        with open(ficObjets, 'r', encoding="utf-8") as f:
            pDictParams['objets'] = json.load(f)

    return pDictParams

## -------------------------------------------------------------------------------
### Plot explanation of a specific image data
### @param pDictParams : parameter dictionary
### @param pFicPlot : filename to save plot (png image)
### @param pExplanation : explanation of the image
#def plotExplanation(pDictParams, pFicPlot, pExplanation):
#    # shortcuts
#    pHeightPlot = pDictParams['heightPlot']
#    # Préparation de la feuille
#    ratio = pExplanation.shape[1] / pExplanation.shape[0]
#    plt.figure(figsize=(pHeightPlot * ratio, pHeightPlot))
#
#    pExplanation = np.array(pExplanation, dtype=np.float32)
#
#    # normalize
#    explMin = float(pExplanation.min())
#    explMax = float(pExplanation.max())
#    texte = "min=%f max=%f h=%d w=%d"%(explMin, explMax, pExplanation.shape[0], pExplanation.shape[1])
#
#    #if len(pExplanation.shape) == 3:
#    #    pExplanation = np.mean(pExplanation, -1)
#    # im = plt.imshow(pExplanation, cmap = pCmap)
#    # Legende
#    plt.text(10, 10, texte, fontsize=8, backgroundcolor='white')
#    # plt.colorbar(im)
#
#    plt.axis('off')
#    plt.grid(None)
#    # Save image
#    plt.savefig(pFicPlot, bbox_inches='tight')
#    print("       saved in:", pFicPlot, flush=True)
#    plt.close()

# -------------------------------------------------------------------------------
## Function to reduce multi bands data to 1 band image
# @param pImage : image to treat
# @param pCoeff : multiplicative factor
# @return An one band image
def reduceTo1Band(pImage, pCoeff=1.):
    # generic process
    imgImage3B = np.array(pImage)
    imgImage1B = cv2.cvtColor(imgImage3B, cv2.COLOR_BGR2GRAY)
    imgImage1B = np.uint8(imgImage1B * pCoeff)
    return imgImage1B

# -------------------------------------------------------------------------------
## Function to construct mega-pixels
# @param pImage : image to treat
# @param pMegaPixelsParametres : parameters for mega-pixels functions
# @return map of mega-pixels
def megaPixels(pImage, pMegaPixelsParametres):
    print("   .Mega-Pixels:")
    if isinstance(pImage, torch.Tensor):
        pImage = np.swapaxes(pImage, -1, 0)
    mNbPixels = pMegaPixelsParametres["mapPixels"]
    if mNbPixels > 0:
        print("         .pixel grid %d"%mNbPixels, flush=True)
        w, h, _ = pImage.shape
        imgMap = np.zeros((w, h))
        for i, _ in enumerate(imgMap):
            for j, _ in enumerate(imgMap[i]):
                if len(imgMap[i])%mNbPixels == 0:
                    n1 = int(i / mNbPixels) * (int(len(imgMap) / mNbPixels))
                else:
                    n1 = int(i / mNbPixels) * (int(len(imgMap) / mNbPixels) + 1)
                n2 = int(j / mNbPixels)
                imgMap[i][j] = n1 + n2
    else:
        mPreduceTo1Band = pMegaPixelsParametres["nTo1band"]
        mPpretraitement = pMegaPixelsParametres["pretraitement"]
        mPnoyau = pMegaPixelsParametres["noyau"]
        mPseuil = pMegaPixelsParametres["seuil"]
        print("         .watershed (%s, %d, %d)"%(mPpretraitement, mPnoyau, mPseuil), flush=True)
        # Passage à 1 bande
        imgImage1B = mPreduceTo1Band(pImage)
        # imgImage3B = pImage.numpy()
        # imgImage1B = cv2.cvtColor(imgImage3B, cv2.COLOR_BGR2GRAY)
        # imgImage1B = np.uint8(imgImage1B * 255.)
        # Dilatation
        if mPpretraitement == "dilate":
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (mPnoyau, mPnoyau))
            imgPreTrait = cv2.dilate(imgImage1B, kernel=kernel, iterations=1)
        # Erosion
        elif mPpretraitement == "erode":
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (mPnoyau, mPnoyau))
            imgPreTrait = cv2.erode(imgImage1B, kernel=kernel, iterations=1)
        # Blur
        elif mPpretraitement == "blur":
            imgPreTrait = cv2.medianBlur(imgImage1B, mPnoyau, 0)
        # Aucun
        else:
            imgPreTrait = imgImage1B
        # print(np.min(imgPreTrait), np.max(imgPreTrait))
        # Gradient (D(i)-E(i)) / 2
        kernelCross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        imgGradDilatation = cv2.dilate(imgPreTrait, kernel=kernelCross, iterations=1)
        imgGradErosion = cv2.erode(imgPreTrait, kernel=kernelCross, iterations=1)
        imgGradient = (imgGradDilatation - imgGradErosion) // 2
        # Markers and labelling
        _, imgMarkers = cv2.threshold(imgGradient, mPseuil, 255, cv2.THRESH_BINARY_INV)
        nbmarkers, markers = cv2.connectedComponents(imgMarkers)
        print("         .nb.markers", nbmarkers, flush=True)
        # Segmentation
        imgMap = watershed(imgGradient, markers=markers)
    return imgMap

# ---------------------------------------------------------------------------
## Remove space in filename
# @param pRepertoire : path
# @param pNomFichier : filename
# @return pChemin/pNomFichier
def noSpace(pRepertoire, pNomFichier):
    return os.path.join(pRepertoire, pNomFichier.replace(' ', ''))

# ---------------------------------------------------------------------------
## Create sub path of filename in path
# @param pRepertoire : path
# @param pNomFichier : filename
# @return filename
def createDirName(pRepertoire, pNomFichier):
    dirName = os.path.join(pRepertoire, os.path.dirname(pNomFichier))
    if not os.path.exists(dirName):
        os.makedirs(dirName)
    return noSpace(pRepertoire, pNomFichier)

# ---------------------------------------------------------------------------
## Convert data to XAIframework
# @param pDictParams : parameter dictionary
# @param xData : data to convert
# @param dataInputXAIframework : frame of XAI library for data
# @return converted data (xData, yPred)
def convertDataToXAIframework(pDictParams, xData, dataInputXAIframework):
    # shortcuts
    pNbData = pDictParams['nbData']
    _, aiModel = pDictParams['aiModel']

    # Convert Data
    if not isinstance(xData, list):
        if not isinstance(xData, dataInputXAIframework):
            if hasattr(aiModel.useCase, 'convertDataToFramework'):
                xData = aiModel.useCase.convertDataToFramework(xData, dataInputXAIframework)
            else:
                colPrint("The method 'convertDataToFramework' is not implemented in model class.", "Error")
                xData = None
    else:
        for index in range(pNbData):
            if not isinstance(xData[index], dataInputXAIframework):
                if hasattr(aiModel.useCase, 'convertDataToFramework'):
                    xData[index] = aiModel.useCase.convertDataToFramework(xData[index], dataInputXAIframework)
                else:
                    colPrint("The method 'convertDataToFramework' is not implemented in model class.", "Error")
                    xData[index] = None
    return xData

# ---------------------------------------------------------------------------
## Convert prediction to XAIframework
# @param pDictParams : parameter dictionary
# @param yPred : prediction to convert
# @param predInputXAIframework : framework of XAI library for prediction
# @return converted data yPred
def convertPredToXAIframework(pDictParams, yPred, predInputXAIframework):
    # shortcuts
    pNbData = pDictParams['nbData']
    _, aiModel = pDictParams['aiModel']

    # Convert Prediction
    if not isinstance(yPred, list):
        if not isinstance(yPred, predInputXAIframework):
            if hasattr(aiModel.useCase, 'convertPredictionToFramework'):
                yPred = aiModel.useCase.convertPredictionToFramework(yPred, predInputXAIframework)
            else:
                colPrint("The method 'convertPredictionToFramework' is not implemented in model class.", "Error")
                yPred = None
    else:
        for index in range(pNbData):
            if not isinstance(yPred[index], predInputXAIframework):
                if hasattr(aiModel.useCase, 'convertPredictionToFramework'):
                    yPred[index] = aiModel.useCase.convertPredictionToFramework(yPred[index], predInputXAIframework)
                else:
                    colPrint("The method 'convertPredictionToFramework' is not implemented in model class.", "Error")
                    yPred[index] = None
    return yPred

# ---------------------------------------------------------------------------
## Convert data and prediction to XAIframework
# @param pDictParams : parameter dictionary
# @param pInputXAIframework : framework of XAI library for data and prediction
# @return converted data (xData, yPred)
def convertToXAIframework(pDictParams, pInputXAIframework):
    # shortcuts
    xData, yPred = pDictParams['xy']

    dataInputXAIframework, predInputXAIframework = pInputXAIframework

    # Convert Data
    xData = convertDataToXAIframework(pDictParams, xData, dataInputXAIframework)
    # Convert Prediction
    yPred = convertPredToXAIframework(pDictParams, yPred, predInputXAIframework)

    return xData, yPred

# -------------------------------------------------------------------------------
## Plot explanation
# @param pDictParams : parameter dictionary
# @param pExplanation : explanation image
# @param pAxis : axis to locate legend
# @param pDataName : name of the data
# @param pInference : inference results
def _plotExplanationAsImage(pDictParams, pExplanation, pAxis, pDataName, pInference):
    # shortcuts
    pExplanation = np.array(pExplanation, dtype=np.float32)
    pPercentile = pDictParams["percentile"]
    pAlpha = pDictParams["alpha"]
    pNormalise = pDictParams["normalise"]
    pLegender = pDictParams["legender"]
    pFontSize = pDictParams["fontSize"]
#    pDataProd=pDictParams['dataProd']
#    pRepertProd=pDictParams['repertProd']
#    pDataList=pDictParams['dataList']

    # get the color map
    pCmapMode = pDictParams['cmapListMode']
    if pCmapMode == 1:
        ficJson = pDictParams['cmapListColor']
        if os.path.exists(ficJson):
            with open(ficJson, 'r', encoding="utf-8") as f:
                data = json.load(f)
            key = list(data.keys())[0]
            pCmap = getColormapColors(data[key])
        else:
            colPrint("The json file '%s' for the colormap is not found!"%ficJson, "Error")
            pCmap = pDictParams["cmap"]
    else:
        pCmap = pDictParams["cmap"]

    texte = "%s\n"%pDataName
    if pDictParams["plotDataSize"] == 0:
        texte += " - Model size"
    elif pDictParams["plotDataSize"] == 1:
        texte += " - Data size"
    texte += " - percentile : %d - transp. : %3.1f\n"%(pPercentile, pAlpha)

    explMin = float(pExplanation.min())
    explMax = float(pExplanation.max())
    # normalize
    if pNormalise:
        if pExplanation.max() > 1 or pExplanation.min() < 0:
            pExplanation  -= pExplanation.min()
            pExplanation /= pExplanation.max()
            texte += "- Normalisation"
    texte += " - min = %f  max = %f\n"%(explMin, explMax)

    # inference infos
    if pInference is not None:
        ssTexte = ""
        if pInference["verite"] is not None:
            ssTexte += "truth=%s    "%pInference["verite"]
        if pInference["classe"] is not None:
            ssTexte += "predicted=%s    "%pInference["classe"]
        if pInference["score"] is not None:
            ssTexte += "score=%4.3f"%float(pInference["score"])
        if len(ssTexte) > 0:
            texte += " - %s\n"%ssTexte
        ssTexte = ""
        pModelType = pDictParams['modeltype']
        if pModelType == "detection":
            ssTexte += " - box=%s\n"%(str([int(x) for x in pInference["prediction"][0]]))
        if len(ssTexte) > 0:
            texte += ssTexte
    texte += "\n"
    pExplanation = np.clip(pExplanation, np.percentile(pExplanation, pPercentile), np.percentile(pExplanation, 100 - pPercentile))

    if len(pExplanation.shape) == 3:
        pExplanation = np.mean(pExplanation, -1)

    im = plt.imshow(pExplanation, alpha=pAlpha, cmap=pCmap)

    # Legende
    if pLegender:
        plt.text(10, 10, texte, fontsize=int(pFontSize))
        divider = make_axes_locatable(pAxis)
        cax = divider.append_axes("right", size="5%", pad=0.15)
        plt.colorbar(im, cax=cax)

    plt.axis('off')
    plt.grid(None)

# -------------------------------------------------------------------------------
## Plot explanation of a specific data
# @param pDictParams : parameter dictionary
# @param pResultSavedOn : path to save result
# @param pExplanation : explanation of the image
# @param pData : image to show
# @param pDataName : data name for the filename of the image result
# @param pSuffixe : object class name or bounding box identifier or other ....
def plotExplanationOnImage(pDictParams, pResultSavedOn, pExplanation, pData, pDataName, pSuffixe=None):
    # shortcuts
    pHeightPlot = pDictParams['heightPlot']
    pPlotDataSize = pDictParams['plotDataSize']
    pLegender = pDictParams["legender"]

    if isinstance(pData, torch.Tensor):
        pData = np.swapaxes(pData, -1, 0)

    if isinstance(pExplanation, torch.Tensor) and pExplanation.ndim == 3:
        pExplanation = np.swapaxes(pExplanation, -1, 0)

    # Préparation de la feuille
    ratio = pData.shape[1] / pData.shape[0]

    _, ax = plt.subplots(figsize=(pHeightPlot * ratio, pHeightPlot))
    plt.imshow(pData)
    plt.axis('off')
    plt.grid(None)

    # Traitement de l'objet
    if pSuffixe is None:
        pSuffixe = ""

    # récupération du fichier json de résultat d'inférence
    fichierJson = noSpace(pResultSavedOn.replace("dataPlotExplanations", "dataInference"), "%s%s.json"%(pDataName, pSuffixe))
    if os.path.exists(fichierJson):
        with open(fichierJson, 'r', encoding="utf-8") as fJson:
            inferJson = json.load(fJson)
    else:
        colPrint("Inference result file '%s' not found"%fichierJson, "Info")
        inferJson = None

    _plotExplanationAsImage(pDictParams, pExplanation, ax, pDataName, inferJson)

    # Extension Data size
    txtDataSize = ""
    if pPlotDataSize == 1:
        txtDataSize = "--datasize"
        print("       plot with original data shape", flush=True)
    else:
        print("       plot with model input data shape", flush=True)

    # Save image
    ficData = os.path.basename(pDataName)
    dirName = os.path.dirname(pDataName)
    ficPlot = createDirName(pResultSavedOn, os.path.join(dirName, "%s%s%s"%(ficData, pSuffixe, txtDataSize)))
    if pLegender:
        ficPlot = "%s--legend"%ficPlot
    plt.savefig("%s.png"%ficPlot, bbox_inches='tight')
    print("       saved in:", ficPlot, flush=True)
    plt.close()

# -------------------------------------------------------------------------------
## Function to get a palette of colormap
# @param pColor : name of the palette or list of hex colors or list of rgb colors
# @return a colormap
def getColormapColors(pColor):
    if isinstance(pColor, str):
        palette = pColor
    else:
        if isinstance(pColor[0], str):
            colors = getRGBColor(pColor)
            palette = matplotlib.colors.ListedColormap([[color[0] / 255, color[1] / 255, color[2] / 255, 1] for color in colors])
        else:
            palette = matplotlib.colors.ListedColormap([[color[0] / 255, color[1] / 255, color[2] / 255, 1] for color in pColor])

    return palette

# -------------------------------------------------------------------------------
## Function to get a palette of Hex colors
# @param pColor : name of the palette or list of hex colors or list of rgb colors
# @param nb : number of colors we want (only used if palette)
# @return a list of colors
def getHexColors(pColor, nb=4):
    def colors_to_hex(r, g, b):
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)
    if isinstance(pColor, str):
        cmap = matplotlib.colormaps[pColor]
        colors = cmap.resampled(nb)
        colors = [colors(i / nb) for i in range(nb)]
        couleurs = [colors_to_hex(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)) for color in colors]
    else:
        if isinstance(pColor[0], str):
            couleurs = pColor
        else:
            couleurs = [colors_to_hex(int(color[0]), int(color[1]), int(color[2])) for color in pColor]

    return couleurs

# -------------------------------------------------------------------------------
## Function to get a palette of RGB colors
# @param pCmap : name of the palette or list of hex colors or list of rgb colors
# @param nb : number of colors we want (only use if palette)
# @return a list of colors
def getRGBColor(pCmap, nb=4):
    def hex2rgb(h):  # rgb order (PIL)
        return tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4))
    if isinstance(pCmap, str):
        hexColor = getHexColors(pCmap, nb)
        rgbColor = [hex2rgb(c) for c in hexColor]
    else:
        if isinstance(pCmap[0], str):
            rgbColor = [hex2rgb(c) for c in pCmap]
        else:
            rgbColor = pCmap
    return rgbColor

# ===============================================================================
# end of file
