# Pytracto

## Python package for diffusion MRI tractography and connectivity

**Author : François Ramon**

Uses nipype workflows, on interfaces of Mrtrix3, FSL, freesurfer, ANTs and other neuroimaging softwares

## Installation 

### Neuroimaging sofware requirements : 

- mrtrix3 (installed with condo install mrtrix3)
- FSL
- Freesurfer 7.4.1
- ANTs

### Python packages requirements :

Most important packages with version such as nipype are in setup.py and automatically installed with pip install
For secondary packages, run

` pip install -r requirements.txt`

To install : 

`git clone https://github.com/FRramon/pytracto.git`
`cd pytracto`

Navigate in pytracto path and type in terminal:

`pip install .` or `python setup.py install`

Pytracto is then *installed*.

