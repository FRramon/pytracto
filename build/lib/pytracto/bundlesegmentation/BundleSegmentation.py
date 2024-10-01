#################################################################################################
###                       Bundle Segmentation based on CSD in MNI space                       ###
# #
# #
# This script comprises a series of Bash commands executed in the shell. 						#
# It assumes the prior execution of the pipeline on the specified subject_list and session_list.#
# The script orchestrates the following operations:												#
# #
# 1. Conversion of Diffusion Weighted Imaging (DWI) data to NIfTI format,						#
#    Computation of Fractional Anisotropy (FA), and registration to the MNI standard space.		#
# #
# 2. TractSeg execution, encompassing bundle segmentation, endings segmentation, 				#
#    Tract Orientation Maps (TOM) computation, bundle tracking, and tractometry analysis.		#
# #
# 3. Masking of the initial tractography based on specific criteria.							#
# #
# 4. Visualization of the obtained segmentations.												#
# #
#################################################################################################


import os
import sys
import subprocess
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


#from pytracto.bundlesegmentation.BundleSegmentationParameters import *



## Dans kwargs : verbose et mni file

def bundle_segmentation(
    source_dir: str,
    subject_list: list,
    ses_list: list,
    derivatives_folder :str,
    **kwargs
    ):
    """
    Performs bundle segmentation using tractseg.
    DWI images are first registered to MNI152 space using a FA map.
    Tractseg segments into 72 bundles, using a U-net architecture
    All 72 bundles are registered back to subject DWI space using inverse transform

    Args:
            source_dir (str): source directory of the DICOM
            subject_list (list[str]): list of subjects
            ses_list (list[int]): list of sessions
    """

    mni_file = kwargs.get("mni_fa_filepath")#source_dir + "/code/MNI_FA_template.nii.gz"
    verbose = kwargs.get("verbose")

    for sub in subject_list:
        for ses in ses_list:
            # Set up ids and identifier
            subject_id = "sub-" + sub
            session_id = "ses-" + ses
            identifier = "_ses_id_" + ses + "_subject_id_" + sub

            print(f"Running on {subject_id} - {session_id}")

            # Set up directories
            main_workflow_dir = source_dir + "/" + derivatives_folder + "/main_workflow"
            dwipreproc_dir = os.path.join(
                main_workflow_dir, "preproc", identifier, "biascorrect"
            )
            tracto_dir = os.path.join(main_workflow_dir, "wf_tractography", identifier)
            freesurfer_dir = os.path.join(
                main_workflow_dir, "fs_workflow", identifier, "fs_reconall", sub, "mri"
            )
            connectome_dir = os.path.join(main_workflow_dir, "connectome", identifier)

            raw_dir = os.path.join(main_workflow_dir, "bundle_segmentation")
            if not os.path.exists(raw_dir):
                os.mkdir(raw_dir)

            bundle_dir = os.path.join(raw_dir, identifier)
            if not os.path.exists(bundle_dir):
                os.mkdir(bundle_dir)

            #####################

            # Copy preprocessed DWI to the bundle directory
            dwimif = bundle_dir + "/DWI.mif"
            if not os.path.isfile(dwimif):
                print("--- [Node] : copying DWIs")
                command_cat = (
                    f"cp {dwipreproc_dir}/biascorrect.mif {bundle_dir}/DWI.mif"
                )
                subprocess.run(command_cat, shell=True)
            elif verbose == True:
                print("--- [Node] : DWI copying already done")

            # Convert DWI to Nifti
            dwinii = bundle_dir + "/DWI.nii.gz"
            if not os.path.isfile(dwinii):
                print("--- [Node] : Convert dwi to nifti")
                command_convert_dwi = f"mrconvert {bundle_dir}/DWI.mif {bundle_dir}/DWI.nii.gz -export_grad_fsl {bundle_dir}/bvec.bvecs {bundle_dir}/bval.bvals -force"
                subprocess.run(command_convert_dwi, shell=True)
            elif verbose == True:
                print("--- [Node] : DWI conversion from mif to nifti already done")

            # Create a mask of DWI
            maskmif = bundle_dir + "/brainmask.mif"
            if not os.path.isfile(maskmif):
                print("--- [Node] : Create Mask")
                command_create_mask = f"dwi2mask {bundle_dir}/DWI.mif {bundle_dir}/brainmask.mif -force"
                subprocess.run(command_create_mask, shell=True)
            elif verbose == True:
                print("--- [Node] : Mask creation already done")


            #convert the mask to nii
            masknii = bundle_dir + "/brainmask.nii.gz"
            if not os.path.isfile(masknii):
                print("--- [Node] : Convert Mask to nifti")
                command_convert_mask = f"mrconvert {bundle_dir}/brainmask.mif {bundle_dir}/brainmask.nii.gz -force"
                subprocess.run(command_convert_mask, shell=True)
            elif verbose == True:
                print("--- [Node] : Mask conversion to nifti already done")

            # Compute FA on the DWI using the diffusion tensor
            FAnii = bundle_dir + "/FA.nii.gz"
            if not os.path.isfile(FAnii):
                print("--- [Node] : Computing FA for MNI registration")
                command_calcFA = f"calc_FA -i {bundle_dir}/DWI.nii.gz -o {bundle_dir}/FA.nii.gz --bvals {bundle_dir}/bval.bvals --bvecs {bundle_dir}/bvec.bvecs --brain_mask {bundle_dir}/brainmask.nii.gz"
                subprocess.run(command_calcFA, shell=True)
            elif verbose == True:
                print("--- [Node] : FA already computed")

            # Computing the transformation matrix between MNI's FA and subject space FA
            FAMNInii = bundle_dir + "/FA_MNI.nii.gz"
            if not os.path.isfile(FAMNInii):
                print("--- [Node] : Computing flirt mat for MNI registration")
                command_calcFA = f"flirt -ref {mni_file} -in {bundle_dir}/FA.nii.gz -out {bundle_dir}/FA_MNI.nii.gz -omat {bundle_dir}/FA_2_MNI.mat -dof 6 -cost mutualinfo -searchcost mutualinfo"
                subprocess.run(command_calcFA, shell=True)
            elif verbose == True:
                print("--- [Node] : MNI registration already applied to FA")

            # Apply transformation matrix on the diffusion image
            diffusion_mni_nii = bundle_dir + "/Diffusion_MNI.nii.gz"
            if not os.path.isfile(diffusion_mni_nii):
                print("--- [Node] : Apply transformation MNI registration on dwi")
                command_1 = f"flirt -ref {mni_file} -in {bundle_dir}/DWI.nii.gz -out {bundle_dir}/Diffusion_MNI.nii.gz -applyxfm -init {bundle_dir}/FA_2_MNI.mat -dof 6"
                subprocess.run(command_1, shell=True)

                command_2 = f"cp {bundle_dir}/bval.bvals {bundle_dir}/MNI_bval.bvals"
                subprocess.run(command_2, shell=True)

                command_3 = f"rotate_bvecs -i {bundle_dir}/bvec.bvecs -t {bundle_dir}/FA_2_MNI.mat -o {bundle_dir}/MNI_bvec.bvecs"
                subprocess.run(command_3, shell=True)
            elif verbose == True:
                print("--- [Node] : MNI registration already applied to DWI")

            # Prepare the folders for tractseg
            outputdir = bundle_dir + "/tractseg_output"
            if not os.path.exists(outputdir):
                print("--- [Node] : Creating output directory")
                os.mkdir(outputdir)
            elif verbose == True:
                print("--- [Node] : /tractseg_output directory already created  ")

            # Apply tractseg : Bundle segmentation
            segdir = outputdir + "/bundle_segmentations"
            if not os.path.exists(segdir) or not os.listdir(segdir) :
                os.makedirs(segdir,exist_ok = True)
                print("apply TractSeg")
                command = f"TractSeg -i {bundle_dir}/Diffusion_MNI.nii.gz -o {bundle_dir}/tractseg_output --output_type tract_segmentation --raw_diffusion_input --bvals {bundle_dir}/MNI_bval.bvals --bvecs {bundle_dir}/MNI_bvec.bvecs --csd_type csd_msmt --super_resolution"
                subprocess.run(command, shell=True)
                # command_rm = f'rm {segdir}/.tck'
                # subprocess.run(command_rm,shell = True)
            elif verbose == True:
                print("--- [Node] : Tractseg already segmented bundle volumes")

            # Apply tractseg : Ending segmentation
            enddir = outputdir + "/endings_segmentations"
            if not os.path.exists(enddir) or not os.listdir(enddir):
                os.makedirs(enddir,exist_ok = True)
                print("apply TractSeg")
                command = f"TractSeg -i {bundle_dir}/tractseg_output/peaks.nii.gz -o {bundle_dir}/tractseg_output --output_type endings_segmentation"
                subprocess.run(command, shell=True)
            elif verbose == True:
                print("--- [Node] : Tractseg already segmented endings volumes")

            # Apply tractseg : TOM segmentation
            TOMdir = outputdir + "/TOM"
            if not os.path.exists(TOMdir) or not os.listdir(TOMdir):
                os.makedirs(TOMdir,exist_ok = True)
                print("apply TractSeg")
                command = f"TractSeg -i {bundle_dir}/tractseg_output/peaks.nii.gz -o {bundle_dir}/tractseg_output --output_type TOM"
                subprocess.run(command, shell=True)
            elif verbose == True:
                print("--- [Node] : Tractseg already segmented bundle volumes")

            # Perform tracking inside the mask bundle, following peaks, between start and end regions
            Trackingdir = outputdir + "/TOM_trackings"
            if not os.path.exists(Trackingdir) or not os.listdir(Trackingdir):
                os.makedirs(Trackingdir,exist_ok = True)
                print("apply TractSeg")
                command = f"Tracking -i {outputdir}/peaks.nii.gz -o {bundle_dir}/tractseg_output --nr_fibers 5000"
                subprocess.run(command, shell=True)
            elif verbose == True:
                print("--- [Node] : Tractseg already segmented bundle volumes")

            # Compute the inverse transformation matrix to go back to subject space
            mni2fa = bundle_dir + "/MNI_2_FA.mat"
            if not os.path.isfile(mni2fa):
                command = f"convert_xfm -omat {bundle_dir}/MNI_2_FA.mat -inverse {bundle_dir}/FA_2_MNI.mat"
                print(command)
                subprocess.run(command, shell=True)
            elif verbose == True:
                print("--- [Node] : MNI to FA registration  matrix already created")

            # Moving bundles to subject space
            segSubject = outputdir + "/segmentation_subject_space"
            if not os.path.exists(segSubject) or not os.listdir(segSubject):
                os.makedirs(segSubject,exist_ok = True)
                print("--- [Node] : Moving bundles masks to subject space")
                bundles_MNI = os.listdir(
                    os.path.join(outputdir, "bundle_segmentations")
                )

                for bundles in bundles_MNI:
                    if verbose:
                        print(f"Moving {bundles} to subject space")
                    command = f"flirt -ref {bundle_dir}/FA.nii.gz -in {segdir}/{bundles} -out {segSubject}/subject_space_{bundles} -applyxfm -init {bundle_dir}/MNI_2_FA.mat -dof 6 -interp spline"
                    subprocess.run(command, shell=True)
            elif verbose == True:
                print("--- [Node] : Bundles already transformed to subject space")

            # Invert the masks binary
            segInverse = outputdir + "/segmentation_subject_space_inverse"
            if not os.path.exists(segInverse) or not os.listdir(segInverse):
                os.makedirs(segInverse,exist_ok = True)
                print("--- [Node] : Inversing pixels in bundle masks")
                bundles_subject = os.listdir(segSubject)
                for bundles in bundles_subject:
                    if verbose:
                        print(f"	--- Inversing {bundles}")
                    tract_name = bundles[14:-7] + ".mif"
                    command = f"mrthreshold {segSubject}/{bundles} -invert {segInverse}/{tract_name} -force"
                    subprocess.run(command, shell=True)
            elif verbose == True:
                print("--- [Node] : Bundle mask already inverted")


def tract_masking(
    source_dir: str,
    subject_list: list,
    ses_list: list,
    derivatives_folder:str,
    **kwargs
    ):
    """
    Performs bundle segmentation using tractseg.
    DWI images are first registered to MNI152 space using a FA map.
    Tractseg segments into 72 bundles, using a U-net architecture
    All 72 bundles are registered back to subject DWI space using inverse transform

    Args:
            source_dir (str): source directory of the DICOM
            subject_list (list[str]): list of subjects
            ses_list (list[int]): list of sessions
    """
    mni_file = kwargs.get("mni_fa_filepath")#source_dir + "/code/MNI_FA_template.nii.gz"
    verbose = kwargs.get("verbose")

    for sub in subject_list:
        for ses in ses_list:


            subject_id = "sub-" + sub
            session_id = "ses-" + ses
            identifier = "_ses_id_" + ses + "_subject_id_" + sub

            print(f"Running on {subject_id} - {session_id}")

            # Set up directories
            main_workflow_dir = source_dir + "/" + derivatives_folder + "/main_workflow"
            dwipreproc_dir = os.path.join(
                main_workflow_dir, "preproc", identifier, "biascorrect"
            )
            tracto_dir = os.path.join(main_workflow_dir, "wf_tractography", identifier)
            freesurfer_dir = os.path.join(
                main_workflow_dir, "fs_workflow", identifier, "fs_reconall", sub, "mri"
            )
            connectome_dir = os.path.join(main_workflow_dir, "connectome", identifier)

            raw_dir = os.path.join(main_workflow_dir, "bundle_segmentation")

            bundle_dir = os.path.join(raw_dir, identifier)

            outputdir = bundle_dir + "/tractseg_output"



            #Mask the tractography (sift) inside the masks
            tracts_subject_masked = outputdir + "/tracts_subject_masked"
            if not os.path.exists(tracts_subject_masked):
                os.mkdir(tracts_subject_masked)
                print("--- [Node] : mask streamlines into bundle - with exclude")
                bundles_subject = os.listdir(segInverse)
                for bundles in bundles_subject:
                    if verbose:
                        print(f"	--- masking {bundles}")
                    tract_name = bundles[:-4] + ".tck"
                    command = f"tckedit -exclude {segInverse}/{bundles} {tracto_dir}/tcksift2/sift_tracks.tck {tracts_subject_masked}/{tract_name} -force"
                    print(command)
                    subprocess.run(command, shell=True)
            elif verbose == True:
                print(
                    "--- [Node] : masking streamlines into bundles by exclusion already done"
                )

            # Compute lighter tracts files (5k per bundles)
            tracts_5k = outputdir + "/tracts_5k"
            if not os.path.exists(tracts_5k):
                os.mkdir(tracts_5k)
                print("--- [Node] : filter to 5k fibres")
                tracts_list = os.listdir(tracts_subject_masked)
                for tracts in tracts_list:
                    command = f"tckedit  {tracts_subject_masked}/{tracts} -number 5k {tracts_5k}/5k_{tracts} -force"
                    print(command)
                    subprocess.run(command, shell=True)
            elif verbose == True:
                print(
                    "--- [Node] : Filtering to 5k fibers per bundle for visualization already done"
                )

            # # Perform tractometry, to vizualise FA through a bundle
            # tractometry = f"{bundle_dir}/tractseg_output/Tractometry_{sub}_{ses}.csv"
            # if not os.path.isfile(tractometry):
            #     # os.mkdir(tractometry)
            #     print("apply TractSeg")
            #     command = f"Tractometry -i {bundle_dir}/tractseg_output/TOM_trackings/ -o {bundle_dir}/tractseg_output/Tractometry_{sub}_{ses}.csv -e {bundle_dir}/tractseg_output/endings_segmentations/ -s {bundle_dir}/FA.nii.gz"
            #     subprocess.run(command, shell=True)
            # elif verbose == True:
            #     print("--- [Node] : Tractseg already proceeded tractometry")

            ## Viewer : all tracts
            # if ViewAllTracts:
            #     print("--- [Node] : Viewing whole 5k segmentation")

            #     tracts_list = os.listdir(tracts_subject_masked)

            #     command = f"mrview {freesurfer_dir}/brain.mgz "
            #     for tracts in tracts_list:
            #         R = np.random.choice(range(256))
            #         G = np.random.choice(range(256))
            #         B = np.random.choice(range(256))

            #         command_i = f"-mode 3 -imagevisible 0 -tractography.load {tracts_subject_masked}/{tracts} -tractography.geometry pseudotubes -tractography.colour {R},{G},{B} -tractography.opacity 1 "
            #         command += command_i

            #     # print(command)
            #     subprocess.run(command, shell=True)

            # ## Viewer : all 5k tracts
            # if View5kTracts:
            #     print("--- [Node] : Viewing whole segmentation ")

            #     tracts_list = os.listdir(tracts_5k)

            #     command = f"mrview {freesurfer_dir}/brain.mgz -connectome.init {connectome_dir}/labelconvert/mapflow/_labelconvert2/parcellation.mif -connectome.load {connectome_dir}/tck2connectome/mapflow/_tck2connectome2/connectome.csv "
            #     for tracts in tracts_list:
            #         R = np.random.choice(range(256))
            #         G = np.random.choice(range(256))
            #         B = np.random.choice(range(256))

            #         command_i = f" -mode 3 -imagevisible 0 -tractography.load {tracts_5k}/{tracts} -tractography.geometry pseudotubes -tractography.thickness 0.1 -tractography.colour {R},{G},{B} -tractography.opacity 1"
            #         command += command_i

            #     # print(command)
            #     subprocess.run(command, shell=True)

            # ## Viewer : Tractseg tracts
            # if ViewTractSegTracts:
            #     print("Viewing whole segmentation tractseg")

            #     tracts_seg = os.path.join(outputdir, "TOM_trackings")
            #     tracts_list = os.listdir(tracts_seg)

            #     command = f"mrview {bundle_dir}/FA_MNI.nii.gz "
            #     for tracts in tracts_list:
            #         R = np.random.choice(range(256))
            #         G = np.random.choice(range(256))
            #         B = np.random.choice(range(256))

            #         command_i = f"-mode 3 -imagevisible 0 -tractography.load {tracts_seg}/{tracts} -tractography.geometry pseudotubes -tractography.colour {R},{G},{B} -tractography.opacity 1 "
            #         command += command_i

            #     # print(command)
            #     subprocess.run(command, shell=True)
