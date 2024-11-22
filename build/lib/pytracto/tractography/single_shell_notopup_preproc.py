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

from nipype import config, logging

config.enable_debug_mode()
config.set('execution','use_relative_paths','true')
config.set('execution','has_method','content')

logging.update_logging(config)


############# DC : Node Definition #######################


def execute_single_shell_notopup_workflow(
    source_dir: str,
    rawdata_dir: str,
    derivatives_dir: str,
    subject_list: list,
    session_list: str,
    templates: dict,
    **kwargs,
):
    """
    Workflow for diffusion MRI tractography and connectivity matrixes creation.
    For single shell diffusion MRI data

    Args:
          source_dir (str): base directory 
          rawdata_dir (str):  path to nifti files
          derivatives_dir (str): chosen derivatives folder
          subject_list (list[str]): subjects list in the format ['01','02','03']
          session_list (str): session id
          **kwargs: keywords argument for specific pipeline parameters

    """

    infosource = Node(
        IdentityInterface(fields=["subject_id", "ses_id"]), name="infosource"
    )
    infosource.iterables = [("subject_id", subject_list),("ses_id", session_list)]

    sf = Node(SelectFiles(templates), name="sf")
    sf.inputs.base_directory = rawdata_dir

        # Datasink - creates output folder for important outputs
    datasink = Node(DataSink(base_directory=derivatives_dir,
                             container='derivatives'),
                    name="datasink")

    ## Use the following DataSink output substitutions
    substitutions = [('_subject_id_', 'sub-'),
                     ('_ses_id_','ses-'),
                     ('_concatenated_', ''),
                     ('_roi', '')
                     ]

    subjFolders = [
        ('ses-%ssub-%s' % (session_id, subject_id), 'sub-%s/ses-%s' % (subject_id, session_id))
        for subject_id in subject_list
        for session_id in session_list  
    ]
    substitutions.extend(subjFolders)
    datasink.inputs.substitutions = substitutions


    # Conversion des DWI PA en .mif (utilisation du nifti, bvec et bval) +
    # Concatenation
    mrconvertPA = Node(
        mrt.MRConvert(), name="mrconvertPA"
    )
 
    ############# DC : Connecting the WF #######################

    wf_dc = Workflow(name="wf_dc", base_dir=derivatives_dir)
    wf_dc.config["execution"]["use_caching"] = "True"
    wf_dc.config["execution"]["hash_method"] = "content"

    wf_dc.connect(infosource, "subject_id", sf, "subject_id")
    wf_dc.connect(infosource, "ses_id", sf, "ses_id")

    wf_dc.connect(sf, "dwiPA", mrconvertPA, "in_file")
    wf_dc.connect(sf, "bvecPA", mrconvertPA, "in_bvec")
    wf_dc.connect(sf, "bvalPA", mrconvertPA, "in_bval")


    ############################################################
    ########          Preprocessing Workflow           #########
    ############################################################

    ##########       Preproc: Node definition       ############

    ############# Denoising + Unring #############
    denoise = Node(mrt.DWIDenoise(), name="denoise")
    unring = Node(mrt.MRDeGibbs(), name="unring")

    # extract b=0 channels from the DWI PA:
    b0PA_extract = Node(mrt.DWIExtract(), name="b0PA_extract")
    b0PA_extract.inputs.bzero = True
    b0PA_extract.inputs.out_file = "b0PA.mif"

    # Mean b=0 PA
    avg_b0PA = Node(mrt.MRMath(), name="avg_b0PA")
    avg_b0PA.inputs.operation = "mean"
    avg_b0PA.inputs.axis = 3
    avg_b0PA.inputs.out_file = "avg_b0PA.mif"

 

    ##########           Preproc Connecting the WF         ##########

    wf_preproc = Workflow(name="preproc", base_dir=derivatives_dir)
    wf_preproc.config["execution"]["use_caching"] = "True"
    wf_preproc.config["execution"]["hash_method"] = "content"

    wf_preproc.connect(denoise, "out_file", unring, "in_file")
    wf_preproc.connect(unring, "out_file", b0PA_extract, "in_file")
    wf_preproc.connect(b0PA_extract, "out_file", avg_b0PA, "in_file")


    #######################################################################
    #########         Connecting Workflows together        ################
    #######################################################################

    main_wf = Workflow(name="main_workflow", base_dir=derivatives_dir)
    main_wf.config["execution"]["use_caching"] = "True"
    main_wf.config["execution"]["hash_method"] = "content"

    main_wf.connect(wf_dc, "mrconvertPA.out_file", wf_preproc, "denoise.in_file")

    main_wf.connect([

        (wf_preproc, datasink, [('denoise.out_file', 'dwi.preproc.@denoise')]),
        (wf_preproc, datasink, [('unring.out_file', 'dwi.preproc.@unr')]),
        (wf_preproc, datasink, [('avg_b0PA.out_file', 'dwi.preproc.@b0')])

    

        ])

    main_wf.run(plugin=kwargs.get("plugin_processing"), plugin_args={"n_procs": 12})
