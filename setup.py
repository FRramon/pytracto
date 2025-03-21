from setuptools import setup, find_packages

setup(
    name="pytracto",
    version="0.1",
    author="François Ramon",
    author_email="francois.ramon@orange.fr",
    description="A python package for diffusion MRI tractography and connectivity, using interfaces of mrtrix3, fsl, freesurfer, ants, connectomemapper",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=["pytracto", "pytracto.QA_check","pytracto.BIDS_formatting","pytracto.tractography","pytracto.matrixescreation","pytracto.bundlesegmentation"],
    install_requires=[
        "python-on-whales>=0.71",
        "pybids>=0.16",
        "nipype==1.8.6",
        "connectomemapper>=3.1",
        "seaborn",
        "pandas",
        "numpy",
        "dmri-amico",
        "matplotlib",
        "sympy",
        "dipy",
        # 'dmri-amico @ git+https://github.com/daducci/AMICO.git#egg=dmri-amico'
    ],
)
#'dmri-amico>=2.0.1'
