#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================
import os, glob, json, tarfile, copy
import shutil

from kaasrc.communs import colPrint
import kaasrc.communs

# check if we can compile latex reports
print("LaTeX presence check for possible report compilation:")
ISLATEX = os.system("which latex") == 0

# -------------------------------------------------------------------------------
# astuce pour raccourcir le nom de la data lorsqu'il est long
def shortenFilename(filename, max_length=25):
    if len(filename) <= max_length:
        return filename
    half_length = (max_length - 3) // 2
    return "%s{\\dots}%s"%(filename[:half_length], filename[-half_length:])

# -------------------------------------------------------------------------------
## Function to built a tar.gz archive
def builtTGZ(pResultSavedOn, pLongRapport=0):
    # compression des données produites (dataPlot)
    ici = os.getcwd()
    os.chdir(os.path.join(pResultSavedOn, '..'))
    reperToTar = os.path.basename(pResultSavedOn)
    nomtar = "%s.tgz"%reperToTar
    with tarfile.open(nomtar, "w:gz") as tarHandle:
        for root, _, files in os.walk(reperToTar):
            for file in files:
                if '.pdf' not in file:
                    tarHandle.add(os.path.join(root, file))
    repertReport = os.path.join(pResultSavedOn, "..", nomtar)
    print("   .Archive of the report generated in %s"%os.path.abspath(repertReport))
    print("       contains %d lines."%pLongRapport)
    os.chdir(ici)

# ---------------------------------------------------------------------------
def ajouterTabLaTex(pTailleCol, pNbColLatex):

    texte  = "\\begin{tabular}{%s}\n\\hline\n"%('C{%d}'%pTailleCol * pNbColLatex)

    for tag in ["NOMDATA", "NUMDATA", "GDTRUTH", "IMADATA", "INFEREN", "CLSDATA", "SCODATA", "EXPLICA", "EXPDATA", "MINDATA", "MAXDATA", "ERRDATA"]:
        sep = '&'
        for i in range(pNbColLatex):
            if i == pNbColLatex - 1:
                sep = '\\\\'
            texte += "$%s%d$ %s\n"%(tag, i + 1, sep)
    texte += "\hline\n\\end{tabular}\n\n"
    texte += "$DATA$"
    return texte

# ---------------------------------------------------------------------------
def rapporterDataFullReport(pRapport, pTexte, pNumCol, pNbColLatex, pDataPlot, pDataSuffixes=None, pInferJson=None, pExplJson=None, pRepertImages=None, pTitleData=None):
    tailleCol = 170 / pNbColLatex

    if pDataSuffixes is None:
        pDataSuffixes = {'--i_': None, '--c_': None, '--s_': None}
    if pInferJson is None:
        pInferJson = {"classe": None, "score": None, "inferenceVSverite": None}
    if pExplJson is None:
        pExplJson = {"min": None, "max": None}

    if pNumCol == 1:
        pTexte = ajouterTabLaTex(tailleCol, pNbColLatex)

    nomfichier = os.path.basename(pDataPlot).replace('.png', '').replace(' ', '')
    nom = nomfichier

    if pTitleData:
        nblig = len(pTitleData.split('\\\\'))
        pTexte = pTexte.replace('$NOMDATA%d$'%pNumCol, "\\mnp{%d}{%d}{\\footnotesize{\\cellcolor{brown!25} %s}}"%(nblig, tailleCol, pTitleData.replace('_', '\\_')))
    else:
        nblig = len(nom.split('\\\\'))
        pTexte = pTexte.replace('$NOMDATA%d$'%pNumCol, "\\mnp{%d}{%d}{\\footnotesize{\\cellcolor{brown!25} %s}}"%(nblig, tailleCol, nom.replace('_', '\\_')))
    # numero de l'item
    if pDataSuffixes['--i_'] is None:
        pTexte = pTexte.replace('$NUMDATA%d$'%pNumCol, "")
    else:
        pTexte = pTexte.replace('$NUMDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{brown!25} Item: %s}}"%(tailleCol, pDataSuffixes['--i_']))
    # recherche de l'inférence et vérité
    inferenceVSverite = None
    if not isinstance(pInferJson['inferenceVSverite'], list):
        inferenceVSverite = pInferJson['inferenceVSverite']
    elif pDataSuffixes['--i_'] is not None:
        inferenceVSverite = pInferJson['inferenceVSverite']
    if inferenceVSverite is not None and pInferJson['verite'] is not None:
        pTexte = pTexte.replace('$GDTRUTH%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{brown!25} Gd Truth: %s}}"%(tailleCol, pInferJson['verite'].replace('_', '\\_')))
    else:
        pTexte = pTexte.replace('$GDTRUTH%d$'%pNumCol, "")
    # image
    if pRepertImages:
        pTexte = pTexte.replace('$IMADATA%d$'%pNumCol, "\\imaw{%d}{%s/%s}"%(tailleCol, pRepertImages, nom))
    else:
        pTexte = pTexte.replace('$IMADATA%d$'%pNumCol, "\\imaw{%d}{%s}"%(tailleCol, nom))
    # bloc d'inférence
    classeCheck = (not isinstance(pInferJson['classe'], list) and pInferJson['classe'] is not None) or (isinstance(pInferJson['classe'], list) and pDataSuffixes['--i_'] is not None)
    scoreCheck = (not isinstance(pInferJson['score'], list) and pInferJson['score'] is not None) or (isinstance(pInferJson['score'], list) and pDataSuffixes['--i_'] is not None)
    if classeCheck or scoreCheck:
        pTexte = pTexte.replace('$INFEREN%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} \\textbf{inference}}}"%tailleCol)
    else:
        pTexte = pTexte.replace('$INFEREN%d$'%pNumCol, "")
    # classe d'inférence
    if pInferJson['classe'] is not None and isinstance(pInferJson['classe'], list):
        if pDataSuffixes['--i_'] is not None:
            classe = pInferJson['classe'][int(pDataSuffixes['--i_'])]
            pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Classed: %s}}"%(tailleCol, classe.replace('_', '\\_')))
        else:
            # The class of the item can not be found; the item itself is undefined!
            pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "")
    elif pInferJson['classe'] is not None:
        pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Classed: %s}}"%(tailleCol, pInferJson['classe'].replace('_', '\\_')))
    else:
        pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "")
    # score d'inférence
    if pInferJson['score'] is not None and isinstance(pInferJson['score'], list):
        if pDataSuffixes['--i_'] is not None:
            score = pInferJson['score'][int(pDataSuffixes['--i_'])]
            pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Score: %4.3f}}"%(tailleCol, score))
        else:
            # The score of the item can not be found; the item itself is undefined!
            pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "")
    elif pInferJson['score'] is not None:
        pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Score: %4.3f}}"%(tailleCol, pInferJson['score']))
    else:
        pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "")
    # classe d'explication
    if pDataSuffixes['--c_'] is not None or pExplJson['min'] is not None or pExplJson['max'] is not None:
        pTexte = pTexte.replace('$EXPLICA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} \\textbf{explanation}}}"%tailleCol)
    else:
        pTexte = pTexte.replace('$EXPLICA%d$'%pNumCol, "")
    # min d'explication
    if pExplJson['min'] is not None:
        pTexte = pTexte.replace('$MINDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} Min: %s}}"%(tailleCol, pExplJson['min']))
    else:
        pTexte = pTexte.replace('$MINDATA%d$'%pNumCol, "")
    # max d'explication
    if pExplJson['max'] is not None:
        pTexte = pTexte.replace('$MAXDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} Max: %s}}"%(tailleCol, pExplJson['max']))
    else:
        pTexte = pTexte.replace('$MAXDATA%d$'%pNumCol, "")
    if pDataSuffixes['--c_'] is not None:
        pTexte = pTexte.replace('$EXPDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} Explained: %s}}"%(tailleCol, pDataSuffixes['--c_'].replace('_', '\\_')))
    else:
        pTexte = pTexte.replace('$EXPDATA%d$'%pNumCol, "")
    # erreur de prediction
    if inferenceVSverite is not None and inferenceVSverite is False:
        pTexte = pTexte.replace('$ERRDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{red!75} Inference error!}}"%(tailleCol))
    else:
        pTexte = pTexte.replace('$ERRDATA%d$'%pNumCol, "")

    pNumCol += 1
    if pNumCol > pNbColLatex:
        pRapport = pRapport.replace("$DATA$", pTexte)
        pNumCol = 1

    return pRapport, pTexte, pNumCol

# ---------------------------------------------------------------------------
## End of reporting
# @param pRapport : full report
# @param pTexte : text to clean
# @param pNbCol : number of columns filled
# @param pNbColTotal : number of columns in the table
# @return pRapport, pTexte, pNbCol
def finRapporterDataFullReport(pRapport, pTexte, pNbCol, pNbColTotal):
    # Fin d'écriture des données
    for n in range(pNbCol, pNbColTotal + 1):
        pTexte = pTexte.replace('$NOMDATA%d$'%n, "")
        pTexte = pTexte.replace('$NUMDATA%d$'%n, "")
        pTexte = pTexte.replace('$GDTRUTH%d$'%n, "")
        pTexte = pTexte.replace('$IMADATA%d$'%n, "")
        pTexte = pTexte.replace('$CLSDATA%d$'%n, "")
        pTexte = pTexte.replace('$SCODATA%d$'%n, "")
        pTexte = pTexte.replace('$EXPDATA%d$'%n, "")
        pTexte = pTexte.replace('$MINDATA%d$'%n, "")
        pTexte = pTexte.replace('$MAXDATA%d$'%n, "")
        pTexte = pTexte.replace('$ERRDATA%d$'%n, "")
        pTexte = pTexte.replace('$INFEREN%d$'%n, "")
        pTexte = pTexte.replace('$EXPLICA%d$'%n, "")

    if pNbCol > 1:
        pRapport = pRapport.replace("$DATA$", pTexte)
        pNbCol = 1

    return pRapport, pTexte, pNbCol

# ---------------------------------------------------------------------------
def rapporterData(pRapport, pTexte, pDirName, pDataPlot, pNumCol, pNbColLatex, pTxtDataSize="", pInferJson=None, pExplJson=None):
    tailleCol = 180 / pNbColLatex

    # Création du dictionnaire des suffixes
    nom = os.path.splitext(os.path.basename(pDataPlot))[0]
    dataSuffixes = {'--i_': None, '--c_': None, '--s_': None}
    for key, _ in dataSuffixes.items():
        if key in nom:
            dataSuffixes[key] = nom.split(key)[1].split('--')[0]

    if pInferJson is None:
        pInferJson = {"classe": None, "score": None, "inferenceVSverite": None}
    if pExplJson is None:
        pExplJson = {"min": None, "max": None}

    if pNumCol == 1:
        pTexte = ajouterTabLaTex(tailleCol, pNbColLatex)

    nomfichier = os.path.join(pDirName, os.path.basename(pDataPlot).replace('.png', '').replace(' ', ''))
    nom = nomfichier
    for sep in ['--i_', '--c_', '--s_']:
        nom = nom.split(sep)[0]

    pTexte = pTexte.replace('$NOMDATA%d$'%pNumCol, "\\mnp{2}{%d}{\\footnotesize{\\cellcolor{brown!25} \\textbf{data}\\\\%s}}"%(tailleCol, shortenFilename(nom).replace('_', '\\_')))
    # numero de l'item
    if dataSuffixes['--i_'] is not None:
        pTexte = pTexte.replace('$NUMDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{brown!25} Item: %s}}"%(tailleCol, int(dataSuffixes['--i_'])))
    else:
        pTexte = pTexte.replace('$NUMDATA%d$'%pNumCol, "")
    # recherche de l'inférence et vérité
    inferenceVSverite = None
    if not isinstance(pInferJson['inferenceVSverite'], list):
        inferenceVSverite = pInferJson['inferenceVSverite']
    elif dataSuffixes['--i_'] is not None:
        inferenceVSverite = pInferJson['inferenceVSverite']
    if inferenceVSverite is not None and pInferJson['verite'] is not None:
        pTexte = pTexte.replace('$GDTRUTH%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{brown!25} Gd Truth: %s}}"%(tailleCol, pInferJson['verite'].replace('_', '\\_')))
    else:
        pTexte = pTexte.replace('$GDTRUTH%d$'%pNumCol, "")
    # image
    pTexte = pTexte.replace('$IMADATA%d$'%pNumCol, "\\imaw{%d}{%s%s.png}"%(tailleCol, nomfichier, pTxtDataSize))
    # bloc d'inférence
    classeCheck = (not isinstance(pInferJson['classe'], list) and pInferJson['classe'] is not None) or (isinstance(pInferJson['classe'], list) and dataSuffixes['--i_'] is not None)
    scoreCheck = (not isinstance(pInferJson['score'], list) and pInferJson['score'] is not None) or (isinstance(pInferJson['score'], list) and dataSuffixes['--i_'] is not None)
    if classeCheck or scoreCheck:
        pTexte = pTexte.replace('$INFEREN%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} \\textbf{inference}}}"%tailleCol)
    else:
        pTexte = pTexte.replace('$INFEREN%d$'%pNumCol, "")
    # classe d'inférence
    if pInferJson['classe'] is not None and isinstance(pInferJson['classe'], list):
        if dataSuffixes['--i_'] is not None:
            classe = pInferJson['classe'][int(dataSuffixes['--i_'])]
            pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Classed: %s}}"%(tailleCol, classe.replace('_', '\\_')))
        else:
            # The class of the item can not be found; the item itself is undefined!
            pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "")
    elif pInferJson['classe'] is not None:
        pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Classed: %s}}"%(tailleCol, pInferJson['classe'].replace('_', '\\_')))
    else:
        pTexte = pTexte.replace('$CLSDATA%d$'%pNumCol, "")
    # score d'inférence
    if pInferJson['score'] is not None and isinstance(pInferJson['score'], list):
        if dataSuffixes['--i_'] is not None:
            score = pInferJson['score'][int(dataSuffixes['--i_'])]
            pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Score: %4.3f}}"%(tailleCol, score))
        else:
            # The score of the item can not be found; the item itself is undefined!
            pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "")
    elif pInferJson['score'] is not None:
        pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{cyan!25} Score: %4.3f}}"%(tailleCol, pInferJson['score']))
    else:
        pTexte = pTexte.replace('$SCODATA%d$'%pNumCol, "")
    # bloc d'explication
    if dataSuffixes['--c_'] is not None or pExplJson['min'] is not None or pExplJson['max'] is not None:
        pTexte = pTexte.replace('$EXPLICA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} \\textbf{explanation}}}"%tailleCol)
    else:
        pTexte = pTexte.replace('$EXPLICA%d$'%pNumCol, "")
    # classe d'explication
    if dataSuffixes['--c_'] is not None:
        pTexte = pTexte.replace('$EXPDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} Explained: %s}}"%(tailleCol, dataSuffixes['--c_'].replace('_', '\\_')))
    else:
        pTexte = pTexte.replace('$EXPDATA%d$'%pNumCol, "")
    # min d'explication
    if pExplJson['min'] is not None:
        pTexte = pTexte.replace('$MINDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} Min: %s}}"%(tailleCol, pExplJson['min']))
    else:
        pTexte = pTexte.replace('$MINDATA%d$'%pNumCol, "")
    # max d'explication
    if pExplJson['max'] is not None:
        pTexte = pTexte.replace('$MAXDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{gray!25} Max: %s}}"%(tailleCol, pExplJson['max']))
    else:
        pTexte = pTexte.replace('$MAXDATA%d$'%pNumCol, "")
    # erreur de prediction
    if inferenceVSverite is not None and inferenceVSverite is False:
        pTexte = pTexte.replace('$ERRDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{red!75} Inference error!}}"%(tailleCol))
    else:
        pTexte = pTexte.replace('$ERRDATA%d$'%pNumCol, "")
#    if pInferJson['inferenceVSverite'] is False:
#        pTexte = pTexte.replace('$ERRDATA%d$'%pNumCol, "\\mnp{1}{%d}{\\footnotesize{\\cellcolor{red!75} %s}}"%(tailleCol, pInferJson['inferenceVSverite']))
#    else:
#        pTexte = pTexte.replace('$ERRDATA%d$'%pNumCol, "")

    pNumCol += 1
    if pNumCol > pNbColLatex:
        pRapport = pRapport.replace("$DATA$", pTexte)
        pNumCol = 1

    return pRapport, pTexte, pNumCol


# ---------------------------------------------------------------------------
## Writing the image data report in LaTeX
# @param pRapport : Latex report
# @param pTexte : text to report
# @param pNbCol : current column
# @param pNbColLatex : nb columns
# @return complete report
def finRapporterData(pRapport, pTexte, pNbCol, pNbColLatex):
    # Fin d'écriture des données
    for n in range(pNbCol, pNbColLatex + 1):
        pTexte = pTexte.replace('$NOMDATA%d$'%n, "")
        pTexte = pTexte.replace('$NUMDATA%d$'%n, "")
        pTexte = pTexte.replace('$GDTRUTH%d$'%n, "")
        pTexte = pTexte.replace('$IMADATA%d$'%n, "")
        pTexte = pTexte.replace('$CLSDATA%d$'%n, "")
        pTexte = pTexte.replace('$SCODATA%d$'%n, "")
        pTexte = pTexte.replace('$EXPDATA%d$'%n, "")
        pTexte = pTexte.replace('$MINDATA%d$'%n, "")
        pTexte = pTexte.replace('$MAXDATA%d$'%n, "")
        pTexte = pTexte.replace('$ERRDATA%d$'%n, "")
        pTexte = pTexte.replace('$INFEREN%d$'%n, "")
        pTexte = pTexte.replace('$EXPLICA%d$'%n, "")

    if pNbCol > 1:
        pRapport = pRapport.replace("$DATA$", pTexte)

    # Fin du rapport ; plus d'élément à écrire :
    # 1- suppression des lignes inutiles
    inutile = "\n%s \\\\\n"%(" &\n" * (pNbColLatex - 1))
    while inutile in pRapport:
        pRapport = pRapport.replace(inutile, "\n")

    # 2- suppression du tag $DATA$
    pRapport = pRapport.replace("$DATA$", "")

    return pRapport

# ---------------------------------------------------------------------------
## Writing the image data report in LaTeX
# @param pDictParams : parameter dictionary
# @param pExtension : extension of explanation filename
# @param pClasses : labels of classes
def writeReportImage(pDictParams, pExtension="npy", pClasses=None):
    # shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pPlotDataSize = pDictParams['plotDataSize']
    pNbColLatex = pDictParams['nbColLatex']
    pDataBandPathList = pDictParams['dataBandPathList']

    repertkaaActions = os.path.dirname(kaasrc.kaaActions.__file__)
    with open(os.path.join(repertkaaActions, "ressources", "contactSheet.tex"), 'r', encoding="utf-8") as f:
        rapport = f.read()

    if pPlotDataSize == 1:
        strShapePlot = "Plots with original data shape"
    else:
        strShapePlot = "Plots with model input data shape"

    rapport = rapport.replace("$TITRE$", "%s\\\\\\small %s"%(pRepertProd.replace('_', '\\_').replace('/', ' : '), strShapePlot))

    numCol = 1
    texte = ""

    txtDataSize = ""
    if pPlotDataSize == 1:
        txtDataSize = "--datasize"

    # Récolte des résultats d'explication (dataExplanations)
    listDataExplain = []
    repert = os.path.join(pDataProd, "dataExplanations", pRepertProd)
    for (dirpath, _, filenames) in os.walk(repert):
        for file in filenames:
            if file != "allData.%s"%pExtension:
                _, ext = os.path.splitext(file)
                if ext == ".%s"%pExtension:
                    listDataExplain.append((os.path.join(dirpath, file), os.path.dirname(os.path.join(dirpath, file).replace(repert + os.sep, ''))))
    if len(listDataExplain) == 0:
        colPrint("The list of explanation files is empty. Verify their file extension (default npy).", "Warning")

    # Boucle sur les résultats d'explication (dataExplanations)
    for dataExplain, dirname in listDataExplain:

        # récupération du fichier json de résultat d'inférence
        fichierJson = dataExplain.replace(".%s"%pExtension, ".json").replace("dataExplanations", "dataInference")
        if os.path.exists(fichierJson):
            with open(fichierJson, 'r', encoding="utf-8") as fJson:
                inferJson = json.load(fJson)
        else:
            inferJson = None

        # positionnement sur le répertoire des données produites (dataPlot)
        if pDataBandPathList is None:
            dataPlotList = [dataExplain.replace(".%s"%pExtension, ".png").replace("dataExplanations", "dataPlotExplanations")]
        else:
            # Cas de plusieurs bandes images
            # 1- determination de l'index
            indexData = -1
            dataToFind, _ = os.path.splitext(os.path.basename(dataExplain))
            for i, dataBandList in enumerate(pDataBandPathList):
                if indexData == -1:
                    for dataBand in dataBandList:
                        if dataToFind in dataBand:
                            indexData = i
                            break
            if indexData == -1:
                colPrint("Donnée %s non trouvée"%dataToFind, "Error")
            # 2- récupération des données
            dataPlotList = []
            for dataBand in pDataBandPathList[indexData]:
                baseNameDataBand, _ = os.path.splitext(os.path.basename(dataBand))
                dataPlotList.append(dataExplain.replace(dataToFind, baseNameDataBand).replace(".%s"%pExtension, ".png").replace("dataExplanations", "dataPlotExplanations"))

        # recherche du json de l'explication
        fichierJson = dataExplain.replace(".%s"%pExtension, ".json")
        if os.path.exists(fichierJson):
            with open(fichierJson, 'r', encoding="utf-8") as fJson:
                explJson = json.load(fJson)
        else:
            explJson = None

        for dataPlot in dataPlotList:
            if os.path.exists(dataPlot):
                rapport, texte, numCol = rapporterData(rapport, texte, dirname, dataPlot, numCol, pNbColLatex, pTxtDataSize=txtDataSize, pInferJson=inferJson, pExplJson=explJson)

        # S'il y a une visualisationet/ou un traitement par classe
        if pClasses is not None:
            for classe in pClasses:
                # recherche du json de l'inférence
                fichierJson = dataExplain.replace(".%s"%pExtension, "--c_%s.json"%classe)
                if os.path.exists(fichierJson):
                    with open(fichierJson, 'r', encoding="utf-8") as fJson:
                        inferJson = json.load(fJson)

                for dataPlot in dataPlotList:
                    dataToPlot = dataPlot.replace(".png", "--c_%s.png"%classe)
                    if os.path.exists(dataToPlot):
                        rapport, texte, numCol = rapporterData(rapport, texte, dirname, dataToPlot, numCol, pNbColLatex, pTxtDataSize=txtDataSize, pInferJson=inferJson, pExplJson=explJson)

    # Fin d'écriture des données
    rapport = finRapporterData(rapport, texte, numCol, pNbColLatex)

    # sauvegarde du rapport LaTeX
    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
    latexReport = os.path.join(resultSavedOn, "contactSheet%s.tex"%txtDataSize)
    with open(latexReport, 'w', encoding="utf-8") as f:
        f.write(rapport)

    # compression des données produites (dataPlot)
    builtTGZ(resultSavedOn, rapport.count('\n'))

    # compile latex report
    if ISLATEX:
        latexReportPath = os.path.dirname(latexReport)
        latexReport = os.path.basename(latexReport).replace('.tex', '')
        os.system("cd %s;pdflatex -interaction nonstopmode %s.tex > /dev/null "%(latexReportPath, latexReport))
        os.system("cd %s;rm %s.log %s.aux > /dev/null "%(latexReportPath, latexReport, latexReport))
        colPrint("Quick report available in %s/%s.pdf"%(latexReportPath,latexReport))
    else:
        colPrint("Quick report available in %s"%latexReport)

# ---------------------------------------------------------------------------
## Writing the image data report in LaTeX
# @param pDictParams : parameter dictionary
# @param pExtension : extension of explanation filename
# @param pListItems : list of items (rule, object, etc.) to plot
# @param pClasses : labels of classes
# @param pSuffixes : list of filename suffixes to append to result filename
def writeReportTabText(pDictParams, pExtension="npy", pListItems=None, pClasses=None, pSuffixes=None):
    if pListItems is None:
        pListItems = [""]
    if pSuffixes is None:
        pSuffixes = [""]

    # shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pNbColLatex = pDictParams['nbColLatex']

    for i, _ in enumerate(pSuffixes):
        if pSuffixes[i] != "":
            pSuffixes[i] = "--s_%s"%pSuffixes[i]

    repertkaaActions = os.path.dirname(kaasrc.kaaActions.__file__)
    with open(os.path.join(repertkaaActions, "ressources", "contactSheet.tex"), 'r', encoding="utf-8") as f:
        rapport = f.read()

    rapport = rapport.replace("$TITRE$", pRepertProd.replace('_', '\\_').replace('/', ' : '))

    numCol = 1
    texte = ""

    # Récolte des résultats d'explication (dataExplain)
    listDataExplain = []

    repert = os.path.join(pDataProd, "dataExplanations", pRepertProd)
    for (dirpath, _, filenames) in os.walk(repert):
        for file in filenames:
            if file[:7] != "allData":
                _, ext = os.path.splitext(file)
                if ext == ".%s"%pExtension:
                    listDataExplain.append((os.path.join(dirpath, file), os.path.dirname(os.path.join(dirpath, file).replace(repert + os.sep, ''))))

    # Boucle sur les résultats d'explication (dataExplain)
    listDataPlotReported = []
    for dataExplain, dirname in listDataExplain:

        # récupération du fichier json de résultat d'inférence
        fichierJson = dataExplain.replace(".%s"%pExtension, ".json").replace("dataExplanations", "dataInference")
        if os.path.exists(fichierJson):
            with open(fichierJson, 'r', encoding="utf-8") as fJson:
                inferJson = json.load(fJson)
        else:
            # Si on ne le trouve pas, on retire toutes les extensions
            inferJson = None
            # Création du dictionnaire des suffixes
            nom = os.path.splitext(os.path.basename(fichierJson))[0]
            for key in ['--i_', '--c_', '--s_']:
                if key in nom:
                    dataExtension = nom.split(key)[1].split('--')[0]
                    fichierJson = fichierJson.replace('%s%s'%(key, dataExtension), '')
                    if os.path.exists(fichierJson):
                        with open(fichierJson, 'r', encoding="utf-8") as fJson:
                            inferJson = json.load(fJson)
                            break

        # positionnement sur le répertoire des données produites (dataPlot)
        dataPlot = dataExplain.replace(".%s"%pExtension, ".png").replace("dataExplanations", "dataPlotExplanations")

        # recherche du json de l'explication
        fichierJson = dataExplain.replace(pExtension, "json")
        if os.path.exists(fichierJson):
            with open(fichierJson, 'r', encoding="utf-8") as fJson:
                explJson = json.load(fJson)
        else:
            explJson = None

        # Boucle sur la liste des items de la donnée (ex: regles d'une table)
        for idxItem in pListItems:
            extIdxItem = ""
            if idxItem != "":
                extIdxItem = "--i_%s"%idxItem

            for suffixe in pSuffixes:
                dataToPlot = dataPlot.replace(".png", "%s%s.png"%(extIdxItem, suffixe))
                if os.path.exists(dataToPlot) and dataToPlot not in listDataPlotReported:
                    listDataPlotReported.append(dataToPlot)
                    rapport, texte, numCol = rapporterData(rapport, texte, dirname, dataToPlot, numCol, pNbColLatex, pInferJson=inferJson, pExplJson=explJson)

            if pClasses is not None:
                for classe in pClasses:
                    extClass = ""
                    if classe != "":
                        extClass = "--c_%s"%classe

                    # recherche du json de l'explication
                    fichierJson = dataExplain.replace(".%s"%pExtension, "%s%s.json"%(extIdxItem, extClass))
                    if os.path.exists(fichierJson):
                        with open(fichierJson, 'r', encoding="utf-8") as fJson:
                            explJson = json.load(fJson)

                    for suffixe in pSuffixes:
                        dataToPlot = dataPlot.replace(".png", "%s%s%s.png"%(extIdxItem, extClass, suffixe))
                        if os.path.exists(dataToPlot) and dataToPlot not in listDataPlotReported:
                            listDataPlotReported.append(dataToPlot)
                            rapport, texte, numCol = rapporterData(rapport, texte, dirname, dataToPlot, numCol, pNbColLatex, pInferJson=inferJson, pExplJson=explJson)

    # Fin d'écriture des données
    rapport = finRapporterData(rapport, texte, numCol, pNbColLatex)

    # sauvegarde du rapport LaTeX
    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
    latexReport = os.path.join(resultSavedOn, "contactSheet.tex")
    with open(latexReport, 'w', encoding="utf-8") as f:
        f.write(rapport)

    # compression des données produites (dataPlot)
    builtTGZ(resultSavedOn, rapport.count('\n'))

    # compile latex report
    if ISLATEX:
        latexReportPath = os.path.dirname(latexReport)
        latexReport = os.path.basename(latexReport).replace('.tex', '')
        os.system("cd %s;pdflatex -interaction nonstopmode %s.tex > /dev/null "%(latexReportPath, latexReport))
        os.system("cd %s;rm %s.log %s.aux > /dev/null "%(latexReportPath, latexReport, latexReport))
        colPrint("Quick report available in %s/%s.pdf"%(latexReportPath,latexReport))
    else:
        colPrint("Quick report available in %s"%latexReport)

# ---------------------------------------------------------------------------
## Writing the object data report in LaTeX
# @param pDictParams : parameter dictionary
def writeReportObjDetection(pDictParams):
    # shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pPlotDataSize = pDictParams['plotDataSize']

    pDictParams = kaasrc.communs.updateListObjects(pDictParams)
    pListObjets = pDictParams['objets']
    pNbColLatex = pDictParams['nbColLatex']
    pLegende = "--legend" if pDictParams['legender']==1 else ""

    repertkaaActions = os.path.dirname(kaasrc.kaaActions.__file__)
    with open(os.path.join(repertkaaActions, "ressources", "contactSheet.tex"), 'r', encoding="utf-8") as f:
        rapport = f.read()

    if pPlotDataSize == 1:
        strShapePlot = "Plots with original data shape"
    else:
        strShapePlot = "Plots with model input data shape"

    rapport = rapport.replace("$TITRE$", "%s\\\\\\small %s"%(pRepertProd.replace('_', '\\_').replace('/', ' : '), strShapePlot))

    numCol = 1
    texte = ""

    txtDataSize = ""
    if pPlotDataSize == 1:
        txtDataSize = "--datasize"

    for index in range(pNbData):
        dataName = pDataList[index]
        dirName = os.path.dirname(dataName)
        if dataName not in pListObjets:
            ficObjets = os.path.join(pDataProd, "dataExplanations", pRepertProd, 'listObjects.json')
            print("          No objet found for",dataName, flush=True)
            print("            Check file:",ficObjets, flush=True)
            continue
        for objet in pListObjets[dataName]:
            fichierJson = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataInference", pRepertProd, dirName), "%s--i_%d.json"%(os.path.basename(dataName), objet))
            # recherche du json de l'inférence
            if os.path.exists(fichierJson):
                with open(fichierJson, 'r', encoding="utf-8") as fJson:
                    inferJson = json.load(fJson)
            else:
                inferJson = None
            # recherche du json de l'explication
            fichierJson = fichierJson.replace("dataInference", "dataExplanations")
            if os.path.exists(fichierJson):
                with open(fichierJson, 'r', encoding="utf-8") as fJson:
                    explJson = json.load(fJson)
            else:
                explJson = None

            dataPlot = fichierJson.replace(".json", "%s.png"%pLegende).replace("dataExplanations", "dataPlotExplanations")
            if os.path.exists(dataPlot):
                rapport, texte, numCol = rapporterData(rapport, texte, dirName, dataPlot, numCol, pNbColLatex, pTxtDataSize=txtDataSize, pInferJson=inferJson, pExplJson=explJson)

    # Fin d'écriture des données
    rapport = finRapporterData(rapport, texte, numCol, pNbColLatex)

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
    latexReport = os.path.join(resultSavedOn, "contactSheet%s.tex"%txtDataSize)
    with open(latexReport, 'w', encoding="utf-8") as f:
        f.write(rapport)

    # compression des données produites (dataPlot)
    builtTGZ(resultSavedOn, rapport.count('\n'))

    # compile latex report
    if ISLATEX:
        latexReportPath = os.path.dirname(latexReport)
        latexReport = os.path.basename(latexReport).replace('.tex', '')
        os.system("cd %s;pdflatex -interaction nonstopmode %s.tex > /dev/null "%(latexReportPath, latexReport))
        os.system("cd %s;rm %s.log %s.aux > /dev/null "%(latexReportPath, latexReport, latexReport))
        colPrint("Quick report available in %s/%s.pdf"%(latexReportPath,latexReport))
    else:
        colPrint("Quick report available in %s"%latexReport)

# ---------------------------------------------------------------------------
## Writing the segmentation object data report in LaTeX
# @param pDictParams : parameter dictionary
# @param pExtension : filename extension of explanation filename
# @return -not applicable-
def writeReportObjSegmentation(pDictParams, pExtension="npy"):
    # shortcuts
    pRepertProd = pDictParams['repertProd']
    pDataProd = pDictParams['dataProd']
    pNbData = pDictParams['nbData']
    pDataList = pDictParams['dataList']
    pPlotDataSize = pDictParams['plotDataSize']

    pDictParams = kaasrc.communs.updateListObjects(pDictParams)
    pListObjets = pDictParams['objets']
    pNbColLatex = pDictParams['nbColLatex']

    repertkaaActions = os.path.dirname(kaasrc.kaaActions.__file__)
    with open(os.path.join(repertkaaActions, "ressources", "contactSheet.tex"), 'r', encoding="utf-8") as f:
        rapport = f.read()

    if pPlotDataSize == 1:
        strShapePlot = "Plots with original data shape"
    else:
        strShapePlot = "Plots with model input data shape"

    rapport = rapport.replace("$TITRE$", "%s\\\\\\small %s"%(pRepertProd.replace('_', '\\_').replace('/', ' : '), strShapePlot))

    numCol = 1
    texte = ""

    txtDataSize = ""
    if pPlotDataSize == 1:
        txtDataSize = "--datasize"

    for index in range(pNbData):
        dataName = pDataList[index]
        dirName = os.path.dirname(dataName)

        for classObjets in pListObjets[dataName]:
            className = classObjets[0]
            fichierJson = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataInference", pRepertProd, dirName), "%s--c_%s.json"%(os.path.basename(dataName), className))
            if os.path.exists(fichierJson):
                with open(fichierJson, 'r', encoding="utf-8") as fJson:
                    inferJson = json.load(fJson)
            else:
                inferJson = None

            if len(classObjets) == 1:
                dataExplain = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s--c_%s.%s'%(os.path.basename(dataName), className, pExtension))

                # recherche du json de l'explication
                fichierJson = dataExplain.replace(".%s"%pExtension, ".json")
                if os.path.exists(fichierJson):
                    with open(fichierJson, 'r', encoding="utf-8") as fJson:
                        explJson = json.load(fJson)
                else:
                    explJson = None

                dataPlot = dataExplain.replace("dataExplanations", "dataPlotExplanations").replace("--c_%s.%s"%(className, pExtension), "--c_%s.png"%className)
                if os.path.exists(dataPlot):
                    rapport, texte, numCol = rapporterData(rapport, texte, dirName, dataPlot, numCol, pNbColLatex, pTxtDataSize=txtDataSize, pInferJson=inferJson, pExplJson=None)
            else:
                listObjets = classObjets[1]

                for objet in listObjets:
                    dataExplain = kaasrc.communs.noSpace(os.path.join(pDataProd, "dataExplanations", pRepertProd, dirName), '%s--i_%d--c_%s.%s'%(os.path.basename(dataName), objet, className, pExtension))

                    # recherche du json de l'explication
                    fichierJson = dataExplain.replace(".%s"%pExtension, ".json")
                    if os.path.exists(fichierJson):
                        with open(fichierJson, 'r', encoding="utf-8") as fJson:
                            explJson = json.load(fJson)
                    else:
                        explJson = None

                    # fichier d'explication
                    dataPlot = dataExplain.replace("dataExplanations", "dataPlotExplanations").replace("--i_%d--c_%s.%s"%(objet, className, pExtension), "--i_%d--c_%s.png"%(objet, className))
                    if os.path.exists(dataPlot):
                        rapport, texte, numCol = rapporterData(rapport, texte, dirName, dataPlot, numCol, pNbColLatex, pTxtDataSize=txtDataSize, pInferJson=inferJson, pExplJson=explJson)

    # Fin d'écriture des données
    rapport = finRapporterData(rapport, texte, numCol, pNbColLatex)

    resultSavedOn = os.path.join(pDataProd, "dataPlotExplanations", pRepertProd)
    latexReport = os.path.join(resultSavedOn, "contactSheet%s.tex"%txtDataSize)
    with open(latexReport, 'w', encoding="utf-8") as f:
        f.write(rapport)

    # compression des données produites (dataPlot)
    builtTGZ(resultSavedOn, rapport.count('\n'))

    # compile latex report
    if ISLATEX:
        latexReportPath = os.path.dirname(latexReport)
        latexReport = os.path.basename(latexReport).replace('.tex', '')
        os.system("cd %s;pdflatex -interaction nonstopmode %s.tex > /dev/null "%(latexReportPath, latexReport))
        os.system("cd %s;rm %s.log %s.aux > /dev/null "%(latexReportPath, latexReport, latexReport))
        colPrint("Quick report available in %s/%s.pdf"%(latexReportPath,latexReport))
    else:
        colPrint("Quick report available in %s"%latexReport)

# ---------------------------------------------------------------------------
## Function to write the aides dictionary in the full report
# @param pAidesDict : parameter aides dictionary
# @param pRapport : current full report
# @return pRapport : updated full report
def writeAidesDictInReport(pAidesDict, pRapport):

    for key, subdict in pAidesDict.items():

        keyToPlot = "%s \\textit{'%s'}"%(key[0].capitalize(), key[1])
        keyToPlot = keyToPlot.replace('_', '\\_').replace(os.sep, ':')

        # écrire le titre de la section
        pRapport = pRapport.replace("$AIDE$", "\n\\section{" + keyToPlot + "}\n$AIDE$")

        for subkey, (_, desc, parameters_aides) in subdict.items():

            subkeyToPlot = "%s \\textit{'%s'}"%(subkey[0].capitalize(), subkey[1])
            subkeyToPlot = subkeyToPlot.replace('_', '\\_').replace(os.sep, ':')

            # écrire le nom de la méthode ou la métrique
            pRapport = pRapport.replace("$AIDE$", "\\subsection{" + subkeyToPlot + "}\n$AIDE$")
            # écrire la description correspondante
            pRapport = pRapport.replace("$AIDE$", desc.replace('_', '\\_') + "\n$AIDE$")

            # écrire les desciption des paramètres de la méthode ou la métrique
            if parameters_aides:
                pRapport = pRapport.replace("$AIDE$", "\\subsubsection{Parameters}\n$AIDE$")
                pRapport = pRapport.replace("$AIDE$", "\\begin{description}\n$AIDE$")
                for param_code, param_desc in parameters_aides:
                    pRapport = pRapport.replace("$AIDE$", "\\item [" + param_code.split('.')[-1] + "]\\label{" + param_code + "} : " + param_desc.replace('_', '\\_') + "\n$AIDE$")
                pRapport = pRapport.replace("$AIDE$", "\\end{description}\n\n$AIDE$")

    pRapport = pRapport.replace("$AIDE$", "")

    return pRapport

# ---------------------------------------------------------------------------
## Function to write the inferences dictionary in the full report
# @param pInferencesDict : parameter dictionary
# @param pRapport : current full report
# @param pRepertFullReport : the directory of the full report
# @param pNbColLatex : number of columns in the table
# @param pIndexSplit : index to find library and method etc. names in a filename
# @return pRapport : updated full report
def writeInferenceDictInReport(pInferencesDict, pRapport, pRepertFullReport, pNbColLatex, pIndexSplit):

    numCol = 1
    texte = ""

    for key, filename in pInferencesDict.items():

        keyToPlot = "%s \\textit{'%s'}"%(key[0].capitalize(), key[1])
        keyToPlot = keyToPlot.replace('_', '\\_').replace(os.sep, ':')

        # écrire le nom de la donnée
        pRapport = pRapport.replace("$DATA$", "\\section{" + keyToPlot + "}\n$DATA$")

        filenameSplit = filename.split(os.sep)
        library = filenameSplit[pIndexSplit]

        repertImages = os.path.join("images", library, "dataInference")
        fullReperImages = os.path.join(pRepertFullReport, repertImages)

        # copier l'image à afficher dans le dossier "images" du full report
        os.makedirs(fullReperImages, exist_ok=True)
        os.chmod(fullReperImages, 0o0777)
        pathCopy = os.path.join(fullReperImages, os.path.basename(filename))
        shutil.copyfile(filename, pathCopy)
        filename = pathCopy

        if os.path.exists(filename):
            pRapport, texte, numCol = rapporterDataFullReport(pRapport, texte, numCol, pNbColLatex, filename, pRepertImages=repertImages)

        pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

    return pRapport

# ---------------------------------------------------------------------------
## Function to copy the image to plot in the "images" directory of full report
def copyImageToFullReport(pFullReperImages, pFilename):
    os.makedirs(pFullReperImages, exist_ok=True)
    os.chmod(pFullReperImages, 0o0777)
    pathCopy = os.path.join(pFullReperImages, os.path.basename(pFilename))
    shutil.copyfile(pFilename, pathCopy)

    return pathCopy

# ---------------------------------------------------------------------------
def reportMultiData(subSection, texteSubSection, numColSubSection, filenameReport, pNbColLatex, pDataSuffixes, pInferJson, pExplJson, pRepertImages, pTitleData, pDataBandPathList, filename, fullReperImages, pDataName=None):
    # Cas de plusieurs données associées
    # 1- determination de l'index
    indexData = -1
    dataToFind, _ = os.path.splitext(os.path.basename(filename))
    for i, dataBandList in enumerate(pDataBandPathList):
        if indexData == -1:
            for dataBand in dataBandList:
                if dataToFind in dataBand:
                    indexData = i
                    break
    if indexData == -1:
        colPrint("Donnée %s non trouvée"%dataToFind, "Error")
    # 2- rapport des données
    for dataBand in pDataBandPathList[indexData]:
        baseNameDataBand, _ = os.path.splitext(os.path.basename(dataBand))
        pathToPlot = filenameReport.replace(dataToFind, baseNameDataBand)
        copyImageToFullReport(fullReperImages, filename.replace(dataToFind, baseNameDataBand))
        titleData = pTitleData
        if pDataName is not None:
            titleData = "\\textbf{%s}\\\\ %s"%(pDataName, shortenFilename(baseNameDataBand))
            if pTitleData != "":
                titleData += "\\\\ %s"%pTitleData
        subSection, texteSubSection, numColSubSection = rapporterDataFullReport(subSection, texteSubSection, numColSubSection, pNbColLatex,
                                                                                pathToPlot, pDataSuffixes, pInferJson, pExplJson, pRepertImages, titleData)

    return subSection, texteSubSection, numColSubSection

# ---------------------------------------------------------------------------
## Function to write explanations or metrics dictionary in the full report
# @param pDict : parameter dictionary
# @param pRapport : current full report
# @param pRepertFullReport : the directory of the full report
# @param pNbColLatex : number of columns in the table
# @param pIndexSplit : index to find library and method etc. names in a filename
# @return pRapport : updated full report
def writeDictInReportMetric(pDict, pRapport, pRepertFullReport, pNbColLatex, pIndexSplit):

    numCol = 1
    texte = ""

    graphSubsection = "$DATA$"
    numColGraphSubsection = 1
    texteGraphSubsection = ""

    # pDict: libraryKey, (metricKey, metricParamKey, methodKey, methodParametersKey, listeMetriques)
    for libraryKey, subdictMetricKey in pDict.items():

        # on écrit la section 'bibliotheque'
        libraryKeyToPlot = "%s \\textit{'%s'}"%(libraryKey[0].capitalize(), libraryKey[1])
        libraryKeyToPlot = libraryKeyToPlot.replace('_', '\\_').replace('/', ': ')
        pRapport = pRapport.replace("$DATA$", "\\section{" + libraryKeyToPlot + "}\n$DATA$")

        # pDict: metricKey, (metricParamKey, methodKey, methodParametersKey, listeMetriques)
        for metricKey, subdictMetricParamKey in subdictMetricKey.items():

            # on écrit la section 'bibliotheque'
            libraryMetricKeyToPlot = "%s \\textit{'%s'}"%(metricKey[0].capitalize(), metricKey[1])
            libraryMetricKeyToPlot = libraryMetricKeyToPlot.replace('_', '\\_').replace('/', ': ')
            pRapport = pRapport.replace("$DATA$", "\\subsection{" + libraryMetricKeyToPlot + "}\n$DATA$")

            # pDict: metricParamKey, (methodKey, methodParametersKey, listeMetriques)
            for metricParamKey, subdictMethodKey in subdictMetricParamKey.items():

                # On recupere le nombre de sous-sections de methodes
                nbSubdictMethodKey = len(subdictMethodKey.items())

                metricParamKeyToPlot = "%s \\textit{'%s'}"%(metricParamKey[0].capitalize(), metricParamKey[1])
                metricParamKeyToPlot = metricParamKeyToPlot.replace('_', '\\_').replace(os.sep, ':')
                pRapport = pRapport.replace("$DATA$", "\\subsubsection{" + metricParamKeyToPlot + "}\n$DATA$")

                # pDict: methodKey, (methodParametersKey, listeMetriques)
                for methodKey, listPlots in subdictMethodKey.items():

                    methodKeyToPlot = "%s \\textit{'%s'}"%(methodKey[0].capitalize(), methodKey[1])
                    methodKeyToPlot = methodKeyToPlot.replace('_', '\\_').replace(os.sep, ':')

                    # pDict: methodParametersKey, dataMetriq, filename
                    for methodParamKey, dataMetriq, filename in listPlots:
                        filenameSplit = filename.split(os.sep)
                        library = filenameSplit[pIndexSplit]

                        # si le fichier de la donnée à trace n'existe pas, on passe au suivant
                        if not os.path.exists(filename):
                            continue

                        # on construit le répertoire de réception de la copie pour le rapport LaTeX
                        repertImages = os.path.join("images", library)
                        fullReperImages = os.path.join(pRepertFullReport, repertImages)

                        # copier l'image à afficher dans le dossier "images" du full report
                        copyImageToFullReport(fullReperImages, filename)

                        #   § Bibliothèque/metrique
                        #   §.§  parametres-metrique
                        #   §.§.§ Methode
                        #           metriques

                        titleData = ""

                        # ajouter les données dans la sous-section commune
                        sdl = ""
                        if dataMetriq is not None:
                            titleData += "\\textbf{data}\\\\ %s"%shortenFilename(dataMetriq.replace('_', '\\_'))
                            sdl = "\\\\"
                            dataMetriq = None
                        if methodParamKey[0] and methodParamKey[0] == "data":
                            titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, methodParamKey[0], methodParamKey[1])
                            sdl = "\\\\"
                        if methodKey[0] and methodKey[0] == 'comparison of methods':
                            titleData += "%s\\textbf{%s}"%(sdl, methodKey[0])
                            sdl = "\\\\"
                            if methodParamKey[0] and methodParamKey[0] != "data" and methodParamKey != "allData":
                                titleData += "%s\\textbf{%s}"%(sdl, methodParamKey[0])
                                for method in methodParamKey[1]:
                                    titleData += "%s  -\\textbf{%s}: %s"%(sdl, method, methodParamKey[1][method])
                        else:
                            if methodKey[0]:
                                titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, methodKey[0], methodKey[1])
                                sdl = "\\\\"
                            if methodParamKey[0] and methodParamKey[0] != "data" and methodParamKey != "allData":
                                titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, methodParamKey[0], methodParamKey[1])
                        titleData = titleData or "--"

                        graphSubsection, texteGraphSubsection, numColGraphSubsection = rapporterDataFullReport(graphSubsection, texteGraphSubsection, numColGraphSubsection, pNbColLatex, filename, pDataSuffixes=dataMetriq, pRepertImages=repertImages, pTitleData=titleData)

                if nbSubdictMethodKey > 1 or (nbSubdictMethodKey == 1 and len(list(subdictMethodKey.values())[0]) > 1):
                    # fin d'écriture de la sous-section 'particulière' dans le rapport
                    pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

            if texteGraphSubsection != "":
                # fin d'écriture de la sous-section commune
                graphSubsection, texteGraphSubsection, numColGraphSubsection = finRapporterDataFullReport(graphSubsection, texteGraphSubsection, numColGraphSubsection, pNbColLatex)
                # ajouter la sous-section commune dans le rapport
                pRapport = pRapport.replace("$DATA$", graphSubsection)
                # réinitialiser les variables de la sous-section commune
                graphSubsection = "$DATA$"
                texteGraphSubsection = ""

        pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

    return pRapport

# ---------------------------------------------------------------------------
## Function to write explanations or metrics dictionary in the full report
# @param pDictParams : parameter dictionary
# @param pDict : parameter dictionary
# @param pRapport : current full report
# @param pRepertFullReport : the directory of the full report
# @param pNbColLatex : number of columns in the table
# @param pIndexSplit : index to find library and method etc. names in a filename
# @return pRapport : updated full report
def writeDictInReportExpMethod(pDictParams, pDict, pRapport, pRepertFullReport, pNbColLatex, pIndexSplit):
    # shortcut
    pDataBandPathList = pDictParams['dataBandPathList']

    numCol = 1
    texte = ""

    commonSubsection = "$DATA$"
    numColCommonSubsection = 1
    texteCommonSubsection = ""

    commonSubsubsection = "$DATA$"
    numColCommonSubsubsection = 1
    texteCommonSubsubsection = ""

    # pDict: methodKey, (libraryKey, methodParamKey, dataKey, listeExplications)
    for methodKey, subdictLibrary in pDict.items():
        # booléen pour déterminer s'il existe une sous-section 'bibliotheque' dans la section courante
        existSubsectionLibrary = False

        # on écrit la section 'méthode'
        methodKeyToPlot = "%s \\textit{'%s'}"%(methodKey[0].capitalize(), methodKey[1])
        methodKeyToPlot = methodKeyToPlot.replace('_', '\\_').replace('/', ': ')
        pRapport = pRapport.replace("$DATA$", "\\section{%s}\n$DATA$"%methodKeyToPlot)

        # pDict: libraryKey, (methodParamKey, dataKey, listeExplications)
        for libraryKey, subdictMethodParam in subdictLibrary.items():
            # booléen pour déterminer s'il existe une sous-sous-section 'particulière' dans la sous-section courante
            existSubsectionMethodParams = False

            # On recupere le nombre de sous-sections de jeu de paramètres
            nbSubdictMethodParam = len(subdictMethodParam.items())

            # s'il y a plusieurs méthodes ou si la méthode a plusieurs paramétre
            if nbSubdictMethodParam > 1 or (nbSubdictMethodParam == 1 and len(list(subdictMethodParam.values())[0]) > 1):
                # commencer une sous-section 'bibliotheque' dans le rapport
                existSubsectionLibrary = True
                pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

                # on écrit la sous-section 'bibliotheque'
                libraryKeyToPlot = "%s \\textit{'%s'}"%(libraryKey[0].capitalize(), libraryKey[1])
                libraryKeyToPlot = libraryKeyToPlot.replace('_', '\\_').replace(os.sep, ':')
                pRapport = pRapport.replace("$DATA$", "\\subsection{%s}\n$DATA$"%libraryKeyToPlot)

            # pDict: methodParamKey, (dataKey, listeExplications)
            for methodParamKey, listPlots in subdictMethodParam.items():

                # On recupere le nombre de données à tracer
                nbItemsListPlots = len(listPlots)

                # s'il y a plusieurs jeux de paramètres
                if nbItemsListPlots > 1:
                    # commencer une sous-sous-section 'jeu de paramètres' dans le rapport
                    existSubsectionMethodParams = True
                    pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

                    # on écrit la sous-sous-section 'methodParams'
                    methodParamKeyToPlot = "%s \\textit{'%s'}"%(methodParamKey[0].capitalize(), methodParamKey[1])
                    methodParamKeyToPlot = methodParamKeyToPlot.replace('_', '\\_').replace(os.sep, ':')
                    pRapport = pRapport.replace("$DATA$", "\\subsubsection{" + methodParamKeyToPlot + "}\n$DATA$")

                # pDict: dataKey, listeExplications
                for dataKey, dataSuffixes, filename, inferJson, explJson in listPlots:
                    # on recupere le nom de la bibliothèque et le nom du repertoire de dépôt de la donnée à tracer
                    filenameSplit = filename.split(os.sep)
                    library = filenameSplit[pIndexSplit]
                    dirname = filenameSplit[pIndexSplit + 3]

                    # si le fichier de la donnée à trace n'existe pas, on passe au suivant
                    if not os.path.exists(filename):
                        continue

                    # on construit le répertoire de réception de la copie pour le rapport LaTeX
                    repertImages = os.path.join("images", library, dirname)
                    fullReperImages = os.path.join(pRepertFullReport, repertImages)

                    # on copie l'image à afficher dans le dossier "images" du full report
                    filenameReport = copyImageToFullReport(fullReperImages, filename)

                    #   § Methode
                    #   §.§ Bibliothèque (si existSubsectionLibrary)
                    #   §.§.§ Parametrages (si existSubsectionMethodParams)
                    #           explications

                    titleData = ""

                    # S'il n'y a qu'un seul jeu de paramètres et qu'une donnée à tracer
                    if nbSubdictMethodParam == 1 and nbItemsListPlots == 1:
                        # ajouter les données dans la sous-section commune
                        sdl = ""
                        if libraryKey[0]:
                            titleData += "\\textbf{%s}\\\\ %s"%(libraryKey[0], libraryKey[1])
                            sdl = "\\\\"
                        if methodParamKey[0]:
                            titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, methodParamKey[0], methodParamKey[1])
                            sdl = "\\\\"
                        if dataKey[0]:
                            titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, dataKey[0], dataKey[1])
                        titleData = titleData or "--"

                        # si la donnée n'a pas de donnée annexes (autre bandes image par ex.)
                        if pDataBandPathList is None:
                            commonSubsection, texteCommonSubsection, numColCommonSubsection = rapporterDataFullReport(commonSubsection, texteCommonSubsection, numColCommonSubsection, pNbColLatex, filenameReport,
                                                                                                                      pDataSuffixes=dataSuffixes, pInferJson=inferJson, pExplJson=explJson, pRepertImages=repertImages, pTitleData=titleData)
                        else:
                            commonSubsection, texteCommonSubsection, numColCommonSubsection = reportMultiData(commonSubsection, texteCommonSubsection, numColCommonSubsection, filenameReport, pNbColLatex,
                                                                                                              dataSuffixes, inferJson, explJson, repertImages, titleData,
                                                                                                              pDataBandPathList, filename, fullReperImages, dataKey[0])

                    # sinon, s'il y a plusieurs seul jeu de paramètres et qu'une donnée à tracer
                    elif nbSubdictMethodParam > 1 and nbItemsListPlots == 1:
                        # ajouter les données dans la sous-sous-section commune
                        sdl = ""
                        if methodParamKey[0]:
                            titleData += "\\textbf{%s}\\\\ %s"%(methodParamKey[0], methodParamKey[1])
                            sdl = "\\\\"
                        if dataKey[0] and dataKey != "allData":
                            titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, dataKey[0], dataKey[1])
                        titleData = titleData or "--"
                        commonSubsubsection, texteCommonSubsubsection, numColCommonSubsubsection = rapporterDataFullReport(commonSubsubsection, texteCommonSubsubsection, numColCommonSubsubsection, pNbColLatex, filename,
                                                                                                                           pDataSuffixes=dataSuffixes, pInferJson=inferJson, pExplJson=explJson, pRepertImages=repertImages, pTitleData=titleData)

                    else:
                        # ajouter les données directement dans le rapport
                        sdl = ""
                        if pDataBandPathList is None:
                            if dataKey[0]:
                                titleData += "\\textbf{%s}\\\\ %s"%(dataKey[0], dataKey[1])
                            titleData = titleData or "--"
                            pRapport, texte, numCol = rapporterDataFullReport(pRapport, texte, numCol, pNbColLatex, filename,
                                                                              pDataSuffixes=dataSuffixes, pInferJson=inferJson, pExplJson=explJson, pRepertImages=repertImages, pTitleData=titleData)
                        else:
                            pRapport, texte, numCol = reportMultiData(pRapport, texte, numCol, filenameReport, pNbColLatex,
                                                                                                              dataSuffixes, inferJson, explJson, repertImages, titleData,
                                                                                                              pDataBandPathList, filename, fullReperImages, dataKey[0])
                if nbItemsListPlots > 1:
                    # fin d'écriture de la sous-sous-section dans le rapport
                    pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

            if texteCommonSubsubsection != "":
                # fin d'écriture de la sous-sous-section commune
                commonSubsubsection, texteCommonSubsubsection, numColCommonSubsubsection = finRapporterDataFullReport(commonSubsubsection, texteCommonSubsubsection, numColCommonSubsubsection, pNbColLatex)
                # ajouter un titre à la sous-sous-section commune
                if existSubsectionMethodParams:
                    commonSubsubsection = "\\subsubsection{Miscellanous}\n" + commonSubsubsection
                # ajouter la sous-sous-section commune dans le rapport
                pRapport = pRapport.replace("$DATA$", commonSubsubsection)
                # réinitialiser les variables de la sous-sous-section commune
                commonSubsubsection = "$DATA$"
                texteCommonSubsubsection = ""

            if nbSubdictMethodParam > 1 or (nbSubdictMethodParam == 1 and len(list(subdictMethodParam.values())[0]) > 1):
                # fin d'écriture de la sous-section 'particulière' dans le rapport
                pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

        if texteCommonSubsection != "":
            # fin d'écriture de la sous-section commune
            commonSubsection, texteCommonSubsection, numColCommonSubsection = finRapporterDataFullReport(commonSubsection, texteCommonSubsection, numColCommonSubsection, pNbColLatex)
            # ajouter un titre à la sous-section commune
            if existSubsectionLibrary:
                commonSubsection = "\\subsection{Miscellanous}\n" + commonSubsection
            # ajouter la sous-section commune dans le rapport
            pRapport = pRapport.replace("$DATA$", commonSubsection)
            # réinitialiser les variables de la sous-section commune
            commonSubsection = "$DATA$"
            texteCommonSubsection = ""

        pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

    return pRapport

# ---------------------------------------------------------------------------
## Function to write explanations or metrics dictionary in the full report
# @param pDictParams : parameter dictionary
# @param pDict : parameter dictionary
# @param pRapport : current full report
# @param pRepertFullReport : the directory of the full report
# @param pNbColLatex : number of columns in the table
# @param pIndexSplit : index to find library and method etc. names in a filename
# @return pRapport : updated full report
def writeDictInReportExpData(pDictParams, pDict, pRapport, pRepertFullReport, pNbColLatex, pIndexSplit):
    # shortcut
    pDataBandPathList = pDictParams['dataBandPathList']

    numCol = 1
    texte = ""

    # Pour les sous-sections "Miscellanous" de méthodes
    # - cas 1 : 1 bibliothèque / 1 jeu de paramètre
    subSectionLibrary11 = "$DATA$"
    numColSubSectionLibrary11 = 1
    texteSubSectionLibrary11 = ""

    # - cas 2 : n bibliothèques / 1 jeu de paramètre
    subSectionLibraryn1 = "$DATA$"
    numColSubSectionLibraryn1 = 1
    texteSubSectionLibraryn1 = ""

    # - cas 3 : n bibliothèques / n jeux de paramètre
    subSectionLibrarynn = "$DATA$"
    numColSubSectionLibrarynn = 1
    texteSubSectionLibrarynn = ""

    # pDict: dataKey, (methodKey, libraryKey, methodParametersKey, listeExplications)
    for dataKey, subdictMethod in pDict.items():

        # on écrit la section 'data'
        dataKeyToPlot = "%s \\textit{'%s'}"%(dataKey[0].capitalize(), dataKey[1])
        dataKeyToPlot = dataKeyToPlot.replace('_', '\\_').replace('/', ': ')
        pRapport = pRapport.replace("$DATA$", "\\section{%s}\n$DATA$"%dataKeyToPlot)

        # pDict: methodKey, (libraryKey, methodParametersKey, listeExplications)
        for methodKey, subdictLibrary in subdictMethod.items():
            # booléen pour déterminer s'il existe une sous-section 'particulière' dans la sous-section courante
            existSubsectionMethod = True

            # On recupere le nombre de sous-sections de jeu de paramètres
            nbSubdictLibrary = len(subdictLibrary.items())

            # On dentifie la méthode en cours de traitement
            methodKeyToPlot = "%s \\textit{'%s'}"%(methodKey[0].capitalize(), methodKey[1])
            methodKeyToPlot = methodKeyToPlot.replace('_', '\\_').replace(os.sep, ':')

            # pDict: libraryKey, (methodParametersKey, listeExplications)
            for libraryKey, listPlots in subdictLibrary.items():

                # On recupere le nombre de données à tracer
                nbItemsListPlots = len(listPlots)

                # On dentifie la bibliothèque en cours de traitement
                libraryKeyToPlot = "%s \\textit{'%s'}"%(libraryKey[0].capitalize(), libraryKey[1])
                libraryKeyToPlot = libraryKeyToPlot.replace('_', '\\_').replace(os.sep, ':')

                # pDict: methodParametersKey, listeExplications
                for methodParametersKey, dataSuffixes, filename, inferJson, explJson in listPlots:
                    # on recupere le nom de la bibliothèque et le nom du repertoire de dépôt de la donnée à tracer
                    filenameSplit = filename.split(os.sep)
                    library = filenameSplit[pIndexSplit]
                    dirname = filenameSplit[pIndexSplit + 3]

                    # si le fichier de la donnée à trace n'existe pas, on passe au suivant
                    if not os.path.exists(filename):
                        continue

                    # on construit le répertoire de réception de la copie pour le rapport LaTeX
                    repertImages = os.path.join("images", library, dirname)
                    fullReperImages = os.path.join(pRepertFullReport, repertImages)

                    # on copie l'image à afficher dans le dossier "images" du full report
                    filenameReport = copyImageToFullReport(fullReperImages, filename)

                    #   § Donnée
                    #   §.§ Methode
                    #       * Bibliothèque
                    #           explications

                    titleData = ""

                    # S'il n'y a qu'une seule bibliothèque et qu'un jeu de paramètre à tracer
                    if nbSubdictLibrary == 1 and nbItemsListPlots == 1:
                        # ajouter les données dans la sous-section commune
                        sdl = ""
                        if libraryKey[0]:
                            titleData += "\\textbf{%s}\\\\ %s"%(libraryKey[0], libraryKey[1])
                            sdl = "\\\\"
                        if methodKey[0]:
                            titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, methodKey[0], methodKey[1])
                            sdl = "\\\\"
                        if methodParametersKey[0]:
                            titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, methodParametersKey[0], methodParametersKey[1])
                        titleData = titleData or "--"

                        # si la donnée n'a pas de donnée annexes (autre bandes image par ex.)
                        if pDataBandPathList is None:
                            subSectionLibrary11, texteSubSectionLibrary11, numColSubSectionLibrary11 = rapporterDataFullReport(subSectionLibrary11, texteSubSectionLibrary11, numColSubSectionLibrary11, pNbColLatex, filename,
                                                                                                                               pDataSuffixes=dataSuffixes, pInferJson=inferJson, pExplJson=explJson, pRepertImages=repertImages, pTitleData=titleData)
                        else:
                            subSectionLibrary11, texteSubSectionLibrary11, numColSubSectionLibrary11 = reportMultiData(subSectionLibrary11, texteSubSectionLibrary11, numColSubSectionLibrary11, filenameReport, pNbColLatex,
                                                                                                              dataSuffixes, inferJson, explJson, repertImages, titleData,
                                                                                                              pDataBandPathList, filename, fullReperImages, dataKey[0])
                    # sinon, plusieurs bibliothèques et qu'un jeu de paramètre à tracer pour chacune
                    elif nbSubdictLibrary > 1 and nbItemsListPlots == 1:
                        # ajouter les données dans la sous-sous-section commune
                        sdl = ""
                        if libraryKey[0]:
                            titleData += "\\textbf{%s}\\\\ %s"%(libraryKey[0], libraryKey[1])
                            sdl = "\\\\"
                        if methodParametersKey[0] and methodParametersKey != "allData":
                            titleData += "%s\\textbf{%s}\\\\ %s"%(sdl, methodParametersKey[0], methodParametersKey[1])
                        titleData = titleData or "--"

                        # si la donnée n'a pas de donnée annexes (autre bandes image par ex.)
                        if pDataBandPathList is None:
                            subSectionLibraryn1, texteSubSectionLibraryn1, numColSubSectionLibraryn1 = rapporterDataFullReport(subSectionLibraryn1, texteSubSectionLibraryn1, numColSubSectionLibraryn1, pNbColLatex, filename,
                                                                                                                               pDataSuffixes=dataSuffixes, pInferJson=inferJson, pExplJson=explJson, pRepertImages=repertImages, pTitleData=titleData)
                        else:
                            subSectionLibraryn1, texteSubSectionLibraryn1, numColSubSectionLibraryn1 = reportMultiData(subSectionLibraryn1, texteSubSectionLibraryn1, numColSubSectionLibraryn1, filenameReport, pNbColLatex,
                                                                                                              dataSuffixes, inferJson, explJson, repertImages, titleData,
                                                                                                              pDataBandPathList, filename, fullReperImages, dataKey[0])
                    else:
                        # ajouter les données directement dans le rapport
                        if methodParametersKey[0]:
                            titleData += "\\textbf{%s}\\\\ %s"%(methodParametersKey[0], methodParametersKey[1])
                        titleData = titleData or "--"

                        # si la donnée n'a pas de donnée annexes (autre bandes image par ex.)
                        if pDataBandPathList is None:
                            subSectionLibrarynn, texteSubSectionLibrarynn, numColSubSectionLibrarynn = rapporterDataFullReport(subSectionLibrarynn, texteSubSectionLibrarynn, numColSubSectionLibrarynn, pNbColLatex, filename,
                                                                                                                               pDataSuffixes=dataSuffixes, pInferJson=inferJson, pExplJson=explJson, pRepertImages=repertImages, pTitleData=titleData)
                        else:
                            subSectionLibrarynn, texteSubSectionLibrarynn, numColSubSectionLibrarynn = reportMultiData(subSectionLibrarynn, texteSubSectionLibrarynn, numColSubSectionLibrarynn, filenameReport, pNbColLatex,
                                                                                                              dataSuffixes, inferJson, explJson, repertImages, titleData,
                                                                                                              pDataBandPathList, filename, fullReperImages, dataKey[0])
                if texteSubSectionLibrarynn != "":
                    # ajouter un titre à la sous-section commune
                    if existSubsectionMethod:
                        textSection = "\\subsection{%s}\n"%methodKeyToPlot
                        existSubsectionMethod = False
                    else:
                        textSection = ""
                    textSection += "\\subsubsection{%s}\n"%libraryKeyToPlot
                    # fin d'écriture de la sous-section commune
                    subSectionLibrarynn, texteSubSectionLibrarynn, numColSubSectionLibrarynn = finRapporterDataFullReport(subSectionLibrarynn, texteSubSectionLibrarynn, numColSubSectionLibrarynn, pNbColLatex)

                    # ajouter la sous-section commune dans le rapport
                    pRapport = pRapport.replace("$DATA$", textSection + subSectionLibrarynn)

                    # réinitialiser les variables de la sous-section commune
                    subSectionLibrarynn = "$DATA$"
                    texteSubSectionLibrarynn = ""

                    # S'il y a plusieurs jeux de données
                    if nbItemsListPlots > 1:
                        # fin d'écriture du tableau de report des données
                        pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

                # for methodParametersKey

            # on a terminé les tracé des données pour une méthode
            # fin d'écriture du tableau de report des données
            pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

            if texteSubSectionLibraryn1 != "":
                # ajouter un titre à la sous-section commune
                textSection = "\\subsection{%s}\n"%methodKeyToPlot
                # fin d'écriture de la sous-section commune
                subSectionLibraryn1, texteSubSectionLibraryn1, numColSubSectionLibraryn1 = finRapporterDataFullReport(subSectionLibraryn1, texteSubSectionLibraryn1, numColSubSectionLibraryn1, pNbColLatex)

                # ajouter la sous-section commune dans le rapport
                pRapport = pRapport.replace("$DATA$", textSection + subSectionLibraryn1)
                # réinitialiser les variables de la sous-section commune
                subSectionLibraryn1 = "$DATA$"
                texteSubSectionLibraryn1 = ""

            # for library

        if texteSubSectionLibrary11 != "":
            # fin d'écriture de la sous-section commune
            textSection = "\\subsection{Miscellanous}\n"
            subSectionLibrary11, texteSubSectionLibrary11, numColSubSectionLibrary11 = finRapporterDataFullReport(subSectionLibrary11, texteSubSectionLibrary11, numColSubSectionLibrary11, pNbColLatex)
            # ajouter la sous-section commune dans le rapport
            pRapport = pRapport.replace("$DATA$", textSection + subSectionLibrary11)
            # réinitialiser les variables de la sous-section commune
            subSectionLibrary11 = "$DATA$"
            texteSubSectionLibrary11 = ""

        # for method

        pRapport, texte, numCol = finRapporterDataFullReport(pRapport, texte, numCol, pNbColLatex)

    return pRapport

# ---------------------------------------------------------------------------
def remplaceExtension(pExtensions, pData, pSubst=""):
    remplacement = pData
    for extension in pExtensions:
        remplacement = remplacement.replace(".%s"%extension, pSubst)
    return remplacement

# ---------------------------------------------------------------------------
## Writing chapter Inference of the full report in LaTeX
# @param pDictParams : parameter dictionary
# @param pRapport : LaTeX report
# @return LaTeX report
def writeChapterInference(pDictParams, pRapport):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pCode = pDictParams['code']
    pDataList = pDictParams['dataList']
    pNbColFullLatexMethod = pDictParams['nbColFullLatexMethod']

    colPrint("  - Inference chapter", "Normal")

    # elements de dépôt du rapport
    dataProdRoot = os.path.dirname(pDataProd)
    repertFullReport = os.path.join(dataProdRoot, "fullReports", pCode)
    # index pour récupérer le répertoire racine du dépôt donneesProd/.../
    indexSplit = len(repertFullReport.split(os.sep)) - 2

    # dictionnaire pour sauvegarder les résultats d'inférence
    inferencesDict = {}

    # parcours des dossiers d'inférence
    for folder in glob.glob(os.path.join(dataProdRoot, "**", "dataInference", pCode, "**"), recursive=True):
        # boucle sur pDataList pour vérifier les fichiers
        for data in pDataList:
            fichInference = os.path.join(folder, f"{data}.png")

            # On ajoute le fichier de la donnée image d'inférence au dictionnaire
            if os.path.isfile(fichInference):
                inferencesDict[('data', data)] = fichInference

    if len(inferencesDict) > 0:
        # ajouter les résultats d'inférence dans le rapport
        pRapport = pRapport.replace("$DATA$", "\\chapter{Inference results}\n\n$DATA$")
        pRapport = writeInferenceDictInReport(inferencesDict, pRapport, repertFullReport, pNbColFullLatexMethod, indexSplit)
    else:
        colPrint("    No data found", "Normal")

    return pRapport

# ---------------------------------------------------------------------------
## separate methode or metric name and its parameters (separated by __)
# @param pFilename : filename
# return tuple method or metric, parameters
def separateParameters(pFilename):
    if '__' in pFilename:
        methMetr = pFilename.split('__')[0]                                 # méthode
        parameters = pFilename.split('__')[1].replace('-', '.')     # parametres où on re-place le point flottant (remplacé par -)  /!\ directive intégration
    else:
        methMetr = pFilename.rstrip('_')   # méthode
        parameters = None          # sans paramètre
    return methMetr, parameters

# ---------------------------------------------------------------------------
## Writing chapter Methods of the full report in LaTeX
# @param pDictParams : parameter dictionary
# @param pRapport : LaTeX report
# @param pAidesDict : elements pour le chapitre d'aide
# @return LaTeX report
def writeChapterMethods(pDictParams, pRapport, pAidesDict):
    # shortcuts
    pExtensions = ['npy', 'pkl']
    pDataProd = pDictParams['dataProd']
    pCode = pDictParams['code']
    pAides = pDictParams['aides']
    pFullReportE = pDictParams['fullReportE'] if 'fullReportE' in pDictParams else None
    pNbColFullLatexMethod = pDictParams['nbColFullLatexMethod']
    pLegende = "--legend" if pDictParams['legender']==1 else ""

    colPrint("  - Explanations chapter", "Normal")

    # elements de dépôt du rapport
    dataProdRoot = os.path.dirname(pDataProd)
    repertFullReport = os.path.join(dataProdRoot, "fullReports", pCode)
    # index pour récupérer le répertoire racine du dépôt donneesProd/.../
    indexSplit = len(repertFullReport.split(os.sep)) - 2

    # ajouter le titre du chapitre dans le rapport
    rapportExpl = "$DATA$"

    # dictionnaire pour sauvegarder les résultats d'explication
    explanationsDict = {}

    # boucle sur les résultats d'explication
    pathExplainList = []
    for extension in pExtensions:
        pathExplainList.extend(glob.glob(os.path.join(dataProdRoot, "**", "dataExplanations", pCode, "**", "*.%s"%extension), recursive=True))

    # récupérer les infos de chaque explication
    methodPlotsList = []
    for pathExplain in pathExplainList:
        # on ne prend pas en compte les fichiers allData.<ext>
        if os.path.basename(pathExplain).startswith("allData"):
            continue
#        colPrint("    - %s"%pathExplain, "Info")

        # on découpe le répertoire pour en extraire les éléments :
        filenameSplit = pathExplain.split(os.sep)
        filename = filenameSplit[-1]                        # nom du fichier d'explication
        extension = filename.split('.')[1]                  # extension du fichier d'explication
        filename = filename.split('.%s'%extension)[0]       # ajustement du nom du fichier sans extension
        dataname = filename.split('--')[0]                  # nom de la donnée (avant les suffixes introduits par '--') /!\ directive intégration
        dataname = remplaceExtension(pExtensions, dataname)
        datanameShort = shortenFilename(dataname)
        library = filenameSplit[indexSplit]                 # nom de la bibliotheque
        dirname = filenameSplit[indexSplit + 3]             # repertoire de la méthode et ses paramètres

        # isolement de la méthode et ses paramères du dirname (séparés par __) /!\ directive intégration
        method, methodParameters = separateParameters(dirname)

        # récupération des elements, item classe et suffixe sur le nom de la donnée (s'il s'agit de l'explication d'un élément d'une donnée) /!\ directive intégration
        dataSuffixes = {'--i_': None, '--c_': None, '--s_': None}
        for key, _ in dataSuffixes.items():
            if key in filename:
                dataSuffixes[key] = filename.split(key)[1].split('--')[0]

        # récupérer la description de la méthode
        methodClefTUI, methodAide = pAides[library + ":" + method]
        # récupérer la description des paramètres de la méthode
        methodParametersAides = []
        if methodParameters is not None:
            methodParametersAides = sorted([(code, desc) for code, desc in pAides.items() if ''.join(code.split('.')[:-1]) == methodClefTUI])
            # mettre à jour les paramètres : ajouter un lien pour chaque paramètre de la méthode vers la partie description
            methodParameters = " ".join("\\hyperref[%s]{%s}" % (methodParametersAides[i][0], param) for i, param in enumerate(sorted(methodParameters.split('_'))))

        # construire les clés de l'explication courante
        dataKey = ('data', dataname)
        dataShortKey = ('data', datanameShort)
        methodKey = ('method', method)
        methodParametersKey = ('parameters', methodParameters)
        libraryKey = ('library', library)

        # récupération du fichier json de résultat d'inférence
        fichierJson = remplaceExtension(pExtensions, pathExplain, '.json').replace("dataExplanations", "dataInference")
        if os.path.exists(fichierJson):
            with open(fichierJson, 'r', encoding="utf-8") as fJson:
                inferJson = json.load(fJson)
        else:
            # Si on ne le trouve pas, on retire toutes les extensions
            for key, dataExtension in dataSuffixes.items():
                fichierJson = fichierJson.replace('%s%s'%(key, dataExtension), '')
                if os.path.exists(fichierJson):
                    with open(fichierJson, 'r', encoding="utf-8") as fJson:
                        inferJson = json.load(fJson)
                        break
                else:
                    inferJson = None

        # recherche du fichier json de résultat d'explication
        fichierJson = remplaceExtension(pExtensions, pathExplain, '.json')
        if os.path.exists(fichierJson):
            with open(fichierJson, 'r', encoding="utf-8") as fJson:
                explJson = json.load(fJson)
        else:
            explJson = None

        # remplir la liste des valeurs de l'explication courante à insérer dans le dictionnaire
        listeExplications = []

        # récupération des plots de l'explication dans le répertoire dataPlotExplanations
        pathPlotExplain = remplaceExtension(pExtensions, pathExplain, '%s.png'%pLegende).replace("dataExplanations", "dataPlotExplanations")  # /!\ directive d'intégration : fichier png
        # ... si le fichier (par simple remplacement de lieu) existe
        if os.path.exists(pathPlotExplain):
            # on ajoute le plot à la liste des explications à rapporter selon le mode de tri demandé
            if pFullReportE == 'data':
                ajout = (methodParametersKey, dataSuffixes, pathPlotExplain, inferJson, explJson)
            else:  # pFullReportE == 'method'
                ajout = (dataShortKey, dataSuffixes, pathPlotExplain, inferJson, explJson)
            if pathPlotExplain not in methodPlotsList:
                listeExplications.append(ajout)
                methodPlotsList.append(pathPlotExplain)
        else:
            # ... sinon, on recherche les plots d'explications avac classes et suffixes potentiels
            listPathPlotExplain = []
            if os.path.exists(pathPlotExplain):
                listPathPlotExplain.append(pathPlotExplain)
            listPathPlotExplain.extend(glob.glob(pathPlotExplain.replace('.png', '--*.png')))
            for filename in listPathPlotExplain:
                copieDataSuffixes = copy.deepcopy(dataSuffixes)
                # on ne rapporte pas les plots avec datasize ou legend /!\ directive d'intégration
                if '--datasize' in filename or '--legend' in filename:
                    continue
                filenameSansPNG = filename.replace('.png', '')
                for key, _ in copieDataSuffixes.items():
                    if key in filenameSansPNG:
                        copieDataSuffixes[key] = filenameSansPNG.split(key)[1].split('--')[0]
                # on ajoute le plot à la liste des explications à rapporter selon le mode de tri demandé
                if pFullReportE == 'data':
                    ajout = (methodParametersKey, copieDataSuffixes, filename, inferJson, explJson)
                else:  # pFullReportE == 'method'
                    ajout = (dataShortKey, copieDataSuffixes, filename, inferJson, explJson)
                if filename not in methodPlotsList:
                    listeExplications.append(ajout)
                    methodPlotsList.append(filename)

        # Si la liste des explications est vide
        if not listeExplications:
            continue

        # ajouter la listeExplications au dictionnaire explanationsDict selon le mode de tri demandé
        if pFullReportE == 'data':
            # tri par data :
            #   § Donnée
            #   §.§ Methode
            #   §.§.§ Bibliothèque
            #           explications
            explanationsDict.setdefault(dataKey, {}).setdefault(methodKey, {}).setdefault(libraryKey, []).extend(listeExplications)
        else:  # pFullReportE == 'method'
            # tri par methode :
            #   § Methode
            #   §.§ Bibliothèque
            #   §.§.§ Parametrages
            #           explications
            explanationsDict.setdefault(methodKey, {}).setdefault(libraryKey, {}).setdefault(methodParametersKey, []).extend(listeExplications)

        # ajouter l'aide de la méthode au dictionnaire pAidesDict
        value = (methodClefTUI, methodAide, methodParametersAides)
        # § Bibliotheque
        # §.§ Methode
        pAidesDict.setdefault(libraryKey, {}).setdefault(methodKey, value)

    # écriture du dictionnaire explanationsDict dans le rapport
    if explanationsDict:
        if pFullReportE == 'data':
            rapportExpl = writeDictInReportExpData(pDictParams, explanationsDict, rapportExpl, repertFullReport, pNbColFullLatexMethod, indexSplit)
        else:  # pFullReportE == 'method'
            rapportExpl = writeDictInReportExpMethod(pDictParams, explanationsDict, rapportExpl, repertFullReport, pNbColFullLatexMethod, indexSplit)
    else:
        print("The folder '%s' does not contain any explanation results of the '%s' use case!"%(os.path.basename(dataProdRoot), pCode))
        return

    # Fin du rapport des explications :
    # - suppression des lignes inutiles
    inutile = "\n%s \\\\\n"%(" &\n" * (pNbColFullLatexMethod - 1))
    while inutile in rapportExpl:
        rapportExpl = rapportExpl.replace(inutile, "\n")
    # - suppression du tag $DATA$
    rapportExpl = rapportExpl.replace("$DATA$", "")

    # ajouter le titre du chapitre dans le rapport
    pRapport = pRapport.replace("$DATA$", "\\chapter{Explanation methods results}\n\n%s$DATA$"%rapportExpl)

    return pRapport, pAidesDict

# ---------------------------------------------------------------------------
## Writing chapter Methods of the full report in LaTeX
# @param pDictParams : parameter dictionary
# @param pRapport : LaTeX report
# @param pAidesDict : elements pour le chapitre d'aide
# @return LaTeX report
def writeChapterMetrics(pDictParams, pRapport, pAidesDict):
    # shortcuts
    pDataProd = pDictParams['dataProd']
    pCode = pDictParams['code']
    pAides = pDictParams['aides']
    pNbColFullLatexMetric = pDictParams['nbColFullLatexMetric']

    colPrint("  - Metrics chapter", "Normal")

    # elements de dépôt du rapport
    dataProdRoot = os.path.dirname(pDataProd)
    repertFullReport = os.path.join(dataProdRoot, "fullReports", pCode)
    # index pour récupérer le répertoire racine du dépôt donneesProd/.../
    indexSplit = len(repertFullReport.split(os.sep)) - 2

    # ajouter le titre du chapitre dans le rapport
    rapportMetr = "$DATA$"

    # dictionnaire pour sauvegarder les résultats des métriques
    metricsDict = {}

    # boucle sur les résultats des métriques
    for pathJson in glob.glob(os.path.join(dataProdRoot, "**", "dataMetrics", pCode, "*.json"), recursive=True):

        # on découpe le répertoire pour en extraire les éléments :
        filenameSplit = pathJson.split(os.sep)
        filename = filenameSplit[-1]                        # nom du fichier d'explication
        filename = filename.replace(".json", "")
        library = filenameSplit[indexSplit]                 # nom de la bibliotheque

        # on ne traite pas les fichiers de metriques avec suffixe --s_  /!\ directive integration
        if "--s_" in filename:
            continue

        # on contrôle si la métrique est spécifique à une donnée  /!\ directive intégration
        dataMetriq = None
        if "--d_" in filename:
            dataMetriq = filename.split("--d_")[1].split('--')[0]
            filename = filename.split("--d_")[0]   # Le nom de fichier est ajusté --d_ est le dernier suffixe /!\ directive integration

        # isolement de la métrique et ses paramères du filename (séparés par __) /!\ directive intégration
        metric, metricParameters = separateParameters(filename)

        # récupérer la description de la métrique
        metricClefTUI, metricAide = pAides[library + ":" + metric]
        # récupérer la description des paramètres de la métrique
        metricParametersAides = []
        if metricParameters is not None:
            metricParametersAides = sorted([(code, desc) for code, desc in pAides.items() if ''.join(code.split('.')[:-1]) == metricClefTUI])
            # mettre à jour les paramètres : ajouter un lien pour chaque paramètre de la métrique vers la partie description
            metricParameters = " ".join("\\hyperref[%s]{%s}" % (metricParametersAides[i][0], param) for i, param in enumerate(sorted(metricParameters.split('_'))))

        # construire les clés de la métrique courante
        metricKey = ('metric', metric)
        metricParamKey = ('parameters', metricParameters)
        libraryKey = ('library', library)

        # récupération du fichier json des métriques
        with open(pathJson, 'r', encoding="utf-8") as fJson:
            metricsJson = json.load(fJson)

        # ajustement du json de métrique dans le cas de traitement de toutes les données
        if "allData" in metricsJson:
            metricsJson = metricsJson["allData"]

        # etablissement de la liste virtuelle des plots à partir des méthodes sur lesquelles la métrique est appliquée
        listeMethodes = []
        # pour chaque element du json de metrique, on ajoute la possibilité d'avoir un plot spécifique pour chaque méthode
        for name, _ in metricsJson.items():
            suffixe = "--m_%s"%name                                                         # /!\ directive intégration
            titre = name
            categorie = 'method'
            listeMethodes.append((suffixe, titre, categorie))

        # ajouter le graph de comparaison dans la liste des plots potentiels de méthodes en tant que métrique
        suffixe = "--g_%s"%"".join(key[0] for key in metricsJson.keys())         # /!\ directive intégration
        titre = list(metricsJson.keys())
        categorie = 'graphique'
        listeMethodes.append((suffixe, titre, categorie))

        # boucle sur la liste virtuelle établie
        valueCompar = []
        methodComparKey = []
        for (suffixe, titre, categorie) in listeMethodes:

            # construire les clés de la méthode
            # - cas d'un graphique de comparaison de méthodes
            if categorie == 'graphique':
                # cas du graph de comparaison
                methodKey = ('comparison of methods', '\\\\'.join(titre))
                methodParametersKey = {}

                for unTitre in titre:
                    # isolement de la methode et ses paramères du titre (séparés par __) /!\ directive intégration
                    method, methodParameters = separateParameters(unTitre)
                    # récupérer la liste des description des paramètres
                    if library + ":" + method not in pAides:
                        methodClefTUI = None
                        methodAide = None
                        methodParametersAides = []
                    else:
                        methodClefTUI, methodAide = pAides[library + ":" + method]
                        # récupérer la description des paramètres de la méthode
                        methodParametersAides = []
                        if methodParameters:
                            methodParametersAides = sorted([(code, desc) for code, desc in pAides.items() if ''.join(code.split('.')[:-1]) == methodClefTUI])
                            # ajouter un lien pour chaque paramètre vers la partie description
                            methodParameters = " ".join("\\hyperref[%s]{%s}" % (methodParametersAides[i][0], param) for i, param in enumerate(sorted(methodParameters.split('_'))))
                        methodParametersKey[method] = methodParameters
                    valueCompar.append((methodClefTUI, methodAide, methodParametersAides))
                    methodComparKey.append(('method', method))
                methodParametersKey = ('method parameters', methodParametersKey)

            else:
                # isolement de la methode et ses paramères du titre (séparés par __) /!\ directive intégration
                method, methodParameters = separateParameters(titre)
                # récupérer la liste des description des paramètres
                methodKey = ('method', method)
                if library + ":" + method not in pAides:
                    methodClefTUI = None
                    methodAide = None
                    methodParametersKey = (None, None)
                else:
                    methodClefTUI, methodAide = pAides[library + ":" + method]
                    # récupérer la description des paramètres de la méthode
                    methodParametersAides = []
                    if methodParameters:
                        methodParametersAides = sorted([(code, desc) for code, desc in pAides.items() if ''.join(code.split('.')[:-1]) == methodClefTUI])
                        # ajouter un lien pour chaque paramètre vers la partie description
                        methodParameters = " ".join("\\hyperref[%s]{%s}" % (methodParametersAides[i][0], param) for i, param in enumerate(sorted(methodParameters.split('_'))))
                    methodParametersKey = ('method parameters', methodParameters)

           # libraryMethodKey = (methodKey[0], libraryKey[1] + "." + methodKey[1])
           # libraryMetricKey = (metricKey[0], libraryKey[1] + "." + metricKey[1])

            # positionnement sur le répertoire des plots des métriques (dataPlotMetrics)
            filename = pathJson.replace(".json", "%s.png"%suffixe).replace("dataMetrics", "dataPlotMetrics")
            if os.path.exists(filename):
                listeMetriques = [(methodParametersKey, dataMetriq, filename)]
            else:
                continue

            # tri par metrique :
            #   § Bibliothèque
            #   §.§ Metrique
            #   §.§.§ parametres-metrique
            #        Methode
            #           metriques
            metricsDict.setdefault(libraryKey, {}).setdefault(metricKey, {}).setdefault(metricParamKey, {}).setdefault(methodKey, []).extend(listeMetriques)

            # ajouter l'aide de la méthode au dictionnaire aidesDict
            value = (methodClefTUI, methodAide, methodParametersAides)
            if methodKey[0] == "comparison of methods":
                for e, v in enumerate(valueCompar):
                    pAidesDict.setdefault(libraryKey, {}).setdefault(methodComparKey[e], v)
            else:
                pAidesDict.setdefault(libraryKey, {}).setdefault(methodKey, value)

        # ajouter l'aide de la métrique au dictionnaire aidesDict
        value = (metricClefTUI, metricAide, metricParametersAides)
        if methodKey[0] == "comparison of methods":
            for e, v in enumerate(valueCompar):
                pAidesDict.setdefault(libraryKey, {}).setdefault(methodComparKey[e], v)
        pAidesDict.setdefault(libraryKey, {}).setdefault(metricKey, value)

    # écriture du dictionnaire metricsDict dans le rapport
    if metricsDict:
        rapportMetr = writeDictInReportMetric(metricsDict, rapportMetr, repertFullReport, pNbColFullLatexMetric, indexSplit)
    else:
        print("The folder '%s' does not contain any metric result of the '%s' use case!"%(os.path.basename(dataProdRoot), pCode))
        return None

    # Fin du rapport des eplications :
    # - suppression des lignes inutiles
    inutile = "\n%s \\\\\n"%(" &\n" * (pNbColFullLatexMetric - 1))
    while inutile in rapportMetr:
        rapportMetr = rapportMetr.replace(inutile, "\n")
    # - suppression du tag $DATA$
    rapportMetr = rapportMetr.replace("$DATA$", "")

    # ajouter le titre du chapitre dans le rapport
    pRapport = pRapport.replace("$DATA$", "\\chapter{Metrics results}\n\n%s$DATA$"%rapportMetr)

    return pRapport, pAidesDict

# ---------------------------------------------------------------------------
## Writing the full report in LaTeX
# @param pDictParams : parameter dictionary
def writeFullReport(pDictParams):
    if pDictParams['fullReport'] == "":
        print("No report part is selected!")
        return
    # shortcuts
    pFullReport = pDictParams['fullReport']
    pUseCase = pDictParams['useCase']
    pAides = pDictParams['aides']
    pFullReportE = pDictParams['fullReportE'] if 'fullReportE' in pDictParams else None

    # recuperation des compléments de données (bande images, etc)
    pDictParams['dataBandPathList'] = None
    if hasattr(pDictParams['pluginUCXAI'].UC, 'UC_dataBandPathList'):
        pDictParams['dataBandPathList'] = pDictParams['pluginUCXAI'].UC.UC_dataBandPathList(pDictParams)

    # créer le répertoire dépôt
    resultSavedOn = os.path.join(os.path.dirname(pDictParams['dataProd']), "fullReports", pDictParams['code'])
    os.makedirs(resultSavedOn, exist_ok=True)
    os.chmod(resultSavedOn, 0o0777)

    # récuperer le template du rapport
    repertkaaActions = os.path.dirname(kaasrc.kaaActions.__file__)
    with open(os.path.join(repertkaaActions, "ressources", "fullReport.tex"), 'r', encoding="utf-8") as f:
        rapport = f.read()

    # ajouter la version de KAA
    rapport = rapport.replace("$VERSION$", kaasrc.kaaActions.KAAVERSION)

    # ajouter le cas d'usage dans le rapport
    rapport = rapport.replace("$USECASE$", pAides['useCase'].replace('_', '\\_'))

    reportName = "%s_fullReport_"%pUseCase
    titre = ""

    # dictionnaire pour sauvegarder l'aide : la description des méthodes et des métriques et leurs paramètres
    aidesDict = {}

    # 1) Chapitre inférences
    rapport = writeChapterInference(pDictParams, rapport)

    # 2) Chapitre explications
    if 'Explanations' in pFullReport:
        titre = "Explanations "
        reportName += "_expl-%s"%pFullReportE
        resWriteChapterMethods = writeChapterMethods(pDictParams, rapport, aidesDict)
        if resWriteChapterMethods is not None:
            rapport, aidesDict = resWriteChapterMethods

    # ---------------------
    # 3) Chapitre métriques
    # ---------------------
    if 'Metrics' in pFullReport:
        if 'Explanations' in pFullReport:
            rapport = rapport.replace("$DATA$", "\\newpage\n$DATA$")
            titre += "and metrics "
        else:
            titre += "Metrics "
        reportName += "_metr"

        resWriteChapterMetrics = writeChapterMetrics(pDictParams, rapport, aidesDict)
        if resWriteChapterMetrics is not None:
            rapport, aidesDict = resWriteChapterMetrics

    # Fin du rapport : suppression du tag $DATA$
    rapport = rapport.replace("$DATA$", "")

    # écriture du dictionnaire aidesDict dans le rapport
    rapport = rapport.replace("$AIDE$", "\\chapter{Libraries, methods and metrics}\n\n$AIDE$")
    rapport = writeAidesDictInReport(aidesDict, rapport)

    # écriture du titre du rapport
    titre += "results"
    rapport = rapport.replace("$TITRE$", titre)

    # sauvegarde du rapport LaTeX
    latexReport = os.path.join(resultSavedOn, "%s.tex"%reportName)
    print("   .LaTeX report generated in %s"%os.path.abspath(latexReport))
    with open(latexReport, 'w', encoding="utf-8") as f:
        f.write(rapport)

    for fileTemplate in ["ETAIA.sty", "titlePage.tex", "ETAIA.png", "ETAIAbandeau.png"]:
        shutil.copyfile(os.path.join(repertkaaActions, "ressources", fileTemplate), os.path.join(resultSavedOn, fileTemplate))

    # compression des données produites (dataPlot)
    builtTGZ(resultSavedOn, rapport.count('\n'))

    # compile latex report
    if ISLATEX:
        latexReportPath = os.path.dirname(latexReport)
        latexReport = os.path.basename(latexReport).replace('.tex', '')
        # LaTeX doit être compilé deux fois pour résoudre les références,
        # la première compilation enregistre les labels et les références, la deuxième les résout.
        os.system("cd %s;pdflatex -interaction nonstopmode %s.tex > /dev/null "%(latexReportPath, latexReport))
        os.system("cd %s;pdflatex -interaction nonstopmode %s.tex > /dev/null "%(latexReportPath, latexReport))
        os.system("cd %s;rm %s.log %s.aux %s.out %s.toc> /dev/null "%(latexReportPath, latexReport, latexReport, latexReport, latexReport))

# ===============================================================================
# end of file
