![image](documentation/kaa.png) *Aie Confiance...*
https://www.youtube.com/watch?v=2gflQEF1WQU

<div>
    <a href="#">
        <img src="https://img.shields.io/badge/Python-3.9--3.10-efefef">
    </a>
    <a href="#">
        <img src="https://img.shields.io/badge/License-apache2-efefef">
    </a>
</div>

# KAA v25.12


**KAA** is a Python framework allowing to apply several methods and metrics from several dedicated XAI libraries on AI model to verify them.
It is built around a kernel offering a TUI _Text-based User Interface_ and hosting two sets of plugins:
 - the plugins of the explainability libraries called _pluginsXAI_
 - the plugins of the use cases called _pluginsUCXAI_

KAA must be considered as a comprehensibility tool. It is part of these mediation tools allowing to implement explainability methods in a guided way, to facilitate the adjustment of their parameters by adding knowledge of their influence. It then offers appropriate and relevant interfaces and visualizations of results to select the methods and metrics that are most suited to the user’s problem.


In this version of **KAA**, the *AIX360* (v0.3.0), *Alibi* (v0.9.6), *Captum* (v0.7.0), *PAIR saliency* (v0.2.1), *Shap* (v0.44.1) and *Xplique* (v1.4.0) plugins are provided.

Full documentation can be found in `./documentation/Kaa_User_and_Integration_Manual.pdf`

## Quick Start

**KAA** requires a version of python between 3.9 and 3.10 and several libraries including Tensorflow and Numpy. Installation can be done:

1. using Pypi:

```python
pip install KAA-XAI
```

2. via downlading the v25.12 tag on our github:

Option 1: Using Git
```bash
git clone https://github.com/IRT-Saint-Exupery/KAA.git
cd KAA
git checkout tags/v25.12
```
Option 2: Download the ZIP archive
```bash
wget https://github.com/IRT-Saint-Exupery/KAA/archive/refs/tags/v25.12.zip
unzip v25.12.zip
cd KAA-25.12
```

Install the requirements:

```
pip install -r requirements.txt
```
Then install the XAI libraries you want:


```python
pip install -r requirementsXAIlibs.txt
```

Now that **KAA** is installed, you can launch the *TUI* **KAA** .

```python
python3 kaa/kaa.py -u example/pluginsUCXAI/ -b example/UseCase/ -r ~/KAA_example
```

or execute a command file of the example:

```python
python3 kaa/kaa.py -u example/pluginsUCXAI/ -b example/UseCase/ -r ~/KAA_example -c example/example.cmd
```
The results are available in the *-r* path:
```
~/KAA_example
+-- fullReports
|   +-- Resnet
|       +-- UCRenaultWeldingResnet_fullReport__expl-data.pdf
+-- Xplique
    +-- Occlusion__bz64_pz35_ps3_ov1
    |   +-- contactSheet.pdf
    +-- Rise__bz64_ns2000_gz7_pp0-5
        +-- contactSheet.pdf
```
