### PREPROCESSING PARAMETERS ###

# Eddy options for eddy currents correction based on topup
eddyoptions_param = " --slm=linear"
# Using ANTs for bias correction
useants_param = True

### FREESURFER PARAMETERS ###

# reconall parameter, base is 'all'
reconall_param = "all"

## ODF'S ESTIMATION PARAMETERS ###

# FOD estimation algorithm, base is 'dhollander' most adapted for Multi Shell / Multi Tissue ODFs
fod_algorithm_param = "dhollander"
# CSD algoritm, base is 'msmt_csd' : most adapted for Multi Shell / Multi Tissue ODFs
csd_algorithm_param = "msmt_csd"
tt_algorithm_param = "fsl"

##### TRACTOGRAPHY PARAMETERS ####

# Flirt parameters for T1 registration
flirt_interp_param = "nearestneighbour"
flirt_dof_param = 6

# Tractography algorithm, base is 'iFOD2' (probabilistic), and deterministic is 'DTI'
tckgen_algorithm_param = "iFOD2"
tckgen_backtrack_param = True
# Recommended ntracks is 10 000 000 for the number of streamlines generated. SIFT will filter afterward
# tckgen_ntracks_param = 30000000

#### BUILD CONNECTOME ####

# Path to desired atlas in user's mrtrix3/labelconvert directory
labelconvert_param = "/mnt/POOL_IRM08/CONHECT/dmri-pipeline/fs_a2009s.txt"
# Path to LUT file in $FREESURFER_HOME directory
fs_lut_param = "/mnt/POOL_IRM08/CONHECT/dmri-pipeline/FreeSurferColorLUT.txt"

### COMPUTATIONAL PARAMETERS

plugin_processing = "MultiProc"
