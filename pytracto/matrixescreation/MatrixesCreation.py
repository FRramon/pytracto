## Add parameters probabilist/determinist
## + add atlas schaefer destrieux

# QA check for nipype pipeline

import subprocess
import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import amico

from pytracto.matrixescreation.MatrixesCreationParameters import *


# subject_raw = sys.argv[1]
# session_raw = sys.argv[2]
# source_dir = sys.argv[3]

# Attention ici
# sys.path.append(source_dir + '/dmri-pipeline')
# from run_parameters import *
# from add_connectome_schaefer import *

# subject_list = subject_raw.split(',')
# ses_list = session_raw.split(',')

def build_connectivity_matrixes(source_dir: str,subject_list: list,ses_list:list):
	"""
	This function takes in argument source directory, a subject and session list. 
	It create connectivity matrixes according to a file of parameters. 
	Matrixes for atlas Destrieux & Schaefer
	Matrixes for generative method probabilistic and deterministic
	Matrixes for microstructural parameters : SC, FA, MD, ADC, RD, AD, NDI, ODI, FWF

	Args:
		source_dir (str): source directory where the DICOM are located
		subject_list (list[str]): list of subjects to be processed
		ses_list (list[int]): list of sessions to be processed
	"""

	for sub in subject_list:

		for ses in ses_list:

			subject_id = 'sub-' + sub
			session_id = 'ses-' + ses
			identifier = '_ses_id_' + ses + '_subject_id_' + sub

			print(f"Running on {subject_id} - {session_id}")

			# Set directories
			main_workflow_dir = source_dir + '/' + pipe_name + '/' + 'main_workflow'
			
			preproc_dir = os.path.join(main_workflow_dir,'preproc',identifier)
			tracto_dir = os.path.join(main_workflow_dir,'wf_tractography',identifier)
			connectome_dir = os.path.join(main_workflow_dir,'connectome',identifier)

			if createTensor:
				# Create tensor
				bash_command = f'dwi2tensor -mask {tracto_dir}/brainmask/brainmask.mif {preproc_dir}/biascorrect/biascorrect.mif {connectome_dir}/tensor.mif -force'
				subprocess.run(bash_command, shell=True)

			if createNODDImatrix:

				tracto_noddi_dir = os.path.join(tracto_dir,'noddi')
				if not os.path.exists(tracto_noddi_dir):
					os.mkdir(tracto_noddi_dir)

				connectome_common_noddi_dir = os.path.join(connectome_dir,'noddi')
				if not os.path.exists(connectome_common_noddi_dir):
					os.mkdir(connectome_common_noddi_dir)

				### Create the maps of ODI, NDI and FWF
				## Work on the preprocessed DWI at step 'bias correction'
				# Second : Extract bvals and bvecs from the mif image & convert dwi to nifti

				command_info = f"mrinfo {preproc_dir}/biascorrect/biascorrect.mif -export_grad_fsl {connectome_common_noddi_dir}/bvecs.txt {connectome_common_noddi_dir}/bvals.txt -force"
				subprocess.run(command_info,shell = True)

				command_convert = f"mrconvert {preproc_dir}/biascorrect/biascorrect.mif {connectome_common_noddi_dir}/dwi.nii.gz -force"
				subprocess.run(command_convert,shell = True)

				command_convert = f"mrconvert {tracto_dir}/brainmask/brainmask.mif {connectome_common_noddi_dir}/brainmask.nii.gz -force"
				subprocess.run(command_convert,shell = True)


				os.chdir(connectome_common_noddi_dir)

				# # Define AMICO workflow and perform NODDI model
				amico.setup()
				ae = amico.Evaluation()

				amico.util.fsl2scheme("bvals.txt","bvecs.txt")
				ae.load_data("dwi.nii.gz","bvals.scheme",mask_filename="brainmask.nii.gz", b0_thr=0)
				ae.set_model('NODDI')
				ae.generate_kernels(regenerate=True)
				ae.load_kernels()
				ae.fit()
				ae.save_results()



			if parcellate_schaefer:
				add_schaefer_parcellation(source_dir,sub,ses)


			for gen_met in tckgen_method:

				if gen_met == "Deterministic":
					sift_file = os.path.join(tracto_dir,"tcksift2Det","sift_tracks.tck")
				elif gen_met == "Probabilistic":
					sift_file = os.path.join(tracto_dir,"tcksift2","sift_tracks.tck")

				for atlas in atlas_list:



					if atlas == "Destrieux":
						parcellation_file = os.path.join(connectome_dir,'transform_parcels','mapflow','_transform_parcels2','parcels_coreg.mif')
					elif atlas == "Schaefer":
						parcellation_file = os.path.join(connectome_dir,"parcels_coreg_schaefer.mif")

					connectome_gen_dir = os.path.join(connectome_dir,gen_met)
					if not os.path.exists(connectome_gen_dir):
						os.mkdir(connectome_gen_dir)

					connectome_spe_dir = os.path.join(connectome_dir,gen_met,atlas)
					if not os.path.exists(connectome_spe_dir):
						os.mkdir(connectome_spe_dir)

					if create_smallertck:
						bash_command = f'tckedit {sift_file} -number 100k {tracto_dir}/tcksift2/smaller100ktracks.tck -force'
						subprocess.run(bash_command,shell=True)

					#######################################################
					#####        	 Generate Connectome               ####
					#######################################################

					###### Create Mesh object for cortical & subcortical ROIs #####

					connectome_mesh_dir = os.path.join(connectome_spe_dir,'mesh')
					if not os.path.exists(connectome_mesh_dir):
						os.mkdir(connectome_mesh_dir)

					if createMesh:

						bash_command = f'label2mesh {parcellation_file} {connectome_mesh_dir}/mesh.obj -force'
						subprocess.run(bash_command,shell = True)


					#####				create SC matrix  				#####


					connectome_sc_dir = os.path.join(connectome_spe_dir,'sc')
					if not os.path.exists(connectome_sc_dir):
						os.mkdir(connectome_sc_dir)

					if createSCmatrix:
						bash_command1 = f'tck2connectome –symmetric –zero_diagonal {sift_file} {parcellation_file} {connectome_sc_dir}/sc_connectivity_matrix.csv –out_assignment {connectome_sc_dir}/sc_assignments.csv -force'
						print(f"Running command: {bash_command1}")
						subprocess.run(bash_command1,shell = True)

						bash_command2 = f'connectome2tck {sift_file} {connectome_sc_dir}/sc_assignments.csv {connectome_sc_dir}/exemplar_sc –files single –exemplars {parcellation_file} -force'
						print(f"Running command: {bash_command2}")
						subprocess.run(bash_command2,shell = True)


					#####			create FA matrixes					####


					tracto_fa_dir = os.path.join(tracto_dir,'fa')
					if not os.path.exists(tracto_fa_dir):
						os.mkdir(tracto_fa_dir)

					connectome_fa_dir = os.path.join(connectome_spe_dir,'fa')
					if not os.path.exists(connectome_fa_dir):
						os.mkdir(connectome_fa_dir)

					if createFAmatrix:
						

						# Create FA map
						bash_command2 = f'tensor2metric {connectome_dir}/tensor.mif -fa {tracto_dir}/fa/fa.mif -force'# | tensor2metric {tracto_dir}/fa/tensor.mif -vec {tracto_dir}/fa/vec.mif -force'
						subprocess.run(bash_command2, shell=True)

					 	# Create mean_FA_per_Streamline
						bash_command3 = f'tcksample {sift_file} {tracto_dir}/fa/fa.mif {connectome_fa_dir}/mean_FA_per_streamline.csv -stat_tck mean -force'
						subprocess.run(bash_command3, shell=True)

					 	# Create FA matrix
						bash_command4 = f'tck2connectome -symmetric -zero_diagonal {sift_file} {parcellation_file}  {connectome_fa_dir}/fa_connectivity_matrix.csv -scale_file {connectome_fa_dir}/mean_FA_per_streamline.csv -stat_edge mean –out_assignment {connectome_fa_dir}/fa_assignments.csv -force'
						subprocess.run(bash_command4,shell = True)

					    # Create streamtubes
						bash_command = f'connectome2tck {sift_file} {connectome_fa_dir}/fa_assignments.csv {connectome_fa_dir}/exemplar_fa –files single –exemplars {parcellation_file} -force'
						subprocess.run(bash_command,shell = True)


					#####			create RD matrixes					####

					tracto_rd_dir = os.path.join(tracto_dir,'rd')
					if not os.path.exists(tracto_rd_dir):
						os.mkdir(tracto_rd_dir)

					connectome_rd_dir = os.path.join(connectome_spe_dir,'rd')
					if not os.path.exists(connectome_rd_dir):
						os.mkdir(connectome_rd_dir)

					if createRDmatrix:
						

						# Create RD map
						bash_command2 = f'tensor2metric {connectome_dir}/tensor.mif -rd {tracto_dir}/rd/rd.mif -force'# | tensor2metric {tracto_dir}/fa/tensor.mif -vec {tracto_dir}/fa/vec.mif -force'
						subprocess.run(bash_command2, shell=True)

					 	# Create mean_RD_per_Streamline
						bash_command3 = f'tcksample {sift_file} {tracto_dir}/rd/rd.mif {connectome_rd_dir}/mean_RD_per_streamline.csv -stat_tck mean -force'
						subprocess.run(bash_command3, shell=True)

					 	# Create RD matrix
						bash_command4 = f'tck2connectome -symmetric -zero_diagonal {sift_file} {parcellation_file} {connectome_rd_dir}/rd_connectivity_matrix.csv -scale_file {connectome_rd_dir}/mean_RD_per_streamline.csv -stat_edge mean –out_assignment {connectome_rd_dir}/rd_assignments.csv -force'
						subprocess.run(bash_command4,shell = True)

					    # Create streamtubes
						bash_command = f'connectome2tck {sift_file} {connectome_rd_dir}/rd_assignments.csv {connectome_rd_dir}/exemplar_rd –files single –exemplars {parcellation_file} -force'
						subprocess.run(bash_command,shell = True)


					#####			create AD matrixes					####

					tracto_ad_dir = os.path.join(tracto_dir,'ad')
					if not os.path.exists(tracto_ad_dir):
						os.mkdir(tracto_ad_dir)

					connectome_ad_dir = os.path.join(connectome_spe_dir,'ad')
					if not os.path.exists(connectome_ad_dir):
						os.mkdir(connectome_ad_dir)

					if createADmatrix:
						

						# Create AD map
						bash_command2 = f'tensor2metric {connectome_dir}/tensor.mif -ad {tracto_dir}/ad/ad.mif -force'# | tensor2metric {tracto_dir}/fa/tensor.mif -vec {tracto_dir}/fa/vec.mif -force'
						subprocess.run(bash_command2, shell=True)

					 	# Create mean_AD_per_Streamline
						bash_command3 = f'tcksample {sift_file} {tracto_dir}/ad/ad.mif {connectome_ad_dir}/mean_AD_per_streamline.csv -stat_tck mean -force'
						subprocess.run(bash_command3, shell=True)

					 	# Create AD matrix
						bash_command4 = f'tck2connectome -symmetric -zero_diagonal {sift_file} {parcellation_file} {connectome_ad_dir}/ad_connectivity_matrix.csv -scale_file {connectome_ad_dir}/mean_AD_per_streamline.csv -stat_edge mean –out_assignment {connectome_ad_dir}/ad_assignments.csv -force'
						subprocess.run(bash_command4,shell = True)

					    # Create AD streamtubes
						bash_command = f'connectome2tck {sift_file} {connectome_ad_dir}/ad_assignments.csv {connectome_ad_dir}/exemplar_ad –files single –exemplars {parcellation_file} -force'
						subprocess.run(bash_command,shell = True)

					#####			create ADC matrixes					####

					tracto_adc_dir = os.path.join(tracto_dir,'adc')
					if not os.path.exists(tracto_adc_dir):
						os.mkdir(tracto_adc_dir)

					connectome_adc_dir = os.path.join(connectome_spe_dir,'adc')
					if not os.path.exists(connectome_adc_dir):
						os.mkdir(connectome_adc_dir)

					if createADCmatrix:
						

						# Create ADC map
						bash_command2 = f'tensor2metric {connectome_dir}/tensor.mif -adc {tracto_dir}/adc/adc.mif -force'# | tensor2metric {tracto_dir}/fa/tensor.mif -vec {tracto_dir}/fa/vec.mif -force'
						subprocess.run(bash_command2, shell=True)

					 	# Create mean_AD_per_Streamline
						bash_command3 = f'tcksample {sift_file} {tracto_dir}/adc/adc.mif {connectome_adc_dir}/mean_ADC_per_streamline.csv -stat_tck mean -force'
						subprocess.run(bash_command3, shell=True)

					 	# Create AD matrix
						bash_command4 = f'tck2connectome -symmetric -zero_diagonal {sift_file} {parcellation_file} {connectome_adc_dir}/adc_connectivity_matrix.csv -scale_file {connectome_adc_dir}/mean_ADC_per_streamline.csv -stat_edge mean –out_assignment {connectome_adc_dir}/adc_assignments.csv -force'
						subprocess.run(bash_command4,shell = True)

					    # Create AD streamtubes
						bash_command = f'connectome2tck {sift_file} {connectome_adc_dir}/adc_assignments.csv {connectome_adc_dir}/exemplar_adc –files single –exemplars {parcellation_file} -force'
						subprocess.run(bash_command,shell = True)

					
					### Create matrixes with noddi metrics

					tracto_noddi_dir = os.path.join(tracto_dir,'noddi')
					if not os.path.exists(tracto_noddi_dir):
						os.mkdir(tracto_noddi_dir)

					connectome_noddi_dir = os.path.join(connectome_spe_dir,'noddi')
					if not os.path.exists(connectome_noddi_dir):
						os.mkdir(connectome_noddi_dir)

					connectome_ndi_dir = os.path.join(connectome_spe_dir,'ndi')
					if not os.path.exists(connectome_ndi_dir):
						os.mkdir(connectome_ndi_dir)

					connectome_odi_dir = os.path.join(connectome_spe_dir,'odi')
					if not os.path.exists(connectome_odi_dir):	
						os.mkdir(connectome_odi_dir)

					connectome_fwf_dir = os.path.join(connectome_spe_dir,'fwf')
					if not os.path.exists(connectome_fwf_dir):
						os.mkdir(connectome_fwf_dir)

					if createNODDImatrix:




						noddi_maps_dir = os.path.join(connectome_common_noddi_dir,'AMICO','NODDI')
						


						
					 	# Create mean_NDI_per_Streamline
						bash_command1 = f'tcksample {sift_file} {noddi_maps_dir}/fit_NDI.nii.gz {connectome_ndi_dir}/mean_NDI_per_streamline.csv -stat_tck mean -force'
						subprocess.run(bash_command1, shell=True)

					 	# Create NDI matrix
						bash_command2 = f'tck2connectome -symmetric -zero_diagonal {sift_file} {parcellation_file} {connectome_ndi_dir}/NDI_connectivity_matrix.csv -scale_file {connectome_ndi_dir}/mean_NDI_per_streamline.csv -stat_edge mean –out_assignment {connectome_ndi_dir}/NDI_assignments.csv -force'
						subprocess.run(bash_command2,shell = True)

					    # Create NDI streamtubes
						bash_command3 = f'connectome2tck {sift_file} {connectome_ndi_dir}/NDI_assignments.csv {connectome_ndi_dir}/exemplar_NDI –files single –exemplars {parcellation_file} -force'
						subprocess.run(bash_command3,shell = True)


						## Compute ODI matrix ##


						

						bash_command4 = f'tcksample {sift_file} {noddi_maps_dir}/fit_ODI.nii.gz {connectome_odi_dir}/mean_ODI_per_streamline.csv -stat_tck mean -force'
						subprocess.run(bash_command4, shell=True)

					 	# Create NDI matrix
						bash_command5 = f'tck2connectome -symmetric -zero_diagonal {sift_file} {parcellation_file} {connectome_odi_dir}/ODI_connectivity_matrix.csv -scale_file {connectome_odi_dir}/mean_ODI_per_streamline.csv -stat_edge mean –out_assignment {connectome_odi_dir}/ODI_assignments.csv -force'
						subprocess.run(bash_command5,shell = True)

					    # Create NDI streamtubes
						bash_command6 = f'connectome2tck {sift_file} {connectome_odi_dir}/ODI_assignments.csv {connectome_odi_dir}/exemplar_ODI –files single –exemplars {parcellation_file} -force'
						subprocess.run(bash_command6,shell = True)


						## Compute FWF matrix ##



						bash_command7 = f'tcksample {sift_file} {noddi_maps_dir}/fit_FWF.nii.gz {connectome_fwf_dir}/mean_FWF_per_streamline.csv -stat_tck mean -force'
						subprocess.run(bash_command7, shell=True)

					 	# Create NDI matrix
						bash_command8 = f'tck2connectome -symmetric -zero_diagonal {sift_file} {parcellation_file} {connectome_fwf_dir}/FWF_connectivity_matrix.csv -scale_file {connectome_fwf_dir}/mean_FWF_per_streamline.csv -stat_edge mean –out_assignment {connectome_fwf_dir}/FWF_assignments.csv -force'
						subprocess.run(bash_command8,shell = True)

					    # Create NDI streamtubes
						bash_command9 = f'connectome2tck {sift_file} {connectome_fwf_dir}/FWF_assignments.csv {connectome_fwf_dir}/exemplar_FWF –files single –exemplars {parcellation_file} -force'
						subprocess.run(bash_command9,shell = True)


					if save_matrix:
						sc_file_path = f'{connectome_sc_dir}/sc_connectivity_matrix.csv'   
						fa_file_path = f'{connectome_fa_dir}/fa_connectivity_matrix.csv'
						rd_file_path = f'{connectome_rd_dir}/rd_connectivity_matrix.csv'   
						ad_file_path = f'{connectome_ad_dir}/ad_connectivity_matrix.csv' 
						adc_file_path = f'{connectome_adc_dir}/adc_connectivity_matrix.csv'   
						ndi_file_path = f'{connectome_ndi_dir}/NDI_connectivity_matrix.csv'  
						odi_file_path = f'{connectome_odi_dir}/ODI_connectivity_matrix.csv'   
						fwf_file_path = f'{connectome_fwf_dir}/FWF_connectivity_matrix.csv'   

			 

			  

						if not (os.path.isfile(sc_file_path) and os.path.isfile(fa_file_path) and os.path.isfile(rd_file_path) and os.path.isfile(ad_file_path) and os.path.isfile(adc_file_path) and os.path.isfile(ndi_file_path)  and os.path.isfile(odi_file_path)  and os.path.isfile(fwf_file_path)):
						    print("Error: One or more files not found.")
						    sys.exit(1)

						# Read the CSV files without skipping the header

						df_sc = pd.read_csv(sc_file_path, header=None)
						df_fa = pd.read_csv(fa_file_path, header=None)
						df_rd = pd.read_csv(fa_file_path, header=None)
						df_ad = pd.read_csv(ad_file_path, header=None)
						df_adc = pd.read_csv(adc_file_path, header=None)
						df_ndi = pd.read_csv(ndi_file_path, header=None)
						df_odi = pd.read_csv(odi_file_path, header=None)
						df_fwf = pd.read_csv(fwf_file_path, header=None)


						# Calculate the adaptive outlier threshold (e.g., 99th percentile) for both dataframes
						outlier_threshold_sc = df_sc.stack().quantile(0.99)
						outlier_threshold_fa = 1
						outlier_threshold_rd = df_rd.stack().quantile(0.99)
						outlier_threshold_ad = df_ad.stack().quantile(0.99)
						outlier_threshold_adc = df_adc.stack().quantile(0.99)
						outlier_threshold_ndi = df_ndi.stack().quantile(0.99)
						outlier_threshold_odi = df_odi.stack().quantile(0.99)
						outlier_threshold_fwf = df_fwf.stack().quantile(0.99)



						# Create a function to generate and save the heatmap
						def save_heatmap(dataframe,outlier_threshold,label,gen_met,atlas):
						    plt.figure(figsize=(10, 8))
						    sns.heatmap(dataframe, cmap='viridis', vmin=0, vmax=outlier_threshold, annot = False, fmt=".2f")
						    plt.title(f' sub-{sub} - ses-{ses} - {label}')
						  
						    # Save the heatmap as a PNG file in the source data folder 
						    output_file_path = f'{connectome_dir}/{gen_met}/{atlas}/{label}/{label}_connectivity_matrix.png'
						    plt.savefig(output_file_path)

						# Save heatmaps
						save_heatmap(df_sc,outlier_threshold_sc, "sc",gen_met,atlas)
						save_heatmap(df_fa,outlier_threshold_fa, "fa",gen_met,atlas)
						save_heatmap(df_rd,outlier_threshold_rd, "rd",gen_met,atlas)
						save_heatmap(df_ad,outlier_threshold_ad, "ad",gen_met,atlas)
						save_heatmap(df_adc,outlier_threshold_adc, "adc",gen_met,atlas)
						save_heatmap(df_ndi,outlier_threshold_ndi, "ndi",gen_met,atlas)
						save_heatmap(df_odi,outlier_threshold_odi, "odi",gen_met,atlas)
						save_heatmap(df_fwf,outlier_threshold_fwf, "fwf",gen_met,atlas)



					if viewSCConnectome:
						bash_command = f'mrview {preproc_dir}/biascorrect/biascorrect.mif -connectome.init {connectome_dir}/labelconvert/mapflow/_labelconvert2/parcellation.mif -connectome.load {connectome_sc_dir}/sc_connectivity_matrix.csv -imagevisible 0'
						subprocess.run(bash_command,shell = True)

					if viewFAConnectome:
						bash_command = f'mrview {preproc_dir}/biascorrect/biascorrect.mif -connectome.init {connectome_dir}/labelconvert/mapflow/_labelconvert2/parcellation.mif -connectome.load {connectome_fa_dir}/fa_connectivity_matrix.csv -imagevisible 0'
						subprocess.run(bash_command,shell = True)


