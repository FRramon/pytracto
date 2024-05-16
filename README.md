# Pytracto

## Python package for diffusion MRI tractography and connectivity

Author : **François Ramon**

Mail : francois.ramon@ghu-paris.fr

Uses nipype workflows, on interfaces of Mrtrix3, FSL, freesurfer, ANTs and other neuroimaging softwares

## Installation 

### Neuroimaging sofware requirements : 

- mrtrix3 (installed with `conda install -c mrtrix3 mrtrix3`)
- FSL [^1]
- Freesurfer 7.4.1 [^2]
- ANTs [^3]

### Python packages requirements :

Most important packages with version such as nipype are in setup.py and automatically installed with pip install
For secondary packages, run

` pip install -r requirements.txt`

To install : 

`git clone https://github.com/FRramon/pytracto.git`

`cd pytracto`

Navigate in pytracto path and type in terminal:

`pip install .` or ```python setup.py install```

Pytracto is then *installed*.

## Documentation

A first documentation is available [here](https://frramon.github.io/pytracto/pytracto.html)

## Usage

Typical usage make use of two scripts:
-	run_parameters.py a file containing dictionaries of parameters to be use along the pipeline
-	run_pipeline.py, a file containing commands to execute pipelines.

[^1]: [ https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation]
[^2]: [ https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall]
[^3]: [https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS]
