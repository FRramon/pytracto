Installation
============

Neuroimaging software requirements:
-----------------------------------

- mrtrix3 (installed with ``conda install -c mrtrix3 mrtrix3``)
- FSL [1]_
- Freesurfer 7.4.1 [2]_
- ANTs [3]_

Python packages requirements:
-----------------------------

Most important packages with version such as nipype are in setup.py and automatically installed with pip install.
For secondary packages, run


.. code-block:: bash

    pip install -r requirements.txt



To install:

.. code-block:: bash

    git clone https://github.com/FRramon/pytracto.git
    cd pytracto

Navigate in pytracto path and type in terminal:

``pip install .`` or ``python setup.py install``

Pytracto is then *installed*.

.. [1] https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation
.. [2] https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall
.. [3] https://github.com/ANTsX/ANTs/wiki/Compiling-ANTs-on-Linux-and-Mac-OS





