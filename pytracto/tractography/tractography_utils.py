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
import glob
import nibabel as nib

# Function to Check if the path specified
# specified is a valid directory
def isEmpty(path: str):
    """
    Function to check if a directory exists and is empty

    Args:
            path (str): path to folder
    """
    if os.path.exists(path) and not os.path.isfile(path):
        # print(os.listdir(path)
        # Checking if the directory is empty or not
        if not os.listdir(path):
            return True
        else:
            return False
    else:
        return True


def get_list_sessions(base_dir: str,folder_name: str, session: int,group: str = None):
    """
    Function to get the subject list that attended to a specific session

    Args:
            base_dir (str): base directory
            folder_name (str) : name of the data directory (usually 'rawdata')
            session (int): session to be processed
            group (str,optional): Optional group to include in path
    """

    # Get subjects ids which participated in session i

    if group:
        source_data_dir = os.path.join(base_dir,folder_name, group)
    else:
        source_data_dir = os.path.join(base_dir, folder_name)

    subjects_raw = os.listdir(source_data_dir)
    pattern = re.compile(r"^sub.*")
    subjects = [s for s in subjects_raw if pattern.match(s)]

    haveSes = []

    for s in subjects:
        ses_id = "ses-" + session
        ses_path = os.path.join(source_data_dir, s, ses_id)
        if not isEmpty(ses_path) and not isEmpty(os.path.join(ses_path,"anat")) and not isEmpty(os.path.join(ses_path,"dwi")):
            haveSes.append(s)

    haveSes = [s[4:] for s in haveSes]

    #print(len(haveSes))

    transformed_list = ",".join(haveSes)
    result_list = [transformed_list]

    #print(result_list)

    return result_list

def check_template(base_dir:str,folder_name:str, session_id:str, templates:dict,group:str = None):

    """
    Function to get the subject list that attended to a specific session

    Args:
            base_dir (str): base directory
            folder_name (str) : name of the data directory (usually 'rawdata')
            session (int): session to be processed
            group (str, optional ) : group 
            group (str,optional): Optional group to include in path
    """

    if group:
        source_data_dir = os.path.join(base_dir,folder_name, group)
    else:
        source_data_dir = os.path.join(base_dir, folder_name)

    subjects_raw = os.listdir(source_data_dir)
    pattern = re.compile(r"^sub.*")
    subjects = [s[4:] for s in subjects_raw if pattern.match(s)]

    #print(subjects)
    existing_files = []
    missing_files = []
    matching_subject_ids = []
    non_matching_subject_ids = []


    for subject_id in subjects:
        subject_has_all_files = True

        for key, template in templates.items():
            # Format the template with subject_id and session_id
            path_pattern = template.format(subject_id=subject_id, ses_id=session_id)
            full_path_pattern = os.path.join(source_data_dir, path_pattern)

            # Use glob to handle the wildcard and find matching files
            matching_files = glob.glob(full_path_pattern)

            if matching_files:
                existing_files.extend(matching_files)
            else:
                missing_files.append(full_path_pattern)
                subject_has_all_files = False

        if subject_has_all_files:
            matching_subject_ids.append(subject_id)
        else:
            non_matching_subject_ids.append(subject_id)


    #print(len(matching_subject_ids))

    return matching_subject_ids, existing_files, missing_files,non_matching_subject_ids



def extract_dim(pattern):

    """
    Explore nifti headers to search for a potential dimension error.

    Args:
            pattern : file path pattern for the nifti image to be analyzed
    Returns: 
            a tuple comprising:
            - a list of three int : dimension x,y,z
            - a boolean, True if the image has a dimension error
    """
    file_paths = glob.glob(pattern)
    filepath = file_paths[0]

    n_img = nib.load(filepath)
    header = n_img.header
    dims = header['dim']

    dimension_error = False

    if 'anat' in filepath:
        dims_order = [dims[2],dims[3],dims[1]]
        if dims_order[0] != 256 or dims_order[1] != 256:
            dimension_error = True
    elif 'dwi' in filepath:
        dims_order = [dims[1],dims[2],dims[3]]
        if dims_order[0] != 128 or dims_order[1] != 128 or dims_order[2] != 70:
            dimension_error = True

    elif 'fmap' in filepath:
        dims_order = [dims[1],dims[2],dims[3]]
        if dims_order[0] != 128 or dims_order[1] != 128 or dims_order[2] != 70:
            dimension_error = True
            


    return dims_order,dimension_error

def check_problems_nifti(base_dir: str,folder_name: str,templates: dict,session: str,group = None):

    """
    Get the list of subject that can be processed using the diffusion workflows

    Args:
            base_dir (str): base directory
            folder_name (str) :s
            session (int): session to be processed
            templates (dict) : template for MRI aquisition
            group (str, optional): group of subject to be processed (either patients, temoins etc. )
    Returns: 
            a tuple comprising:
            - the list of subjects that can be processed
            - the list of subjects having dimensions issues
            - the list of subjects having template issues

    """

    # First step : extract subject who underwent the sequences written in 'templates'

    list_seq_not_found = []

    res = check_template(base_dir,folder_name,session_id = session, templates = templates,group = group)
    subject_list = res[0]

    ses_id = 'ses-' + session

    if group:
        data_dir = os.path.join(base_dir,folder_name,group)
    else:
        data_dir = os.path.join(base_dir,folder_name)

    ## Second step : check for dimensions issues in the nifti header

    list_dimension_error = []

    for s in subject_list:
        #print(s)
        for key, template in templates.items():
            file_pattern = f"{data_dir}/{template.format(subject_id=s, ses_id=session)}"
            file_paths = glob.glob(file_pattern)
            
            file_path = file_paths[0]
            dim,dim_error = extract_dim(file_path)
            if dim_error:
                list_dimension_error.append(s)
            #print(f"{key}: {dim}")


    # four_occurences = [subject_id for subject_id, count in Counter(list_dimension_error).items() if count == 4]
    # list_dimension_error = [s for s in list_dimension_error if s not in four_occurences]

    list_dimension_error = list(set(list_dimension_error))


    subject_set = set(subject_list)
    errors_set = set(list_dimension_error)
    subject_to_process = list(subject_set - errors_set)




    return subject_to_process, list_dimension_error,res[3]



def workflow_repartition(base_dir: str,folder_name: str, session: str,templates,shell,group: str = None):
    """
    Get the list of subject that underwent session i and were aquired an inverse phase

    Args:
            base_dir (str): base directory
            folder_name (str) : folder name, usually rawdata
            session (str): session to be processed
            templates (dict) : template for MRI aquisition
            shell (str) : either 'multishell' or 'singleshell', require multishell for b != 0 > 1
            group (str, optional): group of subject to be processed (either patients, temoins etc. )

    Returns:
            a tuple, comprising : 
            - list of subjects that check template
            - list of subjects that must go in even_workflow (multishell data)
            - list of subjects that must go in odd_workflow (multishell data)
            - list of subjects that must go in synth_workflow (multishell data)
            - list of subjects that must go in singleshell_workflow (singleshell data)
            - list of subjects that must go in singleshellsynth_workflow (singleshell data)


    """

    # Get subjects ids which participated in session i

    if group:
        source_data_dir = os.path.join(base_dir,folder_name, group)
    else:
        source_data_dir = os.path.join(base_dir, folder_name)

    # subjects_raw = os.listdir(source_data_dir)
    # pattern = re.compile(r"^sub.*")
    # subjects = [s for s in subjects_raw if pattern.match(s)]

    haveSes = []
    have_odd = []
    have_even = []
    have_not = []
    have_single_not = []
    have_single = []

    subjects = check_problems_nifti(base_dir,folder_name,templates,session,group)
    subject_list = subjects[0]

    for s in subject_list:
        #print(s)
        ses_id = "ses-" + session
        sub_id = "sub-" + s
        ses_path = os.path.join(source_data_dir, sub_id, ses_id)
        if not isEmpty(ses_path):
            haveSes.append(s)

            # print(s)
            acqs = []
            for key, template in templates.items():
                file_pattern = f"{source_data_dir}/{template.format(subject_id=s, ses_id=session)}"
                file_paths = glob.glob(file_pattern)[0]

                acqs.append(file_paths)
                        


            if shell == 'multishell':

                all_files = acqs
                list_nifti = [st for st in all_files if "dwi" in st]


                list_phase = [st.split("_")[3] for st in list_nifti]
                counter = Counter(list_phase)

                max_freq = max(counter.values())
                # print(max_freq)

                if max_freq == 2:
                    have_even.append(s)
                    # if max(counter.values())
                elif max_freq == 3:
                    have_odd.append(s)
                elif max_freq == 4:
                    have_not.append(s)

            elif shell == 'singleshell':

                if os.path.exists(os.path.join(ses_path,'fmap')):
                    all_files = acqs
                    list_nifti = [st for st in all_files if "fmap" in st]
                    if len([s for s in list_nifti if 'dir-AP' in s]) != 0 :
                        have_single.append(s)
                else: 
                    have_single_not.append(s)



            ### Add for single shell : 1PA /1 AP, or 1 PA no AP

    ### Get the list of subjects that have a mri at session i
    haveSes = [s for s in haveSes]
    # transformed_list_Ses = ','.join(haveSes)
    # result_list_Ses = [transformed_list_Ses]

    ### Get the list of subjects that have two inverse phase dwi on session i
    have_even = [s for s in have_even]
    # transformed_list_even = ','.join(have_even)
    # result_list_even = [transformed_list_even]

    ### Get the list of subjects that have only one phase dwi on session i
    have_odd = [s for s in have_odd]
    # transformed_list_odd = ','.join(have_odd)
    # result_list_odd = [transformed_list_odd]

    have_not = [s for s in have_not]
    # transformed_list_not = ','.join(have_not)
    # result_list_not = [transformed_list_not]

    ### Get the list of subject having three identical phases (PA or AP) --> odd

    ### Get the list of subject having two PA and two AP --> even


    # print(f"Even Workflow : {have_even}")
    # print(f"Odd Workflow : {have_odd}")
    # print(f"Synth Workflow : {have_not}")
    # print(f"Single shell Workflow : {have_single}")
    # print(f"Single shell synth Workflow : {have_single_not}")




    return haveSes, have_even, have_odd, have_not,have_single,have_single_not,subjects[1]



# templates_apex = {
#         "anat": "sub-{subject_id}/ses-{ses_id}/anat/sub-{subject_id}_ses-{ses_id}_T1w.nii.gz",
#         "dwiPA": "sub-{subject_id}/ses-{ses_id}/dwi/sub-{subject_id}_ses-{ses_id}_acq-*_dwi.nii.gz",
#         "dwiAP": "sub-{subject_id}/ses-{ses_id}/fmap/sub-{subject_id}_ses-{ses_id}_dir-AP_epi.nii.gz"
#     }


# templates_seq = {
#         "anat": "sub-{subject_id}/ses-{ses_id}/anat/sub-{subject_id}_ses-{ses_id}_T1w.nii.gz",
#         "dwi60": "sub-{subject_id}/ses-{ses_id}/dwi/sub-{subject_id}_ses-{ses_id}_acq-60dirs_dir-*_dwi.nii.gz",
#         "dwi45": "sub-{subject_id}/ses-{ses_id}/dwi/sub-{subject_id}_ses-{ses_id}_acq-45dirs_dir-*_dwi.nii.gz",
#         "dwi30": "sub-{subject_id}/ses-{ses_id}/dwi/sub-{subject_id}_ses-{ses_id}_acq-30dirs_dir-*_dwi.nii.gz",
#         "dwi6": "sub-{subject_id}/ses-{ses_id}/dwi/sub-{subject_id}_ses-{ses_id}_acq-6dirs_dir-*_dwi.nii.gz"
#     }

#lde,ls = check_problems_nifti('/Volumes/LaCie/apex/apex_data','rawdata',templates_apex,'post')
# stp,lde,ls = check_problems_nifti('/Volumes/LaCie/nifti3','nifti3',templates_seq,'002',group = "Patients")
# print(stp)
# print(len(stp))

# print(lde)
# print(ls)





# r = workflow_repartition(base_dir ='/Volumes/LaCie',folder_name = 'nifti3', session ="001",templates = templates_seq,shell = "multishell",group = 'Patients')
# r = workflow_repartition(base_dir ='/Volumes/LaCie/APEX/apex_data',folder_name = 'rawdata', session ="post",templates = templates_apex,shell = 'singleshell')


# print(r[0])
# print(r[1])
# print(r[2])
# print(r[3])
# print(r[4])
# print(r[5])
# print(r[6])
