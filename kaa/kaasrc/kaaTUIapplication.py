#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================

import os, time, shutil, json

import kaasrc.mpTUI
from kaasrc.communs import colPrint
import kaasrc.kaaActions
from contextlib import redirect_stdout, redirect_stderr

# ---------
try:
    import tensorflow.compat.v2 as tf
    tf.config.run_functions_eagerly(True)
except Exception as err:
    print("Error:", err)
    colPrint("Package tensorflow is not or not properly installed.", pType="Error")
# ---------

# -------------------------------------------------------------------------------
## TUI menu class
class MenuTUI:
    # ---------------------------------------------------------------------------
    # Initialisation function
    # @param pPluginsXAI  : classe des plugins d'explicabilité XAI
    # @param pPluginsUCXAI : classe des plugins UC vs XAI
    # @param pFichierCommandes : fichier de commandes
    # @param debug : optionel ; non debug par défaut, activable pas !d!
    def __init__(self, pPluginsXAI, pPluginsUCXAI, pRepResultProd, pRepUseCaseBase, debug=False):
        # conservation du flag du mode debug, des plugins et des répertoires de cas d'usage et de données produites
        self.debug = debug
        self.echo = True
        self.pluginsXAI = pPluginsXAI
        self.pluginsUCXAI = pPluginsUCXAI
        self.repResultProd = pRepResultProd
        self.repUseCaseBase = pRepUseCaseBase
        # préparation de la table/carte mega dictionnaire des (UC, modèle, xai, methodes, métriques)
        self.table = {}
        for cu in pPluginsUCXAI.plugins:
            if cu.nom not in self.table:
                self.table[cu.nom] = {}
            for mod in cu.modeles:
                if mod not in self.table[cu.nom].keys():
                    self.table[cu.nom][mod] = {}
                self.table[cu.nom][mod][cu.bibliotheque] = {'methodes': cu.methodes, 'metriques': cu.metriques}
            self.table[cu.nom]['plugin'] = cu.UC

        # liste ordonnée des cas d'usages pour la comboBox 'cbxCasUsage'
        casDusage = list(self.table.keys())
        casDusage.sort()

        # Bloc de parametres et variables des cas d'usage
        modelsParams = []
        varModelsParams = []
        self.modelParams = {}
        self.modelCle = {}
        for i, cu in enumerate(casDusage):
            if hasattr(self.table[cu]['plugin'], "getModelParams"):
                cmd = "c%i"%i
                modelOptions = self.table[cu]['plugin'].getModelParams()
                modelParams, _, varModelParams, _ = self.paramModel(modelOptions, cu, cmd)
                modelsParams += modelParams
                varModelsParams += varModelParams
                self.modelParams[cu] = modelOptions
                self.modelCle[cu] = cmd
        listeActions = []
        self.listeParams = []
        # Bloc de parametres et variables des méthodes présentes
        methodes, self.aideMethodes, varMethodes, listeActions = self.paramMethode(pPluginsXAI, listeActions)

        # Bloc de parametres et variables des méthodes présentes
        metriques, self.aideMetriques, varMetriques = self.paramMetrique(pPluginsXAI)

        # Préparation du menu TUI
        elementsBlocl1 = [
            # ==== [(U) USE CASE ] ==============================================================
            [{'COLON':1, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ("_",5," MODEL ")}],
            [{'COLON':1, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.0, 'TYPE': 'CBX', 'ACTION': 'c', 'OFFSET': 2, 'NOM': 'cbxCasUsage', 'LARG': 38, 'TEXTE': "Use case ", 'OPTIONS': casDusage, 'SELECT': "@CBXcasdusage@", "AIDE": ["Select the use case you want to test", None]}],
            [{'COLON':1, 'TAB':1.0, 'TYPE': 'CBX', 'ACTION': 'o', 'OFFSET': 2, 'NOM': 'cbxModele'  , 'LARG': 38, 'TEXTE': "Model    ", 'OPTIONS': []  , 'SELECT': "@CBXmodele@", "AIDE": ["Select the model you want to test", None]}]]
        elementsBlocl2 = [
            # ==== [(D) DATASET ] ===============================================================
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ("_",5," DATASET ")}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'LBL', 'OFFSET': 2, 'TEXTE': "Selection mode "}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'CBX', 'ACTION': 'dm', 'OFFSET': 6, 'NOM': 'cbxModeData', 'LARG': 40, 'TEXTE': "", 'OPTIONS': ["data from a specific file",
                                                                                                                               "one or more data from config file list",
                                                                                                                               "all data from dataset",
                                                                                                                               "selection of data from dataset"], 'SELECT': "@CBXdataListMode@",
                                                                                                                    "AIDE": ["Select one or multiple datasets from the list in the configuration file.", None]}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'EDT', 'ACTION': 'dd', 'OFFSET': 4, 'NOM': 'edtFichData', 'LARG': 40, 'TEXTE': "File ", 'ALIGN': 'G', 'SELECT': "@EDTdataListFichier@","AIDE":"File to use to defining datas"}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'LBL'              , 'OFFSET': 2                    , 'LARG': 6, 'TEXTE': "Num.Data "},
             {'COLON':2, 'TAB':1.0, 'TYPE': 'LBL'              , 'OFFSET': 10                   , 'LARG': 6, 'TEXTE': "Offset ", 'CONDVIS': ('dm', [3])},
             {'COLON':2, 'TAB':1.0, 'TYPE': 'LBL'              , 'OFFSET': 12                   , 'LARG': 6, 'TEXTE': "Step ", 'CONDVIS': ('dm', [3])}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'EDT', 'ACTION': 'dn', 'OFFSET': 2 , 'NOM': 'edtNbdata' , 'LARG': 6, 'SELECT': "@EDTnbData@","AIDE":"Number of data to treat"},
             {'COLON':2, 'TAB':1.0, 'TYPE': 'EDT', 'ACTION': 'do', 'OFFSET': 7 , 'NOM': 'edtOffset' , 'LARG': 6, 'SELECT': "@EDToffset@", 'CONDVIS': ('dm', [3]),"AIDE":"Offset of the begining of the list of data"},
             {'COLON':2, 'TAB':1.0, 'TYPE': 'EDT', 'ACTION': 'dp', 'OFFSET': 7 , 'NOM': 'edtPas'    , 'LARG': 6, 'SELECT': "@EDTstepData@", 'CONDVIS': ('dm', [3]),"AIDE":"Step between data to treat"}],
            [{'COLON':2, 'TAB':1.0, 'TYPE': 'SEP', 'TEXTE': ""}],
            # ==== [(B) EXPLAINABILITY ] ========================================================
            [{'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'TAB':1.1, 'TYPE': 'CBX', 'ACTION': 'b', 'OFFSET': 2, 'NOM': 'cbxBibliotheque', 'LARG': 36, 'TEXTE': "Libraries   ", 'OPTIONS': [], 'SELECT': "@CBXbibliotheque@", "AIDE": ["Select a library to explain the model predictions.", None]}],
            [{'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ""}],
            # -------- [(H) METHODS ] -----------------------------------------------------------  -
            [{'COLON':1, 'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ('_',5," METHODS ")}],
            [{'COLON':1, 'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.1, 'TYPE': 'CBX', 'ACTION': 'h', 'OFFSET': 2, 'NOM': 'cbxMethode', 'LARG': 33   , 'TEXTE': "Methods     ", 'OPTIONS': [], 'SELECT': "@CBXmethode@", "AIDE": ["Select a method to calculate the importance of the input features.", None]}]]
        elementsBlocl3 = [
            # -------- [(Q) METRICS ] -----------------------------------------------------------  -
            #[{'COLON':2, 'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': "b3"}],
            [{'COLON':2, 'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ('_',5," METRICS ")}],
            [{'COLON':2, 'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.1, 'TYPE': 'CBX', 'ACTION': 'm', 'OFFSET': 2, 'NOM': 'cbxMetrique', 'LARG': 33  , 'TEXTE': "Metrics     ", 'OPTIONS': [], 'SELECT': "@CBXmetrique@", "AIDE": ["Calculate evaluation metrics to measure the model performance.", None]}]]
        elementsBlocl4 = [
            [{'COLON':2, 'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.1, 'TYPE': 'GCB', 'ACTION': 'u', 'NOM': 'ckbMetrique' , 'OFFSET': 2, 'LARG': 14, 'COL': 2, 'TEXTE': "Metric on", 'OPTIONS': [], 'SELECT': "@GCBmetriquesOn@","AIDE":"List of methods to evaluate with the metric"}],
            [{'COLON':2, 'TAB':1.1, 'TYPE': 'SEP', 'TEXTE': ""}],
            # -------- [(C) VISUALISATION ] -----------------------------------------------------  -
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ("_",5," VISUALISATION ")}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'CBX', 'ACTION': 'tcm', 'OFFSET': 2  , 'NOM': 'cbxModeCmap'   , 'LARG': 38, 'TEXTE': "Colormap ", 'OPTIONS': ["one colormap in the list", "colormap from a specific file"], 'SELECT': "@CBXcmapListMode@",
                                                                                                                    "AIDE": ["Select one or multiple datasets from the list in the configuration file.", None]}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'EDT', 'ACTION': 'tcf', 'OFFSET': 4  , 'NOM': 'edtColorData'  , 'LARG': 38, 'SELECT': "@EDTcmapListColor@", 'TEXTE': "File   ", 'ALIGN': 'G',"AIDE":"File containing the colormap"}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'CBX', 'ACTION': 'tc' , 'OFFSET': 4  , 'NOM': 'cbxCmap'       , 'LARG': 16, 'TEXTE': "List    ", 'OPTIONS': ["hot", "jet", "nipy_spectral", "plasma", "tab20b", "terrain"], 'SELECT': "@CBXcmap@", "AIDE": ["Apply the colormap to represent the importance scores.",
                                                                                                                                                                                              ["Matplotlib colormap hot", "Matplotlib colormap jet", "Matplotlib colormap nipy_spectral", "Matplotlib colormap plasma", "Matplotlib colormap tab20b", "Matplotlib colormap terrain"]]}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'EDT', 'ACTION': 'tp' , 'OFFSET': 2  , 'NOM': 'edtPersentile' , 'LARG': 6, 'TEXTE': "Percentile "  , 'SELECT': "@EDTpercentile@", "AIDE": "Select the percentile to define the range of values represented."},
             {'COLON':1, 'TAB':1.2, 'TYPE': 'EDT', 'ACTION': 'ta' , 'OFFSET': 2  , 'NOM': 'edtAlpha'      , 'LARG': 6, 'TEXTE': "Transparency ", 'SELECT': "@EDTalpha@"     , "AIDE": "Adjust the transparency for overlay on the input image."}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'CKB', 'ACTION': 'tn' , 'OFFSET': 3  , 'NOM': 'ckbNormer'     , 'LARG': 4, 'ALIGN': 'G', 'TEXTE': "Normalise "    , 'SELECT': "@CKBnormalise@" , "AIDE": "Normalize the importance scores for better interpretation."},
             {'COLON':1, 'TAB':1.2, 'TYPE': 'CKB', 'ACTION': 'tl' , 'OFFSET': 13 , 'NOM': 'ckbLegender'   , 'LARG': 4, 'ALIGN': 'G', 'TEXTE': "Legend "       , 'SELECT': "@CKBlegender@"  , "AIDE": "Add a legend to explain the meaning of the colors."}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'EDT', 'ACTION': 'fz' , 'OFFSET': 3  , 'NOM': 'edtFontSize'   , 'LARG': 6, 'TEXTE': "Font size ", 'SELECT': "@EDTfontSize@"     , "AIDE": "Adjust the font size of the legend."}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],

            [{'COLON':1, 'TAB':1.2, 'TYPE': 'LBL'               , 'OFFSET': 2 , 'TEXTE': "Tabular use case", 'CONDVIS': ('@datatype@', ['tabular'])}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'EDT', 'ACTION': 'r', 'OFFSET': 4 , 'CONDVIS': ('@datatype@', ['tabular']), 'TEXTE': 'Item explanations ', 'NOM': 'edtItems', 'LARG': 26, 'SELECT': "@EDTitems@","AIDE":"Item toexplanation to report (tabular use case only)"}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': "", 'CONDVIS': ('@datatype@', ['tabular'])}],

            [{'COLON':1, 'TAB':1.2, 'TYPE': 'RAD', 'ACTION': 'tw', 'OFFSET': 2 , 'NOM': 'radPlotDataSize' , 'LARG': 14, 'TEXTE': "Plot size", 'DECALAGE': 4,  'OPTIONS': [" model size", " data size"], 'SELECT': "@RADplotdatasize@","AIDE":""}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SPB', 'ACTION': 'th', 'OFFSET': 4 , 'NOM': 'spnHeightPlot' , 'LARG': 6, 'TEXTE': "Image height (inch) ", 'INTERVALLE': (1, 10, 1, 2), 'DECALAGE': 0, 'SELECT': "@SPBheightPlot@","AIDE":""}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SPB', 'ACTION': 'nc', 'OFFSET': 2 , 'NOM': 'spnColLatex' , 'LARG': 6, 'TEXTE': "Quick report: Num.Columns ", 'INTERVALLE': (1, 6, 1, 2), 'DECALAGE': 0, 'SELECT': "@SPBnbColLatex@","AIDE":""}],
            [{'COLON':1, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],

            # ==== [(F) FULL REPORT ] ===============================================================
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE':("_",5," FULL REPORT ")}],
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'GCB', 'ACTION': 'f','NOM': 'ckbReports' ,'OFFSET':2,'LARG':20,'COL':2,'TEXTE':"Report on",'OPTIONS':["Explanations" ,"Metrics"],'SELECT':"@GCBreports@"}],  # en attente
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'CBX', 'ACTION': 'fe',  'OFFSET': 2 , 'NOM': 'fExplanations','LARG':16, 'TEXTE':"Report the explanations sorted by ", 'OPTIONS':["method","data"],'SELECT':"@CBXereport@",'CONDVIS':('@GCBreports@',[[0],[0,1]])}],
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'SEP', 'TEXTE': "",'CONDVIS':('@GCBreports@',[[0],[0,1]])}],
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'SPB', 'ACTION': 'nch', 'OFFSET': 2 , 'NOM': 'spnColFullLatexMethod' , 'LARG': 6, 'TEXTE': "Num. columns for method results", 'INTERVALLE': (1, 6, 1, 2), 'DECALAGE': 0, 'SELECT': "@SPBnbColFullLatexMethod@","AIDE":""}],
            [{'COLON':2, 'TAB':1.2, 'TYPE': 'SPB', 'ACTION': 'ncq', 'OFFSET': 2 , 'NOM': 'spnColFullLatexMetric' , 'LARG': 6, 'TEXTE': "Num. columns for metric results", 'INTERVALLE': (1, 6, 1, 2), 'DECALAGE': 0, 'SELECT': "@SPBnbColFullLatexMetric@","AIDE":""}],

            # ==== [(A) ACTIONS ] ===============================================================
            [{'COLON':1, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': ("_",5," ACTIONS ")}],
            [{'COLON':1, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.3, 'TYPE': 'GCB', 'ACTION': 'a', 'NOM': 'ckbActions' , 'OFFSET': 6, 'LARG': 20, 'COL': 2, 'TEXTE': "Possible actions", 'OPTIONS': ["Inference", "Explanations", "Plot explanations", "Metrics", "Plot metrics", "Quick report", "Full report"], 'SELECT': "@GCBactions@",
                                            "AIDE": ("Select the actions to perform.", ["Perform an inference using the model to predict the output for the selected data."
                                                                                , "Generate explanations for the model predictions, helping to understand how it reaches its conclusions."
                                                                                , "Display the explanations graphically for better visualization of the important features."
                                                                                , "Calculate the evaluation metrics of the model."
                                                                                , "Plot the evaluation metrics of the model to analyze its evolution."
                                                                                , "Generate a quick report summarizing the results of the explanation and evaluation."
                                                                                , "Generate a full report summarizing all the results generated on the use case."])}],
            [{'COLON':1, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':1, 'TAB':1.3, 'TYPE': 'BTN', 'ACTION': 'l', 'OFFSET': 28        , 'TEXTE': "Launch actions ", "AIDE": "Execute the selected actions."}],
            [{'COLON':1, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': ""}],
            # ==== [(G) MANAGEMENT ] ============================================================
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': "" }],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': ("_",5," MANAGEMENT ")}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': ""}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'EDT', 'ACTION': 'L', 'OFFSET': 2 , 'LARG': 10   , 'TEXTE': "Log extension          ", 'SELECT': "@EDTextensionLog@", "AIDE": "Activate the log extension to record the execution details."}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'EDT', 'ACTION': 'P', 'OFFSET': 2 , 'LARG': 10   , 'TEXTE': "Prod. path extension   ", 'SELECT': "@EDTextensionProd@", "AIDE": "Set the output directory for the generated files (Test)."}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': "" }],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'CKB', 'ACTION': 'T', 'OFFSET': 2 , 'ALIGN': 'G' , 'TEXTE': "Traces in logs         ", 'SELECT': "@CKBtrace@", "AIDE": "Activate the recording of execution traces in the logs (disabled)."}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'LBL', 'ACTION': 'Z', 'OFFSET': 2 , 'ALIGN': 'D' , 'TEXTE': "Remove logs            ", "AIDE": "Delete the previously generated logs."}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': "" }],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'CKB', 'ACTION': 'K', 'OFFSET': 2 , 'ALIGN': 'G' , 'TEXTE': "Check types and shapes ", "AIDE": "For use case integration process, check types and shapes of data throughout the process (9 points).", 'SELECT': "@CKBcontrols@"}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'SEP', 'TEXTE': "" }],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'LBL', 'ACTION': 'V', 'OFFSET': 2 , 'ALIGN': 'D' , 'TEXTE': "Save context           ", "AIDE": "Save the context of the execution for a later resumption."}],
            [{'COLON':2, 'TAB':1.3, 'TYPE': 'LBL', 'ACTION': 'X', 'OFFSET': 2 , 'ALIGN': 'D' , 'TEXTE': "Save and Quit          ", "AIDE": "Save the context and quit the application."}],
            ]

        # variables pour sauvegarder le contexte
        variables = {
            'CBXcasdusage': 0      , 'CBXmodele': -1,
            'CBXdataListMode': 0   , 'EDTdataListFichier': "",
            'EDTnbData': "0"       , 'EDToffset': "0"         , 'EDTstepData': "1"     , #'fltData': "*",
            'CBXbibliotheque': 0   , 'CBXmethode': 0          , 'CBXmetrique': 0       , 'GCBactions': [],
            'GCBmetriquesOn': []   , 'EDTextensionLog': ""    , 'EDTextensionProd': "" , 'CKBtrace': 0,
            'EDTpercentile': "1"   , 'EDTalpha': "0.6"        , 'CBXcmapListMode': 0   , 'EDTcmapListColor': "",
            'CBXcmap': 0           , 'CKBnormalise': 1        , 'EDTfontSize': "12",
            'CKBlegender': 0       , 'SPBheightPlot': 5       , 'RADplotdatasize': 0   , 'SPBnbColLatex': 3,
            'EDTitems': '1-10'     , 'CKBcontrols': 0,
            'GCBreports':[]        , 'CBXereport':0           , 'mreport':"0"          , 'SPBnbColFullLatexMethod': 4, 'SPBnbColFullLatexMetric': 2,
            'datatype': ""       #, 'modeltype': ""
            }
        for variable, valeur in varModelsParams:
            variables[variable] = valeur
        for variable, valeur in varMethodes:
            variables[variable] = valeur
        for variable, valeur in varMetriques:
            variables[variable] = valeur

        # Création de la classe du menu TUI
        self.appliTUI = {
            #'TUIVERSION': "3.0",
            'TITRE'        : 'KAA',
            'VERSION'      : kaasrc.kaaActions.KAAVERSION,
            'PALETTE'      : "tuiKaa.pal",
            #'LARGEUR'      : [92,2,92],#92,
            'LARGEUR' : [60,2,60],
            'HAUTEUR'      : 27,
            'MARGE'        : 1,
            'ELEMENTS'     :
                [[{'TYPE':'TAB','TAB':1,'ACTION':'k','OPTIONS':[" USE CASE "," EXPLAINABILITY "," REPORTS "," EXECUTION "],'SELECT':0,
                   'AIDE':('Tabs to manage yours explanations',['Use case definition','Explainability methods ans metrics','Cursomization of the reports','Configuration and launcher'])}]]+
                elementsBlocl1 + modelsParams + elementsBlocl2 + methodes + elementsBlocl3 + metriques + elementsBlocl4,
            'VARIABLES'    : variables,
            'CONFIGURATION': "tuiKaa.cfg",
            'QUITTER'      : 'X'}
        #self.tui = kaasrc.TUI.TUI(appliTUI, debug)

        self.tui = kaasrc.mpTUI.TUI(self.appliTUI, debug)
        #mpTUI.TUI_boucle(self.tui)#,pInitialisationTUI=menu.initialisation)

    # ---------------------------------------------------------------------------
    ## Methode d'affichage du mode debug
    # @param args : éléments à afficher
    def _debug(self, *args):
        if not self.debug:
            return
        print(kaasrc.communs.fYellow + "DEBUG > ", end=" ")
        for e in args:
            print(e, end=" ")
        print()

    # ---------------------------------------------------------------------------
    ## Methode de récupération des méthodes et leurs paramètres depuis les plugins disponibles
    # @param pPluginsXAI : classe des plugins XAI disponibles
    # @param pListeActions : liste des éléments d'action pour contrôle des doublons
    # @return tuple (méthodes , aides, paramètre, list d'actions)
    def paramMethode(self, pPluginsXAI, pListeActions):
        methodes = []
        aideMethodes = {}
        varMethodes = []
        # Pour chaque bibliothèque d'XAI présente...
        for plugin in pPluginsXAI.plugins:
            self._debug("Nom", plugin.nom, "clef menu", plugin.clef)
            self._debug("Méthodes", plugin.methodes)
            # Pour chaque méthode de la bibliothèque d'XAI présente...
            for methode in plugin.methodes:
                self._debug("  - methode", methode)
                # On defini le groupe TUI
                groupe = "METHODE*%s:%s"%(plugin.nom, methode)
                self._debug("    groupe", groupe)
                # On récupère la lettre clef de la méthode et la liste des paramètres
                aideMethode = None
                if len(plugin.methodes[methode]) == 3:
                    clefMethode, listeParam, aideMethode = plugin.methodes[methode]
                else:
                    clefMethode, listeParam = plugin.methodes[methode]

                aideMethodes["%s:%s"%(plugin.nom, methode)] = aideMethode
                if listeParam is None:
                    listeParam = []
                # Pour chaque paramètre on crée un editeur TUI
                # et on enregistre la variable associé au paramètre
                for param in listeParam:
                    dictionnaire = None
                    aide = None
                    if len(param) == 5:
                        nom, clef, defaut, dictionnaire, aide = param
                    elif len(param) == 4:
                        nom, clef, defaut, descdico = param
                        if isinstance(descdico, str):
                            aide = descdico
                        else:
                            dictionnaire = descdico
                    else:
                        nom, clef, defaut = param

                    action = plugin.clef + clefMethode + clef
                    entreeAide = plugin.clef + '.' + clefMethode + '.' + clef
                    if entreeAide in self.listeParams:
                        colPrint("/!\\ Doublon de commande de paramètre '%s' pour plugin %s / methode %s / paramètre %s !"%(action, plugin.nom, methode, nom),pType="Error")
                    self.listeParams.append(entreeAide)
                    self._debug("    parametre", param, nom, action)

                    dicoMethode = {'COLON':1, 'TAB':1.1, 'GROUP': groupe, 'TYPE': 'EDT', 'ACTION': action, 'OFFSET': 6, 'LARG': 16, 'TEXTE': "%s "%nom, 'SELECT': "@"+action+"@"}
                    if dictionnaire is not None:
                        if "options" in dictionnaire:
                            options = dictionnaire["options"]
                            options.sort()
                            dicoMethode['OPTIONS'] = options
                            dicoMethode['TYPE'] = 'CBX'
                        if "lien" in dictionnaire:
                            dicoMethode["CONDVIS"] = dictionnaire["lien"]
                    if aide is not None:
                        dicoMethode['AIDE'] = aide

                    varMethodes.append((action, str(defaut)))
                    methodes.append([dicoMethode])

                # Contrôle des doublons
                if plugin.clef + clefMethode in pListeActions:
                    colPrint("/!\\ Doublon d'action '%s' pour plugin %s / methode %s !"%(plugin.clef + clefMethode, plugin.nom, methode),pType="Error")
                pListeActions.append(plugin.clef + clefMethode)
        return methodes, aideMethodes, varMethodes, pListeActions

    # ---------------------------------------------------------------------------
    ## Methode de récupération des modèles et leurs paramètres depuis la lecture des options des cas d'usage
    # @param options : les paramètres du modèle
    # @param model : le modèle étudié
    # @param cmd : commande TUI du cas d'usage : c < rang >
    # @return tuple (modèles , aides, paramètre, list d'actions)
    def paramModel(self, options, model, cmd):
        modelParams = []
        aideModelParams = {}
        varModelParams = []
        pListeActionsModelParams = []

        # Pour chaque bibliothèque d'XAI présente...
        premier = True

        for param in options:
            groupe = "MODEL*%s"%model
            if premier:
                modelParams.extend([[{'COLON':1, 'TAB':1.0, 'GROUP': groupe, 'TYPE': 'SEP', 'TEXTE': ""}],
                                    [{'COLON':1, 'TAB':1.0, 'GROUP': groupe, 'TYPE': 'LBL', 'OFFSET': 2, 'TEXTE': "Model parameters"}]])
                premier = False
            dictionnaire = None
            aide = None
            if len(param) == 5:
                nom, clef, defaut, dictionnaire, aide = param
            elif len(param) == 4:
                nom, clef, defaut, descdico = param
                if isinstance(descdico, str):
                    aide = descdico
                else:
                    dictionnaire = descdico
            else:
                nom, clef, defaut = param

            action = cmd + clef
            self._debug("    parametre", param, nom, action)

            dicoModel = {'COLON':1, 'TAB':1.0, 'GROUP': groupe, 'TYPE': 'EDT', 'ACTION': action, 'OFFSET': 6, 'LARG': 16, 'TEXTE': "%s "%nom, 'SELECT': "@"+action+"@"}

            if dictionnaire is not None:
                if "options" in dictionnaire:
                    options = dictionnaire["options"]
                    options.sort()
                    dicoModel['OPTIONS'] = options
                    dicoModel['TYPE'] = 'CBX'
                if "lien" in dictionnaire:
                    dicoModel["CONDVIS"] = dictionnaire["lien"]
            if aide is not None:
                dicoModel['AIDE'] = aide
                aideModelParams[model] = aide

            varModelParams.append((action, str(defaut)))
            pListeActionsModelParams.append(action)
            modelParams.append([dicoModel])

        return modelParams, aideModelParams, varModelParams, pListeActionsModelParams

    # ---------------------------------------------------------------------------
    ## Methode de récupération des metriques et leurs paramètres depuis les plugins disponibles
    # @param pPluginsXAI : classe des plugins XAI disponibles
    # @return tuple (méthodes , paramètre, list d'actions)
    def paramMetrique(self, pPluginsXAI):
        metriques = []
        aideMetriques = {}
        varMetriques = []
        # Pour chaque bibliothèque d'XAI présente...
        for plugin in pPluginsXAI.plugins:
            self._debug("Nom", plugin.nom, "lettre menu", plugin.clef)
            self._debug("Métriques", plugin.metriques)
            # Pour chaque métrique de la bibliothèque d'XAI présente...
            if plugin.metriques is not None:
                for metrique in plugin.metriques:
                    self._debug("  - métrique", metrique)
                    # On defini le groupe TUI
                    groupe = "METRIQUE*%s:%s"%(plugin.nom, metrique)
                    self._debug("    groupe", groupe)
                    # On récupère la lettre clef de la métrique et la liste des paramètres
                    aideMetrique = None
                    if len(plugin.metriques[metrique]) == 2:
                        clefMetrique, listeParam = plugin.metriques[metrique]
                    elif len(plugin.metriques[metrique]) == 4:
                        clefMetrique, listeParam, _, aideMetrique = plugin.metriques[metrique]
                    else:
                        clefMetrique, listeParam, aideMetrique = plugin.metriques[metrique]
                        if isinstance(aideMetrique, list):
                            aideMetrique = None
                    aideMetriques["%s:%s"%(plugin.nom, metrique)] = aideMetrique
                    if listeParam is None:
                        listeParam = []
                    # Pour chaque paramètre on crée un editeur TUI
                    # et on enregistre la variable associé au paramètre
                    for param in listeParam:
                        dictionnaire = None
                        aide = None
                        if len(param) == 5:
                            nom, clef, defaut, dictionnaire, aide = param
                        elif len(param) == 4:
                            nom, clef, defaut, descdico = param
                            if isinstance(descdico, str):
                                aide = descdico
                            else:
                                dictionnaire = descdico
                        else:
                            nom, clef, defaut = param

                        action = plugin.clef + clefMetrique + clef
                        entreeAide = plugin.clef + '.' + clefMetrique + '.' + clef
                        if entreeAide in self.listeParams:
                            colPrint("/!\\ Doublon de commande de paramètre '%s' pour plugin %s / métrique %s / paramètre %s !"%(action, plugin.nom, metrique, nom),pType="Error")
                        self.listeParams.append(entreeAide)
                        self._debug("    parametre", param, nom, action)

                        dicoMetrique = {'COLON':2, 'TAB':1.1, 'GROUP': groupe, 'TYPE': 'EDT', 'ACTION': action, 'OFFSET': 6, 'LARG': 16, 'TEXTE': "%s "%nom, 'SELECT': "@"+action+"@"}
                        if dictionnaire is not None:
                            if "options" in dictionnaire:
                                options = dictionnaire["options"]
                                options.sort()
                                dicoMetrique['OPTIONS'] = options
                                dicoMetrique['TYPE'] = 'CBX'
                            if "lien" in dictionnaire:
                                dicoMetrique["CONDVIS"] = dictionnaire["lien"]
                        if aide is not None:
                            dicoMetrique['AIDE'] = aide

                        varMetriques.append((action, str(defaut)))
                        metriques.append([dicoMetrique])
        return metriques, aideMetriques, varMetriques

    # ---------------------------------------------------------------------------
    ## Methode de récupération du cas d'usage et du modèle choisis
    # @return tuple (cas d'usage, modèle)
    def casDusageModele(self):
        # Récupération du cas d'usage
        select = self.tui.TUI_getValeurParNom('cbxCasUsage', 'SELECT')
        casDusage = self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS', select)
        # Récupération du modèle
        select = self.tui.TUI_getValeurParNom('cbxModele', 'SELECT')
        modele = self.tui.TUI_getValeurParNom('cbxModele', 'OPTIONS', select)

        return casDusage, modele

    # ---------------------------------------------------------------------------
    ## Methode de récupération de la bibliothèque, la méthode et les métriques choisies
    # @return tuple (bibliothèque , méthode , métriques)
    def bibliothequeMethodeMetrique(self):
        # Récupération de la bibliothèque
        select = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'SELECT')
        bibliotheque = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'OPTIONS', select)

        # Récupération de la methode
        select = self.tui.TUI_getValeurParNom('cbxMethode', 'SELECT')
        if select == -1:
            methode = None
        else:
            methode = self.tui.TUI_getValeurParNom('cbxMethode', 'OPTIONS', select)
            #NEW if len(methode.split(':'))>1:
            #NEW     methode = methode[1]
            if bibliotheque in self.pluginsXAI.dicoPlugins and\
                self.pluginsXAI.dicoPlugins[bibliotheque].methodes is not None and\
                methode not in self.pluginsXAI.dicoPlugins[bibliotheque].methodes.keys():
                methode = None
        # Récupération de la métrique
        select = self.tui.TUI_getValeurParNom('cbxMetrique', 'SELECT')
        metriques = self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS')
        if len(metriques) == 0:
            metrique = None
        else:
            metrique = self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS', select)
            #NEW metrique = self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS', select)
            #NEW if len(metrique.split(':'))>1:
            #NEW     metrique = metrique[1]
            if bibliotheque in self.pluginsXAI.dicoPlugins and\
                self.pluginsXAI.dicoPlugins[bibliotheque].metriques is not None and\
                metrique not in self.pluginsXAI.dicoPlugins[bibliotheque].metriques.keys():
                metrique = None

        # Récupération des méthodes sur lesquelles s'appliquent la métrique
        meth4metr = []
        if len(self.tui.TUI_getValeurParNom('ckbMetrique', 'SELECT'))!=0:
            meth4metr = [self.tui.TUI_getValeurParNom('ckbMetrique', 'OPTIONS', x) for x in self.tui.TUI_getValeurParNom('ckbMetrique', 'SELECT')]

        return bibliotheque, methode, metrique, ",".join(meth4metr)

    # ---------------------------------------------------------------------------
    ## Methode de constitution du Json
    # @param pExtensionProd : extension du répertoire dataProd
    # @param pUsecase : nom du cas d'usage
    # @param pModele : nom du modèle
    # @param pBibliotheque : nom de la bibliothèque
    # @param pMethode : nom de la méthode
    # @param pMetrique : nom de la métrique
    # @param pMeth4metr : liste des méthodes pour la métrique
    # @return parameter dictionary
    def kaaJson(self, pExtensionProd, pUsecase, pModele, pBibliotheque, pMethode, pMetrique, pMeth4metr):
        # répertoire des données produites
        dataProd = os.path.join(self.repResultProd, "dataProd%s"%pExtensionProd, pBibliotheque)

        # Constitution du Json...
        if not os.path.exists(os.path.join(os.getcwd(), 'kaaJson')):
            os.makedirs(os.path.join(os.getcwd(), 'kaaJson'))

        ficJson = os.path.join(os.getcwd(), "kaaJson", "kaa%s.json"%pExtensionProd)
        colPrint(" - Json file: %s"%ficJson)
        with open(ficJson, 'w', encoding="utf-8") as f:
            f.write('{\n')

            # Les bases du travail
            f.write(' "dataProd": "%s"\n'%dataProd)

            # Les paramètres de tracé
            f.write(', "legender": %s\n'%self.tui.TUI_getVariable('CKBlegender'))
            f.write(', "percentile": %s\n'%self.tui.TUI_getVariable('EDTpercentile'))
            f.write(', "alpha": %s\n'%self.tui.TUI_getVariable('EDTalpha'))
            f.write(', "normalise": %s\n'%self.tui.TUI_getVariable('CKBnormalise'))
            f.write(', "fontSize": %s\n'%self.tui.TUI_getVariable('EDTfontSize'))
            f.write(', "cmap": "%s"\n'%self.tui.TUI_getValeurParNom('cbxCmap', 'OPTIONS', self.tui.TUI_getVariable('CBXcmap')))
            f.write(', "heightPlot": %d\n'%self.tui.TUI_getVariable('SPBheightPlot'))
            f.write(', "nbColLatex": %d\n'%self.tui.TUI_getVariable('SPBnbColLatex'))
            f.write(', "items": "%s"\n'%self.tui.TUI_getVariable('EDTitems'))
            f.write(', "plotDataSize": %d\n'%self.tui.TUI_getVariable('RADplotdatasize'))

            # Cas d'usage et modèle
            f.write(', "useCase": "%s"\n'%pUsecase)
            f.write(', "library": "%s"\n'%pBibliotheque)
            f.write(', "useCaseBase": "%s"\n'%self.repUseCaseBase)
            f.write(', "code": "%s"\n'%pModele)

            # Paramètres du modèle
    #        if self.modelParams[pUsecase] is not None and self.modelCle[pUsecase] is not None :
            if pUsecase in self.modelParams:
                modelParams = self.modelParams[pUsecase]
                cleUseCase = self.modelCle[pUsecase]
    #            f.write(', "useCase": "%s"\n'%pUsecase)
                f.write(', "useCaseModelParams": {\n')
                virgule = " "
                suffixe = ""
                for param in modelParams:
                    if len(param) > 3:
                        if len(param) == 5:
                            _, clef, _, dictionnaire, _ = param
                        else:
                            _, clef, _, dictionnaire = param
                        variable = "%s%s"%(cleUseCase, clef)
                        if "options" in dictionnaire:
                            options = dictionnaire["options"]
                            options.sort()
                            valeur = options[int(self.tui.TUI_getVariable(variable))]
                        else:
                            valeur = self.tui.TUI_getVariable(variable)
                        if "lien" in dictionnaire:
                            varlien, vallien = dictionnaire["lien"]
                            vallien = [str(x) for x in vallien]
                            valeurLien = str(self.tui.TUI_getVariable(varlien))
                            if valeurLien not in vallien:
                                valeur = None
                    else:
                        _, clef, _ = param
                        variable = "%s%s"%(cleUseCase, clef)
                        valeur = self.tui.TUI_getVariable(variable)
                    if valeur is not None:
                        suffixe += "_%s%s"%(clef, str(valeur))
                        f.write('        %s"%s": "%s"\n'%(virgule, clef, str(valeur)))
                        virgule = ', '
                f.write('        %s"suffixMethod": "%s"\n'%(virgule, suffixe.replace('.', '-')))
                f.write("        }\n")

            # Les données à traiter
            dataListMode = self.tui.TUI_getVariable('CBXdataListMode')
            f.write(', "dataListMode": %d\n'%dataListMode)
            dataListFichier = self.tui.TUI_getVariable('EDTdataListFichier')
            if dataListFichier == 0 and not os.path.exists(dataListFichier):
                colPrint("The file '%s' containing data list does not exists. Use 'dd:<file>' command."%dataListFichier, pType="Error")
                return None
            f.write(', "dataListFichier": "%s"\n'%self.tui.TUI_getVariable('EDTdataListFichier'))
            f.write(', "nbData": %s\n'%self.tui.TUI_getVariable('EDTnbData'))
            f.write(', "offset": %s\n'%self.tui.TUI_getVariable('EDToffset'))
            f.write(', "stepData": %s\n'%self.tui.TUI_getVariable('EDTstepData'))

            # La cmap à utiliser
            f.write(', "cmapListMode": %d\n'%self.tui.TUI_getVariable('CBXcmapListMode'))
            f.write(', "cmapListColor": "%s"\n'%self.tui.TUI_getVariable('EDTcmapListColor'))

            # controle des données
            f.write(', "controls": %d\n'%self.tui.TUI_getVariable('CKBcontrols'))

            # Récupération des paramètres du Full Report
            select = self.tui.TUI_getValeurParNom('ckbReports', 'SELECT')
            fullReport = [self.tui.TUI_getValeurParNom('ckbReports', 'OPTIONS', x) for x in select]
            f.write(', "fullReport":"%s"\n'%",".join(fullReport))
            f.write(', "nbColFullLatexMethod": %d\n'%self.tui.TUI_getVariable('SPBnbColFullLatexMethod'))
            f.write(', "nbColFullLatexMetric": %d\n'%self.tui.TUI_getVariable('SPBnbColFullLatexMetric'))
            if fullReport:
                if 'Explanations' in fullReport:
                    fullReportE = self.tui.TUI_getValeurParNom('fExplanations', 'OPTIONS', self.tui.TUI_getValeurParNom('fExplanations', 'SELECT'))
                    f.write(', "fullReportE":"%s"\n'%fullReportE)
                if 'Metrics' in fullReport:
                    #fullReportM = self.tui.TUI_getValeurParNom('fMetrics', 'OPTIONS', self.tui.TUI_getValeurParNom('fMetrics', 'SELECT'))
                    f.write(', "fullReportM":"metric"\n')

            # Méthode de la bibliothèque et ses paramètres
            if pBibliotheque not in self.pluginsXAI.dicoPlugins.keys():
                colPrint("The '%s' library is not one of the collected plugins (see list below). Check names..."%pBibliotheque, pType="Error")
                colPrint(', '.join(list(self.pluginsXAI.dicoPlugins.keys())), pType="Erreur")
                return None
            clefBibliotheque = self.pluginsXAI.dicoPlugins[pBibliotheque].clef
            bibMethode = self.pluginsXAI.dicoPlugins[pBibliotheque].methodes[pMethode]
            if len(bibMethode) == 2:
                clefMethode, methodeParams = bibMethode
            else:
                clefMethode, methodeParams, _ = bibMethode
            if methodeParams is None:
                methodeParams = []
            f.write(', "method": "%s"\n'%pMethode)
            f.write(', "%s": {\n'%pMethode)
            virgule = " "
            suffixe = ""
            for param in methodeParams:
                if len(param) > 3:
                    if len(param) == 5:
                        _, clef, _, dictionnaire, _ = param
                    else:
                        _, clef, _, dictionnaire = param
                    variable = "%s%s%s"%(clefBibliotheque, clefMethode, clef)
                    if "options" in dictionnaire:
                        options = dictionnaire["options"]
                        options.sort()
                        valeur = options[int(self.tui.TUI_getVariable(variable))]
                    else:
                        valeur = self.tui.TUI_getVariable(variable)
                    if "lien" in dictionnaire:
                        varlien, vallien = dictionnaire["lien"]
                        vallien = [str(x) for x in vallien]
                        valeurLien = str(self.tui.TUI_getVariable(varlien))
                        if valeurLien not in vallien:
                            valeur = None
                else:
                    _, clef, _ = param
                    variable = "%s%s%s"%(clefBibliotheque, clefMethode, clef)
                    valeur = self.tui.TUI_getVariable(variable)
                if valeur is not None:
                    suffixe += "_%s%s"%(clef, str(valeur))
                    f.write('        %s"%s": "%s"\n'%(virgule, clef, str(valeur)))
                    virgule = ', '
            f.write('        %s"suffixMethod": "%s"\n'%(virgule, suffixe.replace('.', '-')))
            f.write("        }\n")

            # Métrique de la bibliothèque et ses paramètres
            if self.pluginsXAI.dicoPlugins[pBibliotheque].metriques is not None and pMetrique is not None:
                bibMetrique = self.pluginsXAI.dicoPlugins[pBibliotheque].metriques[pMetrique]
                if len(bibMetrique) == 2:
                    clefMetrique, metriqueParams = bibMetrique
                elif len(bibMetrique) == 3:
                    clefMetrique, metriqueParams, _ = bibMetrique
                else:
                    clefMetrique, metriqueParams, _, _ = bibMetrique
                f.write(', "metric": "%s"\n'%pMetrique)
                f.write(', "%s": {\n'%pMetrique)
                virgule = " "
                suffixe = ""
                for param in metriqueParams:
                    if len(param) > 3:
                        if len(param) == 5:
                            _, clef, _, dictionnaire, _ = param
                        else:
                            _, clef, _, dictionnaire = param
                        variable = "%s%s%s"%(clefBibliotheque, clefMetrique, clef)
                        if "options" in dictionnaire:
                            options = dictionnaire["options"]
                            options.sort()
                            valeur = options[int(self.tui.TUI_getVariable(variable))]
                        else:
                            valeur = self.tui.TUI_getVariable(variable)
                        if "lien" in dictionnaire:
                            varlien, vallien = dictionnaire["lien"]
                            vallien = [str(x) for x in vallien]
                            valeurLien = str(self.tui.TUI_getVariable(varlien))
                            if valeurLien not in vallien:
                                valeur = None
                    else:
                        _, clef, _ = param
                        variable = "%s%s%s"%(clefBibliotheque, clefMetrique, clef)
                        valeur = self.tui.TUI_getVariable(variable)
                    if valeur is not None:
                        suffixe += "_%s%s"%(clef, str(valeur))
                        f.write('        %s"%s": "%s"\n'%(virgule, clef, str(valeur)))
                        virgule = ', '
                f.write("        }\n")
                f.write(', "suffixMetric": "%s"\n'%suffixe.replace('.', '-'))

                f.write(', "methods4metric": "%s"\n'%pMeth4metr)
                for methode in self.pluginsXAI.dicoPlugins[pBibliotheque].methodes:
                    bibMethode = self.pluginsXAI.dicoPlugins[pBibliotheque].methodes[methode]
                    if len(bibMethode) == 2:
                        clefMethode, methodeParams = bibMethode
                    else:
                        clefMethode, methodeParams, _ = bibMethode
                    if methode != pMethode:
                        f.write(', "%s": {\n'%methode)
                        virgule = " "
                        suffixe = ""
                        for param in methodeParams:
                            dictionnaire = None
                            aide = None
                            if len(param) == 5:
                                _, clef, _, dictionnaire, aide = param
                            elif len(param) == 4:
                                _, clef, _, descdico = param
                                if isinstance(descdico, str):
                                    aide = descdico
                                else:
                                    dictionnaire = descdico
                            else:
                                _, clef, _ = param

                            variable = "%s%s%s"%(clefBibliotheque, clefMethode, clef)
                            valeur = self.tui.TUI_getVariable(variable)
                            if dictionnaire is not None:
                                if "options" in dictionnaire:
                                    options = dictionnaire["options"]
                                    options.sort()
                                    valeur = options[int(self.tui.TUI_getVariable(variable))]
                                else:
                                    valeur = self.tui.TUI_getVariable(variable)
                                if "lien" in dictionnaire:
                                    varlien, vallien = dictionnaire["lien"]
                                    vallien = [str(x) for x in vallien]
                                    valeurLien = str(self.tui.TUI_getVariable(varlien))
                                    if valeurLien not in vallien:
                                        valeur = None
                            if valeur is not None:
                                suffixe += "_%s%s"%(clef, str(valeur))
                                f.write('        %s"%s": "%s"\n'%(virgule, clef, str(valeur)))
                                virgule = ', '
                        f.write('        %s"suffixMethod": "%s"\n'%(virgule, suffixe.replace('.', '-')))
                        f.write("        }\n")

            # Aides dans le json
            f.write(', "aides": {\n')
            for plugin in self.pluginsUCXAI.plugins:
                if plugin.nom == pUsecase and plugin.bibliotheque == pBibliotheque:
                    f.write('         "useCase": "%s"\n'%plugin.description)
            for cAide, vAide in self.aideMethodes.items():
                library = cAide.split(':')[0]
                methode = cAide.split(':')[1]
                clefLibrary = self.pluginsXAI.dicoPlugins[library].clef
                clefMethode = self.pluginsXAI.dicoPlugins[library].methodes[methode][0]
                f.write('        , "%s": ["%s%s", "%s"]\n'%(cAide, clefLibrary, clefMethode, vAide))
            for cAide, vAide in self.aideMetriques.items():
                library = cAide.split(':')[0]
                metrique = cAide.split(':')[1]
                clefLibrary = self.pluginsXAI.dicoPlugins[library].clef
                clefMetrique = self.pluginsXAI.dicoPlugins[library].metriques[metrique][0]
                f.write('        , "%s": ["%s%s", "%s"]\n'%(cAide, clefLibrary, clefMetrique, vAide))
            for param in self.listeParams:
                aide = "None"
                pparam = param.replace('.', '')
                if pparam in self.tui.TUI_getAides():
                    aide = self.tui.TUI_getAides()[pparam]
                f.write('        , "%s": "%s"\n'%(param, aide))
            f.write("        }\n")

            f.write("}\n")

        # lecture du json pour transmission
        with open(ficJson, 'r', encoding="utf-8") as fJson:
            dictParams = json.load(fJson)

        return dictParams

    # ---------------------------------------------------------------------------
    ## Methode de générique des actions 1, 2, 3, 4, 5 et combinaisons
    # @param pActions : liste des actions à lancer
    def fctXAI(self, pActions):
        colPrint("Launch actions %s"%pActions, pType="Action")

        # recuperation des cas d'usage, modele, bibliotheque methode et metrique
        casDusage, modele = self.casDusageModele()
        bibliotheque, methode, metrique, meth4metr = self.bibliothequeMethodeMetrique()

        # Constitution du log et données produites (répertoire et fichier)
        extensionProd = self.tui.TUI_getVariable('EDTextensionProd')
        repert = os.path.join(self.repResultProd, "logs", "%s-%s_%s_%s"%(casDusage, modele, bibliotheque, extensionProd))

        if not os.path.exists(repert):
            os.makedirs(repert)
        extensionLog = self.tui.TUI_getVariable('EDTextensionLog')
        if extensionLog == "":
            logdate = time.strftime("%d - %m - %Y - %H: %M: %S", time.localtime())
        else:
            logdate = extensionLog
        premAction = pActions.split('.')[0]
        if premAction == "FullReport":
            logFile = "%s_fullReport-%s.log"%(repert.replace('_%s'%bibliotheque, '').replace('_%s'%extensionProd, ''), logdate)
        elif premAction in ["Metric", "PlotM"]:
            logFile = os.path.join(repert, "%s-%s_Metric.log"%(metrique, logdate))
        else:
            logFile = os.path.join(repert, "%s-%s.log"%(methode, logdate))
        if self.tui.TUI_getVariable('CKBtrace'):
            colPrint(" - Log file : %s"%logFile)

        # création du dictionnaire des paramètres de configuration (Json)
        dictParams = self.kaaJson(extensionProd, casDusage, modele, bibliotheque, methode, metrique, meth4metr)
        if dictParams is None:
            return

        # Ajout des plugins dans le dictionnaire
        for plugin in self.pluginsUCXAI.plugins:
            if plugin.nom == casDusage and plugin.bibliotheque == bibliotheque:
                dictParams['pluginUCXAI'] = plugin
        for plugin in self.pluginsXAI.plugins:
            if plugin.nom == bibliotheque:
                dictParams['pluginXAI'] = plugin

        # Lancement des actions
        if self.tui.TUI_getVariable('CKBtrace') == 1:
            with open(logFile, 'w', encoding="utf-8") as f:
                with redirect_stderr(f), redirect_stdout(f):
                    # initialisation
                    dictParams = kaasrc.kaaActions.initialisation(dictParams, self.pluginsUCXAI.pluginsUCXAIdirectory)
                    # actions
                    for action in pActions.split('.'):
                        if action != "FullReport":
                            colPrint("Results saved on subpath: %s"%dictParams['repertProd'])
                        dictParams = kaasrc.kaaActions.launchAction(action, dictParams)
                    colPrint("Actions end normally.", pType="Action")
        else:
            # initialisation
            dictParams = kaasrc.kaaActions.initialisation(dictParams, self.pluginsUCXAI.pluginsUCXAIdirectory)
            # actions
            for action in pActions.split('.'):
                if action != "FullReport":
                    colPrint("Results saved on subpath: %s"%dictParams['repertProd'])
                dictParams = kaasrc.kaaActions.launchAction(action, dictParams)
            colPrint("Actions end normally.", pType="Action")
        del dictParams

    # ---------------------------------------------------------------------------
    ## Methode de l'action c
    # @param val : valeur potentielle
    def applic(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Choice of use case", pType="Select", pEcho=self.echo)
        self._debug("applic()", "MAJ modele du cas d'usage", val)
        self._debug("        ", self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS'))

        # Récupération de l'indice du cas d'usage courant si non fourni
        if val is None:
            val = self.tui.TUI_getValeurParNom('cbxCasUsage', 'SELECT')
        else:
            val = int(val)
            self.tui.TUI_setVariable('CBXcasdusage', val)
        # Cas d'usage sélectionné
        casDusage = self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS', val)
        colPrint("    Use case    : %s"%casDusage, pEcho=self.echo)

        # Mise à jour des modeles associés
        modeles = list(self.table[casDusage].keys())
        modeles.remove('plugin')
        modeles.sort()
        colPrint("    Associated models: %s"%', '.join(modeles), pEcho=self.echo)
        self.tui.TUI_setValeurParNom('cbxModele', 'OPTIONS', modeles)

        self.echo = False
        self.applico(val)
        self.applio("0")
        self.echo = True

    # ---------------------------------------------------------------------------
    ## Methode de l'action o
    # @param val : valeur potentielle
    def applio(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Choice of model", pType="Select", pEcho=self.echo)
        self._debug("applio()", "MAJ bibliothèques liées au modèle du cas d'usage", val)
        self._debug("        ", self.tui.TUI_getValeurParNom('cbxModele', 'OPTIONS'))

        # Cas d'usage sélectionné
        select = self.tui.TUI_getValeurParNom('cbxCasUsage', 'SELECT')
        casDusage = self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS', select)

        # Récupération de l'indice du modèle courant si non fourni
        if val is None:
            val = self.tui.TUI_getValeurParNom('cbxModele', 'SELECT')
        else:
            val = int(val)
            self.tui.TUI_setVariable('CBXmodele', val)
        # Modele sélectionné
        modele = self.tui.TUI_getValeurParNom('cbxModele', 'OPTIONS', val)
        colPrint("    Model   : %s"%modele, pEcho=self.echo)
        # MAJ datatype et modeltype
        fJson = os.path.join(self.pluginsUCXAI.pluginsUCXAIdirectory, casDusage, "%s.json"%casDusage)
        with open(fJson, 'r', encoding="utf-8") as fJson:
            jsonModeles = json.load(fJson)
        self.tui.TUI_setVariable("datatype", jsonModeles[modele]["datatype"])
        self.tui.TUI_setVariable("modeltype", jsonModeles[modele]["modeltype"])
        # Mise à jour des bibliothèques associées
        bibliotheques = list(self.table[casDusage][modele].keys())
        bibliotheques.sort()
        self.tui.TUI_setValeurParNom('cbxBibliotheque', 'OPTIONS', bibliotheques)
        self.tui.TUI_setValeurParNom('cbxModeData', 'SELECT', 0)
        self.echo = False
        self.applidm("0")
        self.applib("0")
        self.echo = True

    # ---------------------------------------------------------------------------
    ## Methode de l'action m
    # @param val : valeur potentielle
    def applidm(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Data selection mode", pType="Select", pEcho=self.echo)
        colPrint("    %s"%val, pEcho=self.echo)
        self.tui.TUI_setVariable('CBXdataListMode', int(val))
        self.tui.TUI_setValeurParNom('edtFichData', 'VISIBLE', int(val) == 0)

    # ---------------------------------------------------------------------------
    ## Methode de l'action dd
    # @param val : valeur potentielle
    def applidd(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Data file selection", pType="Select")
        colPrint("    %s"%val)
        self.tui.TUI_setVariable('EDTdataListFichier', val)
        if not os.path.exists(val):
            colPrint("File not found.", pType="Error")

    # ---------------------------------------------------------------------------
    ## Methode de l'action tcm
    # @param val : valeur potentielle
    def applitcm(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        self.tui.TUI_setVariable('CBXcmapListMode', int(val))
        self.tui.TUI_setValeurParNom('cbxCmap', 'VISIBLE', int(val) == 0)
        self.tui.TUI_setValeurParNom('edtColorData', 'VISIBLE', int(val) == 1)

    # ---------------------------------------------------------------------------
    ## Methode de l'action tcf
    # @param val : valeur potentielle
    def applitcf(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Colormap file selection", pType="Select")
        colPrint("    %s"%val)
        self.tui.TUI_setVariable('EDTcmapListColor', val)
        if not os.path.exists(val):
            colPrint("File not found.", pType="Error")

    # ---------------------------------------------------------------------------
    ## Methode de l'action b
    # @param val : valeur potentielle
    def applib(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Choice of explainability library", pType="Select", pEcho=self.echo)
        self._debug("applib()", "MAJ methode et metrique de la bibliotheque s/ cas d'usage", val)
        self._debug("        ", self.tui.TUI_getValeurParNom('cbxBibliotheque', 'OPTIONS'))

        # Cas d'usage et modèle sélectionnés
        casDusage, modele = self.casDusageModele()

        # Récupération de l'indice du modèle courant si non fourni
        if val is None:
            val = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'SELECT')
        else:
            val = int(val)
            self.tui.TUI_setVariable('CBXbibliotheque', val)
        # Bibilothèque sélectionnée
        select = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'SELECT')
        bibliotheque = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'OPTIONS', select)
        colPrint("    Library : %s"%bibliotheque, pEcho=self.echo)

        # Mise à jour des méthodes associées
        methodes = self.table[casDusage][modele][bibliotheque]['methodes']
        methodes.sort()
        #NEW methodes = ["%s:%s"%(bibliotheque, m) for m in methodes]
        lstMethodes = methodes

        aideMethodes = [self.aideMethodes["%s:%s"%(bibliotheque,m)] for m in lstMethodes]
        #print("DBG-aideMethodes>",len(aideMethodes),aideMethodes)
        aide = self.tui.TUI_getAideParNom('cbxMethode')
        #print("DBG-aide>",aide)
        aide[1] = aideMethodes
        self.tui.TUI_setAideParNom('cbxMethode', aide)
        strMethodes = ', '.join(methodes)
        strMethodes = strMethodes.replace('%s:'%bibliotheque, "")  # <== = ajouté
        colPrint("    Methods : %s"%strMethodes, pEcho=self.echo)
        self.tui.TUI_setValeurParNom('cbxMethode', 'OPTIONS', methodes)
        self.tui.TUI_setValeurParNom('cbxMethode', 'AIDE', aide)
        self.echo = False
        self.applih("0")
        self.echo = True

        # Mise à jour des métriques associées
        metriques = self.table[casDusage][modele][bibliotheque]['metriques']
        if metriques is None:
            self.echo = False
            self.applim("-1")
            self.echo = True
        else:
            metriques.sort()
            #metriques = ["%s:%s"%(bibliotheque, m) for m in metriques]
            lstMetriques = metriques
            aideMetriques = [self.aideMetriques["%s:%s"%(bibliotheque, m)] for m in lstMetriques]
            aide = self.tui.TUI_getAideParNom('cbxMetrique')
            aide[1] = aideMetriques
            self.tui.TUI_setAideParNom('cbxMetrique', aide)
            self.tui.TUI_setValeurParNom('cbxMetrique', 'OPTIONS', metriques)
            self.tui.TUI_setValeurParNom('cbxMetrique', 'AIDE', aide)
            self.echo = False
            self.applim("0")
            self.echo = True

    # ---------------------------------------------------------------------------
    ## Methode de l'action co
    # @param val : valeur potentielle
    def applico(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Choice of use case", pType="Select", pEcho=self.echo)
        self._debug("applico()", "MAJ paramètres du cas d'usage", val)
        self._debug("        ", self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS'))

        # On rend inactifs et invisibles l'ensemble des paramètres de toutes les cas d'usage
        for cGroupe, vGroupe in self.tui.TUI_getGroupes().items():
            self._debug("Desactivation du groupe '%s'."%cGroupe)
            if cGroupe.split('*')[0] == 'MODEL':
                for idObjets in vGroupe:
                    self.tui.TUI_setValeurParId(idObjets, 'VISIBLE', 0)
                    self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 0)
                    widget = self.tui.TUI_getWidgetParId(idObjets)
                    self._debug("        ", widget['NOM'])

        # Récupération de l'indice de la méthode courante si non fourni
        if val is None:
            val = self.tui.TUI_getValeurParNom('cbxCasUsage', 'SELECT')
        else:
            val = int(val)

        # Définition du groupe de paramètres correspondant à la méthode sélectionnée
        if len(self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS')) < val + 1:
            colPrint("Rectification of choice", pType="Warning", pEcho=self.echo)
            val = 0

        usecase = self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS', val)

        colPrint("    %s"%usecase, pEcho=self.echo)
        groupe = "MODEL*%s"%usecase
        # On rend actifs et visibles l'ensemble des paramètres du groupe
        if groupe not in self.tui.TUI_getGroupes():
            self._debug("Le groupe de paramètres '%s' n'est pas dans la liste suivante. Vérifier les correspondances de noms dans les plugins..."%groupe)
            self._debug(', '.join(list(self.tui.TUI_getGroupes().keys())))
        else:
            self._debug("Activation du groupe '%s'."%groupe)
            for idObjets in self.tui.TUI_getGroupes()[groupe]:
                self.tui.TUI_setValeurParId(idObjets, 'VISIBLE', 1)
                self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 1)
                widget = self.tui.TUI_getWidgetParId(idObjets)
                self._debug("        ", widget['NOM'])

                label = widget['TEXTE'].replace(' ', '')
                # on s'assure que le label soit dans le json
                if label in ['datatype', 'modeltype']:
                    # on desactive le widget
                    self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 0)
                    if label in self.tui.TUI_getVariables():
                        val = self.tui.TUI_getVariable(label)
                        self.tui.TUI_setValeurParId(idObjets, 'SELECT', widget['OPTIONS'].index(val))

    # ---------------------------------------------------------------------------
    ## Methode de l'action h
    # @param val : valeur potentielle
    def applih(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Choice of explainability method", pType="Select", pEcho=self.echo)
        self._debug("applih()", "MAJ paramètres de la methode de la bibliotheque s/ cas d'usage", val)
        self._debug("        ", self.tui.TUI_getValeurParNom('cbxMethode', 'OPTIONS'))

        # On rend inactifs et invisibles l'ensemble des paramètres de toutes les méthodes
        for cGroupe, vGroupe in self.tui.TUI_getGroupes().items():
            self._debug("Desactivation du groupe '%s'."%cGroupe)
            if cGroupe.split('*')[0] == 'METHODE':
                for idObjets in vGroupe:
                    self.tui.TUI_setValeurParId(idObjets, 'VISIBLE', 0)
                    self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 0)
                    widget = self.tui.TUI_getWidgetParId(idObjets)
                    self._debug("        ", widget['NOM'])

        # Récupération de l'indice de la méthode courante si non fourni
        if val is None:
            val = self.tui.TUI_getValeurParNom('cbxMethode', 'SELECT')
        else:
            val = int(val)
            self.tui.TUI_setVariable('CBXmethode', val)

        # Définition du groupe de paramètres correspondant à la méthode sélectionnée
        if len(self.tui.TUI_getValeurParNom('cbxMethode', 'OPTIONS')) < val + 1:
            colPrint("Rectification of choice", pType="Warning", pEcho=self.echo)
            val = 0
            self.tui.TUI_setVariable('CBXmethode', val)

        select = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'SELECT')
        bibliotheque = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'OPTIONS', select)
        methode = self.tui.TUI_getValeurParNom('cbxMethode', 'OPTIONS', val)
        colPrint("    %s"%methode, pEcho=self.echo)
        groupe = "METHODE*%s:%s"%(bibliotheque,methode)

        # On rend actifs et visibles l'ensemble des paramètres du groupe
        if groupe not in self.tui.TUI_getGroupes():
            self._debug("Le groupe de paramètres '%s' n'est pas dans la liste suivante. Vérifier les correspondances de noms dans les plugins..."%groupe)
            self._debug(', '.join(list(self.tui.TUI_getGroupes().keys())))
        else:
            self._debug("Activation du groupe '%s'."%groupe)
            for idObjets in self.tui.TUI_getGroupes()[groupe]:
                self.tui.TUI_setValeurParId(idObjets, 'VISIBLE', 1)
                self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 1)
                widget = self.tui.TUI_getWidgetParId(idObjets)
                self._debug("        ", widget['NOM'])

                label = widget['TEXTE'].replace(' ', '')
                # on s'assure que le label soit dans le json
                if label in ['datatype', 'modeltype']:
                    # on desactive le widget
                    self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 0)
                    if label in self.tui.TUI_getVariables():
                        val = self.tui.TUI_getVariable(label)
                        self.tui.TUI_setValeurParId(idObjets, 'SELECT', widget['OPTIONS'].index(val))

    # ---------------------------------------------------------------------------
    ## Methode de l'action m
    # @param val : valeur potentielle
    def applim(self, val=None):
        if val == "--PAS_DE_VALEUR--":
            return
        colPrint("Choice of explainability metric", pType="Select", pEcho=self.echo)
        self._debug("applim()", "MAJ paramètres de la métrique de la bibliotheque s/ cas d'usage", val)
        self._debug("        ", self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS'))

        # On rend inactifs et invisibles l'ensemble des paramètres de toutes les métriques applicables
        for cGroupe, vGroupe in self.tui.TUI_getGroupes().items():
            if cGroupe.split('*')[0] == 'METRIQUE':
                for idObjets in vGroupe:
                    self.tui.TUI_setValeurParId(idObjets, 'VISIBLE', 0)
                    self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 0)

        # Récupération de l'indice de la métrique courante si non fourni
        if val is None:
            val = self.tui.TUI_getValeurParNom('cbxMetrique', 'SELECT')
        else:
            val = int(val)
            self.tui.TUI_setVariable('CBXmetrique', val)
            if val == -1:
                self.tui.TUI_setValeurParNom('cbxMetrique', 'OPTIONS', '')
                self.tui.TUI_setValeurParNom('cbxMetrique', 'SELECT', -1)

        # Définition du groupe de paramètres correspondant à la métrique sélectionnée
        if len(self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS')) < val + 1:
            colPrint("Rectification of choice", pType="Warning", pEcho=self.echo)
            val = 0
            self.tui.TUI_setVariable('CBXmetrique', val)

        if len(self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS')) > 0:
            metrique = self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS', val)
            select = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'SELECT')
            bibliotheque = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'OPTIONS', select)
            colPrint("   %s"%metrique, pEcho=self.echo)
            groupe = "METRIQUE*%s:%s"%(bibliotheque,metrique)

            # On rend actifs et visibles l'ensemble des paramètres du groupe
            if groupe in self.tui.TUI_getGroupes():
                for idObjets in self.tui.TUI_getGroupes()[groupe]:
                    self.tui.TUI_setValeurParId(idObjets, 'VISIBLE', 1)
                    self.tui.TUI_setValeurParId(idObjets, 'ACTIF', 1)

            # Liste des méthodes pour la métrique
            select = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'SELECT')
            bibliotheque = self.tui.TUI_getValeurParNom('cbxBibliotheque', 'OPTIONS', select)
            methodes = []
            tailleMax = 0
            if bibliotheque in self.pluginsXAI.dicoPlugins:
                bibMetrique = self.pluginsXAI.dicoPlugins[bibliotheque].metriques[metrique]
                if len(bibMetrique) == 2:
                    listeMethodes = None
                elif len(bibMetrique) == 4:
                    listeMethodes = None
                    _, _, listeMethodes, _ = bibMetrique
                else:
                    _, _, listeMethodes = bibMetrique
                    if isinstance(listeMethodes, str):
                        listeMethodes = None
                for methode in self.tui.TUI_getValeurParNom('cbxMethode', 'OPTIONS'):
                    if (listeMethodes is None or (listeMethodes is not None and methode in listeMethodes)):
                        methodes.append(methode)
                        tailleMax = max(tailleMax, len(methode))
            methodes.sort()
        else:
            methodes = []
            tailleMax = 0
            self.tui.TUI_setVariable("metrique", -1)
            colPrint("     - No metric - ", pEcho=self.echo)

        self.tui.TUI_setValeurParNom('ckbMetrique', 'OPTIONS', methodes)
        self.tui.TUI_setValeurParNom('ckbMetrique', 'LARG', tailleMax + 2)
        self.tui.TUI_setVariable("metriquesOn", [])
        self.tui.TUI_setValeurParNom('ckbMetrique', 'SELECT', [])

    # ---------------------------------------------------------------------------
    ## Methode de l'action 1
    # @param val : valeur potentielle
    def applil(self, val=None):
        lstCommandes = ["Inference", "Explain", "PlotE", "Metric", "PlotM", "Report", "FullReport"]
        lstActions = self.tui.TUI_getValeurParNom('ckbActions', 'SELECT')
        if len(lstActions)==0:
            colPrint("     - No action selected - ", pType="Error")
        selection = [lstCommandes[int(x)] for x in lstActions]
        self.fctXAI('.'.join(selection))

    # ---------------------------------------------------------------------------
    ## Methode de l'action a
    # @param val : valeur potentielle
    def applia(self, val=None):
        lstActions = self.tui.TUI_getValeurParNom('ckbActions', 'SELECT')
        if 5 in lstActions:
            self.tui.TUI_setVariable("CKBlegender", 0)
            self.tui.TUI_setVariable("RADplotdatasize", 0)
            print(" Force Visualisation with legend (tl:0) and in model size (tw:0).")

    # ---------------------------------------------------------------------------
    ## Methode de l'action Z
    # @param val : valeur potentielle
    def appliZ(self, val=None):
        extensionProd = self.tui.TUI_getVariable('EDTextensionProd')
        casDusage, modele = self.casDusageModele()
        bibliotheque, _, _, _ = self.bibliothequeMethodeMetrique()
        repert = os.path.join(self.repResultProd, "logs", "%s-%s_%s_%s"%(casDusage, modele, bibliotheque, extensionProd))
        colPrint("Directory removing %s"%repert, pType="Action")
        if os.path.exists(repert):
            shutil.rmtree(repert)

    # ---------------------------------------------------------------------------
    ## Methode de l'action V
    # @param val : valeur potentielle
    def appliV(self, val=None):
        self.tui.TUI_SauvegardeConfig()

    # ---------------------------------------------------------------------------
    ## Methode d'initialisation de la TUI
    def initialiseIHM(self):
        self.tui.TUI_ChargeConfig()
        casDusage = self.tui.TUI_getVariable('CBXcasdusage')
        modele = self.tui.TUI_getVariable('CBXmodele')
        bibliotheque = self.tui.TUI_getVariable('CBXbibliotheque')
        methode = self.tui.TUI_getVariable('CBXmethode')
        metrique = self.tui.TUI_getVariable('CBXmetrique')
        dataListMode = self.tui.TUI_getVariable('CBXdataListMode')
        cmapListMode = self.tui.TUI_getVariable('CBXcmapListMode')

        # Mise en place du cas d'usage
        if not -1 < casDusage < len(self.tui.TUI_getValeurParNom('cbxCasUsage', 'OPTIONS')):
            self.tui.TUI_setVariable('CBXcasdusage', 0)
            casDusage = 0
        self.echo = False
        self.applic(casDusage)     # mise en place du cas d'usage
        self.echo = True
        # Mise en place du modèle
#        l = self.tui.TUI_getValeurParNom('cbxModele', 'OPTIONS')
        if not -1 < modele < len(self.tui.TUI_getValeurParNom('cbxModele', 'OPTIONS')):
            self.tui.TUI_setVariable('CBXmodele', 0)
            modele = 0
        self.echo = False
        self.applio(modele)         # mise en place de la modele
        self.applico(casDusage)     # mise en place des paramètres du cas d'usage
        self.echo = True
        # Mise en place de la bibliothèque
        if not -1 < bibliotheque < len(self.tui.TUI_getValeurParNom('cbxBibliotheque', 'OPTIONS')):
            self.tui.TUI_setVariable('CBXbibliotheque', 0)
            bibliotheque = 0
        self.echo = False
        self.applib(bibliotheque)   # mise en place de la bibliotheque
        self.echo = True
        # Mise en place de la méthode
        if not -1 < methode < len(self.tui.TUI_getValeurParNom('cbxMethode', 'OPTIONS')):
            self.tui.TUI_setVariable('CBXmethode', 0)
            methode = 0
        self.echo = False
        self.applih(methode)        # mise en place des paramètres de la méthode sélectionnée
        self.echo = True
        # Mise en place de la métrique
        if not -1 < metrique < len(self.tui.TUI_getValeurParNom('cbxMetrique', 'OPTIONS')):
            self.tui.TUI_setVariable('CBXmetrique', 0)
            metrique = 0
        self.echo = False

        self.applim(metrique)        # mise en place des paramètres de la métrique sélectionnée
        self.applidm(dataListMode)   # mise en place des éléments du mode de sélection
        self.applitcm(cmapListMode)  # mise en place de la colormap
        self.echo = True

        self.tui.fonctGCB(self.tui.TUI_getWidgetParNom('ckbActions'), self.tui.TUI_getVariable('GCBactions'), force=True)
        self.tui.fonctGCB(self.tui.TUI_getWidgetParNom('ckbMetrique'), self.tui.TUI_getVariable('GCBmetriquesOn'), force=True)
        self.tui.TUI_setVariable('CKBtrace', 0)
        self.tui.TUI_setVariable('EDTextensionProd', "Test")
        self.tui.TUI_setVariable('EDTextensionLog', "")
        self.tui.TUI_setVariable('CKBlegender', 0)
        self.tui.TUI_setVariable('CKBnormalise', 1)
        self.tui.TUI_setVariable('CKBcontrols', 0)

# -------------------------------------------------------------------------------
def TUI(pPluginsXAI, pPluginsUCXAI, pRepResultProd, pRepUseCaseBase, pFichierCommandes, pDebug):

    # Création du menu TUI
    menu = MenuTUI(pPluginsXAI, pPluginsUCXAI, pRepResultProd, pRepUseCaseBase, pDebug)

    # Lancement menu TUI
    kaasrc.mpTUI.TUI_boucle(menu,pInitialisationTUI=menu.initialiseIHM,pFichierCommandes=pFichierCommandes)

# ===============================================================================
# end of file
