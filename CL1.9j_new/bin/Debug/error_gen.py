'''
Read dem ascii files from a designated folder.
Generate error corresponding to ground truth and estimated dem files, where error = cosine similarity + dod
'''

from traceback import format_list
import numpy as np 
from numpy.linalg import norm
import pandas as pd
import glob
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.metrics.cluster import normalized_mutual_info_score
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
import math
import tensorflow as tf
import random
import sys
 

def error_gen(est_dem_name,iseed):
    err =0
    cos_app = 0
    sub_app = 0
    # Read ground_truth_dod.txt and Estimated_dod.txt for comparison
    #df_g_truth = pd.read_csv('dod_19-21_orig_CL.txt', skiprows=6, delim_whitespace=True, header = None )
    df_g_truth = pd.read_csv('dod_19-21_orig.txt', skiprows=6, delim_whitespace=True, header = None )
    df_est = pd.read_csv(est_dem_name, skiprows=6, delim_whitespace=True, header = None )
    
    
    #np.random.seed(iseed)
    #fillna
    df_g_truth= df_g_truth.fillna(-9999)
    df_g_truth = df_g_truth.astype('float32')
    df_est = df_est.fillna(-9999)
    df_est = df_est.astype('float32')
    
    mask = tf.cast(tf.math.greater(df_g_truth,0), tf.float32) #Define a mask based on ground truth (consider only negative values)
    df_g_truth = np.asarray(df_g_truth) * mask
    df_est = np.asarray(df_est) * mask

   
    #mse_patch = tf.keras.metrics.mean_squared_error(g_truth, pred_dem)

      
    mse = tf.keras.metrics.mean_squared_error(np.asarray(df_g_truth) , np.asarray(df_est)).numpy()
    #cosine_loss = tf.keras.losses.CosineSimilarity(axis=1)
    #csn_ls = cosine_loss(np.asarray(df_g_truth), np.asarray(df_est) ).numpy()
    err = np.mean(mse)
    #print('Unwt. Cos. sim.:'+str(csn_ls))
    #print('Unwt. Mse:'+str(err))
    
    return err
