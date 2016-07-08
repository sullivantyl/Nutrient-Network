
"""
This program takes data from the USDA Nutrient Database (http://www.ars.usda.gov/Services/docs.htm?docid=25700)
and creates a graph of the correlations between nutrients, based on what foods
they are found in.

By: Tyler Sullivan
"""
import pandas as pd
import numpy as np
import networkx as nx
import community
import os, os.path

# used to format data from the files for easy series formation
def strip(text):
    try:
        return float(text.strip("~"))
    except:
        return text.strip("~")

# opens the nutrition data file
with open ("NUT_DATA.txt") as infile:
    nut_data = pd.read_csv(infile, sep="^", usecols=[0,1,2], names=("NBD_No", "Nutr_No", "Nutr_Val"), converters = {'NBD_No' : strip,'Nutr_No' : strip,'Nutr_Val' : strip})

# gets rid of actual values and converts to 1 or 0 values, then removes zeroes
nut_data['Nutr_Val'][nut_data['Nutr_Val'] > 0] = 1
nut_data = nut_data[nut_data['Nutr_Val'] > 0]

# gets definition data for nutrition names
with open ("NUTR_DEF.txt") as infile:
    nutr_def = pd.read_csv(infile, sep="^", usecols=[0,3], names=("Nutr_No", "NutrDesc"), index_col=(0), converters = {'Nutr_No' : strip, 'NutrDesc' : strip})

# builds the network from the NUT_DATA information, removes self correlations, snips at value
corrdata = nut_data.pivot(index='NBD_No', columns='Nutr_No').fillna(0).corr()
corrdata -= np.eye(len(corrdata))
corrdata = corrdata[corrdata >= 0.5].fillna(0)
nut_network = nx.from_numpy_matrix(corrdata.values)

# converts labels to appropriate nutrition names
labels = dict(enumerate(corrdata.columns))
for a in labels:
    labels[a] = labels[a][1]
nx.relabel_nodes(nut_network, labels, copy=False)
nx.relabel_nodes(nut_network, nutr_def.to_dict()['NutrDesc'], copy=False)

# saves network as graphml file
if not os.path.isdir("results"):
    os.mkdir("results")
with open("results/nut_data.graphml", "wb") as ofile:
    nx.write_graphml(nut_network, ofile)

# creates partitions and gets modularity value
partition = community.best_partition(nut_network)
print("Modularity:", community.modularity(partition, nut_network))

# describe_cluster function from
HOW_MANY = 10
def describe_cluster (x):
    # x is a frame; select the matching rows from "domain"
    rows = nut_data.ix[x.index]
    # Calculate row sums, sort them, get the last HOW_MANY
    top_N = rows.sum(axis=1).sort_values(ascending=False)[ : HOW_MANY]
    # What labels do they have?
    return top_N.index.values

# displays clusters
nut_clusters = pd.DataFrame({"part_id" : pd.Series(partition)})
results = nut_clusters.groupby("part_id").apply(describe_cluster)
_ = [print("--", "; ".join(r.tolist())) for r in results]
