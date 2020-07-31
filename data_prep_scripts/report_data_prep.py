import pandas as pd
import datetime
import json

def date_parser(dates):

    parsed = []

    for date in dates:
        if len(str(date)) == 8:
            parsed.append(pd.to_datetime(date, format='%Y%m%d', errors='ignore'))
        elif len(str(date)) == 6:
            parsed.append(pd.to_datetime(date, format='%Y%m', errors='ignore'))
        else:
            parsed.append('nan')

    return parsed

# Initial read and parsing of dates
reportsDF = pd.read_csv("data/faers_report_data.csv", index_col = 0, usecols = ['ID', 'EVENT_DATE', 'AGE', 'AGE_CODE', 'SEX'], parse_dates = ['EVENT_DATE'], date_parser = date_parser)

# Get rid of NaNs and zero ages
reportsDF = reportsDF.dropna()
reportsDF = reportsDF[reportsDF.AGE != 0]

# Serialize dates to string
reportsDF['EVENT_DATE'] = reportsDF.apply(lambda row: row['EVENT_DATE'].strftime('%Y-%m-%d'), axis = 1)

# Clean up ages
def correct_age(row):
    age = row['AGE']
    code = row['AGE_CODE']

    if code == 'MON':
        return age / 12
    elif code == 'DY':
        return age / 365
    elif code == 'DEC':
        return age * 10
    else:
        return age

reportsDF['AGE'] = reportsDF.apply(correct_age, axis = 1)
reportsDF = reportsDF.drop(labels = 'AGE_CODE', axis = 'columns')

reportsDF['REPORT_ID'] = reportsDF.index

# Split by sex
maleDF = reportsDF[reportsDF['SEX'] == 'M'].drop(labels = 'SEX', axis = 'columns')
femaleDF = reportsDF[reportsDF['SEX'] == 'F'].drop(labels = 'SEX', axis = 'columns')

# print(maleDF)
print(femaleDF.to_dict('records'))

