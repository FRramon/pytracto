
# QA check for nipype pipeline

import subprocess
import os
import sys
import pandas as pd
import seaborn as sns

# source_dir = '/mnt/CONHECT_data'
# pipe_name = 'pipe_patients_30'

def clean_tracks_done(source_dir: str,pipe_name: str):
	"""
	Warning : Function to delete file tracked.tck if sift was ran. 
	Warning : if the pipeline is rerun, it will do again tracks generation.

	Args: 
		source_dir (str): parent folder of dicom directory
		pipe_name (str): name of the folder of the output
	"""

	wf_tractography_path = os.path.join(source_dir,pipe_name,'main_workflow','wf_tractography')
	processed_dirs = os.listdir(wf_tractography_path)

	for dirs in processed_dirs:

		tracks_path = os.path.join(wf_tractography_path,dirs,"tckgen")
		sift_path = os.path.join(wf_tractography_path,dirs,"tcksift2")

		if (os.path.exists(sift_path) and os.path.isfile(os.path.join(sift_path,"result_tcksift2.pklz"))):
			print(f"Sift has been done on {dirs}")

			if os.path.isfile(os.path.join(tracks_path,'tracked.tck')):
				command_rm = f"rm {tracks_path}/tracked.tck"
				subprocess.run(command_rm,shell = True)
				print(command_rm)
		# elif (os.path.exists(sift_path) and os.path.isfile(os.path.join(sift_path,"result_tcksift2.pklz.tmp"))):
		# 	print("Sift currently done, do nothing")
		# else:
		# 	print("Do nothing")


