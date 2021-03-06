# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import seaborn as sns
import networkx as nx
import matplotlib as mpl
import numpy as np
from math import pi
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture as GMM
from umap import UMAP
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from datetime import date
from warnings import filterwarnings
import os
import community

import keras
from keras.models import Sequential
from keras.layers import Dense
from keras import regularizers
from keras.utils import np_utils
from keras.metrics import categorical_accuracy
from keras.layers import Dropout
import keras.backend as K
import scipy.stats as st


filterwarnings('ignore')

# -------   PLOTTING FUNCTIONS -------------------------


def set_plotting_style():
      
    """
    Plotting style parameters, based on the RP group. 
    """    
        
    tw = 1.5

    rc = {'lines.linewidth': 2,
        'axes.labelsize': 18,
        'axes.titlesize': 21,
        'xtick.major' : 16,
        'ytick.major' : 16,
        'xtick.major.width': tw,
        'xtick.minor.width': tw,
        'ytick.major.width': tw,
        'ytick.minor.width': tw,
        'xtick.labelsize': 'large',
        'ytick.labelsize': 'large',
        'font.family': 'sans',
        'weight':'bold',
        'grid.linestyle': ':',
        'grid.linewidth': 1.5,
        'grid.color': '#ffffff',
        'mathtext.fontset': 'stixsans',
        'mathtext.sf': 'fantasy',
        'legend.frameon': True,
        'legend.fontsize': 12, 
       "xtick.direction": "in","ytick.direction": "in"}



    plt.rc('text.latex', preamble=r'\usepackage{sfmath}')
    plt.rc('mathtext', fontset='stixsans', sf='sans')
    sns.set_style('ticks', rc=rc)

    #sns.set_palette("colorblind", color_codes=True)
    sns.set_context('notebook', rc=rc)

    rcParams['axes.titlepad'] = 20 


def bokeh_style():

    '''
    Formats bokeh plotting enviroment. Based on the RPgroup PBoC style.
    '''
    theme_json = {'attrs':{'Axis': {
            'axis_label_text_font': 'Helvetica',
            'axis_label_text_font_style': 'normal'
            },
            'Legend': {
                'border_line_width': 1.5,
                'background_fill_alpha': 0.5
            },
            'Text': {
                'text_font_style': 'normal',
               'text_font': 'Helvetica'
            },
            'Title': {
                #'background_fill_color': '#FFEDC0',
                'text_font_style': 'normal',
                'align': 'center',
                'text_font': 'Helvetica',
                'offset': 2,
            }}}

    return theme_json


def get_gene_data(data, gene_name_column, test_gene_list):
    
    """Extract data from specific genes given a larger dataframe.
    
    Inputs
    
    * data: large dataframe from where to filter
    * gene_name_column: column to filter from
    * test_gene_list : a list of genes you want to get
    
    Output
    * dataframe with the genes you want
    """
    
    gene_profiles = pd.DataFrame()

    for gene in data[gene_name_column].values:

        if gene in test_gene_list: 

            df_ = data[(data[gene_name_column] == gene)]

            gene_profiles = pd.concat([gene_profiles, df_])
    
    gene_profiles.drop_duplicates(inplace = True)
    
    return gene_profiles

# ---------PANDAS FUNCTIONS FOR DATA EXPLORATION -------------------------
def count_feature_types(data):
    
    """
    Get the dtype counts for a dataframe's columns. 
    """
    
    df_feature_type = data.dtypes.sort_values().to_frame('feature_type')\
    .groupby(by='feature_type').size().to_frame('count').reset_index()
    
    return df_feature_type


def get_df_missing_columns(data):
    
    '''
    
    Get a dataframe of the missing values in each column with its corresponding dtype.
    
    '''
    
    # Generate a DataFrame with the % of missing values for each column
    df_missing_values = (data.isnull().sum(axis = 0) / len(data) * 100)\
                        .sort_values(ascending = False)\
                        .to_frame('% missing_values').reset_index()
    
    # Generate a DataFrame that indicated the data type for each column
    df_feature_type = data.dtypes.to_frame('feature_type').reset_index()
    
    # Merge frames
    missing_cols_df = pd.merge(df_feature_type, df_missing_values, on = 'index',
                         how = 'inner')

    missing_cols_df.sort_values(['% missing_values', 'feature_type'], inplace = True)
    
    
    return missing_cols_df


def find_constant_features(data):
    
    """
    Get a list of the constant features in a dataframe. 
    """
    const_features = []
    for column in list(data.columns):
        if data[column].unique().size < 2:
            const_features.append(column)
    return const_features


def duplicate_columns(frame):
    '''
    Get a list of the duplicate columns in a pandas dataframe.
    '''
    groups = frame.columns.to_series().groupby(frame.dtypes).groups
    dups = []

    for t, v in groups.items():

        cs = frame[v].columns
        vs = frame[v]
        lcs = len(cs)

        for i in range(lcs):
            ia = vs.iloc[:,i].values
            for j in range(i+1, lcs):
                ja = vs.iloc[:,j].values
                if np.array_equal(ia, ja):
                    dups.append(cs[i])
                    break
    return dups


def get_duplicate_columns(df):
        
    """
    Returns a list of duplicate columns 
    """
    
    groups = df.columns.to_series().groupby(df.dtypes).groups
    dups = []

    for t, v in groups.items():

        cs = df[v].columns
        vs = df[v]
        lcs = len(cs)

        for i in range(lcs):
            ia = vs.iloc[:,i].values
            for j in range(i+1, lcs):
                ja = vs.iloc[:,j].values
                if np.array_equal(ia, ja):
                    dups.append(cs[i])
                    break
    return dups


def get_df_stats(df):
    
    """
    Wrapper for dataframe stats. 
    
    Output: missing_cols_df, const_feats, dup_cols_list
    """
    missing_cols_df = get_df_missing_columns(df)
    const_features_list = find_constant_features(df)
    dup_cols_list = duplicate_columns(df)

    return missing_cols_df, const_features_list, dup_cols_list


def test_missing_data(df, fname):
    
    """Look for missing entries in a DataFrame."""
    
    assert np.all(df.notnull()), fname + ' contains missing data'



def col_encoding(df, column):
    
    """
    Returns a one hot encoding of a categorical colunmn of a DataFrame.
    
    ------------------------------------------------------------------
    
    inputs~~

    -df:
    -column: name of the column to be one-hot-encoded in string format.
    
    outputs~~
    
    - hot_encoded: one-hot-encoding in matrix format. 
    
    """
    
    le = LabelEncoder()
    
    label_encoded = le.fit_transform(df[column].values)
    
    hot = OneHotEncoder(sparse = False)
    
    hot_encoded = hot.fit_transform(label_encoded.reshape(len(label_encoded), 1))
    
    return hot_encoded


def one_hot_df(df, cat_col_list):
    
    """
    Make one hot encoding on categoric columns.
    
    Returns a dataframe for the categoric columns provided.
    -------------------------
    inputs
    
    - df: original input DataFrame
    - cat_col_list: list of categorical columns to encode.
    
    outputs
    - df_hot: one hot encoded subset of the original DataFrame.
    """

    df_hot = pd.DataFrame()

    for col in cat_col_list:     

        encoded_matrix = col_encoding(df, col)

        df_ = pd.DataFrame(encoded_matrix,
                           columns = [col+ ' ' + str(int(i))\
                                      for i in range(encoded_matrix.shape[1])])

        df_hot = pd.concat([df_hot, df_], axis = 1)
        
    return df_hot


# OTHER FUNCTIONS

def plot_kmeans(kmeans, X, n_clusters=4, rseed=0, ax=None):
    
    """
    Wrapper from JakeVDP data analysis handbook
    """
    labels = kmeans.fit_predict(X)

    # plot the input data
    ax = ax or plt.gca()
    ax.axis('equal')
    ax.scatter(X[:, 0], X[:, 1], c=labels, s=40, cmap='viridis', zorder=2)

    # plot the representation of the KMeans model
    centers = kmeans.cluster_centers_
    radii = [cdist(X[labels == i], [center]).max()
             for i, center in enumerate(centers)]
    for c, r in zip(centers, radii):
        ax.add_patch(plt.Circle(c, r, fc='#CCCCCC', lw=3, alpha=0.5, zorder=1))


def net_stats(G):
    
    '''Get basic network stats and plots. Specifically degree and clustering coefficient distributions.'''
    
    net_degree_distribution= []

    for i in list(G.degree()):
        net_degree_distribution.append(i[1])
        
    print("Number of nodes in the network: %d" %G.number_of_nodes())
    print("Number of edges in the network: %d" %G.number_of_edges())
    print("Avg node degree: %.2f" %np.mean(list(net_degree_distribution)))
    print('Avg clustering coefficient: %.2f'%nx.cluster.average_clustering(G))
    print('Network density: %.2f'%nx.density(G))

    
    fig, axes = plt.subplots(1,2, figsize = (16,4))

    axes[0].hist(list(net_degree_distribution), bins=20, color = 'lightblue')
    axes[0].set_xlabel("Degree $k$")
    
    #axes[0].set_ylabel("$P(k)$")
    
    axes[1].hist(list(nx.clustering(G).values()), bins= 20, color = 'lightgrey')
    axes[1].set_xlabel("Clustering Coefficient $C$")
    #axes[1].set_ylabel("$P(k)$")
    axes[1].set_xlim([0,1])


def get_network_hubs(ntw):
    
    """
    input: NetworkX ntw
    output:Prints a list of global regulator name and eigenvector centrality score pairs
    """
    
    eigen_cen = nx.eigenvector_centrality(ntw)
    
    hubs = sorted(eigen_cen.items(), key = lambda cc:cc[1], reverse = True)[:10]
    
    return hubs


def get_network_clusters(network_lcc, n_clusters):
    
    """
    input = an empyty list
    
    output = a list with the netoworks clusters
    
    """
    cluster_list = []
    
    for i in range(n_clusters):

        cluster_lcc = [n for n in network_lcc.nodes()\
                       if network_lcc.node[n]['modularity'] == i]

        cluster_list.append(cluster_lcc)

    return cluster_list

def download_and_preprocess_data(org, data_dir = None, variance_ratio = 0.8, 
                                output_path = '~/Downloads/'):
    
    """
    General function to download and preprocess dataset from Colombos. 
    Might have some issues for using with Windows. If you're using windows
    I recommend using the urllib for downloading the dataset. 
    
    Params
    -------
    
    
    data_path (str): path to directory + filename. If none it will download the data
                     from the internet. 
                     
    org (str) : Organism to work with. Available datasets are E. coli (ecoli), 
                B.subtilis (bsubt), P. aeruginosa (paeru), M. tb (mtube), etc. 
                Source: http://colombos.net/cws_data/compendium_data/
                
    variance (float): Fraction of the variance explained to make the PCA denoising. 
    
    Returns
    --------
    
    denoised (pd.DataFrame)
    
    """
    #Check if dataset is in directory
    if data_dir is None:
        
        download_cmd = 'wget http://colombos.net/cws_data/compendium_data/'\
                      + org + '_compendium_data.zip'
        
        unzip_cmd = 'unzip '+org +'_compendium_data.zip'
        
        os.system(download_cmd)
        os.system(unzip_cmd)
        
        df = pd.read_csv('colombos_'+ org + '_exprdata_20151029.txt',
                         sep = '\t', skiprows= np.arange(6))
        
        df.rename(columns = {'Gene name': 'gene name'}, inplace = True)
        
        df['gene name'] = df['gene name'].apply(lambda x: x.lower())
        
    else: 
        
        df = pd.read_csv(data_dir, sep = '\t', skiprows= np.arange(6))
        try : 
            df.rename(columns = {'Gene name': 'gene name'}, inplace = True)
        except:
            pass
    annot = df.iloc[:, :3]
    data = df.iloc[:, 3:]

    preprocess = make_pipeline(SimpleImputer( strategy = 'median'),
                               StandardScaler(), )

    scaled_data = preprocess.fit_transform(data)
    
    # Initialize PCA object
    pca = PCA(variance_ratio, random_state = 42).fit(scaled_data)
    
    # Project to PCA space
    projected = pca.fit_transform(scaled_data)
    
    # Reconstruct the dataset using 80% of the variance of the data 
    reconstructed = pca.inverse_transform(projected)

    # Save into a dataframe
    reconstructed_df = pd.DataFrame(reconstructed, columns = data.columns.to_list())

    # Concatenate with annotation data
    denoised_df = pd.concat([annot, reconstructed_df], axis = 1)
    
    denoised_df['gene name'] = denoised_df['gene name'].apply(lambda x: x.lower())

    # Export dataset 
    denoised_df.to_csv(output_path + 'denoised_' + org + '.csv', index = False)


def lower_strings(string_list):
    """
    Helper function to return lowercase version of a list of strings.
    """
    return [str(x).lower() for x in string_list]


def load_gene_ontology_data(): 
    
    """Load the GO annotation dataset of E. coli K-12. """
    
    gene_ontology_data = pd.read_csv('../data/GO_annotations_ecoli.csv')
    
    return gene_ontology_data

def get_GO_gene_set(gene_ontology_data, test_gene_list):
    
    """
    Given a list of genes of interest and the Gene Ontology annotation dataset,
    filter the Gene Ontology dataset for E. coli to make an enrichment analysis.
    _____________________________________________________________________________
    
    inputs~
    
    gene_ontology_data: GO annotation dataset.
    test_gene_list: List of genes of interest.  
    
    outputs~
    
    GO_gene_set:Filtered GO annotation dataset corresponding to the test gene set. 
    
    """
    gene_ontology_data = load_gene_ontology_data()
    
    #Call the sortSeq library to lower the gene names
    gene_ontology_data.gene_name = lower_strings(gene_ontology_data.gene_name.values)
    
    #Call the sortSeq library filter only the GO data from the test gene list 
    GO_gene_set = get_gene_data(gene_ontology_data, 'gene_name', test_gene_list)
    
    return GO_gene_set

def get_hi_GOs(GO_gene_set):
    
    """
    Get the GO IDs whose counts are above the 5% of the total entries of the GO_gene_set.
    
    This allows to reduce our search space and only calculate enrichment p-values for highly 
    represented GOs.
    
    * GO: gene ontology 
    
    -------------------------------------------------------
    input~ GO_gene_set :Filtered GO annotation dataset corresponding to the test gene set. 
    
    output ~ GO IDs that represent > 10% of the dataset. 
    """
    #Treshold = get only the GOs whose counts > 10% of the total counts of GOs in the gene set 
    thr = int(GO_gene_set.shape[0] * 0.10)
    
    #Check that GO_gene_set is not empty.
    if GO_gene_set.shape[0] > 1:
    
        #Get the indices of the GOs that are above the threshold 
        hi_indices = GO_gene_set.GO_ID.value_counts().values > thr


        #Filter and get the GO IDs that are above threshold
        hi_GO_ids = GO_gene_set.GO_ID.value_counts().loc[hi_indices].index.values
        
        #Check that there are GO_IDs above the threshold
        if len(hi_GO_ids) > 0:

            return hi_GO_ids

        else: 
            print('No enriched functions found.')
                
    else: 
        
        print('No enriched functions found.')

def get_hyper_test_p_value(gene_ontology_data, GO_gene_set, hi_GO_ids):
    
    """
    Given a list of GO IDs, calculate its p-value according to the hypergeometric distribution. 
    -------------------------------------------------------
    inputs~
    
    gene_ontology_data: GO annotation dataset.
    GO_gene_set: Filtered GO annotation dataset corresponding to the test gene set. 
    hi_GO_ids: Overrepresented GO IDs. 
    
    outputs~
    
    summary_df: Summary dataframe with the statistically overrepresented GO IDs w/ their reported p-value
                and associated cofit genes. 
    
    """
    
    if hi_GO_ids is not None and len(hi_GO_ids) > 0: 
        n = GO_gene_set.shape[0] # sample size

        M = gene_ontology_data.shape[0] # total number of balls ~ total number of annotations

        p_vals = np.empty(len(hi_GO_ids))

        for i, hi_GO in enumerate(hi_GO_ids):

            # White balls drawn : counts of the hiGO in the GO_gene_set dataset
            w = pd.value_counts(GO_gene_set['GO_ID'].values, sort=False)[hi_GO]

            # Black balls drawn : counts of all of the GO IDs not corresponding to the specific hi_GO
            b = GO_gene_set.shape[0] - w

            # Total number of white balls in the bag : counts of the hiGO in the whole genome
            w_genome = pd.value_counts(gene_ontology_data['GO_ID'].values, sort=False)[hi_GO]

            # Total number of black balls in the bag : counts of non-hiGO IDs in the whole genome
            b_genome = gene_ontology_data.shape[0] - w_genome

            #Initialize an empty array to store the PMFs values
            hypergeom_pmfs = np.empty(n - w + 1)

            #Get all of the PMFs that are >= w (overrepresentation test)

            pmfs = st.hypergeom.pmf(k = np.arange(w, n+1), N = n, n = w_genome, M = M)

            #P-value = PMFs >= w 
            p_val = hypergeom_pmfs.sum()

            #Store p_value in the list 
            p_vals[i] = p_val

        #Filter the p_values < 0.05 
        significant_indices = p_vals < 0.05
        significant_pvals = p_vals[significant_indices]
        #Get significant GO_IDs 
        significant_GOs = hi_GO_ids[significant_indices]

        GO_summary_df = pd.DataFrame({ 'GO_ID': significant_GOs, 'p_val': significant_pvals })

        #Make a left inner join
        summary_df = pd.merge(GO_summary_df, GO_gene_set, on = 'GO_ID', how = 'inner')
        
        print('Enrichment test ran succesfully!')
        
        return summary_df
    
    else: 
        
        print('Enrichment test did not run.')


def get_GO_enrichment(gene_list):

    """
    Wrapper function to perform GO enrichment test. 
    """

    go = load_gene_ontology_data()

    go_gene_set = get_gene_data(go, 'gene_name', gene_list)

    hi_go_ids = get_hi_GOs(go_gene_set)

    enrichment_report = get_hyper_test_p_value(go, go_gene_set, hi_go_ids)

    return enrichment_report