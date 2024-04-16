#################################################################
########        Script for running the pipeline        ##########
#
# Running parameters are in /code/run_parameters.py
# 
#
################################################################

import os
import subprocess
from bids.layout import BIDSLayout

from tractography_utils import *
from run_parameters import *

#################################################################
#########         BIDS Formatting & Correct AP/PA       #########
#################################################################

# if not os.path.exists(os.path.join(source_dir,'nifti3')) and convert2bids:
# 	print('Running; BIDS formatting')
# 	bash_command = 'python generic_heudiconv_conhect.py'
	
########          group/session selection               #########

data_dir = os.path.join(source_dir,data_folder,group)
base_directory = source_dir + '/' + pipe_name
out_dir = source_dir + '/' + result_name
config_list = ["evenPA","oddPA","noAP"]
workflows = ["2_Tractography/even_workflow.py","2_Tractography/odd_workflow.py","2_Tractography/synth_workflow.py"]

# Select subject and sessions
#layout = BIDSLayout(data_dir)


#################################################################
#########         Tractography/Freesurfer pipeline    ###########
#################################################################

#from pipeline_parameters import * ici

if run_pipeline:
	# command_pipeline10 = f'python 2_Tractography/multiple_wf.py {CLI_subject_list} {CLI_session_list} {pipe_name10} {result_name10} {ntracks10}'
	# subprocess.run(command_pipeline10,shell = True)
	# command_pipeline20 = f'python 2_Tractography/multiple_wf.py {CLI_subject_list} {CLI_session_list} {pipe_name20} {result_name20} {ntracks20}'
	# subprocess.run(command_pipeline20,shell = True)

	for ses in session_list:


		# mri_list,even_subject_list,odd_subject_list,synth_subject_list = get_list_sessions_inverse_phase(source_dir,group,ses)
		list_subject_list = get_ids_by_sessions(dicom_dir,source_dir,group,ses)


		print(list_subject_list)
		ses = "00" + str(ses)

		print(f"Dimensions inconsistency : {list_subject_list[4]}")

		for i,config in enumerate(config_list):
			if config == "evenPA":
				subject_list = list_subject_list[1]
				workflow = workflows[0]
			elif config == "oddPA":
				subject_list = list_subject_list[2]
				workflow = workflows[1]
			elif config == "noAP":
				subject_list = list_subject_list[3]
				workflow = workflows[2]

			print(subject_list)
			if subject_list[0] != '':
				print(f"Running {config} workflow on subject {subject_list}")

			
		# subject_list = odd_subject_list
		# #subject_list = ['01,02,03,04,05,06,07,08,09']


		# print('Subjects : ', subject_list)
		# print('Sessions : ', session_list)

		# #CLI_subject_list = '30,40,24,07,25,08,28,22,10,29,39,19,12,13,21,01,37,05,43,34,35,02,14,32,23,15,42,44'


				CLI_subject_list = ','.join(subject_list)

				CLI_session_list = ses  #','.join(session_list)



				command_pipeline = f'python {workflow} {data_dir} {CLI_subject_list} {CLI_session_list} {base_directory} {out_dir} {ntracks} '
				print(command_pipeline)
				subprocess.run(command_pipeline,shell = True)


#################################################################
#########        Create the connectivity matrixes      ##########
#################################################################


if createMatrixes:
	for ses in session_list:
		list_subject_list = get_ids_by_sessions(dicom_dir,source_dir,group,ses)


		print(list_subject_list)
		ses = "00" + str(ses)
		for i,config in enumerate(config_list):
			if config == "evenPA":
				subject_list = list_subject_list[1]
				workflow = workflows[0]
			elif config == "oddPA":
				subject_list = list_subject_list[2]
				workflow = workflows[1]
			elif config == "noAP":
				subject_list = list_subject_list[3]
				workflow = workflows[2]

			print(subject_list)
			if subject_list[0] != '':
				print(f"Running {config} workflow on subject {subject_list}")
		#subject_list = get_list_sessions(source_dir,group,ses)
		#subject_list = ['01,02,03,04,05,06,07,08,09']

		#print('Subjects : ', subject_list)
		#print('Sessions : ', session_list)

				CLI_subject_list = ','.join(subject_list)
				CLI_session_list = ses  #','.join(session_list)


				bash_command = f'python 3_MatrixesCreation/MatrixesCreation.py {CLI_subject_list} {CLI_session_list} {source_dir}'
				subprocess.run(bash_command,shell = True)
	

if createROIfile:
	bash_command = f'python 3_MatrixesCreation/clone_createROIfile.py '
	subprocess.run(bash_command,shell = True)

#################################################################
#########                 QA Check                     ##########
#################################################################

if QAcheck:
	bash_command = f'python QA_check/QA_check_nipype.py {CLI_subject_list} {CLI_session_list}'
	print(bash_command)
	subprocess.run(bash_command,shell = True)


#################################################################
#########            Bundle Segmentation               ##########
#################################################################


if bundleSegmentation:

	for ses in session_list:
		subject_list = get_list_sessions(source_dir,group,ses)
		#subject_list = ['01,02,03,04,05,06,07,08,09']

		print('Subjects : ', subject_list)
		print('Sessions : ', session_list)

		CLI_subject_list = ','.join(subject_list)
		CLI_session_list = ses  #','.join(session_list)


		bash_command = f'python 4_BundleSegmentation/BundleSegmentation.py {CLI_subject_list} {CLI_session_list} {source_dir}'
		print(bash_command)
		subprocess.run(bash_command,shell = True)

#################################################################
#########            Beta test: Clustering             ##########
#################################################################

if ClusterConsensus:
	bash_command = f'python NetworkAnalysis/ClusterConsensus.py {CLI_subject_list} {CLI_session_list} {source_dir}'
	print(bash_command)
	subprocess.run(bash_command,shell = True)

