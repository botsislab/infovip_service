import pandas as pd
import json

def get_filename(data_id):
    return 'data/' + data_id + '.csv'

def get_dataframe(data_id, columns = None):
    return pd.read_csv(get_filename(data_id), usecols = columns)

def get_records(data_id, columns = None):
    df = get_dataframe(data_id, columns)
    return to_dict_dropna(df)

def get_data(data_id, columns = None, filters = []):

    dataframe = get_dataframe(data_id, columns)

    # TODO implement filtering
    for filter in filters:
        dataframe = filter_data(dataframe, filter)

    return to_dict_dropna(dataframe)

def get_unique(data_id, column):
    df = get_dataframe(data_id)
    return df.sort_values(by = [column])[column].unique().tolist()

def to_dict_dropna(dataframe):
    return [
        {
            k: (v if pd.notnull(v) else None)
            for k, v in m.items()
        }
        for m in dataframe.to_dict('record')
    ]

def filter_data(dataframe, filter):

    if filter.type == 'equals':
        return dataframe.loc[dataframe[filter.field] == filter.value]
    else:
        raise Exception('filter.type of ' + filter.type + ' is not supported')

def equals(field, value):
    return relation('equals', field, value)

def relation(type, field, value):
    return Relation(type, field, value)

class Relation:
    def __init__(self, type, field, value):
        self.type = type
        self.field = field
        self.value = value