#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
import os, PIL, json
import numpy as np

from kaasrc.communs import colPrint
import kaasrc.communs
import kaasrc.controles

# ---------
try:
    import torch
except Exception as err:
    print("Error:", err)
    colPrint("Packages torch,torchvision are uninstalled.", "Error")
# ---------

import RenaultWeldingResnet

# -------------------------------------------------------------------------------
## Create an instance of the model
# @param pDictParams : parameter dictionary
# @return the instance of the model
def UC_createModel(pDictParams):
    # shortcuts
    pUseCaseBase = pDictParams['useCaseBase']
    pModelpath = pDictParams['modelpath']
    pModelfile = pDictParams['modelfile']
    pDataPreprocessModelpath = pDictParams['datapreprocessmodelpath']
    pDataPreprocessModelfile = pDictParams['datapreprocessmodelpathfile']
    pCode = pDictParams['code']
    pXAIframework = pDictParams['pluginXAI'].inputXAIframework

    # get model file
    ficModel = os.path.join(pUseCaseBase, pModelpath, pModelfile)
    print("   .create Model from '%s'"%ficModel, flush=True)

    # get data preprocess model file
    ficDataPreprocessModel = os.path.join(pUseCaseBase, pDataPreprocessModelpath, pDataPreprocessModelfile)
    print("   .create Data Preprocess Model from '%s'"%ficDataPreprocessModel, flush=True)

    # create model instance from 'model' parameter
    aiModel = UC_Model(ficModel, ficDataPreprocessModel, pXAIframework)
    print("      ", aiModel.useCase.id, "-/-", pCode, flush=True)

    return aiModel

# ---------------------------------------------------------------------------
## Compute the data inference with model
# @param pAiModel : model instance
# @param pDictParams : parameter dictionary
# @return data, prediction, list of inference error against truth
def UC_computeInference(pAiModel, pDictParams):
    # shortcuts
    pNbData = pDictParams['nbData']
    pClasses = pDictParams['classes']
    pDataPathList = pDictParams['dataPathList']
    pDataList = pDictParams['dataList']
    pDataProd = pDictParams['dataProd']
    pRepertProd = pDictParams['repertProd']

    # the list of data with inference error (!= truth).
    listInferError = []

    # Test/Prediction data
    xData = []
    xDataSize = []
    yPred = []
    print("   .inference", flush=True)
    resultSavedOn = os.path.join(pDataProd, "dataInference", pRepertProd)

    # Loop on data
    for i in range(pNbData):
        # prepare data
        print("     - %s"%pDataPathList[i], flush=True)
        dataPreprocessed, dataSize = pAiModel.useCase.fctPrepareData(pDataPathList[i])
        # control function for fctPrepareData outputs
        kaasrc.controles.controlFctPrepareDataOutput(pDictParams, dataPreprocessed, pAiModel.useCase, __file__)

        # inference on data
        pAiModel.setInferenceCible(True)

        # control function for Inference input
        kaasrc.controles.controlInferenceInput(pDictParams, dataPreprocessed, pAiModel.useCase, __file__)

        # inference
        prediction = pAiModel.useCase(dataPreprocessed)

        # control function for Inference outputs
        kaasrc.controles.controlInferenceOutput(pDictParams, prediction, pAiModel.useCase, __file__)

        # save prediction (inference) with check inference vs truth
        isInferenceKO = pAiModel.savePrediction(i, pDataList, prediction, resultSavedOn, pClasses, dataSize)
        if isInferenceKO:
            print("        ...inference error against truth.", flush=True)
            listInferError.append((pDataPathList[i], isInferenceKO))

        xData.append(dataPreprocessed)
        xDataSize.append(dataSize)
        yPred.append(prediction)

    # save list of data with the inference differing of truth
    if len(listInferError) > 0:
        ficListInferError = os.path.join(resultSavedOn, "..", "listInferError.json")
        print("     - list of data with inference error saved in '%s'."%ficListInferError, flush=True)
        with open(ficListInferError, 'w', encoding="utf-8") as f:
            json.dump(listInferError, f, indent=2)

    xData=torch.cat(xData)
    yPred=torch.cat(yPred)

    # control function for all Inference outputs
    kaasrc.controles.controlUC_computeInferenceOutput(pDictParams, xData, yPred, pAiModel.useCase, pNbData, __file__)

    return xData, xDataSize, yPred, listInferError

# -------------------------------------------------------------------------------
## Prepare the image for the plot. Imposed parameters.
# @param pDictParams : parameter dictionary
# @param pPathImage : image path file
# @param pIndex : the index of the data
# @return image read and normalized
#def UC_ImageDataToPlot(pDictParams, pPathImage, pIndex):
#
#    inputXAIframework = pDictParams['inputXAIframework']
#    pData, _ = kaasrc.communs.convertToXAIframework(pDictParams, inputXAIframework)
#
#    # pData, _ = pDictParams['xy']
#    pDataSize = pDictParams['datasize']
#    pPlotDataSize = pDictParams['plotDataSize']
#
#    image = pData[pIndex]
#    imageSize = pDataSize[pIndex]
#
#    if pPlotDataSize == 1:
#        image = kaasrc.communs.resizeData(image, imageSize)
#
#    return image

# -------------------------------------------------------------------------------
## Prepare the image for the plot. Imposed parameters.
# @param pDictParams : parameter dictionary
# @param pPathImage : image path file
# @return image read and normalized
def UC_ImageDataToPlot(pDictParams, pPathImage):

    image = PIL.Image.open(pPathImage)
    image = np.array(image, dtype=np.float32)

    # Normalisation
    if image.max() > 1 or image.min() < 0:
        image -= image.min()
        image /= image.max()

    # Resize according plot shape (tw TUI command)
    image = kaasrc.communs.fctDataToPlotResized(pDictParams, image)

    return image

# -------------------------------------------------------------------------------
## Prepare the explanation for the plot. Imposed parameters.
# @param pDictParams : parameter dictionary
# @param pExplanation : the explanation
# @param pIndex : the data index in dataList (optionnel)
# @param pItem : the item in tabular data, os the class (optionnel)
# @return explanation to plot
def UC_ExplanationToPlot(pDictParams, pExplanation, pIndex, pItem=""):

    pExplanation = np.transpose(pExplanation)

    # Resize according plot shape (tw TUI command)
    pExplanation = kaasrc.communs.fctExplanationToPlotResized(pDictParams, pExplanation, pIndex)

    return pExplanation

# -------------------------------------------------------------------------------
## Classe Model : class dedicate to use case models
class UC_Model:
    # -------------------------------------------------------------------------------
    ## Initialisation function
    # @param pModelFilePath : model file path
    # @param pDataPreprocessModelFilePath : data preprocess model file path
    # @param pXAIframework : model format
    def __init__(self, pModelFilePath, pDataPreprocessModelFilePath, pXAIframework):
        ## @brief megaPixels function parameters
        self.megaPixelsParametres = {"seuil": 0, "pretraitement": "none", "noyau": 3, "nTo1band": self.reduceTo1Band}
        ## @brief is cuda? and device
        self.cuda, self.device = kaasrc.communs.selDeviceForTorch()
        ## @brief use case initialisation
        self.useCase = RenaultWeldingResnet.RenaultWeldingResnet(self.cuda, self.device, pModelFilePath, pDataPreprocessModelFilePath, pXAIframework)

        ## @brief model initialisation
        self.useCase.returnCall=None
        self.conv_layer_outputs = self.useCase.conv_layer_outputs

    # -------------------------------------------------------------------------------
    ## Function to set inference: target vs explanation
    # @param pCible : boolean
    def setInferenceCible(self, pCible):
        self.useCase.inferenceCible = pCible

    # -------------------------------------------------------------------------------
    ## Function to reduce multi bands data to 1 band image
    # @param pImage : image to treat
    # @return An one band image
    # @remark generic process or call to {usecase}.reduceTo1Band() function
    def reduceTo1Band(self, pImage):
        # generic process
        img_image1B = kaasrc.communs.reduceTo1Band(pImage)
        # or call to {usecase}.reduceTo1Band() function
        # img_image1B = {usecase}.reduceTo1Band(pImage)
        return img_image1B

    # -------------------------------------------------------------------------------
    ## Function to construct mega-pixels
    # @param pImage : image to treat
    # @return map of mega-pixels
    # @remark call to predefined algorithm or call to {usecase}.megaPixels() function
    def megaPixels(self, pImage):
        # call to predefined algorithm
        pixelRegionMap = kaasrc.communs.megaPixels(pImage, self.megaPixelsParametres)
        # or call to {usecase}.megaPixels() function
        # pixelRegionMap = {usecase}.megaPixels(pImage)
        return pixelRegionMap

    # -------------------------------------------------------------------------------
    ## Function to save inference and to control inference correctness
    # @param pIndex : index of data to treat
    # @param pDataPath : filename of data treated
    # @param pYpred : model result
    # @param pResultSavedOn : directory name to save result
    # @param pClassesModele : prediction classes
    # @param pDataSize : size of the data loaded
    # @return list of item with inference vs truth KO
    def savePrediction(self, pIndex, pDataPath, pYpred, pResultSavedOn, pClassesModele, pDataSize):

        # La prédiction brute complète
#        prediction = self.useCase.resPredictionsCibles[0][0].tolist()
#        print("prediction Chafik   :",prediction)
        prediction = self.useCase.resPredictionsCibles[pIndex][0].tolist()
#        print("prediction Philippe :",prediction)
        # La prédiction inférence cible
        predictionCible = pYpred[0].tolist()
        # Index de la classe dans la prédiction
        indexClasse = predictionCible.index(1.0)
        #print("indexClasse Chafik   :",indexClasse)
        #indexClasse = predictionCible.index(1)
        #print("indexClasse Philippe :",indexClasse)
        # Prédiction sous forme de classe prédite
        classesPredites = pClassesModele[indexClasse]
        # Scores des classes prédites
        score = prediction[indexClasse]
        # verite
        verite = pDataPath[pIndex].split('_')[-1].replace(".jpg", "")

        # controle de l'inférence par rapport à la vérité.
        inferenceVSverite = bool(verite == classesPredites)
        # liste des items en erreur
        inferenceKO = not inferenceVSverite

        # sauvegarde de la prédiction sur disque
        ficPrediction, _ = os.path.splitext(kaasrc.communs.createDirName(pResultSavedOn, pDataPath[pIndex]))
        ficPrediction += ".json"
        print("Prediction saved in %s"%ficPrediction, flush=True)
        dictJson = {"classesModele": pClassesModele,
                  "verite": verite,
                  "prediction": prediction,
                  "classe": classesPredites,
                  "score": score,
                  "inferenceVSverite": inferenceVSverite,
                  "taille": pDataSize}
        with open(ficPrediction, 'w', encoding="utf-8") as f:
            json.dump(dictJson, f, indent=2)

        return inferenceKO

# ===============================================================================
# end of file
