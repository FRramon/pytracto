#################################################
####            Create ROI to ROI file       ####
#################################################

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import subprocess


from pytracto.tractography.tractography_utils import *


def create_roi_file(base_dir, folder_name, templates, ses_list, group,**kwargs):
    """
    This function create a xlsx file containing information of all connectivity matrixes for all subjects/sessions in a group.

    Args:
            source_dir (str): source directory (parent folder of dicom_dir)
            dicom_dir (str): directory where the DICOM are located
            ses_list (list[str]): list of sessions to be processed
            group (str): group of patients (either patients, temoins etc. )
    """


    if group == "Patients":
        result_dir = os.path.join(
            base_dir, "full_results", "main_workflow", "connectome"
        )
    else:
        result_dir =  os.path.join(
            base_dir, kwargs.get("out_dir"), "main_workflow", "connectome"
        )

    print(result_dir)
   
    method = "Deterministic"
    atlas = "Destrieux"

    metric_list = ["sc"]#, "odi", "ndi"]  # ["fa","sc","ad","adc","rd","fwf"]

    for metric in metric_list:
        all_non_zero_entries = []
        for ses in ses_list:


            slist = check_problems_nifti(base_dir, folder_name, templates, ses, group)
            subject_list = slist[0]



            for sub in subject_list:
                identifier = "_ses_id_" + ses + "_subject_id_" + sub
                connectome_dir = os.path.join(result_dir, identifier, method,atlas,metric)
                print(connectome_dir)
                if not os.path.exists(connectome_dir):
                    sys.exit(
                        f"Error File not Found: Pipeline has not created connectome matrix for {sub} on {ses}"
                    )
                else:
                    print(f"RUNNING : {sub} - {ses}")

                    print(f"--- Creating ROI file")
                    if (
                        metric == "fa"
                        or metric == "sc"
                        or metric == "rd"
                        or metric == "adc"
                        or metric == "ad"
                    ):
                        input_file = os.path.join(
                            connectome_dir, f"{metric}_connectivity_matrix.csv"
                        )
                    elif metric == "fwf" or metric == "odi" or metric == "ndi":
                        input_file = os.path.join(
                            connectome_dir, f"{metric.upper()}_connectivity_matrix.csv"
                        )

                    df = pd.read_csv(input_file)
                    # Create a list to store the non-zero entries for each subject and session
                    non_zero_entries = []
                    for i in range(df.shape[0]):
                        for j in range(i + 1, df.shape[1]):
                            if df.iloc[i, j] != 0 and i != 0 and j != 0:
                                non_zero_entries.append(
                                    {
                                        "subject": sub,
                                        "session": ses,
                                        "i": i,
                                        "j": j,
                                        metric: df.iloc[i, j],
                                    }
                                )

                    # Extend the list of all_non_zero_entries with the current subject and session entri

                    current_df = pd.DataFrame(non_zero_entries)

                    # Print the sum of the 'k' column for the current subject and session
                    # print(f"Sum of fibercount for {sub} on {ses}: {current_df['FiberCount'].sum()}")

                    print(f"--- Add cortical zones labels to roi file")

                    input_file = source_dir + "/dmri-pipeline/fs_a2009s.txt"
                    df_labelconvert = pd.read_csv(
                        input_file,
                        delim_whitespace=True,
                        comment="#",
                        header=None,
                        names=["index", "labelname", "R", "G", "B", "A"],
                    )

                    df_withlabels = pd.merge(
                        current_df,
                        df_labelconvert[["index", "labelname"]],
                        left_on="i",
                        right_on="index",
                        how="left",
                    )
                    df_withlabels.rename(columns={"labelname": "ROI1"}, inplace=True)
                    df_withlabels.drop(columns="index", inplace=True)

                    # Merge again for 'j' to get ROI2
                    df_withlabels = pd.merge(
                        df_withlabels,
                        df_labelconvert[["index", "labelname"]],
                        left_on="j",
                        right_on="index",
                        how="left",
                    )
                    df_withlabels.rename(columns={"labelname": "ROI2"}, inplace=True)
                    df_withlabels.drop(columns="index", inplace=True)

                    output_current_file = (
                        connectome_dir + f"/{sub}_{ses}_{metric}_ROIs.csv"
                    )
                    df_withlabels.to_csv(output_current_file, mode="w", index=False)

                    all_non_zero_entries.append(df_withlabels)

        result_df = pd.concat(all_non_zero_entries)

        group_dir = kwargs.get("out_dir")
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)

        # Write the result DataFrame to a new CSV file
        output_file = group_dir + f"/{metric}_ROIs.csv"
        print(output_file)
        result_df.to_csv(output_file, mode="w", index=False)


