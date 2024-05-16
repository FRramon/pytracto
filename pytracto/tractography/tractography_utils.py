###########################################################################
###           		 Provide utils functions                            ###
###########################################################################


import os
import shutil
import csv
import pandas as pd
import re
from collections import Counter
import json


# Function to Check if the path specified
# specified is a valid directory
def isEmpty(path: str):
	"""
	Function to check if a directory exists and is empty
	"""
	if os.path.exists(path) and not os.path.isfile(path): 
		#print(os.listdir(path)
		# Checking if the directory is empty or not
		if not os.listdir(path): 
			return True
		else: 
			return False 
	else: 
		return True


def get_list_sessions(base_dir:str,groups:str,session:str):
	"""
	Function to get the subject list that attended to a specific sessino
	"""

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

def get_list_sessions_inverse_phase(base_dir: str,groups: str,session: int):
	"""
	Get the list of subject that underwent session i and were aquired an inverse phase
	"""

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
		ses_id = 'ses-00' + str(session)
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
	# transformed_list_Ses = ','.join(haveSes)
	# result_list_Ses = [transformed_list_Ses]

	### Get the list of subjects that have two inverse phase dwi on session i
	have_even = [s[4:] for s in have_even ]
	# transformed_list_even = ','.join(have_even)
	# result_list_even = [transformed_list_even]

	### Get the list of subjects that have only one phase dwi on session i
	have_odd = [s[4:] for s in have_odd if s[4:] != '20']
	# transformed_list_odd = ','.join(have_odd)
	# result_list_odd = [transformed_list_odd]

	have_not = [s[4:] for s in have_not]
	# transformed_list_not = ','.join(have_not)
	# result_list_not = [transformed_list_not]

	### Get the list of subject having three identical phases (PA or AP) --> odd

	


	### Get the list of subject having two PA and two AP --> even


	return haveSes,have_even,have_odd,have_not

def check_dimensions_problems(source_dir: str,base_dir: str,groups: str,session: int):
	"""
	Get the list of subject in session i that have a dimensionality issue in their images.
	"""
	session = "V" + str(session)
	# Get subjects ids which participated in session i
	source_data_dir = os.path.join(source_dir,'Patients')

	subjects = os.listdir(source_data_dir)
	

	haveProblem = []


	for s in subjects:
		ses_path = os.path.join(source_data_dir,s,session,"01-RawData")
		if os.path.isfile(os.path.join(ses_path,"description.json")):
			f = open(os.path.join(ses_path,"description.json"))
			data = json.load(f)
			b200 = [key for key in data.keys() if "dw-b0200" in key]
			b1500 = [key for key in data.keys() if "dw-b1500" in key]
			b2500_6 = [key for key in data.keys() if "dw-b2500-06dir" in key]
			b2500_60 = [key for key in data.keys() if "dw-b2500-60dir" in key]


			keys = b200 + b1500 + b2500_6 + b2500_60
			norms = [2170,3220,490,4270]

			#print(haveProblem)

			for i,key in enumerate(keys):
				folder = data[key]
				if os.path.exists(os.path.join(ses_path,folder)):
					nvols = len(os.listdir(os.path.join(ses_path,folder)))
					statement = (nvols==norms[i])
					if statement == False:
						#print(f"Problem on {key} for {s} : {nvols} instead of {norms[i]}")
						haveProblem.append(s)


	equivalence_table = pd.read_csv(os.path.join(base_dir,"nifti3","equivalence_table_Patients.csv"))

	#print(equivalence_table.head())
	
	sub_equi_table = equivalence_table[equivalence_table['conhect_label'].isin(haveProblem)]
	sub_numbers = sub_equi_table['functional_label'].tolist()

	haveProblem = list(set(sub_numbers))
	haveProblem = [str(a) for a in haveProblem]

	return haveProblem
			

def get_ids_by_sessions(source_dir : str,base_dir :str,groups :str,session :int):
	"""
	Get subject identifiers that went into session i, had or not inverse phase, had or not a dimension issue.
	"""
	haveSes,have_even,have_odd,have_not = get_list_sessions_inverse_phase(base_dir,groups,session)
	haveProblem = check_dimensions_problems(source_dir,base_dir,groups,session)


	haveSes = [s for s in haveSes if s not in haveProblem]
	transformed_list_Ses = ','.join(haveSes)
	result_list_Ses = [transformed_list_Ses]

	
	if session == 1 : 
		have_even = [s for s in have_even if s not in haveProblem and s != '16']
		haveProblem.append("16")
	elif session == 2:
		have_even = [s for s in have_even if s not in haveProblem and s != '03' and s != '06' and s != '07']
		haveProblem.append("03")
		haveProblem.append("06")

	else: 
		have_even = [s for s in have_even if s not in haveProblem]

	transformed_list_even = ','.join(have_even)
	result_list_even = [transformed_list_even]

	have_odd = [s for s in have_odd if s not in haveProblem]
	transformed_list_odd = ','.join(have_odd)
	result_list_odd = [transformed_list_odd]

	have_not = [s for s in have_not if s not in haveProblem]

	transformed_list_not = ','.join(have_not)
	result_list_not = [transformed_list_not]


	return result_list_Ses,result_list_even,result_list_odd,result_list_not, haveProblem



# r = get_ids_by_sessions("/mnt/POOL_IRM06/CONHECT/ConhectDatabase","/mnt/POOL_IRM08/CONHECT","Patients",2)
# print(r)
