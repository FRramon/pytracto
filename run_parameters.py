################################################################
######                    Instructions                   #######
################################################################


convert2bids = False
run_pipeline = True

createMatrixes = False
createROIfile = False
QAcheck = False
bundleSegmentation= False
ClusterConsensus = False


#### 				     	INPUTS        	                ####


source_dir = '/mnt/POOL_IRM08/CONHECT'
dicom_dir = '/mnt/POOL_IRM06/CONHECT/ConhectDatabase'
data_folder = 'nifti3'
group = 'Patients'
session_list = [2]
pipe_name = 'full_results'
result_name = 'results_patients_20'
ntracks = 10000000



