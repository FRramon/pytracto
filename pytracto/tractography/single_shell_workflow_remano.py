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
import pandas as pd

from nipype import config, logging

config.enable_debug_mode()
config.set('execution','use_relative_paths','true')
config.set('execution','has_method','content')

logging.update_logging(config)


############# DC : Node Definition #######################


def execute_single_shell_workflow_remano(
    source_dir: str,
    rawdata_dir: str,
    derivatives_dir: str,
    subject_list: list,
    session_list: str,
    templates: dict,
    csv_file:str,
    **kwargs
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

    def get_folder_paths(subject_id, ses_id, csv_file):
        import pandas as pd
        # Format the subject_id and ses_id to match the CSV file
        formatted_subject_id = f'sub-{subject_id}'
        formatted_ses_id = f'ses-{ses_id}'

        df = pd.read_csv(csv_file)
        dwiPA_row = df[(df['subject_id'] == formatted_subject_id) & (df['session_id'] == formatted_ses_id) & (df['modality'] == 'dwi')]
        dwiAP_row = df[(df['subject_id'] == formatted_subject_id) & (df['session_id'] == formatted_ses_id) & (df['modality'] == 'fmap')]
        anat_row = df[(df['subject_id'] == formatted_subject_id) & (df['session_id'] == formatted_ses_id) & (df['modality'] == 'anat')]
        if not dwiPA_row.empty and not dwiAP_row.empty and not anat_row.empty:
            dwiPA_folder = dwiPA_row['folder'].values[0]
            dwiAP_folder = dwiAP_row['folder'].values[0]
            anat_folder = anat_row['folder'].values[0]
            return dwiPA_folder, dwiAP_folder, anat_folder
        else:
            raise ValueError(f"No matching rows found for subject_id={formatted_subject_id} and ses_id={formatted_ses_id}")

    infosource = Node(
        IdentityInterface(fields=["subject_id", "ses_id"]), name="infosource"
    )
    infosource.iterables = [("subject_id", subject_list),("ses_id", session_list)]

    get_folders = Node(
        Function(
            input_names=["subject_id", "ses_id", "csv_file"],
            output_names=["dwiPA_folder", "dwiAP_folder","anat_folder"],
            function=get_folder_paths
        ),
        name="get_folders"
    )
    get_folders.inputs.csv_file = csv_file

    sf = Node(SelectFiles({
        'dwiPA': 'source_data/sub-{subject_id}/ses-{ses_id}/{dwiPA_folder}/*',
        'dwiAP': 'source_data/sub-{subject_id}/ses-{ses_id}/{dwiAP_folder}/*',
        'anat' : 'source_data/sub-{subject_id}/ses-{ses_id}/{anat_folder}/*'
    }), name="sf")
    sf.inputs.base_directory = source_dir

    # Conversion des DWI PA en .mif (utilisation du nifti, bvec et bval) +
    # Concatenation
    mrconvertPA = Node(
        mrt.MRConvert(), name="mrconvertPA"
    )
    # mrcatPA = Node(mrt.MRCat(), name="mrcatPA")

    # Conversion du DWI AP en .mif avec le nifti, bvec, bval
    mrconvertAP = Node(
        mrt.MRConvert(), name="mrconvertAP"
    )
    # mrconvertAP = Node(mrt.MRConvert(),name = "mrconvertAP")
    # mrcatAP = Node(mrt.MRCat(), name="mrcatAP")

    ############# DC : Connecting the WF #######################

    wf_dc = Workflow(name="wf_dc", base_dir=derivatives_dir)
    wf_dc.config["execution"]["use_caching"] = "True"
    wf_dc.config["execution"]["hash_method"] = "content"

    wf_dc.connect(infosource, "subject_id", get_folders, "subject_id")
    wf_dc.connect(infosource, "ses_id", get_folders, "ses_id")

    wf_dc.connect(infosource, "subject_id", sf, "subject_id")
    wf_dc.connect(infosource, "ses_id", sf, "ses_id")

    wf_dc.connect(get_folders, "dwiPA_folder", sf, "dwiPA_folder")
    wf_dc.connect(get_folders, "dwiAP_folder", sf, "dwiAP_folder")
    wf_dc.connect(get_folders, "anat_folder", sf, "anat_folder")

    wf_dc.connect(sf, "dwiPA", mrconvertPA, "in_file")
    wf_dc.connect(sf, "dwiAP", mrconvertAP, "in_file")

    # wf_dc.connect(mrconvertPA, "out_file", mrcatPA, "in_files")
    # wf_dc.connect(mrconvertAP, "out_file", mrcatAP, "in_files")


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

    # extract b=0 channels from the DWI PA:

    b0AP_extract = Node(mrt.DWIExtract(), name="b0AP_extract")
    b0AP_extract.inputs.bzero = True
    b0AP_extract.inputs.out_file = "b0AP.mif"

    # Mean b=0 AP
    avg_b0AP = Node(mrt.MRMath(), name="avg_b0AP")
    avg_b0AP.inputs.operation = "mean"
    avg_b0AP.inputs.axis = 3
    avg_b0AP.inputs.out_file = "avg_b0AP.mif"

    # Concat B=0 in reverse phase directions
    merger_preproc = Node(Merge(2), name="merger")

    mrcatb0 = Node(mrt.MRCat(), name="mrcatb0")
    mrcatb0.inputs.axis = 3

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
    dwpreproc.inputs.pe_dir = "PA"

    # Unbias
    biascorrect = Node(mrt.DWIBiasCorrect(), name="biascorrect")
    biascorrect.inputs.use_ants = kwargs.get("useants_param")
    biascorrect.inputs.out_file = "biascorrect.mif"

    ##########           Preproc Connecting the WF         ##########

    wf_preproc = Workflow(name="preproc", base_dir=derivatives_dir)
    wf_preproc.config["execution"]["use_caching"] = "True"
    wf_preproc.config["execution"]["hash_method"] = "content"

    wf_preproc.connect(denoise, "out_file", unring, "in_file")
    wf_preproc.connect(unring, "out_file", b0PA_extract, "in_file")
    wf_preproc.connect(b0PA_extract, "out_file", avg_b0PA, "in_file")
    wf_preproc.connect(b0AP_extract, "out_file", avg_b0AP, "in_file")

    wf_preproc.connect(avg_b0PA, "out_file", merger_preproc, "in1")
    wf_preproc.connect(avg_b0AP, "out_file", merger_preproc, "in2")
    wf_preproc.connect(merger_preproc, "out", mrcatb0, "in_files")
    wf_preproc.connect(unring, "out_file", dwpreproc, "in_file")
    wf_preproc.connect(mrcatb0, "out_file", dwpreproc, "in_epi")
    wf_preproc.connect(dwpreproc, "out_file", biascorrect, "in_file")

    ##################################################################
    #########            Tractography             ####################
    ##################################################################

    ############    Tractography: Nodes definition       #############

    # # Estimation du brain mask : FSL bet
    # convert_mask2nii = Node(mrt.MRConvert(),name = "convert_mask2nii")
    # convert_mask2nii.inputs.out_file = "dwi_preproc.nii"

    # bet_mask = Node(fsl.BET(),name = 'bet_mask')
    # bet_mask.inputs.mask = True
    # # bet_mask.inputs.mask_file = 'mask.nii'

    # convert_mask2mif = Node(mrt.MRConvert(),name = "convert_mask2mif")
    # convert_mask2mif.inputs.out_file = 'mask_preproc.mif'

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

    # tckgen -act ${pref}_5tt_coreg.mif -backtrack -seed_gmwmi
    # ${pref}_gmwmSeed_coreg.mif -select 10000000 ${pref}_wmfod_norm.mif
    # ${pref}_tracks_10mio.tck
    tckgen = Node(mrt.Tractography(), name="tckgen")
    tckgen.inputs.algorithm = kwargs.get("tckgen_algorithm_param")
    tckgen.inputs.select = kwargs.get("tckgen_ntracks_param")
    tckgen.inputs.backtrack = kwargs.get("tckgen_backtrack_param")

    # tckgenDet = Node(mrt.Tractography(), name="tckgenDet")
    # tckgenDet.inputs.algorithm = "SD_Stream"
    # tckgenDet.inputs.select = kwargs.get("tckgen_ntracks_param")

    tcksift2 = Node(cmp_mrt.FilterTractogram(), name="tcksift2")
    tcksift2.inputs.out_file = "sift_tracks.tck"

    tcksift2Det = Node(cmp_mrt.FilterTractogram(), name="tcksift2Det")
    tcksift2Det.inputs.out_file = "sift_tracks.tck"

    # tcksift2.inputs.out_tracks = 'sift_tracks.tck'

    # tcksift2.inputs.out_weights = 'finaltracks.tck'

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
    wf_tractography.connect(brainmask, "out_file", dwi2fod, "mask_file")

    wf_tractography.connect(gmwmi, "out_file", tckgen, "seed_gmwmi")
    wf_tractography.connect(transform5tt, "out_file", tckgen, "act_file")
    wf_tractography.connect(dwi2fod, "wm_odf", tckgen, "in_file")

    # wf_tractography.connect(gmwmi, "out_file", tckgenDet, "seed_gmwmi")
    # wf_tractography.connect(transform5tt, "out_file", tckgenDet, "act_file")
    # wf_tractography.connect(dwi2fod, "wm_odf", tckgenDet, "in_file")

    wf_tractography.connect(tckgen, "out_file", tcksift2, "in_tracks")
    wf_tractography.connect(transform5tt, "out_file", tcksift2, "act_file")
    wf_tractography.connect(dwi2fod, "wm_odf", tcksift2, "in_fod")

    # wf_tractography.connect(tckgenDet, "out_file", tcksift2Det, "in_tracks")
    # wf_tractography.connect(transform5tt, "out_file", tcksift2Det, "act_file")
    # wf_tractography.connect(dwi2fod, "wm_odf", tcksift2Det, "in_fod")



    #######################################################################
    #########         Connecting Workflows together        ################
    #######################################################################

    main_wf = Workflow(name="main_workflow", base_dir=derivatives_dir)
    main_wf.config["execution"]["use_caching"] = "True"
    main_wf.config["execution"]["hash_method"] = "content"

    main_wf.connect(wf_dc, "mrconvertPA.out_file", wf_preproc, "denoise.in_file")
    main_wf.connect(wf_dc, "mrconvertAP.out_file", wf_preproc, "b0AP_extract.in_file")
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



    main_wf.write_graph(graph2use="colored", dotfilename="./pipeline_graph.dot")


    main_wf.run(plugin=kwargs.get("plugin_processing"), plugin_args={"n_procs": 12})
