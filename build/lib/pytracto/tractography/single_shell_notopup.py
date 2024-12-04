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

import glob
from tqdm import tqdm
import json
from nipype import config, logging
logging.update_logging(config)

import logging
from nipype.utils.profiler import log_nodes_cb
import subprocess
from python_on_whales import docker
import shutil

config.enable_debug_mode()
config.set('execution','use_relative_paths','true')
config.set('execution','has_method','content')



############# DC : Node Definition #######################


def execute_single_shell_notopup_preproc_workflow(
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


    callback_log_path = '/home/imabrain/run_stats_preproc.log'

    # Set up the logger if it doesn't exist already
    logger = logging.getLogger('callback')

    if not logger.hasHandlers():  # Avoid adding multiple handlers if logger is already configured
        handler = logging.FileHandler(callback_log_path)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

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


    main_wf.run(plugin=kwargs.get("plugin_processing"), plugin_args={"n_procs": 12,'status_callback' : log_nodes_cb})


#########################################################################################
#################                        SYNBO-DISCO                #####################
#################                 Generate b0 AP                   ######################
#########################################################################################



def process_dwi_json(source_dir,rawdata_folder,derivatives_folder,node_dir,subject_id,session_id,json_file):
    """
    Extract fields from a JSON file to calculate TotalReadoutTime 
    and save the acquisition parameters in a specified format.

    Args:
        json_file (str): Path to the input JSON file.
        output_file (str): Path to the output file (default is 'acqparam.txt').
    """
    try:
        # Load the JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract required fields
        num_phase_encoding_steps = data.get("PhaseEncodingSteps")
        pixel_bandwidth = data.get("PixelBandwidth")
        
        if not num_phase_encoding_steps or not pixel_bandwidth:
            raise ValueError("Missing required fields in the JSON file.")
        
        # Calculate TotalReadoutTime
        total_readout_time = num_phase_encoding_steps / pixel_bandwidth
        
        # Create acqparam content
        acqparam_content = f"""\
0 -1 0 {total_readout_time:.6f}
0 1 0 0
"""

        rawdata_dir = os.path.join(source_dir,rawdata_folder)

        synb0_inputdir = os.path.join(node_dir,"inputs")
        if not os.path.isdir(synb0_inputdir):
            os.mkdir(synb0_inputdir)
        # Write to output file
        with open(os.path.join(synb0_inputdir,"acqparams.txt"), 'w') as f:
            f.write(acqparam_content)
        
        ## get b0 PA and save it to b0.nii.gz
        ## get T1 and save it to T1.nii.gz

        T1_nii = glob.glob(f"{rawdata_dir}/{subject_id}/{session_id}/anat/s*T1w.nii.gz")[0]

        if not os.path.isfile(os.path.join(synb0_inputdir,"T1.nii.gz")):

            shutil.copy(T1_nii,os.path.join(synb0_inputdir,'T1.nii.gz'))

        b0_mif = glob.glob(f"{source_dir}/{derivatives_folder}/derivatives/dwi/preproc/{subject_id}/{session_id}/avg_b0PA.mif")[0]

        if not os.path.isfile(os.path.join(synb0_inputdir,"b0.nii.gz")):
            command = f"mrconvert {b0_mif} {synb0_inputdir}/b0.nii.gz"
            subprocess.run(command,shell = True)

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
#process_dwi_json('sub_ses_dwi.json')



def get_inputs(

    source_dir,
    derivatives_folder,
    rawdata_folder,
    subject_list,
    session_list):

    if not os.path.isdir(os.path.join(source_dir,derivatives_folder)):
        os.mkdir(os.path.join(source_dir,derivatives_folder))

    if not os.path.isdir(os.path.join(source_dir,derivatives_folder,"main_workflow")):
        os.mkdir(os.path.join(source_dir,derivatives_folder,"main_workflow"))

    if not os.path.isdir(os.path.join(source_dir,derivatives_folder,"main_workflow","preproc")):
        os.mkdir(os.path.join(source_dir,derivatives_folder,"main_workflow","preproc"))


    for sub in subject_list:
        for ses in session_list:
            subject_id = "sub-" + sub
            session_id = "ses-" + ses
            identifier = "_ses_id_" + ses + "_subject_id_" + sub
            print(f"Running on {subject_id} - {session_id}")

            if not os.path.isdir(os.path.join(source_dir,derivatives_folder,"main_workflow","preproc",identifier)):
                os.mkdir(os.path.join(source_dir,derivatives_folder,"main_workflow","preproc",identifier))

            synb0_dir = os.path.join(source_dir,derivatives_folder,"main_workflow","preproc",identifier,"synb0")
            if not os.path.isdir(synb0_dir):
                os.mkdir(synb0_dir)

            dwi_dir = os.path.join(source_dir,rawdata_folder,subject_id,session_id,"dwi")
            rawdata_dir = os.path.join(source_dir,rawdata_folder,subject_id,session_id) 
            dwi_json = glob.glob(f"{dwi_dir}/*.json")[0]
            print(dwi_json)

            process_dwi_json(source_dir,rawdata_folder,derivatives_folder,synb0_dir,subject_id,session_id,dwi_json)


    print("Inputs are ready")


def execute_synb0_disco(source_dir,rawdata_folder,derivatives_folder,subject_list,session_list,**kwargs):


    get_inputs(source_dir,derivatives_folder,rawdata_folder,subject_list,session_list)

    ## replace by kwargs get freesurfer license

    freesurfer_bin_path = kwargs.get("freesurfer_path")
    FS_license_file = os.path.join(freesurfer_bin_path, 'license.txt')

    iterate_nb = len(subject_list) * len(session_list)

    for sub in tqdm(subject_list,total = iterate_nb):
        for ses in session_list:
            identifier = f"_ses_id_{ses}_subject_id_{sub}"

            input_synb0 = os.path.join(source_dir,derivatives_folder,"main_workflow","preproc",identifier,"synb0","inputs")
            output_synb0 = os.path.join(source_dir,derivatives_folder,"main_workflow","preproc",identifier,"synb0","outputs")

            if not os.path.isfile(os.path.join(output_synb0,"b0_all.nii.gz")):

                print(os.listdir(input_synb0))
                print(str(os.getuid()))
                       
                output_generator = docker.run(
                    "leonyichencai/synb0-disco:v3.1",
                    ["--user", str(os.getuid()) + ":" + str(os.getgid()),"--notopup",'--memory=48g',"--cpus=12"],
                    volumes=[(input_synb0, "/INPUTS"), (output_synb0, "/OUTPUTS"), (FS_license_file, "/extra/freesurfer/license.txt")],
                    remove=True, stream=True,
                    )
                for stream_type, stream_content in output_generator:
                    print(f"Stream type: {stream_type}, stream content: {stream_content}")

                command_fslmerge = "fslmerge -t {output_synb0}/b0_all.nii.gz {output_synb0}/b0_d_smooth.nii.gz {output_synb0}/b0_u.nii.gz"
                subprocess.run(command_fslmerge,shell = True)


    ## replace by kwargs get freesurfer license
def create_b0_pair(source_dir,rawdata_folder,derivatives_folder,subject_list,session_list,**kwargs):

    freesurfer_bin_path = kwargs.get("freesurfer_path")
    FS_license_file = os.path.join(freesurfer_bin_path, 'license.txt')

    iterate_nb = len(subject_list) * len(session_list)

    for sub in tqdm(subject_list,total = iterate_nb):
        for ses in session_list:
            identifier = f"_ses_id_{ses}_subject_id_{sub}"

            input_synb0 = os.path.join(source_dir,derivatives_folder,"main_workflow","preproc",identifier,"synb0","inputs")
            output_synb0 = os.path.join(source_dir,derivatives_folder,"main_workflow","preproc",identifier,"synb0","outputs")

            command_fslmerge = f"fslmerge -t {output_synb0}/b0_all.nii.gz {output_synb0}/b0_d_smooth.nii.gz {output_synb0}/b0_u.nii.gz"
            subprocess.run(command_fslmerge,shell = True)
             


def execute_single_shell_notopup_tractography_workflow(
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
    sf.inputs.base_directory = source_dir

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

    ############################################################
    ########          Freesurfer  Workflow           ###########
    ############################################################

    os.environ["SUBJECTS_DIR"] = rawdata_dir
    fs_reconall = Node(ReconAll(), name="fs_reconall")
    fs_reconall.inputs.directive = kwargs.get("reconall_param")
    # .inputs.subjects_dir = data_dir
    fs_workflow = Workflow(name="fs_workflow", base_dir=derivatives_dir)
    fs_workflow.config["execution"]["use_caching"] = "True"
    fs_workflow.config["execution"]["hash_method"] = "content"

    fs_workflow.connect(infosource, "subject_id", fs_reconall, "subject_id")
    fs_workflow.connect(sf, "anat", fs_reconall, "T1_files")


    ############################################################
    ########          Preprocessing Workflow           #########
    ############################################################

    ##########       Preproc: Node definition       ############

    ### Topup -> Eddy ###

    # # dwifslpreproc ${pref}_dwi_den_unr.mif ${pref}_dwi_den_unr_preproc.mif -pe_dir PA -rpe_pair -se_epi ${pref}_b0_pair.mif -eddy_options " --slm=linear "
    # dwifslpreproc
    # /mnt/CONHECT_data/pipeline_tmp/main_workflow/preproc/_ses_id_001_subject_id_01/unring/concatenated_denoised_unr.mif
    # preproc.mif -rpe_pair -eddy_options "--slm=linear" -se_epi
    # /mnt/CONHECT_data/pipeline_tmp/main_workflow/preproc/_ses_id_001_subject_id_01/mrcatb0/concatenated.mif
    # -pe_dir j

    dwpreproc = Node(mrt.DWIPreproc(), name="dwpreproc")
    dwpreproc.inputs.rpe_options = "pair"
    dwpreproc.inputs.out_file = "preproc.mif"
    # preproc.inputs.out_grad_mrtrix = "grad.b"    # export final gradient table in MRtrix format
    # linear second level model and replace outliers
    dwpreproc.inputs.eddy_options = kwargs.get("eddyoptions_param")
    dwpreproc.inputs.pe_dir = "AP"

    # Unbias
    biascorrect = Node(mrt.DWIBiasCorrect(), name="biascorrect")
    biascorrect.inputs.use_ants = kwargs.get("useants_param")
    biascorrect.inputs.out_file = "biascorrect.mif"

    ##########           Preproc Connecting the WF         ##########

    wf_preproc = Workflow(name="preproc", base_dir=derivatives_dir)
    wf_preproc.config["execution"]["use_caching"] = "True"
    wf_preproc.config["execution"]["hash_method"] = "content"


    wf_preproc.connect(sf, "dwi_unr", dwpreproc, "in_file")
    wf_preproc.connect(sf,"b0_pair",dwpreproc,"in_epi")
    wf_preproc.connect(dwpreproc,"out_file",biascorrect,"in_file")

    ##################################################################
    #########            Tractography             ####################
    ##################################################################

    ############    Tractography: Nodes definition       #############

    # # Estimation du brain mask : FSL bet

    brainmask = Node(mrt.BrainMask(), name="brainmask")
    brainmask.out_file = "brainmask.mif"

    # DWI2response
    dwiresponse = Node(mrt.ResponseSD(), name="dwiresponse")
    dwiresponse.inputs.algorithm = kwargs.get("fod_algorithm_param")
    dwiresponse.inputs.wm_file = "wm.txt"

    # dwi2fod msmt_csd ${pref}_dwi_preproc.mif -mask ${pref}_mask_preproc.mif
    # ${pref}_wm.txt ${pref}_wmfod.mif ${pref}_gm.txt ${pref}_gmfod.mif
    # ${pref}_csf.txt ${pref}_csffod.mif
    dwi2fod = Node(mrt.ConstrainedSphericalDeconvolution(), name="dwi2fod")
    dwi2fod.inputs.algorithm = kwargs.get("csd_algorithm_param")
    dwi2fod.inputs.wm_txt = "wm.txt"  # ici faire le lien avec dwiresp
    dwi2fod.inputs.wm_odf = "wm.mif"


    gen5tt = Node(mrt.Generate5tt(), name="gen5tt")
    gen5tt.inputs.algorithm = kwargs.get("tt_algorithm_param")
    gen5tt.inputs.out_file = "5tt.mif"

    # dwiextract ${pref}_dwi_preproc.mif - -bzero | mrmath - mean
    # ${pref}_mean_b0_preprocessed.mif -axis 3
    b0_extract = Node(mrt.DWIExtract(), name="b0_extract")
    b0_extract.inputs.bzero = True
    b0_extract.inputs.out_file = "b0_extract.mif"

    avg_b0 = Node(mrt.MRMath(), name="avg_b0")
    avg_b0.inputs.operation = "mean"
    avg_b0.inputs.axis = 3
    avg_b0.inputs.out_file = "avg_b0.mif"

    convertb02nii = Node(mrt.MRConvert(), name="convertb02nii")
    convertb02nii.inputs.out_file = "b0.nii.gz"
    convert5tt2nii = Node(mrt.MRConvert(), name="convert5tt2nii")
    convert5tt2nii.inputs.out_file = "5tt.nii.gz"

    # fslroi ${pref}_5tt_nocoreg.nii.gz ${pref}_5tt_vol0.nii.gz 0 1 #Extract
    # the first volume of the 5tt dataset (since flirt can only use 3D images,
    # not 4D images)
    fslroi = Node(
        fsl.ExtractROI(roi_file="5tt_vol0.nii.gz", t_min=0, t_size=1), name="fslroi"
    )

    # flirt -in ${pref}_mean_b0_preprocessed.nii.gz -ref
    # ${pref}_5tt_vol0.nii.gz -interp nearestneighbour -dof 6 -omat
    # ${pref}_diff2struct_fsl.mat
    flirt = Node(fsl.FLIRT(), name="flirt")
    flirt.inputs.dof = kwargs.get("flirt_dof_param")
    flirt.inputs.interp = kwargs.get("flirt_interp_param")
    flirt.inputs.out_matrix_file = "diff2struct_fsl.mat"

    # transformconvert ${pref}_diff2struct_fsl.mat
    # ${pref}_mean_b0_preprocessed.nii.gz ${pref}_5tt_nocoreg.nii.gz
    # flirt_import ${pref}_diff2struct_mrtrix.txt
    transformconvert = Node(mrt.TransformFSLConvert(), name="transformconvert")
    transformconvert.inputs.flirt_import = True

    # mrtransform ${pref}_5tt_nocoreg.mif -linear ${pref}_diff2struct_mrtrix.txt -inverse ${pref}_5tt_coreg.mif
    # mrtransform ${pref}_T1_raw.mif -linear ${pref}_diff2struct_mrtrix.txt
    # -inverse ${pref}_T1_coreg.mif
    transform5tt = Node(mrt.MRTransform(), name="transform5tt")
    # transform5tt.inputs.invert=True
    transform5tt.inputs.out_file = "5tt_coreg.mif"
    transformT1 = Node(mrt.MRTransform(), name="transformT1")
    # transformT1.inputs.invert=True
    transformT1.inputs.out_file = "T1_coreg.mif"

    # gmwmi
    gmwmi = Node(cmp_mrt.GenerateGMWMInterface(), name="gmwmi")
    gmwmi.inputs.out_file = "gmwmi.mif"

    tckgenDet = Node(mrt.Tractography(), name="tckgenDet")
    tckgenDet.inputs.algorithm = "SD_Stream"
    tckgenDet.inputs.select = kwargs.get("tckgen_ntracks_param")

    tcksift2Det = Node(cmp_mrt.FilterTractogram(), name="tcksift2Det")
    tcksift2Det.inputs.out_file = "sift_tracks.tck"


    #############     Tractography: Connecting the WF    ##################

    wf_tractography = Workflow(name="wf_tractography", base_dir=derivatives_dir)
    wf_tractography.config["execution"]["use_caching"] = "True"
    wf_tractography.config["execution"]["hash_method"] = "content"

    wf_tractography.connect(b0_extract, "out_file", avg_b0, "in_file")
    wf_tractography.connect(avg_b0, "out_file", convertb02nii, "in_file")

    wf_tractography.connect(gen5tt, "out_file", convert5tt2nii, "in_file")

    wf_tractography.connect(convert5tt2nii, "out_file", fslroi, "in_file")
    wf_tractography.connect(convertb02nii, "out_file", flirt, "in_file")
    wf_tractography.connect(fslroi, "roi_file", flirt, "reference")

    wf_tractography.connect(convertb02nii, "out_file", transformconvert, "in_file")
    wf_tractography.connect(flirt, "out_matrix_file", transformconvert, "in_transform")
    wf_tractography.connect(convert5tt2nii, "out_file", transformconvert, "reference")

    wf_tractography.connect(gen5tt, "out_file", transform5tt, "in_files")

    wf_tractography.connect(
        transformconvert, "out_transform", transform5tt, "linear_transform"
    )
    wf_tractography.connect(
        transformconvert, "out_transform", transformT1, "linear_transform"
    )

    wf_tractography.connect(transform5tt, "out_file", gmwmi, "in_file")

    wf_tractography.connect(dwiresponse, "wm_file", dwi2fod, "wm_txt")
    wf_tractography.connect(dwiresponse, "gm_file", dwi2fod, "gm_txt")
    wf_tractography.connect(dwiresponse, "csf_file", dwi2fod, "csf_txt")
    wf_tractography.connect(brainmask, "out_file", dwi2fod, "mask_file")

    wf_tractography.connect(gmwmi, "out_file", tckgenDet, "seed_gmwmi")
    wf_tractography.connect(transform5tt, "out_file", tckgenDet, "act_file")
    wf_tractography.connect(dwi2fod, "wm_odf", tckgenDet, "in_file")

    wf_tractography.connect(tckgenDet, "out_file", tcksift2Det, "in_tracks")
    wf_tractography.connect(transform5tt, "out_file", tcksift2Det, "act_file")
    wf_tractography.connect(dwi2fod, "wm_odf", tcksift2Det, "in_fod")

    #######################################################################
    ############          Connectome construction          ################
    #######################################################################

    connectome = Workflow(name="connectome", base_dir=derivatives_dir)
    connectome.config["execution"]["use_caching"] = "True"
    connectome.config["execution"]["hash_method"] = "content"

    # labelconvert $datadir/anat/$sub_id/mri/aparc.a2009s+aseg.mgz
    # $FREESURFER_HOME/FreeSurferColorLUT.txt
    # ~/miniconda3/share/mrtrix3/labelconvert/fs_a2009s.txt
    # $datadir/results/${sub_id}_${ses_id}_parcels_destrieux.mif -force

    labelconvert = MapNode(
        mrt.LabelConvert(), name="labelconvert", iterfield=["in_file"]
    )
    labelconvert.inputs.in_config = kwargs.get("labelconvert_param")
    labelconvert.inputs.in_lut = kwargs.get("fs_lut_param")

    transform_parcels = MapNode(
        mrt.MRTransform(), name="transform_parcels", iterfield=["in_files"]
    )
    transform_parcels.inputs.out_file = "parcels_coreg.mif"

    tck2connectomeDet = MapNode(
        mrt.BuildConnectome(), name="tck2connectomeDet", iterfield=["in_parc"]
    )
    tck2connectomeDet.inputs.zero_diagonal = True
    tck2connectomeDet.inputs.out_file = "connectome.csv"
    # connectome.connect(tcksift2,'out_tracks',tck2connectome,'in_file')

    connectome.connect(labelconvert, "out_file", transform_parcels, "in_files")
    # connectome.connect(transform_parcels, "out_file", tck2connectome, "in_parc")
    connectome.connect(transform_parcels, "out_file", tck2connectomeDet, "in_parc")

    #######################################################################
    #########         Connecting Workflows together        ################
    #######################################################################

    main_wf = Workflow(name="main_workflow", base_dir=derivatives_dir)
    main_wf.config["execution"]["use_caching"] = "True"
    main_wf.config["execution"]["hash_method"] = "content"

    # main_wf.connect(wf_dc, "sf.dwi_unr", wf_preproc, "preproc.in_file")
    # main_wf.connect(wf_dc, "sf.b0_pair", wf_preproc, "preproc.in_pair")

    #main_wf.connect(wf_dc, "mrconvertAP.out_file", wf_preproc, "b0AP_extract.in_file")
    main_wf.connect(
        wf_preproc, "biascorrect.out_file", wf_tractography, "brainmask.in_file"
    )
    main_wf.connect(
        wf_preproc, "biascorrect.out_file", wf_tractography, "b0_extract.in_file"
    )
    main_wf.connect(
        wf_preproc, "biascorrect.out_file", wf_tractography, "dwiresponse.in_file"
    )
    main_wf.connect(
        wf_preproc, "biascorrect.out_file", wf_tractography, "dwi2fod.in_file"
    )
    main_wf.connect(wf_dc, "sf.anat", wf_tractography, "gen5tt.in_file")
    main_wf.connect(wf_dc, "sf.anat", wf_tractography, "transformT1.in_files")


    main_wf.connect(
        fs_workflow, "fs_reconall.aparc_aseg", connectome, "labelconvert.in_file"
    )
    main_wf.connect(
        wf_tractography,
        "transformconvert.out_transform",
        connectome,
        "transform_parcels.linear_transform",
    )
    # main_wf.connect(
    #     wf_tractography, "tcksift2.out_tracks", connectome, "tck2connectome.in_file"
    # )
    main_wf.connect(
        wf_tractography,
        "tcksift2Det.out_tracks",
        connectome,
        "tck2connectomeDet.in_file",
    )

    main_wf.run(plugin=kwargs.get("plugin_processing"), plugin_args={"n_procs": 12})


