import pandas as pd
import datetime
import json

featureCountsDF = pd.read_csv("data/ether_feature_counts.csv", index_col = 0)
# featureCountsDF = featureCountsDF[featureCountsDF.CausalityScore != 3]

# print(featureCountsDF.CausalityScore.unique())
print(featureCountsDF.to_dict('records'))
# print(featureCountsDF.CaseID.unique().tolist())