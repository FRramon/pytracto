import subprocess
import os

##### Get aparc+aseg_schaefer.mgz ####



sub = '02'
ses = '001'

subject_id = 'sub-' + sub
session_id = 'ses-' + ses
identifier = '_ses_id_' + ses + '_subject_id_' + sub


os.environ['FREESURFER_HOME'] = "/opt/freesurfer"
os.environ['SUBJECTS_DIR'] = f"/Volumes/LaCie/pipe_patients_10/pipe_patients_10/main_workflow/fs_workflow/{identifier}/fs_reconall"

reconall_dir = f"/Volumes/LaCie/pipe_patients_10/pipe_patients_10/main_workflow/fs_workflow/{identifier}/fs_reconall/{sub}"
code_dir = "/Users/francoisramon/Desktop/These/CONHECT/dMRI_pipeline/code"
connectome_dir = f"/Volumes/LaCie/pipe_patients_10/pipe_patients_10/main_workflow/connectome/{identifier}"
tracto_dir =  f"/Volumes/LaCie/pipe_patients_10/pipe_patients_10/main_workflow/wf_tractography/{identifier}"
############ FREESURFER COMMAND  ########


command_lh = f"mris_ca_label -l $SUBJECTS_DIR/{sub}/label/lh.cortex.label {sub} lh $SUBJECTS_DIR/{sub}/surf/lh.sphere.reg /Users/francoisramon/Downloads/gcs/lh.Schaefer2018_400Parcels_7Networks.gcs $SUBJECTS_DIR/{sub}/label/lh.Schaefer2018_400Parcels_7Networks_order.annot"
#subprocess.run(command_lh,shell = True)

command_rh = f"mris_ca_label -l $SUBJECTS_DIR/{sub}/label/rh.cortex.label {sub} rh $SUBJECTS_DIR/{sub}/surf/rh.sphere.reg /Users/francoisramon/Downloads/gcs/rh.Schaefer2018_400Parcels_7Networks.gcs $SUBJECTS_DIR/{sub}/label/rh.Schaefer2018_400Parcels_7Networks_order.annot"
#subprocess.run(command_rh,shell = True)

## Check if pial is pial or pial.T1 : 
if os.path.isfile(os.path.join(reconall_dir,"surf","rh.pial.T1")):
	print("rename")
	os.rename(os.path.join(reconall_dir,"surf","rh.pial.T1"),os.path.join(reconall_dir,"surf","rh.pial"))
if os.path.isfile(os.path.join(reconall_dir,"surf","lh.pial.T1")):
	print("rename")
	os.rename(os.path.join(reconall_dir,"surf","lh.pial.T1"),os.path.join(reconall_dir,"surf","lh.pial"))


command_aparc2aseg = f"mri_aparc2aseg --s {sub} --o {reconall_dir}/mri/aparc_aseg_schaefer.mgz --annot Schaefer2018_400Parcels_7Networks_order"
#subprocess.run(command_aparc2aseg,shell = True)

############  Mrtrix3 COMMANDS   #########

command_label_convert = f"labelconvert {reconall_dir}/mri/aparc_aseg_schaefer.mgz {code_dir}/Schaefer2018_400Parcels_7Networks_order_LUT.txt {code_dir}/lut_mrtrix3_schaefer.txt {connectome_dir}/labelconvert/parcellation_schaefer.mif"
#subprocess.run(command_label_convert,shell = True)
#### And after that we can reuse matrix creation file.

command_simple_tck = f"tck2connectome {tracto_dir}/tcksift2/sift_tracks.tck {connectome_dir}/labelconvert/parcellation_schaefer.mif {connectome_dir}/connectome_schaefer.csv -zero_diagonal -out_assignments {connectome_dir}/assignments_schaefer.csv -force"
subprocess.run(command_simple_tck,shell = True)

command_exemplar = f'connectome2tck {tracto_dir}/tcksift2/sift_tracks.tck {connectome_dir}/assignments_schaefer.csv {connectome_dir}/exemplar_schaefer –files single –exemplars {connectome_dir}/labelconvert/parcellation_schaefer.mif -force'
subprocess.run(command_exemplar,shell = True)









