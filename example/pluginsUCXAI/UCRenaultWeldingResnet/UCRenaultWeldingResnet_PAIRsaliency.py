#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ===============================================================================

import numpy as np

from kaasrc.communs import colPrint
import kaasrc.plugin_collection
import kaasrc.communs

# ---------
try:
    import torch
except Exception as err:
    print("Error:", err)
    colPrint("Package torch is uninstalled.", "Error")
# ---------

from . import UCRenaultWeldingResnet

# -------------------------------------------------
# ## Function that interfaces with a model to return specific output
# ## in a dictionary when given an input and other arguments.
# @param x_value : Input for the model
# @param call_model_args : Other arguments used to call and run the model
# @param expected_keys : List of keys that are expected in the output
# @return outputs of the model
def PAIR_OutputLayerValues(pXvalue,call_model_args,expected_keys=None):
    aiModel = call_model_args['aiModel']
    targets = call_model_args['targets']
    target_idx = np.argmax(targets)
    pXvalue = torch.from_numpy(pXvalue).type(torch.float32)
    pXvalue = torch.movedim(pXvalue, 3, 1)
    output = aiModel(pXvalue)
    output = torch.cat(output, dim=0)
    output = output.cpu().detach()
    output = [output[:,target_idx]]
    return {"OUTPUT_LAYER_VALUES": output}

# -------------------------------------------------
# ## Function that interfaces with a model to return specific output
# ## in a dictionary when given an input and other arguments.
# @param x_value : Input for the model
# @param call_model_args : Other arguments used to call and run the model
# @param expected_keys : List of keys that are expected in the output
# @return gradients w.r.t the model
def PAIR_InputOutputGradients(pXvalue,call_model_args,expected_keys=None):
    pXvalue = torch.from_numpy(pXvalue).type(torch.float32)
    pXvalue = torch.movedim(pXvalue, 3, 1)
    pXvalue.requires_grad_(True)
    output = call_model_args(pXvalue)
    output = torch.cat(output, dim=0)
    outputs = output[:,0]
    grads = torch.autograd.grad(outputs, pXvalue, grad_outputs=torch.ones_like(outputs))
    grads = torch.movedim(grads[0], 1, 3)
    gradients = grads.detach().numpy()
    return {"INPUT_OUTPUT_GRADIENTS": gradients}

# -------------------------------------------------
# ## Function that interfaces with a model to return specific output
# ## in a dictionary when given an input and other arguments.
# @param x_value : Input for the model
# @param call_model_args : Other arguments used to call and run the model
# @param expected_keys : List of keys that are expected in the output
# @return gradients w.r.t the model
def PAIR_ConvolutionGradientsAndValues(pXvalue,call_model_args,expected_keys=None):
    pXvalue = torch.from_numpy(pXvalue).type(torch.float32)
    pXvalue = torch.movedim(pXvalue, 3, 1)
    pXvalue.requires_grad_(True)
    output = call_model_args(pXvalue)
    output = torch.cat(output, dim=0)
    one_hot = torch.zeros_like(output)
    one_hot[:,0] = 1
    call_model_args.model.zero_grad()
    output.backward(gradient=one_hot, retain_graph=True)
    return call_model_args.conv_layer_outputs

# ------------------------------------------------------------------------------
## Class for Use case vs Library
class UCRenaultWeldingResnet_PAIRsaliency(kaasrc.plugin_collection.Plugin):
    # ---------------------------------------------------------------------------------
    ## Class constructor
    # @param self : l'instance de la classe
    def __init__(self):
        super().__init__()
        self.nom = "UCRenaultWeldingResnet"
        self.description = UCRenaultWeldingResnet.RenaultWeldingResnet.RenaultWeldingResnet.description
        self.modeles = ["Resnet"]
        self.bibliotheque = "PAIRsaliency"
        self.methodes = ["GuidedIG","SmoothGrad-GuidedIG","VanillaGradients","SmoothGrad-VanillaGradients","BlurIG","SmoothGrad-BlurIG","GradCAM","IntegratedGradients", "Occlusion"]
        self.metriques = None
        self.UC = UCRenaultWeldingResnet

    # ---------------------------------------------------------------------------
    ## Create an instance of the model
    # @param pDictParams : parameter dictionary
    # @return the instance of the model
    # @remark Call directly UC_createModel() of UC model
    def UCXAI_createModel(self, pDictParams):
        aiModel = self.UC.UC_createModel(pDictParams)
        aiModel.useCase.returnCall="inference"
        return aiModel

    # ---------------------------------------------------------------------------
    ## Compute the data inference with model
    # @param pAiModel : model instance
    # @param pDictParams : parameter dictionary
    # @return data, prediction, list of inference error against truth
    # @remark Call directly UC_computeInference() of UC model
    def UCXAI_computeInference(self, pAiModel, pDictParams):
        return self.UC.UC_computeInference(pAiModel, pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the explanations computation
    # @param pDictParams : parameter dictionary
    def UCXAI_computeExplanations(self, pDictParams):
        # shortcuts
        pMethod = pDictParams['method']

        if pMethod=="GradCAM":
            pDictParams['callModelFunctionToGradient'] = PAIR_ConvolutionGradientsAndValues
        elif pMethod=="Occlusion":
            pDictParams['callModelFunctionToGradient'] = PAIR_OutputLayerValues
        else:
            pDictParams['callModelFunctionToGradient'] = PAIR_InputOutputGradients

        pDictParams['pluginXAI'].XAI_computeExplanations(pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the explanations plotting
    # @param pDictParams : parameter dictionary
    def UCXAI_plotExplanations(self, pDictParams):

        def fctExplain(pDictParams,oneExplanation,index):
            # Resize according plot shape (tw TUI command)
            explanation = np.transpose(oneExplanation)
            explanation=kaasrc.communs.fctExplanationToPlotResized(pDictParams,explanation,index)
            return explanation

        pDictParams['pluginXAI'].XAI_plotExplanations(pDictParams,pFctExplainToPlot=fctExplain,pFctDataToPlot=self.UC.UC_ImageDataToPlot)

    # ---------------------------------------------------------------------------
    ## Launch the metrics computation
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_computeMetrics() of XAI plugin
    def UCXAI_computeMetrics(self, pDictParams):
        pDictParams['pluginXAI'].XAI_computeMetrics(pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the metrics plotting
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_plotMetrics() of XAI plugin
    def UCXAI_plotMetrics(self, pDictParams):
        pDictParams['pluginXAI'].XAI_plotMetrics(pDictParams)

    # ---------------------------------------------------------------------------
    ## Launch the report writing as contact sheet
    # @param pDictParams : parameter dictionary
    # @remark Call directly XAI_writeReport() of XAI plugin
    def UCXAI_writeReport(self, pDictParams):
        pDictParams['pluginXAI'].XAI_writeReport(pDictParams)

# ===============================================================================
# end of file
