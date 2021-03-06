import pandas as pd
import numpy as np
import correlation_computer as cc
import sys, multiprocessing, functools

### Utils ###

def load_score_map(input_prefix, day, measure, epsilon=0.000000001):
    """The centrality maps were pre-sorted in decreasing order!!!"""
    scores = pd.read_csv(input_prefix + '/%s_scores_%i.txt_s' % (measure,day), sep=" ", names=["id","score"])
    scores = scores.set_index("id")
    # all active nodes is set to have positive centrality scores
    if epsilon != None:
        scores["score"] = scores["score"] + epsilon
    return scores


def result2file(result_list,file_name):
    """Write correlation values to file for each snapshot."""
    with open(file_name, 'w') as f:
        if len(result_list) == 1:
            f.write('%f\n' % (result_list[0]))
        else:
            for i in xrange(len(result_list)):
                f.write('%i %f\n' % (i, result_list[i]))
    print 'Done'


def calculate_corr_for_a_day(input_prefix, corr_type, measure, day, output_prefix=None):
    """Calculate the selected correlation measure for the given snapshot."""
    prev_day = load_score_map(input_prefix, day-1, measure)
    current_day = load_score_map(input_prefix, day, measure)
    corr = None
    if corr_type=="pearson":
        corr = cc.corr_pearson(prev_day,current_day)[0]
    elif corr_type=="spearman":
        corr = cc.corr_spearman(prev_day,current_day)[0]
    elif corr_type=="kendall":
        corr = cc.corr_kendalltau(prev_day,current_day)[0]
    elif corr_type=="w_kendall":
        corr = cc.corr_weighted_kendalltau(prev_day,current_day,use_fast=False)[0]
    elif corr_type=="w_kendall_fast":
        corr = cc.corr_weighted_kendalltau(prev_day,current_day,use_fast=True)[0]
    else:
        raise RuntimeError("Invalid correlation type: %s!" % corr_type)
    if output_prefix == None:
    	return corr
    else:
	result2file([corr], '%s_%s_%i.%s' % (output_prefix, measure, day-1, corr_type))
        

def calculate_corr_for_days(input_prefix, days, corr_type, measure_type, n_threads=10):
    """Calculate the selected correlation measure for multiple snapshots. 
    Choose from 'pearson', 'spearman', 'kendall' or 'w_kendall'."""
    #return map(lambda x: calculate_corr_for_a_day(input_prefix, corr_type, measure_type, x), days)
    f_partial = functools.partial(calculate_corr_for_a_day,input_prefix,corr_type,measure_type)
    pool = multiprocessing.Pool(processes=n_threads)
    res = pool.map(f_partial, days)
    pool.close()
    pool.join()
    return res
    

### Popularity model ###

import scipy.stats as stats

def get_correlations_from_matrix(A, num_of_days, corr_type):
    if corr_type=="pearson":
        corr = map(lambda i : stats.pearsonr(A[i-1,:],A[i,:])[0], range(1,num_of_days))
    elif corr_type=="spearman":
        corr = map(lambda i : stats.spearmanr(A[i-1,:],A[i,:])[0], range(1,num_of_days))
    elif corr_type=="kendall":
        print "NOTE: Execution can be very slow for big vectors!"
        corr = map(lambda i : stats.kendalltau(A[i-1,:],A[i,:])[0], range(1,num_of_days))
    else:
        raise RuntimeError("Invalid correlation type: %s!" % corr_type)
    return corr

def sort_and_get_corr(A, corr_type, idx):
    two_day_df = pd.DataFrame(A[[idx-1,idx],:].T, columns=["prev","curr"]) # transposition is needed!
    two_day_df["id"] = two_day_df.index
    prev_df = two_day_df[["id","prev"]].query("prev>0")
    curr_df = two_day_df[["id","curr"]].query("curr>0")
    prev_df.sort_values("prev", ascending=False, inplace=True)
    curr_df.sort_values("curr", ascending=False, inplace=True)
    prev_day = prev_df.set_index("id")
    current_day = curr_df.set_index("id")
    if corr_type=="pearson":
        corr = cc.corr_pearson(prev_day,current_day)[0]
    elif corr_type=="spearman":
        corr = cc.corr_spearman(prev_day,current_day)[0]
    elif corr_type=="kendall":
        corr = cc.corr_kendalltau(prev_day,current_day)[0]
    elif corr_type=="w_kendall":
        corr = cc.corr_weighted_kendalltau(prev_day,current_day,use_fast=False)[0]
    elif corr_type=="w_kendall_fast":
        corr = cc.corr_weighted_kendalltau(prev_day,current_day,use_fast=True)[0]
    else:
        raise RuntimeError("Invalid correlation type: %s!" % corr_type)
    return corr
    
def get_correlations_from_matrix_for_act(A, num_of_days, corr_type, n_threads=4):
    """Function to call scipy correlation code for active vertices.
    Matrix A contains scores from popularity model."""
    #return map(lambda i : sort_and_get_corr(A,i,corr_type=corr_type), range(1,num_of_days))
    f_partial = functools.partial(sort_and_get_corr,A,corr_type)
    pool = multiprocessing.Pool(processes=n_threads)
    res = pool.map(f_partial, range(1,num_of_days))
    pool.close()
    pool.join()
    return res


if __name__ == "__main__":
    if len(sys.argv) == 6:
        input_prefix = sys.argv[1]
        output_prefix = sys.argv[2]
        corr_type = sys.argv[3]
        measure = sys.argv[4]
        day = int(sys.argv[5])
        
        calculate_corr_for_a_day(input_prefix, corr_type, measure, day, output_prefix)
    else:
        print "Usage: <input_prefix> <output_prefix> <corr_type> <measure> <second_day>"		

