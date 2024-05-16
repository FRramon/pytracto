from tkinter import *
import subprocess
import os
import signal
import pandas as pd
import sys

# code_dir = '/mnt/POOL_IRM08/CONHECT/dmri-pipeline'
# sys.path.append(code_dir)
from pytracto.tractography.tractography_utils import *


# def clickNormal():
#     global phase_encoding_dir
#     phase_encoding_dir = "Normal"
#     root.destroy()
#     #close opened image
#     return phase_encoding_dir

# def clickAbnormal():
#     global phase_encoding_dir
#     phase_encoding_dir = "Abnormal"
#     root.destroy()
#     #close opened image
#     return phase_encoding_dir
    
# def click2PA():
#     global phase_encoding_dir
#     phase_encoding_dir = "2 PA"
#     root.destroy()
#     #close opened image
#     return phase_encoding_dir
    
# def click2AP():
#     global phase_encoding_dir
#     phase_encoding_dir = "2 AP"
#     root.destroy()
#     #close opened image
#     return phase_encoding_dir

def clickA():
    global quality
    quality = "A"
    root.destroy()
    #close opened image
    return quality


def clickB():
    global quality
    quality = "B"
    root.destroy()
    #close opened image
    return quality

def clickC():
    global quality
    quality = "C"
    root.destroy()
    #close opened image
    return quality


# data_dir= '/mnt/POOL_IRM08/CONHECT/full_results'
# source_dir = '/mnt/POOL_IRM06/CONHECT/ConhectDatabase'
# base_dir = '/mnt/POOL_IRM08/CONHECT'
# start = 0
# group = ['Patients']
# ses_list = [1]

def execute_qa_check(data_dir: str,source_dir : str,base_dir: str,start: int,group: str,ses_list: list):
    """
    This function is an interactive program for quality assessment of the outputs of the dMRI pipeline. 
    It creates an excel with steps qualities.

    Args: 
        data_dir (str): directory that points to the pipeline's output directory
        source_dir (str): source directory where dicom are located
        base_dir (str): base directory
        start (int): line in the excel to (re) start
        group (str): group of subjects (either patients, temoins etc. )
        ses_list (list[int]): list of sessions to be processed

    """
    
    columns = ['Group', 'subject_id', 'session_id','anat','dwiAP','dwiPA','rsfmri','fmap','PE_direction','topup','topupquality','5tt mask','5tt quality','gmwmi','gmwmi quality', 'anat2diff quality','streamline reg quality']

    df = pd.DataFrame(columns=columns)

    # # Create a dictionary with the data for the new row



    for g in group:

        for ses in ses_list:

            result_list_Ses,result_list_even,result_list_odd,result_list_not, haveProblem = get_ids_by_sessions(source_dir,base_dir,g,ses)

            #print(subjects_list)

            subjects_list = result_list_Ses[0].split(',')

            print(subjects_list)

            ## Loop over patient ##


            for sub in subjects_list:


                has_fmap = 0
                has_anat = 0
                has_dwiAP = 0
                has_dwiPA = 0
                has_rsfmri = 0
                phase_encoding_dir = "NA"

                subject_id = 'sub-' + sub
                session_id = 'ses-00' + str(ses)
                identifier = '_ses_id_00' + str(ses) + '_subject_id_' + sub

                print(identifier)

                tracto_dir = os.path.join(data_dir,'main_workflow','wf_tractography',identifier)
                connectome_dir=  os.path.join(data_dir,'main_workflow','connectome',identifier)
                preproc_dir = os.path.join(data_dir,'main_workflow','preproc',identifier)


    ################################# CHECK FOR TOPUP & TOPUP QUALITY #############################################


                if os.path.isfile(f"{preproc_dir}/dwpreproc/preproc.mif"):

                    has_topup = 1

                    quality = "NA"

                    ## Open chosen image (mricron, mango, mrview, fsleyes, matplotlib.pyplot.imshow or nilearn.plotting ...) ##

                    command_view = f"mrview {base_dir}/nifti3/{g}/{subject_id}/{session_id}/anat/{subject_id}_{session_id}_T1w.nii.gz -overlay.load {preproc_dir}/dwpreproc/preproc.mif"# -overlay.opacity 0.6 -overlay.colour 0,0,255 "


                    pro = subprocess.Popen(command_view, stdout=subprocess.PIPE, 
                           shell=True, preexec_fn=os.setsid) 


                    root = Tk()
                    root.title("T1 registration to diffusion space quality ?")
                    root.geometry("500x160")
                    button1 = Button(root,text='A', command=clickA)
                    button1.pack()
                    button2 = Button(root,text='B', command=clickB)
                    button2.pack()
                    button3 = Button(root,text='C', command=clickC)
                    button3.pack()


                    root.mainloop()

                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  

                    topup_quality = quality

                    print(topup_quality)


    ################################# CHECK FOR 5TT AND 5TT QUALITY #############################################



                if os.path.isfile(f"{tracto_dir}/gen5tt/5tt.mif") and os.path.isfile(f"{preproc_dir}/biascorrect/biascorrect.mif"):

                    has_5tt = 1

                    quality = "NA"

                    ## Open chosen image (mricron, mango, mrview, fsleyes, matplotlib.pyplot.imshow or nilearn.plotting ...) ##

                    command_view = f"mrview {preproc_dir}/biascorrect/biascorrect.mif -overlay.load {tracto_dir}/gen5tt/5tt.mif -overlay.opacity 0.6 -overlay.colour 0,0,255 -overlay.intensity 0,15000"


                    pro = subprocess.Popen(command_view, stdout=subprocess.PIPE, 
                           shell=True, preexec_fn=os.setsid) 


                    root = Tk()
                    root.title("gray matter / white matter interface quality ?")
                    root.geometry("500x160")
                    button1 = Button(root,text='A', command=clickA)
                    button1.pack()
                    button2 = Button(root,text='B', command=clickB)
                    button2.pack()
                    button3 = Button(root,text='C', command=clickC)
                    button3.pack()


                    root.mainloop()

                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  

                    m5tt_quality = quality

                    print(m5tt_quality)
    ################################# CHECK FOR GMWMI & GMWMI QUALITY #############################################



                if os.path.isfile(f"{tracto_dir}/gmwmi/gmwmi.mif") and os.path.isfile(f"{preproc_dir}/biascorrect/biascorrect.mif"):

                    has_gmwmi = 1

                    quality = "NA"

                    ## Open chosen image (mricron, mango, mrview, fsleyes, matplotlib.pyplot.imshow or nilearn.plotting ...) ##

                    command_view = f"mrview {preproc_dir}/biascorrect/biascorrect.mif -overlay.load {tracto_dir}/gmwmi/gmwmi.mif -overlay.opacity 0.6 -overlay.colour 0,0,255 -overlay.intensity 0,15000"


                    pro = subprocess.Popen(command_view, stdout=subprocess.PIPE, 
                           shell=True, preexec_fn=os.setsid) 


                    root = Tk()
                    root.title("gray matter / white matter interface quality ?")
                    root.geometry("500x160")
                    button1 = Button(root,text='A', command=clickA)
                    button1.pack()
                    button2 = Button(root,text='B', command=clickB)
                    button2.pack()
                    button3 = Button(root,text='C', command=clickC)
                    button3.pack()


                    root.mainloop()

                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  

                    gmwmi_quality = quality

                    print(gmwmi_quality)


    ################################# CHECK FOR ANAT2DIFF REGISTRATION QUALITY #############################################


                if os.path.isfile(f"{tracto_dir}/transformT1/T1_coreg.mif") and os.path.isfile(f"{preproc_dir}/biascorrect/biascorrect.mif"):

                    #has_fmap = 1

                    quality = "NA"

                    ## Open chosen image (mricron, mango, mrview, fsleyes, matplotlib.pyplot.imshow or nilearn.plotting ...) ##

                    command_view = f"mrview {preproc_dir}/biascorrect/biascorrect.mif -overlay.load {tracto_dir}/transformT1/T1_coreg.mif -overlay.opacity 0.6 -overlay.colour 0,0,255 -overlay.intensity 0,15000"


                    pro = subprocess.Popen(command_view, stdout=subprocess.PIPE, 
                           shell=True, preexec_fn=os.setsid) 


                    root = Tk()
                    root.title("T1 registration to diffusion space quality ?")
                    root.geometry("500x160")
                    button1 = Button(root,text='A', command=clickA)
                    button1.pack()
                    button2 = Button(root,text='B', command=clickB)
                    button2.pack()
                    button3 = Button(root,text='C', command=clickC)
                    button3.pack()


                    root.mainloop()

                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  

                    anat2diff_quality = quality

                    print(anat2diff_quality)


    ################################# CHECK FOR PROB STREAMLINE REGISTRATION QUALITY #############################################


                if os.path.isfile(f"{tracto_dir}/tcksift2/sift_tracks.tck") and os.path.isfile(f"{preproc_dir}/biascorrect/biascorrect.mif"):

                    has_probsift = 1

                    quality = "NA"

                    ## Open chosen image (mricron, mango, mrview, fsleyes, matplotlib.pyplot.imshow or nilearn.plotting ...) ##

                    command_view = f"mrview {preproc_dir}/biascorrect/biascorrect.mif -overlay.load {tracto_dir}/transformT1/T1_coreg.mif -overlay.opacity 0.6 -overlay.colour 0,0,255 -overlay.intensity 0,15000"


                    pro = subprocess.Popen(command_view, stdout=subprocess.PIPE, 
                           shell=True, preexec_fn=os.setsid) 


                    root = Tk()
                    root.title("T1 registration to diffusion space quality ?")
                    root.geometry("500x160")
                    button1 = Button(root,text='A', command=clickA)
                    button1.pack()
                    button2 = Button(root,text='B', command=clickB)
                    button2.pack()
                    button3 = Button(root,text='C', command=clickC)
                    button3.pack()


                    root.mainloop()

                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  

                    anat2diff_quality = quality

                    print(anat2diff_quality)


    ################################# CHECK FOR DET STREAMLINE REGISTRATION QUALITY #############################################


                if os.path.isfile(f"{tracto_dir}/tcksift2Det/sift_tracks.tck") and os.path.isfile(f"{preproc_dir}/biascorrect/biascorrect.mif"):

                    has_detsift = 1

                    quality = "NA"

                    ## Open chosen image (mricron, mango, mrview, fsleyes, matplotlib.pyplot.imshow or nilearn.plotting ...) ##

                    command_view = f"mrview {preproc_dir}/biascorrect/biascorrect.mif -overlay.load {tracto_dir}/transformT1/T1_coreg.mif -overlay.opacity 0.6 -overlay.colour 0,0,255 -overlay.intensity 0,15000"


                    pro = subprocess.Popen(command_view, stdout=subprocess.PIPE, 
                           shell=True, preexec_fn=os.setsid) 


                    root = Tk()
                    root.title("T1 registration to diffusion space quality ?")
                    root.geometry("500x160")
                    button1 = Button(root,text='A', command=clickA)
                    button1.pack()
                    button2 = Button(root,text='B', command=clickB)
                    button2.pack()
                    button3 = Button(root,text='C', command=clickC)
                    button3.pack()


                    root.mainloop()

                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  

                    anat2diff_quality = quality

                    print(anat2diff_quality)

                # if os.path.isfile(f"{ses_dir}/{ses}/anat/{sub}_{ses}_T1w.nii.gz"):
                #     has_anat = 1
                # if os.path.isfile(f"{ses_dir}/{ses}/dwi/{sub}_{ses}_acq-6dirs_dir-AP_dwi.nii.gz"):
                #     has_dwiAP = 1
                # if os.path.isfile(f"{ses_dir}/{ses}/dwi/{sub}_{ses}_acq-60dirs_dir-PA_dwi.nii.gz"):
                #     has_dwiPA = 1
                # if os.path.isfile(f"{ses_dir}/{ses}/func/{sub}_{ses}_task-rest_bold.nii.gz"):
                #     has_rsfmri = 1


                row_iter = {'Group': g, 'subject_id': sub,'session_id': ses,'anat':has_anat,'dwiAP': has_dwiAP,'dwiPA':has_dwiPA,'rsfmri':has_rsfmri,'fmap' : has_fmap,'PE_direction':phase_encoding_dir}
                df = df._append(row_iter,ignore_index=True)
               # row_iter = pd.DataFrame(row_iter)

                #df = pd.concat([df,row_iter],ignore_index=True)



    df.to_csv("/mnt/POOL_IRM08/CONHECT/irm_inventory_conhect_patients.csv") ### To change
        
