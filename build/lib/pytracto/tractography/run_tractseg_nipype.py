from nipype import SelectFiles, Node, Workflow, DataSink, IdentityInterface, MapNode
from nipype.interfaces.utility import Merge, Function
from bids.layout import BIDSLayout
import nipype.interfaces.mrtrix3 as mrt
from nipype.interfaces import fsl
from nipype.interfaces.fsl import ExtractROI
from nipype.interfaces.freesurfer import ReconAll
import cmtklib.interfaces.mrtrix3 as cmp_mrt
import os
import sys


import interface as tr


tractseg = Node(tr.Tractseg(), name="tractseg")
