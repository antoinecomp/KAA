#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Text-based User Interface : Ph Dejean 09.2018
# from https://framagit.org/PhDejean/mp_TUI
# ===============================================================================
#
# ------------------------------------------------
#  Chargement de l'environnement
# ------------------------------------------------
import json, os, copy

CLAVIER = False
TUIVERSION = "25.04"

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
    fBlack    = colorama.Fore.BLACK

    fLBlack    = colorama.Fore.LIGHTBLACK_EX
    fLBlue     = colorama.Fore.LIGHTBLUE_EX
    fLCyan     = colorama.Fore.LIGHTCYAN_EX
    fLGreen    = colorama.Fore.LIGHTGREEN_EX
    fLMagenta  = colorama.Fore.LIGHTMAGENTA_EX
    fLRed      = colorama.Fore.LIGHTRED_EX
    fLWhite    = colorama.Fore.LIGHTWHITE_EX
    fLYellow   = colorama.Fore.LIGHTYELLOW_EX

    bRed      = colorama.Back.RED
    bGreen    = colorama.Back.GREEN
    bYellow   = colorama.Back.YELLOW
    bWhite    = colorama.Back.WHITE
    bBlue     = colorama.Back.BLUE
    bMagenta  = colorama.Back.MAGENTA
    bCyan     = colorama.Back.CYAN
    bBlack    = colorama.Back.BLACK

    bLBlack    = colorama.Back.LIGHTBLACK_EX
    bLBlue     = colorama.Back.LIGHTBLUE_EX
    bLCyan     = colorama.Back.LIGHTCYAN_EX
    bLGreen    = colorama.Back.LIGHTGREEN_EX
    bLMagenta  = colorama.Back.LIGHTMAGENTA_EX
    bLRed      = colorama.Back.LIGHTRED_EX
    bLWhite    = colorama.Back.LIGHTWHITE_EX
    bLYellow   = colorama.Back.LIGHTYELLOW_EX

    sBright   = colorama.Style.BRIGHT
    sDim      = colorama.Style.DIM
    sNormal   = colorama.Style.NORMAL
    sReset    = colorama.Style.RESET_ALL
else:
    fRed      = ""
    fGreen    = ""
    fYellow   = ""
    fWhite    = ""
    fBlue     = ""
    fMagenta  = ""
    fCyan     = ""
    fBlack    = ""

    fLBlack    = ""
    fLBlue     = ""
    fLCyan     = ""
    fLGreen    = ""
    fLMagenta  = ""
    fLRed      = ""
    fLWhite    = ""
    fLYellow   = ""

    bRed      = ""
    bGreen    = ""
    bYellow   = ""
    bWhite    = ""
    bBlue     = ""
    bMagenta  = ""
    bCyan     = ""
    bBlack    = ""

    bLBlack    = ""
    bLBlue     = ""
    bLCyan     = ""
    bLGreen    = ""
    bLMagenta  = ""
    bLRed      = ""
    bLWhite    = ""
    bLYellow   = ""

    sBright   = ""
    sDim      = ""
    sNormal   = ""
    sReset    = ""

version = 1.0

# ---------------------------------------------------------------------------------
## Test if the value n is a float string
# @param n : value
# @return true or false
def isDigit(n):
    try:
        float(n)
        return True
    except ValueError:
        return False

# ---------------------------------------------------------------------------------
## Class TUI: Text User Interface
class TUI:
    # ---------------------------------------------------------------------------
    ## Fonction d'initialisation de la classe
    # @param pTUI : déclaration de l'interface
    # @param pDebug : niveau de debug
    def __init__(self, pTUI, pDebug):
        self.debug = pDebug
        self.appliTUI = pTUI
        largeurTUI = pTUI['LARGEUR']
        self.hauteur = pTUI['HAUTEUR']
        self.marge = 2*pTUI['MARGE']
        self.blocs = {}
        self.palette = {}
        self.TUI_fixePalette(pTUI['PALETTE'])
        self.cmdLatest = ""
        if isinstance(largeurTUI,int):
            self.espaceInterieur = largeurTUI
            self.largeur = self.espaceInterieur+self.marge+2 # 2:bordure
        else:
            largeurTUI.append(0)
            self.espaceInterieur = -self.marge # la double marge du dernier séparateur est à supprimer
            self.largeur = 2 # bordure
            nbBlocs = len(largeurTUI)//2
            for i in range(nbBlocs):
                bordGh = i==0
                bordDt = i==nbBlocs-1
                largeur = largeurTUI[i*2]
                if isinstance(largeurTUI[i*2+1],int):
                    tailleSep = largeurTUI[i*2+1]
                    coulSep = self.palette['Separateur']
                    #print("DBG>",coulSep,(bBlack,  fLRed, sBright))
                else:
                    tailleSep,coulSep = largeurTUI[i*2+1]
                self.blocs[i+1] = (largeur,tailleSep,bordGh,bordDt,coulSep)
                self.espaceInterieur += largeur+tailleSep+self.marge
                self.largeur += largeur+tailleSep+self.marge
        self.blocs[0] = (self.espaceInterieur,0,True,True,self.palette['Separateur'])
        #print("DBG-largeur>",self.espaceInterieur,self.largeur)
        self.actions = {}
        self.actionWidget = {}
        self.aides = {}
        self.widgets = {}       # [id] = element
        self.groupes = {}       # [nomGroupe] = [id, ...]
        self.table = {}         # [ligne] = [id, ...]
        self.maxLignes = 0
        self.indexWidgets = {}  # [nom] = (ligne, colonne)
        self.tableDesBlocs = {}
        self.version = pTUI['VERSION']
        self.listeCommandes = []
        self.affichageTUI = True
        self.enregistrement = False
        self.fichierEnregistrement = None
        self.quitter = pTUI['QUITTER']
        self.fichierConfiguration = pTUI['CONFIGURATION']
        numObjet = 0
        numId = 0
        listeTab = []
        listeNoms = []
        stop = False
        # Boucle sur les lignes d'elements
        for ligne, _ in enumerate(self.appliTUI['ELEMENTS']):
            ligneElement = []
            # Pour chaque ligne de l'UI, boucle sur les elements
            for numElem, _ in enumerate(self.appliTUI['ELEMENTS'][ligne]):
                element = copy.deepcopy(self.appliTUI['ELEMENTS'][ligne][numElem])
                element['ID'] = numId
                if isinstance(largeurTUI,int):
                    element['COLON'] = None
                element['OFFSETDEPL'] = 0
                numId += 1
                # gestion des zones retractables
                element['SPLDEP'] = True
                element['SPLTAG'] = None
                if 'SPL' in element:
                    element['SPL'] = str(element['SPL']).split('.')
                    element['SPLTAG'] = True
                # gestion des onglets
                if element['TYPE'] == 'SPL':
                    element['SELECT'] = 0
                if element['TYPE'] == 'TAB':
                    listeTab.append(element)
                element['TABVIS'] = True
                if 'COLON' not in element:
                    element['COLON']=0
                if 'TAB' in element:
                    element['TAB'] = [int(x) for x in str(element['TAB']).split('.')]
                # On valide l'activité
                if 'ACTIF' not in element:
                    element['ACTIF'] = True
                # On configure des éléments manquants
                if element['TYPE'] == 'SPB' and 'INTERVALLE' not in element:
                    element['INTERVALLE'] = (0, 100, 1, 10)
                if element['TYPE'] == 'CBX':
                    element['DEPLOIE'] = False
                if 'MODIFIABLE' not in element:
                    element['MODIFIABLE'] = False
#                if element['TYPE'] in ['CBX', 'LST']:
#                    if 'MODIFIABLE' not in element:
#                        element['MODIFIABLE'] = False
                if element['TYPE'] == 'ZED':
                    if 'HAUT' not in element:
                        element['HAUT'] = 0
                    if 'SCROLL' not in element:
                        element['SCROLL'] = -1
                    self.TUI_setValeurObjet(element,'SELECT',element['SELECT']) # pour mise en forme
#                if element['TYPE'] == 'SEP':
#                    if 'LARG' not in element:
#                        element['LARG'] = self.espace
                if 'ACTION' not in element:
                    element['ACTION'] = None
                if 'LARG' not in element:
                    element['LARG'] = 0
                if 'TEXTE' not in element:
                    element['TEXTE'] = ""
                # Si l'alignement n'est pas défini : Gauche
                if 'ALIGN' not in element:
                    if element['TYPE'] in ["EDT", "SPB", "SLD", "GCB", "RAD"]:
                        element['ALIGN'] = 'D'
                    elif element['TYPE'] in ["BTN"]:
                        element['ALIGN'] = 'C'
                    else:
                        element['ALIGN'] = 'G'
                if 'OFFSET' not in element:
                    element['OFFSET'] = 0
                if 'DECAL' not in element:
                    element['DECAL']=0
                # traitement du nom déclaré
                if 'NOM' not in element:
                    if element['ACTION'] is not None:
                        element['NOM'] = "%s%s"%(element['TYPE'], element['ACTION'])
                    else:
                        element['NOM'] = "tuiOBJET%d"%numObjet
                        numObjet += 1
                if element['NOM'] not in listeNoms:
                    listeNoms.append(element['NOM'])
                else:
                    self._print("/!\\ Doublon de nom pour '%s' !"%element['NOM'], "Error")
                    stop=True

                # traitement de l'action déclarée
                if 'ACTION' in element:
                    if element['ACTION'] is not None:
                        if element['ACTION'] in self.actions and self.actions[element['ACTION']] != element['NOM']:
                            self._print("/!\\ Doublon d'action '%s' pour '%s' !"%(element['ACTION'], element['NOM']), "Error")
                            stop=True
                        else:
                            self.actions[element['ACTION']] = element['NOM']
                            if 'AIDE' not in element:
                                element['AIDE'] = "Sorry no description available for this item."
                            self.aides[element['ACTION']] = element['AIDE']
                    self.actionWidget[element['ACTION']] = element['ID']
                self.indexWidgets[element['NOM']] = element['ID']
                # traitement de la visibilité du widget
                if 'VISIBLE' not in element:
                    element['VISIBLE'] = True
                    if element['TYPE']=='TAB':
                        element['VISIBLE']=[True for e in range(len(element['OPTIONS']))]
                if 'CONDVIS' in element:
                    condAct, condVal = element['CONDVIS']
                    condVal = [str(x) for x in condVal]
                    element['CONDVIS'] = (condAct, condVal)
                # Groupes
                if 'GROUP' in element:
                    if element['GROUP'] not in self.groupes:
                        self.groupes[element['GROUP']] = [element['ID']]
                    else:
                        self.groupes[element['GROUP']].append(element['ID'])
                # enregistrement du widget dans la ligne
                ligneElement.append(element)
            # Sauvegarde...
            self.table[self.maxLignes] = []
            self.maxLignes += 1
            for element in ligneElement:
                self.widgets[element['ID']] = element
                self.table[self.maxLignes - 1].append(element['ID'])
        for objetTab in listeTab:
            self.fonctTAB(objetTab, "--PAS_DE_VALEUR--")
        if stop:
            exit()

        self._print("To see hidden commands, press '!'.", )

    # ---------------------------------------------------------------------------------
    ## Print a colored message
    # @param pMessage : message to print
    # @param pType : message type to define color
    def _print(self, pMessage, pType="Normal"):
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
            print(fLBlack + pMessage, flush=True)
        elif pType == "Info":
            print(fYellow + sBright + pMessage, flush=True)
        else:
            print(fRed, "type '%s' inconnu, message '%s'"%(pType, pMessage), flush=True)

    # ---------------------------------------------------------------------------
    ## Chargement du fichier de commandes
    # @param pFichierCommandes : fichier de commandes
    def TUI_ChargerCommandes(self, pFichierCommandes):
        if not os.path.exists(pFichierCommandes):
            self._print("The command file '%s' does not exist."%pFichierCommandes, "Error")
            return
        with open(pFichierCommandes, 'r', encoding="utf-8") as f:
            commandes = f.readlines()
        self.listeCommandes = []
        for ligne in commandes:
            if ligne[0] != ';':
                # retrait des commentaires ;; blabla
                ligne = ligne.split(';;')[0]
                ligne = ligne.replace('\n', '').split(' ')
                for cmd in ligne:
                    self.listeCommandes.append(cmd)
        self.affichageTUI = False

    # ---------------------------------------------------------------------------------
    ## Extraction d'une commande
    def TUI_ExtraitCommande(self):
        return self.listeCommandes.pop(0).split(':')

    # ---------------------------------------------------------------------------------
    ## Chargement du fichier de configuration
    def TUI_ChargeConfig(self):
        if self.fichierConfiguration is None:
            return
        if not os.path.exists(self.fichierConfiguration):
            return
        with open(self.fichierConfiguration, 'r', encoding="utf-8") as f:
            dictConfig = json.load(f)

        self.appliTUI['VARIABLES'] = dictConfig['VARIABLES']

        for cNom, vNom in self.indexWidgets.items():
            for champ in ['VISIBLE', 'ACTIF', 'SPLDEP', 'SPLTAG', 'SELECT', 'TABVIS']:
                if cNom in dictConfig["WIDGETS"] and champ in dictConfig["WIDGETS"][cNom]:
                    self.widgets[vNom][champ] = dictConfig["WIDGETS"][cNom][champ]

    # ---------------------------------------------------------------------------------
    ## Sauvegarde du fichier de configuration
    def TUI_SauvegardeConfig(self):
        if self.fichierConfiguration is None:
            return
        dictConfig = {'VARIABLES':self.appliTUI['VARIABLES'],
                      "WIDGETS":{}}

        for cNom, vNom in self.indexWidgets.items():
            objet = self.widgets[vNom]
            dictConfig["WIDGETS"][cNom] = {}
            for champ in ['VISIBLE', 'ACTIF', 'SPLDEP', 'SPLTAG', 'SELECT', 'TABVIS']:
                if champ in objet:
                    dictConfig["WIDGETS"][cNom][champ] = objet[champ]

        with open(self.fichierConfiguration, 'w', encoding="utf-8") as f:
            json.dump(dictConfig, f, indent=4)
        with open(os.path.splitext(self.fichierConfiguration)[0]+'.pal', 'w', encoding="utf-8") as f:
            json.dump(self.palette, f, indent=4)

    # ---------------------------------------------------------------------------------
    ## Remplacement des valeurs de variable dans un élément
    # @param elem : élément de base pour la substitution
    # @return elem : élément modifié
    def _remplaceVariable(self, elem):
        if isinstance(elem, int):
            return elem
        if isinstance(elem, list):
            for i, _ in enumerate(elem):
                elem[i] = self._remplaceVariable(elem[i])
        else:
            for var in self.appliTUI['VARIABLES'].keys():
                rVar = "@%s@"%var
                # print("var:", var)
                elem = elem.replace(rVar, str(self.appliTUI['VARIABLES'][var]))
        return elem

    # ---------------------------------------------------------------------------------
    ## Affectation d'une valeur à une variable
    # @param variable : nom de la variable
    # @param valeur : valeur de la variable
    def TUI_setVariable(self, pVariable, pValeur):
        self.appliTUI['VARIABLES'][pVariable] = pValeur

    # ---------------------------------------------------------------------------------
    ## Décupération de la une valeur d'une variable
    # @param variable : nom de la variable
    # @return valeur
    def TUI_getVariable(self, pVariable):
        return self.appliTUI['VARIABLES'][pVariable]

    # ---------------------------------------------------------------------------------
    def TUI_nomCouleur(self,pFond,pTexte,pStyle):
        dicoCouleurs = {fRed:"fRed",fGreen:"fGreen",fYellow:"fYellow",fWhite:"fWhite",fBlue:"fBlue",fMagenta:"fMagenta",fCyan:"fCyan",fBlack:"fBlack",
                        fLBlack:"fLBlack",fLBlue:"fLBlue",fLCyan:"fLCyan",fLGreen:"fLGreen",fLMagenta:"fLMagenta",fLRed:"fLRed",fLWhite:"fLWhite",fLYellow:"fLYellow",
                        bRed:"bRed",bGreen:"bGreen",bYellow:"bYellow",bWhite:"bWhite",bBlue:"bBlue",bMagenta:"bMagenta",bCyan:"bCyan",bBlack:"bBlack",
                        bLBlack:"bLBlack",bLBlue:"bLBlue",bLCyan:"bLCyan",bLGreen:"bLGreen",bLMagenta:"bLMagenta",bLRed:"bLRed",bLWhite:"bLWhite",bLYellow:"bLYellow",
                        sBright:"sBright",sDim:"sDim",sNormal:"sNormal",sReset:"sReset"}
        return "%s,%s,%s"%(dicoCouleurs[pFond],dicoCouleurs[pTexte],dicoCouleurs[pStyle])

    # ---------------------------------------------------------------------------------
    def _getCouleur(self,pCouleur):
        if isinstance(pCouleur, str):
            if pCouleur in self.palette:
                return self.palette[pCouleur]
            else:
                return self._couleurPerso(pCouleur)
        return pCouleur

    # ---------------------------------------------------------------------------------
    ## Définition de la palette de couleurs
    # @param nom : nom de la palette
    def TUI_fixePalette(self, nom="EXPLAIN"):
        if nom is None:
            self.palette = {'Titre'      : None,
                            'Action'     : None,
                            'Bordure'    : None,
                            'Separateur' : None,
                            'Normal'     : None,
                            'Onglet'     : None,
                            'OngletOff'  : None,
                            'Bouton'     : None,
                            'Editeur'    : None,
                            'Options'    : None,
                            'Decorateur' : None,
                            'Selecteur'  : None,
                            'Alerte'     : None}
        elif nom in ['defaut', 'NoirBlanc']:
            self.palette = {'Titre'      : (bLWhite, fBlack,  sNormal),
                            'Action'     : (bWhite,  fLBlack, sNormal),
                            'Bordure'    : (bLWhite, fWhite,  sNormal),
                            "Separateur" : (bLWhite, fLBlack, sBright),
                            'Normal'     : (bLWhite, fBlack,  sNormal),
                            'Onglet'     : (bLWhite, fBlack,  sNormal),
                            'OngletOff'  : (bWhite,  fLBlack, sNormal),
                            "Bouton"     : (bLBlack, fBlack,  sNormal),
                            'Editeur'    : (bWhite,  fBlack,  sNormal),
                            'Options'    : (bLBlack, fWhite,  sNormal),
                            'Decorateur' : (bWhite,  fLBlack, sNormal),
                            "Selecteur"  : (bWhite,  fBlack,  sNormal),
                            'Alerte'     : (bLRed,   fYellow, sBright)}
        elif nom == 'Jaune':
            self.palette = {'Titre'      : (bYellow, fBlack,   sBright),
                            'Action'     : (bBlack,  fLYellow, sBright),
                            'Bordure'    : (bYellow, fBlack,   sDim),
                            "Separateur" : (bBlack,  fLYellow, sBright),
                            'Normal'     : (bBlack,  fYellow,  sNormal),
                            'Onglet'     : (bYellow, fBlack,   sNormal),
                            'OngletOff'  : (bBlack,  fLBlack,  sDim),
                            "Bouton"     : (bYellow, fBlack,   sNormal),
                            'Editeur'    : (bYellow, fBlack,   sNormal),
                            'Options'    : (bYellow, fBlack,   sNormal),
                            'Decorateur' : (bYellow, fBlack,   sNormal),
                            "Selecteur"  : (bYellow, fBlack,   sBright),
                            'Alerte'     : (bRed,    fBlack,   sNormal), }
        elif nom == 'Bleu':
            self.palette = {'Titre'      : (bBlue,  fBlack,  sBright),
                            'Action'     : (bBlack, fLBlue,  sBright),
                            'Bordure'    : (bBlue,  fBlack,  sDim),
                            "Separateur" : (bBlack, fLRed,   sBright),
                            'Normal'     : (bBlack, fBlue,   sNormal),
                            'Onglet'     : (bBlue,  fBlack,  sNormal),
                            'OngletOff'  : (bBlack, fLBlack, sDim),
                            "Bouton"     : (bBlue,  fBlack,  sNormal),
                            'Editeur'    : (bBlue,  fBlack,  sNormal),
                            'Options'    : (bBlue,  fBlack,  sNormal),
                            'Decorateur' : (bBlue,  fBlack,  sNormal),
                            "Selecteur"  : (bBlue,  fBlack,  sBright),
                            'Alerte'     : (bRed,   fBlack,  sNormal), }
        elif nom == "BleuJaune":
            self.palette = {"Titre"      : (bBlack, fYellow,  sBright),
                            "Action"     : (bBlack, fYellow,  sBright),
                            "Bordure"    : (bBlack, fYellow,  sDim),
                            "Separateur" : (bBlack, fLYellow, sBright),
                            "Normal"     : (bBlack, fWhite,   sDim),
                            "Onglet"     : (bBlack, fYellow,  sBright),
                            "OngletOff"  : (bBlack, fLBlack,  sDim),
                            "Bouton"     : (bBlue,  fYellow,  sNormal),
                            "Editeur"    : (bBlue,  fWhite,   sBright),
                            "Decorateur" : (bBlue,  fYellow,  sNormal),
                            "Selecteur"  : (bBlue,  fYellow,  sBright),
                            "Options"    : (bBlue,  fCyan,    sBright),
                            'Alerte'     : (bRed,   fBlack,   sNormal), }
        elif nom == 'JauneGris':
            self.palette = {"Titre"      : (bBlack,  fYellow,  sBright),
                            "Action"     : (bBlack,  fYellow,  sBright),
                            "Bordure"    : (bBlack,  fYellow,  sDim),
                            "Separateur" : (bBlack,  fLYellow, sBright),
                            "Normal"     : (bBlack,  fWhite ,  sDim),
                            "Onglet"     : (bBlack,  fYellow,  sBright),
                            "OngletOff"  : (bBlack,  fWhite,   sDim),
                            "Bouton"     : (bLBlack, fYellow,  sBright),
                            "Editeur"    : (bLBlack, fYellow,  sBright),
                            "Decorateur" : (bLBlack, fYellow,  sBright),
                            "Selecteur"  : (bLBlack, fYellow,  sBright),
                            "Options"    : (bLBlack, fYellow,  sBright),
                            'Alerte'     : (bRed,    fBlack,   sNormal), }
        elif nom == 'VertGris':
            self.palette = {"Titre"      : (bBlack,  fLGreen,  sBright),
                            "Action"     : (bBlack,  fGreen,   sNormal),
                            "Bordure"    : (bBlack,  fLGreen,  sDim),
                            "Separateur" : (bBlack,  fLYellow, sBright),
                            "Normal"     : (bBlack,  fWhite ,  sNormal),
                            "Onglet"     : (bBlack,  fLYellow, sBright),
                            "OngletOff"  : (bBlack,  fGreen,   sNormal),
                            "Bouton"     : (bLBlack, fGreen,   sBright),
                            "Editeur"    : (bLBlack, fGreen,   sBright),
                            "Decorateur" : (bLBlack, fGreen,   sDim),
                            "Selecteur"  : (bLBlack, fLGreen,  sBright),
                            "Options"    : (bLBlack, fGreen,   sBright),
                            'Alerte'     : (bRed,    fBlack,   sNormal), }
        elif os.path.exists(nom):
            with open(nom, 'r', encoding="utf-8") as f:
                self.palette = json.load(f)
        elif nom == "EXPLAIN":
            for k in self.palette:
                print("Couleur de " + self._couleurID(k, k))
            print('         ', end=" ")
            for back, stBack in [(bRed    , "fRed     "),
                                (bGreen   , "fGreen   "),
                                (bYellow  , "fYellow  "),
                                (bWhite   , "fWhite   "),
                                (bBlue    , "fBlue    "),
                                (bMagenta , "fMagenta "),
                                (bCyan    , "fCyan    "),
                                (bBlack   , "fBlack   "),
                                (bLBlack  , "fLBlack  "),
                                (bLBlue   , "fLBlue   "),
                                (bLCyan   , "fLCyan   "),
                                (bLGreen  , "fLGreen  "),
                                (bLMagenta, "fLMagenta"),
                                (bLRed    , "fLRed    "),
                                (bLWhite  , "fLWhite  "),
                                (bLYellow , "fLYellow ")]:
                print(stBack, end=" ")
            print()
            for back, stBack in [(bRed    , "bRed     "),
                                (bGreen   , "bGreen   "),
                                (bYellow  , "bYellow  "),
                                (bWhite   , "bWhite   "),
                                (bBlue    , "bBlue    "),
                                (bMagenta , "bMagenta "),
                                (bCyan    , "bCyan    "),
                                (bBlack   , "bBlack   "),
                                (bLBlack  , "bLBlack  "),
                                (bLBlue   , "bLBlue   "),
                                (bLCyan   , "bLCyan   "),
                                (bLGreen  , "bLGreen  "),
                                (bLMagenta, "bLMagenta"),
                                (bLRed    , "bLRed    "),
                                (bLWhite  , "bLWhite  "),
                                (bLYellow , "bLYellow ")]:
                print(stBack, end=" ")
                for lum, stLum in [(sBright, "Bri"), (sDim, "Dim"), (sNormal, "Nor")]:
                    for fore in [fRed, fGreen, fYellow, fWhite, fBlue, fMagenta, fCyan, fBlack,
                                 fLBlack, fLBlue, fLCyan, fLGreen, fLMagenta, fLRed, fLWhite, fLYellow]:
                        print(back + fore + lum + "Style %s"%stLum + sReset, end=" ")
                    if stLum == "N":
                        print()
                    else:
                        print('\n         ', end=" ")
                print()
        else:
            print(fRed + "Palette '%s' inconnue."%nom)
            self.TUI_fixePalette('defaut')

        #print("DBG>",len(self.blocs))
        for iBloc,_ in enumerate(self.blocs):
            largeur,tailleSep,bordGh,bordDt,_ = self.blocs[iBloc]
            coulSep = self.palette["Separateur"]
            self.blocs[iBloc] = (largeur,tailleSep,bordGh,bordDt,coulSep)

    # ---------------------------------------------------------------------------------
    def _couleurID(self, texte,coul,pActif=True):
        f, t, s = self.palette[coul]
        if not pActif:
            s = sDim
        return self._couleur(texte, f + t + s)

    @staticmethod
    def _couleur(texte, coul=None):
        # if self.debug > 2:
        #  return texte
        if coul is None:
            return texte
        return coul + texte + sReset

    def _couleurPerso(self, coul):
        if self.palette['Titre'] is None:
            return None
        # if self.debug > 2:
        #  return coul
        (fG, bG) = coul
        if fG == 'ROUGE':
            coul = fRed
        elif fG == 'VERT':
            coul = fGreen
        elif fG == 'JAUNE':
            coul = fYellow
        elif fG == 'BLANC':
            coul = fWhite
        elif fG == 'BLEU':
            coul = fBlue
        elif fG == 'MAGENTA':
            coul = fMagenta
        elif fG == 'CYAN':
            coul = fCyan
        elif fG == 'NOIR':
            coul = fBlack
        if bG == 'ROUGE':
            coul += bRed
        elif bG == 'VERT':
            coul += bGreen
        elif bG == 'JAUNE':
            coul += bYellow
        elif bG == 'BLANC':
            coul += bWhite
        elif bG == 'BLEU':
            coul += bBlue
        elif bG == 'MAGENTA':
            coul += bMagenta
        elif bG == 'CYAN':
            coul += bCyan
        elif bG == 'NOIR':
            coul += bBlack
        return coul

    # ---------------------------------------------------------------------------------
    ## Affichage d'un texte sur une ligne avec formatage sur 65 caracteres
    def _contenuSeparateur(self, pTexte, elem):
        if elem['OFFSET'] != 0:
            n = elem['OFFSET']
        else:
            n = self.espaceInterieur
        chaine = pTexte * n
        elem['LARG'] = len(chaine)
        return chaine

    # ---------------------------------------------------------------------------------
    def _AffLigneSeparateur(self, deb, elem, fin, pVersion=False):
        txtVersion = ""
        n = self.largeur-2 # 2: bordure
        if pVersion:
            n  -= 7 + len(TUIVERSION)
            txtVersion = "mpTUI v%s"%TUIVERSION
        ligne = ' ' + self._couleurID(deb + elem * n, 'Bordure') + self._couleurID(txtVersion, 'Bordure') + self._couleurID(fin, 'Bordure')
        return ligne

    # ---------------------------------------------------------------------------------
    ## Affichage d'un texte centre sur une ligne avec formatage sur 65 caracteres
    def _AffLigneCentrerTexte(self, pTexte):
        if len(pTexte)%2 != self.espaceInterieur%2:
            pTexte += ' '
        n = self.espaceInterieur - len(pTexte) + self.marge
        if self.debug:
            pTexte = 'C' * (n // 2) + pTexte + 'C' * (n // 2)
        else:
            pTexte = ' ' * (n // 2) + pTexte + ' ' * (n // 2)
        ligne = ' ' + self._couleurID('\u2503', 'Bordure') + self._couleurID(pTexte, 'Titre') + self._couleurID('\u2503', 'Bordure')
        return ligne

    # ---------------------------------------------------------------------------------
    def _AffLigneGaucheTexte(self, pNumBloc, pTexte, lLen):
        #n = self.espaceInterieur  # Les deux bordures extérieures
        pNumBloc = pNumBloc if pNumBloc is not None else 0
        espace,interBloc,bordGh,bordDt,coulSep = self.blocs[pNumBloc]
        #print("DBG>",coulSep)
        f, t, s = coulSep
        coulSep = f+t+s
        if self.debug:
            chaine = self._couleurID('M' * (self.marge // 2), 'Normal') + pTexte + self._couleurID('G' * (espace - lLen), 'Normal')
            chaine += self._couleurID('M' * (self.marge // 2), 'Normal')
            chaine += self._couleur('|' * interBloc, coulSep)
        else:
            chaine = self._couleurID(' ' * (self.marge // 2), 'Normal') + pTexte + self._couleurID(' ' * (espace - lLen), 'Normal')
            chaine += self._couleurID(' ' * (self.marge // 2), 'Normal')
            chaine += self._couleur('|' * interBloc, coulSep)
        ligne = ''
        if bordGh :
            ligne += ' '+self._couleurID('\u2503', 'Bordure')
        ligne += chaine
        if bordDt:
            ligne += self._couleurID('\u2503', 'Bordure')
        return ligne

    # ---------------------------------------------------------------------------------
    def _AffLigneDroiteTexte(self, pTexte, lLen):
        n = self.espaceInterieur
        if self.debug:
            chaine = self._couleurID('D' * (n - lLen), 'Normal') + pTexte
        else:
            chaine = self._couleurID(' ' * (n - lLen), 'Normal') + pTexte
        ligne = ' ' + self._couleurID('\u2503', 'Bordure') + chaine + self._couleurID('\u2503', 'Bordure')
        return ligne

    # ---------------------------------------------------------------------------------
    def _decoration(self, pDebForm, pFinForm):
        f, t, s = self.palette['Decorateur']
        decorDeb = self._couleur(pDebForm, f + t + s)
        decorFin = self._couleur(pFinForm, f + t + s)
        return decorDeb, decorFin, len(pDebForm + pFinForm)

    # ---------------------------------------------------------------------------------
    def _formatCouleur(self,pElement,pTexte,pCoulDefaut='Normal'):
        if 'COUL' in pElement:
            if isinstance(pElement['COUL'], str):
                coulTexte = self._couleurID(pTexte, pElement['COUL'],pElement['ACTIF'])
            else:
                f, t, s = pElement['COUL']
                if not pElement['ACTIF']:
                    s = sDim
                coulTexte = self._couleur(pTexte, f + t + s)
        else:
            coulTexte = self._couleurID(pTexte, pCoulDefaut,pElement['ACTIF'])
        return coulTexte

    # ---------------------------------------------------------------------------------
    def _formatAlignement(self,pTexte,pLargeur,pAlignement):
        if len(pTexte) < pLargeur:
            if pAlignement == 'D':
                pTexte = ' '*(pLargeur-len(pTexte))+pTexte
            elif pAlignement == 'G':
                pTexte = pTexte+' '*(pLargeur-len(pTexte))
            else:
                debTexte = ' '*((pLargeur-len(pTexte))//2)
                finTexte = debTexte
                if len(debTexte)*2+len(pTexte)!=pLargeur:
                    finTexte += ' '
                pTexte = debTexte+pTexte+finTexte
        return pTexte

    # ---------------------------------------------------------------------------------
    def _FormateSEP(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']
        if largeur == 0:
            bloc = pElement['COLON'] if pElement['COLON'] is not None else 0
            largeur = self.blocs[bloc][0]
            #    largeur = self.espace
     #   print("DBG-SEP>",largeur,pElement['COLON'])

        # 3 - Traitement du texte
        # contenu
        if isinstance(pElement['TEXTE'],tuple):
            separateur,espace,libelle = pElement['TEXTE']
            libelle = self._remplaceVariable(libelle)
            texte = "%s[ %s ]%s"%(separateur*espace,libelle,separateur*(largeur-espace-len(libelle)-4))
        else:
            texte = self._remplaceVariable(pElement['TEXTE'])
            texte = texte * largeur
        # couleur
        coulTexte = self._formatCouleur(pElement,texte,"Separateur")

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        if self.debug:
            coulOffset = self._couleurID('O' * offset, 'Normal')
        else:
            coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        #  - s.o. -

        # Constitution des chaines
        chaine = coulOffset + coulTexte
        largElement = offset + len(texte)

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateTEN(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        hauteur = pElement['DIM']

        bloc = pElement['COLON'] if pElement['COLON'] is not None else 0
        largeur = self.blocs[bloc][0]

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        texte = texte * largeur
        # couleur
        coulTexte = self._formatCouleur(pElement,texte)

        # 5 - Traitement de l'action
        #  - s.o. -

        # Constitution des chaines
        chaine = [coulTexte]*hauteur
        largElement = [len(texte)]*hauteur

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateSLD(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -
        (imin, imax, its, itx) = pElement['INTERVALLE']
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']
        largeurEditeur = 4
        if isinstance(largeur,tuple):
            largeur,largeurEditeur = largeur
        if largeur==0:
            #print("DBG-SLD> MnMx",imax-imin+1,self.espaceInterieur-self.marge)
            largeur = min(imax-imin+1,self.espaceInterieur-self.marge-largeurEditeur-len(action))

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        # couleur
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        if self.debug:
            coulOffset = self._couleurID('O' * offset, 'Normal')
        else:
            coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action
        # couleur
        _, t, s = self.palette['Action']
        f, _, _ = self.palette['Onglet']
        coulAction = self._couleur(action, f + t + s)

        # 6 - Traitement de la sélection
        # contenu
        selection = int(self.TUI_getValeurObjet(pElement,'SELECT'))

        echelle = (largeur-1)/(imax-imin)
        pointeur = int(selection*echelle)
        selection = str(selection)

        # 3 - Traitement du slider
        slider = list('-' * largeur)
        #print("slider",len(slider),pointeur)
        slider[pointeur]='o'
        slider=''.join(slider)
        # couleur
        coulSlider = self._formatCouleur(pElement, slider, 'Selecteur')

        # formatage
        decorDeb, decorFin, longForm = self._decoration("[", "]")

        selection = self._formatAlignement(selection,largeurEditeur,pElement['ALIGN'])
        coulSelection = self._formatCouleur(pElement, selection, 'Editeur')

        # Constitution des chaines
        if pElement['ALIGN'] == 'D':
            chaine = coulOffset + coulTexte + coulAction + decorDeb + coulSlider + coulSelection + decorFin
        else:
            chaine = coulOffset + coulTexte + coulAction + decorDeb + coulSelection + coulSlider + decorFin
        largElement = offset + len(texte) + len(action) + len(slider) + longForm + largeurEditeur

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateLBL(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action
        # couleur
        coulAction = self._couleurID(action, 'Action', pElement['ACTIF'])

        # 6 - Traitement de la sélection
        # contenu
        if largeur>0:
            texte = self._formatAlignement(texte,largeur,pElement['ALIGN'])
            if len(texte)>largeur:
                if pElement['ALIGN'] == 'G':
                    texte = ''.join(list(texte)[:(largeur-3)])+'...'
                else:
                    texte = '...'+''.join(list(texte)[-(largeur-3):])
        coulTexte = self._formatCouleur(pElement, texte, 'Normal')

        # Constitution de la chaine
        if pElement['ALIGN'] == 'G':
            chaine = coulOffset + coulAction + coulTexte
            largElement = offset + len(action) + len(texte)
        else:
            chaine = coulOffset + coulTexte + coulAction
            largElement = offset + len(action) + len(texte)

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateEDT(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        # couleur
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action
        # couleur
        coulAction = self._couleurID(action, 'Action', pElement['ACTIF'])

        # 6 - Traitement de la sélection
        # contenu
        selection = str(self.TUI_getValeurObjet(pElement,'SELECT'))
        if largeur > 0:
            selection = self._formatAlignement(selection,largeur,pElement['ALIGN'])
            if len(selection) > largeur:
                if pElement['ALIGN'] == 'G':
                    selection = ''.join(list(selection)[:(largeur-3)])+'...'
                else:
                    selection = '...'+''.join(list(selection)[-(largeur-3):])

        # formatage
        decorDeb, decorFin, longForm = self._decoration("|", "|")
        coulSelection = self._formatCouleur(pElement, selection, 'Editeur')

        # Constitution de la chaine
        chaine = coulOffset + coulTexte + coulAction + decorDeb + coulSelection + decorFin
        largElement = offset + len(texte) + len(action) + len(selection) + longForm

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateSPB(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        # couleur
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = "(%s)"%pElement['ACTION']
        # couleur
        coulAction = self._couleurID(action, 'Action', pElement['ACTIF'])

        # 6 - Traitement de la sélection
        # contenu
        selection = str(self.TUI_getValeurObjet(pElement,'SELECT'))
        if largeur > 0:
            selection = self._formatAlignement(selection,largeur,pElement['ALIGN'])
        # formatage
        decorDeb, decorFin, longForm = self._decoration("|", "|")
        selectForm = self._couleurID("+-", "Selecteur", pElement['ACTIF'])
        longForm = 5  # || +  - |
        coulSelection = self._formatCouleur(pElement, selection, 'Editeur')

        # Constitution de la chaine
        #       offset     blabla      (a)        |      selection       |          + -         |
        chaine = coulOffset + coulTexte + coulAction + decorDeb + coulSelection + decorFin + selectForm + decorFin
        largElement = offset + len(texte) + len(action) + len(selection) + longForm

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateCKB(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        #  - s.o. -

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        # couleur
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action
        # couleur
        coulAction = self._couleurID(action, 'Action', pElement['ACTIF'])

        # 6 - Traitement de la sélection
        # contenu
        selection = " "
        if self.TUI_getValeurObjet(pElement,'SELECT') == 1:
            selection = "x"
        # formatage
        decorDeb, decorFin, longForm = self._decoration("[", "]")
        # couleur
        coulSelection = self._formatCouleur(pElement, selection, "Selecteur")

        # Constitution de la chaine
        if pElement['ALIGN'] == 'D':
            chaine = coulOffset + decorDeb + coulSelection + decorFin + coulAction + coulTexte
            largElement = offset + len(action) + len(selection) + len(texte) + longForm
        else:
            chaine = coulOffset + coulTexte + coulAction + decorDeb + coulSelection + decorFin
            largElement = offset + len(action) + len(texte) + len(selection) + longForm

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateBTN(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']

        # 3 - Traitement du texte
        # contenu
        texte = "%s"%self._remplaceVariable(pElement['TEXTE'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action
        # couleur
        _, t, s = self.palette["Action"]
        f, _, _ = self.palette["Bouton"]

        coulAction = self._couleur(action, f + t + s)

        # 6 - Traitement de la sélection
        #  - s.o. -

        # 7 - Traitement du decorateur
        decorDeb, decorFin, longForm = self._decoration("[", "]")

        # largeur et alignement
        if largeur > 0:
            largeur -= len(action) + longForm
            texte = self._formatAlignement(texte,largeur,pElement['ALIGN'])
        largeur = max(largeur, len(texte))
        coulTexte = self._formatCouleur(pElement, texte, "Bouton")

        # Constitution de la chaine
        chaine = coulOffset + decorDeb + coulAction + coulTexte + decorFin
        largElement = offset + len(action) + largeur + longForm
        return chaine, largElement

    # ---------------------------------------------------------------------------------
    #
    # ____/(t:0)TAB\____________
    def _FormateTAB(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        bloc = pElement['COLON'] if pElement['COLON'] is not None else 0
        espace = self.blocs[bloc][0]

        # 3 - Traitement de la sélection
        #  - s.o. -
        selection = int(self.TUI_getValeurObjet(pElement,'SELECT'))

        # 4 - Traitement du texte
        # contenu
        onglets = self._remplaceVariable(pElement['OPTIONS'])
        texte=[]
        coulTexte=[]
        for itexte,vtexte in enumerate(onglets):
            if pElement['VISIBLE'][itexte]:
                texte.append(vtexte)
                coulTexte.append(self._formatCouleur(pElement, vtexte, 'Onglet' if itexte == selection else 'OngletOff'))

        # 5 - Traitement de l'offset
        #  - s.o. -

        # 6 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        # couleur
        coulAction = []
        actionBrut = []
        for itexte,_ in enumerate(onglets):
            #print("DBG>",pElement['VISIBLE'][itexte])
            if pElement['VISIBLE'][itexte]:
                f, _, _ = self.palette['Onglet' if itexte == selection else 'OngletOff']
                _, t, s = self.palette['Action' if itexte == selection else 'OngletOff']
                coulAction.append(self._couleur("(%s:%d)"%(action,itexte), f + t + s))
                actionBrut.append("(%s:%d)"%(action,itexte))

        # 7 - Traitement du formatage
        debForm, finForm, longForm = "/", "\\", 2
        cardeb = '_'
        coulDeb = self._formatCouleur(pElement, cardeb, 'Onglet')

        # couleur
        coulDebForm = self._formatCouleur(pElement, debForm, 'Onglet')
        coulFinForm = self._formatCouleur(pElement, finForm, 'Onglet')

        # Constitution de la chaine
        chaineBrut=[""]
        itemsBrut=[]
        listeItems=[]
        for itexte,_ in enumerate(texte):
            strChaineBrut = cardeb.join(chaineBrut) + cardeb + debForm + actionBrut[itexte] + texte[itexte] + finForm
            if len(strChaineBrut)<espace:
                chaineBrut.append(debForm + actionBrut[itexte] + texte[itexte] + finForm)
                itemsBrut.append(itexte)
            else:
                listeItems.append(itemsBrut)
                chaineBrut=["",debForm + actionBrut[itexte] + texte[itexte] + finForm]
                itemsBrut=[itexte]
        if len(chaineBrut)>1:
            listeItems.append(itemsBrut)

        chaines=[]
        largElement=[]
        for items in listeItems:
            chaine = []
            lenAction = 0
            for itexte in items:
                chaine.append(coulDebForm + coulAction[itexte] + coulTexte[itexte] + coulFinForm)
                lenAction += longForm + 6 + len(texte[itexte])
            carFin = cardeb * (espace - lenAction)
            chaines.append(coulDeb + coulDeb.join(chaine) + self._formatCouleur(pElement, carFin, 'Onglet'))
            largElement.append(espace)

        return chaines, largElement

    # ---------------------------------------------------------------------------------
    def _FormateSPL(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']
        #print("DBG:SPL>",self.blocs,largeur,pElement['COLON'])
        bloc = pElement['COLON'] if pElement['COLON'] is not None else 0
        espace = self.blocs[bloc][0]

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        # largeur et alignement
        if largeur > 0:
            texte = self._formatAlignement(texte,largeur,pElement['ALIGN'])
        # couleur
        coulTexte = self._formatCouleur(pElement, texte , "Onglet")

        # 4 - Traitement de l'offset
        #  - s.o. -

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action
        # couleur
        _, t, s = self.palette['Action']
        f, _, _ = self.palette['Onglet']
        coulAction = self._couleur(action, f + t + s)

        # 6 - Traitement de la sélection
        #  - s.o. -

        # 7 - Traitement du formatage
        if pElement['ACTION'] is None:
            debForm, finForm, longForm = "", "", 0
        else:
            debForm, finForm, longForm = "[", "]", 2
        if len(pElement['SPL']) == 1:
            caract = '='
            nbCaract = 3
        else:
            caract = '-'
            nbCaract = 6
        if len(texte) != 0:
            cardeb = caract * nbCaract
            carFin = caract * (espace - len(action) - len(texte) - nbCaract - longForm)
        else:
            cardeb = '-' * espace
            carFin = ''
        debForm = cardeb + debForm
        finForm = finForm + carFin
        # couleur
        coulDeb = self._formatCouleur(pElement, debForm , "Onglet")
        coulFin = self._formatCouleur(pElement, finForm , "Onglet")

        # Constitution de la chaine
        chaine = coulDeb + coulAction + coulTexte + coulFin
        largElement = espace

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateCBX(self, pElement):
        # 1 - Traitement des options
        options = pElement['OPTIONS']
        if len(options) == 0:
            return [], [], None
        # détermination de la largeur des choix
        largOptions = 1
        for i in range(len(options)):
            options[i] = self._remplaceVariable(options[i])
            largOptions = max(largOptions, len(options[i]))

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']
        if largeur == 0:
            largeur = largOptions

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 5 - Traitement de l'action
        # contenu
        action = "(%s)"%pElement['ACTION']
        coulAction = self._couleurID(action, 'Action', pElement['ACTIF'])
        actionDeploie = pElement['ACTION']

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        offsetMin = len(pElement['ACTION'])+1+(1 if len(pElement['OPTIONS'])>9 else 0)
        if len(texte)<offsetMin:
            offset+=offsetMin
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        offsetOptions = len(action)
        deuxPointsValeur = 1 + len(str(len(pElement['OPTIONS']) - 1))
        coulOffsetOptions = self._couleurID(' ' * (offset + len(texte) - deuxPointsValeur), 'Normal')
        coulOffsetFin = self._couleurID(' ' * (offset + len(texte) + offsetOptions), 'Normal')

        # 6 - Traitement de la sélection
        # contenu
        numSelection = int(self.TUI_getValeurObjet(pElement,'SELECT'))
        selection = ""
        if numSelection != -1:
            if numSelection >= len(pElement['OPTIONS']):
                numSelection = 0
            selection = options[numSelection]
        # formatage
        decorDeb, decorFin, longForm = self._decoration("|", "|")
        deploieForm = self._couleurID("v", "Decorateur", pElement['ACTIF'])
        selectForm = self._couleurID(">", "Selecteur", pElement['ACTIF'])
        deselectForm = self._couleurID(" ", "Decorateur", pElement['ACTIF'])
        longForm = 4  # ||v|
        coulSelection = self._formatCouleur(pElement, selection , "Editeur")
        coulEspaceSelection = self._formatCouleur(pElement, ' ' * (largeur - len(selection)), "Editeur")

        # Constitution des chaines
        deploie = None
        if pElement['DEPLOIE']:
            chaineDeploie = []
            largElementDeploie = []
            lenEspace = 0
            if len(options) > 10:
                lenEspace = 1
            for i, _ in enumerate(options):
                espace = ''
                if len(options) > 10 > i:
                    espace = ' '
                coulNumerotation = self._couleurID('(%s:%d)%s'%(actionDeploie, i, espace), 'Action', pElement['ACTIF'])
                coulOption = self._couleurID(options[i], 'Options', pElement['ACTIF'])
                coulEspaceOption = self._couleurID(' '*(largeur-len(options[i])-1), 'Options', pElement['ACTIF'])
                if i == numSelection:
                    coulSelect = selectForm
                else:
                    coulSelect = deselectForm
                #                        offset            (a)            |      >            option      |
                if pElement['ALIGN']=="G":
                    chaineDeploie.append(coulOffsetOptions + coulNumerotation + decorDeb + coulSelect + coulOption + coulEspaceOption + decorFin)
                else:
                    chaineDeploie.append(coulOffsetOptions + coulNumerotation + decorDeb + coulSelect + coulEspaceOption + coulOption + decorFin)
                largElementDeploie.append(pElement['OFFSETDEPL'] + offset + len(texte) + offsetOptions - deuxPointsValeur + longForm + largeur + lenEspace)
            # trait final
            traitFinal = '+' + '-' * largeur + '+'
            coulTraitFinal = self._couleurID(traitFinal, 'Decorateur', pElement['ACTIF'])
            chaineDeploie.append(coulOffsetFin + coulTraitFinal)
            largElementDeploie.append(pElement['OFFSETDEPL'] + offset + len(texte) + offsetOptions + largeur + 2)
            deploie = (chaineDeploie, largElementDeploie)
        pElement['DEPLOIE'] = False

        # Chaine simple avec ou sans déploiement
        if pElement['ALIGN']=="G":
            chaine = coulOffset + coulTexte + coulAction + decorDeb + coulSelection + coulEspaceSelection + decorFin + deploieForm + decorFin
        else:
            chaine = coulOffset + coulTexte + coulAction + decorDeb + coulEspaceSelection + coulSelection + decorFin + deploieForm + decorFin
        largElement = offset + len(texte) + len(action) + 1 + largeur + 3

        return chaine, largElement, deploie

    # ---------------------------------------------------------------------------------
    def _FormateLST(self, pElement):
        # 1 - Traitement des options
        options = pElement['OPTIONS']
        if len(options) == 0:
            return [], []
        # détermination de la largeur des choix
        largOptions = 1
        for i in range(len(options)):
            options[i] = self._remplaceVariable(options[i])
            largOptions = max(largOptions, len(options[i]))

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']
        if largeur == 0:
            largeur = largOptions

        # 3 - Traitement du texte
        texte = self._remplaceVariable(pElement['TEXTE'])
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 5 - Traitement de l'action
        action = pElement['ACTION']

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 4b - Traitement du décalage
        decalage = pElement['DECAL']
        coulDecalage = self._couleurID(' ' * decalage, 'Normal')

        # 6 - Traitement de la sélection
        # contenu
        selections = self.TUI_getValeurObjet(pElement,'SELECT')
        # formatage
        decorDeb, decorFin, longForm = self._decoration("|", "|")
        selectForm = self._couleurID(">", "Selecteur", pElement['ACTIF'])
        deselectForm = self._couleurID(" ", "Selecteur", pElement['ACTIF'])

        # Constitution des chaines
        chaine = []
        largElement = []
        if len(texte) > 0:
            chaine.append(coulOffset + coulTexte)
            largElement.append(offset + len(texte))
        for i, _ in enumerate(options):
            espace = ''
            if len(options) > 10 > i:
                espace = ' '
            numerotation = '(%s:%d)%s'%(action, i, espace)
            coulNumerotation = self._couleurID(numerotation, 'Action', pElement['ACTIF'])
            selection = options[i]
            if len(options[i]) > largeur:
                if pElement['ALIGN'] == 'G':
                    selection = ''.join(list(options[i])[:(largeur-3)])+'...'
                else:
                    selection = '...'+''.join(list(options[i])[-(largeur-3):])
            coulOption = self._formatCouleur(pElement,selection, 'Options')
            coulEspaceOption = self._formatCouleur(pElement,' '*(largeur-len(selection)), 'Options')
            if i in selections:
                coulSelect = selectForm
            else:
                coulSelect = deselectForm
            #                        offset            (a)            |      >            option      |
            if pElement['ALIGN']=="G":
                chaine.append(coulOffset + coulDecalage + coulNumerotation + decorDeb + coulSelect + coulOption + coulEspaceOption + decorFin)
            else:
                chaine.append(coulOffset + coulDecalage + coulNumerotation + decorDeb + coulSelect + coulEspaceOption + coulOption + decorFin)
            largElement.append(offset + decalage + len(numerotation) + longForm+1 + largeur)

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateGRD(self, pElement):
        # 1 - Traitement de la grille
        grille = pElement['SELECT']
        if len(grille) == 0:
            return [], []

        # 2 - Traitement de la largeur
        largCellules = pElement['LARG']
        if isinstance(largCellules,int):
            largCellules = [largCellules]*len(grille[0])
        largCellules = list(largCellules)
        for col in range(len(grille[0])):
            if largCellules[col] == 0:
                # détermination de la largeur des choix
                for lig in range(len(grille)):
                    grille[lig][col] = self._remplaceVariable(grille[lig][col])
                    largCellules[col] = max(largCellules[col], len(grille[lig][col]))
        largeur = sum(largCellules)

        # 3 - Traitement du texte
        texte = self._remplaceVariable(pElement['TEXTE'])
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 5 - Traitement de l'action
        action = "(%s)"%pElement['ACTION']
        coulAction = self._couleurID(action, 'Action', pElement['ACTIF'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 4b - Traitement du décalage
        decalage = pElement['DECAL']
        coulDecalage = self._couleurID(' ' * decalage, 'Normal')

        if isinstance(pElement['ALIGN'],tuple):
            alignLig,alignCol,alignCell = pElement['ALIGN']
        else:
            alignLig,alignCol,alignCell = pElement['ALIGN'],pElement['ALIGN'],pElement['ALIGN']

        # 6 - Traitement de la sélection
        # formatage
        decorCol,sepCol,decorLig,sepLig = '','','',''
        if 'DECOR' in pElement:
            decorCol,sepCol,decorLig,sepLig = pElement['DECOR']
        decorDeb, decorFin, longForm = self._decoration(decorCol,decorCol)
        sepCol, _, longFormSep = self._decoration(sepCol,sepCol)
        longFormSep = longFormSep//2
        coulDecorLig, _, _ = self._decoration(decorLig,decorLig)
        coulSepLig, _, _ = self._decoration(sepLig,sepLig)

        # Constitution des chaines
        #-entete
        chaine = []
        largElement = []
        ligneEntete = ""
        taillEntete = 0
        if len(texte)>0:
            ligneEntete += coulOffset + coulTexte
            taillEntete += offset + len(texte)
        if largCellules[0]==0:
            ligneEntete += coulAction
            taillEntete += len(action)
            action = ""
        if len(ligneEntete)>0:
            chaine.append(ligneEntete)
            largElement.append(taillEntete)
        #-entete
        for iLigne,vLigne in enumerate(grille):
#            numerotation = '(%s:%d)%s'%(action, i, espace)
#            coulNumerotation = self._couleurID(numerotation, 'Action')
#            coulEspaceOption = self._formatCouleur(pElement,' '*(largeur-len(options[i])), 'Options')
#            if i in selections:
#                coulSelect = selectForm
#            else:
#                coulSelect = deselectForm
            chaineLigne = coulOffset + coulDecalage
            for iCellule,vCellule in enumerate(vLigne):
                if iCellule==1:
                    chaineLigne += decorDeb
                elif iCellule>1:
                    chaineLigne += sepCol
                if iLigne+iCellule==0:
                    vCellule = self._formatAlignement(action,largCellules[iCellule],'C')
                    coulCellule = self._couleurID(vCellule, 'Action', pElement['ACTIF'])
                elif iLigne==0:
                    vCellule = self._formatAlignement(vCellule,largCellules[iCellule],alignCol)
                    coulCellule = self._formatCouleur(pElement,vCellule, 'Decorateur')
                elif iCellule==0:
                    vCellule = self._formatAlignement(vCellule,largCellules[iCellule],alignLig)
                    coulCellule = self._formatCouleur(pElement,vCellule, 'Decorateur')
                elif vCellule is None:
                    vCellule = self._formatAlignement("",largCellules[iCellule],alignCell)
                    coulCellule = self._formatCouleur(pElement,vCellule, 'Normal')
                else:
                    #print("DBG>",largCellules,iCellule,vLigne)
                    vCellule = self._formatAlignement(vCellule,largCellules[iCellule],alignCell)
                    if len(vCellule) > largCellules[iCellule]:
                        if alignCell == 'G':
                            vCellule = ''.join(list(vCellule)[:(largCellules[iCellule]-3)])+'...'
                        else:
                            vCellule = '...'+''.join(list(vCellule)[-(largCellules[iCellule]-3):])
                    coulCellule = self._formatCouleur(pElement,vCellule, 'Editeur')
                chaineLigne += coulCellule
            chaineLigne += decorFin
            chaine.append(chaineLigne)
            largeurChaine = offset + decalage + longForm + longFormSep*(len(grille[0])-2) + largeur
            largElement.append(largeurChaine)
            isDecorLig = False
            if decorLig!='':
                if iLigne==0:
                    ligne = coulDecorLig*(largeur+len(grille[0])-1)
                    if largCellules[0]==0 and sepCol!='':
                        ligne = sepCol + coulDecorLig*(largeur+len(grille[0])-2)
                    chaine.append(coulOffset + coulDecalage + ligne + decorFin)
                    largElement.append(largeurChaine)
                    isDecorLig = True
                elif iLigne==len(grille)-1:
                    chaine.append(coulOffset + coulDecalage + coulDecorLig*(largeur+len(grille[0])))
                    largElement.append(largeurChaine)
                    isDecorLig = True
            if sepLig!='' and not isDecorLig:
                ligne = coulSepLig*(largeur+len(grille[0])-1)
                if largCellules[0]==0 and sepCol!='':
                    ligne = sepCol + coulSepLig*(largeur+len(grille[0])-2)
                chaine.append(coulOffset + coulDecalage + ligne + decorFin)
                largElement.append(largeurChaine)
        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateRAD(self, pElement):
        # 1 - Traitement des options
        options = pElement['OPTIONS']
        # détermination de la largeur des choix
        largOptions = 1
        for i, _ in enumerate(options):
            options[i] = self._remplaceVariable(options[i])
            largOptions = max(largOptions, len(options[i]))

        # 2 - Traitement de la largeur
        largeur = 0
        nbCol = 1
        espaceCol = 1
        if isinstance(pElement['LARG'],int):
            largeur = pElement['LARG']
        elif len(pElement['LARG'])==2:
            largeur,nbCol = pElement['LARG']
        else:
            largeur,nbCol,espaceCol = pElement['LARG']
        coulSepCol = self._couleurID(' ' * espaceCol, 'Normal')
        if largeur == 0:
            largeur = largOptions

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        longFormat = 7 + len(pElement['ACTION'])  # (X:n)( * )"
        if len(texte) > 0:
            while len(texte) < largeur + longFormat:  # Largeur des options, longeur du format, complement d'offset
                if self.debug:
                    texte += 'L'
                else:
                    texte += ' '
        # couleur
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']

        # 6 - Traitement de la sélection
        # contenu
        selection = self.TUI_getValeurObjet(pElement,'SELECT')
        # formatage
        decorDeb, decorFin, longFormat = self._decoration("(", ")")
        selectForm = self._formatCouleur(pElement, "o", "Selecteur")
        deselectForm = self._formatCouleur(pElement, " ", "Selecteur")

        longFormat += 5+len(action)  # (X:n)[ ]"
        if len(options) > 10:
            longFormat += 1

        # Constitution des chaines
        chaine = []
        largElement = []
        dbg = []
        if len(texte) > 0:
            chaine.append(coulOffset + coulTexte)
            largElement.append(offset + len(texte))
        nbLignes = len(options) // nbCol
        if nbLignes * nbCol < len(options):
            nbLignes += 1
        for i in range(nbLignes):
            wkchaine = ""
            wkdbg = ""
            wklargElement = 0
            for col in range(nbCol):
                icol = i * nbCol + col
                if icol < len(options):
                    esp = " " if len(options) > 10 > i else ""
                    # couleur
                    coulAction = self._couleurID('(%s:%d)%s'%(action, icol, esp), 'Action', pElement['ACTIF'])
                    if icol == selection:
                        coulSelect = selectForm
                    else:
                        coulSelect = deselectForm
                    texte = self._formatAlignement(options[icol],largeur,pElement['ALIGN'])
                    coulTexte = self._couleurID(texte, 'Options', pElement['ACTIF'])
                    if pElement['ALIGN'] == 'G':
                        wkchaine += coulTexte + coulAction + decorDeb + coulSelect + decorFin
                    else:
                        wkchaine += coulAction + decorDeb + coulSelect + decorFin + coulTexte
                    wkdbg += options[icol]
                    wklargElement += longFormat + largeur
                if nbCol>1 and col<nbCol-1:
                    wkchaine += coulSepCol
                    wklargElement += espaceCol

            chaine.append(coulOffset + wkchaine)
            dbg.append(wkdbg)
            largElement.append(offset + wklargElement)
        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateGCB(self, pElement):
        # 1 - Traitement des options
        options = pElement['OPTIONS']
        if len(options) == 0:
            return [], []
        # détermination de la largeur des choix
        largOptions = 1
        for i, _ in enumerate(options):
            options[i] = self._remplaceVariable(options[i])
            largOptions = max(largOptions, len(options[i]))

        # 2 - Traitement de la largeur
        largeur = 0
        nbCol = 1
        espaceCol = 1
        if isinstance(pElement['LARG'],int):
            largeur = pElement['LARG']
        elif len(pElement['LARG'])==2:
            largeur,nbCol = pElement['LARG']
        else:
            largeur,nbCol,espaceCol = pElement['LARG']
        coulSepCol = self._couleurID(' ' * espaceCol, 'Normal')
        if largeur == 0:
            largeur = largOptions

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        longFormat = 8  # (X:n)( * )"
        if len(options) > 10:
            longFormat += 1
        if len(texte) > 0:
            while len(texte) < largeur + longFormat:  # Largeur des options, longeur du format, complement d'offset
                texte += ' '
        # couleur
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 6 - Traitement de la sélection
        # contenu
        selections = self.TUI_getValeurObjet(pElement,'SELECT')
        # formatage
        decorDeb, decorFin, longFormat = self._decoration("[", "]")
        selectForm = self._formatCouleur(pElement, "x", "Selecteur")
        deselectForm = self._formatCouleur(pElement, " ", "Selecteur")

        longFormat += 5+len(action)  # (X:n)[ ]"
        if len(options) > 10:
            longFormat += 1

        # Constitution des chaines
        chaine = []
        largElement = []
        dbg = []
        if len(texte) > 0:
            chaine.append(coulOffset + coulTexte)
            largElement.append(offset + len(texte))
        nbLignes = len(options) // nbCol
        if nbLignes * nbCol < len(options):
            nbLignes += 1
        for i in range(nbLignes):
            wkchaine = ""
            wkdbg = ""
            wklargElement = 0
            for col in range(nbCol):
                icol = i * nbCol + col
                if icol < len(options):
                    esp = " " if len(options) > 10 > i else ""
                    # couleur
                    coulAction = self._couleurID('(%s:%d)%s'%(action, icol, esp), 'Action', pElement['ACTIF'])
                    if icol in selections:
                        coulSelect = selectForm
                    else:
                        coulSelect = deselectForm
                    texte = self._formatAlignement(options[icol],largeur,pElement['ALIGN'])
                    coulTexte = self._couleurID(texte, 'Options', pElement['ACTIF'])
                    if pElement['ALIGN'] == 'G':
                        wkchaine += coulTexte + coulAction + decorDeb + coulSelect + decorFin
                    else:
                        wkchaine += coulAction + decorDeb + coulSelect + decorFin + coulTexte
                    wkdbg += options[icol]
                    wklargElement += longFormat + largeur
                if nbCol>1 and col<nbCol-1:
                    wkchaine += coulSepCol
                    wklargElement += espaceCol

            chaine.append(coulOffset + wkchaine)
            dbg.append(wkdbg)
            largElement.append(offset + wklargElement)
        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateSelectZED(self,pElement,pSelection):
        if isinstance(pSelection,str):
            pSelection = [pSelection]
        largeur = pElement['LARG']
        if largeur == 0:
            largeur = self.espaceInterieur - 2*self.marge - len(self._remplaceVariable(pElement['TEXTE'])) - len(pElement['ACTION']) - pElement['OFFSET']
        listeTexte = []
        for ligneSel in pSelection:
            while len(ligneSel) > largeur:
                listeTexte.append(ligneSel[:largeur])
                ligneSel = ligneSel[largeur:]
            ligneSel = ligneSel + ' ' * (largeur - len(ligneSel))
            listeTexte.append(ligneSel)
        return listeTexte

    # ---------------------------------------------------------------------------------
    def _FormateZED(self, pElement):
        # 1 - Traitement des options
        #  - s.o. -
        selection = self.TUI_getValeurObjet(pElement,'SELECT')
        taille = len(selection)

        # 2 - Traitement de la largeur
        largeur = pElement['LARG']
        hauteur = pElement['HAUT']
        if largeur == 0:
            largeur = self.espaceInterieur - 2*self.marge - len(self._remplaceVariable(pElement['TEXTE'])) - len(pElement['ACTION']) - pElement['OFFSET']

        # 3 - Traitement du texte
        # contenu
        texte = self._remplaceVariable(pElement['TEXTE'])
        # couleur
        coulTexte = self._couleurID(texte, 'Normal', pElement['ACTIF'])

        # 4 - Traitement de l'offset
        offset = pElement['OFFSET']
        coulOffset = self._couleurID(' ' * offset, 'Normal')

        # 4b - Traitement du décalage
        decalage = pElement['DECAL']
        coulDecalage = self._couleurID(' ' * decalage, 'Normal')

        # 5 - Traitement de l'action
        # contenu
        action = pElement['ACTION']
        if action is None:
            action = ""
        else:
            action = "(%s)"%action
        # couleur
        coulAction = self._couleurID(action, 'Action', pElement['ACTIF'])

        # ascenseur
        scroll = pElement['SCROLL']
        nScroll = self._couleurID('|', 'Selecteur')
        iScroll = self._couleurID('o', 'Selecteur')

        # 6 - Traitement de la sélection
        # contenu
        if hauteur==0:
            scroll = -1
        elif len(selection)<=hauteur:
            while len(selection)<hauteur:
                selection.append(' '*largeur)
            scroll = -1
        elif scroll==-1:
            if pElement['ALIGN'] == "G":
                selection = selection[:hauteur]
                selection[-1] = ''.join(selection[-1][:-3])+'...'
            else:
                selection = selection[-hauteur:]
                selection[0] = '...'+''.join(selection[0][3:])
        else:
            selection = selection[scroll:scroll+hauteur]

        # formatage
        decorDeb, decorFin, longForm = self._decoration("|", "|")

        # Constitution des chaines
        chaine = []
        largElement = []
        chaine.append(coulOffset + coulTexte + coulAction)
        largElement.append(offset + len(texte) + len(action))
        indexScroll = 0
        if scroll!=-1:
            indexScroll = scroll//((taille-1)/(hauteur+1))

        for iTexte, vTexte in enumerate(selection):
    #        coulSelection = self._couleurID(texte, 'Editeur')
            coulSelection = self._formatCouleur(pElement, vTexte, 'Editeur')
            if scroll==-1:
                chaine.append(coulOffset + coulDecalage + decorDeb + coulSelection + decorFin)
                largElement.append(offset + decalage +  largeur + longForm)
            elif iTexte==indexScroll:
                chaine.append(coulOffset + coulDecalage + decorDeb + coulSelection + decorFin + iScroll + decorFin)
                largElement.append(offset + decalage +  largeur + longForm + 2)
            else:
                chaine.append(coulOffset + coulDecalage + decorDeb + coulSelection + decorFin + nScroll + decorFin)
                largElement.append(offset + decalage +  largeur + longForm + 2)

        return chaine, largElement

    # ---------------------------------------------------------------------------------
    def _FormateElement(self, pElement):
        if self.debug > 1:
            self._print(pElement)
        deploie = None
        if pElement['TYPE'] == 'SPL':
            (chaine, lenChaine) = self._FormateSPL(pElement)
        elif pElement['TYPE'] == 'TAB':
            (chaine, lenChaine) = self._FormateTAB(pElement)
        elif pElement['TYPE'] == 'LBL':
            (chaine, lenChaine) = self._FormateLBL(pElement)
        elif pElement['TYPE'] == 'BTN':
            (chaine, lenChaine) = self._FormateBTN(pElement)
        elif pElement['TYPE'] == 'EDT':
            (chaine, lenChaine) = self._FormateEDT(pElement)
        elif pElement['TYPE'] == 'CBX':
            (chaine, lenChaine, deploie) = self._FormateCBX(pElement)
        elif pElement['TYPE'] == 'SLD':
            (chaine, lenChaine) = self._FormateSLD(pElement)
        elif pElement['TYPE'] == 'SPB':
            (chaine, lenChaine) = self._FormateSPB(pElement)
        elif pElement['TYPE'] == 'SEP':
            (chaine, lenChaine) = self._FormateSEP(pElement)
        elif pElement['TYPE'] == 'ZED':
            (chaine, lenChaine) = self._FormateZED(pElement)
        elif pElement['TYPE'] == 'RAD':
            (chaine, lenChaine) = self._FormateRAD(pElement)
        elif pElement['TYPE'] == 'GCB':
            (chaine, lenChaine) = self._FormateGCB(pElement)
        elif pElement['TYPE'] == 'CKB':
            (chaine, lenChaine) = self._FormateCKB(pElement)
        elif pElement['TYPE'] == 'LST':
            (chaine, lenChaine) = self._FormateLST(pElement)
        elif pElement['TYPE'] == 'TEN':
            (chaine, lenChaine) = self._FormateTEN(pElement)
        elif pElement['TYPE'] == 'GRD':
            (chaine, lenChaine) = self._FormateGRD(pElement)
        else:
            chaine = ""
            lenChaine = 0
            print(pElement['TYPE'])
        return chaine, lenChaine, deploie

    # ---------------------------------------------------------------------------------
    def _AffChaines(self, listChaines):
        printTUI = []
        if len(listChaines) == 0:
            return printTUI
        # Si debug : affichage de la regle
        #  chaine et la longueur
        chaine = ''
        lenChaine = 0
        b, c, _, _ = listChaines[0]
        deploie = None
        if not isinstance(c, list):
            for b, c, l, d in listChaines:
                chaine += c
                lenChaine += l
                if d is not None:
                    deploie = d
            #print("DBG-cas1>",l,lenChaine)
            printTUI.append((b,self._AffLigneGaucheTexte(b, chaine, lenChaine)))
            if deploie is not None:
                chaine, lenChaine = deploie
                for num, item in enumerate(chaine):
                    printTUI.append((b,self._AffLigneGaucheTexte(b, item, lenChaine[num])))
        else:
            hauteurMax = 0
            for b, multiChaine, _, _ in listChaines:
                hauteurMax = max(hauteurMax, len(multiChaine))
            for idx in range(len(listChaines)):
                b, multiChaine, multiLenChaine, x = listChaines[idx]
                while len(multiChaine) != hauteurMax:
                    multiChaine.append(self._couleurID(' '*multiLenChaine[0], 'Normal'))
                    multiLenChaine.append(multiLenChaine[0])
                listChaines[idx] = b, multiChaine, multiLenChaine, x
            for idxHaut in range(hauteurMax):
                chaine = ""
                lenChaine = 0
                for b, multiChaine, multiLenChaine, _ in listChaines:
                    chaine += multiChaine[idxHaut]
                    lenChaine += multiLenChaine[idxHaut]
              #  print("DBG-cas2>",lenChaine)
                printTUI.append((b,self._AffLigneGaucheTexte(b, chaine, lenChaine)))
        return printTUI

    # ---------------------------------------------------------------------------------
    def _cmdSelectionDSI(self,val,valSelect,listeOptions,dsi=True):
        if dsi and val == 'd':
            valSelect = []
        elif dsi and val == 's':
            valSelect = list(range(len(listeOptions)))
        elif dsi and val == 'i':
            objInv = [x for x in list(range(len(listeOptions))) if x not in valSelect]
            valSelect = objInv

        elif isDigit(val):
            ival = int(val)
            if -1 < ival < len(listeOptions):
                if ival in valSelect:
                    valSelect.remove(ival)
                else:
                    valSelect.append(ival)
        valSelect.sort()
        return valSelect

    # ---------------------------------------------------------------------------------
    def _cmdSelectionBEPM(self,val,valSelect,listeOptions=None,intervalle=None):
        if intervalle is None:
            imin, imax, its, itx = 0, len(listeOptions)-1, 1, 1
        else:
            imin, imax, its, itx = intervalle
        if val == 'b':
            valSelect = imin
        elif val == '--':
            valSelect = int(valSelect)-itx
        elif val == '-':
            valSelect = int(valSelect)-its
        elif val == '+':
            valSelect = int(valSelect)+its
        elif val == '++':
            valSelect = int(valSelect)+itx
        elif val == 'e':
            valSelect = imax
        elif isDigit(val):
            valSelect = int(val)
        else:
            valSelect = int(valSelect)

        valSelect  = min(valSelect, imax)
        valSelect  = max(valSelect, imin)

        return valSelect

    # ---------------------------------------------------------------------------------
    def _listSelect(self,pListe,pFct):
        if len(pListe)>0:
            selections = [pFct(x) for x in pListe.split(',')]
        else:
            selections = []
        return selections

    # ---------------------------------------------------------------------------------
    def fonctLBL(self, objet, val):
        pass

    # ---------------------------------------------------------------------------------
    def fonctLST(self, objet, val):
        # Récupération de la sélection
        valSelect = self.TUI_getValeurObjet(objet,'SELECT')
        listeOptions = self.TUI_getValeurObjet(objet,'OPTIONS')

        if val != "--PAS_DE_VALEUR--":
            valSelect = self._cmdSelectionDSI(val,valSelect,listeOptions)
            self.TUI_setValeurObjet(objet,'SELECT',valSelect)
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            valeur = [self.TUI_getValeurObjet(objet,'OPTIONS')[s] for s in select]
            print(fGreen+"Valeurs actuelles :")
            for s,v in zip(select,valeur):
                print(fGreen+"   item %s, valeur '%s'"%(s,v))

#            if val == 'd':
#                valSelect = []
#            elif val == 's':
#                valSelect = list(range(len(objet['OPTIONS'])))
#            elif val == 'i':
#                objInv = select
#                select = list(range(len(objet['OPTIONS'])))
#                for ival in objInv:
#                    select.remove(ival)
#            elif isDigit(val):
#                ival = int(val)
#                if -1 < ival < len(objet['OPTIONS']):
#                    if ival in valSelect:
#                        valSelect.remove(ival)
#                    else:
#                        valSelect.append(ival)
#            select.sort()
#            if isinstance(objet['SELECT'], str) and len(objet['SELECT']) > 0 and objet['SELECT'][0] == '@':
#                variable = objet['SELECT'].replace('@', '')
#                valeur = [str(x) for x in select]
#                self.TUI_setVariable(variable, ", ".join(valeur))
#            else:
#                objet['SELECT'] = select

    # ---------------------------------------------------------------------------------
    def fonctRAD(self, objet, val):
        # Récupération de la sélection
        valSelect = self.TUI_getValeurObjet(objet,'SELECT')
        listeOptions = self.TUI_getValeurObjet(objet,'OPTIONS')

        if val != "--PAS_DE_VALEUR--":
            valSelect = self._cmdSelectionBEPM(val,valSelect,listeOptions)
            self.TUI_setValeurObjet(objet,'SELECT',valSelect)
#            if isDigit(val):
#                ival = int(val)
#                if -1 < ival < len(objet['OPTIONS']):
#                    if isinstance(objet['SELECT'], str) and len(objet['SELECT']) > 0 and objet['SELECT'][0] == '@':
#                        variable = objet['SELECT'].replace('@', '')
#                        self.TUI_setVariable(variable, val)
#                    else:
#                        objet['SELECT'] = ival
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            valeur = self.TUI_getValeurObjet(objet,'OPTIONS')[select]
            print(fGreen+"Valeur actuelle : item %s, valeur '%s'"%(select,valeur))

    # ---------------------------------------------------------------------------------
    def fonctGCB(self, objet, val, force=False):
        # Récupération de la sélection
        valSelect = self.TUI_getValeurObjet(objet,'SELECT')
        listeOptions = self.TUI_getValeurObjet(objet,'OPTIONS')

        if val != "--PAS_DE_VALEUR--":
            # Traitement
            #select = objet['SELECT']
            #variable = None
            #if isinstance(select, str) and len(select) > 0 and select[0] == '@':
            #    variable = select.replace('@', '')

            if force and val != "":
                # Si on force la valeur
                valSelect = val
                valSelect.sort()
            else:
                valSelect = self._cmdSelectionDSI(val,valSelect,listeOptions)
#                # Sinon force la valeur
#                if val == 'd':
#                    valSelect = []
#                elif val == 's':
#                    valSelect = list(range(len(listeOptions)))
#                elif val == 'i':
#                    objInv = valSelect
#                    valSelect = list(range(len(listeOptions)))
#                    for ival in objInv:
#                        valSelect.remove(ival)
#                elif isDigit(val):
#                    ival = int(val)
#                    if -1 < ival < len(objet['OPTIONS']):
#                        if ival in valSelect:
#                            valSelect.remove(ival)
#                        else:
#                            valSelect.append(ival)
#            valSelect.sort()

            # Rangement de la sélection
            self.TUI_setValeurObjet(objet,'SELECT',valSelect)

#            if isinstance(objet['SELECT'], str) and len(objet['SELECT']) > 0 and objet['SELECT'][0] == '@':
#                variable = objet['SELECT'].replace('@', '')
#                valeur = [str(x) for x in select]
#                self.TUI_setVariable(variable, ",".join(valeur))
#            else:
#                objet['SELECT'] = select
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            valeur = [self.TUI_getValeurObjet(objet,'OPTIONS')[s] for s in select]
            print(fGreen+"Valeurs actuelles :")
            for s,v in zip(select,valeur):
                print(fGreen+"   item %s, valeur '%s'"%(s,v))

    # ---------------------------------------------------------------------------------
    # Fonction de bascule de la checkbox
    def fonctCKB(self, objet, val):
        # Récupération de la sélection
        valSelect = self.TUI_getValeurObjet(objet, 'SELECT')

        if val != "--PAS_DE_VALEUR--":
            if isDigit(val):
                valSelect = 1-int(val)
        valSelect = 1-valSelect

        self.TUI_setValeurObjet(objet,'SELECT',valSelect)
        #if variable is not None:
        #    self.TUI_setVariable(variable, str(valeur))
        #else:
        #    objet['SELECT'] = valeur

    # ---------------------------------------------------------------------------------
    # Fonction de la combobox : récupère l'item
    def fonctCBX(self, objet, val):
        # Récupération de la sélection
        valSelect = self.TUI_getValeurObjet(objet,'SELECT')
        listeOptions = self.TUI_getValeurObjet(objet,'OPTIONS')

        if val != "--PAS_DE_VALEUR--":
            valSelect = self._cmdSelectionBEPM(val,valSelect,listeOptions)
            self.TUI_setValeurObjet(objet,'SELECT',valSelect)
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            valeur = self.TUI_getValeurObjet(objet,'OPTIONS')[select]
            print(fGreen+"Valeur actuelle : item %s, valeur %s"%(select,valeur))

    # ---------------------------------------------------------------------------------
    def fonctSLD(self, objet, val):
        valSelect = self.TUI_getValeurObjet(objet,'SELECT')
        (imin, imax, its, itx) = self.TUI_getValeurObjet(objet,'INTERVALLE')

        if val != "--PAS_DE_VALEUR--":
            valSelect = self._cmdSelectionBEPM(val,valSelect,intervalle=(imin, imax, its, itx))
            self.TUI_setValeurObjet(objet,'SELECT',valSelect)
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            print(fGreen+"Valeur actuelle : %s"%select)

#            if isDigit(val):
#                ival = int(val)
#                if ival < imin:
#                    ival = imin
#                elif imax < ival:
#                    ival = imax
#            else:
#                if isinstance(objet['SELECT'], str) and len(objet['SELECT']) > 0 and objet['SELECT'][0] == '@':
#                    variable = objet['SELECT'].replace('@', '')
#                    ival = int(self.TUI_getVariable(variable))
#                else:
#                    ival = int(objet['SELECT'])
#                if val == '++':
#                    ival += itx
#                elif val == '+':
#                    ival += its
#                ival  = min(ival, imax)
#                if val == '-':
#                    ival  -= its
#                elif val == '--':
#                    ival  -= itx
#                ival  = max(ival, imin)
#            if isinstance(objet['SELECT'], str) and len(objet['SELECT']) > 0 and objet['SELECT'][0] == '@':
#                variable = objet['SELECT'].replace('@', '')
#                self.TUI_setVariable(variable, ival)
#            else:
#                objet['SELECT'] = ival

    # ---------------------------------------------------------------------------------
    def fonctSPB(self, objet, val):
        valSelect = self.TUI_getValeurObjet(objet,'SELECT')
        (imin, imax, its, itx) = self.TUI_getValeurObjet(objet,'INTERVALLE')

        if val != "--PAS_DE_VALEUR--":
            valSelect = self._cmdSelectionBEPM(val,valSelect,intervalle=(imin, imax, its, itx))
            self.TUI_setValeurObjet(objet,'SELECT',valSelect)
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            print(fGreen+"Valeur actuelle : %s"%select)

#        (imin, imax, its, itx) = objet['INTERVALLE']
#        if val != "--PAS_DE_VALEUR--":
#            if isDigit(val):
#                ival = int(val)
#                if ival < imin:
#                    ival = imin
#                elif imax < ival:
#                    ival = imax
#            else:
#                if isinstance(objet['SELECT'], str) and len(objet['SELECT']) > 0 and objet['SELECT'][0] == '@':
#                    variable = objet['SELECT'].replace('@', '')
#                    ival = int(self.TUI_getVariable(variable))
#                else:
#                    ival = int(objet['SELECT'])
#                if val == '++':
#                    ival += itx
#                elif val == '+':
#                    ival += its
#                ival  = min(ival, imax)
#                if val == '-':
#                    ival  -= its
#                elif val == '--':
#                    ival  -= itx
#                ival  = max(ival, imin)
#            if isinstance(objet['SELECT'], str) and len(objet['SELECT']) > 0 and objet['SELECT'][0] == '@':
#                variable = objet['SELECT'].replace('@', '')
#                self.TUI_setVariable(variable, ival)
#            else:
#                objet['SELECT'] = ival

    # ---------------------------------------------------------------------------------
    def fonctEDT(self, objet, val):
        if val != "--PAS_DE_VALEUR--":
            self.TUI_setValeurObjet(objet,'SELECT',val)
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            print(fGreen+"Valeur actuelle : %s"%select)

    # ---------------------------------------------------------------------------------
    def fonctZED(self, objet, val):
        if val != "--PAS_DE_VALEUR--":
            self.TUI_setValeurObjet(objet,'SELECT',val)
        else:
            select = self.TUI_getValeurObjet(objet,'SELECT')
            print(fGreen+"Valeur actuelle : %s"%select)

    # ---------------------------------------------------------------------------------
    def fonctBTN(self, objet, val):
        pass

    # ---------------------------------------------------------------------------------
    def fonctSPL(self, pObjet, val):
        if val != "--PAS_DE_VALEUR--":
            actif = val
        else:
            actif = not self.TUI_getValeurObjet(pObjet,'SPLTAG')
        pSplitter = self.TUI_getValeurObjet(pObjet,'SPL')

        for _, vObjet in self.widgets.items():
            if 'SPL' in vObjet:
                if vObjet['SPL'] == pSplitter:
                    if vObjet['TYPE'] != 'SPL':
                        vObjet['SPLDEP'] = actif
                elif len(pSplitter) == 1 and vObjet['SPL'][0] == pSplitter[0]:
                    vObjet['SPLDEP'] = actif
        self.TUI_setValeurObjet(pObjet,'SPLTAG',actif)
        self.TUI_setValeurObjet(pObjet,'SELECT',1 if actif else 0)

    # ---------------------------------------------------------------------------------
    def fonctTAB(self, pObjet, val):
        # Récupération de la sélection
        valSelect = int(self.TUI_getValeurObjet(pObjet,'SELECT'))
        listeOptions = self.TUI_getValeurObjet(pObjet,'OPTIONS')

        if val != "--PAS_DE_VALEUR--":
            valSelect = int(self._cmdSelectionBEPM(val,valSelect,listeOptions))
            self.TUI_setValeurObjet(pObjet,'SELECT',valSelect)
            actif = valSelect
        else:
            select = int(self.TUI_getValeurObjet(pObjet,'SELECT'))
            valeur = self.TUI_getValeurObjet(pObjet,'OPTIONS')[select]
            print(fGreen+"Valeur actuelle : item %s, valeur %s"%(select,valeur))
            actif = select
        curTab = self.TUI_getValeurObjet(pObjet,'TAB')

        self.TUI_setValeurObjet(pObjet,'SELECT',actif)
        for _, vObjet in self.widgets.items():
            if 'TAB' in vObjet and vObjet['TAB'][0] == curTab[0] and len(vObjet['TAB']) == 2:
                vObjet['TABVIS'] = vObjet['TAB'][1] == actif

    # ---------------------------------------------------------------------------------
    def fonctGRD(self, objet, val):
        grille = self.TUI_getValeurObjet(objet,'SELECT')
        if val == "--PAS_DE_VALEUR--":
            return
        val = val.split(', ')
        if len(val)>=2: # au moins ligne,colonne
            if not isDigit(val[0]):
                print(fRed+"Valeur de ligne %s incorrecte : 1 à %d"%(val[0],len(grille)))
                return
            lig = int(val[0])
            if lig < 1 or lig > len(grille):
                print(fRed+"Valeur de ligne %d incorrecte : 1 à %d"%(lig,len(grille)))
                return
            if not isDigit(val[1]):
                print(fRed+"Valeur de colonne %s incorrecte : 1 à %d"%(val[0],len(grille[0])))
                return
            col = int(val[1])
            if col < 1 or col > len(grille[0]):
                print(fRed+"Valeur de colonne %d incorrecte : 1 à %d"%(col,len(grille[0])))
                return
            if len(val)==3:
                grille[lig][col]=val[2]
                self.TUI_setValeurObjet(objet,'SELECT',grille)
            else:
                print(fGreen+"Valeur actuelle : %s"%grille[lig][col])

    # ---------------------------------------------------------------------------------
    def TUI_ActionWidget(self, action):
        if action[0] in self.actionWidget:
            idObjet = self.actionWidget[action[0]]
            objet = self.widgets[idObjet]
            # if objet['TYPE'] != 'SPL' and
            if not objet['ACTIF']:
                return [None]
            if objet['TYPE'] == 'ZED' and objet['SCROLL']!=-1 and len(action) == 2:
                scroll = objet['SCROLL']
                if action[1] == "++":
                    scroll -= objet['HAUT']//2
                    action = [None]
                elif action[1] == "+":
                    scroll -= 1
                    action = [None]
                elif action[1] == "-":
                    scroll += 1
                    action = [None]
                elif action[1] == "--":
                    scroll += objet['HAUT']//2
                    action = [None]
                elif action[1] == "h":
                    scroll = 0
                    action = [None]
                elif action[1] == "b":
                    scroll = len(objet['SELECT'])-objet['HAUT']
                    action = [None]
                self.widgets[idObjet]['SCROLL'] = min(max(0,scroll),len(objet['SELECT'])-objet['HAUT'])
            if objet['TYPE'] == 'CBX' and len(action) == 2:
                if action[1] == "v":
                    self.widgets[idObjet]['DEPLOIE'] = True
                    action = [None]
                elif action[1][0] == "'":
                    if action[1][1:] in self.TUI_getValeurObjet(objet, 'OPTIONS'):
                        action[1] = '%d'%self.TUI_getValeurObjet(objet, 'OPTIONS').index(action[1][1:])
                    else:
                        self._print("L'option '%s' est inexistante dans la liste des possibles : %s"%(action[1][1:],self.TUI_getValeurObjet(objet, 'OPTIONS')),"Alert")
                        action = [action[0],"--PAS_DE_VALEUR--"]
            if objet['TYPE']=='GRD' and objet['MODIFIABLE'] and len(action)>1:
                #print("DBG>",self.TUI_getValeurObjet(objet, 'SELECT'))
                grille = self.TUI_getValeurObjet(objet, 'SELECT')
                if action[1]=='al' and len(action)>=2:
                    nLigne = [""]*len(grille[0])
                    if len(action)==3:
                        nLigne[0] = str(action[2])
                    grille.append(nLigne)
                    self.TUI_setValeurObjet(objet, 'SELECT', grille)
                elif action[1]=='il' and len(action)>=3:
                    if action[2].isdigit():
                        ligne = int(action[2])
                        if 1<=ligne<=len(grille):
                            nGrille = []
                            for iLigne,vLigne in enumerate(grille):
                                if iLigne==ligne:
                                    nLigne = [""]*len(grille[0])
                                    if len(action)==4:
                                        nLigne[0] = str(action[3])
                                    nGrille.append(nLigne)
                                nGrille.append(vLigne)
                            self.TUI_setValeurObjet(objet, 'SELECT', nGrille)
                elif action[1]=='sl':
                    if action[2].isdigit():
                        ligne = int(action[2])
                        if 1<=ligne<=len(grille):
                            nGrille = []
                            for iLigne,vLigne in enumerate(grille):
                                if iLigne!=ligne:
                                    nGrille.append(vLigne)
                            self.TUI_setValeurObjet(objet, 'SELECT', nGrille)
                elif action[1] in ['ac','ic']:
                    if action[1]=='ac':
                        colonne = len(grille[0])
                        entete = ""
                        if len(action)==3:
                            entete = str(action[2])
                    else: #'ic'
                        if not action[2].isdigit():
                            action = [None]
                            pass
                        colonne = int(action[2])
                        entete = ""
                        if len(action)==4:
                            entete = str(action[3])
                    for iLigne,vLigne in enumerate(grille):
                        if iLigne==0:
                            vLigne.insert(colonne,entete)
                        else:
                            vLigne.insert(colonne,"")
                        grille[iLigne] = vLigne
                    self.TUI_setValeurObjet(objet, 'SELECT', grille)
                elif action[1]=='sc':
                    if action[2].isdigit():
                        colonne = int(action[2])
                        if 1<=colonne<=len(grille[0]):
                            for iLigne,vLigne in enumerate(grille):
                                nLigne = []
                                for iCellule,vCellule in enumerate(vLigne):
                                    if iCellule!=colonne:
                                        nLigne.append(vCellule)
                                grille[iLigne] = nLigne
                            self.TUI_setValeurObjet(objet, 'SELECT', grille)
                if action[1] in ['al','il','sl','ac','ic','sc']:
                    action = [None]
                #print("DBG>",self.TUI_getValeurObjet(objet, 'SELECT'))
            if objet['TYPE'] in ['CBX','GCB','LST','RAD'] and objet['MODIFIABLE'] and len(action)==3:
                if action[1]=='a':
                    item = action[2]
                    options = self.TUI_getValeurObjet(objet, 'OPTIONS')
                    if item not in options:
                        options.append(item)
                        if objet['TYPE'] in ['CBX','RAD']:
                            self.TUI_setValeurObjet(objet, 'SELECT', len(options)-1)
                        elif objet['TYPE']in ['GCB','LST']:
                            icourant = self.TUI_getValeurObjet(objet, 'SELECT')
                            icourant.append(len(options)-1)
                            self.TUI_setValeurObjet(objet, 'SELECT', icourant)
                    action = [None]
                elif action[1]=='s':
                    options = self.TUI_getValeurObjet(objet, 'OPTIONS')
                    if action[2].isdigit():
                        item = int(action[2])
                        if 0<int(action[2])<len(options):
                            icourant = self.TUI_getValeurObjet(objet, 'SELECT')
                            options.remove(options[item])
                            if objet['TYPE'] in ['CBX','RAD'] and icourant==len(options):
                                self.TUI_setValeurObjet(objet, 'SELECT', icourant-1)
                            elif objet['TYPE'] in ['GCB','LST'] and item in icourant:
                                icourant.remove(item)
                                self.TUI_setValeurObjet(objet, 'SELECT', icourant)
                                self.TUI_setValeurObjet(objet, 'OPTIONS', options)
                    action = [None]
                #print("DBG>",self.TUI_getValeurObjet(objet, 'SELECT'))
                #print("DBG>",self.TUI_getValeurObjet(objet, 'OPTIONS'))
            if action[0] is not None:
                commande = 'self.fonct%s'%objet['TYPE']
                eval(commande + "(objet, '%s')"%(', '.join(action[1:])))
                if objet['TYPE'] == 'CBX':
                    self.widgets[idObjet]['DEPLOIE'] = False
                    if action[1] in ['+','-','e']:
                        action[1] = str(self.widgets[idObjet]['SELECT'])
        return action

    # ---------------------------------------------------------------------------------
    def TUI_CollapseTabs(self, pCollapse):
        for _, widget in self.widgets.items():
            if widget['TYPE'] == 'SPL':
                self.fonctSPL(widget, not pCollapse)

    # ---------------------------------------------------------------------------------
    def TUI_CollapseTab(self, pWidget, pCollapse):
        if pWidget['TYPE'] == 'SPL':
            self.fonctSPL(pWidget, not pCollapse)

    # ---------------------------------------------------------------------------------
    def TUI_ActiveTab(self, pWidget, pActive):
        if pWidget['TYPE'] == 'TAB':
            self.fonctTAB(pWidget, pActive)

    # ---------------------------------------------------------------------------------
    def TUI_Rafraichir(self):
        if self.debug:
            self._print(" > Largeur : %d"%self.largeur)
            self._print(" > Marge   : %d"%self.marge)
            self._print(" > Espace  : %d"%self.espaceInterieur)
            regle1 = "|         1         2         3         4         5         6         7         8         9         10        11        12        13        14        15        16"
            regle2 = "|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|1"
            regle3 = "|         1         2         3         4         5         6         7         8         9         10        11        12        13        14        15        16"
            regle4 = "|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|123456789|1"
            print(regle1[:(self.largeur + 1)]+'|')
            print(regle2[:(self.largeur + 1)]+'|>Largeur')
            print("  "+regle3[:(self.espaceInterieur + 1)]+'|')
            print("  "+regle4[:(self.espaceInterieur + 1)]+'|>Espace')

        # déclaration de l'écran TUI : printTUI
        # composé de tuplets : ( bloc, ligne à afficher )
        printTUI = []

        # 1- Ajout de l'entete :
        #     Affichage de la bordure haute
        printTUI.append((None,self._AffLigneSeparateur('\u250F', '\u2501', '\u2513')))
        #     Affichage du titre et de la version
        printTUI.append((None,self._AffLigneCentrerTexte("%s %s"%(self.appliTUI['TITRE'], self.appliTUI['VERSION']))))
        #     Affichage de la separation Titre/Version vs Corps
        printTUI.append((None,self._AffLigneSeparateur('\u2523', '\u2501', '\u252B')))

        # 2- Boucle sur les lignes d'elements
        hauteur = 3 + 1 # 3 entete + 1 fond
        for numLig in range(self.maxLignes):
            if numLig in self.table:
                ligne = self.table[numLig]
                chaines = []
                sommeLenChaine = 0
                # recolte des éléments visibles
                for numElem, _ in enumerate(ligne):
                    pElement = self.widgets[ligne[numElem]]
                    #print("DBG-ligne>",ligne,pElement['TYPE'])
                    if "CONDVIS" in pElement:
                        condition, valeurs = pElement['CONDVIS']
                        condAction = False
                        if condition in self.actionWidget:
                            condAction = str(self.TUI_getValeurParAction(condition, 'SELECT')) in valeurs and\
                                           self.TUI_getValeurParAction(condition, 'VISIBLE')
                        elif condition.replace('@', '') in self.appliTUI['VARIABLES']:
                            condition = condition.replace('@', '')
                            condAction = str(self.TUI_getVariable(condition)) in valeurs  # and self.TUI_getVariable(condition)
                        pElement['VISIBLE'] = condAction  # or (self.TUI_getVariable(condition) in valeurs)
                    if (pElement['VISIBLE']==True or (isinstance(pElement['VISIBLE'],list) and True in pElement['VISIBLE'])) and pElement['SPLDEP'] and pElement['TABVIS']:
                        pElement['OFFSETDEPL'] = sommeLenChaine
                        chaine, lenChaine, deploie = self._FormateElement(pElement)
                        if isinstance(lenChaine, list):
                            if len(lenChaine) > 0:
                                sommeLenChaine += lenChaine[0]
                        else:
                            sommeLenChaine += lenChaine
                        chaines.append((pElement['COLON'],chaine, lenChaine, deploie))
                # affichage des éléments visibles
                printTUI.extend(self._AffChaines(chaines))

        printTUI.append((None,None))

        listeBlocs = {'flag':False, 0:[], 1:[], 2:[]}
        for bloc,ligne in printTUI:
            #print("DBG>",bloc,ligne,listeBlocs['flag'])
            if bloc in [0,None]:
                if listeBlocs['flag']:
                    #print(len(listeBlocs[1]),len(listeBlocs[2]))
                    while len(listeBlocs[2])<len(listeBlocs[1]):
                        pElement={'COLON':2,'TYPE': 'SEP', 'TEXTE': ' ', 'ACTIF': True, 'LARG': 0, 'OFFSET': 0, 'VISIBLE': True}
                        chaine, lenChaine, deploie = self._FormateElement(pElement)
                        chaines = [(2,chaine, lenChaine, deploie)]
                        listeBlocs[2].append(self._AffChaines(chaines)[0][1])
                    while len(listeBlocs[1])<len(listeBlocs[2]):
                        pElement={'COLON':1,'TYPE': 'SEP', 'TEXTE': ' ', 'ACTIF': True, 'LARG': 0, 'OFFSET': 0, 'VISIBLE': True}
                        chaine, lenChaine, deploie = self._FormateElement(pElement)
                        chaines = [(1,chaine, lenChaine, deploie)]
                        listeBlocs[1].append(self._AffChaines(chaines)[0][1])
                    #print(len(listeBlocs[1]),len(listeBlocs[2]))
                    for iligne in range(len(listeBlocs[1])):
                        print("%s%s"%(listeBlocs[1][iligne],listeBlocs[2][iligne]))
                        hauteur += 1
                if ligne is not None:
                    print(ligne)
                    hauteur += 1
                listeBlocs = {'flag':False, 0:[], 1:[], 2:[]}
            else:
                listeBlocs['flag']=True
                if bloc!=0:
                    listeBlocs[bloc].append(ligne)

        # Complément de hauteur
        if self.hauteur is not None:
            while hauteur<self.hauteur:
                print(self._AffLigneCentrerTexte(""))
                hauteur += 1

        # Affichage de la bordure basse
        print(self._AffLigneSeparateur('\u2517', '\u2501', '\u251B',True))

    # ---------------------------------------------------------------------------------
    def TUI_Enregistrement(self, pFichier=None):
        # tester les cas d'erreurs
        # stop/reprise !r! quand aucun fichier n'est défini
        if pFichier is None and not self.enregistrement:
            self._print("No file is specified. Use !r:<file> to open one.", "Warning")
            return
        # création !r:<file> quand un fichier est défini
        if pFichier is not None and self.fichierEnregistrement is not None:
            self._print("The file %s is open. Close it with !r!."%self.fichierEnregistrement, "Warning")
            return
        if pFichier is not None:
            self.fichierEnregistrement = pFichier
            with open(self.fichierEnregistrement, 'w', encoding="utf-8") as f:
                f.write("; ================================================ \n")
        self.enregistrement  = not self.enregistrement

    # ---------------------------------------------------------------------------------
    def TUI_Information(self, action):
        if action[1] in self.aides:
            texte = self.TUI_getValeurParAction(action[1], 'TEXTE')
            typew = self.TUI_getValeurParAction(action[1], 'TYPE')
            aideOptionCBX = None
            while texte != '' and texte[-1] == ' ':
                texte = texte[:-1]
            texteAide = self.aides[action[1]]
            if typew == 'CBX':
                optionCBX = self.TUI_getValeurParAction(action[1], 'OPTIONS')
                optionCBX = optionCBX[int(self.TUI_getValeurParAction(action[1], 'SELECT'))]
                if texteAide[1] is not None:
                    aideOptionCBX = texteAide[1][int(self.TUI_getValeurParAction(action[1], 'SELECT'))]
                texteAide = texteAide[0]
            # recherche de l'aide d'une option
            aideOption = False
            if len(action) == 3:
                aideOption = None
                if not isinstance(texteAide, str):
                    texteAide, aideOption  = texteAide
                    aideOption  = aideOption[int(action[2])]
                    option = self.TUI_getValeurParAction(action[1], 'OPTIONS')
                    option = option[int(action[2])]
            else:
                if not isinstance(texteAide, str):
                    texteAide, _  = texteAide
            if texte != '':
                self._print("%s: %s"%(texte, texteAide), "Action")
            else:
                self._print("%s"%texteAide, "Action")
            if aideOption != False:
                if aideOption is not None:
                    self._print("     option '%s': %s"%(option, aideOption), "Action")
                elif aideOptionCBX:
                    self._print("    current '%s': %s"%(optionCBX, aideOptionCBX), "Action")
                else:
                    self._print("Sorry no description available for this item.", "Normal")

    # ---------------------------------------------------------------------------------
    def TUI_ListeActions(self,file):
        fichierLaTeX=file
        if fichierLaTeX=="--PAS_DE_VALEUR--":
            fichierLaTeX="commandList.tex"
        with open(fichierLaTeX, 'w', encoding="utf-8") as f:
            f.write("\\documentclass[11pt,a4paper]{article}\n")
            f.write("\\usepackage{geometry}\n")
            f.write("\\usepackage{longtable}\n")
            f.write("\\begin{document}\n")
            f.write("\\newgeometry{left=1cm, bottom=1.5cm, top=2cm, right=1cm}\n")
            f.write("{\\LARGE \\textbf{List of commands for %s %s}}\\\\\n\n"%(self.appliTUI['TITRE'].replace('_','\\_'), self.appliTUI['VERSION'].replace('_','\\_')))
            f.write("\\begin{longtable}{|p{2.5cm}|p{4cm}|p{11cm}|}\n")
            f.write("\\hline\nAction & Item & Description\\\\\n\\hline\n")
            for action in self.actions:
                nomWidget = self.actions[action]
                widget = self.TUI_getWidgetParNom(nomWidget)
                element = widget['TEXTE']
                aide = ""
                if 'OPTIONS' in widget:
                    if isinstance(widget['AIDE'],str):
                        aide = widget['AIDE']
                        f.write("%s & %s & %s\\\\\n"%(action,element.replace('_','\\_'),aide.replace('_','\\_')))
                    else:
                        aide,listeAideOptions = widget['AIDE']
                        f.write("%s & %s & %s\\\\\n"%(action,element,aide))
                        for eoption,voption in enumerate(widget['OPTIONS']):
                            f.write("%s:%d & %s & %s\\\\\n"%(action, eoption, voption.replace('_', '\\_'), listeAideOptions[eoption].replace('_', '\\_') if listeAideOptions is not None else ""))
                else:
                    aide = widget['AIDE']
                    f.write("%s & %s & %s\\\\\n"%(action, element.replace('_', '\\_'), aide.replace('_', '\\_')))
            f.write("\\hline\n\\end{longtable}\n\\end{document}\n")

        if os.system("which latex") == 0:
            os.system("pdflatex -interaction nonstopmode commandList.tex > /dev/null")
            os.system("rm commandList.log commandList.aux> /dev/null")

    # ---------------------------------------------------------------------------------
    def recupereAction(self):
        try:
            action = input(fYellow + '? ')
        except Exception as err:
            self._print(err, "Error")
            return []
        if self.enregistrement and action[0] != '!':
            with open(self.fichierEnregistrement, 'a', encoding="utf-8") as f:
                f.write("%s\n"%action)
        return action.split(':')

    # ---------------------------------------------------------------------------------
    def TUI_Afficher(self, pAction=None):
        if self.affichageTUI:
            self.TUI_Rafraichir()
            action = self.recupereAction()
        else:
            action = pAction
        if len(action) == 1:
            action.append("--PAS_DE_VALEUR--")
        if CLAVIER:
            print("CLV > ", action)
        action = self.TUI_ActionWidget(action)
        if action[0] == "!d!":
            self.debug = not self.debug
            action = ["", "--PAS_DE_VALEUR--"]
        elif action[0] == "!p!":
            self.TUI_fixePalette()
        elif action[0] == "!p":
            if action[1] == "kw":
                self.TUI_fixePalette('NoirBlanc')
            if action[1] == "y":
                self.TUI_fixePalette('Jaune')
            if action[1] == "b":
                self.TUI_fixePalette('Bleu')
            if action[1] == "yb":
                self.TUI_fixePalette('BleuJaune')
            if action[1] == "yg":
                self.TUI_fixePalette('JauneGris')
            if action[1] == "gg":
                self.TUI_fixePalette('VertGris')
            elif os.path.exists(action[1]):
                with open(action[1], 'r', encoding="utf-8") as f:
                    self.palette = json.load(f)
        elif action[0] == '!cmd':
            if action[1]=="--PAS_DE_VALEUR--":
                print(fGreen+"Last command file: %s"%self.cmdLatest)
            else:
                self.TUI_ChargerCommandes(action[1])
                self.cmdLatest = action[1]
        elif action[0] == '!cmd!':
            if self.cmdLatest!="":
                self.TUI_ChargerCommandes(self.cmdLatest)
        elif action[0] == '!c!':
            self.TUI_CollapseTabs(True)
        elif action[0] == '!uc!':
            self.TUI_CollapseTabs(False)
        elif action[0] == '!i':
            self.TUI_Information(action)
        elif action[0] == '!l':
            self.TUI_ListeActions(action[1])
        elif action[0] == '!r':
            self.TUI_Enregistrement(pFichier=action[1])
        elif action[0] == '!r!':
            self.TUI_Enregistrement()
        elif action[0] == '!':
            self._print('!d! : debug')
            self._print('!i:<action> : info on element')
            self._print('!c! : collapse tabs - !uc! : uncollapse tabs')
            self._print('!p:<file> : charge palette')
            self._print('!p:kw, !p:y, !p:b, !p:yb, !p:yg, !p:gg : charge predefined palettes')
            self._print('!cmd:<file> : execute commands from file - !cmd! : execute last command file')
            self._print('!r:<file> : record commands on file - !r! : pause/stop or restart recording')
            self._print('!l[:<file>] : record list of actions and their definitions in a file <file> or in local "./commandList.tex". Compile it if LaTeX is installed.')
        elif action[0] == self.quitter:
            if self.fichierEnregistrement is not None:
                with open(self.fichierEnregistrement, 'a', encoding="utf-8") as f:
                    f.write("; ================================================ \n%s\n"%self.quitter)
        self.affichageTUI = len(self.listeCommandes) == 0
        return action

    # ---------------------------------------------------------------------------------
    def TUI_getValeurParAction(self, pAction, pPropriete, pRang=None):
        idObjet = self.actionWidget[pAction]
        objet = self.widgets[idObjet]
        return self.TUI_getValeurObjet(objet, pPropriete, pRang)

    # ---------------------------------------------------------------------------------
    def TUI_getValeurParId(self, pIdObjet, pPropriete, pRang=None):
        objet = self.widgets[pIdObjet]
        return self.TUI_getValeurObjet(objet, pPropriete, pRang)

    # ---------------------------------------------------------------------------------
    def TUI_getValeurParNom(self, pNomWidget, pPropriete, pRang=None):
        idObjet = self.indexWidgets[pNomWidget]
        objet = self.widgets[idObjet]
        return self.TUI_getValeurObjet(objet, pPropriete, pRang)

    # ---------------------------------------------------------------------------------
    def TUI_getValeurObjet(self, pObjet, pPropriete, pRang=None):
        if not pPropriete in pObjet:
            return None
        if isinstance(pObjet[pPropriete], list) and pRang is not None:
            if pRang < len(pObjet[pPropriete]):
                return pObjet[pPropriete][pRang]
            return pObjet[pPropriete][0]
        if isinstance(pObjet[pPropriete], str) and len(pObjet[pPropriete]) > 0 and pObjet[pPropriete][0] == '@':
            variable = pObjet[pPropriete].replace('@', '')
#            if pPropriete=='SELECT' and pObjet['TYPE'] in ['LST','CKB','RAD','TAB']:
#                return self.appliTUI['VARIABLES'][variable]
           # print(variable,self.appliTUI['VARIABLES'][variable],type(self.appliTUI['VARIABLES'][variable]))
            return self.appliTUI['VARIABLES'][variable]
        #print(pObjet['TYPE'],pPropriete,pObjet[pPropriete],type(pObjet[pPropriete]))
        return pObjet[pPropriete]

    # ---------------------------------------------------------------------------------
    def TUI_setValeurParAction(self, pAction, pPropriete, pValeur, pRang=None):
        idObjet = self.actionWidget[pAction]
        objet = self.widgets[idObjet]
        self.TUI_setValeurObjet(objet, pPropriete, pValeur, pRang)

    # ---------------------------------------------------------------------------------
    def TUI_setValeurParId(self, pIdObjet, pPropriete, pValeur, pRang=None):
        objet = self.widgets[pIdObjet]
        self.TUI_setValeurObjet(objet, pPropriete, pValeur, pRang)

    # ---------------------------------------------------------------------------------
    def _setVisibleSPL(self,pSPL,pValeur):
        for _, vNom in self.indexWidgets.items():
            if 'SPL' in self.widgets[vNom] and self.widgets[vNom]['SPL']==pSPL:
                self.widgets[vNom]['VISIBLE']=pValeur

    # ---------------------------------------------------------------------------------
    def _setVisibleUnTAB(self,pObjet,pValeur,pRang):
        for _, vNom in self.indexWidgets.items():
            if 'TAB' in self.widgets[vNom]:
                if self.widgets[vNom]['TAB']==[pObjet['TAB'][0],str(pRang)]:
                    self.widgets[vNom]['VISIBLE']=pValeur
        pObjet['VISIBLE'][pRang] = pValeur

    # ---------------------------------------------------------------------------------
    def _setVisibleTAB(self,pObjet,pValeur,pRang=None):
        if pRang is not None:
            self._setVisibleUnTAB(pObjet,pValeur,pRang)
        else:
            for rang,_ in enumerate(pObjet['OPTIONS']):
                self._setVisibleUnTAB(pObjet,pValeur,rang)

    # ---------------------------------------------------------------------------------
    def TUI_setValeurParNom(self, pNomWidget, pPropriete, pValeur, pRang=None):
        idObjet = self.indexWidgets[pNomWidget]
        objet = self.widgets[idObjet]
        self.TUI_setValeurObjet(objet, pPropriete, pValeur, pRang)

    # ---------------------------------------------------------------------------------
    def TUI_setValeurObjet(self, pObjet, pPropriete, pValeur, pRang=None):
        if pObjet['TYPE']=="ZED" and pPropriete=="SELECT":
            pObjet[pPropriete] = self._FormateSelectZED(pObjet,pValeur)
        elif pObjet['TYPE']=="SPL" and pPropriete=="VISIBLE":
            self._setVisibleSPL(pObjet['SPL'],pValeur)
        elif pObjet['TYPE']=="TAB" and pPropriete=="VISIBLE":
            self._setVisibleTAB(pObjet,pValeur,pRang)
        elif pPropriete=="COUL":
            pObjet[pPropriete] = self._getCouleur(pValeur)
        elif isinstance(pObjet[pPropriete], list) and pRang is not None:
            pObjet[pPropriete][pRang] = pValeur
        elif isinstance(pObjet[pPropriete], str) and len(pObjet[pPropriete]) > 0 and pObjet[pPropriete][0] == '@':
            variable = pObjet[pPropriete].replace('@', '')
            self.appliTUI['VARIABLES'][variable] = pValeur
        else:
            pObjet[pPropriete] = pValeur

    # ---------------------------------------------------------------------------------
    def TUI_getAideParAction(self, pAction):
        return self.aides[pAction]

    # ---------------------------------------------------------------------------------
    def TUI_getAideParNom(self, pNomWidget):
        action = self.TUI_getValeurParNom(pNomWidget, 'ACTION')
        return self.TUI_getAideParAction(action)

    # ---------------------------------------------------------------------------------
    def TUI_setAideParAction(self, pAction, pTexteAide):
        self.aides[pAction] = pTexteAide

    # ---------------------------------------------------------------------------------
    def TUI_setAideParNom(self, pNomWidget, pTexteAide):
        action = self.TUI_getValeurParNom(pNomWidget, 'ACTION')
        self.aides[action] = pTexteAide

    # ---------------------------------------------------------------------------------
    def TUI_appendValeur(self, pNomWidget, pPropriete, pValeur):
        valcourante = self.TUI_getValeurParNom(pNomWidget, pPropriete)
        if valcourante is None:
            valcourante = []
        valcourante.append(pValeur)
        self.TUI_setValeurParNom(pNomWidget, pPropriete, valcourante)

    # ---------------------------------------------------------------------------------
    def TUI_getWidgetParNom(self, pNomWidget):
        idObjet = self.indexWidgets[pNomWidget]
        objet = self.widgets[idObjet]
        return objet

    # ---------------------------------------------------------------------------------
    def TUI_getWidgetParAction(self, pAction):
        idObjet = self.actionWidget[pAction]
        objet = self.widgets[idObjet]
        return objet

    # ---------------------------------------------------------------------------------
    def TUI_getWidgetParId(self, pIdWidget):
        objet = self.widgets[pIdWidget]
        return objet

    # ---------------------------------------------------------------------------------
    def TUI_getIndexItem(self, pNomWidget, pPropriete, pValeur):
        valcourante = self.TUI_getValeurParNom(pNomWidget, pPropriete)
        if isinstance(valcourante, list):
            index = valcourante.index(pValeur)
        else:
            index = None
        return index

# ---------------------------------------------------------------------------------
def TUI_boucle(pMenuTUI,pInitialisationTUI=None,pFichierCommandes=None):
    pMenuTUI.tui.TUI_ChargeConfig()

    if pInitialisationTUI is not None:
        pInitialisationTUI()
    if pFichierCommandes is not None:
        pMenuTUI.tui.TUI_ChargerCommandes(pFichierCommandes)
    # Initialisation des variables
    action = "go!"
    # On boucle tant que l'action est l'une du menu
    while action[0] != pMenuTUI.tui.quitter:
        # Affichage du menu et recupération d'une action
        if len(pMenuTUI.tui.listeCommandes) > 0:
            action = pMenuTUI.tui.TUI_ExtraitCommande()
        action = pMenuTUI.tui.TUI_Afficher(action)
        # Execution des actions
        if action[0] in pMenuTUI.tui.actions.keys():
            commande = 'pMenuTUI.appli'+action[0]
            if not hasattr(pMenuTUI, 'appli'+action[0]):
                if pMenuTUI.tui.debug:
                    print("Pas de fonction %s."%commande+"('%s')"%(','.join(action[1:])))
            else:
                eval(commande+"('%s')"%(','.join(action[1:])))

    pMenuTUI.tui.TUI_SauvegardeConfig()

# ===============================================================================
# end of file
