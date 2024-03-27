import pandas as pd
import numpy as np
import sys
from scipy.stats import pearsonr,spearmanr
import matplotlib.pyplot as plt

def join_clinical_data(clinique,D):

	D = D.rename(columns={"ids":"subject_id","Group":"session_id"})

	D = D.join(clinique[['subject_id','remission','reponse']].set_index('subject_id'), on='subject_id')[['subject_id','session_id','Y','remission','reponse']]

	return D

wd = '/mnt/CONHECT_data/code'


def correlation_metric_clinic(D,session_id,grouping,plot = False):

	D = D.loc[D['session_id'] == session_id][['session_id','Y','remission','reponse']]
	D = D.dropna(subset = [grouping])
	# print(D.head())
	# print(D['remission'])
	X = D['Y']
	Y = D[grouping]
	r,p = pearsonr(X,Y)
	print(r)
	print(p)

	if plot == True:
		plt.plot(X,Y,'ro')
		plt.show()
	return r,p


clinic_data = pd.read_excel(wd + '/Clinique_pourfrancois.xlsx')
D = pd.read_csv('/home/imabrain/global_effFintra.csv')
D = join_clinical_data(clinic_data,D)
#D = D.drop(D[D['subject_id'] == '1-E-147-FE'].index)

correlation_metric_clinic(D,'V1','remission',plot = True)

#D.to_csv(wd + '/metric_with_clinical_outcome.csv')



metric_list = ['global_eff','local_eff','characteristic_path','clust_coeff']
weight_list = ['FBC','FA','NDI','Fintra','GFA','ODI','PD','TD']
session_list = ['V1','V2','V3']

def get_full_correlation_table(wd,metric_list,weight_list,session_list,grouping):

	emptyDF = pd.DataFrame(columns = ['metric','weight','session_id','r','p'])

	clinic_data = pd.read_excel(wd + '/Clinique_pourfrancois.xlsx')

	for metric in metric_list:
		for weight in weight_list:
			identifier = metric +  weight + '.csv'
			print(identifier)
			metrics_data = pd.read_csv('/home/imabrain/' + identifier)

			for session in session_list:
				D = join_clinical_data(clinic_data,metrics_data)
				D = D.drop(D[D['subject_id'] == '1-E-147-FE'].index)
				r,p = correlation_metric_clinic(D,session,grouping)
				newrow = {'metric':metric,'weight':weight,'session_id':session,'r':r,'p':p}
				emptyDF.loc[len(emptyDF)] = newrow

	print(emptyDF.head())
	emptyDF.to_csv(wd + '/all_correlations_' + grouping + '.csv')


#get_full_correlation_table(wd,metric_list,weight_list,session_list,'remission')
				

