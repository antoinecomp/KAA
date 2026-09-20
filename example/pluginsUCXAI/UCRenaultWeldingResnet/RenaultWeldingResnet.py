#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
import PIL
import numpy as np
from collections import OrderedDict

from kaasrc.communs import colPrint

# ---------
try:
    import tensorflow.compat.v2 as tf
    import tensorflow.python.framework.ops as eTensor
except Exception as err:
    print("Error:", err)
    colPrint("Package tensorflow is uninstalled.", "Error")
# ---------
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import models, transforms
except Exception as err:
    print("Error:", err)
    colPrint("Packages torch,torchvision are uninstalled.", "Error")
# ---------
try:
    from ultralytics import YOLO
except Exception as err:
    print("Error:", err)
    colPrint("Package 'ultralytics' is not installed.", "Error")
# ---------
try:
    from preprocess_utils import make_square_bbox_with_margin
except Exception as err:
    print("Error:", err)
    colPrint("Package yolo_utils unavailabled.", "Error")
# ---------

# -------------------------------------------------------------------------------
## Prepare the image for matplotlib plot
# @param pPathImage : image path file
# @return image read and normalized
def fctDataToPlot(pPathImage):
    # ...
    # to customize here if the template in UC<useCase>.py is not correct
    # ...
    # return image
    pass

# -------------------------------------------------------------------------------
## Class dedicated to specific function of the use case
class RenaultWeldingResnet:
    ## @brief description
    description = "Renault welding inspection"

    # -------------------------------------------------------------------------------
    ## Initialisation function
    def __init__(self, pCuda, pDevice, pModelFilePath, pDataPreprocessModelFilePath, pXAIframework):
        ## @brief use case identifier
        self.id = "UC_Renault_Welding_Inspection_Resnet"
        ## @brief use case name
        self.name = self.description
        ## @brief number of channels in an image on disk (0 si no image)
        self.numImageChannels = 3
        ## @brief number of channels in a data for model (0 si no image)
        self.numDataChannels = 3
        ## @brief data load from disk
        self.dataOrigin = None
        ## @brief data prepared for use by the model
        self.dataPreprocessed = None
        ## @brief input features
        self.features = None
        ## @brief number of classes
        self.numClasses = 2
        ## @brief flag to treat prediction as target of explainability one
        self.inferenceCible = True
        ## @brief inference results
        self.resPredictionsCibles = []
        ## @brief size of data for model inference
        self.inputModelSize = [224, 224]  # (height, width)
        self.outputModelSize = self.numClasses
        ## @brief model framework
        self.inputModelFramework = torch.Tensor
        self.outputModelFramework = torch.Tensor
        ## @brief methode framework
        self.XAIframework = pXAIframework
        ## @brief cuda and device
        self.cuda = pCuda
        self.device = pDevice
        ## @brief model
        self.model = self.fctPrepareModel(pModelFilePath, pDataPreprocessModelFilePath)

    # -------------------------------------------------------------------------------
    ## Function to load the model
    # @param pModelFilePath : model file path
    # @param pDataPreprocessModelFilePath : data preprocess model file path
    # @return the model to treat
    def fctPrepareModel(self, pModelFilePath, pDataPreprocessModelFilePath):
        # Load the model
        #print(models)
        model = models.resnet50(weights=None)
        model.fc = nn.Linear(
            in_features=model.fc.in_features, out_features=self.numClasses, bias=True
        )
        # Move model to device before loading state dict
        model.to(self.device)
        # Load the saved weights, removing 'module.' if present
        state_dict = torch.load(
            pModelFilePath, map_location=self.device
        )
        if any(k.startswith("module.") for k in state_dict.keys()):
            new_state_dict = OrderedDict()
            for k, v in state_dict.items():
                new_state_dict[k.replace("module.", "")] = v
            state_dict = new_state_dict
        model.load_state_dict(state_dict)
        model.eval()

        # Register hooks, to use the last convolution layer
        self.conv_layer = model.layer4
        self.conv_layer_outputs = {}
        # - - - - - - - - - - - - - - - -
        def conv_layer_forward(m, i, o):
            # move the channel dimension to the last dimension
            self.conv_layer_outputs["CONVOLUTION_LAYER_VALUES"] = torch.movedim(o, 1, 3).cpu().detach().numpy()
        # - - - - - - - - - - - - - - - -
        def conv_layer_backward(m, i, o):
            # move the channel dimension to the last dimension
            self.conv_layer_outputs["CONVOLUTION_OUTPUT_GRADIENTS"] = torch.movedim(o[0], 1, 3).cpu().detach().numpy()
        # - - - - - - - - - - - - - - - -
        self.conv_layer.register_forward_hook(conv_layer_forward)
        self.conv_layer.register_full_backward_hook(conv_layer_backward)

        # Load the data preprocessing model
        self.data_preprocess_model = YOLO(pDataPreprocessModelFilePath)
        self.data_preprocess_model.to(self.device).eval()

        # Define data transforms
        self.data_transforms = transforms.Compose(
            [
                transforms.Resize((self.inputModelSize[0], self.inputModelSize[1])),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        return model

    # -------------------------------------------------------------------------------
    ## Function to prepare data from file to model input
    # @param pDataPath : data file path
    # @return data for model and dataSize for plot (height, width)
    def fctPrepareData(self, pDataPath):
        # read image
        image = PIL.Image.open(pDataPath)
        image = np.array(image)

        # boxes detection
        result = self.data_preprocess_model(image, conf=0.3, verbose=False)[0]

        # crop the best box if detected
        if len(result.boxes) == 0:
            cropped_image = image
        else:
            # select the box with highest confidence
            best_box = result.boxes[torch.argmax(result.boxes.conf)]
            x1, y1, x2, y2 = best_box.xyxy[0].tolist()

            h, w = image.shape[:2]
            sx1, sy1, sx2, sy2 = make_square_bbox_with_margin(
                (x1, y1, x2, y2), w, h
            )

            # Clamp to image bounds
            sx1, sy1 = max(0, int(sx1)), max(0, int(sy1))
            sx2, sy2 = min(w, int(sx2)), min(h, int(sy2))

            cropped_image = image[sy1:sy2, sx1:sx2]

        dataSize = cropped_image.shape[:2] # (height, width)

        cropped_image = self.data_transforms(PIL.Image.fromarray(cropped_image))
        dataPreprocessed = cropped_image.unsqueeze(0)

        return dataPreprocessed, dataSize

    # -------------------------------------------------------------------------------
    ### Function to reduce multi bands data to 1 band image
    ## param pImage : image to treat
    ## return An one band image
    # def fctreduceTo1Band(self, pImage):
    #    # ...
    #    # to customize here if the template in UC<useCase>.py is not correct
    #    # ...
    #    # return img_image1B
    #    pass

    # -------------------------------------------------------------------------------
    ### Function to construct mega-pixels
    ## param pImage : image to treat
    ## return map of mega-pixels
    # def fctMegaPixels(self, pImage):
    #    # ...
    #    # to customize here if the template in UC<useCase>.py is not correct
    #    # ...
    #    # return img_map
    #    pass

    # -------------------------------------------------------------------------------
    ## Call function
    # @param pData : data to treat
    # @return inference result
    def __call__(self, pData):

        resInference = []
        for x in pData:
            if not isinstance(x, self.inputModelFramework):
                x = self.convertDataToFramework(x, self.inputModelFramework)
            x = torch.unsqueeze(x,0)
            if self.cuda:
                x = x.cuda(device=torch.cuda.current_device()).float()
            inference = self.model(x)
            output_data = inference.cpu().detach().numpy()[0]
            inference_argmax = [1 if i == np.argmax(output_data) else 0 for i in range(len(output_data))]

            if self.inferenceCible:
                # prediction mode
                resInference.append(inference_argmax)
            else:
                # explanation mode
                if self.returnCall == "inference":
                    resInference.append(inference)
                else:
                    resInference.append(inference_argmax)

        if self.inferenceCible:
            # prediction mode
            resInference = np.asarray(resInference)
            resInference = torch.from_numpy(resInference)
            resInference = resInference.type(torch.FloatTensor)
            self.resPredictionsCibles.append(resInference)
        else:
            # explanation mode
            if self.returnCall != "inference":
                resInference = np.asarray(resInference)
                if not isinstance(resInference, self.XAIframework[1]):
                    resInference = self.convertPredictionToFramework(resInference, self.XAIframework[1])

        return resInference

    # -------------------------------------------------------------------------------
    ## predict_proba function for AIX360 metrics
    # @param pData : input data
    # @result probability
    def predict_proba(self, pData):
        # preparation
        x = pData.reshape(self.inputModelSize[0], self.inputModelSize[1], 3)
        if not isinstance(x, self.inputModelFramework):
            x = self.convertDataToFramework(x, self.inputModelFramework)
        x = torch.unsqueeze(x,0)
        if self.cuda:
            x = x.cuda(device=torch.cuda.current_device()).float()
        # model outputs
        inference = self.model(x)
        # softmax to get proba
        proba = F.softmax(inference, dim=0).detach().cpu().numpy()
        return proba

    # -------------------------------------------------------------------------------
    ## convert data to dedicated framework
    # @param pXData : data to convert
    # @param pFramework : XAI framework
    # @result converted data
    def convertDataToFramework(self, pXData, pFramework):
        if pFramework == torch.Tensor:
            pXData = np.swapaxes(pXData, -1, 0)
            pXData = torch.Tensor(pXData)
        elif pFramework == eTensor.EagerTensor:
            pXData = tf.concat(pXData, axis=0)
            pXData = np.swapaxes(pXData, -1, 1)
            pXData = tf.convert_to_tensor(pXData)
        elif pFramework == np.ndarray:
            pXData = pXData.numpy()
            pXData = np.swapaxes(pXData, -1, 1)
        else:
            colPrint("The method 'convertDataToFramework' of the class dedicated to %s does not implement the conversion process from %s to %s"%(self.id, type(pXData), str(pFramework)), "Error")
        return pXData

    # -------------------------------------------------------------------------------
    ## convert prediction to dedicated framework
    # @param pYPred : prediction to convert
    # @param pFramework : XAI framework
    # @result converted prediction
    def convertPredictionToFramework(self, pYPred, pFramework):
        if pFramework == eTensor.EagerTensor:
            pYPred = tf.convert_to_tensor(pYPred)
        elif pFramework == torch.Tensor:
            pYPred = torch.Tensor(pYPred)
        elif pFramework == np.ndarray:
            pYPred = pYPred.numpy()
        else:
            colPrint("The method 'convertPredictionToFramework' of the class dedicated to %s does not implement the conversion process from %s to %s"%(self.id, type(pYPred), str(pFramework)), "Error")
        return pYPred

# -------------------------------------------------------------------------------
# end of file
