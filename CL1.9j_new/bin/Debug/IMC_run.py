from torch.utils.tensorboard import SummaryWriter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import simple_phy_model as sim
import error_gen as err_gn
import xml.etree.ElementTree as ET
import argparse
import glob, os
import time
import random
import signal

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1' 

class file_check:
    '''
    Responsible for Checking, returning and deleting used model output files.
    '''
    def chk_files():
        '''
        Checks for numerical model output files and waits.
        Returns specific output file if available.
        '''
        time_cnt = 0
        for cvmt in range(120):
            flag0 = 0
            files_list = glob.glob("*.txt")

            for avk in files_list:
                 if avk.startswith('elevdiff10') == True:
                 #if avk.startswith('elev.dat10') == True:
                    est_dem_name = avk
                    flag0 = 1
                    
            if flag0 == 0: # File not present      
                time.sleep(10) #Wait
                if time_cnt%60 == 0:
                    print('# ', end = '',flush=True)
                time_cnt += 10
                
            elif flag0 ==1 :
                break

        return est_dem_name
    
    def del_process_files():
        '''
        Deletes numerical model output files
        '''
        files_list = glob.glob("*.txt")
        for avk in files_list:
            if (avk.startswith('elev.dat') == True):
                os.unlink(avk)
            if (avk.startswith('elevdiff') == True):
                os.unlink(avk)
        return None  


def handler(signum, frame):
    '''
    Handles ControlC press, for premature-exit
    '''
    file_01 = None
    print("\n Cntrl-C was pressed. Waiting for Physical model to finish processing . . . ")
    obj = file_check
    while file_01 == None:
        file_01 = obj.chk_files()
    print("Processing over. Deleting previous model output files . . .")
    obj.del_process_files()
    print("Exiting now...")
    exit(1)


def read_csv():
    '''
    Read parameter metadata from csv file.
    '''
    #csv_filename = args.filename_csv
    csv_filename = "CL_param_csv_short.csv"
    c = pd.read_csv(csv_filename,skiprows=1)
    c = c.drop(columns=['Parameter_name_in_CL'])

    ord_param_list = list(c) #make a list of csv columns (Assump: csv coulums are in order of high to low priority)
    low_lim = np.array(c.iloc[0]) #stores lower limit of all parameters in an array
    up_lim =  np.array(c.iloc[1]) #stores upper limit of all parameters in an array
    prior_mu = np.array(c.iloc[2]) #stores prior mu values
    prior_std = np.array(c.iloc[3]) #stores prior std value
    read_data = [low_lim,up_lim,prior_mu,prior_std, ord_param_list]
    return read_data


def save_to_xml(prior_mu,read_data):
    '''
    Updates xml with new parameter value
    '''
    #xml_name = args.filename_xml
    xml_name = "our_site.xml"
    
    lst = read_data[4] #ordered list of parameters to be updated
    tree = ET.parse(xml_name) #pass the paramter filename
    root = tree.getroot()
    for idx, param in enumerate(lst):
        for param in root.iter(param):
            #print("Index: {indx}, Parameter: {pname},  previous value: {prev}, updated to {new}".format(indx = idx, pname = param.tag, prev = param.text, new = prior_mu[idx]))
            param.text = str(float(prior_mu[idx]))
            param.set('updated','yes')
    tree.write(xml_name)


def get_params(curr_param_ID,read_data,cnt,itera, gauss=1): 
    '''
    Returns sample from a gaussian distr. 
    Based of value of 'gauss' parameter an epsilon greedy strategy can also taken
    Value of gauss may be taken as epsilon (default =1, i.e. non Eps. greedy strategy).
    '''
    prm_sugg = 0
    llim, uplim, prior_mu, prior_std = read_data[:4] #Unpack list partially
    # Keep sample if only it is inside the upper and lower limit 
    scl = prior_std[curr_param_ID] # get std dev.
    
    if gauss < 1:
        '''
        Generate using epsilon greedy strategy
        '''
        rn = np.random.rand(1)
        print("rnd_no. "+str(rn))
        if rn<gauss:
            prm_sugg = np.random.uniform (low= llim[curr_param_ID] , high= uplim[curr_param_ID])
            print("Epsilon parameter:"+str(prm_sugg))
        else:
            while (prm_sugg <= llim[curr_param_ID]) or (prm_sugg >uplim[curr_param_ID]):
                prm_sugg = np.random.normal(loc=prior_mu[curr_param_ID], scale=scl)
            print("Suggested parameter:"+str(prm_sugg))

    elif gauss == 1:
        '''
        Generate based only on Gaussian
        '''
        while (prm_sugg <= llim[curr_param_ID]) or (prm_sugg >uplim[curr_param_ID]):
            prm_sugg = np.random.normal(loc=prior_mu[curr_param_ID], scale=scl)
        print("Suggested parameter:"+str(prm_sugg))
    
    #Dont augment for first round   
    #if cnt == 0:
    #    prm_sugg = prior_mu[curr_param_ID]
    #else:
    #    pass

    return prm_sugg


def one_iteration(curr_param_ID, read_data, itera, flag = 0):
    '''
    Runs one iteration of 'cnt' number of rounds each iteration
    '''
    param_best = None
    cnt = 0
    err = 0
    err_min = None
    
    # prior_mu, prior_std, plist = read_data[2:] # Unpack the list partially
    llim, uplim, prior_mu, prior_std, plist = read_data[:5] 
    
    while (cnt<count): #iterate till end of #cnt
        '''
        Explore around given prior. Prior value is constant in a round
        '''
        print('----')
        print("Round No. :"+str(cnt))
        if cnt == 0:
            iseed = random.randint(1,100)
            #iseed = itera #Send iteration count as seed 
        else:
            pass
        #print("iseed_init:"+str(iseed))
        #----Obtain and upload parameter suggestion to CL, via xml----------
        llim, uplim, prior_mu, prior_std = read_data[:4] 
        print("Current prior mu: "+str(prior_mu[curr_param_ID]))
        
        
        # Get Gaussian sample around parameter prior
        sugg_param = get_params(curr_param_ID,read_data,cnt,itera) # Read_data is only updated for new round

        
        # Update in xml value pertaining to current parameter only
        prior_mu[curr_param_ID] = sugg_param   

        # Transfer latest suggested parameter values to XML file 
        save_to_xml(prior_mu,read_data)
        
        print(">> Executing CL-physical model \n")
        
        # Signal CL to read from updated xml and save final file to location
        os.startfile('CAESAR-lisflood 1.9j.exe') #execute CL and generate output
        
        # Check directory for processed files else wait
        obj = file_check
        est_dem_name = obj.chk_files()
    
        # Direct err_gen () to read the file and calculate/ return error
        err = err_gn.error_gen(est_dem_name, iseed)
        print('*ERROR this round:'+str(err)) # Direct error
        print('Corresponding parameter value:'+str(sugg_param))
        
        obj.del_process_files() #Delete process files from last round
        '''
        # Delete last read elevation files from location
        for avk in files_list:
            if (avk.startswith('elev.dat') == True):
                os.unlink(avk)
            if (avk.startswith('elevdiff10') == True):
                os.unlink(avk)
        '''
        #---Manage better parameters for later iterations---------------------------
        # INIT. error parameters (= err_min, param_best),... 
        # ... with first error and corresponding parameter
        if cnt == 0:
            err_min = err
            param_best = sugg_param
        elif (err < err_min) and (cnt >0): # Only if better than minimum recorded
            #print('Err {a} is < err_min {b}'.format(a=err, b=err_min))
            err_min = err
            param_best = sugg_param # keep a copy for local display
        else:
            pass
        #---------------------------------------------------------------------------

        #---If Early_Stopping...
        if err == thres:
            # save last mu and err 
            #if param_best!= None:
            #    prior_mu[curr_param_ID] = param_best
            print("\n")
            print("--------------------------------------------------")
            print('Calibration complete for {param}, with value: {val}.'.format(param=plist[curr_param_ID],val=sugg_param))
            print('Error :' +str(err))
            print("Breaking out...at trial no {v} of {k}, itertation:{i}.".format(v=cnt,k=count,i=itera))
            print("Cumulative trials count: {m}".format(m=cnt+count*itera))
            print("--------------------------------------------------")
            flag = 1 #Set 0->1 since round ended early
            break
        
        #---If END of Round reached...
        elif cnt == count-1:
            print("----------------------------------------------")
            print('Best this iteration, param '+str(param_best))
            print('Error :'+str(err_min)) 
            print("----------------------------------------------")
            print("\n")
            
        rn = np.random.rand(1)
        #if param_best!= None :
        #    prior_mu[curr_param_ID] = param_best #best this round
        
        # Update counter
        cnt = cnt+1  #update counter  
        
    # 'err' is final err score of iteration, 'err_min' is min error in the iteration (=cnt x round) and 
    # 'param_best' is the corresponding parameter.
    return err_min, param_best, flag #Dont need err
   




if __name__ == '__main__':
    
        writer = SummaryWriter('runs/calib_logs')
        signal.signal(signal.SIGINT, handler) #Register Control C press, handler method.
        
        # Enable command-line arguments
        parser = argparse.ArgumentParser(description='Initialization values')
        parser.add_argument('--threshold', type=float, default= 0.0, help='Error threshold value, for early stopping')
        parser.add_argument('--count', type=int, default=3, help='Round Counter value')
        parser.add_argument('--iter', type=int, default=5, help='Iteration Counter value')
        parser.add_argument('--filename_csv', type=str, default='CL_param_csv_short.csv',help='Filename of init value file')
        parser.add_argument('--filename_xml', type=str, default='our_site.xml',help='Filename of xml dump')

        args = parser.parse_args()
        
        #Initialize using parsed information    
        thres = args.threshold #Error Threshold value
        count = args.count #Looping count per round
        num_iter = args.iter #Iteration count
        
        iter_cont_cnt = 0
        min_err_ever = None
        last_param_ID = None
        values = []
        
        fig, axs = plt.subplots(2)
        # Read parameter init data from csv file -> 
        # read_data[[low_limits],[up_limits],[mu_all_params],[std_all_params],[ord_param_list]],list of 5 lists
        read_data = read_csv() #Do once 
        print('Read_data:'+str(read_data)) # Print read parameter table
        prior_mu = read_data[2] 


        # Run parameter-wise calibration
        for curr_param_ID, curr_param in enumerate(read_data[4]): #for each parameter in list
            print("\n")
            print('-> Calibrating for No.{a} parameter, name: {b}'.format(a=curr_param_ID+1, b = curr_param))
            iter_best = 0
            err_col = []
            r_err = []
            
            def_dat = read_data[2]
            iter_param_best =  def_dat[curr_param_ID] #last best from past param round
            
            iter_cont_cnt = curr_param_ID* num_iter
            iter_temp = None

            for itera in range(num_iter): # Run iterations
                print("\n #ITERATION:"+str(itera))   
                #---Run one iteration sub-routine...
                #...(1. New param, 2. upload xml, 3.exec. CL, 4.get error from CL o/p)
                # Passing best parameter recorded till last iteration as prior (in read_data)
                err_min, param_best, flag = one_iteration(curr_param_ID, read_data, itera) 
                writer.add_scalar("ErrMin(one_iteration), iteration", err_min, itera+ iter_cont_cnt)
                
                #Initialization
                if itera == 0 and curr_param_ID == 0:
                   min_err_ever = err_min
                #   temp = err_min
                #elif itera == 0 and curr_param_ID >0:
                #   temp = err_min
                   
              
                #Update prior if error less than minimum saved
                if (err_min <= min_err_ever): #and itera == num_iter-1: #for change in parameter
                    min_err_ever = err_min
                    prior_mu[curr_param_ID] = param_best
                    read_data[2] = prior_mu  # Update read_data list with updated 'prior_mu' vector*
                    iter_param_best = param_best
                    print('err_min <= min_err_ever, updated parameter : '+str(iter_param_best)) 
                    values.append(iter_param_best)

                elif (err_min > min_err_ever): #  and itera == num_iter-1:
                    prior_mu[curr_param_ID] = iter_param_best
                    read_data[2] = prior_mu  # Update read_data list with updated 'prior_mu' vector*    
                    print('err_min > min_err_ever, parameter not updated, curr. value : '+str(iter_param_best))
                    
                                     
                print('Current min_err {err_m}, min error ever: {ever}.'.format(err_m=err_min,ever = min_err_ever ))
                writer.add_scalar("MinErrEvr, iteration", min_err_ever, itera+ iter_cont_cnt)
                #err_col.append(err) # collect for error plotting
                
                if flag ==1:
                   break
                
        # Flush all output files
        obj = file_check
        obj.del_process_files()        
        save_to_xml(read_data[2],read_data) # Save final result to xml 
        #with open("Param_values.txt", "w") as output:
        #    output.write(str(values))
        print("\n")
        print('Final calibrated parameters: {j}.'.format(j = read_data[2])) #Print final result

        