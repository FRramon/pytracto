# Author François Ramon
# 01/02/2024

##########################################################################################
#																						 #
# This script uses AMICO (Accelerated Microstructure Imaging via Convex Optimization) 	 #
# to perform microstruct model on Diffusion Weighted Image.									 #
#																						 #
##########################################################################################

# Import necessary packages

import subprocess
import os
import amico

# Define the data path

data_dir = "/Users/francoisramon/Desktop/Thèse/dMRI_pipeline/test_microstruct/test_subject"
microstruct_dir = "/Users/francoisramon/Desktop/Thèse/dMRI_pipeline/test_microstruct/test_subject/microstructure"


# First compute a brain mask

command_convert = f"dwi2mask {data_dir}/DWI.mif {microstruct_dir}/brain_mask.nii.gz"
subprocess.run(command_convert,shell = True)

# First : Extract tensor metrics from the DWI : FA, RD, AD, MD.

command_info = f"dwi2tensor {data_dir}/DWI.mif -mask {microstruct_dir}/brain_mask.nii.gz {microstruct_dir}/dwitensor.mif -force"
subprocess.run(command_info,shell = True)

command_info = f"tensor2metric {microstruct_dir}/dwitensor.mif -mask {microstruct_dir}/brain_mask.nii.gz -fa {microstruct_dir}/fa.mif  -ad {microstruct_dir}/ad.mif  -rd {microstruct_dir}/rd.mif -adc {microstruct_dir}/adc.mif -force"
subprocess.run(command_info,shell = True)

# Second : Extract bvals and bvecs from the mif image & convert dwi to nifti

command_info = f"mrinfo {data_dir}/DWI.mif -export_grad_fsl {microstruct_dir}/bvecs.txt {microstruct_dir}/bvals.txt"
subprocess.run(command_info,shell = True)

command_convert = f"mrconvert {data_dir}/DWI.mif {microstruct_dir}/dwi.nii.gz"
subprocess.run(command_convert,shell = True)



# Change to subdirectory "microstruct"

os.chdir(microstruct_dir)

# Define AMICO workflow and perform NODDI model

ae = amico.Evaluation()

amico.util.fsl2scheme('bvals.txt','bvecs.txt')
ae.load_data('dwi.nii.gz','bvals.scheme',mask_filename='brain_mask.nii.gz', b0_thr=0)
ae.set_model('NODDI')
ae.generate_kernels(regenerate=True)
ae.load_kernels()
ae.fit()
ae.save_results()









