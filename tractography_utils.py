###########################################################################
###           		 Provide utils functions                            ###
###########################################################################


import os
import shutil
import csv
import pandas as pd
import re
from collections import Counter


# Function to Check if the path specified 
# specified is a valid directory 
def isEmpty(path): 
    if os.path.exists(path) and not os.path.isfile(path): 
        #print(os.listdir(path))
        # Checking if the directory is empty or not 
        if not os.listdir(path): 
            return True
        else: 
            return False 
    else: 
        return True


def get_list_sessions(base_dir,groups,session):

	# Get subjects ids which participated in session i

	source_data_dir = os.path.join(base_dir,'nifti3',groups)

	subjects_raw = os.listdir(source_data_dir)
	pattern = re.compile(r'^sub-\d')
	subjects = [s for s in subjects_raw if pattern.match(s)]

	haveSes = []

	for s in subjects:
		ses_id = 'ses-' + session
		ses_path = os.path.join(source_data_dir,s,ses_id)
		if not isEmpty(ses_path):
			haveSes.append(s)

	haveSes = [s[4:] for s in haveSes]

	print(len(haveSes))

	transformed_list = ','.join(haveSes)
	result_list = [transformed_list]

	print(result_list)

	return result_list

def get_list_sessions_inverse_phase(base_dir,groups,session):

	# Get subjects ids which participated in session i
	source_data_dir = os.path.join(base_dir,'nifti3',groups)

	subjects_raw = os.listdir(source_data_dir)
	pattern = re.compile(r'^sub-\d')
	subjects = [s for s in subjects_raw if pattern.match(s)]

	haveSes = []
	have_odd = []
	have_even = []
	have_not = []

	for s in subjects:
		ses_id = 'ses-' + session
		ses_path = os.path.join(source_data_dir,s,ses_id)
		if not isEmpty(ses_path):
			haveSes.append(s)

			all_files = os.listdir(os.path.join(ses_path,"dwi"))
			list_nifti = [st for st in all_files if st[-7:]==".nii.gz"]
			list_phase = [st.split('_')[3] for st in list_nifti]
			#print(s)

			counter = Counter(list_phase)
			max_freq = max(counter.values())
			#print(max_freq)
			

			if max_freq == 2:
				have_even.append(s)
				#if max(counter.values()) 
			elif max_freq == 3:
				have_odd.append(s)
			elif max_freq == 4:
				have_not.append(s)


	### Get the list of subjects that have a mri at session i
	haveSes = [s[4:] for s in haveSes]
	transformed_list_Ses = ','.join(haveSes)
	result_list_Ses = [transformed_list_Ses]

	### Get the list of subjects that have two inverse phase dwi on session i
	have_even = [s[4:] for s in have_even ]
	transformed_list_even = ','.join(have_even)
	result_list_even = [transformed_list_even]

	### Get the list of subjects that have only one phase dwi on session i
	have_odd = [s[4:] for s in have_odd if s[4:] != '20']
	print(have_odd)
	transformed_list_odd = ','.join(have_odd)
	result_list_odd = [transformed_list_odd]

	have_not = [s[4:] for s in have_not]
	transformed_list_not = ','.join(have_not)
	result_list_not = [transformed_list_not]

	### Get the list of subject having three identical phases (PA or AP) --> odd

	


	### Get the list of subject having two PA and two AP --> even


	return result_list_Ses,result_list_even,result_list_odd,result_list_not

#r1,r2,r3,r4 = get_list_sessions_inverse_phase('/mnt/POOL_IRM08/CONHECT','Patients','003')
