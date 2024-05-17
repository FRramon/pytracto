# import os
# import argparse
# import sys
# #sys.path.append('/mnt/POOL_IRM08/CONHECT/dmri-pipeline')

# from pytracto.tractography.tractography_utils import *

# # base_dir = '/mnt/POOL_IRM08/CONHECT'
# # source_dir = '/mnt/POOL_IRM06/CONHECT/ConhectDatabase'
# # # arg1 = sys.argv[1]
# # # arg2 = sys.argv[2]

# # #subject_list = ["0" + str(i) for i in range(1,47)]
# # ses_list = ["1","2","3"]

# # group = "Patients"

# def get_percentage(L):
#     print(len(L))
#     fraction = sum(L) / len(L) * 100
#     return round(fraction, 2)

# def fill_list(L, step_file):
#     if os.path.isfile(step_file):
#         L.append(True)
#     else:
#         L.append(False)
#     return L

# def main(base_dir: str ,source_dir: str ,group: str, ses_list :list, output_file: str):
#     """
#     Function to generate a csv file of computation progress during the execution of the pipeline.

#     Args:
#         base_dir (str): base directory
#         source_dir (str): source directory (parent folder of dicom directory)
#         group (str): group of subjects to be processed (either patients, temoins etc. )
#         ses_list (list[int]): list of sessions to be processed
#         output_file (str): filename for the output file
#     """
#     progress_report = []

#     for ses in ses_list:
#         den_list, eddy_list, sift_list, tckgen_list, fs_list, preproc_list = [], [], [], [], [], []

#         print(f"Progress in session {ses}")

#         all_subject_list = get_ids_by_sessions(source_dir,base_dir,group,int(ses))
#         subject_list =all_subject_list[2][0].split(',')
#         ses = "00" + ses
#         for sub in subject_list:

#             identifier = f'_ses_id_{ses}_subject_id_{sub}'
#             print(identifier)
#             res_dir = os.path.join(base_dir,'full_results')
#             main_workflow_dir = os.path.join(res_dir, 'main_workflow')
#             preproc_dir = os.path.join(main_workflow_dir, 'preproc', identifier)
#             tracto_dir = os.path.join(main_workflow_dir, 'wf_tractography', identifier)
#             connectome_dir = os.path.join(main_workflow_dir, 'connectome', identifier)

#             den_file = os.path.join(preproc_dir, "denoise", "concatenated_denoised.mif")
#             print(den_file)
#             den_list = fill_list(den_list, den_file)

#             eddy_file = os.path.join(preproc_dir, "dwpreproc", "preproc.mif")
#             eddy_list = fill_list(eddy_list, eddy_file)

#             preproc_file = os.path.join(preproc_dir, "biascorrect", "biascorrect.mif")
#             preproc_list = fill_list(preproc_list, preproc_file)

#             tckgen_file = os.path.join(tracto_dir, "tckgen", "tracked.tck")
#             tckgen_list = fill_list(tckgen_list, tckgen_file)

#             sift_file = os.path.join(tracto_dir, "tcksift2", "sift_tracks.tck")
#             sift_list = fill_list(sift_list, sift_file)
#             fs_file = os.path.join(main_workflow_dir, "fs_workflow", identifier, "fs_reconall", sub, "mri","aparc.a2009s+aseg.mgz")
#             fs_list = fill_list(fs_list, fs_file)

#         progress_report.append(f"Progress in session {ses}\n")
#         progress_report.append("T1 Processing\n")
#         progress_report.append(f"    Freesurfer reconall: {get_percentage(fs_list)}%\n")
#         progress_report.append("DWI Processing\n")
#         progress_report.append(f"    Denoising: {get_percentage(den_list)}%\n")
#         progress_report.append(f"    Eddy preproc: {get_percentage(eddy_list)}%\n")
#         progress_report.append(f"    Complete preprocessing: {get_percentage(preproc_list)}%\n")
#         progress_report.append(f"    Generate tracks: {get_percentage(tckgen_list)}%\n")
#         progress_report.append(f"    Complete tractography: {get_percentage(sift_list)}%\n")


#     with open(output_file, 'w') as f:
#         f.writelines(progress_report)


# #main(base_dir,source_dir, group, ses_list, "/home/francoisramon/Desktop/test_av.txt")
