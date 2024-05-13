import os
import pandas as pd


## Load the three files

source_dir = "/mnt/CONHECT_data/pipe_patients_10/main_workflow/grouped_results"

filename1 = source_dir + "/SC_ROIS_ALL.csv"

N1 = pd.read_csv(filename1)

group = ['V1' for x in range(N1.shape[0])]


N1['Group'] = group
print(N1.head())


source_dir2 = "/mnt/CONHECT_data/pipe_patients_20/main_workflow/grouped_results"
filename2 = source_dir2 + "/SC_ROIS_ALL.csv"

N2 = pd.read_csv(filename2)

group2 = ['V2' for x in range(N2.shape[0])]


N2['Group'] = group2
print(N2.head())


source_dir3 = "/mnt/CONHECT_data/pipe_patients_30/main_workflow/grouped_results"
filename3 = source_dir3 + "/SC_ROIS_ALL.csv"

N3 = pd.read_csv(filename3)

group3 = ['V3' for x in range(N3.shape[0])]


N3['Group'] = group3
print(N3.head())
### Add a column group 'N1' 'N2' 'N3'

## Merge the dataframe rows

All_groups_SC = pd.concat([N1,N2,N3],axis=0)
All_groups_SC.to_csv(source_dir + '/All_groups_SC.csv')
All_groups_SC.to_csv(source_dir2 + '/All_groups_SC.csv')
All_groups_SC.to_csv(source_dir3 + '/All_groups_SC.csv')

## Try using Network Conhect