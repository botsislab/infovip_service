import pandas as pd
import json

similarityDF = pd.read_csv("data/SMQ_Similarities.csv", index_col = 0)

# Deserialize literal sets found in raw dataset
# similarityDF['MatchingPTs'] = similarityDF.apply(lambda row: list(eval(row['MatchingPTs'])), axis = 1)

# List of high similarity reports sorted by report and similarity
# similarityDF = similarityDF.drop(labels = 'MatchingPTs', axis = 'columns')
# highSimilarityDF = similarityDF.loc[similarityDF['LinSimilarity'] > 0.5]
# print(highSimilarityDF.sort_values(by = ['ReportID', 'LinSimilarity']))

# List of high similarity reports grouped by SMQ (with a count)
similarityDF = similarityDF.drop(labels = 'MatchingPTs', axis = 'columns')
highSimilarityDF = similarityDF.loc[similarityDF['LinSimilarity'] > 0.6]
print(highSimilarityDF.groupby('SMQ').count())

# List of all unique SMQs sorted alphabetically
# print(similarityDF.sort_values(by = ['SMQ']).SMQ.unique())

# reportsOfInterest = similarityDF.loc[similarityDF['LinSimilarity'] > 0.5].ReportID.unique()
# print(similarityDF.loc[similarityDF['ReportID'].isin(reportsOfInterest)].groupby('ReportID').count().sort_values(by = ['SMQ']))

quit()

# reportID = 10303397
# reportID = 7806518
reportID = 10639530

similarities = []
allSMQs = similarityDF.sort_values(by = ['SMQ']).SMQ.unique().tolist()
reportRecords = similarityDF.loc[similarityDF['ReportID'] == reportID]

# For each unique SMQ
for smq in allSMQs:
    # Get the similarity score for this SMQ and the selected ReportID
    if smq in reportRecords.SMQ.values:
        smqRecord = reportRecords.loc[reportRecords['SMQ'] == smq]
        similarities.append(smqRecord.iloc[0]['LinSimilarity'])
        # print(smqRecord.iloc[0]['LinSimilarity'])
    else:
        similarities.append(0)

# print(allSMQs)
print(similarities)